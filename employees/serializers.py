from rest_framework import serializers
from .models import Employee, Performance
from departments.serializers import DepartmentSerializer

class EmployeeListSerializer(serializers.ModelSerializer):
    """Simplified employee serializer for list views.
    
    Provides essential employee information optimized for list display
    with minimal data transfer.
    """
    full_name = serializers.ReadOnlyField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'full_name', 'email', 'department_name', 'position', 'employment_status']

class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Comprehensive employee serializer for detail views and CRUD operations.
    
    Includes complete employee information with nested department details
    and computed fields. Provides validation for email uniqueness and salary.
    """
    full_name = serializers.ReadOnlyField()
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.IntegerField(write_only=True)
    years_of_service = serializers.ReadOnlyField()
    
    class Meta:
        model = Employee
        fields = [
            'id', 'employee_id', 'first_name', 'last_name', 'full_name',
            'email', 'phone_number', 'address', 'date_of_birth', 'gender',
            'department', 'department_id', 'position', 'date_joined', 
            'salary', 'employment_status', 'years_of_service',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['employee_id', 'created_at', 'updated_at']

    def validate_email(self, value):
        """Validates email uniqueness across all employees.
        
        Args:
            value: Email address to validate
            
        Returns:
            Validated email address
            
        Raises:
            ValidationError: If email already exists for another employee
        """
        if Employee.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Employee with this email already exists.")
        return value

    def validate_salary(self, value):
        """Validates salary is non-negative.
        
        Args:
            value: Salary amount to validate
            
        Returns:
            Validated salary amount
            
        Raises:
            ValidationError: If salary is negative
        """
        if value < 0:
            raise serializers.ValidationError("Salary cannot be negative.")
        return value

class PerformanceSerializer(serializers.ModelSerializer):
    """Performance review serializer with employee information and validation."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    rating_display = serializers.CharField(source='get_rating_display', read_only=True)
    
    class Meta:
        model = Performance
        fields = [
            'id', 'employee', 'employee_name', 'rating', 'rating_display',
            'review_date', 'reviewer', 'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_rating(self, value):
        """Validates rating is within acceptable range (1-5).
        
        Args:
            value: Rating value to validate
            
        Returns:
            Validated rating value
            
        Raises:
            ValidationError: If rating is outside 1-5 range
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value