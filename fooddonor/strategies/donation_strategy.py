# strategies/donation_strategy.py
from abc import ABC, abstractmethod

class DonationStrategy(ABC):
    @abstractmethod
    def select_recipient(self, donation, recipient_list):
        pass
