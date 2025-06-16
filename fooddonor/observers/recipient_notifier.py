# observers/recipient_notifier.py
from .observer import Observer
from django.core.mail import send_mail
from recipient.models import Recipient

class RecipientNotifier(Observer):
    def update(self, donation):
        recipients = Recipient.objects.filter(location=donation.pickup_location)
        for recipient in recipients:
            send_mail(
                'New Donation Available!',
                f"A new donation '{donation.title}' is available in your area.",
                'noreply@fooddonation.com',
                [recipient.user.email],
                fail_silently=True,
            )
