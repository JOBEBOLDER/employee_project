from django.db import models
from django.core.validators import MinLengthValidator

class Department(models.Model):
    """Department model representing organizational units within the company.
    
    Manages department information including name validation, employee counting,
    and active status tracking. Auto-formats department names to title case.
    """
    name = models.CharField(
        max_length=100, 
        unique=True,
        validators=[MinLengthValidator(2)],
        help_text="Department name must be unique and at least 2 characters long"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Optional description of the department"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this department is currently active"
    )

    class Meta:
        db_table = 'departments'
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        """String representation of the department."""
        return self.name

    @property
    def employee_count(self):
        """Returns the number of active employees in this department.
        
        Returns:
            int: Count of active employees assigned to this department
        """
        return self.employees.filter(is_active=True).count()

    def save(self, *args, **kwargs):
        """Custom save method to format department name to title case.
        
        Strips whitespace and converts name to title case before saving.
        """
        if self.name:
            self.name = self.name.strip().title()
        super().save(*args, **kwargs)