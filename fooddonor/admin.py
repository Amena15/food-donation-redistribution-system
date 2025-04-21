from django.contrib import admin
from .models import Profile, FoodDonation, DonationRequest

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'phone_number')

@admin.register(FoodDonation)
class FoodDonationAdmin(admin.ModelAdmin):
    list_display = ('title', 'donor', 'status', 'created_at', 'expiry_date')
    list_filter = ('status',)
    search_fields = ('title', 'description', 'donor__user__username')
    date_hierarchy = 'created_at'

@admin.register(DonationRequest)
class DonationRequestAdmin(admin.ModelAdmin):
    list_display = ('donation', 'recipient', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('donation__title', 'recipient__user__username')
    date_hierarchy = 'created_at'