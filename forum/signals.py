from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile, Reply
from .notifications import send_reply_notification


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a User is created"""
    if created:
        UserProfile.objects.create(
            user=instance,
            full_name=instance.get_full_name() or instance.username,
            bits_email=instance.email if instance.email else None
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(
            user=instance,
            full_name=instance.get_full_name() or instance.username,
            bits_email=instance.email if instance.email else None
        )


@receiver(post_save, sender=Reply)
def notify_thread_author(sender, instance, created, **kwargs):
    """Send email notification when a new reply is created"""
    if created and not instance.is_deleted:
        send_reply_notification(instance)
