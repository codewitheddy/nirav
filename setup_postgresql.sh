#!/bin/bash
# PostgreSQL Setup and Verification Script for cPanel
# Run this after creating database in cPanel

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PostgreSQL Setup for Django${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create .env file from .env.example first${NC}"
    exit 1
fi

# Source .env file
export $(cat .env | grep -v '^#' | xargs)

echo -e "${BLUE}Step 1: Verifying Database Configuration${NC}"
echo "----------------------------------------"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} DATABASE_URL is configured"

# Extract database details from DATABASE_URL
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

echo -e "${BLUE}Step 2: Testing Database Connection${NC}"
echo "----------------------------------------"

# Test database connection
if python manage.py dbshell -c "\q" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Database connection successful"
else
    echo -e "${RED}✗${NC} Database connection failed"
    echo -e "${YELLOW}Please check your DATABASE_URL in .env${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}Step 3: Checking for Duplicate Names${NC}"
echo "----------------------------------------"

# Fix duplicates if any
python manage.py fix_duplicates
echo ""

echo -e "${BLUE}Step 4: Running Database Migrations${NC}"
echo "----------------------------------------"

# Run migrations
python manage.py migrate

echo -e "${GREEN}✓${NC} Migrations completed"
echo ""

echo -e "${BLUE}Step 5: Verifying Database Tables${NC}"
echo "----------------------------------------"

# Check if tables exist
TABLES=$(python manage.py dbshell -c "\dt" 2>/dev/null | grep -c "shop_" || echo "0")

if [ "$TABLES" -gt "0" ]; then
    echo -e "${GREEN}✓${NC} Found $TABLES shop tables"
else
    echo -e "${RED}✗${NC} No shop tables found"
    exit 1
fi
echo ""

echo -e "${BLUE}Step 6: Database Statistics${NC}"
echo "----------------------------------------"

# Get record counts
python manage.py shell << EOF
from shop.models import Product, Category, Order

print(f"Products: {Product.objects.count()}")
print(f"Categories: {Category.objects.count()}")
print(f"Orders: {Order.objects.count()}")
EOF

echo ""

echo -e "${BLUE}Step 7: Creating Superuser (Optional)${NC}"
echo "----------------------------------------"

read -p "Do you want to create a superuser now? (y/n): " CREATE_SUPERUSER

if [ "$CREATE_SUPERUSER" = "y" ] || [ "$CREATE_SUPERUSER" = "Y" ]; then
    python manage.py createsuperuser
    echo -e "${GREEN}✓${NC} Superuser created"
else
    echo -e "${YELLOW}Skipped. You can create it later with:${NC}"
    echo "  python manage.py createsuperuser"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}PostgreSQL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

echo "Next steps:"
echo "1. Collect static files: python manage.py collectstatic --noinput"
echo "2. Test your application"
echo "3. Create regular database backups"
echo ""

echo "Useful commands:"
echo "  - Database shell: python manage.py dbshell"
echo "  - Create backup: pg_dump -U $DB_USER $DB_NAME > backup.sql"
echo "  - Check migrations: python manage.py showmigrations"
echo ""
