from django.db import migrations


def add_permissions(apps, schema_editor):
    Role = apps.get_model('access_control', 'Role')
    RolePolicy = apps.get_model('access_control', 'RolePolicy')

    new_permissions = [
        ('user',    'users', 'read',   'own'),
        ('user',    'users', 'update', 'own'),
        ('user',    'users', 'delete', 'own'),
        ('manager', 'users', 'read',   'own'),
        ('manager', 'users', 'update', 'own'),
        ('manager', 'users', 'delete', 'own'),
    ]

    for role_name, resource, action, scope in new_permissions:
        try:
            role = Role.objects.get(name=role_name)
            RolePolicy.objects.get_or_create(
                role=role,
                resource=resource,
                action=action,
                defaults={'scope': scope},
            )
        except Role.DoesNotExist:
            pass


def remove_permissions(apps, schema_editor):
    Role = apps.get_model('access_control', 'Role')
    RolePolicy = apps.get_model('access_control', 'RolePolicy')

    for role_name in ['user', 'manager']:
        try:
            role = Role.objects.get(name=role_name)
            RolePolicy.objects.filter(
                role=role,
                resource='users',
                action__in=['read', 'update', 'delete'],
                scope='own',
            ).delete()
        except Role.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0003_seed_roles'),
    ]

    operations = [
        migrations.RunPython(add_permissions, remove_permissions),
    ]
