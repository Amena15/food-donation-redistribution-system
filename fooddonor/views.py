# donation/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import FoodDonation, DonationRequest, Profile
from .forms import FoodDonationForm, DonationRequestForm, SignUpForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
from django.contrib.auth import logout as django_logout
from django.urls import reverse
from django.db.models import Sum, Count
from datetime import date
from django.db.models.functions import TruncMonth
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from .models import FoodListing
from .forms import FoodDonationForm


def home(request):
    return render(request, 'home.html')

def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create Profile instance linked to user
            phone_number = form.cleaned_data.get('phone_number')
            role = form.cleaned_data.get('role')
            location = form.cleaned_data.get('location')
            needs_description = form.cleaned_data.get('needs_description')
            from .models import Profile
            Profile.objects.create(
                user=user,
                phone_number=phone_number,
                role=role,
                location=location,
                needs_description=needs_description
            )
            login(request, user)
            return redirect('fooddonor:donor_dashboard')  # Correct redirection after successful signup
    else:
        form = SignUpForm()

    # Add Bootstrap classes to form fields
    for field_name, field in form.fields.items():
        # Check if widget is Textarea or other field types
        if isinstance(field.widget, forms.Textarea):
            field.widget.attrs.update({'class': 'form-control'})
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs.update({'class': 'form-select'})
        elif isinstance(field.widget, forms.TextInput):
            field.widget.attrs.update({'class': 'form-control'})
        elif isinstance(field.widget, forms.EmailInput):
            field.widget.attrs.update({'class': 'form-control'})
        elif isinstance(field.widget, forms.PasswordInput):
            field.widget.attrs.update({'class': 'form-control'})
        else:
            field.widget.attrs.update({'class': 'form-control'})  # Fallback for other types

    return render(request, 'registeruser.html', {'form': form})

def choose_login(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')

        if user_type == 'fooddonor':
            return redirect('fooddonor:donorlogin')  
        elif user_type == 'foodrecipient':
            return redirect('foodrecipient:recipientlogin')
        elif user_type == 'foodadmin':
            return redirect('foodadmin:adminlogin')
        else:
            return render(request, 'chooselogin.html', {'error': 'Invalid user type'})
    else:
        return render(request, 'chooselogin.html')

def donor_login(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)

        # ✅ Get the original destination if it exists
        next_url = request.POST.get('next')

        # ✅ If next exists and is safe, go there
        if next_url:
            return redirect(next_url)

        # Otherwise, role-based redirection
        if hasattr(user, 'profile'):
            role = user.profile.role
            if role == 'donor':
                return redirect('fooddonor:donor_dashboard')
            elif role == 'recipient':
                return redirect('foodrecipient:recipient_dashboard')
            elif role == 'admin':
                return redirect('foodadmin:admin_dashboard')

        return redirect('fooddonor:home')  # fallback

    return render(request, 'donorlogin.html', {'form': form})



def recipient_login(request):
    """
    View for handling food recipient login.
    """
    if request.method == 'POST':
        # Process recipient login form
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Add your authentication logic here
        # Similar to donor_login
        
        return render(request, 'recipientlogin.html', {'error': 'Invalid credentials'})
    
    return render(request, 'recipientlogin.html', {'title': 'Food Recipient Login'})

def admin_login(request):
    """
    View for handling admin login.
    """
    if request.method == 'POST':
        # Process admin login form
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Add your authentication logic here
        # Similar to donor_login
        
        return render(request, 'adminlogin.html', {'error': 'Invalid credentials'})
    
    return render(request, 'adminlogin.html', {'title': 'Admin Login'})

def clean_username(self):
    username = self.cleaned_data.get('username')
    # Custom validation to ensure the username is not too short
    if len(username) < 6:
        raise forms.ValidationError("Username must be at least 6 characters long.")
    return username


# Helper functions for role checks
def is_donor(user):
    try:
        return user.profile.role == 'donor'
    except Profile.DoesNotExist:
        return False

def logout(request):
    django_logout(request)
    return redirect('fooddonor:home')  # or 'home' or wherever you want to send the user after logout


@login_required
@user_passes_test(is_donor)
def donor_dashboard(request):
    profile = request.user.profile
    user = request.user

    # 1. Active Listings
    active_listings = FoodDonation.objects.filter(donor=profile, status='available')

    # 2. Total Donated (only delivered donations)
    total_donated = FoodDonation.objects.filter(
        donor=profile,
        status='delivered'
    ).aggregate(total=Sum('quantity'))['total'] or 0

    # 3. Upcoming Pickups
    upcoming_pickups = DonationRequest.objects.filter(
        donation__donor=profile,
        status='approved',
        donation__expiry_date__gte=date.today()
    ).order_by('donation__expiry_date')

    # 4. People Impacted (e.g. 1 kg = ~2.5 meals)
    people_impacted = round(total_donated * 2.5)

    # 5. For Tables Below:
    monthly_donated = (
        FoodDonation.objects.filter(donor=profile, status='delivered')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('quantity'))
        .order_by('month')
    )

    donated_by_category = (
        FoodDonation.objects.filter(donor=profile, status='delivered')
        .values('title')
        .annotate(total=Sum('quantity'))
        .order_by('-total')
    )

    impact_stats = []
    for entry in monthly_donated:
        meals = round(entry['total'] * 2.5)
        beneficiaries = round(meals / 2.0)  # ~2 meals per person
        impact_stats.append({
            'month': entry['month'].strftime("%b %Y"),
            'meals': meals,
            'beneficiaries': beneficiaries,
        })

    context = {
        'active_listings': active_listings.count(),
        'active_listings_data': active_listings,
        'total_donated_kg': total_donated,
        'upcoming_pickups': upcoming_pickups,
        'people_impacted': people_impacted,
        'total_donated_monthly': monthly_donated,
        'donated_by_category': donated_by_category,
        'impact_stats': impact_stats,
        'user_full_name': user.get_full_name() or user.username,
        'user_first_name': user.first_name or user.username,
    }

    return render(request, 'donordashboard.html', context)

