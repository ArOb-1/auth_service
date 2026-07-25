import json
import pytest

from users.models import User
from access_control.models import Role
from access_control.choices import RoleName
from auth_core.utils import hash_password, check_password, generate_access_token


@pytest.mark.django_db
class TestUserMe:

    def test_get_own_profile(self, client, regular_user, access_token):
        res = client.get(
            '/users/me/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 200
        data = res.json()
        assert data['email'] == regular_user.email
        assert str(data['id']) == str(regular_user.id)

    def test_unauthenticated_cannot_get_profile(self, client):
        res = client.get('/users/me/')
        assert res.status_code == 401


@pytest.mark.django_db
class TestUserUpdate:

    def test_update_first_name(self, client, regular_user, access_token):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({'first_name': 'John'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 200
        regular_user.refresh_from_db()
        assert regular_user.first_name == 'John'

    def test_update_last_name(self, client, regular_user, access_token):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({'last_name': 'Doe'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 200
        regular_user.refresh_from_db()
        assert regular_user.last_name == 'Doe'

    def test_update_patronymic(self, client, regular_user, access_token):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({'patronymic': 'Jr'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 200
        regular_user.refresh_from_db()
        assert regular_user.patronymic == 'Jr'

    def test_update_email(self, client, regular_user, access_token):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({'email': 'newemail@example.com'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 200
        regular_user.refresh_from_db()
        assert regular_user.email == 'newemail@example.com'

    def test_update_email_already_taken(self,
                                        client,
                                        regular_user,
                                        regular_user_2,
                                        access_token):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({'email': regular_user_2.email}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 409
        regular_user.refresh_from_db()
        assert regular_user.email == 'user@test.com'

    def test_update_password(self, client, regular_user, access_token):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({
                'old_password': 'testpass123',
                'new_password': 'newpassword456',
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 200
        regular_user.refresh_from_db()
        assert check_password('newpassword456', regular_user.password_hash)

    def test_update_password_wrong_old(self,
                                       client,
                                       regular_user,
                                       access_token):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({
                'old_password': 'wrongpassword',
                'new_password': 'newpassword456',
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 401
        regular_user.refresh_from_db()
        assert check_password('testpass123', regular_user.password_hash)

    def test_update_password_missing_old(self,
                                         client,
                                         regular_user,
                                         access_token):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({'new_password': 'newpassword456'}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 400

    def test_update_no_fields(self, client, regular_user, access_token):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({}),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 400

    def test_unauthenticated_cannot_update(self, client):
        res = client.patch(
            '/users/me/update/',
            data=json.dumps({'first_name': 'John'}),
            content_type='application/json',
        )
        assert res.status_code == 401


@pytest.mark.django_db
class TestUserDelete:

    def test_soft_delete(self, client, regular_user, access_token):
        res = client.delete(
            '/users/me/delete/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 200
        regular_user.refresh_from_db()
        assert regular_user.is_active is False

    def test_record_remains_in_db_after_delete(self,
                                               client,
                                               regular_user,
                                               access_token):
        client.delete(
            '/users/me/delete/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert User.objects.filter(id=regular_user.id).exists()

    def test_cannot_login_after_delete(self,
                                       client,
                                       regular_user,
                                       access_token):
        client.delete(
            '/users/me/delete/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        res = client.post(
            '/auth/login/',
            data=json.dumps({
                'email': 'user@test.com',
                'password': 'testpass123',
            }),
            content_type='application/json',
        )
        assert res.status_code == 401

    def test_old_token_invalid_after_delete(self,
                                            client,
                                            regular_user,
                                            access_token):
        client.delete(
            '/users/me/delete/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        res = client.get(
            '/users/me/',
            HTTP_AUTHORIZATION=f'Bearer {access_token}',
        )
        assert res.status_code == 401

    def test_unauthenticated_cannot_delete(self, client):
        res = client.delete('/users/me/delete/')
        assert res.status_code == 401
