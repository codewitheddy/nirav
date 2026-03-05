#!/bin/bash
# Django cPanel Deployment Script
# Run this script on your cPanel server after uploading files

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_info "Please create .env file from .env.example"
    exit 1
fi

print_header "Django cPanel Deployment"

# Get virtual environment path
read -p "Enter virtual environment path (e.g., /home/username/virtualenv/jewellery_site/3.11): " VENV_PATH

if [ ! -d "$VENV_PATH" ]; then
    print_error "Virtual environment not found at: $VENV_PATH"
    exit 1
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source "$VENV_PATH/bin/activate"
print_success "Virtual environment activated"

# Install dependencies
print_header "Installing Dependencies"
print_info "This may take a few minutes..."
pip install -r requirements.txt
print_success "Dependencies installed"

# Check for duplicates
print_header "Checking for Duplicate Names"
if python manage.py fix_duplicates; then
    print_success "No duplicates found or duplicates fixed"
else
    print_warning "Check duplicate fix output above"
fi

# Run migrations
print_header "Running Database Migrations"
python manage.py migrate
print_success "Migrations completed"

# Collect static files
print_header "Collecting Static Files"
python manage.py collectstatic --noinput
print_success "Static files collected"

# Create superuser (optional)
print_header "Create Superuser"
read -p "Do you want to create a superuser now? (y/n): " CREATE_SUPERUSER
if [ "$CREATE_SUPERUSER" = "y" ] || [ "$CREATE_SUPERUSER" = "Y" ]; then
    python manage.py createsuperuser
    print_success "Superuser created"
else
    print_info "Skipped superuser creation"
    print_info "You can create it later with: python manage.py createsuperuser"
fi

# Clear sessions
print_header "Clearing Old Sessions"
python manage.py clearsessions
print_success "Sessions cleared"

# Create symlinks for static files
print_header "Setting Up Static Files"
read -p "Enter public_html path (e.g., /home/username/public_html): " PUBLIC_HTML

if [ -d "$PUBLIC_HTML" ]; then
    cd "$PUBLIC_HTML"
    
    # Remove old symlinks if they exist
    [ -L "static" ] && rm static
    [ -L "media" ] && rm media
    
    # Get project path
    PROJECT_PATH=$(dirname "$(pwd)")
    
    # Create new symlinks
    ln -s "$PROJECT_PATH/jewellery_site/staticfiles" static
    ln -s "$PROJECT_PATH/jewellery_site/media" media
    
    print_success "Symlinks created"
    print_info "Static files: $PUBLIC_HTML/static -> $PROJECT_PATH/jewellery_site/staticfiles"
    print_info "Media files: $PUBLIC_HTML/media -> $PROJECT_PATH/jewellery_site/media"
else
    print_warning "public_html not found at: $PUBLIC_HTML"
    print_info "You'll need to create symlinks manually"
fi

# Restart application
print_header "Restarting Application"
PROJECT_DIR=$(pwd)
mkdir -p "$PROJECT_DIR/tmp"
touch "$PROJECT_DIR/tmp/restart.txt"
print_success "Application restart triggered"

# Final checks
print_header "Deployment Summary"
print_success "Dependencies installed"
print_success "Database migrated"
print_success "Static files collected"
print_success "Sessions cleared"
print_success "Application restarted"

print_header "Next Steps"
print_info "1. Visit your website to test"
print_info "2. Test cart functionality"
print_info "3. Login to /myadmin/ with your superuser credentials"
print_info "4. Check error logs if any issues: tail -f ~/logs/error_log"

print_header "Deployment Complete!"
print_success "Your Django application is now live on cPanel!"

echo ""
print_info "Useful commands:"
echo "  - Restart app: touch ~/jewellery_site/tmp/restart.txt"
echo "  - View logs: tail -f ~/logs/error_log"
echo "  - Django shell: python manage.py shell"
echo "  - Clear sessions: python manage.py clearsessions"
echo ""
