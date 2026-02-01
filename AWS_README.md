# AWS EC2 with S3 Storage - Deployment Summary

## Overview

This guide provides complete instructions for deploying your PDF Converter API on AWS EC2 using S3 for file storage.

---

## What You'll Build

```
┌─────────────────────────────────────────────────────┐
│                   AWS Cloud                          │
│                                                      │
│  ┌──────────────────────────────────────────┐      │
│  │          EC2 Instance (Ubuntu)           │      │
│  │                                           │      │
│  │  ┌─────────────────────────────────┐    │      │
│  │  │      Nginx (Reverse Proxy)      │    │      │
│  │  │      Port 80/443 → 8000         │    │      │
│  │  └─────────────────────────────────┘    │      │
│  │                                           │      │
│  │  ┌─────────────────────────────────┐    │      │
│  │  │  FastAPI App (uvicorn)          │    │      │
│  │  │  - File Upload/Download         │    │      │
│  │  │  - Conversion Management        │◄───┼──────┼─── Users
│  │  └─────────────────────────────────┘    │      │
│  │                                           │      │
│  │  ┌─────────────────────────────────┐    │      │
│  │  │  Celery Workers (4 concurrent)  │    │      │
│  │  │  - PDF to Word                  │    │      │
│  │  │  - Word to PDF                  │    │      │
│  │  │  - Excel to PDF                 │    │      │
│  │  │  - Image conversions            │    │      │
│  │  └─────────────────────────────────┘    │      │
│  │                                           │      │
│  │  ┌─────────────────────────────────┐    │      │
│  │  │  Redis (Message Broker)         │    │      │
│  │  │  - Task Queue                   │    │      │
│  │  │  - Result Backend               │    │      │
│  │  └─────────────────────────────────┘    │      │
│  │                                           │      │
│  │  ┌─────────────────────────────────┐    │      │
│  │  │  Flower (Monitoring)            │    │      │
│  │  │  Port 5555                      │    │      │
│  │  └─────────────────────────────────┘    │      │
│  │                                           │      │
│  │  ┌─────────────────────────────────┐    │      │
│  │  │  LibreOffice (Headless)         │    │      │
│  │  │  - Document Conversion Engine   │    │      │
│  │  └─────────────────────────────────┘    │      │
│  │                                           │      │
│  └───────────────┬───────────────────────────┘      │
│                  │                                   │
│                  │ IAM Role                          │
│                  │ (S3 Access)                       │
│                  ▼                                   │
│  ┌──────────────────────────────────────────┐      │
│  │         S3 Bucket                         │      │
│  │  - uploads/ (input files)                │      │
│  │  - outputs/ (converted files)            │      │
│  │  - backups/ (system backups)             │      │
│  │  - Lifecycle: Auto-delete after 7 days   │      │
│  └──────────────────────────────────────────┘      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start (TL;DR)

If you're experienced with AWS, here's the condensed version:

```bash
# 1. Create S3 Bucket
aws s3 mb s3://pdf-converter-$(date +%s) --region us-east-1

# 2. Create IAM Role with S3 permissions
# (Use AWS Console or see full guide)

# 3. Launch EC2 (t2.medium, Ubuntu 22.04, attach IAM role)
# (Use AWS Console)

# 4. SSH to EC2 and install dependencies
ssh ubuntu@YOUR_IP
sudo apt update && sudo apt install -y python3.11 python3.11-venv \
  redis-server libreoffice poppler-utils nginx supervisor

# 5. Deploy application
cd /opt/pdf-converter
git clone YOUR_REPO .
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Configure .env with S3 settings
# USE_S3_STORAGE=True
# S3_BUCKET_NAME=your-bucket

# 7. Setup Supervisor and Nginx (see configs in guide)

