from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.role not in roles:
                raise PermissionDenied("You do not have permission to perform this action.")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator