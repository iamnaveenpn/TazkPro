from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden

def admin_required(view_func):
    """Decorator to require admin role"""
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.is_admin():
            messages.error(request, 'You need admin privileges to access this page.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def employee_required(view_func):
    """Decorator to require employee role"""
    @wraps(view_func)
    @login_required  
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'User profile not found.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

class AdminRequiredMixin:
    """Mixin to require admin role for class-based views"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile') or not request.user.profile.is_admin():
            messages.error(request, 'You need admin privileges to access this page.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

class EmployeeRequiredMixin:
    """Mixin to require employee role for class-based views"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'User profile not found.')
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
