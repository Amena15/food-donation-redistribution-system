from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from fooddonor.models import FoodDonation, Profile
from django.utils import timezone
from datetime import timedelta
from django.core.validators import MinValueValidator, MaxValueValidator

class RecipientProfile(models.Model):
    """Recipient profile extending the base user model (Decorator Pattern)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recipient_profile')
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    state = models.CharField(max_length=50)
    household_size = models.PositiveIntegerField(default=1)
    monthly_income = models.CharField(max_length=50, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, 
        choices=[
            ('unverified', 'Unverified'),
            ('pending', 'Pending Verification'),
            ('verified', 'Verified')
        ], 
        default='unverified'
    )
    preferred_notification = models.CharField(max_length=10,
        choices=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('both', 'Both')
        ],
        default='email'
    )
    needs_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Recipient Profile"

class RecipientPreference(models.Model):
    """Strategy Pattern for recipient preferences"""
    recipient = models.OneToOneField(RecipientProfile, on_delete=models.CASCADE, related_name='preferences')
    preferred_categories = models.JSONField(default=list)
    dietary_restrictions = models.JSONField(default=list)
    preferred_pickup_times = models.JSONField(default=list)
    max_pickup_distance = models.PositiveIntegerField(default=10)  # in km
    advance_notice = models.PositiveIntegerField(default=1)  # days

    def __str__(self):
        return f"Preferences for {self.recipient.user.username}"

class DonationRequest(models.Model):
    """State Pattern for request status"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    recipient = models.ForeignKey(RecipientProfile, on_delete=models.CASCADE, related_name='requests')
    donation = models.ForeignKey(FoodDonation, on_delete=models.CASCADE, related_name='requests')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pickup_date = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    rating = models.PositiveSmallIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    def __str__(self):
        return f"Request #{self.id} by {self.recipient.user.username}"

class PickupSchedule(models.Model):
    """Observer Pattern for pickup notifications"""
    request = models.OneToOneField(DonationRequest, on_delete=models.CASCADE, related_name='pickup_schedule')
    scheduled_time = models.DateTimeField()
    driver_name = models.CharField(max_length=100, blank=True)
    driver_contact = models.CharField(max_length=15, blank=True)
    vehicle_details = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Pickup for Request #{self.request.id}"

class WishlistItem(models.Model):
    """Composite Pattern for wishlist items"""
    CATEGORY_CHOICES = [
        ('fruits', 'Fruits'),
        ('vegetables', 'Vegetables'),
        ('grains', 'Grains & Cereals'),
        ('dairy', 'Dairy Products'),
        ('meat', 'Meat & Poultry'),
        ('seafood', 'Seafood'),
        ('bakery', 'Bakery Items'),
        ('prepared', 'Prepared Food'),
        ('beverages', 'Beverages'),
        ('canned', 'Canned Goods'),
        ('other', 'Other'),
    ]
    
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Urgent'),
    ]
    
    recipient = models.ForeignKey(RecipientProfile, on_delete=models.CASCADE, related_name='wishlist_items')
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    priority = models.PositiveSmallIntegerField(choices=PRIORITY_CHOICES, default=2)
    desired_frequency = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_fulfilled = models.BooleanField(default=False)
    fulfilled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} (Priority: {self.get_priority_display()})"

class Notification(models.Model):
    """Observer Pattern for notifications"""
    recipient = models.ForeignKey(RecipientProfile, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_request = models.ForeignKey(
        DonationRequest, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    notification_type = models.CharField(max_length=50)

    def __str__(self):
        return f"Notification for {self.recipient.user.username}"

    class Meta:
        ordering = ['-created_at']

@receiver(post_save, sender=User)
def create_recipient_profile(sender, instance, created, **kwargs):
    """Factory Pattern for profile creation"""
    if created and hasattr(instance, 'is_recipient'):
        RecipientProfile.objects.create(user=instance)