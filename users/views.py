from django.views.decorators.http import require_http_methods

from auth_core.utils import (
    parse_body,
    success,
    error,
    hash_password,
    check_password,
)
from auth_core.permissions import require_permission
from access_control.choices import Resource, Action


@require_http_methods(['GET'])
@require_permission(Resource.USERS, Action.READ)
def user_me(request):
    user = request.user
    return success({
        'id':         str(user.id),
        'first_name': user.first_name,
        'last_name':  user.last_name,
        'patronymic': user.patronymic,
        'email':      user.email,
        'role':       user.role.name if user.role else None,
        'created_at': user.created_at.isoformat(),
    })


@require_http_methods(['PATCH'])
@require_permission(Resource.USERS, Action.UPDATE)
def user_update(request):
    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))

    user = request.user
    updated = []

    for field in ['first_name', 'last_name', 'patronymic']:
        if field in body:
            setattr(user, field, body[field].strip())
            updated.append(field)

    if 'email' in body:
        from users.models import User
        new_email = body['email'].strip()
        if not new_email:
            return error('Email cannot be empty')
        if User.objects.filter(email=new_email).exclude(id=user.id).exists():
            return error('Email already registered', status=409)
        user.email = new_email
        updated.append('email')

    if 'new_password' in body:
        old_password = body.get('old_password', '').strip()
        new_password = body.get('new_password', '').strip()

        if not old_password:
            return error('old_password is required to change password')
        if not check_password(old_password, user.password_hash):
            return error('Invalid old password', status=401)
        if not new_password:
            return error('new_password cannot be empty')

        user.password_hash = hash_password(new_password)
        updated.append('password')

    if not updated:
        return error('No fields to update')

    user.save()
    return success({'message': 'Profile updated', 'updated': updated})


@require_http_methods(['DELETE'])
@require_permission(Resource.USERS, Action.DELETE)
def user_delete(request):
    user = request.user
    user.is_active = False
    user.save(update_fields=['is_active', 'updated_at'])
    return success({'message': 'Account deleted'})
