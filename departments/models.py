from django.db import models

# Create your models here.
from django.db import models
from django.core.validators import MinLengthValidator

class Department(models.Model):
    """
    Department model to store department information
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
        return self.name

    @property
    def employee_count(self):
        """Return the number of employees in this department"""
        return self.employees.filter(is_active=True).count()

    def save(self, *args, **kwargs):
        """Override save to ensure name is properly formatted"""
        if self.name:
            self.name = self.name.strip().title()
        super().save(*args, **kwargs)