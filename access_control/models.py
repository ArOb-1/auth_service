from django.db import models
from .choices import (
    Resource, Action, Scope, RoleName
)


class Role(models.Model):
    name = models.CharField(max_length=50,
                            unique=True,
                            choices=RoleName.choices)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'roles'


class RolePolicy(models.Model):
    role = models.ForeignKey(Role,
                             on_delete=models.CASCADE,
                             related_name='policies')
    resource = models.CharField(max_length=50,
                                choices=Resource.choices)
    action = models.CharField(max_length=20,
                              choices=Action.choices)
    scope = models.CharField(max_length=20,
                             choices=Scope.choices)

    class Meta:
        db_table = 'role_policies'
        constraints = [
            models.UniqueConstraint(
                fields=['role', 'resource', 'action'],
                name='unique_role_resource_action'
            )
        ]
