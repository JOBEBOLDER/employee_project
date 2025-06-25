from django.contrib import admin
from .models import Employee, Performance

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'email', 'department', 'position', 'employment_status', 'is_active']
    list_filter = ['department', 'employment_status', 'is_active', 'gender']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    ordering = ['first_name', 'last_name']
    readonly_fields = ['employee_id', 'created_at', 'updated_at']

@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'rating', 'review_date', 'reviewer']
    list_filter = ['rating', 'review_date', 'employee__department']
    search_fields = ['employee__first_name', 'employee__last_name', 'reviewer']
    ordering = ['-review_date']