import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from users.models import User
from .choices import ProductStatus, OrderStatus
from .constants import (
    RATING_MIN, RATING_MAX,
    ORDER_QUANTITY_MIN, ORDER_QUANTITY_MAX,
    SHOP_NAME_MAX_LENGTH,
    PRODUCT_NAME_MAX_LENGTH,
    PRODUCT_PRICE_MAX_DIGITS,
    PRODUCT_PRICE_DECIMAL_PLACES,
)


class Shop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=SHOP_NAME_MAX_LENGTH)
    description = models.TextField(blank=True)
    owner = models.OneToOneField(User,
                                 on_delete=models.CASCADE,
                                 related_name='shop')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'shops'


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=PRODUCT_NAME_MAX_LENGTH)
    description = models.TextField(blank=True)
    price = models.DecimalField(
                      max_digits=PRODUCT_PRICE_MAX_DIGITS,
                      decimal_places=PRODUCT_PRICE_DECIMAL_PLACES,
                  )
    shop = models.ForeignKey(Shop,
                             on_delete=models.CASCADE,
                             related_name='products')
    status = models.CharField(
                      max_length=20,
                      choices=ProductStatus.choices,
                      default=ProductStatus.DRAFT,
                  )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name} ({self.shop.name})'

    class Meta:
        db_table = 'products'


class Order(models.Model):
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='orders')
    product = models.ForeignKey(Product,
                                on_delete=models.CASCADE,
                                related_name='orders')
    status = models.CharField(
                   max_length=20,
                   choices=OrderStatus.choices,
                   default=OrderStatus.PENDING,
               )
    quantity = models.PositiveIntegerField(
                     default=ORDER_QUANTITY_MIN,
                     validators=[
                         MinValueValidator(ORDER_QUANTITY_MIN),
                         MaxValueValidator(ORDER_QUANTITY_MAX),
                     ],
                 )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Order {self.id} | {self.user.email}'

    class Meta:
        db_table = 'orders'


class Review(models.Model):
    id = models.UUIDField(primary_key=True,
                          default=uuid.uuid4,
                          editable=False)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='reviews')
    product = models.ForeignKey(Product,
                                on_delete=models.CASCADE,
                                related_name='reviews')
    rating = models.PositiveSmallIntegerField(
                  validators=[
                      MinValueValidator(RATING_MIN),
                      MaxValueValidator(RATING_MAX),
                  ],
              )
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Review {self.user.email} → {self.product.name}'

    class Meta:
        db_table = 'reviews'
        unique_together = ('user', 'product')
