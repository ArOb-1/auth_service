import pytest
import json
from business.models import Review


@pytest.mark.django_db
class TestReviewList:
    """GET /reviews/"""

    def test_admin_can_see_all_reviews(self, client, admin_headers, review):
        res = client.get('/reviews/', **admin_headers)
        assert res.status_code == 200
        assert len(res.json()['reviews']) == 1

    def test_manager_can_see_all_reviews(self, client, manager_headers, review):
        res = client.get('/reviews/', **manager_headers)
        assert res.status_code == 200
        assert len(res.json()['reviews']) == 1

    def test_user_can_see_all_reviews(self, client, user_headers, review):
        res = client.get('/reviews/', **user_headers)
        assert res.status_code == 200
        assert len(res.json()['reviews']) == 1

    def test_guest_can_see_all_reviews(self, client, guest_headers, review):
        res = client.get('/reviews/', **guest_headers)
        assert res.status_code == 200
        assert len(res.json()['reviews']) == 1

    def test_unauthenticated_can_see_all_reviews(self, client, review):
        res = client.get('/reviews/')
        assert res.status_code == 200
        assert len(res.json()['reviews']) == 1

    def test_filter_by_product_id(self, client, user_headers, review, product):
        res = client.get(f'/reviews/?product_id={product.id}', **user_headers)
        assert res.status_code == 200
        data = res.json()['reviews']
        assert len(data) == 1
        assert data[0]['product_id'] == str(product.id)

    def test_filter_by_wrong_product_id_returns_empty(self, client, user_headers, review):
        res = client.get('/reviews/?product_id=00000000-0000-0000-0000-000000000000', **user_headers)
        assert res.status_code == 200
        assert len(res.json()['reviews']) == 0

    def test_response_fields(self, client, user_headers, review):
        res = client.get('/reviews/', **user_headers)
        assert res.status_code == 200
        r = res.json()['reviews'][0]
        assert 'id' in r
        assert 'author_id' in r
        assert 'product_id' in r
        assert 'rating' in r
        assert 'text' in r
        assert 'created_at' in r


@pytest.mark.django_db
class TestReviewCreate:
    """POST /reviews/create/"""

    def test_user_can_create_review(self, client, user_headers, product):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id), 'rating': 5, 'text': 'Great!'}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 201
        assert 'review_id' in res.json()

    def test_review_is_saved_to_db(self, client, user_headers, product):
        client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id), 'rating': 5, 'text': 'Great!'}),
            content_type='application/json',
            **user_headers,
        )
        assert Review.objects.filter(product=product).count() == 1

    def test_create_review_without_text(self, client, user_headers, product):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id), 'rating': 3}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 201

    def test_cannot_review_same_product_twice(self, client, user_headers, product, review):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id), 'rating': 4}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 409

    def test_cannot_review_unpublished_product(self, client, user_headers, unpublished_product):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(unpublished_product.id), 'rating': 5}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 404

    def test_create_review_with_invalid_product_id(self, client, user_headers):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': '00000000-0000-0000-0000-000000000000', 'rating': 5}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 404

    def test_create_review_without_product_id(self, client, user_headers):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'rating': 5}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 400

    def test_create_review_without_rating(self, client, user_headers, product):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id)}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 400

    def test_create_review_with_rating_too_low(self, client, user_headers, product):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id), 'rating': 0}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 400

    def test_create_review_with_rating_too_high(self, client, user_headers, product):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id), 'rating': 6}),
            content_type='application/json',
            **user_headers,
        )
        assert res.status_code == 400

    def test_manager_cannot_create_review(self, client, manager_headers, product):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id), 'rating': 5}),
            content_type='application/json',
            **manager_headers,
        )
        assert res.status_code == 403

    def test_admin_cannot_create_review(self, client, admin_headers, product):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id), 'rating': 5}),
            content_type='application/json',
            **admin_headers,
        )
        assert res.status_code == 403

    def test_unauthenticated_cannot_create_review(self, client, product):
        res = client.post(
            '/reviews/create/',
            data=json.dumps({'product_id': str(product.id), 'rating': 5}),
            content_type='application/json',
        )
        assert res.status_code == 401


@pytest.mark.django_db
class TestReviewDetail:
    """GET /reviews/<review_id>/"""

    def test_admin_can_see_review(self, client, admin_headers, review):
        res = client.get(f'/reviews/{review.id}/', **admin_headers)
        assert res.status_code == 200
        assert res.json()['id'] == str(review.id)

    def test_manager_can_see_review(self, client, manager_headers, review):
        res = client.get(f'/reviews/{review.id}/', **manager_headers)
        assert res.status_code == 200

    def test_user_can_see_review(self, client, user_headers, review):
        res = client.get(f'/reviews/{review.id}/', **user_headers)
        assert res.status_code == 200

    def test_guest_can_see_review(self, client, guest_headers, review):
        res = client.get(f'/reviews/{review.id}/', **guest_headers)
        assert res.status_code == 200

    def test_unauthenticated_can_see_review(self, client, review):
        res = client.get(f'/reviews/{review.id}/')
        assert res.status_code == 200

    def test_review_not_found(self, client, user_headers):
        res = client.get('/reviews/00000000-0000-0000-0000-000000000000/', **user_headers)
        assert res.status_code == 404

    def test_response_fields(self, client, user_headers, review):
        res = client.get(f'/reviews/{review.id}/', **user_headers)
        data = res.json()
        assert 'id' in data
        assert 'author_id' in data
        assert 'product_id' in data
        assert 'rating' in data
        assert 'text' in data
        assert 'created_at' in data


@pytest.mark.django_db
class TestReviewDelete:
    """DELETE /reviews/<review_id>/delete/"""

    def test_user_can_delete_own_review(self, client, user_headers, review):
        res = client.delete(f'/reviews/{review.id}/delete/', **user_headers)
        assert res.status_code == 200
        assert not Review.objects.filter(id=review.id).exists()

    def test_user_cannot_delete_other_user_review(self, client, user_2_headers, review):
        res = client.delete(f'/reviews/{review.id}/delete/', **user_2_headers)
        assert res.status_code == 403
        assert Review.objects.filter(id=review.id).exists()

    def test_admin_can_delete_any_review(self, client, admin_headers, review):
        res = client.delete(f'/reviews/{review.id}/delete/', **admin_headers)
        assert res.status_code == 200
        assert not Review.objects.filter(id=review.id).exists()

    def test_manager_cannot_delete_review(self, client, manager_headers, review):
        res = client.delete(f'/reviews/{review.id}/delete/', **manager_headers)
        assert res.status_code == 403
        assert Review.objects.filter(id=review.id).exists()

    def test_unauthenticated_cannot_delete_review(self, client, review):
        res = client.delete(f'/reviews/{review.id}/delete/')
        assert res.status_code == 401
        assert Review.objects.filter(id=review.id).exists()

    def test_review_not_found(self, client, user_headers):
        res = client.delete('/reviews/00000000-0000-0000-0000-000000000000/delete/', **user_headers)
        assert res.status_code == 404
