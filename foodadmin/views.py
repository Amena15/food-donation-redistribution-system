# In foodadmin/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login,logout
from django.urls import reverse
from django.contrib import messages
from fooddonor.models import Profile, FoodDonation, DonationRequest
from .models import AdminActivity
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from fooddonor.models import FoodDonation, DonationRequest, Profile
from django.utils import timezone
from datetime import datetime
import json
from django.db.models.functions import TruncMonth
from fooddonor.models import Feedback

def login_type_selection(request):
    """
    View for displaying the initial login type selection page.
    When form is submitted, redirects to the appropriate login page.
    """
    context = {
        'title': 'Food Donation System - Select Login Type'
    }

    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        
        # Validate user type and redirect accordingly
        if user_type == 'fooddonor':
            return redirect(reverse('donor_login'))
        elif user_type == 'foodrecipient':
            return redirect(reverse('recipient_login'))
        elif user_type == 'foodadmin':
            return redirect(reverse('adminlogin'))
        else:
            context['error'] = 'Invalid user type selected. Please try again.'
    
    return render(request, 'login_selection.html', context)

def donor_login(request):
    """
    View for handling food donor login.
    """
    if request.method == 'POST':
        # Process donor login form
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Add your authentication logic here
        # Example:
        # user = authenticate(request, username=username, password=password, user_type='donor')
        # if user is not None:
        #     login(request, user)
        #     return redirect('donor_dashboard')
        
        # For now, just show a message
        return render(request, 'donorlogin.html', {'error': 'Invalid credentials'})
    
    return render(request, 'donorlogin.html', {'title': 'Food Donor Login'})

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
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if is_admin(user):
                login(request, user)
                return redirect('foodadmin:admindashboard') 
            else:
                return render(request, 'adminlogin.html', {'error': 'You are not an admin.'})
        else:
            return render(request, 'adminlogin.html', {'error': 'Invalid credentials'})

    return render(request, 'foodadmin/adminlogin.html', {'title': 'Admin Login'})

def admin_logout(request):
    logout(request)
    return redirect('foodadmin:adminlogin')

def is_admin(user):
    try:
        return user.profile.role == 'admin'
    except:
        return False

