from django.db import models
from fooddonor.models import Profile, FoodDonation
from django.contrib.auth.models import User

class RecipientPreference(models.Model):
    recipient = models.OneToOneField(Profile, on_delete=models.CASCADE, limit_choices_to={'role': 'recipient'})
    preferred_food_types = models.TextField(blank=True, null=True)
    dietary_restrictions = models.TextField(blank=True, null=True)
    preferred_pickup_times = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Preferences for {self.recipient.user.username}"
    

class Recipient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    needs_description = models.TextField(blank=True)

    def __str__(self):
        return self.user.username
