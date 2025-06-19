from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from .models import (
    RecipientProfile, 
    RecipientPreference, 
    DonationRequest, 
    PickupSchedule,
    WishlistItem
)
from fooddonor.models import FoodDonation
from datetime import datetime, timedelta, timezone
from django.utils import timezone


class RecipientSignUpForm(UserCreationForm):
    """Composite Pattern for signup form"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'."
    )
    phone_number = forms.CharField(
        validators=[phone_regex],
        max_length=17,
        help_text="Format: +999999999"
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Must be at least 18 years old"
    )
    
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    city = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=10)
    
    STATE_CHOICES = [
        ('Johor', 'Johor'),
        ('Kedah', 'Kedah'),
        ('Kelantan', 'Kelantan'),
        ('Malacca', 'Malacca'),
        ('Negeri Sembilan', 'Negeri Sembilan'),
        ('Pahang', 'Pahang'),
        ('Penang', 'Penang'),
        ('Perak', 'Perak'),
        ('Perlis', 'Perlis'),
        ('Sabah', 'Sabah'),
        ('Sarawak', 'Sarawak'),
        ('Selangor', 'Selangor'),
        ('Terengganu', 'Terengganu'),
        ('Kuala Lumpur', 'Kuala Lumpur'),
        ('Labuan', 'Labuan'),
        ('Putrajaya', 'Putrajaya'),
    ]
    state = forms.ChoiceField(choices=STATE_CHOICES)
    
    HOUSEHOLD_CHOICES = [(i, f"{i} person{'s' if i > 1 else ''}") for i in range(1, 11)]
    household_size = forms.ChoiceField(choices=HOUSEHOLD_CHOICES)
    
    INCOME_CHOICES = [
        ('below_1000', 'Below RM 1,000'),
        ('1000_2000', 'RM 1,000 - RM 2,000'),
        ('2000_3000', 'RM 2,000 - RM 3,000'),
        ('3000_4000', 'RM 3,000 - RM 4,000'),
        ('4000_5000', 'RM 4,000 - RM 5,000'),
        ('above_5000', 'Above RM 5,000'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    monthly_income = forms.ChoiceField(choices=INCOME_CHOICES, required=False)
    
    needs_description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Any dietary restrictions or special needs"
    )
    
    NOTIFICATION_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both')
    ]
    preferred_notification = forms.ChoiceField(
        choices=NOTIFICATION_CHOICES,
        initial='email'
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        label=_("I accept the terms and conditions")
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'password1', 'password2', 'phone_number', 'date_of_birth',
            'address', 'city', 'postal_code', 'state', 'household_size',
            'monthly_income', 'needs_description', 'preferred_notification',
            'terms_accepted'
        ]

    def clean_date_of_birth(self):
        dob = self.cleaned_data['date_of_birth']
        today = datetime.now().date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError("You must be at least 18 years old to register.")
        return dob

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile = RecipientProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                date_of_birth=self.cleaned_data['date_of_birth'],
                address=self.cleaned_data['address'],
                city=self.cleaned_data['city'],
                postal_code=self.cleaned_data['postal_code'],
                state=self.cleaned_data['state'],
                household_size=self.cleaned_data['household_size'],
                monthly_income=self.cleaned_data['monthly_income'],
                needs_description=self.cleaned_data['needs_description'],
                preferred_notification=self.cleaned_data['preferred_notification']
            )
        return user

class RecipientProfileForm(forms.ModelForm):
    """Adapter Pattern for profile editing"""
    class Meta:
        model = RecipientProfile
        fields = [
            'phone_number', 'address', 'city', 'postal_code', 'state',
            'household_size', 'monthly_income', 'needs_description',
            'preferred_notification'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'needs_description': forms.Textarea(attrs={'rows': 3}),
        }

class RecipientPreferenceForm(forms.ModelForm):
    """Strategy Pattern for preferences"""
    CATEGORY_CHOICES = [
        ('fruits', 'Fruits'),
        ('vegetables', 'Vegetables'),
        ('grains', 'Grains & Cereals'),
        ('dairy', 'Dairy Products'),
        ('meat', 'Meat & Poultry'),
        ('seafood', 'Seafood'),
        ('bakery', 'Bakery Items'),
        ('prepared', 'Prepared Food'),
        ('beverages', 'Beverages'),
        ('canned', 'Canned Goods'),
        ('other', 'Other'),
    ]
    
    DIETARY_RESTRICTIONS = [
        ('halal', 'Halal'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('gluten_free', 'Gluten-Free'),
        ('kosher', 'Kosher'),
        ('nut_free', 'Nut-Free'),
        ('lactose_free', 'Lactose-Free'),
    ]
    
    PICKUP_TIMES = [
        ('morning', 'Morning (8am-12pm)'),
        ('afternoon', 'Afternoon (12pm-4pm)'),
        ('evening', 'Evening (4pm-8pm)'),
    ]
    
    preferred_categories = forms.MultipleChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    dietary_restrictions = forms.MultipleChoiceField(
        choices=DIETARY_RESTRICTIONS,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    preferred_pickup_times = forms.MultipleChoiceField(
        choices=PICKUP_TIMES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = RecipientPreference
        fields = [
            'preferred_categories',
            'dietary_restrictions',
            'preferred_pickup_times',
            'max_pickup_distance',
            'advance_notice'
        ]



class DonationRequestForm(forms.ModelForm):
    """Builder Pattern for donation requests"""
    pickup_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text="Preferred pickup date and time"
    )
    
    def __init__(self, *args, **kwargs):
        self.donation = kwargs.pop('donation', None)
        self.recipient = kwargs.pop('recipient', None)
        super().__init__(*args, **kwargs)
        
        if self.donation:
            min_date = timezone.now() + timedelta(hours=2)
            max_date = self.donation.expiry_date - timedelta(hours=12)
            self.fields['pickup_date'].widget.attrs['min'] = min_date.strftime('%Y-%m-%dT%H:%M')
            self.fields['pickup_date'].widget.attrs['max'] = max_date.strftime('%Y-%m-%dT%H:%M')

    class Meta:
        model = DonationRequest
        fields = ['message', 'pickup_date']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Explain why you need this donation...'
            }),
        }

class RequestCancellationForm(forms.ModelForm):
    """Command Pattern for cancellations"""
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text="Please explain why you're cancelling this request"
    )

    class Meta:
        model = DonationRequest
        fields = ['cancellation_reason']

class PickupScheduleForm(forms.ModelForm):
    """Observer Pattern for pickup schedules"""
    class Meta:
        model = PickupSchedule
        fields = ['scheduled_time', 'driver_name', 'driver_contact', 'vehicle_details', 'notes']
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class DonationFeedbackForm(forms.ModelForm):
    """Observer Pattern for feedback"""
    class Meta:
        model = DonationRequest
        fields = ['feedback', 'rating']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'How was your experience with this donation?'
            }),
            'rating': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'class': 'rating-input'
            }),
        }
        labels = {
            'feedback': _('Your Feedback'),
            'rating': _('Rating (1-5)')
        }
        help_texts = {
            'rating': _('1 = Poor, 5 = Excellent')
        }

class WishlistItemForm(forms.ModelForm):
    """Composite Pattern for wishlist items"""
    class Meta:
        model = WishlistItem
        fields = ['name', 'category', 'priority', 'desired_frequency', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'desired_frequency': forms.TextInput(attrs={
                'placeholder': 'e.g., weekly, monthly'
            }),
        }



class ConfirmPickupForm(forms.Form):
    confirmation = forms.BooleanField(
        required=True,
        label="I confirm I have received this donation",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )