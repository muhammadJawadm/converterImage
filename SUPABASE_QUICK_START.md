# Quick Setup for Supabase Storage

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment

Copy `.env.example` to `.env`:
```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edit `.env` and update these values:

```env
# Enable Supabase Storage
USE_SUPABASE_STORAGE=True

# Get these from Supabase Dashboard → Settings → API
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key-here
SUPABASE_BUCKET_NAME=file-conversions

# Redis (local or cloud)
REDIS_URL=redis://localhost:6379/0
```

## Step 3: Create Supabase Bucket

1. Go to https://supabase.com/dashboard
2. Create new project or select existing
3. Navigate to **Storage** → **New bucket**
4. Name: `file-conversions`
5. Make it **Private** (not public)

## Step 4: Test Locally

### Start Redis:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Start Celery Worker:
```bash
celery -A app.celery_app worker --loglevel=info --pool=solo
```

### Start API:
```bash
uvicorn app.main:app --reload
```

### Test Upload:
```bash
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@test.pdf" \
  -F "from_format=pdf" \
  -F "to_format=docx"
```

## Step 5: Verify Supabase

1. Go to Supabase Dashboard → Storage
2. Open `file-conversions` bucket
3. You should see uploaded files in `uploads/` and `outputs/` folders

## Troubleshooting

### "SUPABASE_URL and SUPABASE_KEY must be set"
- Check your `.env` file exists
- Verify `USE_SUPABASE_STORAGE=True`
- Ensure no extra spaces in the values

### "Failed to initialize Supabase client"
- Verify SUPABASE_URL format: `https://xxxxx.supabase.co`
- Check SUPABASE_KEY is the **service_role** key (not anon)
- Test connection: `curl https://your-project.supabase.co/rest/v1/`

### Files not uploading
- Check bucket name matches `SUPABASE_BUCKET_NAME`
- Verify bucket exists in Supabase
- Check service_role key has storage permissions

## Switch Back to Local Storage

To disable Supabase and use local storage:

```env
USE_SUPABASE_STORAGE=False
```

Files will be stored in `storage/uploads` and `storage/outputs` directories.

## Ready for Production?

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for deploying to Railway with Supabase.
