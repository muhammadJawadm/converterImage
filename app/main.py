"""
File Converter API
Production-ready FastAPI application for file format conversion
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings, create_directories
from app.api.routes import conversion, health
from app.utils.file_handler import cleanup_old_files


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    Runs on startup and shutdown
    """
    # Startup
    print(f"\n{'='*60}")
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"{'='*60}\n")
    
    # Create storage directories
    create_directories()
    
    # Initial cleanup of old files
    print("\n🧹 Running initial file cleanup...")
    cleanup_old_files()
    
    print(f"\n✓ API is ready to accept requests!")
    print(f"  - Docs: http://localhost:8000/docs")
    print(f"  - Health: http://localhost:8000/health\n")
    
    yield
    
    # Shutdown
    print("\n👋 Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Convert files between formats: PDF, Word, Excel, Images",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(conversion.router)


@app.get("/", tags=["root"])
def root():
    """Root endpoint"""
    return {
        "message": f"🚀 {settings.APP_NAME} is running!",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }

