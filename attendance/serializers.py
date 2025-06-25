from rest_framework import serializers
from .models import Attendance, LeaveRequest

class AttendanceListSerializer(serializers.ModelSerializer):
    """Simplified attendance serializer for list views with essential information."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    working_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'employee_name', 'date', 'status_display', 
            'check_in_time', 'check_out_time', 'working_hours'
        ]

class AttendanceDetailSerializer(serializers.ModelSerializer):
    """Comprehensive attendance serializer for CRUD operations with validation."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    working_hours = serializers.ReadOnlyField()
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_name', 'date', 'status', 'status_display',
            'check_in_time', 'check_out_time', 'working_hours', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'working_hours']

    def validate(self, data):
        """Validates attendance data for business rules compliance.
        
        Checks:
        - Employee must be active
        - Check-out time validation for overnight shifts
        - Working hours must not exceed 16 hours per day
        
        Args:
            data: Serializer data dictionary
            
        Returns:
            dict: Validated data
            
        Raises:
            ValidationError: If validation rules are violated
        """
        # Check if employee is active
        employee = data.get('employee')
        if employee and not employee.is_active:
            raise serializers.ValidationError("Cannot create attendance for inactive employee.")
            
        # Validate check-in/out times
        check_in = data.get('check_in_time')
        check_out = data.get('check_out_time')
        
        if check_in and check_out and check_out <= check_in:
            # Allow overnight shifts
            from datetime import datetime, timedelta
            date = data.get('date')
            check_in_datetime = datetime.combine(date, check_in)
            check_out_datetime = datetime.combine(date, check_out)
            
            if check_out_datetime <= check_in_datetime:
                check_out_datetime += timedelta(days=1)
                
            # Validate reasonable working hours (max 16 hours)
            working_duration = check_out_datetime - check_in_datetime
            if working_duration.total_seconds() > 16 * 3600:
                raise serializers.ValidationError("Working hours cannot exceed 16 hours per day.")
        
        return data

class LeaveRequestListSerializer(serializers.ModelSerializer):
    """Simplified leave request serializer for list views."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_days = serializers.ReadOnlyField()
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee_name', 'leave_type_display', 'start_date', 
            'end_date', 'duration_days', 'status_display', 'created_at'
        ]

class LeaveRequestDetailSerializer(serializers.ModelSerializer):
    """Comprehensive leave request serializer with overlap detection validation."""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_days = serializers.ReadOnlyField()
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'leave_type_display',
            'start_date', 'end_date', 'duration_days', 'reason', 'status', 
            'status_display', 'approved_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'duration_days']

    def validate(self, data):
        """Validates leave request data for business rules compliance.
        
        Checks:
        - Employee must be active
        - End date must be after or equal to start date
        - No overlapping leave requests for the same employee
        
        Args:
            data: Serializer data dictionary
            
        Returns:
            dict: Validated data
            
        Raises:
            ValidationError: If validation rules are violated
        """
        # Check if employee is active
        employee = data.get('employee')
        if employee and not employee.is_active:
            raise serializers.ValidationError("Cannot create leave request for inactive employee.")
            
        # Validate dates
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before start date.")
            
        # Check for overlapping leave requests
        if employee and start_date and end_date:
            overlapping_requests = LeaveRequest.objects.filter(
                employee=employee,
                status__in=['PENDING', 'APPROVED'],
                start_date__lte=end_date,
                end_date__gte=start_date
            )
            
            if self.instance:
                overlapping_requests = overlapping_requests.exclude(pk=self.instance.pk)
                
            if overlapping_requests.exists():
                raise serializers.ValidationError(
                    "Employee already has a leave request for overlapping dates."
                )
        
        return data