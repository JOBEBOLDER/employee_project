from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for attendance and leave request endpoints
router = DefaultRouter()
router.register(r'attendance', views.AttendanceViewSet)
router.register(r'leave-requests', views.LeaveRequestViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/attendance/analytics/', views.AttendanceAnalyticsView.as_view(), name='attendance-analytics'),
]