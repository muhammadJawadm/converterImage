# ✅ Supabase Storage Integration - Complete

## What Was Changed

Your PDF Converter backend has been successfully updated to support **Supabase cloud storage**, solving the Railway local storage issue.

## 🔧 Changes Made

### 1. **Configuration Updates**
- ✅ Added Supabase settings to [config.py](app/core/config.py)
  - `USE_SUPABASE_STORAGE`: Toggle between local/cloud storage
  - `SUPABASE_URL`: Your Supabase project URL
  - `SUPABASE_KEY`: Service role key for authentication
  - `SUPABASE_BUCKET_NAME`: Storage bucket name

### 2. **Dependencies**
- ✅ Added `supabase==2.3.4` to [requirements.txt](requirements.txt)

### 3. **File Handler Updates** ([file_handler.py](app/utils/file_handler.py))
- ✅ Auto-imports Supabase client when enabled
- ✅ `save_upload_file()`: Uploads to Supabase cloud storage
- ✅ `get_output_file_path()`: Uses temp directory for Supabase mode
- ✅ `save_output_file()`: New function to upload converted files
- ✅ `get_file_from_storage()`: Downloads from Supabase when needed
- ✅ `cleanup_old_files()`: Cleans up Supabase storage

### 4. **Celery Task Updates** ([conversion_tasks.py](app/tasks/conversion_tasks.py))
- ✅ Imports new storage functions
- ✅ Uploads converted files to Supabase automatically
- ✅ Returns public URL in task result

### 5. **API Route Updates** ([conversion.py](app/api/routes/conversion.py))
- ✅ Downloads files from Supabase for user download
- ✅ Uses signed URLs for secure temporary access
- ✅ Supports redirect to Supabase storage

### 6. **Main App Updates** ([main.py](app/main.py))
- ✅ Conditional directory creation (skips for Supabase)
- ✅ Shows storage mode on startup

### 7. **Critical Bug Fixes**
- ✅ Fixed missing `shutil` import in [word_to_pdf.py](app/services/converters/word_to_pdf.py)
- ✅ Fixed LibreOffice path detection logic
- ✅ Removed dead code in word_to_pdf converter

### 8. **Documentation**
- ✅ [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md): Complete Railway deployment guide
- ✅ [SUPABASE_QUICK_START.md](SUPABASE_QUICK_START.md): Quick setup guide
- ✅ Updated [README.md](README.md) with cloud deployment info
- ✅ Updated [.env.example](.env.example) with Supabase settings

## 🚀 How to Use

### For Local Development (No Supabase)

```env
# In your .env file
USE_SUPABASE_STORAGE=False
```

Files will be stored in local `storage/` folders.

### For Cloud Deployment (Railway with Supabase)

```env
# In your .env file or Railway environment variables
USE_SUPABASE_STORAGE=True
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_BUCKET_NAME=file-conversions
```

## 📦 Next Steps

### 1. Install New Dependencies
```bash
pip install -r requirements.txt
```

### 2. Choose Your Storage Mode

#### Option A: Continue with Local Storage (Development)
```bash
# Create .env from example
copy .env.example .env

# Edit .env and set:
USE_SUPABASE_STORAGE=False

# Run normally
uvicorn app.main:app --reload
```

#### Option B: Set Up Supabase (For Railway)
```bash
# Follow the guide:
# 1. Create Supabase account
# 2. Create new project
# 3. Create 'file-conversions' bucket
# 4. Get URL and service_role key

# Update .env:
USE_SUPABASE_STORAGE=True
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-key-here
```

See [SUPABASE_QUICK_START.md](SUPABASE_QUICK_START.md) for detailed setup.

### 3. Deploy to Railway

Follow [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for step-by-step Railway deployment instructions.

## 🧪 Testing

### Test Local Storage
```bash
# Set in .env
USE_SUPABASE_STORAGE=False

# Start services
python -m uvicorn app.main:app --reload

# Upload test file
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@test.pdf" \
  -F "from_format=pdf" \
  -F "to_format=docx"

# Check storage/uploads/ folder
```

### Test Supabase Storage
```bash
# Set in .env
USE_SUPABASE_STORAGE=True
SUPABASE_URL=https://...
SUPABASE_KEY=...

# Start services
python -m uvicorn app.main:app --reload

# Upload test file
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@test.pdf" \
  -F "from_format=pdf" \
  -F "to_format=docx"

# Check Supabase Dashboard → Storage → file-conversions bucket
```

## ⚙️ Configuration Options

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `USE_SUPABASE_STORAGE` | No | `False` | Enable Supabase cloud storage |
| `SUPABASE_URL` | Yes* | - | Your Supabase project URL |
| `SUPABASE_KEY` | Yes* | - | Service role key (not anon!) |
| `SUPABASE_BUCKET_NAME` | Yes* | `file-conversions` | Storage bucket name |

*Required only when `USE_SUPABASE_STORAGE=True`

## 🔒 Security Notes

1. **Use Service Role Key**: The `SUPABASE_KEY` must be the **service_role** key from Supabase Dashboard → Settings → API, NOT the anon/public key.

2. **Never Commit .env**: Your `.env` file should never be committed to Git (already in .gitignore).

3. **Private Bucket**: Make sure your Supabase bucket is set to **Private**, not public.

4. **Signed URLs**: For downloads, the app uses signed URLs that expire after 1 hour for security.

## 🐛 Troubleshooting

### "SUPABASE_URL and SUPABASE_KEY must be set"
- Check `.env` file exists
- Verify `USE_SUPABASE_STORAGE=True`
- Ensure no extra spaces in values

### "Failed to initialize Supabase client"
- Verify URL format: `https://xxxxx.supabase.co`
- Check you're using **service_role** key
- Test connection: `curl https://your-url.supabase.co/rest/v1/`

### Files Not Uploading to Supabase
- Verify bucket name matches `SUPABASE_BUCKET_NAME`
- Check bucket exists in Supabase Dashboard
- Ensure service_role key has storage permissions

### Railway Storage Errors
- Set `USE_SUPABASE_STORAGE=True` in Railway environment variables
- Add all required Supabase environment variables
- Check Railway logs for detailed errors

## 📊 Benefits of Supabase Storage

✅ **No local storage issues** - Perfect for Railway, Heroku, etc.
✅ **Scalable** - Handle large volumes without server disk limits
✅ **Persistent** - Files survive container restarts
✅ **Automatic backups** - Supabase handles backups
✅ **Global CDN** - Fast file access worldwide
✅ **Cost-effective** - Free tier includes 1GB storage

## 🎯 Production Checklist

Before deploying to Railway:

- [ ] Supabase project created
- [ ] `file-conversions` bucket created (private)
- [ ] Service role key obtained
- [ ] `USE_SUPABASE_STORAGE=True` in Railway
- [ ] All Supabase env vars set in Railway
- [ ] Redis service added to Railway
- [ ] Celery worker service created
- [ ] Test file upload/download works
- [ ] Health check returns `"storage": "ok"`

## 📚 Documentation

- [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) - Complete Railway deployment guide
- [SUPABASE_QUICK_START.md](SUPABASE_QUICK_START.md) - Quick Supabase setup
- [SUPABASE_SETUP.md](SUPABASE_SETUP.md) - Detailed Supabase configuration
- [README.md](README.md) - General project documentation

## 🎉 You're Ready!

Your backend now supports both local storage (development) and Supabase cloud storage (production). Deploy to Railway without worrying about storage limitations!

**Need help?** Check the documentation files or review the code comments.
