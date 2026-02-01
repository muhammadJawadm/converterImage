# Cloud-Only File Converter - Quick Setup

## Prerequisites

1. **Supabase Account & Project**
   - Sign up at [https://supabase.com](https://supabase.com)
   - Create a new project
   - Create a storage bucket named `file-conversions`

2. **Python 3.11+** installed
3. **Redis** installed (or Docker)
4. **LibreOffice** installed (for Word/Excel conversions)

## Setup Steps

### 1. Get Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to **Settings → API**
3. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **Service Role Key** (NOT the anon key!)

### 2. Configure Environment

Create a `.env` file in the Backend directory:

```env
# Supabase Cloud Storage (REQUIRED)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key-here
SUPABASE_BUCKET_NAME=file-conversions

# File Upload Limits
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,doc,xlsx,xls,jpg,jpeg,png

# Temp directory for conversion processing
TEMP_DIR=temp

# LibreOffice Path
LIBREOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 4. Start Services

**Terminal 1 - Redis:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**Terminal 2 - Celery Worker:**
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Terminal 3 - FastAPI:**
```bash
python -m uvicorn app.main:app --reload
```

### 5. Test the API

Open http://localhost:8000/docs for interactive API documentation.

## How It Works

### Cloud-Only Architecture

```
User Upload → Supabase Storage (uploads/)
                    ↓
         Download to temp directory
                    ↓
            Local conversion
                    ↓
         Upload to Supabase Storage (outputs/)
                    ↓
        Cleanup temp files
                    ↓
       User downloads via signed URL
```

### File Flow

1. **Upload**: Files uploaded directly to Supabase `uploads/` folder
2. **Processing**: Downloaded to temp, converted, uploaded to `outputs/`
3. **Download**: Users get 1-hour signed URLs to download from Supabase
4. **Cleanup**: Temp files deleted immediately, cloud files cleaned after 24 hours

## API Endpoints

-POST `/api/convert` - Upload & convert file
- **GET** `/api/status/{job_id}` - Check conversion status
- **GET** `/api/download/{job_id}` - Download converted file
- **GET** `/health` - Health check

## Troubleshooting

### "Supabase Storage is required but not configured"
- Check your `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
- Ensure you're using the **service_role** key, not the anon key

### "Failed to upload file to Supabase"
- Verify bucket `file-conversions` exists in your Supabase project
- Check bucket permissions allow service role access

### "No module named 'supabase'"
- Run `pip install -r requirements.txt` in your activated virtual environment

## Storage Structure

```
Supabase Storage: file-conversions/
├── uploads/
│   └── {job_id}_input.{ext}
└── outputs/
    └── {job_id}_output.{ext}
```

## Features

✅ **100% Cloud Storage** - No local file persistence
✅ **Automatic Cleanup** - Temp files removed immediately
✅ **Secure Downloads** - Time-limited signed URLs
✅ **Scalable** - Works in containers and serverless
✅ **CDN Distribution** - Fast global downloads via Supabase CDN

## Next Steps

- Deploy to production (Docker/Kubernetes)
- Set up Supabase bucket lifecycle policies
- Configure CDN for faster downloads
- Add monitoring and analytics
