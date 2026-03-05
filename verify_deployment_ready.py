#!/usr/bin/env python
"""
Pre-deployment verification script for cPanel
Checks if all requirements are met before deployment
"""
import os
import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    if Path(filepath).exists():
        print_success(f"{filepath} exists")
        return True
    else:
        if required:
            print_error(f"{filepath} is missing (REQUIRED)")
        else:
            print_warning(f"{filepath} is missing (optional)")
        return False

def check_directory_exists(dirpath):
    """Check if a directory exists"""
    if Path(dirpath).exists() and Path(dirpath).is_dir():
        print_success(f"{dirpath}/ directory exists")
        return True
    else:
        print_error(f"{dirpath}/ directory is missing")
        return False

def check_env_example():
    """Check .env.example file"""
    if not Path('.env.example').exists():
        print_error(".env.example is missing")
        return False
    
    with open('.env.example', 'r') as f:
        content = f.read()
        required_vars = [
            'SECRET_KEY',
            'DEBUG',
            'ALLOWED_HOSTS',
            'DATABASE_URL',
            'CLOUDINARY_CLOUD_NAME',
            'CLOUDINARY_API_KEY',
            'CLOUDINARY_API_SECRET'
        ]
        
        missing = []
        for var in required_vars:
            if var not in content:
                missing.append(var)
        
        if missing:
            print_error(f".env.example missing variables: {', '.join(missing)}")
            return False
        else:
            print_success(".env.example has all required variables")
            return True

def check_requirements():
    """Check requirements.txt"""
    if not Path('requirements.txt').exists():
        print_error("requirements.txt is missing")
        return False
    
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        content_lower = ''.join(lines).lower()
        
        required_packages = {
            'django': False,
            'gunicorn': False,
            'whitenoise': False,
            'psycopg2-binary': False,
            'python-decouple': False,
            'dj-database-url': False,
            'cloudinary': False,
            'pillow': False
        }
        
        for line in lines:
            line_lower = line.lower().strip()
            for package in required_packages.keys():
                if line_lower.startswith(package + '==') or line_lower.startswith(package + '>='):
                    required_packages[package] = True
        
        missing = [pkg for pkg, found in required_packages.items() if not found]
        
        if missing:
            print_error(f"requirements.txt missing packages: {', '.join(missing)}")
            return False
        else:
            print_success("requirements.txt has all required packages")
            return True

def check_gitignore():
    """Check .gitignore"""
    if not Path('.gitignore').exists():
        print_warning(".gitignore is missing")
        return False
    
    with open('.gitignore', 'r') as f:
        content = f.read()
        if '.env' in content:
            print_success(".gitignore includes .env")
            return True
        else:
            print_error(".gitignore does not include .env (SECURITY RISK)")
            return False

def check_settings():
    """Check Django settings"""
    settings_path = Path('jewellery_site/settings.py')
    if not settings_path.exists():
        print_error("settings.py not found")
        return False
    
    with open(settings_path, 'r') as f:
        content = f.read()
        checks = {
            'ALLOWED_HOSTS': 'ALLOWED_HOSTS' in content,
            'STATIC_ROOT': 'STATIC_ROOT' in content,
            'STATICFILES_DIRS': 'STATICFILES_DIRS' in content,
            'DATABASES': 'DATABASES' in content,
            'SESSION_ENGINE': 'SESSION_ENGINE' in content,
        }
        
        all_good = True
        for check, result in checks.items():
            if result:
                print_success(f"settings.py has {check}")
            else:
                print_error(f"settings.py missing {check}")
                all_good = False
        
        return all_good

def check_migrations():
    """Check if migrations exist"""
    migrations_dir = Path('shop/migrations')
    if not migrations_dir.exists():
        print_error("shop/migrations directory not found")
        return False
    
    migration_files = list(migrations_dir.glob('*.py'))
    migration_files = [f for f in migration_files if f.name != '__init__.py']
    
    if len(migration_files) > 0:
        print_success(f"Found {len(migration_files)} migration files")
        return True
    else:
        print_warning("No migration files found")
        return False

def check_static_files():
    """Check static files structure"""
    static_dir = Path('static')
    if not static_dir.exists():
        print_error("static/ directory not found")
        return False
    
    required_dirs = ['css', 'js', 'images']
    all_exist = True
    
    for dir_name in required_dirs:
        dir_path = static_dir / dir_name
        if dir_path.exists():
            print_success(f"static/{dir_name}/ exists")
        else:
            print_warning(f"static/{dir_name}/ not found")
            all_exist = False
    
    return all_exist

def main():
    print_header("Django cPanel Deployment Verification")
    
    errors = 0
    warnings = 0
    
    # Check required files
    print_header("Required Files")
    required_files = [
        ('requirements.txt', True),
        ('.env.example', True),
        ('passenger_wsgi.py', True),
        ('.htaccess', True),
        ('runtime.txt', True),
        ('manage.py', True),
        ('.gitignore', True),
        ('robots.txt', False),
    ]
    
    for filepath, required in required_files:
        if not check_file_exists(filepath, required):
            if required:
                errors += 1
            else:
                warnings += 1
    
    # Check directories
    print_header("Required Directories")
    required_dirs = [
        'shop',
        'shop/templates',
        'shop/migrations',
        'static',
        'jewellery_site',
    ]
    
    for dirpath in required_dirs:
        if not check_directory_exists(dirpath):
            errors += 1
    
    # Check file contents
    print_header("Configuration Files")
    
    if not check_env_example():
        errors += 1
    
    if not check_requirements():
        errors += 1
    
    if not check_gitignore():
        warnings += 1
    
    if not check_settings():
        errors += 1
    
    # Check migrations
    print_header("Database Migrations")
    if not check_migrations():
        warnings += 1
    
    # Check static files
    print_header("Static Files")
    if not check_static_files():
        warnings += 1
    
    # Summary
    print_header("Verification Summary")
    
    if errors == 0 and warnings == 0:
        print_success("All checks passed! Your project is ready for deployment.")
        print(f"\n{GREEN}✓ READY FOR CPANEL DEPLOYMENT{RESET}\n")
        return 0
    elif errors == 0:
        print_warning(f"{warnings} warning(s) found. Review and fix if needed.")
        print(f"\n{YELLOW}⚠ READY WITH WARNINGS{RESET}\n")
        return 0
    else:
        print_error(f"{errors} error(s) and {warnings} warning(s) found.")
        print(f"\n{RED}✗ NOT READY - FIX ERRORS FIRST{RESET}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
