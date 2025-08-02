# Docker Deployment Guide

This project supports containerized deployment using Docker, including both development and production environment configurations.

## File Description

- `Dockerfile`: Multi-stage Docker image configuration
- `docker-compose.yml`: Docker Compose configuration file
- `nginx.conf`: Nginx reverse proxy configuration
- `.dockerignore`: Files ignored during Docker build

## Quick Start

### Development Environment

1. **Build and start development environment**:
```bash
docker-compose --profile dev up --build
```

2. **Access the application**:
   - Main application: http://localhost:8000
   - API documentation: http://localhost:8000/swagger/
   - Admin panel: http://localhost:8000/admin/

3. **Stop development environment**:
```bash
docker-compose --profile dev down
```

### Production Environment

1. **Build and start production environment**:
```bash
docker-compose --profile prod up --build -d
```

2. **Access the application**:
   - Main application: http://localhost
   - API documentation: http://localhost/swagger/
   - Admin panel: http://localhost/admin/

3. **Stop production environment**:
```bash
docker-compose --profile prod down
```

## Environment Configuration

### Development Environment Features
- Uses Django development server
- Code hot reload
- Debug mode enabled
- SQLite database

### Production Environment Features
- Uses Gunicorn WSGI server
- Nginx reverse proxy
- PostgreSQL database
- Redis cache
- Static file serving
- Health checks
- Non-root user execution

## Database Migration

### Development Environment
```bash
docker-compose --profile dev exec web-dev python manage.py migrate
```

### Production Environment
```bash
docker-compose --profile prod exec web-prod python manage.py migrate
```

## Create Superuser

### Development Environment
```bash
docker-compose --profile dev exec web-dev python manage.py createsuperuser
```

### Production Environment
```bash
docker-compose --profile prod exec web-prod python manage.py createsuperuser
```

## View Logs

### Development Environment
```bash
docker-compose --profile dev logs -f web-dev
```

### Production Environment
```bash
docker-compose --profile prod logs -f web-prod
```

## Health Check

The application provides a health check endpoint:
- URL: `/health/`
- Returns JSON format status information

## Environment Variables

You can configure the application through environment variables:

```bash
# Development environment
export DEBUG=True
export DJANGO_SETTINGS_MODULE=employee_project.settings

# Production environment
export DEBUG=False
export DJANGO_SETTINGS_MODULE=employee_project.settings
```

## Performance Optimization

### Production Environment Optimization
1. **Multiple worker processes**: Gunicorn configured with 3 worker processes
2. **Static file caching**: Nginx configured with static file caching
3. **Gzip compression**: Response compression enabled
4. **Connection pooling**: Database connection pool optimization

### Monitoring
- Health checks: Every 30 seconds
- Logging: Access and error logs
- Container restart policy: `unless-stopped`

## Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check port usage
   lsof -i :8000
   ```

2. **Permission issues**:
   ```bash
   # Rebuild image
   docker-compose --profile prod build --no-cache
   ```

3. **Database connection issues**:
   ```bash
   # Check database container status
   docker-compose --profile prod ps
   ```

### View Logs
```bash
# View all service logs
docker-compose --profile prod logs

# View specific service logs
docker-compose --profile prod logs web-prod
```

## Security Considerations

1. **Production environment**:
   - Change default database passwords
   - Configure HTTPS
   - Set up firewall rules
   - Regularly update dependencies

2. **Environment variables**:
   - Don't hardcode sensitive information in code
   - Use environment variables for configuration management

3. **Container security**:
   - Use non-root user execution
   - Regularly update base images
   - Scan for security vulnerabilities

## Extended Deployment

### Adding SSL Certificates
1. Place certificate files in the project root directory
2. Modify nginx.conf to configure HTTPS
3. Update docker-compose.yml port mappings

### Load Balancing
You can use multiple web-prod instances with a load balancer for horizontal scaling.

### Monitoring Integration
You can integrate monitoring tools like Prometheus, Grafana, etc. 