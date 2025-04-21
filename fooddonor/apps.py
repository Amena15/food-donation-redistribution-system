from django.apps import AppConfig


class DonationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fooddonor'
    verbose_name = 'Food Donation Management'  # Optional: Human-readable name for the app
