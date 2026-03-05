#!/usr/bin/env python3
"""
Validation script to check if Docker deployment setup is complete
"""

import os
import sys
from pathlib import Path

def check_file(filepath, description):
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_env_example():
    """Check if .env.example has required variables"""
    required_vars = [
        'SECRET_KEY',
        'DEBUG',
        'ALLOWED_HOSTS',
        'DATABASE_URL',
        'CLOUDINARY_CLOUD_NAME',
        'CLOUDINARY_API_KEY',
        'CLOUDINARY_API_SECRET'
    ]
    
    if not Path('.env.example').exists():
        print("❌ .env.example not found")
        return False
    
    with open('.env.example', 'r') as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if var not in content:
            missing.append(var)
    
    if missing:
        print(f"❌ .env.example missing variables: {', '.join(missing)}")
        return False
    else:
        print("✅ .env.example has all required variables")
        return True

def check_requirements():
    """Check if requirements.txt has valid Django version"""
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt not found")
        return False
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    # Check for Django
    if 'Django==' not in content:
        print("❌ Django not found in requirements.txt")
        return False
    
    # Check for invalid future versions
    invalid_versions = ['Django==6.', 'Django==7.', 'gunicorn==25.', 'pillow==12.']
    for invalid in invalid_versions:
        if invalid in content:
            print(f"❌ Invalid future version found: {invalid}")
            print("   Run: Update requirements.txt with stable versions")
            return False
    
    # Check for valid Django 5.x
    if 'Django==5.' in content:
        print("✅ requirements.txt has valid Django version (5.x)")
        return True
    elif 'Django==4.' in content:
        print("✅ requirements.txt has valid Django version (4.x)")
        return True
    else:
        print("⚠️  Django version may need verification")
        return True

def main():
    print("=" * 60)
    print("Docker Deployment Setup Validation")
    print("=" * 60)
    print()
    
    checks = []
    
    # Core Docker files
    print("Core Docker Files:")
    checks.append(check_file('Dockerfile', 'Dockerfile'))
    checks.append(check_file('docker-compose.yml', 'Docker Compose'))
    checks.append(check_file('docker-compose.prod.yml', 'Production Compose'))
    checks.append(check_file('.dockerignore', 'Docker Ignore'))
    checks.append(check_file('entrypoint.sh', 'Entrypoint Script'))
    print()
    
    # Helper scripts
    print("Helper Scripts:")
    checks.append(check_file('docker-start.sh', 'Linux/Mac Start Script'))
    checks.append(check_file('docker-start.bat', 'Windows Start Script'))
    print()
    
    # Documentation
    print("Documentation:")
    checks.append(check_file('DOCKER_README.md', 'Docker README'))
    checks.append(check_file('BACK4APP_DEPLOYMENT.md', 'Back4app Guide'))
    checks.append(check_file('BACK4APP_CHECKLIST.md', 'Deployment Checklist'))
    checks.append(check_file('DOCKER_QUICK_REFERENCE.md', 'Quick Reference'))
    checks.append(check_file('DOCKER_DEPLOYMENT_SUMMARY.md', 'Deployment Summary'))
    print()
    
    # Configuration
    print("Configuration:")
    checks.append(check_env_example())
    checks.append(check_requirements())
    print()
    
    # Django files
    print("Django Configuration:")
    checks.append(check_file('manage.py', 'Django Manage'))
    checks.append(check_file('jewellery_site/settings.py', 'Django Settings'))
    checks.append(check_file('jewellery_site/urls.py', 'Django URLs'))
    checks.append(check_file('jewellery_site/wsgi.py', 'WSGI'))
    print()
    
    # Summary
    print("=" * 60)
    total = len(checks)
    passed = sum(checks)
    failed = total - passed
    
    print(f"Total Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("✅ All checks passed! Your project is ready for Docker deployment.")
        print()
        print("Next Steps:")
        print("1. Copy .env.example to .env and configure it")
        print("2. Test locally: ./docker-start.sh (or docker-start.bat on Windows)")
        print("3. Follow BACK4APP_DEPLOYMENT.md for deployment")
        print()
        print("Note: Requirements.txt has been updated with stable versions.")
        print("See DEPLOYMENT_FIX.md for details.")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
