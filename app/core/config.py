"""
Application Configuration
Centralized configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "File Converter API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 50
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS: str = "pdf,docx,doc,xlsx,xls,jpg,jpeg,png"
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR: str = "storage/uploads"
    OUTPUT_DIR: str = "storage/outputs"
    
    @property
    def upload_path(self) -> Path:
        """Get absolute upload directory path"""
        return self.BASE_DIR / self.UPLOAD_DIR
    
    @property
    def output_path(self) -> Path:
        """Get absolute output directory path"""
        return self.BASE_DIR / self.OUTPUT_DIR
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Get list of allowed file extensions"""
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    # LibreOffice Configuration
    LIBREOFFICE_PATH: str = r"C:\Program Files\LibreOffice\program\soffice.exe"
    
    # File Retention
    FILE_RETENTION_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get list of allowed CORS origins"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # Redis & Celery Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    
    @property
    def celery_broker_url(self) -> str:
        """Get Celery broker URL (defaults to REDIS_URL)"""
        return self.CELERY_BROKER_URL or self.REDIS_URL
    
    @property
    def celery_result_backend(self) -> str:
        """Get Celery result backend URL (defaults to REDIS_URL)"""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL
    
    # Celery Task Configuration
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 600  # 10 minutes hard limit
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300  # 5 minutes soft limit
    CELERY_RESULT_EXPIRES: int = 86400  # 24 hours
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    
    # Supported Conversions
    SUPPORTED_CONVERSIONS: dict = {
        "pdf_to_word": {"from": "pdf", "to": "docx"},
        "word_to_pdf": {"from": "docx", "to": "pdf"},
        "excel_to_pdf": {"from": "xlsx", "to": "pdf"},
        "image_to_pdf": {"from": ["jpg", "jpeg", "png"], "to": "pdf"},
        "pdf_to_image": {"from": "pdf", "to": "png"},
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()


def create_directories():
    """Create storage directories if they don't exist"""
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.output_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Storage directories initialized:")
    print(f"  - Uploads: {settings.upload_path}")
    print(f"  - Outputs: {settings.output_path}")
