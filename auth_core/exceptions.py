class NotAuthenticated(Exception):
    pass


class PermissionDenied(Exception):
    pass


class AuthError(Exception):
    status_code = 401
    message = 'Authentication error'

    def __init__(self, message: str = None):
        self.message = message or self.__class__.message
        super().__init__(self.message)


class TokenExpired(AuthError):
    status_code = 401
    message = 'Token has expired'


class TokenInvalid(AuthError):
    status_code = 401
    message = 'Token is invalid'


class UserNotFound(AuthError):
    status_code = 401
    message = 'User not found'


class TokenTypeMismatch(AuthError):
    status_code = 401
    message = 'Wrong token type'
