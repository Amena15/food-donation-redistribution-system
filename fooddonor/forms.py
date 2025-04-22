from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, FoodDonation, DonationRequest

# Sign-Up Form
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    
    ROLES = (
        ('donor', 'Food Donor'),
        ('recipient', 'Food Recipient'),
    )
    role = forms.ChoiceField(choices=ROLES, required=True)
    
    # Optional fields based on role
    location = forms.CharField(max_length=255, required=False)
    needs_description = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'role', 'location', 'needs_description', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Custom validation to ensure the username is not too short
        if len(username) < 6:
            raise forms.ValidationError("Username must be at least 6 characters long.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        if role == 'donor' and not cleaned_data.get('location'):
            raise forms.ValidationError("Location is required for Food Donors.")
        
        if role == 'recipient' and not cleaned_data.get('needs_description'):
            raise forms.ValidationError("Description of needs is required for Food Recipients.")
        
        return cleaned_data

# Food Donation Form
class FoodDonationForm(forms.ModelForm):
    class Meta:
        model = FoodDonation
        fields = ['title', 'description', 'quantity', 'expiry_date', 'pickup_location']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'quantity': forms.TextInput(attrs={'class': 'form-control'}),
            'pickup_location': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Donation Request Form
class DonationRequestForm(forms.ModelForm):
    class Meta:
        model = DonationRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
