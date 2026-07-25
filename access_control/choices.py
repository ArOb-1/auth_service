from django.db import models
from .constants import (
    ADMIN, MANAGER, USER, GUEST,
    USERS, SHOPS, PRODUCTS,
    ORDERS, REVIEWS,
    READ, CREATE, UPDATE, DELETE,
    ALL, OWN, OWN_SHOP, PUBLISHED
)


class RoleName(models.TextChoices):
    ADMIN = ADMIN
    MANAGER = MANAGER
    USER = USER
    GUEST = GUEST


class Resource(models.TextChoices):
    USERS = USERS
    SHOP = SHOPS
    PRODUCT = PRODUCTS
    ORDER = ORDERS
    REVIEW = REVIEWS


class Action(models.TextChoices):
    READ = READ
    CREATE = CREATE
    UPDATE = UPDATE
    DELETE = DELETE


class Scope(models.TextChoices):
    ALL = ALL
    OWN = OWN
    OWN_SHOP = OWN_SHOP
    PUBLISHED = PUBLISHED
