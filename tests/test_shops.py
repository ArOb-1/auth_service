import pytest
from django.urls import reverse
from business.models import Shop

pytestmark = pytest.mark.django_db


class TestShopList:
    def test_admin_can_view_all_shops(self, client, admin_headers, shop, shop_2):
        """Админ видит все магазины"""
        response = client.get(reverse('shop_list'), **admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data['shops']) == 2
        shop_ids = [s['id'] for s in data['shops']]
        assert str(shop.id) in shop_ids
        assert str(shop_2.id) in shop_ids

    def test_manager_sees_all_shops(self, client, manager_headers, shop, shop_2):
        """Менеджер видит все магазины"""
        response = client.get(reverse('shop_list'), **manager_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data['shops']) == 2

    def test_user_sees_all_shops(self, client, user_headers, shop, shop_2):
        """Обычный пользователь видит все магазины"""
        response = client.get(reverse('shop_list'), **user_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data['shops']) == 2

    def test_guest_can_view_shops(self, client, guest_headers, shop):
        """Гость видит все магазины"""
        response = client.get(reverse('shop_list'), **guest_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data['shops']) >= 1


class TestShopCreate:
    def test_manager_can_create_shop(self, client, manager_headers, manager_user):
        """Менеджер может создать магазин"""
        data = {
            'name': 'New Shop',
            'description': 'Description'
        }
        response = client.post(
            reverse('shop_create'),
            data=data,
            content_type='application/json',
            **manager_headers
        )
        assert response.status_code == 201
        shop_id = response.json()['shop_id']
        shop = Shop.objects.get(id=shop_id)
        assert shop.name == 'New Shop'
        assert shop.owner == manager_user

    def test_user_cannot_create_shop(self, client, user_headers):
        """Обычный пользователь не может создать магазин"""
        data = {'name': 'New Shop'}
        response = client.post(
            reverse('shop_create'),
            data=data,
            content_type='application/json',
            **user_headers
        )
        assert response.status_code == 403
        assert 'Permission denied' in response.json()['error']

    def test_guest_cannot_create_shop(self, client, guest_headers):
        """Гость не может создать магазин"""
        data = {'name': 'New Shop'}
        response = client.post(
            reverse('shop_create'),
            data=data,
            content_type='application/json',
            **guest_headers
        )
        assert response.status_code == 403


class TestShopDetail:
    def test_manager_can_view_own_shop(self, client, manager_headers, shop):
        """Менеджер может просматривать свой магазин"""
        response = client.get(
            reverse('shop_detail', args=[shop.id]),
            **manager_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == str(shop.id)
        assert data['name'] == shop.name

    def test_user_can_view_any_shop(self, client, user_headers, shop):
        """Обычный пользователь может просматривать любой магазин"""
        response = client.get(
            reverse('shop_detail', args=[shop.id]),
            **user_headers
        )
        assert response.status_code == 200
        assert response.json()['id'] == str(shop.id)

    def test_shop_not_found(self, client, manager_headers):
        """Ошибка при запросе несуществующего магазина"""
        response = client.get(
            reverse('shop_detail', args=['00000000-0000-0000-0000-000000000000']),
            **manager_headers
        )
        assert response.status_code == 404
        assert 'Shop not found' in response.json()['error']


class TestShopUpdate:
    def test_manager_can_update_own_shop(self, client, manager_headers, shop):
        """Менеджер может обновить свой магазин"""
        data = {'name': 'Updated Name'}
        response = client.patch(
            reverse('shop_update', args=[shop.id]),
            data=data,
            content_type='application/json',
            **manager_headers
        )
        assert response.status_code == 200
        shop.refresh_from_db()
        assert shop.name == 'Updated Name'

    def test_manager_cannot_update_others_shop(self, client, manager_headers, shop_2):
        """Менеджер не может обновить чужой магазин"""
        data = {'name': 'Hacked Name'}
        response = client.patch(
            reverse('shop_update', args=[shop_2.id]),
            data=data,
            content_type='application/json',
            **manager_headers
        )
        assert response.status_code == 403
        assert 'Permission denied' in response.json()['error']

    def test_user_cannot_update_shop(self, client, user_headers, shop):
        """Обычный пользователь не может обновить магазин"""
        data = {'name': 'New Name'}
        response = client.patch(
            reverse('shop_update', args=[shop.id]),
            data=data,
            content_type='application/json',
            **user_headers
        )
        assert response.status_code == 403


class TestShopDelete:
    def test_manager_can_delete_own_shop(self, client, manager_headers, shop):
        """Менеджер может удалить свой магазин"""
        from access_control.models import RolePolicy, Role
        manager = Role.objects.get(name='manager')
        print('\n--- MANAGER ROLE:', manager)
        print('--- POLICIES:', list(RolePolicy.objects.filter(role=manager).values('resource', 'action', 'scope')))
        response = client.delete(
            reverse('shop_delete', args=[shop.id]),
            **manager_headers
        )

        assert response.status_code == 200
        assert not Shop.objects.filter(id=shop.id).exists()

    def test_manager_cannot_delete_others_shop(self, client, manager_headers, shop_2):
        """Менеджер не может удалить чужой магазин"""
        response = client.delete(
            reverse('shop_delete', args=[shop_2.id]),
            **manager_headers
        )
        assert response.status_code == 403

    def test_user_cannot_delete_shop(self, client, user_headers, shop):
        """Обычный пользователь не может удалить магазин"""
        response = client.delete(
            reverse('shop_delete', args=[shop.id]),
            **user_headers
        )
        assert response.status_code == 403
