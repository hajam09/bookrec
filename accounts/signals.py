from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Profile

@receiver(post_save, sender=User)
def createUserProfile(sender, instance, created, **kwargs):
	if created:
		Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def saveUserProfile(sender, instance, **kwargs):
	if not instance.is_superuser:
		instance.profile.save()