# 8. Start services
sudo supervisorctl start all
```

---

## Complete Documentation

### 📘 Main Guides

1. **[AWS_EC2_DEPLOYMENT_GUIDE.md](AWS_EC2_DEPLOYMENT_GUIDE.md)** - Complete step-by-step deployment guide
   - AWS account setup
   - S3 bucket configuration
   - EC2 instance setup
   - Application deployment
   - Production configuration
   - Monitoring and maintenance

2. **[AWS_EC2_QUICK_REFERENCE.md](AWS_EC2_QUICK_REFERENCE.md)** - Quick commands and troubleshooting
   - Common commands
   - Service management
   - Logs viewing
   - Testing procedures
   - Quick fixes

3. **[AWS_DEPLOYMENT_CHECKLIST.md](AWS_DEPLOYMENT_CHECKLIST.md)** - Step-by-step checklist
   - Pre-deployment tasks
   - Installation verification
   - Testing checklist
   - Security checklist
   - Post-deployment tasks

### 📝 Configuration Files

1. **[.env.example](.env.example)** - Environment configuration template
   - S3 settings
   - Application settings
   - Deployment-specific notes

2. **[app/utils/s3_storage.py](app/utils/s3_storage.py)** - S3 storage implementation
   - Upload/download files
   - Presigned URLs
   - File management

---

## Key Features of This Deployment

### ✅ Advantages

- **Scalable**: Easy to scale horizontally with more EC2 instances
- **Cost-Effective**: Pay only for what you use
- **Reliable**: S3 provides 99.999999999% durability
- **Secure**: IAM roles eliminate hardcoded credentials
- **Automatic**: Files auto-delete after 7 days
- **Monitored**: Flower dashboard for worker monitoring
- **Production-Ready**: Nginx, Supervisor, SSL support

### 🔧 Architecture Benefits

1. **Separation of Concerns**
   - FastAPI: API endpoints
   - Celery: Background processing
   - Redis: Message queue
   - S3: File storage
   - Nginx: Reverse proxy

2. **Fault Tolerance**
   - Supervisor auto-restarts failed services
   - Redis persists task queue
   - S3 versioning available
   - Multiple Celery workers

3. **Security**
   - No credentials in code
   - IAM role-based access
   - Private S3 bucket
   - Presigned URLs for downloads
   - Rate limiting in Nginx

---

## Deployment Options

### Option 1: Manual Deployment (Recommended for Learning)
- Follow the full deployment guide step-by-step
- Understand each component
- Best for: First-time deployment, learning AWS

### Option 2: Quick Deployment (For Experienced Users)
- Use quick reference commands
- Skip detailed explanations
- Best for: Experienced AWS users, redeployment

### Option 3: Docker Deployment (Alternative)
- Use docker-compose on EC2
- Simpler container management
- Best for: Containerized workflows

---

## Cost Breakdown

### Monthly Costs (Estimated - us-east-1)

| Service | Specification | Monthly Cost |
|---------|--------------|--------------|
| EC2 Instance | t2.medium (24/7) | $33.00 |
| EBS Storage | 30GB gp3 | $2.40 |
| S3 Storage | 100GB | $2.30 |
| S3 Requests | 1M PUT, 10M GET | $0.50 |
| Data Transfer | 100GB out | $9.00 |
| **Total** | | **~$47/month** |

### Cost Optimization Tips

1. **Use Reserved Instances**: Save up to 75%
2. **Stop EC2 off-hours**: Save 50% if not 24/7
3. **S3 Lifecycle Policies**: Auto-delete old files
4. **Elastic IP**: Free when attached to running instance
5. **CloudFront CDN**: Reduce data transfer costs (optional)

---

## Prerequisites

### Required Knowledge
- Basic Linux command line
- SSH connections
- Environment variables
- Basic networking concepts

### Required Accounts
- AWS account with billing enabled
- Domain name (optional, for SSL)

### Local Tools
- AWS CLI
- SSH client
- Text editor

---

## Step-by-Step Deployment Flow

```
1. AWS Setup (30 min)
   ├── Create AWS account
   ├── Install AWS CLI
   ├── Configure credentials
   └── Select region

2. S3 Configuration (15 min)
   ├── Create bucket
   ├── Configure lifecycle rules
   ├── Set up CORS
   └── Test access

3. IAM Setup (20 min)
   ├── Create IAM role
   ├── Attach S3 policy
   ├── Create instance profile
   └── Verify permissions

4. EC2 Launch (30 min)
   ├── Create security group
   ├── Create key pair
   ├── Launch instance
   ├── Attach IAM role
   └── Allocate Elastic IP

5. System Setup (45 min)
   ├── Connect via SSH
   ├── Update system
   ├── Install Python 3.11
   ├── Install Redis
   ├── Install LibreOffice
   ├── Install Nginx
   └── Install Supervisor

6. Application Deployment (30 min)
   ├── Clone/upload code
   ├── Create virtual environment
   ├── Install dependencies
   ├── Configure .env
   └── Test S3 access

7. Process Management (30 min)
   ├── Configure Supervisor
   ├── Start API service
   ├── Start Celery workers
   ├── Start Flower
   └── Verify all services

8. Nginx Setup (20 min)
   ├── Configure reverse proxy
   ├── Set up rate limiting
   ├── Enable site
   └── Test access

9. Testing (30 min)
   ├── Health check
   ├── Upload test
   ├── Conversion test
   ├── S3 verification
   └── Performance test

10. Production Setup (optional, 60 min)
    ├── Configure domain
    ├── Install SSL certificate
    ├── Set up monitoring
    ├── Configure backups
    └── Enable auto-scaling

Total Time: 4-6 hours (first deployment)
```

---

## Supported Conversions

| From | To | Status |
|------|-----|--------|
| PDF | DOCX | ✅ Supported |
| DOCX | PDF | ✅ Supported |
| XLSX | PDF | ✅ Supported |
| JPG/PNG | PDF | ✅ Supported |
| PDF | PNG | ✅ Supported |

---

## API Endpoints

```
GET  /health                          - Health check
POST /api/convert                     - Upload & convert file
GET  /api/job/{job_id}/status        - Get job status
GET  /api/job/{job_id}/download      - Download result
GET  /docs                            - API documentation
GET  /flower/                         - Worker monitoring
```

---

## Environment Variables Reference

### Required for EC2 + S3 Deployment

```bash
# Enable S3
USE_S3_STORAGE=True

# S3 Configuration
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# Disable Supabase
USE_SUPABASE_STORAGE=False

