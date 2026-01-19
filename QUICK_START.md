# 🚀 Quick Start Guide - File Converter API

Complete step-by-step guide to run the project with Celery + Redis.

---

## ✅ Prerequisites

Before starting, ensure you have:
- ✅ Python 3.11+ installed
- ✅ Docker Desktop installed (for Redis)
- ✅ LibreOffice installed (for Word/Excel conversions)

---

## 📦 Step 1: Install Dependencies

**Open PowerShell in project directory:**
```powershell
cd "c:\Users\muham\Desktop\Couresera Learning\Pdfconverter\Backend"
```

**Activate virtual environment and install:**
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed celery-5.3.6 redis-5.0.3 flower-2.0.1 ...
```

---

## 🐳 Step 2: Start Redis (Docker)

**In the same PowerShell window:**
```powershell
docker run -d -p 6379:6379 --name file-converter-redis redis:7-alpine
```

**Verify Redis is running:**
```powershell
docker ps
```

**You should see:**
```
CONTAINER ID   IMAGE           STATUS    PORTS
xxxxxxxxxx     redis:7-alpine  Up        0.0.0.0:6379->6379/tcp
```

---

## ⚙️ Step 3: Start Celery Worker

**Open a NEW PowerShell window (Terminal 1):**
```powershell
cd "c:\Users\muham\Desktop\Couresera Learning\Pdfconverter\Backend"
venv\Scripts\activate
celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Wait for this message:**
```
[tasks]
  . app.tasks.conversion_tasks.convert_file_task
  . app.tasks.conversion_tasks.convert_pdf_to_word
  ...

[INFO/MainProcess] Connected to redis://localhost:6379/0
[INFO/MainProcess] celery@YOUR-PC ready.
```

✅ **Keep this terminal running!**

---

## 🌐 Step 4: Start FastAPI Server

**Open ANOTHER NEW PowerShell window (Terminal 2):**
```powershell
cd "c:\Users\muham\Desktop\Couresera Learning\Pdfconverter\Backend"
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

**Wait for this message:**
```
🚀 Starting File Converter API v1.0.0

✓ Storage directories initialized
✓ API is ready to accept requests!
  - Docs: http://localhost:8000/docs
  - Health: http://localhost:8000/health

INFO: Application startup complete.
```

✅ **Keep this terminal running!**

---

## 🌸 Step 5: Start Flower (Optional - Monitoring)

**Open ANOTHER NEW PowerShell window (Terminal 3):**
```powershell
cd "c:\Users\muham\Desktop\Couresera Learning\Pdfconverter\Backend"
venv\Scripts\activate
celery -A app.celery_app flower
```

**Access Flower at:** http://localhost:5555

✅ **Keep this terminal running if you want monitoring!**

---

## 🎯 Step 6: Test the API

### **Health Check**
Open browser: http://localhost:8000/health

**Expected response:**
```json
{
  "status": "healthy",
  "checks": {
    "storage": "ok",
    "libreoffice": "ok",
    "redis": "ok",
    "celery_workers": "ok - 1 worker(s) active"
  }
}
```

### **API Documentation**
Open browser: http://localhost:8000/docs

### **Test File Conversion**
1. Click **POST /api/convert**
2. Click **"Try it out"**
3. Upload a file (PDF, Word, Excel, or Image)
4. Set `from_format`: `pdf`
5. Set `to_format`: `png`
6. Click **"Execute"**
7. Copy the `job_id` from response
8. Use **GET /api/status/{job_id}** to check progress
9. Use **GET /api/download/{job_id}** to download when complete

---

## 🎬 Full Command Sequence (Summary)

**Terminal 1 - Celery Worker:**
```powershell
cd "c:\Users\muham\Desktop\Couresera Learning\Pdfconverter\Backend"
venv\Scripts\activate
celery -A app.celery_app worker --loglevel=info --pool=solo
```

**Terminal 2 - FastAPI Server:**
```powershell
cd "c:\Users\muham\Desktop\Couresera Learning\Pdfconverter\Backend"
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

