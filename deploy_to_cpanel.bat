@echo off
REM Django cPanel Deployment Script for Windows
REM This helps prepare files before uploading to cPanel

echo ========================================
echo Django cPanel Deployment Preparation
echo ========================================
echo.

REM Check if .env.example exists
if not exist ".env.example" (
    echo [ERROR] .env.example not found!
    exit /b 1
)

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    exit /b 1
)

REM Check if passenger_wsgi.py exists
if not exist "passenger_wsgi.py" (
    echo [ERROR] passenger_wsgi.py not found!
    exit /b 1
)

echo [OK] All required files present
echo.

REM Run verification script
echo Running pre-deployment verification...
echo.
python verify_deployment_ready.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Verification failed! Fix errors before deploying.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Verification Complete!
echo ========================================
echo.
echo Your project is ready for cPanel deployment.
echo.
echo Next steps:
echo 1. Upload all files to cPanel (except .env, .git, __pycache__)
echo 2. Create .env file on server from .env.example
echo 3. Run deployment commands on cPanel:
echo    - source /path/to/venv/bin/activate
echo    - pip install -r requirements.txt
echo    - python manage.py migrate
echo    - python manage.py collectstatic --noinput
echo    - python manage.py createsuperuser
echo.
echo See CPANEL_DEPLOYMENT_READY.md for detailed instructions.
echo.
pause
