"""
Supabase Storage Utility
Provides cloud storage operations using Supabase Storage
"""
import os
from pathlib import Path
from typing import Optional, Tuple, BinaryIO
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseStorageClient:
    """Supabase Storage client for file operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Optional[any] = None
        self.bucket_name = settings.SUPABASE_BUCKET_NAME
        
        # Supabase is required for cloud-only storage
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment variables. "
                "This application requires Supabase for cloud storage."
            )
        
        try:
            # Import here to avoid issues if supabase is not properly installed
            from supabase import create_client, Client
            
            # Create client with minimal options to avoid proxy parameter issue
            self.client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
            logger.info(f"✓ Supabase client initialized for bucket: {self.bucket_name}")
        except TypeError as e:
            # Handle version incompatibility
            logger.error(f"Supabase client initialization failed (version incompatibility): {e}")
            logger.error("Please upgrade supabase package: pip install --upgrade supabase")
            raise ValueError(f"Supabase SDK version incompatibility: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def is_enabled(self) -> bool:
        """Check if Supabase storage is enabled"""
        return self.client is not None
    
    async def upload_file(
        self,
        local_file_path: Path,
        destination_path: str,
        bucket_name: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload file to Supabase Storage
        
        Args:
            local_file_path: Local file path to upload
            destination_path: Destination path in bucket (e.g., 'uploads/file.pdf')
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Tuple of (success: bool, message: str, public_url: Optional[str])
        """
        if not self.is_enabled():
            return False, "Supabase storage is not enabled", None
        
        bucket = bucket_name or self.bucket_name
        
        try:
            # Read file content
            with open(local_file_path, 'rb') as f:
                file_content = f.read()
            
            # Upload to Supabase
            response = self.client.storage.from_(bucket).upload(
                path=destination_path,
                file=file_content,
                file_options={"content-type": self._get_content_type(local_file_path)}
            )
            
            # Get public URL
            public_url = self.get_public_url(destination_path, bucket)
            
            logger.info(f"✓ Uploaded {local_file_path.name} to Supabase: {destination_path}")
            return True, f"File uploaded successfully to {destination_path}", public_url
            
        except Exception as e:
            error_msg = f"Failed to upload file to Supabase: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    async def download_file(
        self,
        source_path: str,
        local_file_path: Path,
        bucket_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Download file from Supabase Storage
        
        Args:
            source_path: Source path in bucket
            local_file_path: Local destination path
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_enabled():
            return False, "Supabase storage is not enabled"
        
        bucket = bucket_name or self.bucket_name
        
        try:
            # Download from Supabase
            response = self.client.storage.from_(bucket).download(source_path)
            
            # Ensure parent directory exists
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to local file
            with open(local_file_path, 'wb') as f:
                f.write(response)
            
            logger.info(f"✓ Downloaded {source_path} from Supabase to {local_file_path}")
            return True, f"File downloaded successfully to {local_file_path}"
            
        except Exception as e:
            error_msg = f"Failed to download file from Supabase: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_public_url(
        self,
        file_path: str,
        bucket_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Get public URL for a file
        
        Args:
            file_path: File path in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Public URL or None
        """
        if not self.is_enabled():
            return None
        
        bucket = bucket_name or self.bucket_name
        
        try:
            response = self.client.storage.from_(bucket).get_public_url(file_path)
            return response
        except Exception as e:
            logger.error(f"Failed to get public URL: {e}")
            return None
    
    def create_signed_url(
        self,
        file_path: str,
        expiry_seconds: int = 3600,
        bucket_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a signed URL for temporary access
        
        Args:
            file_path: File path in bucket
            expiry_seconds: URL expiry time in seconds (default: 1 hour)
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Signed URL or None
        """
        if not self.is_enabled():
            return None
        
        bucket = bucket_name or self.bucket_name
        
        try:
            response = self.client.storage.from_(bucket).create_signed_url(
                path=file_path,
                expires_in=expiry_seconds
            )
            return response.get('signedURL')
        except Exception as e:
            logger.error(f"Failed to create signed URL: {e}")
            return None
    
    async def delete_file(
        self,
        file_path: str,
        bucket_name: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Delete file from Supabase Storage
        
        Args:
            file_path: File path in bucket
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_enabled():
            return False, "Supabase storage is not enabled"
        
        bucket = bucket_name or self.bucket_name
        
        try:
            self.client.storage.from_(bucket).remove([file_path])
            logger.info(f"✓ Deleted {file_path} from Supabase")
            return True, f"File deleted successfully: {file_path}"
            
        except Exception as e:
            error_msg = f"Failed to delete file from Supabase: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    async def cleanup_old_files(
        self,
        retention_hours: int = 24,
        bucket_name: Optional[str] = None
    ) -> int:
        """
        Remove files older than retention period from Supabase Storage
        
        Args:
            retention_hours: Number of hours to retain files
            bucket_name: Bucket name (defaults to configured bucket)
            
        Returns:
            Number of files deleted
        """
        if not self.is_enabled():
            logger.warning("Supabase storage is not enabled, skipping cleanup")
            return 0
        
        bucket = bucket_name or self.bucket_name
        deleted_count = 0
        
        try:
            # List all files in bucket
            response = self.client.storage.from_(bucket).list()
            
            cutoff_time = datetime.now() - timedelta(hours=retention_hours)
            files_to_delete = []
            
            for file_obj in response:
                # Check file creation/update time
                created_at_str = file_obj.get('created_at')
                if created_at_str:
                    file_time = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    
                    if file_time.replace(tzinfo=None) < cutoff_time:
                        files_to_delete.append(file_obj['name'])
            
            # Delete old files
            if files_to_delete:
                self.client.storage.from_(bucket).remove(files_to_delete)
                deleted_count = len(files_to_delete)
                logger.info(f"✓ Cleaned up {deleted_count} old file(s) from Supabase")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files from Supabase: {e}")
            return 0
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type based on file extension"""
        extension = file_path.suffix.lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.zip': 'application/zip',
        }
        
        return content_types.get(extension, 'application/octet-stream')


# Global Supabase storage client instance (lazy initialization)
_supabase_storage_instance = None


def get_supabase_storage() -> SupabaseStorageClient:
    """Get or create Supabase storage client instance"""
    global _supabase_storage_instance
    if _supabase_storage_instance is None:
        _supabase_storage_instance = SupabaseStorageClient()
    return _supabase_storage_instance


# For backward compatibility
supabase_storage = None
try:
    if settings.USE_SUPABASE_STORAGE:
        supabase_storage = get_supabase_storage()
except Exception as e:
    logger.warning(f"Supabase storage not available: {e}")