@login_required
@user_passes_test(is_admin)
def admindashboard(request):
    active_listings = FoodDonation.objects.filter(status='available').count()
    pending_requests = DonationRequest.objects.filter(status='pending').count()
    active_users = User.objects.filter(is_active=True).count()

    today = timezone.now().date()
    next_week = today + timedelta(days=7)
    expiring_soon = FoodDonation.objects.filter(expiry_date__range=[today, next_week]).count()

    # Pie Chart data (requested food categories)
    category_counts = DonationRequest.objects.values('donation__category').annotate(total=Count('id')).order_by('-total')
    pie_labels = [entry['donation__category'] or "Unknown" for entry in category_counts]
    pie_data = [entry['total'] for entry in category_counts]

    # Bar Chart data (monthly donations)
    monthly_donations = (
        FoodDonation.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    bar_labels = [entry['month'].strftime("%b %Y") for entry in monthly_donations]
    bar_data = [entry['total'] for entry in monthly_donations]

    # Fulfillment Rate
    total_requests = DonationRequest.objects.count()
    fulfilled_requests = DonationRequest.objects.filter(status='completed').count()
    fulfillment_rate = int((fulfilled_requests / total_requests) * 100) if total_requests > 0 else 0

    context = {
        'active_listings': active_listings,
        'pending_requests': pending_requests,
        'active_users': active_users,
        'expiring_soon': expiring_soon,
        'pie_labels': json.dumps(pie_labels),
        'pie_data': json.dumps(pie_data),
        'bar_labels': json.dumps(bar_labels),
        'bar_data': json.dumps(bar_data),
        'fulfillment_rate': fulfillment_rate,
    }
    return render(request, 'foodadmin/admindashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = Profile.objects.all().order_by('role', 'user__date_joined')
    
    context = {
        'users': users,
    }
    return render(request, 'foodadmin/adminusersmanagement.html', context)

@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    profile = get_object_or_404(Profile, id=user_id)
    
    # If user is donor, get their donations
    donations = None
    if profile.role == 'donor':
        donations = FoodDonation.objects.filter(donor=profile)
    
    # If user is recipient, get their requests
    requests = None
    if profile.role == 'recipient':
        requests = DonationRequest.objects.filter(recipient=profile)
    
    context = {
        'profile': profile,
        'donations': donations,
        'requests': requests,
    }
    return render(request, 'foodadmin/adminusersmanagements.html', context)

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.error(request, 'User profile has been deleted!')
    return redirect('foodadmin:adminusersmanagement')

@login_required
@user_passes_test(is_admin)
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    messages.error(request, 'User profile has been deactivate!')
    return redirect('foodadmin:adminusersmanagement')

@login_required
@user_passes_test(is_admin)
def edit_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        profile = get_object_or_404(Profile, user=user)

        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.username = request.POST.get('username')
        user.save()

        profile.role = request.POST.get('role')
        profile.save()
        messages.success(request, 'User profile has been edited!')
        return redirect('foodadmin:adminusersmanagement')
    
@login_required
@user_passes_test(is_admin)
def manage_donations(request):
    donations = FoodDonation.objects.all().order_by('-created_at')
    
    context = {
        'donations': donations,
    }
    return render(request, 'foodadmin/admindonations.html', context)

@login_required
@user_passes_test(is_admin)
def admindonations(request):
    donations = DonationRequest.objects.select_related('donation', 'recipient__user', 'donation__donor__user').all()
    context = {'donations': donations}
    return render(request, 'foodadmin/admindonations.html', context)


@login_required
@user_passes_test(is_admin)
def manage_requests(request):
    requests = DonationRequest.objects.all()
    
    context = {
        'requests': requests,
    }
    return render(request, 'foodadmin/adminrequests.html', context)

@login_required
@user_passes_test(is_admin)
def approve_request(request, request_id):
    donation_request = get_object_or_404(DonationRequest, id=request_id)
    donation_request.status = 'approved'
    donation_request.save()
    messages.success(request, 'Request approved successfully!')
    return redirect('foodadmin:adminrequests')

@login_required
@user_passes_test(is_admin)
def reject_request(request, request_id):
    donation_request = get_object_or_404(DonationRequest, id=request_id)
    donation_request.status = 'rejected'
    donation_request.save()
    messages.error(request, 'Request rejected successfully!')
    return redirect('foodadmin:adminrequests')


from django.contrib.auth.decorators import login_required, user_passes_test

@login_required
@user_passes_test(is_admin)
def food_listings(request):
    # You can fetch data from your model here, e.g., FoodDonation.objects.all()
    context = {
        'title': 'Manage Food Listings',
        'food_listings': FoodDonation.objects.all()  
    }
    return render(request, 'foodadmin/adminfoodlistings.html', context)

@login_required
@user_passes_test(is_admin)
def delete_food(request, donation_id):
    donation = get_object_or_404(FoodDonation, id=donation_id)
    donation.delete()
    return redirect('foodadmin:adminfoodlistings')

@login_required
@user_passes_test(is_admin)
def adminreports(request):
    report_type = request.GET.get('reportType', 'donation')
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')

    start_date = None
    end_date = None

    try:
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # INCLUDE whole end date
    except Exception:
        start_date = end_date = None

    context = {
        'report_type': report_type,
        'is_donation_report': (report_type == 'donation'),
        'is_request_report': (report_type == 'request'),
        'is_pickup_report': (report_type == 'pickup'),
    }

    # Displaying date range text
    if start_date_str and end_date_str:
        context['date_range_display'] = f"{start_date.strftime('%b %d, %Y')} - {(end_date - timedelta(days=1)).strftime('%b %d, %Y')}"
    elif start_date_str:
        context['date_range_display'] = f"Since {start_date.strftime('%b %d, %Y')}"
    elif end_date_str:
        context['date_range_display'] = f"Until {(end_date - timedelta(days=1)).strftime('%b %d, %Y')}"
    else:
        context['date_range_display'] = "Full Period"

    # Donation report
    if report_type == 'donation':
        donations = FoodDonation.objects.all()
        if start_date and end_date:
            donations = donations.filter(created_at__range=(start_date, end_date))
        elif start_date:
            donations = donations.filter(created_at__gte=start_date)
        elif end_date:
            donations = donations.filter(created_at__lte=end_date)

        total_donations = donations.count()
        total_quantity = donations.aggregate(total=Sum('quantity_amount'))['total'] or 0
        top_item = donations.values('title').annotate(count=Count('id')).order_by('-count').first()
        top_donor = Profile.objects.filter(role='donor', donations__in=donations).annotate(total=Count('donations')).order_by('-total').first()
        unique_donors = Profile.objects.filter(role='donor', donations__in=donations).distinct().count()

        context.update({
            'total_donations': total_donations,
            'total_quantity': total_quantity,
            'most_donated_item': top_item['title'] if top_item else 'N/A',
            'top_donor': top_donor.user.username if top_donor else 'N/A',
            'top_donor_count': top_donor.total if top_donor else 0,
            'total_donors': unique_donors
        })

    # Request report
    elif report_type == 'request':
        requests = DonationRequest.objects.all()
        if start_date and end_date:
            requests = requests.filter(created_at__range=(start_date, end_date))
        elif start_date:
            requests = requests.filter(created_at__gte=start_date)
        elif end_date:
            requests = requests.filter(created_at__lte=end_date)

        total_requests = requests.count()
        total_requesters = Profile.objects.filter(role='recipient', donationrequest__in=requests).distinct().count()
        top_requester = Profile.objects.filter(role='recipient', donationrequest__in=requests).annotate(total=Count('donationrequest')).order_by('-total').first()

        context.update({
            'total_requests': total_requests,
            'total_requesters': total_requesters,
            'total_requested_quantity': total_requests,  # because you don’t have actual quantity for requests
            'top_requester': top_requester.user.username if top_requester else 'N/A',
            'top_requester_count': top_requester.total if top_requester else 0
        })

    # Pickup report
    elif report_type == 'pickup':
        pickups = DonationRequest.objects.filter(status='completed')
        if start_date and end_date:
            pickups = pickups.filter(created_at__range=(start_date, end_date))
        elif start_date:
            pickups = pickups.filter(created_at__gte=start_date)
        elif end_date:
            pickups = pickups.filter(created_at__lte=end_date)

        total_pickups = pickups.count()
        donation_ids = pickups.values_list('donation_id', flat=True)
        locations = FoodDonation.objects.filter(id__in=donation_ids)

        top_location = locations.values('pickup_location').annotate(count=Count('id')).order_by('-count').first()

        context.update({
            'total_pickups': total_pickups,
            'total_locations': locations.values('pickup_location').distinct().count(),
            'total_pickup_quantity': total_pickups,  # no quantity, just count
            'top_location': top_location['pickup_location'] if top_location else 'N/A',
            'top_location_count': top_location['count'] if top_location else 0
        })

    context['now'] = timezone.now()
    return render(request, 'foodadmin/adminreports.html', context)



@login_required
@user_passes_test(is_admin)
def adminfeedback(request):
    feedbacks = Feedback.objects.select_related('user').order_by('-submitted_at')
    return render(request, 'foodadmin/adminfeedback.html', {'feedbacks': feedbacks})
