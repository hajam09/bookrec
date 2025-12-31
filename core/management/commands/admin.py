from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from core.models import Profile


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        try:
            Profile.objects.filter(user__username='admin').delete()
            User.objects.filter(username='admin').delete()

            adminUser = User(
                username='admin',
                email='django.admin@example.com',
                first_name='Django',
                last_name='Admin',
                is_staff=True,
                is_active=True,
                is_superuser=True,
            )
            adminUser.set_password('admin')
            adminUser.save()
            Profile.objects.create(
                user=adminUser,
                favouriteGenres=[]
            )
        except IntegrityError as e:
            pass
