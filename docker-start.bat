@echo off
REM Quick start script for local Docker development on Windows

echo Starting Django Jewellery Site with Docker...

REM Check if .env exists
if not exist .env (
    echo .env file not found. Copying from .env.example...
    copy .env.example .env
    echo Please edit .env file with your configuration before continuing.
    echo At minimum, generate a new SECRET_KEY:
    echo python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    pause
    exit /b 1
)

REM Build and start containers
echo Building Docker containers...
docker-compose up --build -d

REM Wait for database
echo Waiting for database to be ready...
timeout /t 5 /nobreak

REM Run migrations
echo Running database migrations...
docker-compose exec web python manage.py migrate

REM Create superuser (optional)
echo.
set /p create_super="Would you like to create a superuser? (y/n): "
if /i "%create_super%"=="y" (
    docker-compose exec web python manage.py createsuperuser
)

REM Show info
echo.
echo Application is running!
echo Visit: http://localhost:8000
echo Admin: http://localhost:8000/admin
echo.
echo View logs with: docker-compose logs -f
echo Stop with: docker-compose down
echo.
docker-compose logs -f
