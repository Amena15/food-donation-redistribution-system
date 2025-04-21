# In foodadmin/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from fooddonor.models import Profile, FoodDonation, DonationRequest
from .models import AdminActivity



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
            return redirect(reverse('admin_login'))
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


# Helper function to check if user is admin
def is_admin(user):
    try:
        return user.profile.role == 'admin'
    except:
        return False

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get statistics for dashboard
    total_donors = Profile.objects.filter(role='donor').count()
    total_recipients = Profile.objects.filter(role='recipient').count()
    active_donations = FoodDonation.objects.filter(status='available').count()
    pending_requests = DonationRequest.objects.filter(status='pending').count()
    
    # Recent activity
    recent_activity = AdminActivity.objects.order_by('-created_at')[:10]
    
    context = {
        'total_donors': total_donors,
        'total_recipients': total_recipients,
        'active_donations': active_donations,
        'pending_requests': pending_requests,
        'recent_activity': recent_activity,
    }
    return render(request, 'foodadmin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_users(request):
    users = Profile.objects.all().order_by('role', 'user__date_joined')
    
    context = {
        'users': users,
    }
    return render(request, 'foodadmin/manage_users.html', context)

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
    return render(request, 'foodadmin/user_detail.html', context)

@login_required
@user_passes_test(is_admin)
def manage_donations(request):
    donations = FoodDonation.objects.all().order_by('-created_at')
    
    context = {
        'donations': donations,
    }
    return render(request, 'foodadmin/manage_donations.html', context)

@login_required
@user_passes_test(is_admin)
def manage_requests(request):
    requests = DonationRequest.objects.filter(status='pending')
    
    context = {
        'requests': requests,
    }
    return render(request, 'foodadmin/manage_requests.html', context)

@login_required
@user_passes_test(is_admin)
def approve_request(request, request_id):
    donation_request = get_object_or_404(DonationRequest, id=request_id)
    
    if request.method == 'POST':
        # Update request status
        donation_request.status = 'approved'
        donation_request.save()
        
        # Update donation status
        donation = donation_request.donation
        donation.status = 'claimed'
        donation.save()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user.profile,
            action='approve_donation',
            description=f"Approved request for {donation.title}",
            target_user=donation_request.recipient,
            target_donation=donation
        )
        
        messages.success(request, 'Request approved successfully!')
        return redirect('foodadmin:manage_requests')
    
    context = {
        'donation_request': donation_request,
    }
    return render(request, 'foodadmin/confirm_approve.html', context)

@login_required
@user_passes_test(is_admin)
def reject_request(request, request_id):
    donation_request = get_object_or_404(DonationRequest, id=request_id)
    
    if request.method == 'POST':
        # Update request status
        donation_request.status = 'rejected'
        donation_request.save()
        
        # Log admin activity
        AdminActivity.objects.create(
            admin=request.user.profile,
            action='reject_donation',
            description=f"Rejected request for {donation_request.donation.title}",
            target_user=donation_request.recipient,
            target_donation=donation_request.donation
        )
        
        messages.success(request, 'Request rejected successfully!')
        return redirect('foodadmin:manage_requests')
    
    context = {
        'donation_request': donation_request,
    }
    return render(request, 'foodadmin/confirm_reject.html', context)

@login_required
@user_passes_test(is_admin)
def analytics(request):
    # Add analytics data gathering here
    
    context = {
        # Add analytics data to context
    }
    return render(request, 'foodadmin/analytics.html', context)