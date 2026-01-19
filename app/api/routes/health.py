"""
Health Check Route
Endpoint for monitoring API health, dependencies, and Celery workers
"""
from fastapi import APIRouter
from datetime import datetime
import os

from app.api.schemas.conversion import HealthResponse
from app.core.config import settings


router = APIRouter(tags=["health"])


def check_redis_connection() -> str:
    """Check Redis connection"""
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return "ok"
    except Exception as e:
        return f"error - {str(e)}"


def check_celery_workers() -> str:
    """Check if Celery workers are running"""
    try:
        from app.celery_app import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            worker_count = len(active_workers)
            return f"ok - {worker_count} worker(s) active"
        else:
            return "warning - no active workers"
    except Exception as e:
        return f"error - {str(e)}"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API health and verify dependencies (Storage, LibreOffice, Redis, Celery)"
)
async def health_check():
    """
    Health check endpoint
    
    Returns API status and checks for:
    - Storage directories accessibility
    - LibreOffice availability (optional)
    - Redis connection
    - Celery worker availability
    """
    checks = {}
    
    # Check storage directories
    try:
        upload_exists = settings.upload_path.exists()
        output_exists = settings.output_path.exists()
        
        if upload_exists and output_exists:
            checks["storage"] = "ok"
        else:
            checks["storage"] = "error - directories not found"
    except Exception as e:
        checks["storage"] = f"error - {str(e)}"
    
    # Check LibreOffice (optional - won't fail health check)
    try:
        if os.path.exists(settings.LIBREOFFICE_PATH):
            checks["libreoffice"] = "ok"
        else:
            checks["libreoffice"] = "not found (required for Word/Excel conversions)"
    except Exception as e:
        checks["libreoffice"] = f"check failed - {str(e)}"
    
    # Check Redis connection
    checks["redis"] = check_redis_connection()
    
    # Check Celery workers
    checks["celery_workers"] = check_celery_workers()
    
    # Determine overall status
    critical_checks = ["storage", "redis"]
    status = "healthy"
    
    for check_name in critical_checks:
        if checks.get(check_name, "").startswith("error"):
            status = "unhealthy"
            break
        elif checks.get(check_name, "").startswith("warning"):
            status = "degraded"
    
    return HealthResponse(
        status=status,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        timestamp=datetime.now(),
        checks=checks
    )
