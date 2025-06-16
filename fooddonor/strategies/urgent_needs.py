# strategies/urgent_needs.py
from .donation_strategy import DonationStrategy

class UrgentNeedsStrategy(DonationStrategy):
    def select_recipient(self, donation, recipient_list):
        return [r for r in recipient_list if r.needs_description and "urgent" in r.needs_description.lower()]
