import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from users.models import User
from access_control.models import Role
from auth_core.utils import hash_password


class Command(BaseCommand):
    help = 'Load test users from data/load_data.json'

    def handle(self, *args, **kwargs):
        data_path = os.path.join(settings.BASE_DIR, 'data', 'load_data.json')

        with open(data_path, 'r', encoding='utf-8') as f:
            users_data = json.load(f)

        created = 0
        skipped = 0

        for data in users_data:
            if User.objects.filter(email=data['email']).exists():
                self.stdout.write(f"  skip     {data['email']} (already exists)")
                skipped += 1
                continue

            try:
                role = Role.objects.get(name=data['role'])
            except Role.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"  error    role '{data['role']}' not found — run migrations first")
                )
                continue

            User.objects.create(
                email=data['email'],
                password_hash=hash_password(data['password']),
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                patronymic=data.get('patronymic', ''),
                role=role,
            )
            self.stdout.write(
                self.style.SUCCESS(f"  created  {data['email']}  [{data['role']}]")
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f'\nDone: {created} created, {skipped} skipped.')
        )