**Terminal 3 - Flower (Optional):**
```powershell
cd "c:\Users\muham\Desktop\Couresera Learning\Pdfconverter\Backend"
venv\Scripts\activate
celery -A app.celery_app flower
```

**One-time (if Redis not running):**
```powershell
docker run -d -p 6379:6379 --name file-converter-redis redis:7-alpine
```

---

## 🔄 Restart Instructions

### **If Redis is Already Created:**
```powershell
docker start file-converter-redis
```

### **Stop Everything:**
- **Celery Worker**: Press `CTRL+C` in Terminal 1
- **FastAPI**: Press `CTRL+C` in Terminal 2
- **Flower**: Press `CTRL+C` in Terminal 3
- **Redis**: `docker stop file-converter-redis`

### **Start Again:**
```powershell
# Start Redis (if stopped)
docker start file-converter-redis

# Terminal 1
celery -A app.celery_app worker --loglevel=info --pool=solo

# Terminal 2
python -m uvicorn app.main:app --reload

# Terminal 3 (optional)
celery -A app.celery_app flower
```

---

## 📊 Your Running Services

```
┌────────────────────────────┐
│   Terminal 1               │  Celery Worker (port internal)
│   celery worker            │  Processes conversion tasks
└────────────────────────────┘

┌────────────────────────────┐
│   Terminal 2               │  FastAPI Server (port 8000)
│   uvicorn app:main         │  REST API endpoints
└────────────────────────────┘

┌────────────────────────────┐
│   Terminal 3 (optional)    │  Flower (port 5555)
│   celery flower            │  Task monitoring dashboard
└────────────────────────────┘

┌────────────────────────────┐
│   Background (Docker)      │  Redis (port 6379)
│   redis                    │  Message broker
└────────────────────────────┘
```

**Data Flow:**
```
Client → FastAPI (8000) → Redis (6379) → Celery Worker → Storage
                             ↓
                         Flower (5555)
```

---

## 🌐 Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **API Docs** | http://localhost:8000/docs | Interactive API testing |
| **Health Check** | http://localhost:8000/health | System status |
| **Flower** | http://localhost:5555 | Task monitoring |

---

## 🎯 Supported Conversions

| From Format | To Format | Example |
|-------------|-----------|---------|
| PDF | DOCX (Word) | `from_format=pdf`, `to_format=docx` |
| DOCX (Word) | PDF | `from_format=docx`, `to_format=pdf` |
| XLSX (Excel) | PDF | `from_format=xlsx`, `to_format=pdf` |
| JPG/PNG | PDF | `from_format=jpg`, `to_format=pdf` |
| PDF | PNG/JPG | `from_format=pdf`, `to_format=png` |

**Note:** Multi-page PDFs converted to images will return a ZIP file containing all pages!

---

## 🐛 Troubleshooting

### **Redis Not Found**
```
Error: Cannot connect to redis
```
**Solution:**
```powershell
docker start file-converter-redis
# Or create new: docker run -d -p 6379:6379 --name file-converter-redis redis:7-alpine
```

### **Celery Tasks Not Registered**
```
[tasks]
(empty)
```
**Solution:** Restart Celery worker (`CTRL+C` then run celery command again)

### **Port Already in Use**
```
Error: Address already in use
```
**Solution:** 
- Kill process on port 8000: `netstat -ano | findstr :8000`
- Or change port: `uvicorn app.main:app --port 8001`

### **LibreOffice Not Found**
```
libreoffice: "not found"
```
**Solution:**
1. Install LibreOffice
2. Update path in `.env`: `LIBREOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe`

---

## 📁 Project Files Location

**Uploaded files:**
```
Backend/storage/uploads/
```

**Converted files:**
```
Backend/storage/outputs/
```

**Configuration:**
```
Backend/.env
```

---

## 🎉 You're All Set!

Your distributed file conversion API is now running!

**Test it:** http://localhost:8000/docs

**Monitor tasks:** http://localhost:5555

**Check health:** http://localhost:8000/health
