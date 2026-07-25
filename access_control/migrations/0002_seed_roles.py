from django.db import migrations
from access_control.choices import RoleName, Resource, Action, Scope


POLICIES = {
    RoleName.GUEST: [
        (Resource.SHOP,    Action.READ,   Scope.ALL),
        (Resource.PRODUCT, Action.READ,   Scope.PUBLISHED),
        (Resource.REVIEW,  Action.READ,   Scope.ALL),
    ],
    RoleName.USER: [
        (Resource.SHOP,    Action.READ,   Scope.ALL),
        (Resource.PRODUCT, Action.READ,   Scope.PUBLISHED),
        (Resource.ORDER,   Action.CREATE, Scope.OWN),
        (Resource.ORDER,   Action.READ,   Scope.OWN),
        (Resource.REVIEW,  Action.CREATE, Scope.OWN),
        (Resource.REVIEW,  Action.READ,   Scope.ALL),
        (Resource.REVIEW,  Action.DELETE, Scope.OWN),
    ],
    RoleName.MANAGER: [
        (Resource.SHOP,    Action.READ,   Scope.ALL),
        (Resource.SHOP,    Action.CREATE, Scope.OWN),
        (Resource.SHOP,    Action.UPDATE, Scope.OWN),
        (Resource.PRODUCT, Action.READ,   Scope.OWN_SHOP),
        (Resource.PRODUCT, Action.CREATE, Scope.OWN_SHOP),
        (Resource.PRODUCT, Action.UPDATE, Scope.OWN_SHOP),
        (Resource.PRODUCT, Action.DELETE, Scope.OWN_SHOP),
        (Resource.ORDER,   Action.READ,   Scope.OWN_SHOP),
        (Resource.ORDER,   Action.UPDATE, Scope.OWN_SHOP),
        (Resource.REVIEW,  Action.READ,   Scope.ALL),
    ],
    RoleName.ADMIN: [
        (Resource.USERS,   Action.READ,   Scope.ALL),
        (Resource.USERS,   Action.UPDATE, Scope.ALL),
        (Resource.USERS,   Action.DELETE, Scope.ALL),
        (Resource.SHOP,    Action.READ,   Scope.ALL),
        (Resource.SHOP,    Action.CREATE, Scope.ALL),
        (Resource.SHOP,    Action.UPDATE, Scope.ALL),
        (Resource.SHOP,    Action.DELETE, Scope.ALL),
        (Resource.PRODUCT, Action.READ,   Scope.ALL),
        (Resource.PRODUCT, Action.CREATE, Scope.ALL),
        (Resource.PRODUCT, Action.UPDATE, Scope.ALL),
        (Resource.PRODUCT, Action.DELETE, Scope.ALL),
        (Resource.ORDER,   Action.READ,   Scope.ALL),
        (Resource.ORDER,   Action.UPDATE, Scope.ALL),
        (Resource.ORDER,   Action.DELETE, Scope.ALL),
        (Resource.REVIEW,  Action.READ,   Scope.ALL),
        (Resource.REVIEW,  Action.DELETE, Scope.ALL),
    ],
}


def seed_roles(apps, schema_editor):
    Role = apps.get_model('access_control', 'Role')
    RolePolicy = apps.get_model('access_control', 'RolePolicy')

    for role_name, policies in POLICIES.items():
        role, _ = Role.objects.get_or_create(name=role_name)

        for resource, action, scope in policies:
            RolePolicy.objects.get_or_create(
                role=role,
                resource=resource,
                action=action,
                defaults={'scope': scope},
            )


def unseed_roles(apps, schema_editor):
    Role = apps.get_model('access_control', 'Role')
    Role.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('access_control', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]
