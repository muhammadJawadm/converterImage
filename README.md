# File Conversion Backend API

A scalable, production-ready REST API for converting files between various formats (PDF, Word, Excel, Images). Built with FastAPI, Celery, Redis, and LibreOffice.

## 🚀 Features

- **Multiple Format Support**: PDF ↔ Word, Excel → PDF, Image ↔ PDF
- **Cloud Storage Options**: AWS S3, Supabase, or Local Storage
- **Distributed Processing**: Celery + Redis for scalable background tasks
- **Multiple Task Queues**: Separate queues for different conversion types
- **Real-time Monitoring**: Flower dashboard for task inspection
- **Docker Support**: Complete containerized deployment
- **Cloud Deployments**: AWS EC2, Railway, or self-hosted
- **Async Processing**: Non-blocking API with progress tracking
- **REST API**: Clean, well-documented endpoints
- **File Validation**: MIME type, extension, and size validation
- **Security**: Filename sanitization, directory traversal prevention
- **Auto-cleanup**: Automatic removal of old files from cloud storage
- **CORS Support**: Ready for frontend integration
- **Health Monitoring**: Health check endpoint for all services

## 📚 Deployment Guides

Choose your deployment platform:

### ☁️ AWS EC2 with S3 Storage (Recommended for Production)
- **[AWS Deployment Overview](AWS_README.md)** - Start here
- **[Complete EC2 Setup Guide](AWS_EC2_DEPLOYMENT_GUIDE.md)** - Step-by-step instructions
- **[Quick Reference](AWS_EC2_QUICK_REFERENCE.md)** - Commands and troubleshooting
- **[Deployment Checklist](AWS_DEPLOYMENT_CHECKLIST.md)** - Track your progress
- **Features**: Scalable, cost-effective, S3 storage, production-ready
- **Cost**: ~$47/month (can be optimized)

### 🚂 Railway with Supabase (Quick Deploy)
- **[Railway Deployment Guide](RAILWAY_DEPLOYMENT.md)** - One-click deployment
- **[Supabase Setup](SUPABASE_SETUP.md)** - Cloud storage configuration
- **Features**: Zero-config deployment, free tier available
- **Best for**: Quick prototypes, small projects

### 🐳 Docker Compose (Self-Hosted)
- **Quick Start**: See Docker section below
- **Features**: Easy local development, portable deployment
- **Best for**: Development, testing, small-scale production

## 🏗️ Architecture

```
Client → FastAPI → Redis → Celery Workers → File Storage
                     ↓
                  Flower (Monitoring)
```

**Components:**
- **FastAPI**: Web API server (port 8000)
- **Redis**: Message broker and result backend (port 6379)
- **Celery Workers**: Background task processors (autoscaling)
- **Flower**: Celery monitoring dashboard (port 5555)

## 📋 Supported Conversions

| From         | To           | Library Used  |
|--------------|--------------|---------------|
| PDF          | Word (DOCX)  | pdf2docx      |
| Word (DOCX)  | PDF          | LibreOffice   |
| Excel (XLSX) | PDF          | LibreOffice   |
| Image (JPG/PNG) | PDF       | img2pdf       |
| PDF          | Image (PNG)  | pdf2image     |

## 🛠️ Prerequisites

### Required
- **Python 3.11+**
- **Redis** (for Celery message broker)
- **LibreOffice** (for Word/Excel conversions)
  - Windows: Download from https://www.libreoffice.org/download/
  - Linux: `apt-get install libreoffice`

### For Cloud Deployment (Railway, etc.)
- **Supabase Account** (for cloud storage)
  - Free tier available: https://supabase.com
  - See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for setup

### Optional
- **poppler** (for PDF to Image conversion)
  - Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases
  - Linux: `apt-get install poppler-utils`

## 📦 Installation

1. **Clone or navigate to project directory**
   ```bash
   cd Backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` to customize settings:
   
   **For Local Development:**
   - Set `USE_SUPABASE_STORAGE=False`
   - Set `USE_S3_STORAGE=False`
   - Files stored in `storage/` directory
   
   **For AWS EC2 Deployment:**
   - Set `USE_S3_STORAGE=True`
   - Set `USE_SUPABASE_STORAGE=False`
   - Set `S3_BUCKET_NAME` and `AWS_REGION`
   - See [AWS_EC2_DEPLOYMENT_GUIDE.md](AWS_EC2_DEPLOYMENT_GUIDE.md)
   
   **For Cloud Deployment (Railway, etc.):**
   - Set `USE_SUPABASE_STORAGE=True`
   - Set `USE_S3_STORAGE=False`
   - Add Supabase credentials
   - See [SUPABASE_QUICK_START.md](SUPABASE_QUICK_START.md)

5. **Install LibreOffice**
   - Download and install from https://www.libreoffice.org/download/
   - Update `LIBREOFFICE_PATH` in `.env` if installed in custom location

## 🚀 Running the API

### Quick Start with Docker (Recommended)
```bash
# Start all services (FastAPI, Redis, Celery, Flower)
docker-compose up --build

# Access services:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Flower: http://localhost:5555
```

### Local Development (Without Docker)

