# Testing the File Conversion API (Without Frontend)

## 🌐 Method 1: Interactive API Docs (Easiest!)

Your API has a **built-in web interface** at http://localhost:8000/docs

### How to Use:

1. **Open in browser**: http://localhost:8000/docs
2. **Click on any endpoint** to expand it
3. **Click "Try it out"** button
4. **Fill in the parameters** and upload files
5. **Click "Execute"** to test

---

## 📝 Step-by-Step: Convert a File

### Using the Interactive Docs:

**Step 1: Upload & Convert**
1. Open http://localhost:8000/docs
2. Find `POST /api/convert` endpoint
3. Click **"Try it out"**
4. Click **"Choose File"** and select a file (e.g., a PDF or Word doc)
5. Enter `from_format`: `pdf` (or `docx`, `xlsx`, etc.)
6. Enter `to_format`: `docx` (or `pdf`, `png`, etc.)
7. Click **"Execute"**
8. **Copy the `job_id`** from the response

**Step 2: Check Status**
1. Find `GET /api/status/{job_id}` endpoint
2. Click **"Try it out"**
3. Paste your `job_id` in the field
4. Click **"Execute"**
5. Wait until `status` is `"completed"`

**Step 3: Download File**
1. Find `GET /api/download/{job_id}` endpoint
2. Click **"Try it out"**
3. Paste your `job_id`
4. Click **"Execute"**
5. Click **"Download file"** to save the converted file

---

## 💻 Method 2: Using PowerShell (Command Line)

### Convert PDF to Word:
```powershell
# Step 1: Upload and convert
curl.exe -X POST "http://localhost:8000/api/convert" `
  -F "file=@C:\path\to\your\document.pdf" `
  -F "from_format=pdf" `
  -F "to_format=docx"

# Copy the job_id from response

# Step 2: Check status
curl.exe "http://localhost:8000/api/status/YOUR-JOB-ID-HERE"

# Step 3: Download (opens in browser)
start "http://localhost:8000/api/download/YOUR-JOB-ID-HERE"
```

### Word to PDF:
```powershell
curl.exe -X POST "http://localhost:8000/api/convert" `
  -F "file=@C:\path\to\your\document.docx" `
  -F "from_format=docx" `
  -F "to_format=pdf"
```

### Image to PDF:
```powershell
curl.exe -X POST "http://localhost:8000/api/convert" `
  -F "file=@C:\path\to\your\image.jpg" `
  -F "from_format=jpg" `
  -F "to_format=pdf"
```

---

## 🔧 Method 3: Using Postman

1. **Create New Request** → `POST`
2. **URL**: `http://localhost:8000/api/convert`
3. **Body** → Select `form-data`
4. Add fields:
   - `file` → Type: **File** → Choose your file
   - `from_format` → Type: **Text** → Value: `pdf`
   - `to_format` → Type: **Text** → Value: `docx`
5. **Send** → Copy the `job_id`
6. **New Request**: `GET http://localhost:8000/api/status/{job_id}`
7. **New Request**: `GET http://localhost:8000/api/download/{job_id}`

---

## 🐍 Method 4: Using Python Script

Create a file `test_api.py`:

```python
import requests
import time

# Upload and convert
files = {'file': open('sample.pdf', 'rb')}
data = {'from_format': 'pdf', 'to_format': 'docx'}

response = requests.post('http://localhost:8000/api/convert', files=files, data=data)
job_id = response.json()['job_id']
print(f"Job ID: {job_id}")

# Check status
while True:
    status_response = requests.get(f'http://localhost:8000/api/status/{job_id}')
    status_data = status_response.json()
    print(f"Status: {status_data['status']}")
    
    if status_data['status'] == 'completed':
        break
    elif status_data['status'] == 'failed':
        print(f"Error: {status_data['error']}")
        exit(1)
    
    time.sleep(2)

# Download file
download_response = requests.get(f'http://localhost:8000/api/download/{job_id}')
with open('converted_file.docx', 'wb') as f:
    f.write(download_response.content)
print("File downloaded!")
```

Run it:
```bash
pip install requests
python test_api.py
```

---

## ✅ Supported Conversions

| From Format | To Format | Example |
|-------------|-----------|---------|
| PDF | DOCX (Word) | `from_format=pdf`, `to_format=docx` |
| DOCX (Word) | PDF | `from_format=docx`, `to_format=pdf` |
| XLSX (Excel) | PDF | `from_format=xlsx`, `to_format=pdf` |
| JPG/PNG | PDF | `from_format=jpg`, `to_format=pdf` |
| PDF | PNG/JPG | `from_format=pdf`, `to_format=png` |

---

## 🔍 Health Check

Test if everything is working:

**Browser**: http://localhost:8000/health

**PowerShell**:
```powershell
curl.exe "http://localhost:8000/health"
```

Should return:
```json
{
  "status": "healthy",
  "checks": {
    "storage": "ok",
    "libreoffice": "ok"
  }
}
```

---

## 🎯 Quick Test Files

Create test files in your Backend folder:

**test.txt** (save as .docx):
```
Hello World!
This is a test document for conversion.
```

Then convert it to PDF using any method above!

---

## 💡 Tips

- **Job IDs** are UUIDs like: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
- Files are kept for **24 hours** then auto-deleted
- Max file size: **50 MB** (configurable in `.env`)
- Check logs in terminal to see what's happening

---

## 🐛 Troubleshooting

**"LibreOffice not found"**
- Verify installation: `"C:\Program Files\LibreOffice\program\soffice.exe"`
- Update path in `.env` file if installed elsewhere

**"Conversion failed"**
- Check the file format matches `from_format`
- Check terminal logs for detailed error

**"File too large"**
- Increase `MAX_FILE_SIZE_MB` in `.env`
- Restart server after changing `.env`
