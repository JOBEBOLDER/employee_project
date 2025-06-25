from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random
from decimal import Decimal
from datetime import date, timedelta

from departments.models import Department
from employees.models import Employee, Performance
from attendance.models import Attendance, LeaveRequest

fake = Faker()

class Command(BaseCommand):
    """Django management command to seed database with realistic fake data.
    
    Generates departments, employees, performance reviews, and attendance records
    with proper relationships and constraints. Ensures data consistency by
    handling unique constraints and date validations.
    
    Usage:
        python manage.py seed_data --employees 50
    """
    help = 'Seed database with fake data'

    def add_arguments(self, parser):
        """Adds command line arguments.
        
        Args:
            parser: Argument parser instance
        """
        parser.add_argument('--employees', type=int, default=30, help='Number of employees to create')

    def handle(self, *args, **options):
        """Main command handler that orchestrates data generation.
        
        Args:
            args: Positional arguments
            options: Command options dictionary
        """
        num_employees = options['employees']
        
        self.stdout.write('Creating departments...')
        departments = self.create_departments()
        
        self.stdout.write(f'Creating {num_employees} employees...')
        employees = self.create_employees(departments, num_employees)
        
        self.stdout.write('Creating performance reviews...')
        self.create_performance_reviews(employees)
        
        self.stdout.write('Creating attendance records...')
        self.create_attendance_records(employees)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {num_employees} employees with related data!'))

    def create_departments(self):
        """Creates predefined departments with descriptions.
        
        Returns:
            List of Department objects created or retrieved
        """
        departments_data = [
            {'name': 'Engineering', 'description': 'Software development and technical operations'},
            {'name': 'Human Resources', 'description': 'HR and employee management'},
            {'name': 'Sales', 'description': 'Sales and business development'},
            {'name': 'Marketing', 'description': 'Marketing and brand management'},
            {'name': 'Finance', 'description': 'Financial operations'},
        ]
        
        departments = []
        for data in departments_data:
            dept, created = Department.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']}
            )
            departments.append(dept)
        
        return departments

    def create_employees(self, departments, count):
        """Creates specified number of employees with realistic data.
        
        Args:
            departments: List of Department objects to assign employees to
            count: Number of employees to create
            
        Returns:
            List of Employee objects created
        """
        employees = []
        for i in range(count):
            department = random.choice(departments)
            
            employee = Employee.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.unique.email(),
                phone_number=fake.phone_number()[:15],
                address=fake.address(),
                date_of_birth=fake.date_of_birth(minimum_age=22, maximum_age=65),
                gender=random.choice(['M', 'F', 'O']),
                department=department,
                position=fake.job(),
                date_joined=fake.date_between(start_date='-2y', end_date='today'),
                salary=Decimal(random.randint(40000, 120000)),
                employment_status=random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'INACTIVE']),
            )
            employees.append(employee)
        
        return employees

    def create_performance_reviews(self, employees):
        """Creates performance reviews for employees with unique date constraints.
        
        Ensures each employee has unique review dates by tracking used dates
        and retrying generation if conflicts occur.
        
        Args:
            employees: List of Employee objects to create reviews for
        """
        for employee in employees:
            num_reviews = random.randint(1, 3)
            used_dates = set()
            
            for _ in range(num_reviews):
                # Ensure unique review dates per employee
                max_attempts = 10
                for attempt in range(max_attempts):
                    review_date = fake.date_between(start_date=employee.date_joined, end_date='today')
                    if review_date not in used_dates:
                        used_dates.add(review_date)
                        break
                else:
                    # Skip this review if unable to find unique date after 10 attempts
                    continue
                    
                Performance.objects.create(
                    employee=employee,
                    rating=random.randint(1, 5),
                    review_date=review_date,
                    reviewer=fake.name(),
                    comments=fake.paragraph(),
                )

    def create_attendance_records(self, employees):
        """Creates attendance records for the last 30 days for active employees.
        
        Generates weekday attendance records with realistic status distribution
        and check-in/check-out times.
        
        Args:
            employees: List of Employee objects to create attendance for
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Weekdays only
                for employee in employees:
                    if employee.is_active and random.random() < 0.9:
                        Attendance.objects.create(
                            employee=employee,
                            date=current_date,
                            status=random.choices(
                                ['PRESENT', 'ABSENT', 'LATE', 'SICK_LEAVE'],
                                weights=[80, 10, 8, 2]
                            )[0],
                            check_in_time=f"{random.randint(8,9)}:{random.randint(0,59):02d}",
                            check_out_time=f"{random.randint(17,19)}:{random.randint(0,59):02d}",
                        )
            current_date += timedelta(days=1)