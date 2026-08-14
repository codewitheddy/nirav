#!/usr/bin/env python
"""
Cleanup script for cPanel deployment
Removes unnecessary files and prepares project for production
"""
import os
import shutil
from pathlib import Path

# Colors for output
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

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text):
    print(f"{BLUE}ℹ{RESET} {text}")

# Files and directories to keep for deployment
KEEP_FILES = {
    # Core Django files
    'manage.py',
    'passenger_wsgi.py',
    'requirements.txt',
    'runtime.txt',
    '.htaccess',
    'robots.txt',
    '.gitignore',
    '.env.example',
    
    # Essential documentation
    'README.md',
    'DEPLOYMENT_README.md',
    'CPANEL_DEPLOYMENT_READY.md',
    'CPANEL_QUICK_START.md',
    'POSTGRESQL_SETUP_GUIDE.md',
    
    # Deployment tools
    'verify_deployment_ready.py',
    'deploy_to_cpanel.sh',
    'setup_postgresql.sh',
}

# Directories to keep
KEEP_DIRS = {
    'jewellery_site',
    'shop',
    'static',
    'staticfiles',
    'media',
}

# Files/directories to remove
REMOVE_PATTERNS = [
    '*.pyc',
    '__pycache__',
    '*.pyo',
    '*.pyd',
    '.Python',
    'pip-log.txt',
    'pip-delete-this-directory.txt',
    '.pytest_cache',
    '.coverage',
    'htmlcov',
    '*.log',
    'db.sqlite3',
    '.DS_Store',
    'Thumbs.db',
]

# Documentation to move to docs folder
DOCS_TO_MOVE = [
    'ADMIN_*.md',
    'CART_*.md',
    'DEPLOYMENT_*.md',
    'MYADMIN_*.md',
    'IMAGE_*.md',
    'PRODUCT_*.md',
    'ABOUT_*.md',
    'ADD_*.md',
    'BACK_*.md',
    'BOOTSTRAP_*.md',
    'CLOUDINARY_*.md',
    'CONTACT_*.md',
    'FAQ_*.md',
    'HERO_*.md',
    'MODAL_*.md',
    'PAGINATION_*.md',
    'PREMIUM_*.md',
    'PRODUCTION_*.md',
    'PROJECT_*.md',
    'PYTHON_*.md',
    'QUICK_*.md',
    'SAMPLE_*.md',
    'SENTRY_*.md',
    'SETUP_*.md',
    'SQUARE_*.md',
    'TOAST_*.md',
    'WEBSITE_*.md',
    'WHATSAPP_*.md',
    'WORLD_*.md',
    'DUPLICATE_*.md',
    'SYNTAX_*.md',
]

def cleanup_pyc_files():
    """Remove Python compiled files"""
    print_header("Cleaning Python Compiled Files")
    count = 0
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments and .git
        dirs[:] = [d for d in dirs if d not in ['venv', 'env', '.git', '.kiro', 'node_modules']]
        
        for file in files:
            if file.endswith(('.pyc', '.pyo', '.pyd')):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    count += 1
                except Exception as e:
                    print_warning(f"Could not remove {file_path}: {e}")
    
    print_success(f"Removed {count} compiled Python files")

def cleanup_pycache():
    """Remove __pycache__ directories"""
    print_header("Cleaning __pycache__ Directories")
    count = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                count += 1
                dirs.remove('__pycache__')
            except Exception as e:
                print_warning(f"Could not remove {pycache_path}: {e}")
    
    print_success(f"Removed {count} __pycache__ directories")

def cleanup_logs():
    """Remove log files"""
    print_header("Cleaning Log Files")
    count = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ['venv', 'env', '.git', '.kiro']]
        
        for file in files:
            if file.endswith('.log'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    count += 1
                except Exception as e:
                    print_warning(f"Could not remove {file_path}: {e}")
    
    print_success(f"Removed {count} log files")

def organize_documentation():
    """Move documentation files to docs folder"""
    print_header("Organizing Documentation")
    
    # Create docs directory
    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)
    
    moved_count = 0
    kept_count = 0
    
    # Get all markdown files in root
    md_files = list(Path('.').glob('*.md'))
    
    for md_file in md_files:
        if md_file.name in KEEP_FILES:
            kept_count += 1
            print_info(f"Keeping: {md_file.name}")
        else:
            try:
                dest = docs_dir / md_file.name
                shutil.move(str(md_file), str(dest))
                moved_count += 1
            except Exception as e:
                print_warning(f"Could not move {md_file.name}: {e}")
    
    print_success(f"Moved {moved_count} documentation files to docs/")
    print_info(f"Kept {kept_count} essential documentation files in root")

