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
    """Django management command to seed database with realistic fake data."""
    help = 'Seed database with fake data'

    def add_arguments(self, parser):
        """Adds command line arguments."""
        parser.add_argument('--employees', type=int, default=30, help='Number of employees to create')

    def handle(self, *args, **options):
        """Main command handler that orchestrates data generation."""
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
        """Creates predefined departments with descriptions."""
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
        """Creates specified number of employees with realistic data."""
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
        """Creates performance reviews for employees with unique date constraints."""
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
        """Creates attendance records for the last 6 months for active employees."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)  # 6个月的数据
        
        self.stdout.write(f'Creating attendance records from {start_date} to {end_date}...')
        
        current_date = start_date
        records_created = 0
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # 只在工作日
                for employee in employees:
                    if employee.is_active and random.random() < 0.95:  # 95%的员工有考勤记录
                        # 根据月份调整出勤率
                        month = current_date.month
                        if month in [12, 1]:  # 假期月份
                            status_weights = [70, 15, 10, 5]
                        elif month in [6, 7, 8]:  # 夏季
                            status_weights = [80, 8, 10, 2]
                        else:  # 正常月份
                            status_weights = [85, 8, 5, 2]
                        
                        status = random.choices(
                            ['PRESENT', 'ABSENT', 'LATE', 'SICK_LEAVE'],
                            weights=status_weights
                        )[0]
                        
                        # 为PRESENT和LATE状态添加签到签退时间
                        check_in_time = None
                        check_out_time = None
                        
                        if status in ['PRESENT', 'LATE']:
                            if status == 'LATE':
                                check_in_hour = random.randint(9, 11)  # 迟到
                            else:
                                check_in_hour = random.randint(8, 9)   # 正常
                            
                            check_in_minute = random.randint(0, 59)
                            check_in_time = f"{check_in_hour}:{check_in_minute:02d}"
                            
                            # 签退时间（工作8-9小时）
                            work_hours = random.randint(8, 9)
                            check_out_hour = check_in_hour + work_hours
                            check_out_minute = random.randint(0, 59)
                            
                            if check_out_hour >= 24:
                                check_out_hour -= 24
                            check_out_time = f"{check_out_hour}:{check_out_minute:02d}"
                        
                        try:
                            Attendance.objects.create(
                                employee=employee,
                                date=current_date,
                                status=status,
                                check_in_time=check_in_time,
                                check_out_time=check_out_time,
                                notes=f"Auto-generated record"
                            )
                            records_created += 1
                        except Exception as e:
                            # 如果有重复记录，跳过
                            pass
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'Created {records_created} attendance records.')

    def create_leave_requests(self, employees):
        """Creates sample leave requests."""
        for employee in employees:
            if employee.is_active and random.random() < 0.3:  # 30% 员工有请假记录
                num_requests = random.randint(1, 2)
                
                for _ in range(num_requests):
                    start_date = fake.date_between(start_date='-60d', end_date='+30d')
                    duration = random.randint(1, 5)
                    end_date = start_date + timedelta(days=duration)
                    
                    LeaveRequest.objects.create(
                        employee=employee,
                        leave_type=random.choice(['SICK', 'VACATION', 'PERSONAL', 'EMERGENCY']),
                        start_date=start_date,
                        end_date=end_date,
                        reason=fake.sentence(),
                        status=random.choice(['PENDING', 'APPROVED', 'DENIED']),  # 更多拒绝的
                        approved_by=fake.name() if random.random() < 0.8 else ''
                    )