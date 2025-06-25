from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, date
from collections import defaultdict
import calendar

from .models import Attendance, LeaveRequest
from .serializers import (
    AttendanceListSerializer, AttendanceDetailSerializer,
    LeaveRequestListSerializer, LeaveRequestDetailSerializer
)

class AttendanceViewSet(viewsets.ModelViewSet):
    """Attendance management ViewSet with advanced filtering and bulk operations.
    
    Features:
    - Date range and monthly filtering
    - Bulk attendance record creation
    - Individual employee attendance summaries
    - Dynamic serializer selection
    """
    queryset = Attendance.objects.select_related('employee').all()
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'status', 'employee__department']
    search_fields = ['employee__first_name', 'employee__last_name', 'notes']
    ordering_fields = ['date', 'check_in_time']
    ordering = ['-date']

    def get_serializer_class(self):
        """Returns appropriate serializer based on action type."""
        if self.action == 'list':
            return AttendanceListSerializer
        return AttendanceDetailSerializer

    def get_queryset(self):
        """Returns filtered queryset supporting date range and monthly filtering.
        
        Query Parameters:
            date_from: Filter records on or after this date
            date_to: Filter records on or before this date
            month: Filter records for specific month (1-12)
            year: Filter records for specific year
        """
        queryset = Attendance.objects.select_related('employee').all()
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Monthly filtering
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif year:
            queryset = queryset.filter(date__year=year)
            
        return queryset

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Creates multiple attendance records in a single request.
        
        Processes array of attendance records, validates each one, and returns
        summary of successful creations and validation errors.
        
        Request Body:
            attendance_records: Array of attendance record objects
            
        Returns:
            Response with creation summary and error details
        """
        attendance_records = request.data.get('attendance_records', [])
        
        if not attendance_records:
            return Response(
                {'error': 'No attendance records provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_records = []
        errors = []
        
        for record_data in attendance_records:
            serializer = AttendanceDetailSerializer(data=record_data)
            if serializer.is_valid():
                created_records.append(serializer.save())
            else:
                errors.append({
                    'data': record_data,
                    'errors': serializer.errors
                })
        
        return Response({
            'created_count': len(created_records),
            'error_count': len(errors),
            'created_records': AttendanceDetailSerializer(created_records, many=True).data,
            'errors': errors
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Returns attendance summary statistics for a specific employee.
        
        Calculates attendance rates, working hours, and presence statistics
        for the specified time period.
        
        Query Parameters:
            employee_id: Required employee ID
            month: Optional month filter (1-12)
            year: Optional year filter
            
        Returns:
            Response with attendance summary statistics
        """
        employee_id = request.query_params.get('employee_id')
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        if not employee_id:
            return Response(
                {'error': 'employee_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Attendance.objects.filter(employee_id=employee_id)
        
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif year:
            queryset = queryset.filter(date__year=year)
        
        # Calculate statistics
        total_days = queryset.count()
        present_days = queryset.filter(status__in=['PRESENT', 'LATE']).count()
        absent_days = queryset.filter(status='ABSENT').count()
        late_days = queryset.filter(status='LATE').count()
        
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        # Calculate average working hours
        working_records = queryset.exclude(
            Q(check_in_time__isnull=True) | Q(check_out_time__isnull=True)
        )
        
        total_working_hours = sum(record.working_hours for record in working_records)
        average_working_hours = (
            total_working_hours / working_records.count()
            if working_records.count() > 0 else 0
        )
        
        # Get employee name
        employee_name = "Unknown"
        if queryset.exists():
            employee_name = queryset.first().employee.full_name
        
        return Response({
            'employee_name': employee_name,
            'period': f"{month}/{year}" if month and year else str(year) if year else "All time",
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'attendance_rate': round(attendance_rate, 2),
            'average_working_hours': round(average_working_hours, 2)
        })

class LeaveRequestViewSet(viewsets.ModelViewSet):
    """Leave request management ViewSet with approval workflow.
    
    Features:
    - Leave request CRUD operations
    - Approval and rejection actions
    - Date range filtering
    - Status-based filtering
    """
    queryset = LeaveRequest.objects.select_related('employee').all()
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'leave_type', 'status', 'employee__department']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    ordering_fields = ['created_at', 'start_date', 'end_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Returns appropriate serializer based on action type."""
        if self.action == 'list':
            return LeaveRequestListSerializer
        return LeaveRequestDetailSerializer

    def get_queryset(self):
        """Returns filtered queryset supporting date range filtering.
        
        Query Parameters:
            date_from: Filter requests starting on or after this date
            date_to: Filter requests ending on or before this date
        """
        queryset = LeaveRequest.objects.select_related('employee').all()
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(start_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(end_date__lte=date_to)
            
        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approves a pending leave request.
        
        Args:
            request: HTTP request object
            pk: Leave request primary key
            
        Returns:
            Response with success message and updated request data
        """
        leave_request = self.get_object()
        
        if leave_request.status != 'PENDING':
            return Response(
                {'error': 'Only pending leave requests can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        leave_request.status = 'APPROVED'
        leave_request.approved_by = request.data.get('approved_by', 'System')
        leave_request.save()
        
        serializer = self.get_serializer(leave_request)
        return Response({
            'message': 'Leave request approved successfully',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejects a pending leave request.
        
        Args:
            request: HTTP request object
            pk: Leave request primary key
            
        Returns:
            Response with success message and updated request data
        """
        leave_request = self.get_object()
        
        if leave_request.status != 'PENDING':
            return Response(
                {'error': 'Only pending leave requests can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        leave_request.status = 'REJECTED'
        leave_request.approved_by = request.data.get('approved_by', 'System')
        leave_request.save()
        
        serializer = self.get_serializer(leave_request)
        return Response({
            'message': 'Leave request rejected',
            'data': serializer.data
        })

class AttendanceAnalyticsView(APIView):
    """Attendance analytics API providing comprehensive statistical insights."""
    
    def get(self, request):
        """Returns comprehensive attendance analytics data."""
        month = request.query_params.get('month')
        year = request.query_params.get('year', timezone.now().year)
        
        queryset = Attendance.objects.select_related('employee__department')
        
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif year:
            queryset = queryset.filter(date__year=year)
        
        # Monthly overview - 生成最近6个月的数据
        monthly_data = defaultdict(lambda: {'present': 0, 'absent': 0, 'late': 0})
        
        # 获取最近6个月
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)
        
        # 按月份统计实际数据
        for record in queryset.filter(date__gte=start_date):
            month_name = calendar.month_name[record.date.month]
            if record.status == 'PRESENT':
                monthly_data[month_name]['present'] += 1
            elif record.status == 'ABSENT':
                monthly_data[month_name]['absent'] += 1
            elif record.status == 'LATE':
                monthly_data[month_name]['late'] += 1
        
        # 确保所有月份都有数据（即使是0）
        current_date = start_date
        while current_date <= end_date:
            month_name = calendar.month_name[current_date.month]
            if month_name not in monthly_data:
                monthly_data[month_name] = {'present': 0, 'absent': 0, 'late': 0}
            current_date = current_date.replace(day=1)
            # 移动到下个月
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        monthly_overview = []
        
        # 按时间顺序排列最近6个月
        for i in range(6):
            target_date = end_date - timedelta(days=30 * i)
            month_name = calendar.month_name[target_date.month]
            if month_name in monthly_data:
                monthly_overview.append({
                    'month': month_name,
                    'present': monthly_data[month_name]['present'],
                    'absent': monthly_data[month_name]['absent'],
                    'late': monthly_data[month_name]['late']
                })
        
        # 反转顺序，让最早的月份在前面
        monthly_overview.reverse()
        
        # 其余代码保持不变...
        status_counts = queryset.values('status').annotate(count=Count('id')).order_by('-count')
        attendance_by_status = [
            {'status': item['status'], 'count': item['count']}
            for item in status_counts
        ]
        
        # Department-wise attendance rates
        dept_stats = {}
        for record in queryset:
            dept_name = record.employee.department.name
            if dept_name not in dept_stats:
                dept_stats[dept_name] = {'total': 0, 'present': 0}
            
            dept_stats[dept_name]['total'] += 1
            if record.status in ['PRESENT', 'LATE']:
                dept_stats[dept_name]['present'] += 1
        
        department_wise_attendance = [
            {
                'department': dept_name,
                'attendance_rate': round(
                    (stats['present'] / stats['total'] * 100) if stats['total'] > 0 else 0, 2
                )
            }
            for dept_name, stats in dept_stats.items()
        ]
        
        # Average working hours calculation
        working_records = queryset.exclude(
            Q(check_in_time__isnull=True) | Q(check_out_time__isnull=True)
        )
        
        total_working_hours = sum(record.working_hours for record in working_records)
        average_working_hours = (
            total_working_hours / working_records.count()
            if working_records.count() > 0 else 0
        )
        
        return Response({
            'period': f"{month}/{year}" if month else str(year),
            'total_records': queryset.count(),
            'monthly_overview': monthly_overview,
            'attendance_by_status': attendance_by_status,
            'department_wise_attendance': department_wise_attendance,
            'average_working_hours': round(average_working_hours, 2)
        })