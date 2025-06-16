from .base_donation_handler import BaseDonationHandler

class EmailNotifier:
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def handle(self, donation):
        # Simulate sending email
        print(f"[EMAIL] Notifying donor and admins about new donation: {donation}")
        self._wrapped.handle(donation)