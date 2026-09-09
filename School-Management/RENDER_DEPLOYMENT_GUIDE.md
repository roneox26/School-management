# Render Deployment Guide

This project is configured and ready for deployment on Render.

## Prerequisites
1. A Render account (free account is supported)
2. A GitHub repository with this project

## Files Included
- **Procfile**: Configuration for running the app with gunicorn
- **requirements.txt**: All Python dependencies
- **render.yaml**: Render-specific configuration
- **runtime.txt**: Python version specification

## Deployment Steps

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 2. Connect to Render
1. Go to https://render.com
2. Click "New +" and select "Web Service"
3. Select "Deploy an existing repository"
4. Select your GitHub repository
5. Give your service a name (e.g., `school-management`)

### 3. Configure Environment Variables
In Render dashboard, add the following environment variables:

**Required:**
- `FLASK_ENV`: production
- `SECRET_KEY`: [Generate a strong secret key]
- `DATABASE_URL`: sqlite:///school_management.db

**Optional (for email/SMS features):**
- `MAIL_SERVER`: smtp.gmail.com
- `MAIL_PORT`: 587
- `MAIL_USE_TLS`: True
- `MAIL_USERNAME`: your-email@gmail.com
- `MAIL_PASSWORD`: your-app-password
- `MAIL_DEFAULT_SENDER`: noreply@yourdomain.com
- `TWILIO_ACCOUNT_SID`: your-sid
- `TWILIO_AUTH_TOKEN`: your-token
- `TWILIO_PHONE_NUMBER`: your-number
- `INFOBIP_API_KEY`: your-api-key
- `INFOBIP_BASE_URL`: https://your-api.infobip.com
- `INFOBIP_SENDER`: SCHOOL

### 4. Configure Services
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT main:app`
- **Python Version**: 3.11

### 5. Deploy
Click "Create Web Service" and Render will automatically:
1. Build the application
2. Run database initialization
3. Start the application

## Important Notes

### Database
- The app uses SQLite3 locally stored in `school_management.db`
- For production, consider migrating to PostgreSQL on Render
- To migrate to PostgreSQL, update DATABASE_URL and use SQLAlchemy

### Port Configuration
- The app automatically uses the PORT environment variable provided by Render
- Default port is 8000 for local development
- Render will automatically assign a port

### Security
- Change the `SECRET_KEY` to a strong random value
- Keep all credentials in environment variables
- Set `FLASK_ENV=production`

### Monitoring
- Check application logs in the Render dashboard
- Monitor performance metrics
- Set up alerts for errors

## Upgrading to Production Database

To use PostgreSQL instead of SQLite:

1. Create a PostgreSQL database on Render
2. Add `DATABASE_URL` environment variable with PostgreSQL connection string
3. Update requirements.txt to include psycopg2:
   ```
   psycopg2-binary==2.9.9
   ```
4. Update database connection code in main.py

## Troubleshooting

**Build fails:**
- Check that requirements.txt has all dependencies
- Verify Python version compatibility

**App crashes after deploy:**
- Check application logs in Render dashboard
- Verify environment variables are set correctly
- Check database initialization

**Static files not loading:**
- Ensure static/ directory is in the root
- Force rebuild: Click "Clear build cache and redeploy"

## Support

For more information:
- Render Docs: https://render.com/docs
- Flask Documentation: https://flask.palletsprojects.com
- Gunicorn Documentation: https://gunicorn.org
