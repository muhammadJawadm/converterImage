# Supabase Storage Setup Guide

This guide will help you configure your PDF Converter backend to use Supabase Storage for cloud-based file storage.

## Prerequisites

1. **Supabase Account**: Create a free account at [https://supabase.com](https://supabase.com)
2. **Supabase Project**: Create a new project in your Supabase dashboard

## Step 1: Create Storage Bucket

1. Go to your Supabase project dashboard
2. Navigate to **Storage** in the left sidebar
3. Click **New bucket**
4. Configure the bucket:
   - **Name**: `file-conversions` (or your preferred name)
   - **Public bucket**: Toggle OFF (for private files)
   - **File size limit**: Set to 52428800 (50 MB) or higher
5. Click **Create bucket**

## Step 2: Configure Bucket Policies (Optional)

For better security, set up Row Level Security (RLS) policies:

1. Go to **Storage** → Click on your bucket
2. Navigate to **Policies** tab
3. Add policies as needed for your use case

**Example policy for service role access:**
```sql
-- Allow service role to upload files
CREATE POLICY "Service role can upload files"
ON storage.objects FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'file-conversions');

-- Allow service role to download files
CREATE POLICY "Service role can download files"
ON storage.objects FOR SELECT
TO service_role
USING (bucket_id = 'file-conversions');

-- Allow service role to delete files
CREATE POLICY "Service role can delete files"
ON storage.objects FOR DELETE
TO service_role
USING (bucket_id = 'file-conversions');
```

## Step 3: Get Your Credentials

1. Go to **Settings** → **API** in your Supabase dashboard
2. Copy the following values:
   - **Project URL**: Your Supabase project URL (e.g., `https://xxxxx.supabase.co`)
   - **Service Role Key**: Your service_role secret key (anon key won't work for backend operations)

⚠️ **Important**: Use the **service_role** key, NOT the anon/public key. The service role key bypasses RLS policies.

## Step 4: Configure Environment Variables

1. Navigate to your Backend directory
2. Copy `.env.example` to `.env` if you haven't already:
   ```bash
   copy .env.example .env
   ```

3. Edit `.env` and update these values:
   ```env
   # Supabase Storage Configuration
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-service-role-key-here
   SUPABASE_BUCKET_NAME=file-conversions
   USE_SUPABASE_STORAGE=True
   ```

## Step 5: Install Dependencies

Install the Supabase Python SDK:

```bash
# Activate your virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Step 6: Test the Integration

### Start the Application

```bash
# Start Redis (if not using Docker)
docker run -d -p 6379:6379 redis:7-alpine

# Start Celery Worker
celery -A app.celery_app worker --loglevel=info --pool=solo

# Start FastAPI
python -m uvicorn app.main:app --reload
```

### Verify Supabase Connection

Check the health endpoint to verify Supabase is connected:

```bash
curl http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "checks": {
    "storage": "ok",
    "supabase_storage": "ok - connected",
    ...
  }
}
```

### Test File Upload

```bash
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@test.pdf" \
  -F "from_format=pdf" \
  -F "to_format=docx"
```

Check your Supabase Storage dashboard - you should see files appearing in the `file-conversions` bucket under the `uploads/` folder.

## How It Works

### Hybrid Storage Approach

The implementation uses a **hybrid approach**:

1. **Upload**: Files are saved locally first, then uploaded to Supabase
2. **Conversion**: Conversion happens using local files
3. **Output**: Converted files are uploaded to Supabase
4. **Download**: Users download from Supabase via signed URLs
5. **Cleanup**: Old files are removed from both local storage and Supabase

### File Paths in Supabase

```
file-conversions/
├── uploads/
│   └── {job_id}_input.{ext}
└── outputs/
    └── {job_id}_output.{ext}
```

### Signed URLs

When users download files, the API generates signed URLs that expire after 1 hour. This ensures secure, temporary access to files.

## Troubleshooting

### "Supabase storage is not enabled"

- Make sure `USE_SUPABASE_STORAGE=True` in your `.env` file
- Verify your credentials are correct

### "Failed to upload to Supabase"

- Check your service role key (not anon key)
- Verify bucket name matches your configuration
- Ensure bucket exists in Supabase dashboard
- Check bucket policies allow service role access

### "Failed to generate signed URL"

- Verify bucket is created
- Check file exists in Supabase Storage dashboard
- Ensure service role key has proper permissions

### Files not appearing in Supabase

- Check application logs for upload errors
- Verify `USE_SUPABASE_STORAGE=True`
- Ensure credentials are correct in `.env`

## Switching Between Storage Modes

### Disable Supabase (Local Only)

```env
USE_SUPABASE_STORAGE=False
```

The application will work with local storage only.

### Enable Supabase (Hybrid)

```env
USE_SUPABASE_STORAGE=True
```

Files will be stored both locally and in Supabase.

## Production Deployment

For production:

1. Use environment variables (not `.env` file)
2. Keep service role key secret
3. Set up proper bucket policies
4. Consider CDN for faster downloads
5. Monitor storage usage in Supabase dashboard

## Next Steps

- Set up automatic cleanup schedules
- Configure bucket lifecycle policies
- Set up monitoring and alerts
- Consider implementing file compression
- Add analytics for storage usage
