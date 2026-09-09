# Render Deployment Configuration

## Quick Start Check List

✅ Files Created:
- [ ] Procfile - Render execution configuration
- [ ] runtime.txt - Python version specification  
- [ ] render.yaml - Service configuration
- [ ] requirements.txt - Updated with all dependencies
- [ ] wsgi.py - WSGI entry point for gunicorn
- [ ] RENDER_DEPLOYMENT_GUIDE.md - Detailed deployment instructions

✅ Code Updates:
- [ ] main.py - Updated to read PORT from environment

## Next Steps

1. **Initialize Git Repository**
   ```bash
   cd School-Management
   git init
   git add .
   git commit -m "Initial commit - Ready for Render deployment"
   ```

2. **Push to GitHub**
   - Create a new repository on GitHub
   - Push this project to your GitHub repository

3. **Deploy on Render**
   - Go to https://render.com
   - Sign up/Login
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure settings as per RENDER_DEPLOYMENT_GUIDE.md
   - Deploy

## Environment Variables for Render

Copy this template and set values in Render dashboard:

```
FLASK_ENV=production
SECRET_KEY=<generate-a-strong-random-key>
DATABASE_URL=sqlite:///school_management.db
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=<your-email>
MAIL_PASSWORD=<your-app-password>
MAIL_DEFAULT_SENDER=<sender-email>
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@school.com
ADMIN_PASSWORD=<secure-password>
INFOBIP_API_KEY=<your-api-key>
INFOBIP_BASE_URL=https://api.infobip.com
INFOBIP_SENDER=SCHOOL
```

## Important Production Notes

1. **Database**
   - Current setup uses SQLite (suitable for small to medium deployments)
   - For larger deployments, upgrade to PostgreSQL
   - PostgreSQL is available on Render as a separate service

2. **Static Files & Assets**
   - Make sure static/ directory structure is intact
   - All CSS, JS, and images are in static/ folder

3. **Scaling**
   - Start with free tier for testing
   - Upgrade to paid plan for production usage
   - Monitor memory and CPU usage

4. **Monitoring**
   - Enable error tracking in Render dashboard
   - Check logs regularly
   - Set up email notifications for critical errors

## Build & Start Commands

**Build:** `pip install -r requirements.txt`
**Start:** `gunicorn -w 4 -b 0.0.0.0:$PORT main:app`

## Troubleshooting

If deployment fails:
1. Check Render logs for specific errors
2. Verify all environment variables are set
3. Ensure requirements.txt is complete
4. Check that main.py is in the root directory

## Support & Resources

- 📚 Render Documentation: https://render.com/docs
- 🐍 Flask Guide: https://flask.palletsprojects.com/en/latest/
- 🔧 Gunicorn Guide: https://docs.gunicorn.org
