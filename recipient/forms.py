from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import RecipientProfile

class RecipientSignUpForm(UserCreationForm):
    # Personal Information
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    
    # Address Information
    address = forms.CharField(widget=forms.Textarea, required=True)
    city = forms.CharField(max_length=100, required=True)
    postal_code = forms.CharField(max_length=10, required=True)
    state = forms.ChoiceField(choices=[
        ('Johor', 'Johor'),
        ('Kedah', 'Kedah'),
        ('Kelantan', 'Kelantan'),
        ('Kuala Lumpur', 'Kuala Lumpur'),
        ('Labuan', 'Labuan'),
        ('Melaka', 'Melaka'),
        ('Negeri Sembilan', 'Negeri Sembilan'),
        ('Pahang', 'Pahang'),
        ('Penang', 'Penang'),
        ('Perak', 'Perak'),
        ('Perlis', 'Perlis'),
        ('Putrajaya', 'Putrajaya'),
        ('Sabah', 'Sabah'),
        ('Sarawak', 'Sarawak'),
        ('Selangor', 'Selangor'),
        ('Terengganu', 'Terengganu'),
    ], required=True)
    
    # Household Information
    household_size = forms.ChoiceField(choices=[
        ('1', '1 person'),
        ('2', '2 people'),
        ('3', '3 people'),
        ('4', '4 people'),
        ('5', '5 people'),
        ('6+', '6+ people'),
    ], required=True)
    
    monthly_income = forms.ChoiceField(choices=[
        ('below_1000', 'Below RM 1,000'),
        ('1000_2000', 'RM 1,000 - RM 2,000'),
        ('2000_3000', 'RM 2,000 - RM 3,000'),
        ('3000_4000', 'RM 3,000 - RM 4,000'),
        ('above_4000', 'Above RM 4,000'),
    ], required=False)
    
    special_needs = forms.CharField(
        widget=forms.Textarea, 
        required=False,
        help_text="Any dietary restrictions, allergies, or special needs"
    )
    
    # Account Preferences
    preferred_notification_method = forms.ChoiceField(
        choices=[
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('both', 'Both')
        ],
        initial='email'
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        label="I agree to the Terms and Conditions and Privacy Policy"
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 
            'phone_number', 'date_of_birth', 'address', 'city', 
            'postal_code', 'state', 'household_size', 'monthly_income',
            'special_needs', 'preferred_notification_method',
            'password1', 'password2', 'terms_accepted'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.Textarea, forms.TextInput, forms.EmailInput, forms.PasswordInput)):
                field.widget.attrs.update({'class': 'form-control'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Create recipient profile
            RecipientProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data['phone_number'],
                location=f"{self.cleaned_data['address']}, {self.cleaned_data['postal_code']} {self.cleaned_data['city']}, {self.cleaned_data['state']}",
                needs_description=self.cleaned_data['special_needs'],
                preferred_notification_method=self.cleaned_data['preferred_notification_method'],
                household_size=self.cleaned_data['household_size'],
                monthly_income=self.cleaned_data['monthly_income'],
                date_of_birth=self.cleaned_data['date_of_birth']
            )
        
        return user