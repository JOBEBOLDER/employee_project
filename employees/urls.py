from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, auth_views

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet)
router.register(r'performance', views.PerformanceViewSet)
router.register(r'auth', auth_views.AuthViewSet, basename='auth')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/analytics/', views.EmployeeAnalyticsView.as_view(), name='employee-analytics'),
    
    # Template views
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('attendance/', views.AttendanceListView.as_view(), name='attendance_list'),
    
    # Authentication views
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('register/', auth_views.register_view, name='register'),
]