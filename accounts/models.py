from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models

from core.models import Category


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', unique=True, db_index=True)
    favouriteGenres = ArrayField(models.CharField(max_length=8192), blank=True)
    profilePicture = models.ImageField(upload_to='profile-picture', blank=True, null=True)
