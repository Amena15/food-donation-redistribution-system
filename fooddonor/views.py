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
from django.utils import timezone
from datetime import timedelta
import json
from django.http import JsonResponse
from .models import Notification
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .factories import UserFactory 
from .strategies.context import DonationContext
from .strategies.nearest_recipient import NearestRecipientStrategy
from .strategies.urgent_needs import UrgentNeedsStrategy
from .strategies.first_come import FirstComeFirstServeStrategy
from recipient.models import RecipientProfile
from .observers.subject import Subject
from .decorators.base_donation_handler import BaseDonationHandler
from .decorators.donation_logger import DonationLogger
from .decorators.email_notifier import EmailNotifier
from .singleton.singleton import NotificationManager
from .models import UserSettings
from django.core.paginator import Paginator
from collections import defaultdict


def home(request):
    return render(request, 'home.html')

def about(request):
    """Static about page"""
    return render(request, 'about.html')

def contact(request):
    """Contact form view"""
    if request.method == 'POST':
        messages.success(request, "Your message has been sent successfully!")
        return render(request, 'contact.html', {'message_sent': True})
    return render(request, 'contact.html')

def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Extract form data
            phone_number = form.cleaned_data.get('phone_number')
            role = form.cleaned_data.get('role')
            location = form.cleaned_data.get('location')
            needs_description = form.cleaned_data.get('needs_description')

            # Use the Factory Pattern here!
            profile = UserFactory.create_user(user, role)
            profile.phone_number = phone_number
            profile.location = location
            profile.needs_description = needs_description
            profile.save()

            login(request, user)

            # Role-based redirect (optional for future enhancement)
            if role == 'donor':
                return redirect('fooddonor:donor_dashboard')
            elif role == 'recipient':
                return redirect('foodrecipient:recipient_dashboard')
            elif role == 'admin':
                return redirect('foodadmin:admindashboard')
            else:
                return redirect('home')  # fallback
        else:
            # Return form with errors if invalid
            # Add Bootstrap styling to all fields
            for field in form.fields.values():
                if isinstance(field.widget, (forms.Textarea, forms.TextInput, forms.EmailInput, forms.PasswordInput)):
                    field.widget.attrs.update({'class': 'form-control'})
                elif isinstance(field.widget, forms.Select):
                    field.widget.attrs.update({'class': 'form-select'})
                else:
                    field.widget.attrs.update({'class': 'form-control'})
            return render(request, 'registeruser.html', {'form': form})
    else:
        form = SignUpForm()

    # Add Bootstrap styling to all fields
    for field in form.fields.values():
        if isinstance(field.widget, (forms.Textarea, forms.TextInput, forms.EmailInput, forms.PasswordInput)):
            field.widget.attrs.update({'class': 'form-control'})
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs.update({'class': 'form-select'})
        else:
            field.widget.attrs.update({'class': 'form-control'})

    return render(request, 'registeruser.html', {'form': form})

