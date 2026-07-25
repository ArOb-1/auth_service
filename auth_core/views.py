from django.http import JsonResponse
from django.db import transaction
import jwt
from django.views.decorators.http import require_POST

from users.models import User
from access_control.models import Role
from access_control.choices import RoleName

from .utils import (
    hash_password,
    check_password,
    generate_access_token,
    generate_refresh_token,
    decode_token,
    parse_body,
    success,
    error,
)
from .exceptions import (
    TokenTypeMismatch
)


@require_POST
def register(request):
    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))
    email = body.get('email', '').strip()
    password = body.get('password', '').strip()

    if not email or not password:
        return error('Email and password are required')

    if User.objects.filter(email=email).exists():
        return error(f'email already registered: {email}', status=409)

    try:
        with transaction.atomic():
            role = Role.objects.get(name=RoleName.USER)
            user = User.objects.create(
                email=email,
                password_hash=hash_password(password),
                role=role,
            )
            access_token = generate_access_token(user.id, user.role.name)
            refresh_token = generate_refresh_token(user.id)

        return success({
            'user_id': str(user.id),
            'access_token': access_token,
            'refresh_token': refresh_token,
        }, status=201)

    except Exception as e:
        return error(f'Registration failed error: {str(e)}', status=500)


@require_POST
def login(request):
    try:
        body = parse_body(request)
    except ValueError as e:
        raise error(str(e))

    email = body.get('email', '').strip()
    password = body.get('password', '').strip()

    if not email or not password:
        return error('Email and password are required')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return error('User not found', status=401)

    if not check_password(password, user.password_hash):
        return error('Invalid password', status=401)

    return success({
        'access_token':  generate_access_token(user.id, user.role.name),
        'refresh_token': generate_refresh_token(user.id),
    })


@require_POST
def refresh(request):
    try:
        body = parse_body(request)
    except ValueError as e:
        return error(str(e))

    token = body.get('refresh_token', '').strip()

    if not token:
        return error('refresh token is required')

    try:
        payload = decode_token(token)

        if payload.get('type') != 'refresh':
            raise TokenTypeMismatch()

        user = User.objects.get(id=payload['user_id'])
    except jwt.ExpiredSignatureError:
        return error('Refresh token has expired', status=401)
    except jwt.InvalidTokenError:
        return error('Invalid refresh token', status=401)
    except TokenTypeMismatch:
        return error('Invalid token type', status=401)
    except User.DoesNotExist:
        return error('User not found', status=401)

    return success({
        'access_token':  generate_access_token(user.id, user.role.name),
        'refresh_token': generate_refresh_token(user.id),
    })


@require_POST
def logout(request):
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return error('Unauthorized', status=401)
    token = auth_header.split(' ')[1]
    payload = decode_token(token)

    if payload is None:
        return error('Unauthorized', status=401)

    return success({'message': 'Logged out successfully'})
