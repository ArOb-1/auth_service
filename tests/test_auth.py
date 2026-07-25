import pytest
import json

from users.models import User

pytestmark = pytest.mark.django_db


class TestRegister:
    url = '/auth/register/'

    def post(self, data, client):
        return client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_success(self, client):
        resp = self.post(data={'email': 'new@test.com',
                               'password': 'pass123'}, client=client)
        assert resp.status_code == 201

    def test_duplicate_email(self, client, regular_user):
        resp = self.post(data={'email': 'user@test.com',
                               'password': 'pass123'},
                         client=client)
        assert resp.status_code == 409

    def test_missing_email(self, client):
        resp = self.post(data={'password': 'pass123'},
                         client=client)
        assert resp.status_code == 400

    def test_missing_password(self, client):
        resp = self.post(data={'email': 'new@test.com'},
                         client=client)
        assert resp.status_code == 400

    def test_no_user_on_missing_email(self, client):
        before = User.objects.count()
        self.post(data={'password': 'pass123'}, client=client)
        assert User.objects.count() == before

    def test_no_user_on_missing_password(self, client):
        before = User.objects.count()
        self.post(data={'email': 'new@test.com'}, client=client)
        assert User.objects.count() == before

    def test_no_user_on_duplicate_email(self, client, regular_user):
        before = User.objects.count()
        self.post(data={'email': 'user@test.com', 'password': 'pass123'},
                  client=client)
        assert User.objects.count() == before


class TestLogin:
    url = '/auth/login/'

    def post(self, data, client):
        return client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_success(self, client, regular_user):
        resp = self.post(data={'email': 'user@test.com',
                               'password': 'testpass123'},
                         client=client)
        assert resp.status_code == 200
        data = resp.json()
        assert 'access_token' in data
        assert 'refresh_token' in data

    def test_wrong_password(self, client, regular_user):
        resp = self.post(data={'email': 'user@test.com',
                               'password': 'wrong'},
                         client=client)
        assert resp.status_code == 401

    def test_user_not_found(self, client):
        resp = self.post(data={'email': 'ghost@test.com',
                               'password': 'testpass123'},
                         client=client)
        assert resp.status_code in (401, 404)


class TestRefresh:
    login_url = '/auth/login/'
    url = '/auth/refresh/'

    def post(self, data, client):
        return client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def _get_tokens(self, client, user):
        resp = client.post(
            self.login_url,
            data=json.dumps({'email': user.email, 'password': 'testpass123'}),
            content_type='application/json',
        )
        return resp.json()

    def test_success(self, client, regular_user):
        tokens = self._get_tokens(client, regular_user)
        resp = self.post(data={
            'refresh_token': tokens.get('refresh_token')
            }, client=client)
        assert resp.status_code == 200
        assert 'access_token' in resp.json()

    def test_invalid_token(self, client):
        resp = self.post(data={
            'refresh_token': 'bad.token.here'
        }, client=client)
        assert resp.status_code == 401


class TestLogout:
    url = '/auth/logout/'

    def test_success(self, client, user_headers):
        resp = client.post(self.url, **user_headers)
        assert resp.status_code == 200

    def test_no_auth(self, client):
        resp = client.post(self.url)
        assert resp.status_code == 401
