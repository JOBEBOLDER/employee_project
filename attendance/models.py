from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from employees.models import Employee

class Attendance(models.Model):
    """
    Attendance model to track employee attendance
    """
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late'),
        ('HALF_DAY', 'Half Day'),
        ('SICK_LEAVE', 'Sick Leave'),
        ('VACATION', 'Vacation'),
        ('HOLIDAY', 'Holiday'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    check_in_time = models.TimeField(null=True, blank=True, help_text="Time when employee checked in")
    check_out_time = models.TimeField(null=True, blank=True, help_text="Time when employee checked out")
    notes = models.TextField(blank=True, help_text="Additional notes about attendance")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_attendance'
        ordering = ['-date', 'employee']
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.get_status_display()})"

    @property
    def working_hours(self):
        """Calculate total working hours for the day"""
        if self.check_in_time and self.check_out_time:
            from datetime import datetime, timedelta
            check_in = datetime.combine(self.date, self.check_in_time)
            check_out = datetime.combine(self.date, self.check_out_time)
            if check_out < check_in:
                check_out += timedelta(days=1)
            total_time = check_out - check_in
            return total_time.total_seconds() / 3600
        return 0


class LeaveRequest(models.Model):
    """
    Model to handle employee leave requests
    """
    LEAVE_TYPES = [
        ('SICK', 'Sick Leave'),
        ('VACATION', 'Vacation'),
        ('PERSONAL', 'Personal Leave'),
        ('EMERGENCY', 'Emergency Leave'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(help_text="Reason for leave request")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'leave_requests'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0