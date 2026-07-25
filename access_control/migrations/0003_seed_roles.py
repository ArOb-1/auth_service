from django.db import migrations


def add_manager_delete_policy(apps, schema_editor):
    Role = apps.get_model('access_control', 'Role')
    RolePolicy = apps.get_model('access_control', 'RolePolicy')

    manager = Role.objects.get(name='manager')

    RolePolicy.objects.get_or_create(
        role=manager,
        resource='shops',
        action='delete',
        defaults={'scope': 'own'},
    )


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0002_seed_roles'),
    ]

    operations = [
        migrations.RunPython(add_manager_delete_policy, migrations.RunPython.noop),
    ]
