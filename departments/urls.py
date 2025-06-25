from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 创建路由器
router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]