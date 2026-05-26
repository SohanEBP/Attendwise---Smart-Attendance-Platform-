from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        try:
            if request.user.profile.role == 'admin':
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'You do not have admin access.')
        return redirect('dashboard')
    return wrapper


def teacher_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            if request.user.profile.role in ('teacher', 'admin') or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'Teacher access required.')
        return redirect('dashboard')
    return wrapper


def student_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            if request.user.profile.role == 'student':
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'Student access required.')
        return redirect('dashboard')
    return wrapper
