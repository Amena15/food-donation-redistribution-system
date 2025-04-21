# In foodadmin/models.py
from django.db import models
from fooddonor.models import Profile, FoodDonation, DonationRequest

class AdminActivity(models.Model):
    ACTION_CHOICES = (
        ('approve_donation', 'Approved Donation'),
        ('reject_donation', 'Rejected Donation'),
        ('verify_user', 'Verified User'),
        ('ban_user', 'Banned User'),
        ('other', 'Other Action'),
    )
    
    admin = models.ForeignKey(Profile, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'})
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    target_user = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_actions')
    target_donation = models.ForeignKey(FoodDonation, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.admin.user.username} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"