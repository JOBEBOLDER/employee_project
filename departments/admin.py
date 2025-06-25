from django.contrib import admin
from .models import Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin interface for department management with enhanced functionality.
    
    Provides list view with employee count, filtering by status and date,
    search capabilities, and read-only timestamp fields.
    """
    list_display = ['name', 'employee_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    def employee_count(self, obj):
        """Returns the number of active employees in the department.
        
        Args:
            obj: Department instance
            
        Returns:
            int: Count of active employees
        """
        return obj.employee_count
    employee_count.short_description = 'Employees'