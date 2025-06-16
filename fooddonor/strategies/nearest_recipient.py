# strategies/nearest_recipient.py
from .donation_strategy import DonationStrategy

class NearestRecipientStrategy(DonationStrategy):
    def select_recipient(self, donation, recipient_list):
        # Sort recipients based on proximity to donation pickup location
        return sorted(recipient_list, key=lambda r: r.distance_to(donation.pickup_location))
