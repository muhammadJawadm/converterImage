"""
AWS S3 Storage Utility
Provides cloud storage operations using AWS S3
"""
import os
import boto3
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta
import logging
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3StorageClient:
    """AWS S3 Storage client for file operations"""
    
    def __init__(self):
        """Initialize S3 client"""
        self.s3_client = None
        self.bucket_name = getattr(settings, 'S3_BUCKET_NAME', '')
        self.region = getattr(settings, 'AWS_REGION', 'us-east-1')
        self.presigned_url_expiration = getattr(settings, 'S3_PRESIGNED_URL_EXPIRATION', 3600)
        
        if not self.bucket_name:
            logger.warning("S3_BUCKET_NAME not configured. S3 storage will be disabled.")
            return
        
        try:
            # Initialize boto3 S3 client
            # When running on EC2 with IAM role, credentials are automatic
            self.s3_client = boto3.client(
                's3',
                region_name=self.region
            )
            
            # Verify bucket access
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"✓ S3 client initialized for bucket: {self.bucket_name} in {self.region}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Ensure IAM role is attached to EC2 instance.")
            self.s3_client = None
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                logger.error(f"Access denied to S3 bucket '{self.bucket_name}'. Check IAM permissions.")
            else:
                logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
        except Exception as e:
            logger.error(f"Unexpected error initializing S3 client: {e}")
            self.s3_client = None
    
    def is_enabled(self) -> bool:
        """Check if S3 storage is enabled"""
        return self.s3_client is not None
    
    async def upload_file(
        self,
        local_file_path: Path,
        destination_path: str,
        bucket_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload file to S3
        
        Args:
            local_file_path: Local file path to upload
            destination_path: Destination path in bucket (e.g., 'uploads/file.pdf')
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Tuple of (success: bool, message: str, public_url: Optional[str])
        """
        if not self.is_enabled():
            return False, "S3 storage is not enabled", None
        
        bucket = bucket_name or self.bucket_name
        
        try:
            # Get content type
            content_type = self._get_content_type(local_file_path)
            
            # Upload file
            with open(local_file_path, 'rb') as f:
                self.s3_client.upload_fileobj(
                    f,
                    bucket,
                    destination_path,
                    ExtraArgs={
                        'ContentType': content_type,
                        'ServerSideEncryption': 'AES256'
                    }
                )
            
            # Generate presigned URL for download
            public_url = self.get_presigned_url(destination_path, bucket)
            
            logger.info(f"✓ Uploaded {local_file_path.name} to S3: {destination_path}")
            return True, f"File uploaded successfully to {destination_path}", public_url
            
        except FileNotFoundError:
            error_msg = f"Local file not found: {local_file_path}"
            logger.error(error_msg)
            return False, error_msg, None
        except ClientError as e:
            error_msg = f"Failed to upload file to S3: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error uploading to S3: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    async def download_file(
        self,
        source_path: str,
        local_file_path: Path,
        bucket_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Download file from S3
        
        Args:
            source_path: Source path in bucket (e.g., 'uploads/file.pdf')
            local_file_path: Local destination path
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_enabled():
            return False, "S3 storage is not enabled"
        
        bucket = bucket_name or self.bucket_name
        
        try:
            # Ensure parent directory exists
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            self.s3_client.download_file(bucket, source_path, str(local_file_path))
            
            logger.info(f"✓ Downloaded from S3: {source_path} to {local_file_path}")
            return True, f"File downloaded successfully from {source_path}"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                error_msg = f"File not found in S3: {source_path}"
            else:
                error_msg = f"Failed to download file from S3: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error downloading from S3: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def delete_file(
        self,
        file_path: str,
        bucket_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Delete file from S3
        
        Args:
            file_path: Path to file in bucket (e.g., 'uploads/file.pdf')
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_enabled():
            return False, "S3 storage is not enabled"
        
        bucket = bucket_name or self.bucket_name
        
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=file_path)
            logger.info(f"✓ Deleted from S3: {file_path}")
            return True, f"File deleted successfully: {file_path}"
            
        except ClientError as e:
            error_msg = f"Failed to delete file from S3: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error deleting from S3: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_presigned_url(
        self,
        file_path: str,
        bucket_name: Optional[str] = None,
        expiration: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary file access
        
        Args:
            file_path: Path to file in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL or None if failed
        """
        if not self.is_enabled():
            return None
        
        bucket = bucket_name or self.bucket_name
        expiration = expiration or self.presigned_url_expiration
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket,
                    'Key': file_path
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    async def list_files(
        self,
        prefix: str = "",
        bucket_name: Optional[str] = None
    ) -> Tuple[bool, str, list]:
        """
        List files in S3 bucket
        
        Args:
            prefix: Prefix to filter files (e.g., 'uploads/')
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Tuple of (success: bool, message: str, files: list)
        """
        if not self.is_enabled():
            return False, "S3 storage is not enabled", []
        
        bucket = bucket_name or self.bucket_name
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': self.get_presigned_url(obj['Key'], bucket)
                    })
            
            return True, f"Found {len(files)} files", files
            
        except ClientError as e:
            error_msg = f"Failed to list files from S3: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, []
        except Exception as e:
            error_msg = f"Unexpected error listing S3 files: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, []
    
    async def file_exists(
        self,
        file_path: str,
        bucket_name: Optional[str] = None
    ) -> bool:
        """
        Check if file exists in S3
        
        Args:
            file_path: Path to file in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            True if file exists, False otherwise
        """
        if not self.is_enabled():
            return False
        
        bucket = bucket_name or self.bucket_name
        
        try:
            self.s3_client.head_object(Bucket=bucket, Key=file_path)
            return True
        except ClientError:
            return False
    
    def _get_content_type(self, file_path: Path) -> str:
        """
        Determine content type from file extension
        
        Args:
            file_path: Path to file
            
        Returns:
            MIME type string
        """
        extension = file_path.suffix.lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.txt': 'text/plain',
            '.json': 'application/json',
        }
        
        return content_types.get(extension, 'application/octet-stream')


# Global instance
_s3_storage: Optional[S3StorageClient] = None


def get_s3_storage() -> S3StorageClient:
    """
    Get or create S3 storage client instance
    
    Returns:
        S3StorageClient instance
    """
    global _s3_storage
    if _s3_storage is None:
        _s3_storage = S3StorageClient()
    return _s3_storage