**Prerequisites:**
- Redis server running
- LibreOffice installed

**1. Start Redis:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**2. Start Celery Worker:**
```bash
# Windows
celery -A app.celery_app worker --loglevel=info --pool=solo

# Linux/Mac
celery -A app.celery_app worker --loglevel=info
```

**3. Start Flower (Optional):**
```bash
celery -A app.celery_app flower
```

**4. Start FastAPI:**
```bash
python -m uvicorn app.main:app --reload
```

### Using Helper Scripts

**Windows:**
```bash
# Interactive menu
start.bat

# Or use Makefile
make start-docker
```

**Linux/Mac:**
```bash
make start-docker
```

API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Flower Dashboard**: http://localhost:5555

## 📚 API Endpoints

### 1. Convert File
**POST** `/api/convert`

Upload and convert a file.

**Request:**
- Form Data:
  - `file`: File to upload (multipart/form-data)
  - `from_format`: Source format (pdf, docx, xlsx, jpg, png)
  - `to_format`: Target format (pdf, docx, png)

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "message": "Conversion job created successfully",
  "created_at": "2024-01-17T18:30:00"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@document.pdf" \
  -F "from_format=pdf" \
  -F "to_format=docx"
```

### 2. Check Status
**GET** `/api/status/{job_id}`

Check conversion progress.

**Response:**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "message": "Conversion completed successfully",
  "created_at": "2024-01-17T18:30:00",
  "completed_at": "2024-01-17T18:30:15",
  "download_url": "/api/download/123e4567-e89b-12d3-a456-426614174000"
}
```

### 3. Download File
**GET** `/api/download/{job_id}`

Download converted file.

**Response:** File download

### 4. Health Check
**GET** `/health`

Check API health and dependencies.

**Response:**
```json
{
  "status": "healthy",
  "app_name": "File Converter API",
  "version": "1.0.0",
  "checks": {
    "storage": "ok",
    "libreoffice": "ok"
  }
}
```

## 📁 Project Structure

```
Backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── api/
│   │   ├── routes/
│   │   │   ├── conversion.py   # Conversion endpoints
│   │   │   └── health.py       # Health check endpoint
│   │   └── schemas/
│   │       └── conversion.py   # Pydantic models
│   ├── services/
│   │   ├── conversion_service.py  # Job orchestration
│   │   └── converters/
│   │       ├── base.py           # Base converter
│   │       ├── pdf_to_word.py
│   │       ├── word_to_pdf.py
│   │       ├── excel_to_pdf.py
│   │       ├── image_to_pdf.py
│   │       └── pdf_to_image.py
│   ├── core/
│   │   └── config.py           # Configuration
│   └── utils/
│       └── file_handler.py     # File utilities
├── storage/
│   ├── uploads/                # Uploaded files
│   └── outputs/                # Converted files
├── requirements.txt
├── .env.example
└── README.md
```

## ⚙️ Configuration

Edit `.env` file to customize:

```env
# File size limit (MB)
MAX_FILE_SIZE_MB=50

# Allowed file extensions
ALLOWED_EXTENSIONS=pdf,docx,doc,xlsx,xls,jpg,jpeg,png

# LibreOffice path
LIBREOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe

# File retention (hours)
FILE_RETENTION_HOURS=24

# CORS origins
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 🔒 Security Features

- **File Type Validation**: MIME type and extension checking
- **Size Limits**: Configurable maximum file size
- **Filename Sanitization**: Prevention of directory traversal attacks
- **CORS Protection**: Configurable allowed origins
- **Input Validation**: Pydantic schema validation

## 🧪 Testing with Postman

1. Import the API using OpenAPI spec: http://localhost:8000/docs
2. Create a POST request to `/api/convert`
3. Add form-data with:
   - `file`: Select file
   - `from_format`: Enter format (e.g., "pdf")
   - `to_format`: Enter format (e.g., "docx")
4. Send request and save the `job_id`
5. Check status with GET `/api/status/{job_id}`
6. Download with GET `/api/download/{job_id}`

## 🔄 Future Enhancements

The codebase is structured for easy scaling:

- **Celery Integration**: Replace `BackgroundTasks` with Celery for distributed processing
- **Redis**: Use Redis for job queue and status tracking
- **S3 Storage**: Replace local storage with cloud storage
- **Database**: PostgreSQL for job history and analytics
- **Authentication**: Add JWT authentication for user management
- **Rate Limiting**: Add request throttling
- **Webhooks**: Notify on completion
- **Batch Processing**: Multiple file conversions

## 🐛 Troubleshooting

### LibreOffice not found
- Ensure LibreOffice is installed
- Update `LIBREOFFICE_PATH` in `.env` to correct location
- Windows default: `C:\Program Files\LibreOffice\program\soffice.exe`

### PDF to Image fails
- Install poppler: https://github.com/oschwartz10612/poppler-windows/releases
- Add poppler `bin` folder to system PATH

### File upload fails
- Check file size limits in `.env`
- Verify file extension is allowed
- Check storage directory permissions

## 📝 License

MIT License - Feel free to use in your projects

## 👨‍💻 Author

Built with ❤️ using FastAPI and Python
