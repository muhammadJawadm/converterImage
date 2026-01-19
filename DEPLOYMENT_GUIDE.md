# Celery + Redis Deployment Guide

Complete guide for running the file conversion API with Celery, Redis, and Docker.

## 🚀 Quick Start with Docker (Recommended)

### Prerequisites
- Docker Desktop installed
- Docker Compose installed (included with Docker Desktop)

### Start All Services
```bash
docker-compose up --build
```

This will start:
- **Redis** (port 6379) - Message broker
- **FastAPI** (port 8000) - Web API
- **Celery Worker** - Background task processor
- **Flower** (port 5555) - Monitoring dashboard

### Access Services
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs  
- **Flower Dashboard**: http://localhost:5555
- **Health Check**: http://localhost:8000/health

### Stop Services
```bash
docker-compose down
```

### Scale Workers
```bash
# Run 5 worker containers
docker-compose up --scale celery-worker=5
```

---

## 💻 Local Development (Without Docker)

### Prerequisites
- Python 3.11+
- Redis server
- LibreOffice (for Word/Excel conversions)

### Step 1: Install Redis

**Windows:**
- Download from: https://github.com/microsoftarchive/redis/releases
- Or use Docker: `docker run -d-p 6379:6379 redis:7-alpine`

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# Mac
brew install redis
```

### Step 2: Start Redis
```bash
redis-server
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Start Celery Worker
```bash
# Windows
celery -A app.celery_app worker --loglevel=info --pool=solo

# Linux/Mac
celery -A app.celery_app worker --loglevel=info
```

### Step 5: Start Flower (Optional)
```bash
celery -A app.celery_app flower
```

### Step 6: Start FastAPI
```bash
python -m uvicorn app.main:app --reload
```

---

## 🎯 Testing the API

### Using Interactive Docs
1. Open http://localhost:8000/docs
2. Try the `/api/convert` endpoint
3. Upload a file and get a `job_id`
4. Check status with `/api/status/{job_id}`
5. Download with `/api/download/{job_id}`

### Using cURL
```bash
# Convert PDF to Word
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@document.pdf" \
  -F "from_format=pdf" \
  -F "to_format=docx"

# Check status
curl "http://localhost:8000/api/status/{job_id}"

# Download file
curl "http://localhost:8000/api/download/{job_id}" -o converted.docx
```

---

## 📊 Monitoring with Flower

Access Flower dashboard at http://localhost:5555

**Features:**
- Real-time task monitoring
- Worker statistics
- Task history and results
- Task retry/revoke actions
- Queue inspection

---

## 🔧 Configuration

### Environment Variables (.env)
```env
# Redis
REDIS_URL=redis://localhost:6379/0

# File Settings
MAX_FILE_SIZE_MB=50
FILE_RETENTION_HOURS=24

# LibreOffice Path
LIBREOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe
```

### Celery Queues

The system uses multiple queues for different conversion types:

- **default** - General tasks
- **pdf_queue** - PDF conversions (high resource)
- **image_queue** - Image conversions (lightweight)
- **office_queue** - Word/Excel conversions (LibreOffice)

**Start worker for specific queue:**
```bash
celery -A app.celery_app worker -Q pdf_queue --loglevel=info
```

---

## 🐳 Docker Commands

### Build Images
```bash
docker-compose build
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f celery-worker
docker-compose logs -f fastapi
```

### Restart Services
```bash
docker-compose restart
```

### Remove Everything
```bash
docker-compose down -v --rmi all
```

---

## 🔍 Health Checks

The `/health` endpoint now includes:
- Storage directories ✓
- LibreOffice availability ✓
- Redis connection ✓
- Celery workers ✓

Example response:
```json
{
  "status": "healthy",
  "checks": {
    "storage": "ok",
    "libreoffice": "ok",
    "redis": "ok",
    "celery_workers": "ok - 3 worker(s) active"
  }
}
```

---

## 📈 Scaling Strategies

### Horizontal Scaling (More Workers)
```bash
# Docker
docker-compose up --scale celery-worker=10

# Manual
# Start multiple worker processes on different machines
celery -A app.celery_app worker --loglevel=info
```

### Queue-Based Routing
```bash
# Dedicated workers for different workloads
celery -A app.celery_app worker -Q pdf_queue --concurrency=4
celery -A app.celery_app worker -Q image_queue --concurrency=8
```

### Autoscaling
```bash
# Scale between 2 and 10 workers based on load
celery -A app.celery_app worker --autoscale=10,2
```

---

## 🐛 Troubleshooting

### Redis Connection Error
```
Error: Can't connect to Redis
```
**Solution:**
- Ensure Redis is running: `redis-cli ping` should return `PONG`
- Check REDIS_URL in `.env`
- For Docker: Use `redis://redis:6379/0` instead of `localhost`

### No Celery Workers
```
celery_workers: "warning - no active workers"
```
**Solution:**
- Start a Celery worker process
- Check worker logs for errors

### Task Stuck in PENDING
```
Status: PENDING forever
```
**Solution:**
- Worker might be down - check worker logs
- Task might not be registered - restart workers
- Redis connection issue

### LibreOffice Not Found
```
LibreOffice not found at path
```
**Solution:**
- Install LibreOffice
- Update `LIBREOFFICE_PATH` in `.env`
- For Docker: LibreOffice is included in images

---

## 🔐 Production Considerations

### Security
- [ ] Enable Redis password authentication
- [ ] Use Redis ACLs for worker authentication
- [ ] Set up network isolation
- [ ] Implement API rate limiting
- [ ] Add authentication/authorization

### Performance
- [ ] Use Redis persistence (RDB/AOF)
- [ ] Configure worker concurrency based on CPU cores
- [ ] Set appropriate task time limits
- [ ] Enable task result backend for persistence

### Monitoring
- [ ] Set up log aggregation (ELK, Splunk)
- [ ] Configure alerts for task failures
- [ ] Monitor Redis memory usage
- [ ] Track worker resource consumption

---

## 📝 Migration from BackgroundTasks

If upgrading from the previous BackgroundTasks version:

1. **Install new dependencies:**
   ```bash
   pip install celery[redis]==5.3.6 redis==5.0.3 flower==2.0.1
   ```

2. **Start Redis:**
   ```bash
   docker run -d -p 6379:6379 redis:7-alpine
   ```

3. **Start Celery worker:**
   ```bash
   celery -A app.celery_app worker --loglevel=info --pool=solo
   ```

4. **Update client code:**
   - Old job IDs won't work - they're now Celery task IDs
   - Task states may differ slightly

5. **Test thoroughly:**
   - Submit test conversions
   - Verify status endpoints
   - Confirm downloads work

---

## 🆘 Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Verify health: http://localhost:8000/health
3. Check Flower: http://localhost:5555
4. Review task states in Redis: `redis-cli KEYS celery*`
