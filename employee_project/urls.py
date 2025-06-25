"""
Main URL configuration for Employee Management System.

Defines routing for admin interface, API endpoints, documentation,
and dashboard visualization. Includes Swagger/ReDoc documentation
accessible at /swagger/ and /redoc/ respectively.

URL Structure:
    /admin/ - Django admin interface
    /dashboard/ - Analytics dashboard with charts
    /api/departments/ - Department management endpoints
    /api/employees/ - Employee management endpoints  
    /api/attendance/ - Attendance tracking endpoints
    /swagger/ - Interactive API documentation
    /redoc/ - Alternative API documentation view
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from employees.views import DashboardView

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Employee Management API",
        default_version='v1',
        description="A comprehensive REST API for managing employees, departments, and attendance records",
        terms_of_service="https://www.company.com/terms/",
        contact=openapi.Contact(email="admin@company.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin interface for data management
    path('admin/', admin.site.urls),
    
    # Dashboard page for data visualization
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # API endpoints - include all app URLs
    path('', include('departments.urls')),
    path('', include('employees.urls')),
    path('', include('attendance.urls')),
    
    # API Documentation endpoints
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Default route redirects to API documentation
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]