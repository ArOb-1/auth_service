from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=50,
                            unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'roles'


class BusinessElement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'business_elements'


class AccessRoleRule(models.Model):
    role = models.ForeignKey(Role,
                             on_delete=models.CASCADE,
                             related_name='rules')
    element = models.ForeignKey(BusinessElement,
                                on_delete=models.CASCADE,
                                related_name='rules')

    read_permission = models.BooleanField(default=False)
    read_all_permission = models.BooleanField(default=False)

    create_permission = models.BooleanField(default=False)

    update_permission = models.BooleanField(default=False)
    update_all_permission = models.BooleanField(default=False)

    delete_permission = models.BooleanField(default=False)
    delete_all_permission = models.BooleanField(default=False)

    class Meta:
        db_table = 'access_roles_rules'
        unique_together = ('role', 'element')

    def __str__(self):
        return f'{self.role.name} → {self.element.name}'
