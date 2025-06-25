from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Avg

from .models import Employee, Performance
from .serializers import EmployeeListSerializer, EmployeeDetailSerializer, PerformanceSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Employee Management ViewSet 
    Provides complete employee CRUD operations and customization features
    """
    queryset = Employee.objects.select_related('department').all()
    
    # 过滤、搜索、排序配置
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'employment_status', 'is_active', 'gender']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id', 'position']
    ordering_fields = ['first_name', 'last_name', 'date_joined', 'salary']
    ordering = ['first_name', 'last_name']

    def get_serializer_class(self):
        """根据操作类型返回不同的序列化器"""
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer

    def get_queryset(self):
        """支持日期范围过滤"""
        queryset = Employee.objects.select_related('department').all()
        
        # 按入职日期范围过滤
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date_joined__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_joined__lte=date_to)
            
        return queryset

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活员工"""
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
        """停用员工"""
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
        """获取员工详细档案，包括绩效和考勤统计"""
        employee = self.get_object()
        
        # 获取最近的绩效评估
        recent_performances = employee.performances.all()[:5]
        
        # 获取考勤统计
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
    """
    Performance Appraisal Management ViewSet
    """
    queryset = Performance.objects.select_related('employee').all()
    serializer_class = PerformanceSerializer
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'rating', 'employee__department']
    search_fields = ['employee__first_name', 'employee__last_name', 'reviewer']
    ordering_fields = ['review_date', 'rating']
    ordering = ['-review_date']

    def get_queryset(self):
        """支持评估日期范围过滤"""
        queryset = Performance.objects.select_related('employee').all()
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(review_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(review_date__lte=date_to)
            
        return queryset

class EmployeeAnalyticsView(APIView):
    """
    员工数据分析API
    """
    def get(self, request):
        """获取员工统计分析数据"""
        # 基础统计
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(is_active=True).count()
        
        # 按部门统计员工
        employees_by_dept = Employee.objects.filter(is_active=True).values(
            'department__name'
        ).annotate(count=Count('id')).order_by('-count')
        
        # 按状态统计员工
        status_distribution = Employee.objects.values(
            'employment_status'
        ).annotate(count=Count('id')).order_by('-count')
        
        # 平均工资按部门
        salary_by_dept = Employee.objects.filter(is_active=True).values(
            'department__name'
        ).annotate(avg_salary=Avg('salary')).order_by('-avg_salary')
        
        # 绩效概览
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
    """
    仪表板页面视图
    """
    def get(self, request):
        return render(request, 'dashboard.html')