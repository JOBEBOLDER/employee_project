from django.contrib import admin
from .models import Attendance, LeaveRequest

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface for attendance records with filtering and search capabilities."""
    list_display = ['employee', 'date', 'status', 'check_in_time', 'check_out_time']
    list_filter = ['status', 'date', 'employee__department']
    search_fields = ['employee__first_name', 'employee__last_name']
    ordering = ['-date']

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    """Admin interface for leave requests with status and type filtering."""
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'status']
    list_filter = ['leave_type', 'status', 'start_date']
    search_fields = ['employee__first_name', 'employee__last_name']
    ordering = ['-created_at']