# Railway Deployment Guide with Supabase Storage

This guide will help you deploy your PDF Converter backend to Railway using Supabase for cloud storage.

## Prerequisites

1. **Railway Account**: Sign up at [https://railway.app](https://railway.app)
2. **Supabase Account**: Create account at [https://supabase.com](https://supabase.com)
3. **GitHub Account**: Your code should be in a GitHub repository

## Step 1: Setup Supabase Storage

### 1.1 Create Supabase Project
1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click **New Project**
3. Fill in:
   - **Name**: `pdf-converter` (or your preferred name)
   - **Database Password**: Generate a strong password
   - **Region**: Choose closest to your users
4. Click **Create new project**

### 1.2 Create Storage Bucket
1. Navigate to **Storage** in the left sidebar
2. Click **New bucket**
3. Configure:
   - **Name**: `file-conversions`
   - **Public bucket**: Toggle **OFF** (private)
   - **File size limit**: `52428800` (50 MB)
4. Click **Create bucket**

### 1.3 Get Credentials
1. Go to **Settings** → **API**
2. Copy these values (you'll need them for Railway):
   - **Project URL**: `https://xxxxx.supabase.co`
   - **Service Role Key**: Click "Reveal" next to `service_role` (NOT the anon key)

⚠️ **Important**: Use the **service_role** key, not the anon key!

## Step 2: Prepare Your Repository

### 2.1 Create .env for Reference (Don't commit!)
Create a `.env` file locally to test:

```env
# Application
APP_NAME=File Converter API
APP_VERSION=1.0.0
DEBUG=False

# File Configuration
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,doc,xlsx,xls,jpg,jpeg,png

# Storage - MUST use Supabase for Railway
USE_SUPABASE_STORAGE=True
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-here
SUPABASE_BUCKET_NAME=file-conversions

# Redis (Railway will provide this)
REDIS_URL=redis://default:password@host:port

# CORS (Update with your frontend URL)
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000

# File Retention
FILE_RETENTION_HOURS=24
```

### 2.2 Update .gitignore
Ensure `.env` is in your `.gitignore`:

```
.env
__pycache__/
*.pyc
venv/
storage/
temp/
.DS_Store
```

### 2.3 Push to GitHub
```bash
git add .
git commit -m "Add Supabase storage integration"
git push origin main
```

## Step 3: Deploy to Railway

### 3.1 Create New Project
1. Go to [https://railway.app/new](https://railway.app/new)
2. Click **Deploy from GitHub repo**
3. Select your repository
4. Railway will detect your Python app

### 3.2 Add Redis Service
1. In your Railway project, click **New**
2. Select **Database** → **Redis**
3. Railway will provision Redis and create `REDIS_URL` variable

### 3.3 Configure Environment Variables

Click on your **Backend service** → **Variables** tab and add:

```
APP_NAME=File Converter API
APP_VERSION=1.0.0
DEBUG=False

MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,doc,xlsx,xls,jpg,jpeg,png

USE_SUPABASE_STORAGE=True
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-from-step-1.3
SUPABASE_BUCKET_NAME=file-conversions

REDIS_URL=${{Redis.REDIS_URL}}

CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000

FILE_RETENTION_HOURS=24
```

⚠️ **Important**:
- Replace `SUPABASE_URL` with your actual Supabase URL
- Replace `SUPABASE_KEY` with your service_role key
- `REDIS_URL` will automatically use Railway's Redis
- Update `CORS_ORIGINS` with your actual frontend URL

### 3.4 Configure Build & Start Commands

In Railway service settings:

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 3.5 Add Celery Worker Service

Your app needs a separate Celery worker. Create another service:

1. Click **New** → **GitHub Repo** (same repo)
2. Name it `celery-worker`
3. Add same environment variables as backend
4. Set **Start Command**:
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

### 3.6 (Optional) Add Flower Monitoring

For Celery monitoring:

1. Click **New** → **GitHub Repo** (same repo)
2. Name it `flower`
3. Add same environment variables
4. Set **Start Command**:
```bash
celery -A app.celery_app flower --port=$PORT
```

## Step 4: Deploy

1. Railway will automatically deploy when you push to GitHub
2. Monitor logs in Railway dashboard
3. Check health endpoint: `https://your-app.railway.app/health`

## Step 5: Test Your Deployment

### 5.1 Check Health
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "checks": {
    "storage": "ok",
    "redis": "ok",
    "celery_workers": "ok - 1 worker(s) active"
  }
}
```

### 5.2 Test File Upload
```bash
curl -X POST "https://your-app.railway.app/api/convert" \
  -F "file=@test.pdf" \
  -F "from_format=pdf" \
  -F "to_format=docx"
```

### 5.3 Check Conversion Status
```bash
curl https://your-app.railway.app/api/status/{job_id}
```

## Troubleshooting

### Error: "SUPABASE_URL and SUPABASE_KEY must be set"
- Verify environment variables are set in Railway
- Make sure `USE_SUPABASE_STORAGE=True`
- Check that SUPABASE_KEY is the **service_role** key

### Error: "LibreOffice not found"
Railway's default buildpack includes LibreOffice. If missing, add `nixpacks.toml`:

```toml
[phases.setup]
nixPkgs = ["python39", "libreoffice", "poppler_utils"]
```

### Celery Worker Not Starting
- Check Redis connection in logs
- Verify `REDIS_URL` environment variable
- Ensure celery-worker service is running

### File Upload Fails
- Check Supabase bucket exists and is named correctly
- Verify service_role key has proper permissions
- Check Railway logs for detailed error

### CORS Errors
- Update `CORS_ORIGINS` with your actual frontend URL
- Remove trailing slashes from URLs
- Test with your frontend URL, not localhost

## Monitoring

### View Logs
```bash
railway logs
```

### Check Celery Tasks
Visit Flower dashboard (if deployed):
```
https://your-flower-app.railway.app
```

### Monitor Supabase Storage
1. Go to Supabase Dashboard → Storage
2. Click on `file-conversions` bucket
3. View uploaded files and monitor storage usage

## Cost Optimization

### Railway
- **Hobby Plan**: $5/month (includes $5 credit)
- **Pro Plan**: Pay as you go
- Sleep inactive services to save costs

### Supabase
- **Free Tier**: 1GB storage
- **Pro Plan**: $25/month for more storage

### Tips
- Set `FILE_RETENTION_HOURS=1` for faster cleanup
- Monitor storage usage regularly
- Use signed URLs to prevent direct access
- Implement rate limiting to prevent abuse

## Production Checklist

- [ ] `DEBUG=False` in environment variables
- [ ] Strong Supabase service_role key
- [ ] CORS configured with actual frontend URL
- [ ] Health checks passing
- [ ] Celery worker running
- [ ] Test file upload/download
- [ ] Monitor logs for errors
- [ ] Set up error tracking (Sentry)
- [ ] Configure custom domain (optional)
- [ ] Set up SSL/HTTPS (Railway provides this)

## Next Steps

1. **Add Authentication**: Implement JWT or API keys
2. **Rate Limiting**: Prevent abuse
3. **Monitoring**: Set up Sentry for error tracking
4. **Backups**: Regular Supabase backups
5. **CDN**: Use Cloudflare for static assets

## Support

- **Railway Docs**: https://docs.railway.app
- **Supabase Docs**: https://supabase.com/docs
- **Project Issues**: Open issue on GitHub

---

**Deployed Successfully?** 🎉

Your API should now be live at: `https://your-app.railway.app`

Test it with: `https://your-app.railway.app/docs`
