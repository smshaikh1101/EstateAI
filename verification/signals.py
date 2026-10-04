from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_migrate)
def ensure_profiles(sender, **kwargs):
    # sender is an AppConfig
    try:
        if getattr(sender, "name", "") != "verification":
            return
    except Exception:
        return

    for u in User.objects.all():
        Profile.objects.get_or_create(user=u)
