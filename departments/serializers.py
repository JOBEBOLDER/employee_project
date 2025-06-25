from rest_framework import serializers
from .models import Department

class DepartmentSerializer(serializers.ModelSerializer):
    employee_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'is_active', 'employee_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'employee_count']

    def validate_name(self, value):
        """
        Validate department name
        """
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Department name must be at least 2 characters long.")
        return value.strip().title()