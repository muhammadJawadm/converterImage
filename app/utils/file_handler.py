"""
File Handling Utilities
Provides secure file operations, validation, and management
"""
import os
import uuid
import re
import mimetypes
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime, timedelta
from fastapi import UploadFile, HTTPException
from app.core.config import settings


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
    
    Args:
        file: Uploaded file object
        job_id: Unique job identifier
        
    Returns:
        Path to saved file
    """
    # Sanitize filename
    safe_filename = sanitize_filename(file.filename)
    
    # Create unique filename with job_id prefix
    extension = get_file_extension(safe_filename)
    unique_filename = f"{job_id}_input.{extension}"
    
    # Full path
    file_path = settings.upload_path / unique_filename
    
    # Save file
    content = await file.read()
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
        Path for output file
    """
    filename = f"{job_id}_output.{output_extension}"
    return settings.output_path / filename


def cleanup_old_files(retention_hours: Optional[int] = None):
    """
    Remove files older than retention period
    
    Args:
        retention_hours: Number of hours to retain files (default: from settings)
    """
    if retention_hours is None:
        retention_hours = settings.FILE_RETENTION_HOURS
    
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
