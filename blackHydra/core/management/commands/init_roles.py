from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from core.models import ScanResult


class Command(BaseCommand):
    help ='Intialize user roles'

    def handle(self, *args, **kwargs):
        admin_group, _ = Group.objects.get_or_create(name='admin')
        analyst_group, _ = Group.objects.get_or_create(name='analyst')

        perms =  Permission.objects.filter(content_type__app_label='core')
        admin_group.permissions.set(perms)


        view_perms  = perms.filter(codename__startswith='view_')
        analyst_group.permissions.set(view_perms)


        self.stdout.write(self.style.SUCCESS("Roles created and permisions set ."))