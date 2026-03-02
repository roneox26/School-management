# PostgreSQL Support for Render Deployment

This document outlines the PostgreSQL support added to the School Management System for deployment on Render.

## Overview

The application now supports both SQLite (for local development) and PostgreSQL (for production on Render).

### Database Detection

The application automatically detects which database to use based on the `DATABASE_URL` environment variable:

- **SQLite**: Used when `DATABASE_URL` is not set or does not start with `postgresql`
- **PostgreSQL**: Used when `DATABASE_URL` starts with `postgresql`

## Render Deployment Configuration

### Updated render.yaml

The `render.yaml` file now includes:

1. **Web Service** (`school-management`):
   - Python 3.11 environment
   - Free tier plan
   - Gunicorn startup command
   - References PostgreSQL connection via `POSTGRES_DATABASE_URL`

2. **PostgreSQL Service** (`school-management-postgres`):
   - PostgreSQL 15 major version
   - Free tier plan
   - Automatically provides `POSTGRES_DATABASE_URL` environment variable

### Environment Variables

The following environment variables are automatically configured on Render:

| Variable | Type | Description |
|----------|------|-------------|
| `PYTHON_VERSION` | Config | Python 3.11.0 |
| `FLASK_ENV` | Config | Set to `production` |
| `SECRET_KEY` | Generated | Auto-generated secure key |
| `DATABASE_URL` | Reference | Points to `POSTGRES_DATABASE_URL` from PostgreSQL service |
| `MAIL_SERVER` | Config | SMTP server (default: smtp.gmail.com) |
| `MAIL_PORT` | Config | SMTP port (default: 587) |
| `MAIL_USE_TLS` | Config | TLS enabled (default: True) |

## Dependencies

New dependencies added to `requirements.txt`:

- **psycopg2-binary** (2.9.9): PostgreSQL adapter for Python
- **SQLAlchemy** (2.0.23): SQL toolkit (for future ORM migration)

## Database Migration

### From SQLite to PostgreSQL

1. Deploy the application to Render with the updated `render.yaml`
2. The database schema will be automatically created on PostgreSQL
3. For existing data migration:
   - Export data from SQLite database
   - Import into PostgreSQL database
   - Or re-initialize with fresh data

## Local Development

For local development, the application continues to use SQLite:

```bash
# No DATABASE_URL needed - uses local SQLite database
python main.py
```

## Production Deployment Steps

1. Push changes to repository:
   ```bash
   git add .
   git commit -m "Add PostgreSQL support for Render"
   git push
   ```

2. Connect Render to your GitHub repository

3. Create new web service and PostgreSQL service via Render dashboard OR deploy using `render.yaml`

4. Render will automatically:
   - Install dependencies from `requirements.txt`
   - Create PostgreSQL database instance
   - Set `POSTGRES_DATABASE_URL` environment variable
   - Start the application with gunicorn

## Database Helper Functions

All database operations have been updated to support both databases:

- `get_db_connection()`: Returns appropriate database connection
- `init_db()`: Initializes schema for selected database
- `save_to_db()`: Inserts data with UUID generation
- `get_from_db()`: Retrieves data with caching support
- `update_in_db()`: Updates existing data
- `delete_from_db()`: Deletes data entries

### Query Compatibility

The application uses parameterized queries compatible with both databases:
- SQLite: Uses `?` placeholders
- PostgreSQL: Uses `%s` placeholders

Data is accessed appropriately:
- SQLite: Dictionary-like access (`row['column']`)
- PostgreSQL: Tuple indexing (`row[0]`)

## Monitoring

On Render, you can monitor your application through:

1. **Render Dashboard**: View logs, deployment status, environment variables
2. **Application Logs**: Access via Render web service logs
3. **Database Connection**: Monitor PostgreSQL instance performance

## Troubleshooting

### Connection Issues

If experiencing database connection errors:

1. Check `DATABASE_URL` format: `postgresql://user:password@host:port/database`
2. Verify PostgreSQL service is running on Render
3. Check firewall/network rules allow database connections
4. Review application logs for detailed error messages

### Schema Issues

If database initialization fails:

1. Verify `app_data` table exists in PostgreSQL
2. Check table schema matches expected structure
3. Review logs for SQL errors

### Switching Databases

To switch from SQLite to PostgreSQL:

1. Set `DATABASE_URL` environment variable to PostgreSQL connection string
2. Restart application - it will auto-detect and use PostgreSQL

## Future Enhancements

Potential improvements for database handling:

1. **ORM Migration**: Migrate from raw SQL to SQLAlchemy ORM
2. **Connection Pooling**: Add connection pool for production use
3. **Migrations**: Implement Alembic for schema versioning
4. **Backup Strategy**: Automated backups for PostgreSQL

## Support

For issues related to PostgreSQL deployment:

1. Check Render documentation: https://render.com/docs
2. Review PostgreSQL documentation: https://www.postgresql.org/docs/
3. Check application logs on Render dashboard

---

**Last Updated**: March 2, 2026
**Version**: 1.0
