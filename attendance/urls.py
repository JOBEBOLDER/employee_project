from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from employees.views import AttendanceListView

# 创建路由器
router = DefaultRouter()
router.register(r'attendance', views.AttendanceViewSet)
router.register(r'leave-requests', views.LeaveRequestViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    # 修复：分析API应该在router外面
    path('api/attendance-analytics/', views.AttendanceAnalyticsView.as_view(), name='attendance-analytics'),
    # 模板视图
    path('attendance/', AttendanceListView.as_view(), name='attendance_list'),
]