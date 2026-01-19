"""
Conversion API Routes
Endpoints for file conversion, status checking, and file download (Celery-powered)
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from celery.result import AsyncResult
from datetime import datetime

from app.api.schemas.conversion import (
    ConversionResponse,
    StatusResponse,
    ErrorResponse,
    ConversionStatus
)
from app.utils.file_handler import (
    validate_file_type,
    validate_file_size,
    save_upload_file,
    validate_conversion_format,
    get_file_extension
)
from app.tasks.conversion_tasks import convert_file_task


router = APIRouter(prefix="/api", tags=["conversion"])


@router.post(
    "/convert",
    response_model=ConversionResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse}
    },
    summary="Upload and convert file",
    description="Upload a file and convert it to the specified format. Returns a job ID to track conversion progress via Celery."
)
async def convert_file(
    file: UploadFile = File(..., description="File to convert"),
    from_format: str = Form(..., description="Source file format (e.g., pdf, docx, xlsx)"),
    to_format: str = Form(..., description="Target file format (e.g., pdf, docx, png)")
):
    """
    Convert uploaded file to specified format using Celery background tasks
    
    - **file**: File to upload and convert
    - **from_format**: Source format (pdf, docx, doc, xlsx, xls, jpg, jpeg, png)
    - **to_format**: Target format (pdf, docx, png, jpg)
    """
    try:
        # Validate conversion format
        is_valid, error_msg = validate_conversion_format(from_format, to_format)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate file type
        is_valid, error_msg = validate_file_type(file)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Validate file extension matches from_format
        file_ext = get_file_extension(file.filename)
        if file_ext != from_format.lower() and not (file_ext in ["jpg", "jpeg"] and from_format.lower() in ["jpg", "jpeg"]):
            raise HTTPException(
                status_code=400,
                detail=f"File extension '.{file_ext}' does not match specified format '{from_format}'"
            )
        
        # Validate file size
        is_valid, error_msg = await validate_file_size(file)
        if not is_valid:
            raise HTTPException(status_code=413, detail=error_msg)
        
        # Generate temporary job ID for file storage
        from app.utils.file_handler import generate_job_id
        temp_job_id = generate_job_id()
        
        # Save uploaded file
        input_path = await save_upload_file(file, temp_job_id)
        
        # Submit Celery task
        task = convert_file_task.apply_async(
            args=[temp_job_id, str(input_path), from_format, to_format]
        )
        
        # Return Celery task ID as job_id
        return ConversionResponse(
            job_id=task.id,
            status=ConversionStatus.PENDING,
            message="Conversion job submitted successfully. Task is queued for processing.",
            created_at=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/status/{job_id}",
    response_model=StatusResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Check conversion status",
    description="Get the current status of a conversion job by its Celery task ID."
)
async def get_conversion_status(job_id: str):
    """
    Get conversion job status from Celery
    
    - **job_id**: Celery task ID returned from /convert endpoint
    """
    try:
        # Get Celery task result
        task_result = AsyncResult(job_id)
        
        # Map Celery states to our API states
        celery_state = task_result.state
        
        if celery_state == "PENDING":
            status = ConversionStatus.PENDING
            message = "Task is waiting in queue"
            
        elif celery_state in ["STARTED", "PROGRESS", "CONVERTING"]:
            status = ConversionStatus.PROCESSING
            # Get progress from task meta
            task_info = task_result.info or {}
            progress = task_info.get("progress", 0)
            task_status = task_info.get("status", "Processing...")
            message = f"{task_status} ({progress}%)"
            
        elif celery_state == "SUCCESS":
            status = ConversionStatus.COMPLETED
            message = "Conversion completed successfully"
            
        elif celery_state in ["FAILURE", "REVOKED", "REJECTED"]:
            status = ConversionStatus.FAILED
            message = "Conversion failed"
            
        else:
            status = ConversionStatus.PENDING
            message = f"Unknown state: {celery_state}"
        
        # Prepare response
        response = StatusResponse(
            job_id=job_id,
            status=status,
            message=message,
            created_at=None,  # Celery doesn't track creation time easily
            completed_at=None,
            error=None
        )
        
        # Add download URL if completed
        if status == ConversionStatus.COMPLETED:
            response.download_url = f"/api/download/{job_id}"
            if task_result.result:
                response.completed_at = datetime.now()
        
        # Add error details if failed
        if status == ConversionStatus.FAILED:
            try:
                error_info = str(task_result.info)
                response.error = error_info if error_info else "Unknown error occurred"
            except:
                response.error = "Task failed with unknown error"
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking task status: {str(e)}")


@router.get(
    "/download/{job_id}",
    response_class=FileResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse}
    },
    summary="Download converted file",
    description="Download the converted file if the conversion is complete."
)
async def download_converted_file(job_id: str):
    """
    Download converted file from Celery task result
    
    - **job_id**: Celery task ID
    """
    try:
        # Get Celery task result
        task_result = AsyncResult(job_id)
        
        # Check if task exists
        if task_result.state == "PENDING":
            raise HTTPException(
                status_code=404,
                detail=f"Job '{job_id}' not found or not yet started"
            )
        
        # Check if conversion is completed
        if task_result.state != "SUCCESS":
            raise HTTPException(
                status_code=400,
                detail=f"Conversion not yet completed. Current status: {task_result.state}"
            )
        
        # Get result data
        result_data = task_result.result
        if not result_data or 'output_path' not in result_data:
            raise HTTPException(
                status_code=500,
                detail="Task completed but output file information is missing"
            )
        
        # Get output file path
        output_path = Path(result_data['output_path'])
        
        # Check if file exists, or if .zip exists (multi-page PDF to images)
        if not output_path.exists():
            # Try .zip file (for multi-page PDF to image conversions)
            zip_path = output_path.with_suffix('.zip')
            if zip_path.exists():
                output_path = zip_path
                to_format = 'zip'
            else:
                raise HTTPException(status_code=404, detail="Converted file not found")
        
        # Determine media type
        to_format = result_data.get('to_format', output_path.suffix.lstrip('.'))
        
        # Override to_format if we're serving a ZIP
        if output_path.suffix == '.zip':
            to_format = 'zip'
        
        media_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "zip": "application/zip"
        }
        
        media_type = media_types.get(to_format, "application/octet-stream")
        
        # Determine filename
        if output_path.suffix == '.zip':
            filename = f"converted_pages_{job_id}.zip"
        else:
            filename = f"converted_{job_id}.{to_format}"
        
        # Return file
        return FileResponse(
            path=output_path,
            media_type=media_type,
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")
