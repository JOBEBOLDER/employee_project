from django.db import models
from django.core.validators import RegexValidator, EmailValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from departments.models import Department

class Employee(models.Model):
    """
    Employee model to store employee information
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('TERMINATED', 'Terminated'),
        ('ON_LEAVE', 'On Leave'),
    ]

    # Personal Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        help_text="Phone number in international format"
    )
    address = models.TextField(help_text="Complete address")
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    # Employment Information
    employee_id = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Unique employee identifier"
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT,
        related_name='employees',
        help_text="Employee's department"
    )
    position = models.CharField(max_length=100, help_text="Job position/title")
    date_joined = models.DateField(default=timezone.now)
    salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monthly salary"
    )
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='ACTIVE'
    )
    
    # System fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employees'
        ordering = ['first_name', 'last_name']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            # Generate employee ID based on department
            dept_code = self.department.name[:3].upper() if self.department else "EMP"
            count = Employee.objects.filter(department=self.department).count() + 1
            self.employee_id = f"{dept_code}{count:04d}"
        
        if self.first_name:
            self.first_name = self.first_name.strip().title()
        if self.last_name:
            self.last_name = self.last_name.strip().title()
            
        super().save(*args, **kwargs)


class Performance(models.Model):
    """
    Performance model to track employee performance reviews
    """
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Below Average'),
        (3, 'Average'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='performances')
    rating = models.IntegerField(choices=RATING_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_date = models.DateField(default=timezone.now)
    reviewer = models.CharField(max_length=100)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'employee_performance'
        ordering = ['-review_date']
        unique_together = ['employee', 'review_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_rating_display()} ({self.review_date})"