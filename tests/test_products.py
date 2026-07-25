import pytest
import json
from business.models import Product, ProductStatus


@pytest.mark.django_db
class TestProductList:
    """GET /products/"""

    def test_admin_sees_all_products(self, client, admin_headers, product, unpublished_product):
        res = client.get('/products/', **admin_headers)
        assert res.status_code == 200
        assert len(res.json()['products']) == 2

    def test_manager_sees_only_own_shop_products(self, client, manager_headers, manager_2_headers, product, shop_2):
        Product.objects.create(name='Other Product', price='200.00', shop=shop_2, status=ProductStatus.PUBLISHED)

        res = client.get('/products/', **manager_headers)
        assert res.status_code == 200
        data = res.json()['products']
        assert len(data) == 1
        assert data[0]['id'] == str(product.id)

    def test_manager_2_sees_only_own_shop_products(self, client, manager_2_headers, product, shop_2):
        other = Product.objects.create(name='Other Product', price='200.00', shop=shop_2, status=ProductStatus.PUBLISHED)

        res = client.get('/products/', **manager_2_headers)
        assert res.status_code == 200
        data = res.json()['products']
        assert len(data) == 1
        assert data[0]['id'] == str(other.id)

    def test_user_sees_only_published_products(self, client, user_headers, product, unpublished_product):
        res = client.get('/products/', **user_headers)
        assert res.status_code == 200
        data = res.json()['products']
        assert len(data) == 1
        assert data[0]['id'] == str(product.id)

    def test_guest_sees_only_published_products(self, client, guest_headers, product, unpublished_product):
        res = client.get('/products/', **guest_headers)
        assert res.status_code == 200
        data = res.json()['products']
        assert len(data) == 1
        assert data[0]['id'] == str(product.id)

    def test_unauthenticated_can_see_published_products(self, client, product, unpublished_product):
        res = client.get('/products/')
        assert res.status_code == 200
        data = res.json()['products']
        assert len(data) == 1
        assert data[0]['id'] == str(product.id)


