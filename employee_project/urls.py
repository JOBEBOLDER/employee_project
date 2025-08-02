from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from employees.views import DashboardView

# 健康检查视图
def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'message': 'Employee Management System is running'
    })

# Swagger配置
schema_view = get_schema_view(
    openapi.Info(
        title="Employee Management API",
        default_version='v1',
        description="A comprehensive REST API for managing employees, departments, and attendance records",
        contact=openapi.Contact(email="admin@company.com"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 健康检查
    path('health/', health_check, name='health-check'),
    
    # Dashboard页面
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # API endpoints
    path('', include('departments.urls')),
    path('', include('employees.urls')),
    path('', include('attendance.urls')),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # 默认跳转到API文档
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]