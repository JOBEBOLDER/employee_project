from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Department
from .serializers import DepartmentSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing departments
    Provides CRUD operations: Create, Read, Update, Delete
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    
    # 添加过滤、搜索、排序功能
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']  # 可以按是否激活过滤
    search_fields = ['name', 'description']  # 可以搜索名称和描述
    ordering_fields = ['name', 'created_at']  # 可以按名称或创建时间排序
    ordering = ['name']  # 默认按名称排序

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Custom action to activate a department
        URL: /api/departments/{id}/activate/
        """
        department = self.get_object()
        department.is_active = True
        department.save()
        
        serializer = self.get_serializer(department)
        return Response({
            'message': f'Department "{department.name}" has been activated.',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Custom action to deactivate a department
        URL: /api/departments/{id}/deactivate/
        """
        department = self.get_object()
        
        # 检查是否有活跃员工
        active_employees = department.employees.filter(is_active=True).count()
        if active_employees > 0:
            return Response(
                {'error': f'Cannot deactivate department. It has {active_employees} active employees.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        department.is_active = False
        department.save()
        
        serializer = self.get_serializer(department)
        return Response({
            'message': f'Department "{department.name}" has been deactivated.',
            'data': serializer.data
        })