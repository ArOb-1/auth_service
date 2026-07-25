import json
import os
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand

from access_control.models import Role
from auth_core.utils import hash_password
from business.models import Order, Product, Review, Shop
from users.models import User


class Command(BaseCommand):
    help = 'Load test data from data/load_data.json'

    def handle(self, *args, **kwargs):
        path = os.path.join(settings.BASE_DIR, 'data', 'load_data.json')
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        users = self._seed_users(data.get('users', []))
        shops = self._seed_shops(data.get('shops', []), users)
        products = self._seed_products(data.get('products', []), shops)
        self._seed_orders(data.get('orders', []), users, products)
        self._seed_reviews(data.get('reviews', []), users, products)

        self.stdout.write(self.style.SUCCESS('\nDone. Service is ready for testing.\n'))

    def _seed_users(self, items):
        self.stdout.write('\nUsers:')
        result = {}

        for d in items:
            if User.objects.filter(email=d['email']).exists():
                user = User.objects.get(email=d['email'])
                self.stdout.write(f"   skip    {d['email']}  [{d['role']}]")
            else:
                try:
                    role = Role.objects.get(name=d['role'])
                except Role.DoesNotExist:
                    self.stdout.write(self.style.ERROR(
                        f"   error   role '{d['role']}' not found — run migrations first"
                    ))
                    continue

                user = User.objects.create(
                    email=d['email'],
                    password_hash=hash_password(d['password']),
                    first_name=d.get('first_name', ''),
                    last_name=d.get('last_name', ''),
                    patronymic=d.get('patronymic', ''),
                    role=role,
                )
                self.stdout.write(self.style.SUCCESS(
                    f"   created {d['email']}  [{d['role']}]"
                ))

            result[d['email']] = user

        return result

    def _seed_shops(self, items, users):
        self.stdout.write('\nShops:')
        result = {}

        for d in items:
            owner = users.get(d['owner_email'])
            if not owner:
                self.stdout.write(self.style.ERROR(
                    f"   error   owner '{d['owner_email']}' not found"
                ))
                continue

            shop, created = Shop.objects.get_or_create(
                name=d['name'],
                defaults={
                    'description': d.get('description', ''),
                    'owner': owner,
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"   created {shop.name}  (owner: {d['owner_email']})"
                ))
            else:
                self.stdout.write(f"   skip    {shop.name}")

            result[d['name']] = shop

        return result

    def _seed_products(self, items, shops):
        self.stdout.write('\nProducts:')
        result = {}

        for d in items:
            shop = shops.get(d['shop_name'])
            if not shop:
                self.stdout.write(self.style.ERROR(
                    f"   error   shop '{d['shop_name']}' not found"
                ))
                continue

            product, created = Product.objects.get_or_create(
                name=d['name'],
                shop=shop,
                defaults={
                    'description': d.get('description', ''),
                    'price': Decimal(d['price']),
                    'status': d.get('status', 'draft'),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"   created {product.name}  [{product.status}]  {product.price} ₽"
                ))
            else:
                self.stdout.write(f"   skip    {product.name}")

            result[d['name']] = product

        return result

    def _seed_orders(self, items, users, products):
        self.stdout.write('\nOrders:')

        for d in items:
            user = users.get(d['user_email'])
            product = products.get(d['product_name'])

            if not user or not product:
                self.stdout.write(self.style.ERROR('   error   user or product not found'))
                continue

            order, created = Order.objects.get_or_create(
                user=user,
                product=product,
                defaults={
                    'quantity': d.get('quantity', 1),
                    'status': d.get('status', 'pending'),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"   created {d['user_email']} → {product.name}"
                    f"  x{order.quantity}  [{order.status}]"
                ))
            else:
                self.stdout.write(f"   skip    {d['user_email']} → {product.name}")

    def _seed_reviews(self, items, users, products):
        self.stdout.write('\nReviews:')

        for d in items:
            user = users.get(d['user_email'])
            product = products.get(d['product_name'])

            if not user or not product:
                self.stdout.write(self.style.ERROR('   error   user or product not found'))
                continue

            review, created = Review.objects.get_or_create(
                user=user,
                product=product,
                defaults={
                    'rating': d['rating'],
                    'text': d.get('text', ''),
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"   created {d['user_email']} → {product.name}"
                    f"  {'⭐' * review.rating}"
                ))
            else:
                self.stdout.write(f"   skip    {d['user_email']} → {product.name}")
