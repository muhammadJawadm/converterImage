"""
File Handling Utilities
Provides secure file operations, validation, and management
Supports local storage, Supabase cloud storage, and AWS S3
"""
import os
import uuid
import re
import mimetypes
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta
from fastapi import UploadFile, HTTPException
from app.core.config import settings

# Lazy import storage clients to avoid initialization errors
_supabase_storage = None
_s3_storage = None


def _get_supabase_storage():
    """Lazy load Supabase storage"""
    global _supabase_storage
    if _supabase_storage is None and settings.USE_SUPABASE_STORAGE:
        from app.utils.supabase_storage import get_supabase_storage
        _supabase_storage = get_supabase_storage()
    return _supabase_storage


def _get_s3_storage():
    """Lazy load S3 storage"""
    global _s3_storage
    if _s3_storage is None and settings.USE_S3_STORAGE:
        from app.utils.s3_storage import get_s3_storage
        _s3_storage = get_s3_storage()
    return _s3_storage


def _get_active_storage():
    """Get the active cloud storage client"""
    if settings.USE_S3_STORAGE:
        return _get_s3_storage()
    elif settings.USE_SUPABASE_STORAGE:
        return _get_supabase_storage()
    return None


def generate_job_id() -> str:
    """Generate a unique job ID using UUID4"""
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and special characters
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Get the filename without path components
    filename = os.path.basename(filename)
    
    # Remove special characters except dots, hyphens, and underscores
    filename = re.sub(r'[^\w\s\.\-]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename
    
    Args:
        filename: File name
        
    Returns:
        File extension without dot (lowercase)
    """
    return Path(filename).suffix.lstrip('.').lower()


def validate_file_type(file: UploadFile) -> Tuple[bool, str]:
    """
    Validate file type based on extension and MIME type
    
    Args:
        file: Uploaded file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file extension
    extension = get_file_extension(file.filename)
    
    if extension not in settings.allowed_extensions_list:
        return False, f"File type '.{extension}' not allowed. Allowed types: {', '.join(settings.allowed_extensions_list)}"
    
    # Verify MIME type
    mime_type = file.content_type
    expected_mimes = {
        'pdf': ['application/pdf'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'doc': ['application/msword'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
        'xls': ['application/vnd.ms-excel'],
        'jpg': ['image/jpeg'],
        'jpeg': ['image/jpeg'],
        'png': ['image/png'],
    }
    
    if extension in expected_mimes:
        if mime_type not in expected_mimes[extension]:
            return False, f"MIME type mismatch. Expected {expected_mimes[extension]}, got {mime_type}"
    
    return True, ""


async def validate_file_size(file: UploadFile) -> Tuple[bool, str]:
    """
    Validate file size is within limits
    
    Args:
        file: Uploaded file object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Read file to check size
    content = await file.read()
    file_size = len(content)
    
    # Reset file pointer
    await file.seek(0)
    
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return False, f"File size ({size_mb:.2f}MB) exceeds maximum allowed size ({settings.MAX_FILE_SIZE_MB}MB)"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, ""


async def save_upload_file(file: UploadFile, job_id: str) -> Path:
    """
    Save uploaded file to storage with sanitized name
    Uploads to S3/Supabase if enabled, otherwise saves locally
    
    Args:
        file: Uploaded file object
        job_id: Unique job identifier
        
    Returns:
        Path to saved file (local temp path if using cloud storage, or local storage path)
    """
    # Sanitize filename
    safe_filename = sanitize_filename(file.filename)
    
    # Create unique filename with job_id prefix
    extension = get_file_extension(safe_filename)
    unique_filename = f"{job_id}_input.{extension}"
    
    # Read file content
    content = await file.read()
    
    cloud_storage = _get_active_storage()
    
    if cloud_storage and cloud_storage.is_enabled():
        # Create temporary file for processing
        temp_dir = Path(tempfile.gettempdir()) / "pdfconverter"
        temp_dir.mkdir(parents=True, exist_ok=True)
        file_path = temp_dir / unique_filename
        
        # Save temporarily
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Upload to cloud storage (S3 or Supabase)
        destination_path = f"uploads/{unique_filename}"
        success, message, public_url = await cloud_storage.upload_file(
            file_path, destination_path
        )
        
        if not success:
            # Clean up temp file
            file_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"Failed to upload to cloud storage: {message}")
        
        # Return temp path for processing (will be cleaned up later)
        return file_path
    else:
        # Save locally
        file_path = settings.upload_path / unique_filename
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path


def get_output_file_path(job_id: str, output_extension: str) -> Path:
    """
    Generate output file path for converted file
    
    Args:
        job_id: Unique job identifier
        output_extension: Extension for output file (without dot)
        
    Returns:
        Path for output file (temp path if using cloud storage, or local storage path)
    """
    filename = f"{job_id}_output.{output_extension}"
    
    cloud_storage = _get_active_storage()
    
    if cloud_storage and cloud_storage.is_enabled():
        # Use temp directory for cloud storage
        temp_dir = Path(tempfile.gettempdir()) / "pdfconverter"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir / filename
    else:
        return settings.output_path / filename


async def save_output_file(file_path: Path, job_id: str) -> Tuple[bool, str, Optional[str]]:
    """
    Save output file to cloud storage if enabled
    
    Args:
        file_path: Local file path to upload
        job_id: Job identifier
        
    Returns:
    cloud_storage = _get_active_storage()
    
    if not cloud_storage or not cloud_storage.is_enabled():
        return True, "File saved locally", None
    
    # Upload to cloud storage (S3 or Supabase)
    destination_path = f"outputs/{file_path.name}"
    success, message, public_url = await cloud
    destination_path = f"outputs/{file_path.name}"
    success, message, public_url = await supabase_storage.upload_file(
        file_path, destination_path
    )
    
    if success:
        # Clean up local temp file
        file_path.unlink(missing_ok=True)
    
    return success, message, public_url


async def get_file_from_storage(job_id: str, file_path: Path) -> Path:
    """cloud storage if needed)
    
    Args:
        job_id: Job identifier
        file_path: Expected file path
        
    Returns:
        Local file path
    """
    cloud_storage = _get_active_storage()
    
    if not cloud_storage or not cloud_storage.is_enabled():
        return file_path
    
    # Check if file exists locally
    if file_path.exists():
        return file_path
    
    # Download from cloud storage (S3 or Supabase)
    source_path = f"outputs/{file_path.name}"
    success, message = await cloudh.name}"
    success, message = await supabase_storage.download_file(source_path, file_path)
    
    if not success:
        raise FileNotFoundError(f"Failed to download file from cloud storage: {message}")
    
    return file_path


def cleanup_old_files(retention_hours: Optional[int] = None):
    """
    Remove files older than retention period
    
    Args:
        retention_hours: Number of hours to retain files (default: from settings)
    """
    if retention_hours is None:
        retention_hours = settings.FILE_RETENTION_HOURS
    
    cloud_storage = _get_active_storage()
    
    if cloud_storage and cloud_storage.is_enabled():
        # Use cloud storage cleanup
        try:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            deleted_count = loop.run_until_complete(
                cloud_storage.cleanup_old_files(retention_hours)
            )
            return deleted_count
        except Exception as e:
            print(f"⚠️  Cloud storage cleanup failed: {e}")
            return 0
    
    # Local storage cleanup
    cutoff_time = datetime.now() - timedelta(hours=retention_hours)
    deleted_count = 0
    
    # Clean uploads and outputs directories
    for directory in [settings.upload_path, settings.output_path]:
        if not directory.exists():
            continue
            
        for file_path in directory.iterdir():
            if file_path.is_file():
                # Check file modification time
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
    
    if deleted_count > 0:
        print(f"✓ Cleaned up {deleted_count} old file(s)")
    
    return deleted_count


def validate_conversion_format(from_format: str, to_format: str) -> Tuple[bool, str]:
    """
    Validate if conversion between formats is supported
    
    Args:
        from_format: Source file format
        to_format: Target file format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Normalize formats
    from_fmt = from_format.lower().strip()
    to_fmt = to_format.lower().strip()
    
    # Check if conversion is supported
    supported_pairs = [
        ("pdf", "docx"),
        ("docx", "pdf"),
        ("doc", "pdf"),
        ("xlsx", "pdf"),
        ("xls", "pdf"),
        ("jpg", "pdf"),
        ("jpeg", "pdf"),
        ("png", "pdf"),
        ("pdf", "png"),
        ("pdf", "jpg"),
    ]
    
    if (from_fmt, to_fmt) in supported_pairs:
        return True, ""
    
    return False, f"Conversion from '{from_fmt}' to '{to_fmt}' is not supported"
