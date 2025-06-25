from rest_framework import serializers
from .models import Employee, Performance
from departments.serializers import DepartmentSerializer

class EmployeeListSerializer(serializers.ModelSerializer):
    """简化版员工序列化器，用于列表显示"""
    full_name = serializers.ReadOnlyField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Employee
        fields = ['id', 'employee_id', 'full_name', 'email', 'department_name', 'position', 'employment_status']

class EmployeeDetailSerializer(serializers.ModelSerializer):
    """详细版员工序列化器，用于详情和创建/更新"""
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
        """验证邮箱唯一性"""
        if Employee.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Employee with this email already exists.")
        return value

    def validate_salary(self, value):
        """验证工资"""
        if value < 0:
            raise serializers.ValidationError("Salary cannot be negative.")
        return value

class PerformanceSerializer(serializers.ModelSerializer):
    """绩效评估序列化器"""
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
        """验证评分范围"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value