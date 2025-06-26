from rest_framework import permissions

class RoleBasedPermission(permissions.BasePermission):
    """Custom permission class for role-based access control."""
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if not request.user.is_authenticated:
            return False
        
        # Superuser has all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user has profile
        if not hasattr(request.user, 'profile'):
            return False
        
        user_role = request.user.profile.role
        
        # Define view permissions
        view_permissions = {
            'EmployeeViewSet': {
                'ADMIN': ['list', 'create', 'retrieve', 'update', 'destroy'],
                'HR': ['list', 'create', 'retrieve', 'update'],
                'MANAGER': ['list', 'retrieve', 'update'],
                'EMPLOYEE': ['list', 'retrieve'],
            },
            'DepartmentViewSet': {
                'ADMIN': ['list', 'create', 'retrieve', 'update', 'destroy'],
                'HR': ['list', 'retrieve'],
                'MANAGER': ['list', 'retrieve'],
                'EMPLOYEE': ['list', 'retrieve'],
            },
            'AttendanceViewSet': {
                'ADMIN': ['list', 'create', 'retrieve', 'update', 'destroy'],
                'HR': ['list', 'create', 'retrieve', 'update'],
                'MANAGER': ['list', 'retrieve'],
                'EMPLOYEE': ['list', 'create', 'retrieve'],
            }
        }
        
        view_name = view.__class__.__name__
        allowed_actions = view_permissions.get(view_name, {}).get(user_role, [])
        
        return view.action in allowed_actions

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object."""
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        user_role = request.user.profile.role
        
        # Employees can only access their own records
        if user_role == 'EMPLOYEE':
            if hasattr(obj, 'employee'):
                return obj.employee.user_profile.user == request.user
            elif hasattr(obj, 'user'):
                return obj.user == request.user
        
        return True


# Django view decorators (不使用DRF的装饰器)
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(allowed_roles):
    """Decorator to check if user has required role."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if not hasattr(request.user, 'profile'):
                raise PermissionDenied("User profile not found")
            
            if request.user.profile.role not in allowed_roles:
                raise PermissionDenied("Insufficient permissions")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

# Convenience decorators
admin_required = role_required(['ADMIN'])
hr_required = role_required(['ADMIN', 'HR'])
manager_required = role_required(['ADMIN', 'HR', 'MANAGER'])