@pytest.mark.django_db
class TestProductCreate:
    """POST /products/create/"""

    def test_manager_can_create_product(self, client, manager_headers, shop):
        res = client.post(
            '/products/create/',
            data=json.dumps({'name': 'New Product', 'price': '99.99', 'shop_id': str(shop.id)}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 201
        assert 'product_id' in res.json()

    def test_product_is_saved_to_db(self, client, manager_headers, shop):
        client.post(
            '/products/create/',
            data=json.dumps({'name': 'New Product', 'price': '99.99', 'shop_id': str(shop.id)}),
            content_type='application/json',
            **manager_headers,
        )
        assert Product.objects.filter(name='New Product').count() == 1

    def test_product_created_with_draft_status(self, client, manager_headers, shop):
        res = client.post(
            '/products/create/',
            data=json.dumps({'name': 'New Product', 'price': '99.99', 'shop_id': str(shop.id)}),
            content_type='application/json',
            **manager_headers,
        )
        product = Product.objects.get(id=res.json()['product_id'])
        assert product.status == ProductStatus.DRAFT

    def test_manager_cannot_create_product_in_other_shop(self, client, manager_2_headers, shop):
        # shop принадлежит manager_user, запрос от manager_user_2
        res = client.post(
            '/products/create/',
            data=json.dumps({'name': 'New Product', 'price': '99.99', 'shop_id': str(shop.id)}),
            content_type='application/json',
            **manager_2_headers,
        )
        assert res.status_code == 404

    def test_create_product_without_name(self, client, manager_headers, shop):
        res = client.post(
            '/products/create/',
            data=json.dumps({'price': '99.99', 'shop_id': str(shop.id)}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 400

    def test_create_product_without_price(self, client, manager_headers, shop):
        res = client.post(
            '/products/create/',
            data=json.dumps({'name': 'New Product', 'shop_id': str(shop.id)}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 400

    def test_create_product_without_shop_id(self, client, manager_headers):
        res = client.post(
            '/products/create/',
            data=json.dumps({'name': 'New Product', 'price': '99.99'}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 400

    def test_create_product_with_invalid_shop_id(self, client, manager_headers):
        res = client.post(
            '/products/create/',
            data=json.dumps({'name': 'New Product', 'price': '99.99', 'shop_id': '00000000-0000-0000-0000-000000000000'}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 404

    def test_user_cannot_create_product(self, client, user_headers, shop):
        res = client.post(
            '/products/create/',
            data=json.dumps({'name': 'New Product', 'price': '99.99', 'shop_id': str(shop.id)}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 403

    def test_unauthenticated_cannot_create_product(self, client, shop):
        res = client.post(
            '/products/create/',
            data=json.dumps({'name': 'New Product', 'price': '99.99', 'shop_id': str(shop.id)}),
            content_type='application/json',
        )
        assert res.status_code == 401


@pytest.mark.django_db
class TestProductDetail:
    """GET /products/<product_id>/"""

    def test_admin_can_see_any_product(self, client, admin_headers, product):
        res = client.get(f'/products/{product.id}/', **admin_headers)
        assert res.status_code == 200
        assert res.json()['id'] == str(product.id)

    def test_admin_can_see_unpublished_product(self, client, admin_headers, unpublished_product):
        res = client.get(f'/products/{unpublished_product.id}/', **admin_headers)
        assert res.status_code == 200

    def test_manager_can_see_own_shop_product(self, client, manager_headers, product):
        res = client.get(f'/products/{product.id}/', **manager_headers)
        assert res.status_code == 200

    def test_manager_cannot_see_other_shop_product(self, client, manager_2_headers, product):
        res = client.get(f'/products/{product.id}/', **manager_2_headers)
        assert res.status_code == 403

    def test_manager_can_see_own_unpublished_product(self, client, manager_headers, unpublished_product):
        res = client.get(f'/products/{unpublished_product.id}/', **manager_headers)
        assert res.status_code == 200

    def test_user_can_see_published_product(self, client, user_headers, product):
        res = client.get(f'/products/{product.id}/', **user_headers)
        assert res.status_code == 200

    def test_user_cannot_see_unpublished_product(self, client, user_headers, unpublished_product):
        res = client.get(f'/products/{unpublished_product.id}/', **user_headers)
        assert res.status_code == 404

    def test_guest_can_see_published_product(self, client, guest_headers, product):
        res = client.get(f'/products/{product.id}/', **guest_headers)
        assert res.status_code == 200

    def test_guest_cannot_see_unpublished_product(self, client, guest_headers, unpublished_product):
        res = client.get(f'/products/{unpublished_product.id}/', **guest_headers)
        assert res.status_code == 404

    def test_product_not_found(self, client, admin_headers):
        res = client.get('/products/00000000-0000-0000-0000-000000000000/', **admin_headers)
        assert res.status_code == 404

    def test_unauthenticated_can_see_published_product(self, client, product):
        res = client.get(f'/products/{product.id}/')
        assert res.status_code == 200

    def test_unauthenticated_cannot_see_unpublished_product(self, client, unpublished_product):
        res = client.get(f'/products/{unpublished_product.id}/')
        assert res.status_code == 404


@pytest.mark.django_db
class TestProductUpdate:
    """PATCH /products/<product_id>/update/"""

    def test_manager_can_update_own_product(self, client, manager_headers, product):
        res = client.patch(
            f'/products/{product.id}/update/',
            data=json.dumps({'name': 'Updated Name'}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 200
        product.refresh_from_db()
        assert product.name == 'Updated Name'

    def test_manager_can_update_price(self, client, manager_headers, product):
        res = client.patch(
            f'/products/{product.id}/update/',
            data=json.dumps({'price': '999.99'}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 200
        product.refresh_from_db()
        assert str(product.price) == '999.99'

    def test_manager_can_update_status(self, client, manager_headers, product):
        res = client.patch(
            f'/products/{product.id}/update/',
            data=json.dumps({'status': ProductStatus.DRAFT}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 200
        product.refresh_from_db()
        assert product.status == ProductStatus.DRAFT

    def test_manager_cannot_update_other_shop_product(self, client, manager_2_headers, product):
        res = client.patch(
            f'/products/{product.id}/update/',
            data=json.dumps({'name': 'Hacked Name'}),
            content_type='application/json',
            **manager_2_headers,
        )
        assert res.status_code == 403
        product.refresh_from_db()
        assert product.name == 'Test Product'

    def test_user_cannot_update_product(self, client, user_headers, product):
        res = client.patch(
            f'/products/{product.id}/update/',
            data=json.dumps({'name': 'Updated Name'}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 403

    def test_unauthenticated_cannot_update_product(self, client, product):
        res = client.patch(
            f'/products/{product.id}/update/',
            data=json.dumps({'name': 'Updated Name'}),
            content_type='application/json',
        )
        assert res.status_code == 401

    def test_product_not_found(self, client, manager_headers):
        res = client.patch(
            '/products/00000000-0000-0000-0000-000000000000/update/',
            data=json.dumps({'name': 'Updated Name'}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 404


@pytest.mark.django_db
class TestProductDelete:
    """DELETE /products/<product_id>/delete/"""

    def test_manager_can_delete_own_product(self, client, manager_headers, product):
        res = client.delete(f'/products/{product.id}/delete/', **manager_headers)
        assert res.status_code == 200
        assert not Product.objects.filter(id=product.id).exists()

    def test_manager_cannot_delete_other_shop_product(self, client, manager_2_headers, product):
        res = client.delete(f'/products/{product.id}/delete/', **manager_2_headers)
        assert res.status_code == 403
        assert Product.objects.filter(id=product.id).exists()

    def test_user_cannot_delete_product(self, client, user_headers, product):
        res = client.delete(f'/products/{product.id}/delete/', **user_headers)
        assert res.status_code == 403

    def test_unauthenticated_cannot_delete_product(self, client, product):
        res = client.delete(f'/products/{product.id}/delete/')
        assert res.status_code == 401

    def test_product_not_found(self, client, manager_headers):
        res = client.delete(
            '/products/00000000-0000-0000-0000-000000000000/delete/',
            **manager_headers,
        )
        assert res.status_code == 404
