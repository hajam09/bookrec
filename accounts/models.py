from django.db import models
from django.contrib.auth.models import User
from book.models import Category

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, db_index=True)
	favouriteGenres = models.ManyToManyField(Category, related_name='favouriteGenres')
	profilePicture = models.ImageField(upload_to='profilePicture', blank=True, null=True)