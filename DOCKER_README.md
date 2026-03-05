# Docker Deployment Guide

This project is configured for Docker deployment, making it easy to run locally and deploy to platforms like Back4app, AWS, Google Cloud, or any Docker-compatible hosting.

## Quick Start (Local Development)

### Prerequisites
- Docker and Docker Compose installed
- Git (optional)

### Linux/Mac
```bash
chmod +x docker-start.sh
./docker-start.sh
```

### Windows
```bash
docker-start.bat
```

The script will:
1. Check for `.env` file (create from `.env.example` if missing)
2. Build Docker containers
3. Run database migrations
4. Optionally create a superuser
5. Start the application

Visit http://localhost:8000 to see your site!

## Manual Setup

### 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Generate a secure SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Edit `.env` and update:
- `SECRET_KEY` - Use the generated key
- `DEBUG=True` for local development
- `CLOUDINARY_*` - Your Cloudinary credentials (for media storage)

### 2. Build and Run

Build the containers:
```bash
docker-compose build
```

Start the services:
```bash
docker-compose up -d
```

Run migrations:
```bash
docker-compose exec web python manage.py migrate
```

Create a superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

### 3. Access the Application

- Main site: http://localhost:8000
- Admin panel: http://localhost:8000/admin

## Docker Commands Reference

### Container Management
```bash
# Start containers
docker-compose up -d

# Stop containers
docker-compose down

# Restart containers
docker-compose restart

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f web
```

### Django Management
```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic

# Django shell
docker-compose exec web python manage.py shell

# Run custom management command
docker-compose exec web python manage.py <command>
```

### Database Management
```bash
# Access PostgreSQL shell
docker-compose exec db psql -U jewellery_user -d jewellery_db

# Create database backup
docker-compose exec db pg_dump -U jewellery_user jewellery_db > backup.sql

# Restore database backup
docker-compose exec -T db psql -U jewellery_user jewellery_db < backup.sql
```

### Debugging
```bash
# Access container shell
docker-compose exec web bash

# Check container status
docker-compose ps

# View container resource usage
docker stats

# Rebuild containers (after code changes)
docker-compose up -d --build
```

## Project Structure

```
.
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-container setup
├── .dockerignore          # Files excluded from build
├── entrypoint.sh          # Container startup script
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── jewellery_site/       # Django project
├── shop/                 # Main app
└── static/              # Static files
```

## Environment Variables

### Required
- `SECRET_KEY` - Django secret key (generate new for production)
- `DEBUG` - Set to False in production
- `ALLOWED_HOSTS` - Comma-separated list of allowed domains
- `DATABASE_URL` - PostgreSQL connection string

### Optional
- `CLOUDINARY_CLOUD_NAME` - For media storage
- `CLOUDINARY_API_KEY` - Cloudinary API key
- `CLOUDINARY_API_SECRET` - Cloudinary API secret
- `SENTRY_DSN` - Error tracking (optional)
- `GUNICORN_WORKERS` - Number of worker processes (default: 3)
- `GUNICORN_TIMEOUT` - Request timeout in seconds (default: 120)

## Production Deployment

### Back4app
See [BACK4APP_DEPLOYMENT.md](BACK4APP_DEPLOYMENT.md) for detailed instructions.

### Other Platforms

The Docker configuration works with:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- DigitalOcean App Platform
- Heroku (with Docker)
- Any Docker-compatible hosting

General steps:
1. Push code to Git repository
2. Configure environment variables on platform
3. Connect PostgreSQL database
4. Deploy container
5. Run migrations

## Troubleshooting

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Database connection errors
```bash
# Ensure database is running
docker-compose ps

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Static files not loading
```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --noinput

# Check STATIC_ROOT setting in settings.py
```

### Container won't start
```bash
# Check logs
docker-compose logs web

# Rebuild without cache
docker-compose build --no-cache

# Remove volumes and rebuild
docker-compose down -v
docker-compose up --build
```

### Permission errors
```bash
# On Linux, fix permissions
sudo chown -R $USER:$USER .
```

## Performance Optimization

### Production Settings
1. Set `DEBUG=False`
2. Configure proper `ALLOWED_HOSTS`
3. Use PostgreSQL (included in docker-compose)
4. Enable caching (Redis recommended)
5. Use Cloudinary for media files
6. Enable Gunicorn workers (3-4 per CPU core)

### Scaling
```bash
# Scale web workers
docker-compose up -d --scale web=3
```

### Monitoring
- Use `docker stats` for resource monitoring
- Configure Sentry for error tracking
- Set up logging aggregation

## Security Checklist

- [ ] Generate new SECRET_KEY for production
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use strong database passwords
- [ ] Enable HTTPS/SSL
- [ ] Keep dependencies updated
- [ ] Regular security audits
- [ ] Backup database regularly

## Development Workflow

1. Make code changes
2. Rebuild if needed: `docker-compose up -d --build`
3. Run migrations: `docker-compose exec web python manage.py migrate`
4. Test changes
5. Commit to Git

## Support

- Docker Documentation: https://docs.docker.com/
- Django Documentation: https://docs.djangoproject.com/
- PostgreSQL Documentation: https://www.postgresql.org/docs/

## License

[Your License Here]
