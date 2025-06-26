from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

def login_view(request):
    """Web-based login view."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'auth/login.html')

def logout_view(request):
    """Web-based logout view."""
    logout(request)
    return redirect('login')

def register_view(request):
    """Web-based registration view (简化版)."""
    if not request.user.is_authenticated:
        return redirect('login')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            messages.success(request, f'User {username} created successfully')
            return redirect('register')
    
    return render(request, 'auth/register.html')

# 简化的API ViewSet
class AuthViewSet(viewsets.ViewSet):
    """Simple authentication ViewSet."""
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """User login endpoint."""
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': 'Username and password required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        
        if user:
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
            })
        
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """User logout endpoint."""
        try:
            request.user.auth_token.delete()
        except:
            pass
        
        return Response({'message': 'Successfully logged out'})