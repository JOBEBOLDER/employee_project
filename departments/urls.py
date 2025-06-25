from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from employees.views import DepartmentListView  # 导入视图

# 创建路由器
router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    # 添加模板视图
    path('departments/', DepartmentListView.as_view(), name='department_list'),
]