@login_required
@user_passes_test(is_donor)
def food_listing(request):
    donations = FoodDonation.objects.filter(donor=request.user.profile).order_by('-created_at')
    return render(request, 'foodlisting.html', {'donations': donations})

def is_recipient(user):
    try:
        return user.profile.role == 'recipient'
    except Profile.DoesNotExist:
        return False

# Donation list view
def donation_list(request):
    """View all available donations"""
    donations = FoodDonation.objects.filter(status='available').order_by('-created_at')
    return render(request, 'donation/donation_list.html', {'donations': donations})

# Donation detail view
def donation_detail(request, pk):
    """View details of a specific donation"""
    donation = get_object_or_404(FoodDonation, pk=pk)
    
    # Check if user is recipient and add request form if needed
    request_form = None
    if request.user.is_authenticated:
        try:
            if request.user.profile.role == 'recipient' and donation.status == 'available':
                # Check if user has already requested this donation
                existing_request = DonationRequest.objects.filter(
                    recipient=request.user.profile,
                    donation=donation
                ).exists()
                
                if not existing_request:
                    request_form = DonationRequestForm()
        except Profile.DoesNotExist:
            pass
    
    context = {
        'donation': donation,
        'request_form': request_form
    }
    return render(request, 'donation/donation_detail.html', context)

# Create donation view
@login_required
@user_passes_test(is_donor)
def donation_create(request):
    """Create a new donation"""
    if request.method == 'POST':
        form = FoodDonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user.profile
            donation.save()
            messages.success(request, "Your donation has been posted successfully!")
            return redirect('donation:donation_detail', pk=donation.pk)
    else:
        form = FoodDonationForm()
    
    return render(request, 'donation/donation_form.html', {'form': form, 'action': 'Create'})

# Edit donation view
@login_required
@user_passes_test(is_donor)
def donation_edit(request, pk):
    """Edit an existing donation"""
    donation = get_object_or_404(FoodDonation, pk=pk, donor__user=request.user)
    
    if donation.status != 'available':
        messages.error(request, "You cannot edit a donation that has been claimed or delivered.")
        return redirect('donation:donation_detail', pk=donation.pk)
    
    if request.method == 'POST':
        form = FoodDonationForm(request.POST, instance=donation)
        if form.is_valid():
            form.save()
            messages.success(request, "Your donation has been updated successfully!")
            return redirect('donation:donation_detail', pk=donation.pk)
    else:
        form = FoodDonationForm(instance=donation)
    
    return render(request, 'donation/donationform.html', {
        'form': form, 
        'action': 'Edit',
        'donation': donation
    })