# Redis
REDIS_URL=redis://localhost:6379/0

# Production Mode
DEBUG=False

# LibreOffice (Linux)
LIBREOFFICE_PATH=/usr/bin/libreoffice
```

---

## Common Issues & Solutions

### Issue: S3 Access Denied
**Solution**: Verify IAM role is attached to EC2 instance
```bash
aws sts get-caller-identity
aws s3 ls s3://your-bucket
```

### Issue: Application Won't Start
**Solution**: Check logs and Python dependencies
```bash
sudo supervisorctl tail -f pdf-converter-api stderr
```

### Issue: Conversion Fails
**Solution**: Verify LibreOffice is installed
```bash
libreoffice --version
which libreoffice
```

### Issue: Redis Connection Failed
**Solution**: Restart Redis service
```bash
sudo systemctl restart redis-server
redis-cli ping
```

---

## Security Best Practices

1. **SSH Access**: Limit to specific IPs
2. **S3 Bucket**: Block public access
3. **IAM Permissions**: Least privilege principle
4. **Credentials**: Never hardcode in code
5. **SSL/HTTPS**: Always use in production
6. **Firewall**: Minimal port exposure
7. **Updates**: Regular security patches
8. **Monitoring**: CloudWatch alarms
9. **Backups**: Regular and tested
10. **Passwords**: Strong and rotated

---

## Performance Tuning

### Recommended Settings

**EC2 Instance Type by Load:**
- Light (<10 conversions/min): t2.medium
- Medium (10-50 conversions/min): t3.large
- Heavy (>50 conversions/min): c5.xlarge

**Celery Workers:**
- CPU cores × 2 = concurrency
- Example: 2 vCPU → 4 workers

**Redis Memory:**
- Small: 256MB
- Medium: 512MB
- Large: 1GB+

**Nginx Workers:**
- worker_processes auto;
- worker_connections 1024;

---

## Monitoring Checklist

### Daily Monitoring
- [ ] Check service status
- [ ] Review error logs
- [ ] Monitor disk space
- [ ] Verify backups

### Weekly Monitoring
- [ ] CloudWatch metrics
- [ ] S3 storage costs
- [ ] Conversion statistics
- [ ] Security audit

### Monthly Monitoring
- [ ] Cost analysis
- [ ] Performance review
- [ ] Dependency updates
- [ ] Backup restoration test

---

## Next Steps After Deployment

1. **Set up Domain**: Configure DNS for your EC2 IP
2. **Enable HTTPS**: Install SSL certificate with Let's Encrypt
3. **Configure Monitoring**: Set up CloudWatch alarms
4. **Set up CI/CD**: Automate deployments with GitHub Actions
5. **Load Testing**: Verify performance with expected traffic
6. **Documentation**: Document your specific configuration
7. **User Training**: Train users on the API

---

## Support Resources

### Documentation
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Celery Documentation](https://docs.celeryproject.org/)

### AWS Support
- AWS Support Center: https://console.aws.amazon.com/support/
- AWS Free Tier: https://aws.amazon.com/free/
- AWS Calculator: https://calculator.aws/

### Community
- Stack Overflow: Tag with `aws-ec2`, `aws-s3`, `fastapi`
- GitHub Issues: (your repository)

---

## Troubleshooting Resources

1. Check application logs: `sudo supervisorctl tail -f pdf-converter-api`
2. Check worker logs: `sudo supervisorctl tail -f pdf-converter-worker`
3. Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
4. Test S3 access: `aws s3 ls s3://your-bucket`
5. Test Redis: `redis-cli ping`
6. Review full guide: `AWS_EC2_DEPLOYMENT_GUIDE.md`
7. Use checklist: `AWS_DEPLOYMENT_CHECKLIST.md`

---

## Files Created for AWS Deployment

1. `AWS_EC2_DEPLOYMENT_GUIDE.md` - Complete deployment guide
2. `AWS_EC2_QUICK_REFERENCE.md` - Quick commands reference
3. `AWS_DEPLOYMENT_CHECKLIST.md` - Deployment checklist
4. `app/utils/s3_storage.py` - S3 storage implementation
5. `.env.example` - Updated with S3 configuration
6. `requirements.txt` - Updated with boto3

---

## Version History

- **v1.0.0** - Initial AWS EC2 + S3 deployment guide
- S3 storage integration
- Comprehensive documentation
- Production-ready configuration

---

## License & Credits

- Application: (Your License)
- AWS: Pay-as-you-go pricing
- Open Source Dependencies: See requirements.txt

---

## Getting Help

If you encounter issues during deployment:

1. **Check the full guide**: `AWS_EC2_DEPLOYMENT_GUIDE.md`
2. **Use the checklist**: `AWS_DEPLOYMENT_CHECKLIST.md`
3. **Review quick reference**: `AWS_EC2_QUICK_REFERENCE.md`
4. **Check logs**: See logging section in guides
5. **AWS Support**: Use AWS Support Center
6. **Community**: Stack Overflow, GitHub Issues

---

**Happy Deploying! 🚀**

Remember: The first deployment takes time, but subsequent updates are much faster. Take it step-by-step and verify each component before moving to the next.
