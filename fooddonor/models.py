from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    USER_ROLES = (
        ('donor', 'Food Donor'),
        ('recipient', 'Food Recipient'),
        ('admin', 'Administrator'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=10, choices=USER_ROLES)
    location = models.CharField(max_length=255, blank=True, null=True)
    needs_description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class FoodDonation(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('claimed', 'Claimed'),
        ('delivered', 'Delivered'),
        ('expired', 'Expired'),
    )
    
    # Use string reference to avoid circular imports
    donor = models.ForeignKey('fooddonor.Profile', on_delete=models.CASCADE, related_name='donations')
    title = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.CharField(max_length=50)
    expiry_date = models.DateField()
    pickup_location = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} by {self.donor.user.username}"

class DonationRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    
    # Use string references consistently
    recipient = models.ForeignKey('fooddonor.Profile', on_delete=models.CASCADE, related_name='requests')
    donation = models.ForeignKey('fooddonor.FoodDonation', on_delete=models.CASCADE, related_name='requests')
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Request for {self.donation.title} by {self.recipient.user.username}"