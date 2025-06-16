from .donation_strategy import DonationStrategy

# strategies/context.py
class DonationContext:
    def __init__(self, strategy: DonationStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: DonationStrategy):
        self.strategy = strategy

    def assign_recipient(self, donation, recipient_list):
        return self.strategy.select_recipient(donation, recipient_list)