# Delete donation view
@login_required
@user_passes_test(is_donor)
def donation_delete(request, pk):
    """Delete an existing donation"""
    donation = get_object_or_404(FoodDonation, pk=pk, donor__user=request.user)
    
    if donation.status != 'available':
        messages.error(request, "You cannot delete a donation that has been claimed or delivered.")
        return redirect('donation:donation_detail', pk=donation.pk)
    
    if request.method == 'POST':
        donation.delete()
        messages.success(request, "Your donation has been deleted successfully!")
        return redirect('donor_dashboard')
    
    return render(request, 'donation/donationconfirmdelete.html', {'donation': donation})

# Request list view
@login_required
def request_list(request):
    """View all requests relevant to the user"""
    user_profile = request.user.profile
    
    if user_profile.role == 'donor':
        # Donors see requests for their donations
        requests = DonationRequest.objects.filter(
            donation__donor=user_profile
        ).order_by('-created_at')
    elif user_profile.role == 'recipient':
        # Recipients see their own requests
        requests = DonationRequest.objects.filter(
            recipient=user_profile
        ).order_by('-created_at')
    else:
        # Admin sees all requests
        requests = DonationRequest.objects.all().order_by('-created_at')
    
    return render(request, 'donation/requestlist.html', {'requests': requests})

# Request detail view
@login_required
def request_detail(request, pk):
    """View details of a specific request"""
    user_profile = request.user.profile
    
    # Determine which requests the user can access
    if user_profile.role == 'donor':
        donation_request = get_object_or_404(DonationRequest, pk=pk, donation__donor=user_profile)
    elif user_profile.role == 'recipient':
        donation_request = get_object_or_404(DonationRequest, pk=pk, recipient=user_profile)
    else:  # Admin
        donation_request = get_object_or_404(DonationRequest, pk=pk)
    
    return render(request, 'donation/requestdetail.html', {'request': donation_request})

# Update request status view
@login_required
def update_request_status(request, pk, status):
    """Update the status of a request"""
    user_profile = request.user.profile
    
    # Only donors can update request status
    if user_profile.role != 'donor':
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('donation:request_list')
    
    # Get the request
    donation_request = get_object_or_404(DonationRequest, pk=pk, donation__donor=user_profile)
    
    # Check if the status is valid
    valid_statuses = ['approved', 'rejected', 'completed']
    if status not in valid_statuses:
        messages.error(request, "Invalid status.")
        return redirect('donation:request_detail', pk=donation_request.pk)
    
    # Update the request status
    donation_request.status = status
    donation_request.save()
    
    # If approved, update the donation status and reject other requests
    if status == 'approved':
        donation = donation_request.donation
        donation.status = 'claimed'
        donation.save()
        
        # Reject other pending requests
        other_requests = DonationRequest.objects.filter(
            donation=donation, 
            status='pending'
        ).exclude(pk=pk)
        
        for req in other_requests:
            req.status = 'rejected'
            req.save()
    
    # If completed, update the donation status
    elif status == 'completed':
        donation = donation_request.donation
        donation.status = 'delivered'
        donation.save()
    
    messages.success(request, f"Request has been {status} successfully.")
    return redirect('donation:request_detail', pk=donation_request.pk)

def add_food_listing(request):
    if request.method == 'POST':
        # TODO: process the form submission (you can add logic later)
        pass
    return render(request, 'addfoodlisting.html')


def edit_food(request, pk):
    food = get_object_or_404(FoodListing, pk=pk)
    if request.method == 'POST':
        form = FoodDonationForm(request.POST, request.FILES, instance=food)
        if form.is_valid():
            form.save()
            return redirect('fooddonor:food_listing')
    else:
        form = FoodDonationForm(instance=food)
    return render(request, 'editfoodlisting.html', {'form': form})

def delete_food(request, pk):
    food = get_object_or_404(FoodListing, pk=pk)
    if request.method == 'POST':
        food.delete()
        return redirect('fooddonor:food_listing')
    return render(request, 'confirm_delete.html', {'food': food})

