"""
Conversion Service
Main orchestrator for handling conversion jobs
"""
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from app.api.schemas.conversion import ConversionStatus
from app.utils.file_handler import get_output_file_path
from app.services.converters.pdf_to_word import PdfToWordConverter
from app.services.converters.word_to_pdf import WordToPdfConverter
from app.services.converters.excel_to_pdf import ExcelToPdfConverter
from app.services.converters.image_to_pdf import ImageToPdfConverter
from app.services.converters.pdf_to_image import PdfToImageConverter


# In-memory job storage (replace with Redis for production)
jobs_db: Dict[str, dict] = {}


def create_job(job_id: str, input_path: Path, from_format: str, to_format: str):
    """
    Create a new conversion job
    
    Args:
        job_id: Unique job identifier
        input_path: Path to uploaded file
        from_format: Source format
        to_format: Target format
    """
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": ConversionStatus.PENDING,
        "input_path": str(input_path),
        "from_format": from_format.lower(),
        "to_format": to_format.lower(),
        "created_at": datetime.now(),
        "completed_at": None,
        "error": None,
        "output_path": None
    }


def get_job(job_id: str) -> Optional[dict]:
    """
    Get job details by ID
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job dictionary or None if not found
    """
    return jobs_db.get(job_id)


def update_job_status(job_id: str, status: ConversionStatus, error: Optional[str] = None):
    """
    Update job status
    
    Args:
        job_id: Job identifier
        status: New status
        error: Error message if failed
    """
    if job_id in jobs_db:
        jobs_db[job_id]["status"] = status
        
        if error:
            jobs_db[job_id]["error"] = error
        
        if status == ConversionStatus.COMPLETED:
            jobs_db[job_id]["completed_at"] = datetime.now()


async def process_conversion(job_id: str):
    """
    Process a conversion job in background
    
    Args:
        job_id: Job identifier
    """
    job = get_job(job_id)
    
    if not job:
        return
    
    try:
        # Update status to processing
        update_job_status(job_id, ConversionStatus.PROCESSING)
        
        # Get input/output paths
        input_path = Path(job["input_path"])
        from_format = job["from_format"]
        to_format = job["to_format"]
        
        # Get output path
        output_path = get_output_file_path(job_id, to_format)
        
        # Select appropriate converter
        converter = get_converter(from_format, to_format)
        
        if not converter:
            raise ValueError(f"No converter available for {from_format} to {to_format}")
        
        # Perform conversion
        success, message = await converter.convert(input_path, output_path)
        
        if success:
            jobs_db[job_id]["output_path"] = str(output_path)
            update_job_status(job_id, ConversionStatus.COMPLETED)
        else:
            update_job_status(job_id, ConversionStatus.FAILED, error=message)
    
    except Exception as e:
        update_job_status(job_id, ConversionStatus.FAILED, error=str(e))


def get_converter(from_format: str, to_format: str):
    """
    Get appropriate converter based on formats
    
    Args:
        from_format: Source format
        to_format: Target format
        
    Returns:
        Converter instance or None
    """
    from_fmt = from_format.lower()
    to_fmt = to_format.lower()
    
    # PDF to Word
    if from_fmt == "pdf" and to_fmt in ["docx", "doc"]:
        return PdfToWordConverter()
    
    # Word to PDF
    if from_fmt in ["docx", "doc"] and to_fmt == "pdf":
        return WordToPdfConverter()
    
    # Excel to PDF
    if from_fmt in ["xlsx", "xls"] and to_fmt == "pdf":
        return ExcelToPdfConverter()
    
    # Image to PDF
    if from_fmt in ["jpg", "jpeg", "png"] and to_fmt == "pdf":
        return ImageToPdfConverter()
    
    # PDF to Image
    if from_fmt == "pdf" and to_fmt in ["png", "jpg", "jpeg"]:
        return PdfToImageConverter()
    
    return None
