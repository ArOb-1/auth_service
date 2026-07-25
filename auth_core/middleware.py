import jwt
from .utils import decode_token
from users.models import User
from .exceptions import (
    TokenExpired,
    TokenInvalid,
    UserNotFound,
)


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user = None

        auth_header = request.headers.get('Authorization', '')

        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = decode_token(token)
                if payload.get('type') == 'access':
                    request.user = (
                        User.objects
                        .select_related('role')
                        .get(id=payload['user_id'], is_active=True)
                    )
            except jwt.ExpiredSignatureError:
                raise TokenExpired()
            except jwt.InvalidTokenError:
                raise TokenInvalid()
            except User.DoesNotExist:
                pass

        return self.get_response(request)
