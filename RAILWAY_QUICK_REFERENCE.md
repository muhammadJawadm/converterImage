# 🚀 Railway Deployment - Quick Reference

## 📋 Pre-Deployment Checklist

### 1. Supabase Setup (5 minutes)
```bash
1. Go to https://supabase.com → New Project
2. Storage → New Bucket → Name: "file-conversions" (Private)
3. Settings → API → Copy:
   - Project URL
   - Service Role Key (NOT anon key!)
```

### 2. Push to GitHub
```bash
git add .
git commit -m "Add Supabase storage integration"
git push origin main
```

### 3. Railway Setup (10 minutes)

#### Create Services:
1. **Backend API** (from GitHub repo)
2. **Redis** (New → Database → Redis)
3. **Celery Worker** (from same GitHub repo)

## 🔧 Environment Variables for Railway

Copy these to **EACH** service (Backend, Celery Worker):

```bash
# App Config
APP_NAME=File Converter API
APP_VERSION=1.0.0
DEBUG=False

# File Settings
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,doc,xlsx,xls,jpg,jpeg,png
FILE_RETENTION_HOURS=24

# CRITICAL: Supabase Storage (Required!)
USE_SUPABASE_STORAGE=True
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJ...your-service-role-key...
SUPABASE_BUCKET_NAME=file-conversions

# Redis (Auto from Railway)
REDIS_URL=${{Redis.REDIS_URL}}

# CORS (Update with your frontend)
CORS_ORIGINS=https://your-frontend.vercel.app
```

## 🎯 Service Configuration

### Backend API Service
```
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Celery Worker Service
```
Build Command: pip install -r requirements.txt
Start Command: celery -A app.celery_app worker --loglevel=info --pool=solo
```

### Optional: Flower (Monitoring)
```
Build Command: pip install -r requirements.txt
Start Command: celery -A app.celery_app flower --port=$PORT
```

## ✅ Testing After Deployment

### 1. Health Check
```bash
curl https://your-app.railway.app/health

Expected:
{
  "status": "healthy",
  "checks": {
    "storage": "ok",  # Should not say "error"
    "redis": "ok",
    "celery_workers": "ok - 1 worker(s) active"
  }
}
```

### 2. Test Upload
```bash
curl -X POST "https://your-app.railway.app/api/convert" \
  -F "file=@test.pdf" \
  -F "from_format=pdf" \
  -F "to_format=docx"

Expected:
{
  "job_id": "uuid-here",
  "status": "pending",
  "message": "Conversion job submitted successfully..."
}
```

### 3. Check Supabase
- Go to Supabase Dashboard → Storage → file-conversions
- You should see files in `uploads/` folder
- After conversion completes, check `outputs/` folder

## 🐛 Common Issues & Fixes

### ❌ "SUPABASE_URL and SUPABASE_KEY must be set"
**Fix:** 
- Go to Railway service → Variables
- Add `USE_SUPABASE_STORAGE=True`
- Add `SUPABASE_URL` and `SUPABASE_KEY`
- Redeploy

### ❌ Health check shows `"storage": "error"`
**Fix:**
- Verify Supabase bucket exists
- Check service_role key (not anon key!)
- Test: `curl https://your-project.supabase.co/rest/v1/`

### ❌ "No active Celery workers"
**Fix:**
- Ensure Celery Worker service is running
- Check it has same `REDIS_URL` variable
- View logs: Railway → Celery Worker → Logs

### ❌ LibreOffice not found
**Fix:** Railway includes LibreOffice by default. If missing:
- Create `nixpacks.toml`:
```toml
[phases.setup]
nixPkgs = ["python39", "libreoffice", "poppler_utils"]
```

### ❌ CORS errors from frontend
**Fix:**
- Update `CORS_ORIGINS` with your actual frontend URL
- No trailing slashes!
- Format: `https://yourapp.vercel.app,https://other.com`

## 💰 Cost Estimate

### Supabase Free Tier
- ✅ 1GB storage
- ✅ Unlimited API requests
- ✅ Automatic backups

### Railway Hobby Plan
- 💵 $5/month (includes $5 credit)
- ✅ Up to 512MB RAM per service
- ✅ 3 services (API, Worker, Redis)

**Total Cost:** ~$5/month (or free if under limits)

## 🎉 Success Indicators

You're successfully deployed when:

- ✅ Health endpoint returns "healthy"
- ✅ All checks show "ok"
- ✅ Can upload files via API
- ✅ Files appear in Supabase Storage
- ✅ Can download converted files
- ✅ No errors in Railway logs

## 📚 Need More Help?

- Full Guide: [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md)
- Quick Setup: [SUPABASE_QUICK_START.md](SUPABASE_QUICK_START.md)
- Changes: [SUPABASE_INTEGRATION_SUMMARY.md](SUPABASE_INTEGRATION_SUMMARY.md)

## 🔗 Important URLs

After deployment, save these:

- API: `https://your-backend.railway.app`
- API Docs: `https://your-backend.railway.app/docs`
- Health: `https://your-backend.railway.app/health`
- Flower: `https://your-flower.railway.app` (if deployed)
- Supabase: `https://app.supabase.com/project/your-project`

---

**Ready to deploy?** 
1. Setup Supabase (5 min)
2. Configure Railway (10 min)
3. Test deployment (2 min)
4. ✅ You're live!
