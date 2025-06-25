from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet)
router.register(r'performance', views.PerformanceViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/analytics/', views.EmployeeAnalyticsView.as_view(), name='employee-analytics'),
]