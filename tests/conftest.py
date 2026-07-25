import pytest

from django.test import Client

from users.models import User
from access_control.models import Role
from access_control.choices import RoleName
from business.models import Shop, Product, Order, Review
from auth_core.utils import generate_access_token, hash_password
from business.choices import ProductStatus


def _make_user(role_name, email, first_name='Test', last_name='User'):
    role, _ = Role.objects.get_or_create(name=role_name)
    return User.objects.create(
        email=email,
        password_hash=hash_password('testpass123'),
        role=role,
        first_name=first_name,
        last_name=last_name
    )


@pytest.fixture(autouse=True)
def create_roles(db):
    for role_name in RoleName.values:
        Role.objects.get_or_create(name=role_name)


@pytest.fixture
def admin_user(db, create_roles):
    return _make_user(RoleName.ADMIN, 'admin@test.com')


@pytest.fixture
def manager_user(db, create_roles):
    return _make_user(RoleName.MANAGER, 'manager@test.com')


@pytest.fixture
def manager_user_2(db, create_roles):
    return _make_user(RoleName.MANAGER, 'manager2@test.com')


@pytest.fixture
def regular_user(db, create_roles):
    return _make_user(RoleName.USER, 'user@test.com')


@pytest.fixture
def regular_user_2(db, create_roles):
    return _make_user(RoleName.USER, 'user2@test.com')


@pytest.fixture
def guest_user(db, create_roles):
    return _make_user(RoleName.GUEST, 'guest@test.com')


def _auth_headers(user):
    token = generate_access_token(user_id=str(user.id), role=user.role.name)
    return {'HTTP_AUTHORIZATION': f'Bearer {token}'}


@pytest.fixture
def admin_headers(admin_user):
    return _auth_headers(admin_user)


@pytest.fixture
def manager_headers(manager_user):
    return _auth_headers(manager_user)


@pytest.fixture
def manager_2_headers(manager_user_2):
    return _auth_headers(manager_user_2)


@pytest.fixture
def user_headers(regular_user):
    return _auth_headers(regular_user)


@pytest.fixture
def user_2_headers(regular_user_2):
    return _auth_headers(regular_user_2)


@pytest.fixture
def guest_headers(guest_user):
    return _auth_headers(guest_user)


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def shop(db, manager_user):
    return Shop.objects.create(name='Test Shop', owner=manager_user)


@pytest.fixture
def shop_2(db, manager_user_2):
    return Shop.objects.create(name='Other Shop', owner=manager_user_2)


@pytest.fixture
def product(db, shop):
    return Product.objects.create(
        name='Test Product',
        price='100.00',
        shop=shop,
        status=ProductStatus.PUBLISHED,
    )


@pytest.fixture
def unpublished_product(db, shop):
    return Product.objects.create(
        name='Draft Product',
        price='50.00',
        shop=shop,
        status=ProductStatus.DRAFT,
    )


@pytest.fixture
def order(db, regular_user, product):
    return Order.objects.create(
        user=regular_user,
        product=product,
        status='pending',
    )


@pytest.fixture
def review(db, regular_user, product):
    return Review.objects.create(
        user=regular_user,
        product=product,
        text='Great product!',
        rating=5,
    )
