from django.db import models
from fooddonor.models import Profile, FoodDonation
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class RecipientPreference(models.Model):
    recipient = models.OneToOneField(Profile, on_delete=models.CASCADE, limit_choices_to={'role': 'recipient'})
    preferred_food_types = models.TextField(blank=True, null=True)
    dietary_restrictions = models.TextField(blank=True, null=True)
    preferred_pickup_times = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Preferences for {self.recipient.user.username}"
    

class RecipientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    location = models.TextField()
    needs_description = models.TextField(blank=True, null=True)
    verification_status = models.CharField(max_length=20, choices=[
        ('unverified', 'Unverified'),
        ('pending', 'Pending Verification'),
        ('verified', 'Verified')
    ], default='unverified')
    preferred_notification_method = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both')
    ], default='email')
    household_size = models.CharField(max_length=10)
    monthly_income = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    role = models.CharField(default='recipient', max_length=20)


    def __str__(self):
        return f"{self.user.username} - Recipient"

@receiver(post_save, sender=User)
def create_recipient_profile(sender, instance, created, **kwargs):
    if created and hasattr(instance, 'is_recipient'):
        RecipientProfile.objects.create(user=instance)