# strategies/first_come.py
from .donation_strategy import DonationStrategy

class FirstComeFirstServeStrategy(DonationStrategy):
    def select_recipient(self, donation, recipient_list):
        return sorted(recipient_list, key=lambda r: r.requested_at)
