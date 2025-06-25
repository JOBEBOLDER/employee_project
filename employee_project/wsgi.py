"""
WSGI configuration for employee_project.

This module contains the WSGI callable used by WSGI-compatible web servers
to serve the Employee Management System in production environments.

For deployment information, see:
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Set default Django settings module for the WSGI application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_project.settings')

# Create WSGI application instance
application = get_wsgi_application()