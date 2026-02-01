# AWS EC2 Quick Reference

This is a quick reference guide for deploying and managing the PDF Converter API on AWS EC2 with S3 storage.

---

## Prerequisites Checklist

- [ ] AWS Account created
- [ ] AWS CLI installed and configured
- [ ] SSH key pair created
- [ ] S3 bucket created
- [ ] IAM role with S3 permissions created
- [ ] EC2 instance launched

---

## One-Command Setup Summary

### 1. Create S3 Bucket
```bash
BUCKET_NAME="pdf-converter-storage-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME --region us-east-1
echo "Bucket created: $BUCKET_NAME"
```

### 2. Launch EC2 Instance
Use AWS Console or:
```bash
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --count 1 \
  --instance-type t2.medium \
  --key-name pdf-converter-key \
  --security-groups pdf-converter-sg \
  --iam-instance-profile Name=PDFConverterEC2Profile
```

### 3. Connect to EC2
```bash
# Get instance IP
INSTANCE_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=PDF-Converter-API" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

# SSH connect
ssh -i pdf-converter-key.pem ubuntu@$INSTANCE_IP
```

### 4. Install Dependencies on EC2
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install everything in one command
sudo apt install -y \
  python3.11 python3.11-venv python3.11-dev python3-pip \
  build-essential git curl wget redis-server \
  poppler-utils libreoffice libreoffice-writer libreoffice-calc \
  nginx supervisor

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 5. Deploy Application
```bash
# Clone and setup
sudo mkdir -p /opt/pdf-converter
sudo chown ubuntu:ubuntu /opt/pdf-converter
cd /opt/pdf-converter

# Upload your code or clone from Git
# git clone YOUR_REPO_URL .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file (see below for template)
nano .env

# Create directories
mkdir -p storage/uploads storage/outputs temp
```

### 6. Start Services
```bash
# Using Supervisor (copy config files first)
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# Or manually for testing
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
celery -A app.celery_app worker --loglevel=info &
celery -A app.celery_app flower --port=5555 &
```

---

## Environment Variables (.env)

Create `/opt/pdf-converter/.env`:

```bash
# Application
APP_NAME=PDF Converter API
DEBUG=False

# AWS S3 Configuration
USE_S3_STORAGE=True
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name-here
S3_PRESIGNED_URL_EXPIRATION=3600

# Disable Supabase
USE_SUPABASE_STORAGE=False

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS (update with your frontend URL)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# File Settings
MAX_FILE_SIZE_MB=50
FILE_RETENTION_HOURS=24

# LibreOffice
LIBREOFFICE_PATH=/usr/bin/libreoffice
```

---

## Supervisor Configuration Files

### API Service
`/etc/supervisor/conf.d/pdf-converter-api.conf`:
```ini
[program:pdf-converter-api]
directory=/opt/pdf-converter
command=/opt/pdf-converter/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/pdf-converter/api.log
environment=PATH="/opt/pdf-converter/venv/bin"
```

### Celery Worker
`/etc/supervisor/conf.d/pdf-converter-worker.conf`:
```ini
[program:pdf-converter-worker]
directory=/opt/pdf-converter
command=/opt/pdf-converter/venv/bin/celery -A app.celery_app worker --loglevel=info --concurrency=4
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/pdf-converter/worker.log
environment=PATH="/opt/pdf-converter/venv/bin"
stopwaitsecs=600
```

### Flower Monitoring
`/etc/supervisor/conf.d/pdf-converter-flower.conf`:
```ini
[program:pdf-converter-flower]
directory=/opt/pdf-converter
command=/opt/pdf-converter/venv/bin/celery -A app.celery_app flower --port=5555
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/pdf-converter/flower.log
environment=PATH="/opt/pdf-converter/venv/bin"
```

---

## Nginx Configuration

`/etc/nginx/sites-available/pdf-converter`:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

upstream fastapi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name YOUR_IP_OR_DOMAIN;
    client_max_body_size 100M;
    
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/pdf-converter /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## Common Commands

### Service Management
```bash
# Check status
sudo supervisorctl status

# Start all services
sudo supervisorctl start all

# Stop all services
sudo supervisorctl stop all

# Restart all services
sudo supervisorctl restart all

# Restart individual service
sudo supervisorctl restart pdf-converter-api
```

### Logs
```bash
# View API logs
sudo supervisorctl tail -f pdf-converter-api

# View worker logs
sudo supervisorctl tail -f pdf-converter-worker

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Redis
```bash
# Check Redis status
redis-cli ping

# Monitor Redis
redis-cli monitor

# Check memory usage
redis-cli info memory
```

### S3 Operations
```bash
# List bucket contents
aws s3 ls s3://YOUR-BUCKET-NAME/

# Check bucket size
aws s3 ls s3://YOUR-BUCKET-NAME --recursive --summarize --human-readable

# Download a file
aws s3 cp s3://YOUR-BUCKET-NAME/outputs/file.pdf ./

# Delete old files (manual cleanup)
aws s3 rm s3://YOUR-BUCKET-NAME/uploads/ --recursive
```

### System Monitoring
```bash
# Check disk space
df -h

# Check memory
free -h

# Check CPU
htop

# Check running processes
ps aux | grep python
```

---

## Testing the API

### Health Check
```bash
curl http://YOUR_IP/health
```

### Upload and Convert
```bash
# Convert PDF to Word
curl -X POST "http://YOUR_IP/api/convert" \
  -F "file=@test.pdf" \
  -F "to_format=docx"

# Response will include job_id
# {"job_id": "abc-123-def", "status": "pending", ...}
```

### Check Job Status
```bash
curl "http://YOUR_IP/api/job/{job_id}/status"
```

### Download Result
```bash
curl "http://YOUR_IP/api/job/{job_id}/download" -o result.docx
```

---

## Troubleshooting Quick Fixes

### Application won't start
```bash
# Check logs
sudo supervisorctl tail pdf-converter-api stderr

# Test manually
cd /opt/pdf-converter
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### S3 permission denied
```bash
# Check IAM role
aws sts get-caller-identity

# Test S3 access
aws s3 ls s3://YOUR-BUCKET-NAME
```

### Redis connection failed
```bash
# Restart Redis
sudo systemctl restart redis-server

# Check Redis
redis-cli ping
```

### High memory usage
```bash
# Find memory hogs
ps aux --sort=-%mem | head -10

# Restart services
sudo supervisorctl restart all
```

### Port already in use
```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 PID
```

---

## Security Checklist

- [ ] SSH key permissions set to 400
- [ ] Security group allows only necessary ports
- [ ] S3 bucket not publicly accessible
- [ ] .env file permissions set to 600
- [ ] Nginx rate limiting enabled
- [ ] Flower protected with password
- [ ] SSL certificate installed (production)
- [ ] Firewall configured
- [ ] Regular backups scheduled

---

## Performance Tuning

### Increase Celery Workers
```bash
# Edit worker config
sudo nano /etc/supervisor/conf.d/pdf-converter-worker.conf

# Change concurrency (based on CPU cores)
# --concurrency=8

# Restart
sudo supervisorctl restart pdf-converter-worker
```

### Optimize Redis
```bash
sudo nano /etc/redis/redis.conf

# Set max memory
maxmemory 512mb
maxmemory-policy allkeys-lru

# Restart
sudo systemctl restart redis-server
```

### Scale Horizontally
- Add more EC2 instances
- Use Application Load Balancer
- Use ElastiCache Redis instead of local Redis

---

## Backup Script

Create `/opt/pdf-converter/backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/pdf-converter/backups"
mkdir -p $BACKUP_DIR

# Backup Redis
redis-cli SAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup code
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /opt/pdf-converter \
  --exclude='venv' --exclude='storage' --exclude='backups'

# Upload to S3
aws s3 cp $BACKUP_DIR/redis_$DATE.rdb s3://YOUR-BUCKET/backups/
aws s3 cp $BACKUP_DIR/app_$DATE.tar.gz s3://YOUR-BUCKET/backups/

# Clean old local backups
find $BACKUP_DIR -mtime +7 -delete
```

Schedule daily:
```bash
chmod +x /opt/pdf-converter/backup.sh
(crontab -l; echo "0 2 * * * /opt/pdf-converter/backup.sh") | crontab -
```

---

## Cost Estimation (Monthly)

| Service | Configuration | Cost |
|---------|--------------|------|
| EC2 t2.medium | 24/7 running | ~$33 |
| EBS 30GB gp3 | Storage | ~$2.40 |
| S3 Storage | 100GB | ~$2.30 |
| Data Transfer | 100GB out | ~$9 |
| **Total** | | **~$47** |

💡 **Save costs:**
- Use Reserved Instances (up to 75% off)
- Stop instance during off-hours
- Enable S3 lifecycle policies
- Use Spot Instances for workers

---

## URLs After Deployment

- **API**: `http://YOUR_IP:8000`
- **API Docs**: `http://YOUR_IP:8000/docs`
- **Health Check**: `http://YOUR_IP:8000/health`
- **Flower**: `http://YOUR_IP:5555`
- **With Nginx**: `http://YOUR_IP/`

---

## Next Steps After Deployment

1. **Domain Setup**: Point domain to Elastic IP
2. **SSL Certificate**: Install Let's Encrypt SSL
3. **Monitoring**: Set up CloudWatch alarms
4. **Auto Scaling**: Configure ASG for high traffic
5. **CI/CD**: Set up GitHub Actions deployment
6. **Load Testing**: Test with expected traffic
7. **Documentation**: Document your configuration

---

## Support Resources

- Full Guide: `AWS_EC2_DEPLOYMENT_GUIDE.md`
- AWS EC2 Docs: https://docs.aws.amazon.com/ec2/
- AWS S3 Docs: https://docs.aws.amazon.com/s3/
- FastAPI Docs: https://fastapi.tiangolo.com/
- Celery Docs: https://docs.celeryproject.org/

---

**Quick Tip**: Bookmark this page and keep your instance ID, bucket name, and Elastic IP handy!
