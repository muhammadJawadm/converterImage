"""
Pydantic Schemas for API Request/Response Models
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class ConversionStatus(str, Enum):
    """Conversion job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConversionType(str, Enum):
    """Supported conversion types"""
    PDF_TO_WORD = "pdf_to_word"
    WORD_TO_PDF = "word_to_pdf"
    EXCEL_TO_PDF = "excel_to_pdf"
    IMAGE_TO_PDF = "image_to_pdf"
    PDF_TO_IMAGE = "pdf_to_image"


class ConversionResponse(BaseModel):
    """Response model for conversion request"""
    job_id: str = Field(..., description="Unique job identifier")
    status: ConversionStatus = Field(..., description="Current conversion status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "pending",
                "message": "Conversion job created successfully",
                "created_at": "2024-01-17T18:30:00"
            }
        }


class StatusResponse(BaseModel):
    """Response model for status check"""
    job_id: str = Field(..., description="Unique job identifier")
    status: ConversionStatus = Field(..., description="Current conversion status")
    message: str = Field(..., description="Status message")
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    download_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "message": "Conversion completed successfully",
                "created_at": "2024-01-17T18:30:00",
                "completed_at": "2024-01-17T18:30:15",
                "download_url": "/api/download/123e4567-e89b-12d3-a456-426614174000"
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid file type",
                "detail": "File type '.txt' not allowed. Allowed types: pdf, docx, xlsx, jpg, png"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.now)
    checks: dict = Field(default_factory=dict, description="Health check results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "app_name": "File Converter API",
                "version": "1.0.0",
                "timestamp": "2024-01-17T18:30:00",
                "checks": {
                    "storage": "ok",
                    "libreoffice": "ok"
                }
            }
        }
