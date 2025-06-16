from .base_donation_handler import BaseDonationHandler

class DonationLogger:
    def __init__(self, wrapped):
        self._wrapped = wrapped

    def handle(self, donation):
        print(f"[LOG] Donation created: {donation}")
        self._wrapped.handle(donation)