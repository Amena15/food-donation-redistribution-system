# Design Pattern Used: Strategy Pattern
# --------------------------------------------------
# The Strategy Pattern is applied here to allow dynamic selection of 
# different matching algorithms (strategies) based on food donation matching logic.
# Each strategy (e.g., location, expiry, category preference) implements a common interface
# so they can be used interchangeably.

from abc import ABC, abstractmethod
from typing import List, Tuple
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from django.utils import timezone
from django.contrib.gis.geos import Point
from recipient.models import RecipientProfile, RecipientPreference
from fooddonor.models import FoodDonation

# --- Abstract Strategy Interface ---
class MatchingStrategy(ABC):
    @abstractmethod
    def calculate_score(self, food_donation: FoodDonation, recipient: RecipientProfile) -> float:
        """Defines an interface to calculate match score between a food donation and a recipient."""
        pass

# --- Concrete Strategy: Location-based Matching ---
class LocationStrategy(MatchingStrategy):
    def haversine(self, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
        """
        Calculate the great-circle distance in kilometers between two geographic coordinates.
        """
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371  # Radius of Earth in km
        return c * r

    def calculate_score(self, food_donation: FoodDonation, recipient: RecipientProfile) -> float:
        """
        Higher score for recipients closer to the food donation's pickup location.
        """
        if not hasattr(recipient, 'location') or not recipient.location:
            return 0
        
        if not food_donation.pickup_location:
            return 0

        # Extract coordinates from PointField
        donor_point = food_donation.pickup_location
        recipient_point = recipient.location
        
        distance_km = self.haversine(
            donor_point.x, donor_point.y,
            recipient_point.x, recipient_point.y
        )

        max_distance = 50  # km
        score = max(0, 1 - (distance_km / max_distance))  # Score decreases with distance
        return score

# --- Concrete Strategy: Expiry-based Matching ---
class ExpiryStrategy(MatchingStrategy):
    def calculate_score(self, food_donation: FoodDonation, recipient: RecipientProfile) -> float:
        """
        Higher score for food donations that are closer to expiration (urgency-based).
        """
        days_remaining = (food_donation.expiry_date - timezone.now().date()).days
        return max(0, min(1, (7 - days_remaining) / 7))  # Normalize score between 0 and 1

# --- Concrete Strategy: Category Preference Matching ---
class CategoryPreferenceStrategy(MatchingStrategy):
    def calculate_score(self, food_donation: FoodDonation, recipient: RecipientProfile) -> float:
        """
        Match based on recipient's food preferences.
        """
        try:
            preferences = recipient.preferences
            if not preferences.preferred_categories:
                return 0.5  # Default if no preferences set
            
            # Check if food category matches any preferred categories
            category_match = food_donation.category in preferences.preferred_categories
            return 1.0 if category_match else 0.0
        except RecipientPreference.DoesNotExist:
            return 0.5  # Default if preferences unavailable

# --- Concrete Strategy: Dietary Restrictions Matching ---
class DietaryRestrictionStrategy(MatchingStrategy):
    def calculate_score(self, food_donation: FoodDonation, recipient: RecipientProfile) -> float:
        """
        Penalize items that don't match dietary restrictions.
        """
        try:
            preferences = recipient.preferences
            if not preferences.dietary_restrictions:
                return 1.0  # No restrictions = perfect score
            
            # Check if food donation violates any restrictions
            for restriction in preferences.dietary_restrictions:
                if restriction.lower() in (food_donation.dietary_info or '').lower():
                    return 0.0 # Complete mismatch if restriction is violated
            
            return 1.0  # Perfect score if no violations
        except RecipientPreference.DoesNotExist:
            return 1.0  # Assume no restrictions if preferences unavailable

# --- Context Class: MatchingService ---
class MatchingService:
    def __init__(self, strategies: List[MatchingStrategy] = None):
        self.strategies = strategies or [
            LocationStrategy(),
            ExpiryStrategy(),
            CategoryPreferenceStrategy(),
            DietaryRestrictionStrategy()
        ]
        self.weights = {
            'location': 0.4,
            'expiry': 0.3,
            'category': 0.2,
            'dietary': 0.1
        }

    def calculate_match_score(self, food_donation: FoodDonation, recipient: RecipientProfile) -> float:
        """
        Calculate weighted match score between food donation and recipient.
        Returns score normalized to 0-100 range.
        """
        if food_donation.status != 'available':
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for strategy in self.strategies:
            if isinstance(strategy, LocationStrategy):
                weight = self.weights['location']
            elif isinstance(strategy, ExpiryStrategy):
                weight = self.weights['expiry']
            elif isinstance(strategy, CategoryPreferenceStrategy):
                weight = self.weights['category']
            elif isinstance(strategy, DietaryRestrictionStrategy):
                weight = self.weights['dietary']
            else:
                weight = 1.0  # Default weight for custom strategies

            score = strategy.calculate_score(food_donation, recipient)
            total_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return (total_score / total_weight) * 100  # Scale to percentage

    def calculate_distance(self, food_donation: FoodDonation, recipient: RecipientProfile) -> float:
        """
        Calculate the distance between the recipient and the food donation's pickup location.
        Returns the distance in kilometers.
        """
        if not hasattr(recipient, 'location') or not recipient.location:
            return float('inf')

        if not food_donation.pickup_location:
            return float('inf')

        # Use the LocationStrategy's haversine method
        location_strategy = LocationStrategy()
        return location_strategy.haversine(
            food_donation.pickup_location.x, food_donation.pickup_location.y,
            recipient.location.x, recipient.location.y
        )

    def find_best_recipients(self, food_donation: FoodDonation, max_results: int = 5) -> List[Tuple[RecipientProfile, float]]:
        """
        Finds the top matching recipients for a given food donation.
        Returns: List of tuples (recipient, match_score)
        """
        if food_donation.status != 'available':
            return []

        recipients = RecipientProfile.objects.filter(
            user__is_active=True,
            verification_status='verified'
        ).select_related('preferences')

        scored_recipients = []
        for recipient in recipients:
            score = self.calculate_match_score(food_donation, recipient)
            if score > 0:  # Only include recipients with non-zero scores
                scored_recipients.append((recipient, score))
        
        # Sort by score descending
        scored_recipients.sort(key=lambda x: x[1], reverse=True)
        return scored_recipients[:max_results]

    def find_best_donations(self, recipient: RecipientProfile, max_results: int = 10) -> List[Tuple[FoodDonation, float]]:
        """
        Finds the top matching food donations for a given recipient.
        Returns: List of tuples (food_donation, match_score)
        """
        available_donations = FoodDonation.objects.filter(
            status='available',
            expiry_date__gte=timezone.now().date()
        )

        scored_donations = []
        for donation in available_donations:
            score = self.calculate_match_score(donation, recipient)
            if score > 0:  # Only include donations with non-zero scores
                scored_donations.append((donation, score))
        
        # Sort by score descending
        scored_donations.sort(key=lambda x: x[1], reverse=True)
        return scored_donations[:max_results]

    def get_matching_donations_for_recipient(self, recipient: RecipientProfile, max_results: int = 10) -> List[FoodDonation]:
        """
        Convenience method that returns just the FoodDonation objects sorted by match score.
        """
        matched = self.find_best_donations(recipient, max_results)
        return [donation for donation, score in matched]