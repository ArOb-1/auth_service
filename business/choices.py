from django.db import models
from .constants import (
    DRAFT, PUBLISHED, PENDING, CONFIRMED, CANCELLED
)


class ProductStatus(models.TextChoices):
    DRAFT = DRAFT
    PUBLISHED = PUBLISHED


class OrderStatus(models.TextChoices):
    PENDING = PENDING
    CONFIRMED = CONFIRMED
    CANCELLED = CANCELLED
