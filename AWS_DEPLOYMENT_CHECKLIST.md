# AWS EC2 Deployment Checklist

Use this checklist to ensure you complete all necessary steps for deploying your PDF Converter API on AWS EC2 with S3 storage.

---

## Pre-Deployment (AWS Setup)

### AWS Account Setup
- [ ] AWS account created and verified
- [ ] Billing configured and budget alerts set
- [ ] AWS CLI installed on your local machine
- [ ] AWS CLI configured with access keys (`aws configure`)
- [ ] AWS region selected (e.g., us-east-1)

### S3 Bucket Creation
- [ ] S3 bucket created with unique name
- [ ] Bucket region matches EC2 region
- [ ] S3 versioning enabled (optional)
- [ ] S3 lifecycle policy configured for auto-cleanup
- [ ] CORS configured (if needed for browser access)
- [ ] Public access blocked for security
- [ ] Bucket name recorded: `________________`

### IAM Configuration
- [ ] IAM role created: `PDFConverterEC2Role`
- [ ] S3 access policy attached to role
- [ ] Instance profile created: `PDFConverterEC2Profile`
- [ ] Role ARN recorded: `________________`

### Security Group Setup
- [ ] Security group created: `pdf-converter-sg`
- [ ] Inbound rules configured:
  - [ ] SSH (22) - from My IP only
  - [ ] HTTP (80) - from anywhere
  - [ ] HTTPS (443) - from anywhere
  - [ ] Application (8000) - from anywhere (or specific IPs)
  - [ ] Redis (6379) - from security group itself
  - [ ] Flower (5555) - from My IP only
- [ ] Security group ID recorded: `________________`

### SSH Key Pair
- [ ] Key pair created: `pdf-converter-key`
- [ ] Private key downloaded (.pem file)
- [ ] Key file permissions set to 400 (chmod 400 on Linux/Mac)
- [ ] Key file backed up securely
- [ ] Key file location: `________________`

---

## EC2 Instance Setup

### Instance Launch
- [ ] EC2 instance launched
- [ ] Instance type: t2.medium (or larger)
- [ ] AMI: Ubuntu Server 22.04 LTS
- [ ] Storage: 30GB gp3 EBS
- [ ] IAM role attached: PDFConverterEC2Profile
- [ ] Security group attached: pdf-converter-sg
- [ ] Tags added (Name: PDF-Converter-API)
- [ ] Instance ID recorded: `________________`
- [ ] Public IP recorded: `________________`

### Elastic IP (Optional but Recommended)
- [ ] Elastic IP allocated
- [ ] Elastic IP associated with instance
- [ ] Elastic IP recorded: `________________`
- [ ] DNS A record updated (if using domain)

### First Connection
- [ ] Successfully connected via SSH
- [ ] System updated (`sudo apt update && sudo apt upgrade`)
- [ ] Timezone configured (optional)
- [ ] Hostname configured (optional)

---

## System Dependencies Installation

### Python & Build Tools
- [ ] Python 3.11 installed
- [ ] Python virtual environment support installed
- [ ] Build essential tools installed
- [ ] Git installed

### Application Dependencies
- [ ] Redis server installed
- [ ] Redis started and enabled
- [ ] LibreOffice installed
- [ ] Poppler-utils installed (for PDF processing)
- [ ] Nginx installed
- [ ] Supervisor installed

### Verification
- [ ] Python version verified: `python3.11 --version`
- [ ] Redis working: `redis-cli ping` returns PONG
- [ ] LibreOffice available: `libreoffice --version`
- [ ] Nginx installed: `nginx -v`

---

## Application Deployment

### Directory Setup
- [ ] Application directory created: `/opt/pdf-converter`
- [ ] Directory ownership set to ubuntu user
- [ ] Storage directories created (uploads, outputs, temp)

### Code Deployment
- [ ] Code uploaded to server (via Git or SCP)
- [ ] All project files present
- [ ] File permissions verified