def choose_login(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')

        if user_type == 'fooddonor':
            return redirect('fooddonor:donorlogin')  
        elif user_type == 'foodrecipient':
            return redirect('recipient:recipientlogin')
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
                return redirect('foodadmin:admindashboard')

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
    return redirect('fooddonor:home') 


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
    ).aggregate(total=Sum('quantity_amount'))['total'] or 0

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
        .annotate(total=Sum('quantity_amount'))
        .order_by('month')
    )

    donated_by_category = (
        FoodDonation.objects.filter(donor=profile, status='delivered')
        .values('title')
        .annotate(total=Sum('quantity_amount'))
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


def is_recipient(user):
    try:
        return user.profile.role == 'recipient'
    except Profile.DoesNotExist:
        return False

# Donation list view
@login_required
@user_passes_test(is_donor)
def donation_list(request):
    donor = request.user.profile
    food_listings = FoodDonation.objects.filter(donor=donor).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(food_listings, 10)  # Show 10 listings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Stats
    total = food_listings.count()
    active = food_listings.filter(status='available').count()
    pending = food_listings.filter(status='pending').count()
    delivered = food_listings.filter(status='delivered').count()

    return render(request, 'donationlist.html', {
        'food_listings': page_obj,
        'total_listings': total,
        'active_listings': active,
        'pending_listings': pending,
        'delivered_listings': delivered
    })


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
    return render(request, 'donation/donationdetail.html', context)

def assign_donation(request, donation_id):
    donation = get_object_or_404(FoodDonation, pk=donation_id)
    recipient_list = RecipientProfile.objects.all()  # Example list

    # Select strategy (can be chosen by user input in real app)
    strategy = NearestRecipientStrategy()  # You can switch this to UrgentNeedsStrategy(), etc.
    
    context = DonationContext(strategy)
    selected_recipients = context.assign_recipient(donation, recipient_list)

    # Do something with selected_recipients (e.g., show in template or auto-assign)
    return render(request, 'assign_result.html', {'recipients': selected_recipients})

@login_required
def request_donation(request, pk):
    """View to handle a recipient requesting a donation"""
    donation = get_object_or_404(FoodDonation, pk=pk)
    user_profile = request.user.profile

    if user_profile.role != 'recipient':
        messages.error(request, "Only recipients can request donations.")
        return redirect('fooddonor:donation_detail', pk=pk)

    if request.method == 'POST':
        form = DonationRequestForm(request.POST)
        if form.is_valid():
            donation_request = form.save(commit=False)
            donation_request.donation = donation
            donation_request.recipient = user_profile
            donation_request.status = 'pending'
            donation_request.save()
            messages.success(request, "Your request has been submitted.")
            return redirect('fooddonor:donationdetail', pk=pk)
    else:
        form = DonationRequestForm()

    return render(request, 'donation/request_form.html', {'form': form, 'donation': donation})

def donation_created(request):
    manager = NotificationManager()
    manager.send_notification(request.user, "Your donation was successfully posted!")

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

@login_required
def add_food(request):
    if request.method == 'POST':
        form = FoodDonationForm(request.POST, request.FILES)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user.profile
            donation.save()

            # Notify, log, whatever...
            messages.success(request, "Food donation listing added successfully!")
            return redirect('fooddonor:donation_list')
        else:
            messages.error(request, "Please correct the form errors below.")
    else:
        form = FoodDonationForm()
    
    return render(request, 'addfoodlisting.html', {'form': form})

@login_required
@user_passes_test(is_donor)
def edit_food(request, pk):
    food = get_object_or_404(FoodDonation, pk=pk, donor=request.user.profile)
    if request.method == 'POST':
        form = FoodDonationForm(request.POST, request.FILES, instance=food)
        if form.is_valid():
            form.save()
            messages.success(request, "Donation updated successfully!")
            return redirect('fooddonor:donation_list')
    else:
        form = FoodDonationForm(instance=food)
    return render(request, 'editfoodlisting.html', {'form': form, 'food': food})

@login_required
@user_passes_test(is_donor)
def delete_food(request, pk):
    food = get_object_or_404(FoodDonation, pk=pk, donor=request.user.profile)
    food.delete()
    messages.success(request, "Donation deleted successfully.")
    return redirect('fooddonor:donation_list')


def pickup_schedule(request):
    # Replace with your actual queryset
    upcoming_pickups = []  # Example: PickupSchedule.objects.filter(donor=request.user)
    return render(request, 'pickupschedule.html', {
        'upcoming_pickups': upcoming_pickups
    })

def notifications(request):
    # Dummy notifications for display purposes
    notifications = [
        {"date": "2025-06-12", "message": "Your donation has been picked up.", "status": "Read"},
        {"date": "2025-06-10", "message": "New pickup scheduled for June 15.", "status": "Unread"},
    ]
    return render(request, 'notifications.html', {'notifications': notifications})

def submit_feedback(request):
    if request.method == 'POST':
        # Here you can handle the feedback form submission if needed
        # For now, just redirect back to the feedback page or show a success message
        return render(request, 'feedback.html', {'message': 'Thank you for your feedback!'})
    return render(request, 'feedback.html')

@login_required
def donation_history(request):
    donations = FoodDonation.objects.filter(donor__user=request.user)

    # Group total quantity_amount by unit
    unit_totals = defaultdict(float)
    for d in donations:
        if d.quantity_amount and d.quantity_unit:
            unit_totals[d.quantity_unit] += d.quantity_amount

    # Pagination
    paginator = Paginator(donations, 10)  # Show 10 donations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Sample logic for statistics (customize as needed)
    total_donations = donations.count()
    total_weight = sum(
    float(d.quantity_amount)
        for d in donations
        if d.quantity_unit == "kg"
    )
    estimated_meals = total_weight * 4  # e.g., 1kg = 4 meals
    total_impact = estimated_meals // 2  # example assumption

    return render(request, 'donationhistory.html', {
        'donations': donations,
        'total_donations': total_donations,
        'total_weight': total_weight,
        'estimated_meals': estimated_meals,
        'total_impact': total_impact,
    })

@login_required
@user_passes_test(is_donor)
def settings(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()

            # Basic validation (can be extended)
            if not first_name or not last_name or not email:
                messages.error(request, "Please fill in all required profile fields.")
            else:
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.save()

                profile.phone = phone
                profile.save()

                messages.success(request, "Profile information updated successfully.")

        elif form_type == 'organization':
            org_name = request.POST.get('org_name', '').strip()
            org_type = request.POST.get('org_type', '').strip()
            address = request.POST.get('address', '').strip()
            city = request.POST.get('city', '').strip()
            postal_code = request.POST.get('postal_code', '').strip()

            if not org_name or not org_type or not address or not city or not postal_code:
                messages.error(request, "Please fill in all required organization fields.")
            else:
                profile.organization_name = org_name
                profile.organization_type = org_type
                profile.address = address
                profile.city = city
                profile.postal_code = postal_code
                profile.save()

                messages.success(request, "Organization details updated successfully.")

        elif form_type == 'notifications':
            profile.email_notifications = 'email_notifications' in request.POST
            profile.sms_notifications = 'sms_notifications' in request.POST
            profile.pickup_reminders = 'pickup_reminders' in request.POST
            profile.weekly_reports = 'weekly_reports' in request.POST
            profile.feature_updates = 'feature_updates' in request.POST
            profile.save()

            messages.success(request, "Notification preferences updated successfully.")

        elif form_type == 'donation_preferences':
            profile.default_quantity_unit = request.POST.get('default_quantity_unit', profile.default_quantity_unit)
            profile.preferred_pickup_time = request.POST.get('preferred_pickup_time', profile.preferred_pickup_time)
            profile.advance_notice = request.POST.get('advance_notice', profile.advance_notice)
            profile.save()

            messages.success(request, "Donation preferences updated successfully.")

        elif form_type == 'password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            elif len(new_password) < 8:
                messages.error(request, "New password must be at least 8 characters long.")
            else:
                user.set_password(new_password)
                user.save()
                profile.password_changed_at = timezone.now()
                profile.save()
                messages.success(request, "Password changed successfully.")
                # After password change, re-login might be required
                return redirect('fooddonor:donorlogin')

        elif form_type == 'delete_account':
            user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect('fooddonor:home')

        else:
            messages.error(request, "Invalid form submission.")

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'donorsettings.html', context)


def get_user_settings(user):
    settings, created = UserSettings.objects.get_or_create(user=user)
    return settings

@login_required
def notifications_view(request):
    user = request.user
    notifications = Notification.objects.filter(user=user).order_by('-date')
    stats = {
        'unread_count': notifications.filter(read=False).count(),
        'urgent_count': notifications.filter(urgent=True).count(),
        'total_week': notifications.filter(date__gte=timezone.now() - timedelta(days=7)).count(),
    }
    user_settings = get_user_settings(user)
    return render(request, 'notifications.html', {
        'notifications': notifications,
        'stats': stats,
        'user_settings': user_settings,
    })

@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return JsonResponse({'status': 'success'})

@login_required
def mark_notification_read(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        Notification.objects.filter(id=data['id'], user=request.user).update(read=True)
        return JsonResponse({'status': 'success'})

@login_required
def delete_notification(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        Notification.objects.filter(id=data['id'], user=request.user).delete()
        return JsonResponse({'status': 'success'})


@login_required
@csrf_exempt
def toggle_email_notifications(request):
    if request.method == 'POST':
        profile = request.user.profile
        profile.email_notifications = not profile.email_notifications
        profile.save()
        return JsonResponse({'status': 'success', 'email_notifications': profile.email_notifications})

@login_required
@require_POST
def toggle_sms_notifications(request):
    # Dummy response; replace with your actual logic
    return JsonResponse({'status': 'SMS notifications toggled'})

@login_required
@require_POST
def toggle_push_notifications(request):
    # Replace with your actual toggle logic
    return JsonResponse({'status': 'Push notifications toggled'})