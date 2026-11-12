# dashboard/access.py
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def staff_required(view):
    """Logged-in staff (admins and superusers) only. Everyone else gets a 403 page."""
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapper


def home_for(user):
    """Which dashboard a user lands on after logging in."""
    return 'dashboard:admin_home' if user.is_staff else 'dashboard:teacher'