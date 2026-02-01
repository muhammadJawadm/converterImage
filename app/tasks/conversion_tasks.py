"""
Celery Tasks for File Conversion
Background tasks for converting files between formats
"""
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from pathlib import Path
import logging

from app.celery_app import celery_app
from app.utils.file_handler import get_output_file_path, save_output_file
from app.services.converters.pdf_to_word import PdfToWordConverter
from app.services.converters.word_to_pdf import WordToPdfConverter
from app.services.converters.excel_to_pdf import ExcelToPdfConverter
from app.services.converters.image_to_pdf import ImageToPdfConverter
from app.services.converters.pdf_to_image import PdfToImageConverter

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """
    Custom Task class with callbacks for progress tracking
    """
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"Task {task_id} retrying: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)


@celery_app.task(
    bind=True,
    base=CallbackTask,
    name="app.tasks.conversion_tasks.convert_file_task",
    max_retries=3,
    default_retry_delay=60
)
def convert_file_task(self, job_id: str, input_path: str, from_format: str, to_format: str) -> dict:
    """
    Main conversion task with progress tracking
    
    Args:
        self: Task instance (bound)
        job_id: Unique job identifier
        input_path: Path to uploaded file
        from_format: Source format
        to_format: Target format
        
    Returns:
        dict: Result with output_path and metadata
    """
    try:
        # Update task state to STARTED
        self.update_state(
            state='STARTED',
            meta={'progress': 0, 'status': 'Starting conversion...'}
        )
        
        # Convert paths to Path objects
        input_file = Path(input_path)
        output_file = get_output_file_path(job_id, to_format)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 25, 'status': 'Initializing converter...'}
        )
        
        # Get appropriate converter
        converter = get_converter(from_format, to_format)
        if not converter:
            raise ValueError(f"No converter available for {from_format} to {to_format}")
        
        # Update progress
        self.update_state(
            state='CONVERTING',
            meta={'progress': 50, 'status': f'Converting {from_format} to {to_format}...'}
        )
        
        # Perform conversion (async function called in sync context)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        success, message = loop.run_until_complete(converter.convert(input_file, output_file))
        
        if not success:
            raise Exception(f"Conversion failed: {message}")
        
        # Upload output to Supabase if enabled
        self.update_state(
            state='PROGRESS',
            meta={'progress': 90, 'status': 'Uploading to cloud storage...'}
        )
        
        upload_success, upload_message, public_url = loop.run_until_complete(
            save_output_file(output_file, job_id)
        )
        
        if not upload_success:
            raise Exception(f"Failed to save output file: {upload_message}")
        
        # Return result
        return {
            'job_id': job_id,
            'output_path': str(output_file),
            'public_url': public_url,
            'from_format': from_format,
            'to_format': to_format,
            'status': 'completed',
            'message': message
        }
        
    except SoftTimeLimitExceeded:
        logger.error(f"Task {self.request.id} exceeded time limit")
        raise
    
    except Exception as exc:
        logger.error(f"Conversion task failed for {job_id}: {exc}")
        # Retry task if retries remaining
        raise self.retry(exc=exc)


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


# Specific tasks for different conversion types (optional - for queue routing)

@celery_app.task(bind=True, base=CallbackTask, name="app.tasks.conversion_tasks.convert_pdf_to_word")
def convert_pdf_to_word(self, job_id: str, input_path: str) -> dict:
    """PDF to Word conversion task"""
    return convert_file_task(self, job_id, input_path, "pdf", "docx")


@celery_app.task(bind=True, base=CallbackTask, name="app.tasks.conversion_tasks.convert_word_to_pdf")
def convert_word_to_pdf(self, job_id: str, input_path: str) -> dict:
    """Word to PDF conversion task"""
    return convert_file_task(self, job_id, input_path, "docx", "pdf")


@celery_app.task(bind=True, base=CallbackTask, name="app.tasks.conversion_tasks.convert_excel_to_pdf")
def convert_excel_to_pdf(self, job_id: str, input_path: str) -> dict:
    """Excel to PDF conversion task"""
    return convert_file_task(self, job_id, input_path, "xlsx", "pdf")


@celery_app.task(bind=True, base=CallbackTask, name="app.tasks.conversion_tasks.convert_image_to_pdf")
def convert_image_to_pdf(self, job_id: str, input_path: str) -> dict:
    """Image to PDF conversion task"""
    return convert_file_task(self, job_id, input_path, "jpg", "pdf")


@celery_app.task(bind=True, base=CallbackTask, name="app.tasks.conversion_tasks.convert_pdf_to_image")
def convert_pdf_to_image(self, job_id: str, input_path: str) -> dict:
    """PDF to Image conversion task"""
    return convert_file_task(self, job_id, input_path, "pdf", "png")
