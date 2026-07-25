import pytest
import json
from django.test import Client
from business.models import Order


@pytest.mark.django_db
class TestOrderList:
    """GET /orders/"""

    def test_admin_sees_all_orders(self, client, admin_headers, order):
        res = client.get('/orders/', **admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data['orders']) == 1

    def test_user_sees_only_own_orders(self, client, user_headers, regular_user, regular_user_2, product):
        Order.objects.create(user=regular_user, product=product, status='pending')
        Order.objects.create(user=regular_user_2, product=product, status='pending')

        res = client.get('/orders/', **user_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data['orders']) == 1
        assert data['orders'][0]['user_id'] == str(regular_user.id)

    def test_guest_cannot_list_orders(self, client, guest_headers):
        res = client.get('/orders/', **guest_headers)
        assert res.status_code == 403

    def test_unauthenticated_cannot_list_orders(self, client):
        res = client.get('/orders/')
        assert res.status_code == 401


@pytest.mark.django_db
class TestOrderCreate:
    """POST /orders/create/"""

    def test_user_can_create_order(self, client, user_headers, product):
        res = client.post(
            '/orders/create/',
            data=json.dumps({'product_id': str(product.id), 'quantity': 2}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 201
        assert 'order_id' in res.json()

    def test_order_is_saved_to_db(self, client, user_headers, regular_user, product):
        client.post(
            '/orders/create/',
            data=json.dumps({'product_id': str(product.id), 'quantity': 1}),
            content_type='application/json',
            **user_headers,
        )
        assert Order.objects.filter(user=regular_user).count() == 1

    def test_create_order_without_product_id(self, client, user_headers):
        res = client.post(
            '/orders/create/',
            data=json.dumps({'quantity': 1}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 400

    def test_create_order_with_invalid_product_id(self, client, user_headers):
        res = client.post(
            '/orders/create/',
            data=json.dumps({'product_id': '00000000-0000-0000-0000-000000000000', 'quantity': 1}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 404

    def test_manager_cannot_create_order(self, client, manager_headers, product):
        res = client.post(
            '/orders/create/',
            data=json.dumps({'product_id': str(product.id), 'quantity': 1}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 403

    def test_guest_cannot_create_order(self, client, guest_headers, product):
        res = client.post(
            '/orders/create/',
            data=json.dumps({'product_id': str(product.id), 'quantity': 1}),
            content_type='application/json',
            **guest_headers,
        )
        assert res.status_code == 403

    def test_unauthenticated_cannot_create_order(self, client, product):
        res = client.post(
            '/orders/create/',
            data=json.dumps({'product_id': str(product.id), 'quantity': 1}),
            content_type='application/json',
        )
        assert res.status_code == 401


@pytest.mark.django_db
class TestOrderDetail:
    """GET /orders/<order_id>/"""

    def test_user_can_see_own_order(self, client, user_headers, order):
        res = client.get(f'/orders/{order.id}/', **user_headers)
        assert res.status_code == 200
        data = res.json()
        assert data['id'] == str(order.id)

    def test_user_cannot_see_other_user_order(self, client, user_2_headers, order):
        res = client.get(f'/orders/{order.id}/', **user_2_headers)
        assert res.status_code == 403

    def test_admin_can_see_any_order(self, client, admin_headers, order):
        res = client.get(f'/orders/{order.id}/', **admin_headers)
        assert res.status_code == 200

    def test_manager_can_see_own_shop_order(self, client, manager_headers, order):
        res = client.get(f'/orders/{order.id}/', **manager_headers)
        assert res.status_code == 200

    def test_manager_cannot_see_other_shop_order(self, client, manager_2_headers, order):
        res = client.get(f'/orders/{order.id}/', **manager_2_headers)
        assert res.status_code == 403

    def test_order_not_found(self, client, admin_headers):
        res = client.get('/orders/00000000-0000-0000-0000-000000000000/', **admin_headers)
        assert res.status_code == 404

    def test_guest_cannot_see_order(self, client, guest_headers, order):
        res = client.get(f'/orders/{order.id}/', **guest_headers)
        assert res.status_code == 403

    def test_unauthenticated_cannot_see_order(self, client, order):
        res = client.get(f'/orders/{order.id}/')
        assert res.status_code == 401


@pytest.mark.django_db
class TestOrderUpdateStatus:
    """PATCH /orders/<order_id>/status/"""

    def test_admin_can_update_status(self, client, admin_headers, order):
        res = client.patch(
            f'/orders/{order.id}/status/',
            data=json.dumps({'status': 'confirmed'}),
            content_type='application/json',
            **admin_headers,
        )
        assert res.status_code == 200
        assert res.json()['status'] == 'confirmed'

    def test_status_is_saved_to_db(self, client, admin_headers, order):
        client.patch(
            f'/orders/{order.id}/status/',
            data=json.dumps({'status': 'confirmed'}),
            content_type='application/json',
            **admin_headers,
        )
        order.refresh_from_db()
        assert order.status == 'confirmed'

    def test_update_status_with_invalid_status(self, client, admin_headers, order):
        res = client.patch(
            f'/orders/{order.id}/status/',
            data=json.dumps({'status': 'invalid_status'}),
            content_type='application/json',
            **admin_headers,
        )
        assert res.status_code == 400

    def test_update_status_without_status(self, client, admin_headers, order):
        res = client.patch(
            f'/orders/{order.id}/status/',
            data=json.dumps({}),
            content_type='application/json',
            **admin_headers,
        )
        assert res.status_code == 400

    def test_user_cannot_update_status(self, client, user_headers, order):
        res = client.patch(
            f'/orders/{order.id}/status/',
            data=json.dumps({'status': 'completed'}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 403

    def test_guest_cannot_update_status(self, client, guest_headers, order):
        res = client.patch(
            f'/orders/{order.id}/status/',
            data=json.dumps({'status': 'completed'}),
            content_type='application/json',
            **guest_headers,
        )
        assert res.status_code == 403

    def test_unauthenticated_cannot_update_status(self, client, order):
        res = client.patch(
            f'/orders/{order.id}/status/',
            data=json.dumps({'status': 'completed'}),
            content_type='application/json',
        )
        assert res.status_code == 401

    def test_order_not_found(self, client, admin_headers):
        res = client.patch(
            '/orders/00000000-0000-0000-0000-000000000000/status/',
            data=json.dumps({'status': 'completed'}),
            content_type='application/json',
            **admin_headers,
        )
        assert res.status_code == 404
