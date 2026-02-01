# AWS EC2 Deployment Guide with S3 Storage

Complete step-by-step guide to deploy your PDF Converter API on AWS EC2 with S3 for file storage.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [AWS Setup](#aws-setup)
3. [S3 Bucket Configuration](#s3-bucket-configuration)
4. [EC2 Instance Setup](#ec2-instance-setup)
5. [Application Deployment](#application-deployment)
6. [Production Configuration](#production-configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Local Requirements
- AWS Account with billing enabled
- AWS CLI installed ([Download](https://aws.amazon.com/cli/))
- SSH client (PuTTY for Windows or OpenSSH)
- Basic knowledge of Linux commands

### AWS Resources You'll Create
- 1 EC2 Instance (t2.medium or larger recommended)
- 1 S3 Bucket for file storage
- 1 IAM Role with S3 access
- 1 Security Group
- 1 Elastic IP (optional but recommended)

---

## AWS Setup

### Step 1: Install and Configure AWS CLI

```bash
# Install AWS CLI (if not already installed)
# Windows: Download from https://aws.amazon.com/cli/

# Configure AWS CLI
aws configure

# Enter your credentials:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: us-east-1  (or your preferred region)
# Default output format: json
```

### Step 2: Create IAM Role for EC2

This role allows your EC2 instance to access S3 without hardcoding credentials.

```bash
# Create trust policy file
cat > ec2-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
  --role-name PDFConverterEC2Role \
  --assume-role-policy-document file://ec2-trust-policy.json

# Create S3 access policy
cat > s3-access-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET-NAME/*",
        "arn:aws:s3:::YOUR-BUCKET-NAME"
      ]
    }
  ]
}
EOF

# Attach policy to role
aws iam put-role-policy \
  --role-name PDFConverterEC2Role \
  --policy-name S3AccessPolicy \
  --policy-document file://s3-access-policy.json

# Create instance profile
aws iam create-instance-profile \
  --instance-profile-name PDFConverterEC2Profile

# Add role to instance profile
aws iam add-role-to-instance-profile \
  --instance-profile-name PDFConverterEC2Profile \
  --role-name PDFConverterEC2Role
```

**Alternative: Using AWS Console**
1. Go to IAM Console → Roles → Create Role
2. Select "AWS Service" → "EC2"
3. Attach policy "AmazonS3FullAccess" (or create custom policy above)
4. Name: `PDFConverterEC2Role`
5. Create role

---

## S3 Bucket Configuration

### Step 1: Create S3 Bucket

```bash
# Replace with your unique bucket name
BUCKET_NAME="pdf-converter-storage-$(date +%s)"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Enable versioning (optional)
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Configure lifecycle rules for automatic cleanup
cat > lifecycle-policy.json <<EOF
{
  "Rules": [
    {
      "Id": "DeleteOldFiles",
      "Status": "Enabled",
      "Prefix": "",
      "Expiration": {
        "Days": 7
      }
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket $BUCKET_NAME \
  --lifecycle-configuration file://lifecycle-policy.json
```

### Step 2: Configure CORS (if accessing from browser)

```bash
cat > cors-config.json <<EOF
{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3000
    }
  ]
}
EOF

aws s3api put-bucket-cors \
  --bucket $BUCKET_NAME \
  --cors-configuration file://cors-config.json
```

### Step 3: Block Public Access (Security)

```bash
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

---

## EC2 Instance Setup

### Step 1: Create Security Group

```bash
# Create security group
aws ec2 create-security-group \
  --group-name pdf-converter-sg \
  --description "Security group for PDF Converter API" \
  --vpc-id vpc-YOUR_VPC_ID

# Allow SSH (port 22)
aws ec2 authorize-security-group-ingress \
  --group-name pdf-converter-sg \
  --protocol tcp \
  --port 22 \
  --cidr 0.0.0.0/0

# Allow HTTP (port 80)
aws ec2 authorize-security-group-ingress \
  --group-name pdf-converter-sg \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

# Allow HTTPS (port 443)
aws ec2 authorize-security-group-ingress \
  --group-name pdf-converter-sg \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Allow Application (port 8000)
aws ec2 authorize-security-group-ingress \
  --group-name pdf-converter-sg \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0

# Allow Redis (port 6379) - only from within VPC
aws ec2 authorize-security-group-ingress \
  --group-name pdf-converter-sg \
  --protocol tcp \
  --port 6379 \
  --source-group pdf-converter-sg

# Allow Flower monitoring (port 5555)
aws ec2 authorize-security-group-ingress \
  --group-name pdf-converter-sg \
  --protocol tcp \
  --port 5555 \
  --cidr 0.0.0.0/0
```

**Using AWS Console:**
1. EC2 Console → Security Groups → Create Security Group
2. Add inbound rules:
   - SSH (22) from My IP
   - HTTP (80) from Anywhere
   - HTTPS (443) from Anywhere
   - Custom TCP (8000) from Anywhere
   - Custom TCP (6379) from Security Group itself
   - Custom TCP (5555) from My IP

### Step 2: Create Key Pair

```bash
# Create SSH key pair
aws ec2 create-key-pair \
  --key-name pdf-converter-key \
  --query 'KeyMaterial' \
  --output text > pdf-converter-key.pem

# Set permissions (Linux/Mac)
chmod 400 pdf-converter-key.pem

# For Windows, use PuTTY to convert .pem to .ppk
```

**Using AWS Console:**
1. EC2 Console → Key Pairs → Create Key Pair
2. Name: `pdf-converter-key`
3. Format: `.pem` (for OpenSSH) or `.ppk` (for PuTTY)
4. Download and save securely

### Step 3: Launch EC2 Instance

**Recommended Instance Type:**
- **Development/Testing:** t2.medium (2 vCPU, 4 GB RAM)
- **Production:** t3.large (2 vCPU, 8 GB RAM) or larger

```bash
# Launch instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --count 1 \
  --instance-type t2.medium \
  --key-name pdf-converter-key \
  --security-groups pdf-converter-sg \
  --iam-instance-profile Name=PDFConverterEC2Profile \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30,"VolumeType":"gp3"}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=PDF-Converter-API}]'
```

**Using AWS Console:**
1. EC2 Console → Launch Instance
2. **Name:** PDF-Converter-API
3. **AMI:** Ubuntu Server 22.04 LTS (Free tier eligible)
4. **Instance Type:** t2.medium
5. **Key Pair:** pdf-converter-key
6. **Network Settings:**
   - Select Security Group: pdf-converter-sg
7. **Configure Storage:** 30 GB gp3
8. **Advanced Details:**
   - IAM Instance Profile: PDFConverterEC2Profile
9. Click "Launch Instance"

### Step 4: Allocate Elastic IP (Optional but Recommended)

```bash
# Allocate Elastic IP
aws ec2 allocate-address --domain vpc

# Note the AllocationId from output
# Associate with instance (replace with your values)
aws ec2 associate-address \
  --instance-id i-1234567890abcdef0 \
  --allocation-id eipalloc-12345678
```

---

## Application Deployment

### Step 1: Connect to EC2 Instance

```bash
# Get instance public IP from AWS Console or CLI
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=PDF-Converter-API" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text

# SSH into instance (Linux/Mac)
ssh -i pdf-converter-key.pem ubuntu@YOUR_INSTANCE_PUBLIC_IP

# For Windows, use PuTTY with .ppk file
```

### Step 2: Update System and Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install system dependencies
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    redis-server \
    poppler-utils \
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    nginx \
    supervisor

# Install Docker (optional, if using Docker deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 3: Configure Redis

```bash
# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG

# Configure Redis for production
sudo nano /etc/redis/redis.conf
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server
```

### Step 4: Clone and Setup Application

```bash
# Create application directory
sudo mkdir -p /opt/pdf-converter
sudo chown ubuntu:ubuntu /opt/pdf-converter
cd /opt/pdf-converter

# Clone your repository (replace with your repo URL)
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .

# Or upload your code using SCP
# scp -i pdf-converter-key.pem -r ./Backend/* ubuntu@YOUR_IP:/opt/pdf-converter/

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install boto3 for AWS S3
pip install boto3

# Create necessary directories
mkdir -p storage/uploads storage/outputs temp
```

### Step 5: Configure Environment Variables

```bash
# Create .env file
cat > .env <<EOF
# Application Settings
APP_NAME=PDF Converter API
APP_VERSION=1.0.0
DEBUG=False

# File Upload Configuration
MAX_FILE_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,doc,xlsx,xls,jpg,jpeg,png

# Storage Configuration
USE_S3_STORAGE=True
AWS_REGION=us-east-1
S3_BUCKET_NAME=$BUCKET_NAME
S3_PRESIGNED_URL_EXPIRATION=3600

# Disable Supabase (we're using S3)
USE_SUPABASE_STORAGE=False
SUPABASE_URL=
SUPABASE_KEY=

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Celery Task Configuration
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_RESULT_EXPIRES=86400

# CORS Origins (update with your frontend URL)
CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com

# LibreOffice Path (Linux)
LIBREOFFICE_PATH=/usr/bin/libreoffice

# File Retention
FILE_RETENTION_HOURS=24
EOF

# Secure the .env file
chmod 600 .env
```

### Step 6: Create S3 Storage Utility

Create a new file for S3 storage handling:

```bash
nano app/utils/s3_storage.py
```

Copy the content from the `s3_storage.py` file that will be created next.

### Step 7: Test the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Test FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, test the health endpoint
curl http://localhost:8000/health

# Stop with Ctrl+C if it works
```

---

## Production Configuration

### Option 1: Using Supervisor (Recommended for Simple Deployments)

#### Step 1: Configure Supervisor for FastAPI

```bash
# Create supervisor config for FastAPI
sudo nano /etc/supervisor/conf.d/pdf-converter-api.conf
```

Add this content:

```ini
[program:pdf-converter-api]
directory=/opt/pdf-converter
command=/opt/pdf-converter/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/pdf-converter/api.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/pdf-converter/venv/bin"
```

#### Step 2: Configure Supervisor for Celery Worker

```bash
sudo nano /etc/supervisor/conf.d/pdf-converter-worker.conf
```

Add this content:

```ini
[program:pdf-converter-worker]
directory=/opt/pdf-converter
command=/opt/pdf-converter/venv/bin/celery -A app.celery_app worker --loglevel=info --concurrency=4
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/pdf-converter/worker.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/pdf-converter/venv/bin"
stopwaitsecs=600
```

#### Step 3: Configure Supervisor for Flower (Optional Monitoring)

```bash
sudo nano /etc/supervisor/conf.d/pdf-converter-flower.conf
```

Add this content:

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

#### Step 4: Start Services

```bash
# Create log directory
sudo mkdir -p /var/log/pdf-converter
sudo chown ubuntu:ubuntu /var/log/pdf-converter

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Start all services
sudo supervisorctl start pdf-converter-api
sudo supervisorctl start pdf-converter-worker
sudo supervisorctl start pdf-converter-flower

# Check status
sudo supervisorctl status

# View logs
sudo supervisorctl tail -f pdf-converter-api
```

### Option 2: Using Docker (Recommended for Production)

```bash
# Make sure you're in the application directory
cd /opt/pdf-converter

# Create production docker-compose override
cat > docker-compose.prod.yml <<EOF
version: '3.8'

services:
  fastapi:
    environment:
      - USE_S3_STORAGE=True
      - AWS_REGION=us-east-1
      - S3_BUCKET_NAME=$BUCKET_NAME
    restart: always

  celery-worker:
    environment:
      - USE_S3_STORAGE=True
      - AWS_REGION=us-east-1
      - S3_BUCKET_NAME=$BUCKET_NAME
    restart: always
    deploy:
      replicas: 2

  flower:
    restart: always
EOF

# Build and start containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Configure Nginx as Reverse Proxy

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/pdf-converter
```

Add this content:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

upstream fastapi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;  # Replace with your domain or public IP

    client_max_body_size 100M;
    
    # API endpoints
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long conversions
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }

    # Flower monitoring (optional, restrict access)
    location /flower/ {
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        
        proxy_pass http://127.0.0.1:5555/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable the site and restart Nginx:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/pdf-converter /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Create password for Flower (optional)
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Setup SSL with Let's Encrypt (Production Only)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal is set up automatically
# Test renewal
sudo certbot renew --dry-run
```

---

## Monitoring & Maintenance

### System Monitoring

```bash
# Check service status
sudo supervisorctl status

# Or for Docker
docker-compose ps

# Check Redis
redis-cli info stats

# Check disk usage
df -h

# Check memory usage
free -h

# Check CPU usage
htop
```

### Application Logs

```bash
# Supervisor logs
sudo supervisorctl tail -f pdf-converter-api
sudo supervisorctl tail -f pdf-converter-worker

# Docker logs
docker-compose logs -f fastapi
docker-compose logs -f celery-worker

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Flower Monitoring Dashboard

Access Flower at: `http://YOUR_IP:5555` or `http://YOUR_DOMAIN/flower/`

### CloudWatch Integration (Optional)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# Start CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json
```

### S3 Storage Monitoring

```bash
# Check bucket size
aws s3 ls s3://$BUCKET_NAME --recursive --human-readable --summarize

# List recent files
aws s3 ls s3://$BUCKET_NAME/uploads/ --human-readable

# Monitor S3 costs
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --filter file://s3-filter.json
```

### Automated Backups

```bash
# Create backup script
cat > /opt/pdf-converter/backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/opt/pdf-converter/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Redis
redis-cli SAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup application code
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /opt/pdf-converter \
  --exclude='/opt/pdf-converter/venv' \
  --exclude='/opt/pdf-converter/storage' \
  --exclude='/opt/pdf-converter/backups'

# Upload to S3
aws s3 cp $BACKUP_DIR/redis_$DATE.rdb s3://$BUCKET_NAME/backups/
aws s3 cp $BACKUP_DIR/app_$DATE.tar.gz s3://$BUCKET_NAME/backups/

# Clean old local backups (keep last 7 days)
find $BACKUP_DIR -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/pdf-converter/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/pdf-converter/backup.sh >> /var/log/pdf-converter/backup.log 2>&1") | crontab -
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo supervisorctl tail -f pdf-converter-api stderr

# Check if port is already in use
sudo lsof -i :8000

# Test manually
cd /opt/pdf-converter
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Celery Worker Issues

```bash
# Check worker status
celery -A app.celery_app inspect active

# Purge all tasks
celery -A app.celery_app purge

# Restart worker
sudo supervisorctl restart pdf-converter-worker
```

### S3 Access Issues

```bash
# Verify IAM role is attached
aws ec2 describe-instances --instance-ids i-YOUR_INSTANCE_ID \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'

# Test S3 access from EC2
aws s3 ls s3://$BUCKET_NAME

# Check S3 permissions
aws s3api get-bucket-policy --bucket $BUCKET_NAME
```

### High Memory Usage

```bash
# Check memory
free -h

# Find memory-hogging processes
ps aux --sort=-%mem | head -n 10

# Restart services
sudo supervisorctl restart all

# Or for Docker
docker-compose restart
```

### Redis Connection Issues

```bash
# Check Redis status
sudo systemctl status redis-server

# Test connection
redis-cli ping

# Check Redis connections
redis-cli CLIENT LIST

# Restart Redis
sudo systemctl restart redis-server
```

### LibreOffice Conversion Failures

```bash
# Test LibreOffice
libreoffice --headless --convert-to pdf test.docx --outdir /tmp

# Check if LibreOffice is installed
which libreoffice

# Reinstall if needed
sudo apt install --reinstall libreoffice-writer libreoffice-calc
```

---

## Performance Optimization

### 1. Increase Worker Concurrency

```bash
# Edit worker config
sudo nano /etc/supervisor/conf.d/pdf-converter-worker.conf

# Increase concurrency based on CPU cores
# command=.../celery -A app.celery_app worker --concurrency=8

# Restart
sudo supervisorctl restart pdf-converter-worker
```

### 2. Enable Nginx Caching

Add to Nginx config:

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g;
proxy_cache api_cache;
proxy_cache_valid 200 5m;
```

### 3. Use Elasticache Redis (Production)

Replace local Redis with AWS Elasticache for better performance and reliability.

### 4. Auto Scaling

Set up Auto Scaling Group for multiple EC2 instances with Load Balancer.

---

## Cost Optimization

### EC2 Costs
- Use **Reserved Instances** for 1-3 year commitments (up to 75% savings)
- Use **Spot Instances** for worker nodes (up to 90% savings)
- Stop instances during non-business hours if applicable

### S3 Costs
- Use **S3 Lifecycle Policies** to delete old files automatically
- Use **S3 Intelligent-Tiering** for automatic cost optimization
- Monitor and set up **S3 Budget Alerts**

### Estimated Monthly Costs (us-east-1)
- EC2 t2.medium (24/7): ~$33/month
- EBS 30GB gp3: ~$2.40/month
- S3 Storage (100GB): ~$2.30/month
- Data Transfer (100GB): ~$9/month
- **Total: ~$47/month**

---

## Security Checklist

- [ ] SSH access limited to specific IPs
- [ ] Strong SSH key pair generated and secured
- [ ] S3 bucket not publicly accessible
- [ ] IAM role with least privilege access
- [ ] Environment variables secured (.env file permissions)
- [ ] SSL/TLS certificate installed (HTTPS)
- [ ] Nginx rate limiting enabled
- [ ] Flower monitoring password protected
- [ ] Regular system updates scheduled
- [ ] CloudWatch monitoring enabled
- [ ] Backup strategy implemented
- [ ] Security group rules minimized

---

## Quick Reference Commands

```bash
# Start all services
sudo supervisorctl start all

# Stop all services
sudo supervisorctl stop all

# Restart all services
sudo supervisorctl restart all

# View API logs
sudo supervisorctl tail -f pdf-converter-api

# View worker logs
sudo supervisorctl tail -f pdf-converter-worker

# Check Redis
redis-cli ping

# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# View S3 files
aws s3 ls s3://$BUCKET_NAME/uploads/

# Clean old temp files
find /opt/pdf-converter/temp -mtime +1 -delete
```

---

## Testing the Deployment

### 1. Test Health Endpoint

```bash
curl http://YOUR_IP/health
# or
curl https://your-domain.com/health
```

### 2. Test File Upload and Conversion

```bash
# Upload a test file
curl -X POST "http://YOUR_IP/api/convert" \
  -F "file=@test.pdf" \
  -F "to_format=docx"

# Check job status
curl "http://YOUR_IP/api/job/{job_id}/status"

# Download result
curl "http://YOUR_IP/api/job/{job_id}/download" -o result.docx
```

### 3. Monitor with Flower

Visit: `http://YOUR_IP:5555` or `http://YOUR_DOMAIN/flower/`

---

## Next Steps

1. **Set up Domain Name**: Configure Route 53 or your DNS provider
2. **Enable HTTPS**: Install SSL certificate with Let's Encrypt
3. **Set up Monitoring**: Configure CloudWatch alarms
4. **Implement CI/CD**: Use GitHub Actions for automated deployments
5. **Load Testing**: Test with Apache Bench or Locust
6. **Backup Strategy**: Verify automated backups are working
7. **Documentation**: Document your specific deployment configuration

---

## Support & Resources

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)

---

**Deployment Date:** _____________  
**Deployed By:** _____________  
**Instance ID:** _____________  
**Bucket Name:** _____________  
**Domain:** _____________