def remove_sqlite_db():
    """Remove SQLite database (not needed for PostgreSQL deployment)"""
    print_header("Removing SQLite Database")
    
    if Path('db.sqlite3').exists():
        try:
            os.remove('db.sqlite3')
            print_success("Removed db.sqlite3")
        except Exception as e:
            print_warning(f"Could not remove db.sqlite3: {e}")
    else:
        print_info("No SQLite database found")

def cleanup_temp_files():
    """Remove temporary files"""
    print_header("Cleaning Temporary Files")
    
    temp_patterns = ['.DS_Store', 'Thumbs.db', '*.tmp', '*.bak', '*~']
    count = 0
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ['venv', 'env', '.git', '.kiro']]
        
        for file in files:
            for pattern in temp_patterns:
                if file == pattern or (pattern.startswith('*') and file.endswith(pattern[1:])):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        count += 1
                    except Exception as e:
                        print_warning(f"Could not remove {file_path}: {e}")
    
    print_success(f"Removed {count} temporary files")

def verify_essential_files():
    """Verify all essential files are present"""
    print_header("Verifying Essential Files")
    
    missing = []
    for file in KEEP_FILES:
        if not Path(file).exists():
            missing.append(file)
    
    if missing:
        print_warning(f"Missing files: {', '.join(missing)}")
        return False
    else:
        print_success("All essential files present")
        return True

def create_deployment_package_list():
    """Create a list of files to upload to cPanel"""
    print_header("Creating Deployment Package List")
    
    package_file = Path('DEPLOYMENT_PACKAGE_LIST.txt')
    
    with open(package_file, 'w') as f:
        f.write("# Files to Upload to cPanel\n")
        f.write("# Generated by cleanup_for_deployment.py\n\n")
        
        f.write("## Core Files\n")
        for file in sorted(KEEP_FILES):
            if Path(file).exists():
                f.write(f"✓ {file}\n")
        
        f.write("\n## Directories\n")
        for dir_name in sorted(KEEP_DIRS):
            if Path(dir_name).exists():
                f.write(f"✓ {dir_name}/\n")
        
        f.write("\n## Do NOT Upload\n")
        f.write("✗ .env (create on server)\n")
        f.write("✗ .git/\n")
        f.write("✗ .kiro/\n")
        f.write("✗ docs/ (optional)\n")
        f.write("✗ venv/\n")
        f.write("✗ __pycache__/\n")
        f.write("✗ *.pyc\n")
        f.write("✗ db.sqlite3\n")
    
    print_success(f"Created {package_file}")

def show_summary():
    """Show cleanup summary"""
    print_header("Cleanup Summary")
    
    # Count files
    total_files = sum(1 for _ in Path('.').rglob('*') if _.is_file())
    py_files = sum(1 for _ in Path('.').rglob('*.py') if _.is_file())
    
    print_info(f"Total files: {total_files}")
    print_info(f"Python files: {py_files}")
    
    # Check directory sizes
    for dir_name in KEEP_DIRS:
        if Path(dir_name).exists():
            size = sum(f.stat().st_size for f in Path(dir_name).rglob('*') if f.is_file())
            size_mb = size / (1024 * 1024)
            print_info(f"{dir_name}/: {size_mb:.2f} MB")

def main():
    print_header("Django Project Cleanup for cPanel Deployment")
    
    print_warning("This will clean up your project for deployment.")
    print_warning("Make sure you have committed all changes to Git!")
    
    response = input("\nContinue? (yes/no): ").lower()
    if response not in ['yes', 'y']:
        print_info("Cleanup cancelled")
        return
    
    # Run cleanup tasks
    cleanup_pyc_files()
    cleanup_pycache()
    cleanup_logs()
    remove_sqlite_db()
    cleanup_temp_files()
    organize_documentation()
    
    # Verify and create package list
    verify_essential_files()
    create_deployment_package_list()
    
    # Show summary
    show_summary()
    
    print_header("Cleanup Complete!")
    print_success("Your project is ready for cPanel deployment")
    print_info("Next steps:")
    print_info("1. Review DEPLOYMENT_PACKAGE_LIST.txt")
    print_info("2. Follow CPANEL_DEPLOYMENT_READY.md")
    print_info("3. Upload files to cPanel")

if __name__ == '__main__':
    main()
