from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Avg

from rest_framework.permissions import IsAuthenticated

from .models import Employee, Performance
from .serializers import EmployeeListSerializer, EmployeeDetailSerializer, PerformanceSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    """Employee management ViewSet providing CRUD operations and custom actions.
    
    Features:
    - Dynamic serializer selection based on action type
    - Advanced filtering, searching, and sorting capabilities
    - Custom actions for employee activation/deactivation
    - Employee profile endpoint with performance and attendance stats
    """
    queryset = Employee.objects.select_related('department').all()
    permission_classes = [IsAuthenticated]  # 暂时简化权限
    
    # Filter, search, and ordering configuration
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'employment_status', 'is_active', 'gender']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id', 'position']
    ordering_fields = ['first_name', 'last_name', 'date_joined', 'salary']
    ordering = ['first_name', 'last_name']

    def get_serializer_class(self):
        """Returns appropriate serializer based on action type.
        
        Returns:
            EmployeeListSerializer for list actions
            EmployeeDetailSerializer for all other actions
        """
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer

    def get_queryset(self):
        """Returns filtered queryset supporting date range filtering.
        
        Query Parameters:
            date_from: Filter employees joined on or after this date
            date_to: Filter employees joined on or before this date
        """
        queryset = Employee.objects.select_related('department').all()
        
        # Filter by joining date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date_joined__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_joined__lte=date_to)
            
        return queryset

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activates an employee by setting status to active.
        
        Args:
            request: HTTP request object
            pk: Employee primary key
            
        Returns:
            Response with success message and updated employee data
        """
        employee = self.get_object()
        employee.is_active = True
        employee.employment_status = 'ACTIVE'
        employee.save()
        
        serializer = self.get_serializer(employee)
        return Response({
            'message': f'Employee "{employee.full_name}" has been activated.',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivates an employee by setting status to inactive.
        
        Args:
            request: HTTP request object
            pk: Employee primary key
            
        Returns:
            Response with success message and updated employee data
        """
        employee = self.get_object()
        employee.is_active = False
        employee.employment_status = 'INACTIVE'
        employee.save()
        
        serializer = self.get_serializer(employee)
        return Response({
            'message': f'Employee "{employee.full_name}" has been deactivated.',
            'data': serializer.data
        })

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Returns comprehensive employee profile with statistics.
        
        Includes:
        - Basic employee information
        - Recent performance reviews (last 5)
        - Attendance statistics and rates
        
        Args:
            request: HTTP request object
            pk: Employee primary key
            
        Returns:
            Response containing employee profile data
        """
        employee = self.get_object()
        
        # Get recent performance reviews
        recent_performances = employee.performances.all()[:5]
        
        # Calculate attendance statistics
        total_attendance = employee.attendances.count()
        present_days = employee.attendances.filter(status__in=['PRESENT', 'LATE']).count()
        attendance_rate = (present_days / total_attendance * 100) if total_attendance > 0 else 0
        
        profile_data = {
            'employee': self.get_serializer(employee).data,
            'recent_performances': PerformanceSerializer(recent_performances, many=True).data,
            'attendance_stats': {
                'total_days': total_attendance,
                'present_days': present_days,
                'attendance_rate': round(attendance_rate, 2)
            }
        }
        
        return Response(profile_data)

class PerformanceViewSet(viewsets.ModelViewSet):
    """Performance review management ViewSet with filtering capabilities."""
    queryset = Performance.objects.select_related('employee').all()
    serializer_class = PerformanceSerializer
    permission_classes = [IsAuthenticated]  # 暂时简化权限
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'rating', 'employee__department']
    search_fields = ['employee__first_name', 'employee__last_name', 'reviewer']
    ordering_fields = ['review_date', 'rating']
    ordering = ['-review_date']

    def get_queryset(self):
        """Returns filtered queryset supporting review date range filtering.
        
        Query Parameters:
            date_from: Filter reviews on or after this date
            date_to: Filter reviews on or before this date
        """
        queryset = Performance.objects.select_related('employee').all()
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(review_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(review_date__lte=date_to)
            
        return queryset

class EmployeeAnalyticsView(APIView):
    """Employee analytics API providing statistical insights."""
    
    def get(self, request):
        """Returns comprehensive employee analytics data.
        
        Includes:
        - Employee count statistics
        - Department distribution
        - Employment status breakdown
        - Salary analytics by department
        - Performance review summary
        
        Returns:
            Response containing analytics data
        """
        # Basic statistics
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(is_active=True).count()
        
        # Employees by department
        employees_by_dept = Employee.objects.filter(is_active=True).values(
            'department__name'
        ).annotate(count=Count('id')).order_by('-count')
        
        # Employment status distribution
        status_distribution = Employee.objects.values(
            'employment_status'
        ).annotate(count=Count('id')).order_by('-count')
        
        # Average salary by department
        salary_by_dept = Employee.objects.filter(is_active=True).values(
            'department__name'
        ).annotate(avg_salary=Avg('salary')).order_by('-avg_salary')
        
        # Performance overview
        total_reviews = Performance.objects.count()
        average_rating = Performance.objects.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        
        analytics_data = {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'inactive_employees': total_employees - active_employees,
            'employees_by_department': list(employees_by_dept),
            'employment_status_distribution': list(status_distribution),
            'salary_by_department': [
                {
                    'department': item['department__name'],
                    'avg_salary': round(float(item['avg_salary']), 2)
                }
                for item in salary_by_dept
            ],
            'performance_summary': {
                'total_reviews': total_reviews,
                'average_rating': round(float(average_rating), 2)
            }
        }
        
        return Response(analytics_data)
    
from django.shortcuts import render

class DashboardView(APIView):
    """Dashboard view rendering the analytics visualization page."""
    
    def get(self, request):
        """Renders the dashboard HTML template."""
        return render(request, 'dashboard.html')
    
from django.shortcuts import render

class EmployeeListView(APIView):
    """Employee list view with Django template."""
    
    def get(self, request):
        return render(request, 'employee_list.html')

class DepartmentListView(APIView):
    """Department list view with Django template."""
    
    def get(self, request):
        return render(request, 'department_list.html')

class AttendanceListView(APIView):
    """Attendance list view with Django template."""
    
    def get(self, request):
        return render(request, 'attendance_list.html')