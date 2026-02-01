#!/bin/bash

################################################################################
# PDF Converter API - EC2 Quick Setup Script
# 
# This script automates the deployment of the PDF Converter API on AWS EC2
# with S3 storage integration.
#
# Usage:
#   1. SSH to your EC2 instance
#   2. Download this script: wget https://raw.githubusercontent.com/YOUR_REPO/setup.sh
#   3. Make executable: chmod +x setup.sh
#   4. Run: ./setup.sh
#
# Prerequisites:
#   - EC2 instance with IAM role for S3 access
#   - S3 bucket created
#   - Ubuntu 22.04 LTS
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/pdf-converter"
LOG_DIR="/var/log/pdf-converter"
PYTHON_VERSION="3.11"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}"
    echo "════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should NOT be run as root"
        print_info "Run as regular user (ubuntu), it will use sudo when needed"
        exit 1
    fi
}

################################################################################
# Installation Functions
################################################################################

update_system() {
    print_header "Updating System"
    sudo apt update
    sudo apt upgrade -y
    print_success "System updated"
}

install_python() {
    print_header "Installing Python $PYTHON_VERSION"
    
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev python3-pip
    
    python${PYTHON_VERSION} --version
    print_success "Python $PYTHON_VERSION installed"
}

install_dependencies() {
    print_header "Installing System Dependencies"
    
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
        supervisor \
        htop \
        unzip
    
    print_success "System dependencies installed"
}

configure_redis() {
    print_header "Configuring Redis"
    
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    
    # Test Redis
    if redis-cli ping | grep -q "PONG"; then
        print_success "Redis is running"
    else
        print_error "Redis failed to start"
        exit 1
    fi
}

setup_application_directory() {
    print_header "Setting Up Application Directory"
    
    sudo mkdir -p $APP_DIR
    sudo chown $USER:$USER $APP_DIR
    
    print_success "Application directory created: $APP_DIR"
}

clone_or_upload_code() {
    print_header "Application Code Setup"
    
    print_info "Please choose how to deploy your code:"
    echo "1) Clone from Git repository"
    echo "2) I will upload manually (via SCP/SFTP)"
    read -p "Enter choice [1-2]: " choice
    
    case $choice in
        1)
            read -p "Enter Git repository URL: " repo_url
            cd $APP_DIR
            git clone $repo_url .
            print_success "Code cloned from repository"
            ;;
        2)
            print_info "Please upload your code to: $APP_DIR"
            print_info "Example: scp -r ./Backend/* ubuntu@YOUR_IP:$APP_DIR/"
            read -p "Press Enter when code is uploaded..."
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

create_virtualenv() {
    print_header "Creating Python Virtual Environment"
    
    cd $APP_DIR
    python${PYTHON_VERSION} -m venv venv
    source venv/bin/activate
    
    pip install --upgrade pip
    print_success "Virtual environment created"
}

install_python_packages() {
    print_header "Installing Python Dependencies"
    
    cd $APP_DIR
    source venv/bin/activate
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python packages installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

configure_environment() {
    print_header "Configuring Environment Variables"
    
    if [ -f "$APP_DIR/.env.example" ]; then
        cp $APP_DIR/.env.example $APP_DIR/.env
        print_info "Created .env from .env.example"
    else
        print_info "Creating .env file"
        cat > $APP_DIR/.env <<EOF
# Application
APP_NAME=PDF Converter API
DEBUG=False

# AWS S3 Configuration
USE_S3_STORAGE=True
AWS_REGION=us-east-1
S3_BUCKET_NAME=

# Disable Supabase
USE_SUPABASE_STORAGE=False

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000

# File Settings
MAX_FILE_SIZE_MB=50
FILE_RETENTION_HOURS=24

# LibreOffice
LIBREOFFICE_PATH=/usr/bin/libreoffice
EOF
    fi
    
    # Prompt for S3 bucket name
    read -p "Enter your S3 bucket name: " s3_bucket
    sed -i "s/S3_BUCKET_NAME=.*/S3_BUCKET_NAME=$s3_bucket/" $APP_DIR/.env
    
    # Prompt for AWS region
    read -p "Enter AWS region [us-east-1]: " aws_region
    aws_region=${aws_region:-us-east-1}
    sed -i "s/AWS_REGION=.*/AWS_REGION=$aws_region/" $APP_DIR/.env
    
    # Set permissions
    chmod 600 $APP_DIR/.env
    
    print_success "Environment configured"
}

verify_s3_access() {
    print_header "Verifying S3 Access"
    
    source $APP_DIR/.env
    
    if aws s3 ls s3://$S3_BUCKET_NAME > /dev/null 2>&1; then
        print_success "S3 bucket accessible: $S3_BUCKET_NAME"
    else
        print_error "Cannot access S3 bucket: $S3_BUCKET_NAME"
        print_info "Ensure EC2 instance has IAM role with S3 permissions"
        exit 1
    fi
}

create_storage_directories() {
    print_header "Creating Storage Directories"
    
    mkdir -p $APP_DIR/storage/uploads
    mkdir -p $APP_DIR/storage/outputs
    mkdir -p $APP_DIR/temp
    mkdir -p $APP_DIR/backups
    
    sudo mkdir -p $LOG_DIR
    sudo chown $USER:$USER $LOG_DIR
    
    print_success "Storage directories created"
}

configure_supervisor() {
    print_header "Configuring Supervisor"
    
    # API Service
    sudo tee /etc/supervisor/conf.d/pdf-converter-api.conf > /dev/null <<EOF
[program:pdf-converter-api]
directory=$APP_DIR
command=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$LOG_DIR/api.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="$APP_DIR/venv/bin"
EOF
    
    # Celery Worker
    sudo tee /etc/supervisor/conf.d/pdf-converter-worker.conf > /dev/null <<EOF
[program:pdf-converter-worker]
directory=$APP_DIR
command=$APP_DIR/venv/bin/celery -A app.celery_app worker --loglevel=info --concurrency=4
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$LOG_DIR/worker.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="$APP_DIR/venv/bin"
stopwaitsecs=600
EOF
    
    # Flower Monitoring
    sudo tee /etc/supervisor/conf.d/pdf-converter-flower.conf > /dev/null <<EOF
[program:pdf-converter-flower]
directory=$APP_DIR
command=$APP_DIR/venv/bin/celery -A app.celery_app flower --port=5555
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$LOG_DIR/flower.log
environment=PATH="$APP_DIR/venv/bin"
EOF
    
    # Reload supervisor
    sudo supervisorctl reread
    sudo supervisorctl update
    
    print_success "Supervisor configured"
}

configure_nginx() {
    print_header "Configuring Nginx"
    
    # Get EC2 public IP
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    
    sudo tee /etc/nginx/sites-available/pdf-converter > /dev/null <<EOF
limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;

upstream fastapi_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name $PUBLIC_IP;
    client_max_body_size 100M;
    
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://fastapi_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }
}
EOF
    
    # Enable site
    sudo ln -sf /etc/nginx/sites-available/pdf-converter /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test configuration
    sudo nginx -t
    
    # Restart nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    print_success "Nginx configured for IP: $PUBLIC_IP"
}

