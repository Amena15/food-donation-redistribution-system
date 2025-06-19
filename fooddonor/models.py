from django.db import models
from django.contrib.auth.models import User

class FoodListing(models.Model):
    donor = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    quantity = models.IntegerField()
    location = models.CharField(max_length=255)
    expiry_date = models.DateField()
    pickup_date = models.DateField()
    image = models.ImageField(upload_to='', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('expired', 'Expired')
    ], default='available')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.donor.username}"


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

    default_quantity_unit = models.CharField(
        max_length=50,
        choices=[
            ('Kilograms (kg)', 'Kilograms (kg)'),
            ('Grams (g)', 'Grams (g)'),
            ('Liters (L)', 'Liters (L)'),
            ('Units', 'Units'),
        ],
        default='Units'
    )

    preferred_pickup_time = models.CharField(
        max_length=50,
        choices=[
            ('Morning (8am–12pm)', 'Morning (8am–12pm)'),
            ('Afternoon (12pm–4pm)', 'Afternoon (12pm–4pm)'),
            ('Evening (4pm–8pm)', 'Evening (4pm–8pm)'),
        ],
        blank=True,
        null=True
    )

    advance_notice = models.IntegerField(
        choices=[
            (1, "1 day"),
            (2, "2 days"),
            (3, "3 days"),
            (7, "1 week"),
        ],
        default=1,
        blank=True,
        null=True
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class FoodDonation(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('claimed', 'Claimed'),
        ('delivered', 'Delivered'),
        ('expired', 'Expired'),
    )

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
        ('others', 'Other'),
    ]

    UNIT_CHOICES = [
        ('kg', 'Kilograms'),
        ('lbs', 'Pounds'),
        ('pieces', 'Pieces'),
        ('portions', 'Portions'),
        ('litres', 'Litres'),
        ('packs', 'Packs'),
    ]

    DIETARY_CHOICES = [
        ('halal', 'Halal'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('gluten_free', 'Gluten-Free'),
        ('none', 'None'),
    ]

    ALLERGEN_CHOICES = [
        ('nuts', 'Nuts'),
        ('dairy', 'Dairy'),
        ('gluten', 'Gluten'),
        ('soy', 'Soy'),
        ('shellfish', 'Shellfish'),
    ]
    

    # Use string reference to avoid circular imports
    donor = models.ForeignKey('fooddonor.Profile', on_delete=models.CASCADE, related_name='donations')
    title = models.CharField(max_length=100)
    description = models.TextField()
    quantity_amount = models.FloatField(default=1.0)
    quantity_unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='kg')
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    dietary_info = models.TextField(blank=True, null=True)
    known_allergens = models.TextField(blank=True, null=True)
    expiry_date = models.DateField()
    pickup_location = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='', null=True, blank=True)
    
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
    donation = models.ForeignKey(FoodDonation, on_delete=models.CASCADE)
    recipient = models.ForeignKey(Profile, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pickup_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=50, default='General')
    
    def __str__(self):
        return f"Request for {self.donation.title} by {self.recipient.user.username}"
    
class FoodItem(models.Model):
    title = models.CharField(max_length=100)
    image_url = models.URLField()
    quantity = models.CharField(max_length=100)
    expiry_date = models.DateField()
    donor = models.ForeignKey('auth.User', on_delete=models.CASCADE)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username} - {'Read' if self.read else 'Unread'}"


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s settings"