### Python Environment
- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] pip upgraded to latest version
- [ ] All requirements installed from requirements.txt
- [ ] boto3 installed for S3 support

### Configuration Files
- [ ] .env file created from .env.example
- [ ] Environment variables configured:
  - [ ] USE_S3_STORAGE=True
  - [ ] S3_BUCKET_NAME set correctly
  - [ ] AWS_REGION set correctly
  - [ ] USE_SUPABASE_STORAGE=False
  - [ ] REDIS_URL configured
  - [ ] CORS_ORIGINS updated
  - [ ] DEBUG=False
  - [ ] LIBREOFFICE_PATH=/usr/bin/libreoffice
- [ ] .env file permissions set to 600

### S3 Integration Verification
- [ ] S3 storage utility created (app/utils/s3_storage.py)
- [ ] Config updated with S3 settings
- [ ] File handler updated to support S3
- [ ] S3 access tested from EC2: `aws s3 ls s3://BUCKET_NAME`

---

## Process Management Configuration

### Supervisor Configuration
- [ ] Log directory created: `/var/log/pdf-converter`
- [ ] API service config created
- [ ] Celery worker config created
- [ ] Flower monitoring config created
- [ ] Supervisor configs reloaded
- [ ] All services started successfully

### Service Verification
- [ ] API service running: `sudo supervisorctl status pdf-converter-api`
- [ ] Worker service running: `sudo supervisorctl status pdf-converter-worker`
- [ ] Flower service running: `sudo supervisorctl status pdf-converter-flower`
- [ ] No error logs in stderr

---

## Nginx Configuration

### Nginx Setup
- [ ] Nginx config file created
- [ ] Sites-available link created
- [ ] Default site disabled
- [ ] Rate limiting configured
- [ ] Client max body size set (100M)
- [ ] Proxy timeouts configured
- [ ] Nginx config tested: `sudo nginx -t`
- [ ] Nginx restarted successfully
- [ ] Nginx auto-start enabled

### Password Protection (Optional)
- [ ] htpasswd installed
- [ ] Password file created for Flower
- [ ] Flower route protected in Nginx

---

## Testing & Verification

### Basic Health Checks
- [ ] Health endpoint accessible: `curl http://PUBLIC_IP/health`
- [ ] API docs accessible: `http://PUBLIC_IP/docs`
- [ ] Flower accessible: `http://PUBLIC_IP:5555` (or /flower/)
- [ ] Redis responding: `redis-cli ping`

### File Upload Test
- [ ] Test file upload successful
- [ ] File appears in S3 bucket
- [ ] Conversion job created
- [ ] Job status retrievable

### Conversion Tests
- [ ] PDF to Word conversion works
- [ ] Word to PDF conversion works
- [ ] Excel to PDF conversion works
- [ ] Image to PDF conversion works
- [ ] PDF to Image conversion works

### S3 Storage Tests
- [ ] Files uploaded to S3 successfully
- [ ] Files downloaded from S3 successfully
- [ ] Presigned URLs generated correctly
- [ ] Files accessible via presigned URLs
- [ ] File cleanup works (if configured)

### Performance Tests
- [ ] Multiple concurrent conversions work
- [ ] Large files (near MAX_FILE_SIZE) work
- [ ] Celery workers processing tasks
- [ ] No memory leaks observed

---

## Security Hardening

### Firewall & Access
- [ ] SSH access limited to specific IP (if possible)
- [ ] Flower password protected
- [ ] S3 bucket not publicly accessible
- [ ] Security group rules minimized
- [ ] No sensitive data in logs

### File Permissions
- [ ] .env file: 600 permissions
- [ ] SSH key: 400 permissions
- [ ] Application files owned by ubuntu user
- [ ] Log files properly restricted

### SSL/HTTPS (Production)
- [ ] Domain name configured
- [ ] DNS A record points to Elastic IP
- [ ] Certbot installed
- [ ] SSL certificate obtained
- [ ] Nginx configured for HTTPS
- [ ] HTTP to HTTPS redirect enabled
- [ ] Auto-renewal tested

---

## Monitoring & Maintenance

### Logging Setup
- [ ] Application logs viewable
- [ ] Worker logs viewable
- [ ] Nginx logs viewable
- [ ] Log rotation configured
- [ ] Flower monitoring accessible

### CloudWatch (Optional)
- [ ] CloudWatch agent installed
- [ ] CloudWatch metrics configured
- [ ] CloudWatch alarms set up
- [ ] CloudWatch dashboard created

### Backup Strategy
- [ ] Backup script created
- [ ] Cron job scheduled for backups
- [ ] Backups uploading to S3
- [ ] Backup restoration tested
- [ ] Old backups auto-deleted

### Scheduled Maintenance
- [ ] File cleanup cron job configured
- [ ] System updates scheduled
- [ ] Log rotation configured
- [ ] Monitoring alerts configured

---

## Documentation

### Deployment Documentation
- [ ] Instance details recorded (ID, IP, region)
- [ ] Bucket name documented
- [ ] IAM role ARN documented
- [ ] Security group ID documented
- [ ] All passwords/keys stored securely

### Access Information
- [ ] SSH connection details documented
- [ ] API endpoint documented
- [ ] Flower URL documented
- [ ] Admin credentials secured

### Runbook Created
- [ ] Start/stop procedures documented
- [ ] Common issues and solutions documented
- [ ] Emergency contacts listed
- [ ] Escalation procedures defined

---

## Post-Deployment

### Performance Monitoring
- [ ] Baseline metrics recorded
- [ ] Response times measured
- [ ] Resource usage monitored
- [ ] Scaling thresholds defined

### User Acceptance
- [ ] Frontend integration tested
- [ ] End-to-end workflows verified
- [ ] User documentation provided
- [ ] Support channels established

### Optimization
- [ ] Worker concurrency optimized
- [ ] Redis memory tuned
- [ ] Nginx caching configured (if needed)
- [ ] S3 lifecycle policies fine-tuned

---

## Ongoing Tasks

### Daily
- [ ] Check service status
- [ ] Review error logs
- [ ] Monitor disk space
- [ ] Verify backups

### Weekly
- [ ] Review CloudWatch metrics
- [ ] Check S3 storage costs
- [ ] Analyze conversion statistics
- [ ] Update dependencies (if needed)

### Monthly
- [ ] Security updates applied
- [ ] SSL certificate validity checked
- [ ] Backup restoration tested
- [ ] Cost analysis performed
- [ ] Performance review

---

## Rollback Plan

### If Deployment Fails
- [ ] Previous version available
- [ ] Rollback procedure documented
- [ ] Database migrations reversible (if applicable)
- [ ] DNS changes reversible

### Emergency Contacts
- AWS Support: ________________
- Team Lead: ________________
- DevOps: ________________

---

## Success Criteria

Deployment is successful when:
- [ ] All services running without errors
- [ ] All conversion types working
- [ ] S3 integration fully functional
- [ ] Performance meets requirements
- [ ] Security checklist complete
- [ ] Monitoring and alerts active
- [ ] Documentation complete
- [ ] Stakeholders notified

---

## Sign-Off

- **Deployed by:** ________________
- **Date:** ________________
- **Version:** ________________
- **Environment:** Production / Staging
- **Approved by:** ________________

---

## Resources

- Full Deployment Guide: `AWS_EC2_DEPLOYMENT_GUIDE.md`
- Quick Reference: `AWS_EC2_QUICK_REFERENCE.md`
- Environment Template: `.env.example`
- GitHub Repository: ________________
- AWS Console: https://console.aws.amazon.com
- S3 Bucket URL: ________________

---

**Notes:**
_Use this space for deployment-specific notes, issues encountered, or deviations from the plan._