start_services() {
    print_header "Starting Services"
    
    sudo supervisorctl start all
    sleep 5
    
    # Check status
    sudo supervisorctl status
    
    print_success "Services started"
}

test_deployment() {
    print_header "Testing Deployment"
    
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    
    print_info "Testing health endpoint..."
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        print_success "API is responding"
    else
        print_error "API is not responding"
        print_info "Check logs: sudo supervisorctl tail -f pdf-converter-api"
    fi
    
    print_info "Testing Redis..."
    if redis-cli ping | grep -q "PONG"; then
        print_success "Redis is working"
    else
        print_error "Redis is not working"
    fi
    
    print_info "Testing S3..."
    source $APP_DIR/.env
    if aws s3 ls s3://$S3_BUCKET_NAME > /dev/null 2>&1; then
        print_success "S3 access verified"
    else
        print_error "S3 access failed"
    fi
}

print_summary() {
    PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
    
    print_header "Deployment Complete!"
    
    echo -e "${GREEN}"
    echo "════════════════════════════════════════════════════════════"
    echo "  PDF Converter API Successfully Deployed!"
    echo "════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    echo ""
    echo "📍 Access URLs:"
    echo "   API:            http://$PUBLIC_IP"
    echo "   API Docs:       http://$PUBLIC_IP/docs"
    echo "   Health Check:   http://$PUBLIC_IP/health"
    echo "   Flower Monitor: http://$PUBLIC_IP:5555"
    echo ""
    echo "📂 Directories:"
    echo "   Application:    $APP_DIR"
    echo "   Logs:          $LOG_DIR"
    echo "   Virtual Env:   $APP_DIR/venv"
    echo ""
    echo "🔧 Useful Commands:"
    echo "   View logs:      sudo supervisorctl tail -f pdf-converter-api"
    echo "   Restart API:    sudo supervisorctl restart pdf-converter-api"
    echo "   Restart worker: sudo supervisorctl restart pdf-converter-worker"
    echo "   Status:         sudo supervisorctl status"
    echo "   Redis:          redis-cli ping"
    echo ""
    echo "📚 Documentation:"
    echo "   Full Guide:     $APP_DIR/AWS_EC2_DEPLOYMENT_GUIDE.md"
    echo "   Quick Ref:      $APP_DIR/AWS_EC2_QUICK_REFERENCE.md"
    echo ""
    echo "🔒 Next Steps:"
    echo "   1. Test the API with a file upload"
    echo "   2. Configure domain name (optional)"
    echo "   3. Install SSL certificate (recommended)"
    echo "   4. Set up monitoring and alerts"
    echo "   5. Configure automated backups"
    echo ""
    echo -e "${YELLOW}⚠️  Security Reminders:${NC}"
    echo "   • Restrict SSH access to your IP only"
    echo "   • Configure SSL/HTTPS for production"
    echo "   • Review security group rules"
    echo "   • Set up CloudWatch monitoring"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    print_header "PDF Converter API - EC2 Deployment Script"
    
    check_root
    
    print_info "This script will install and configure the PDF Converter API"
    print_info "Estimated time: 15-30 minutes"
    echo ""
    read -p "Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
    
    # Installation steps
    update_system
    install_python
    install_dependencies
    configure_redis
    setup_application_directory
    clone_or_upload_code
    create_virtualenv
    install_python_packages
    configure_environment
    verify_s3_access
    create_storage_directories
    configure_supervisor
    configure_nginx
    start_services
    
    # Testing
    sleep 5
    test_deployment
    
    # Summary
    print_summary
}

# Run main function
main "$@"
