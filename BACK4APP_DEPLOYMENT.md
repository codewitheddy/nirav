# Back4app Docker Deployment Guide

This guide will help you deploy your Django jewellery e-commerce site to Back4app using Docker containers.

## Prerequisites

1. Back4app account (sign up at https://www.back4app.com/)
2. Git installed locally
3. Docker installed locally (for testing)
4. Cloudinary account for media storage

## Project Structure

The project now includes:
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Local development with PostgreSQL
- `.dockerignore` - Files to exclude from Docker build
- `.env.example` - Environment variables template

## Step 1: Prepare Environment Variables

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Generate a new SECRET_KEY:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

3. Update `.env` with your values:
   - `SECRET_KEY` - Use the generated key
   - `DEBUG=False` for production
   - `ALLOWED_HOSTS` - Add your Back4app domain (e.g., yourapp.back4app.io)
   - `CLOUDINARY_*` - Your Cloudinary credentials
   - `DATABASE_URL` - Will be provided by Back4app

## Step 2: Test Locally with Docker

1. Build and run with docker-compose:
   ```bash
   docker-compose up --build
   ```

2. In another terminal, run migrations:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

3. Visit http://localhost:8000 to test

4. Stop containers:
   ```bash
   docker-compose down
   ```

## Step 3: Deploy to Back4app

### Option A: Using Back4app Dashboard

1. Log in to Back4app dashboard
2. Click "Create a new app"
3. Select "Container" as the app type
4. Connect your Git repository or upload files
5. Back4app will detect the Dockerfile automatically

### Option B: Using Back4app CLI

1. Install Back4app CLI:
   ```bash
   npm install -g back4app-cli
   ```

2. Login:
   ```bash
   b4a login
   ```

3. Initialize your app:
   ```bash
   b4a new
   ```

4. Deploy:
   ```bash
   b4a deploy
   ```

## Step 4: Configure Back4app Environment

In the Back4app dashboard, go to your app settings and add these environment variables:

```
SECRET_KEY=your-generated-secret-key
DEBUG=False
ALLOWED_HOSTS=yourapp.back4app.io,yourdomain.com
DATABASE_URL=postgresql://user:pass@host:port/db
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

Note: Back4app provides a PostgreSQL database. Get the DATABASE_URL from your app's database settings.

## Step 5: Run Migrations

After deployment, run migrations using Back4app's console or CLI:

```bash
b4a run python manage.py migrate
b4a run python manage.py createsuperuser
b4a run python manage.py collectstatic --noinput
```

## Step 6: Configure Domain (Optional)

1. In Back4app dashboard, go to Settings > Custom Domain
2. Add your custom domain
3. Update DNS records as instructed
4. Update `ALLOWED_HOSTS` in environment variables

## Database Backup

Back4app provides automatic backups, but you can also create manual backups:

```bash
b4a db:backup
```

## Monitoring and Logs

View logs in real-time:
```bash
b4a logs --tail
```

Or in the Back4app dashboard under Logs section.

## Troubleshooting

### Static files not loading
- Ensure `collectstatic` ran successfully
- Check `STATIC_ROOT` and `STATIC_URL` settings
- Verify WhiteNoise is in MIDDLEWARE

### Database connection errors
- Verify DATABASE_URL is correct
- Check if migrations ran successfully
- Ensure PostgreSQL service is running

### Container fails to start
- Check logs: `b4a logs`
- Verify all environment variables are set
- Test Dockerfile locally first

### Media files not uploading
- Verify Cloudinary credentials
- Check `DEFAULT_FILE_STORAGE` setting
- Ensure DEBUG=False for production storage

## Performance Optimization

1. Enable caching (Redis available on Back4app)
2. Use CDN for static files
3. Optimize database queries
4. Monitor with Sentry (optional)

## Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY generated
- [ ] ALLOWED_HOSTS configured
- [ ] SSL/HTTPS enabled
- [ ] Database credentials secure
- [ ] Cloudinary credentials secure
- [ ] Regular backups enabled

## Scaling

Back4app allows you to scale your container:
1. Go to Settings > Resources
2. Adjust CPU and Memory
3. Enable auto-scaling if needed

## Cost Considerations

- Back4app offers a free tier for testing
- Monitor your usage in the dashboard
- Optimize container resources
- Use Cloudinary free tier for images

## Support

- Back4app Documentation: https://www.back4app.com/docs
- Back4app Community: https://community.back4app.com/
- Django Documentation: https://docs.djangoproject.com/

## Next Steps

1. Set up monitoring with Sentry
2. Configure automated backups
3. Set up CI/CD pipeline
4. Add custom domain
5. Enable CDN for static files
6. Configure email service (SendGrid, etc.)
