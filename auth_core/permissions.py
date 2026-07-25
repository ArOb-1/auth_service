from functools import wraps
from django.http import JsonResponse

from access_control.models import Role, RolePolicy
from access_control.choices import RoleName
from .exceptions import NotAuthenticated, PermissionDenied


def get_scope(user, resource: str, action: str) -> str:
    if user is None or not user.is_authenticated:
        role = Role.objects.get(name=RoleName.GUEST)
    else:
        role = user.role

    try:
        policy = RolePolicy.objects.get(
            role=role,
            resource=resource,
            action=action
        )
        return policy.scope
    except RolePolicy.DoesNotExist:
        if user is not None and user.is_authenticated:
            raise PermissionDenied
        raise NotAuthenticated


def require_permission(resourse: str, action: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                request.scope = get_scope(request.user,
                                          resourse,
                                          action)
                return view_func(request,
                                 *args,
                                 **kwargs)
            except NotAuthenticated:
                return JsonResponse(
                    {'error': 'Authentication required'},
                    status=401,
                )
            except PermissionDenied:
                return JsonResponse(
                    {'error': 'Permission denied'},
                    status=403,
                )
            except Role.DoesNotExist:
                return JsonResponse(
                    {'error': 'Role not found'},
                    status=500,
                )
        return wrapper
    return decorator
