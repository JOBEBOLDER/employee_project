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
    """
    考勤管理ViewSet
    """
    queryset = Attendance.objects.select_related('employee').all()
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'status', 'employee__department']
    search_fields = ['employee__first_name', 'employee__last_name', 'notes']
    ordering_fields = ['date', 'check_in_time']
    ordering = ['-date']

    def get_serializer_class(self):
        """根据操作类型返回不同的序列化器"""
        if self.action == 'list':
            return AttendanceListSerializer
        return AttendanceDetailSerializer

    def get_queryset(self):
        """支持日期范围和月份过滤"""
        queryset = Attendance.objects.select_related('employee').all()
        
        # 日期范围过滤
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # 月份过滤
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif year:
            queryset = queryset.filter(date__year=year)
            
        return queryset

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """批量创建考勤记录"""
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
        """获取考勤汇总统计"""
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
        
        # 计算统计数据
        total_days = queryset.count()
        present_days = queryset.filter(status__in=['PRESENT', 'LATE']).count()
        absent_days = queryset.filter(status='ABSENT').count()
        late_days = queryset.filter(status='LATE').count()
        
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        # 计算平均工作时间
        working_records = queryset.exclude(
            Q(check_in_time__isnull=True) | Q(check_out_time__isnull=True)
        )
        
        total_working_hours = sum(record.working_hours for record in working_records)
        average_working_hours = (
            total_working_hours / working_records.count()
            if working_records.count() > 0 else 0
        )
        
        # 获取员工姓名
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
    """
    请假申请管理ViewSet
    """
    queryset = LeaveRequest.objects.select_related('employee').all()
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['employee', 'leave_type', 'status', 'employee__department']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    ordering_fields = ['created_at', 'start_date', 'end_date']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """根据操作类型返回不同的序列化器"""
        if self.action == 'list':
            return LeaveRequestListSerializer
        return LeaveRequestDetailSerializer

    def get_queryset(self):
        """支持日期范围过滤"""
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
        """批准请假申请"""
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
        """拒绝请假申请"""
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
    """
    考勤数据分析API
    """
    def get(self, request):
        """获取考勤分析数据"""
        month = request.query_params.get('month')
        year = request.query_params.get('year', timezone.now().year)
        
        queryset = Attendance.objects.select_related('employee__department')
        
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        elif year:
            queryset = queryset.filter(date__year=year)
        
        # 月度概览
        monthly_data = defaultdict(lambda: {'present': 0, 'absent': 0, 'late': 0})
        
        for record in queryset.filter(date__year=year):
            month_name = calendar.month_name[record.date.month]
            if record.status == 'PRESENT':
                monthly_data[month_name]['present'] += 1
            elif record.status == 'ABSENT':
                monthly_data[month_name]['absent'] += 1
            elif record.status == 'LATE':
                monthly_data[month_name]['late'] += 1
        
        monthly_overview = [
            {
                'month': month_name,
                'present': data['present'],
                'absent': data['absent'],
                'late': data['late']
            }
            for month_name, data in monthly_data.items()
        ]
        
        # 按状态统计
        status_counts = queryset.values('status').annotate(count=Count('id')).order_by('-count')
        attendance_by_status = [
            {'status': item['status'], 'count': item['count']}
            for item in status_counts
        ]
        
        # 部门出勤率
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
        
        # 平均工作时间
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