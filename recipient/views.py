from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.http import Http404, JsonResponse
import json
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.contrib.auth.models import User
from .matching import MatchingService
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from .models import PickupSchedule, DonationRequest, Notification
from .forms import ConfirmPickupForm
from django.views.generic import DetailView
from django.views.generic.edit import FormView


from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .models import (
    RecipientProfile,
    RecipientPreference,
    DonationRequest,
    PickupSchedule,
    WishlistItem,
    Notification
)
from .forms import (
    RecipientSignUpForm,
    RecipientProfileForm,
    RecipientPreferenceForm,
    DonationRequestForm,
    RequestCancellationForm,
    PickupScheduleForm,
    DonationFeedbackForm,
    WishlistItemForm
)
from fooddonor.models import FoodDonation, UserSettings
from django.contrib.auth.views import (
    PasswordResetView, 
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.contrib.auth.forms import PasswordResetForm

def home(request):
    return render(request, 'home.html')

def recipient_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Find user by email
        try:
            user = User.objects.get(email=email)
            # Authenticate with the username (not email)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                # Check if user has recipient profile
                if hasattr(user, 'recipient_profile'):
                    login(request, user)
                    return redirect('recipient:dashboard')
                else:
                    messages.error(request, "This account is not registered as a recipient.")
            else:
                messages.error(request, "Invalid password.")
        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")
    
    return render(request, 'recipientlogin.html')

def recipient_logout(request):
    logout(request)
    return redirect('recipient:home')

def register_view(request):
    if request.method == 'POST':
        form = RecipientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Your recipient account was created successfully!')
            return redirect('recipient:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = RecipientSignUpForm()
    
    return render(request, 'recipientregister.html', {'form': form})

@login_required
def dashboard(request):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    
    total_requests = DonationRequest.objects.filter(recipient=recipient).count()
    pending_requests = DonationRequest.objects.filter(
        recipient=recipient,
        status='pending'
    ).count()
    approved_requests = DonationRequest.objects.filter(
        recipient=recipient,
        status='approved'
    ).count()
    completed_requests = DonationRequest.objects.filter(
        recipient=recipient,
        status='completed'
    ).count()
    
    upcoming_pickups = PickupSchedule.objects.filter(
        request__recipient=recipient,
        request__status='approved',
        scheduled_time__gte=timezone.now(),
        is_completed=False
    ).order_by('scheduled_time')[:5]
    
    recent_notifications = Notification.objects.filter(
        recipient=recipient
    ).order_by('-created_at')[:5]
    
    context = {
        'recipient': recipient,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'completed_requests': completed_requests,
        'upcoming_pickups': upcoming_pickups,
        'recent_notifications': recent_notifications,

    }
    
    return render(request, 'recipientdashboard.html', context)

@login_required
def edit_profile(request):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    
    if request.method == 'POST':
        form = RecipientProfileForm(request.POST, instance=recipient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('recipient:profile')
    else:
        form = RecipientProfileForm(instance=recipient)
    
    return render(request, 'profile.html', {'form': form})

@login_required
def edit_preferences(request):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    preferences, created = RecipientPreference.objects.get_or_create(recipient=recipient)
    
    if request.method == 'POST':
        form = RecipientPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated successfully!')
            return redirect('recipient:preferences')
    else:
        form = RecipientPreferenceForm(instance=preferences)
    
    return render(request, 'edit_preferences.html', {'form': form})

@login_required
def browse_donations(request):
    """
    View for recipients to browse available food donations with intelligent matching.
    Uses MatchingService to prioritize donations based on recipient preferences.
    """
    # Check if user has a recipient profile
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You need a recipient profile to browse donations.")
        return redirect('recipient:profile_setup')
    
    recipient = request.user.recipient_profile
    
    # Get filter parameters from request
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    sort_by = request.GET.get('sort', 'match_score')
    
    # Get all available donations
    available_donations = FoodDonation.objects.filter(
        status='available',
        expiry_date__gte=timezone.now().date()
    ).select_related('donor__user')
    
    # Apply category filter if specified
    if category_filter:
        available_donations = available_donations.filter(category=category_filter)
    
    # Apply search filtering if search query exists
    if search_query:
        available_donations = available_donations.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query))
    
    # Initialize matching service
    matching_service = MatchingService()
    
    # Calculate match scores and distances for each donation
    scored_donations = []
    for donation in available_donations:
        score = matching_service.calculate_match_score(donation, recipient)
        distance_km = matching_service.calculate_distance(donation, recipient)
        distance_miles = round(distance_km * 0.621371, 1) if distance_km != float('inf') else 'N/A'
        
        scored_donations.append({
            'object': donation,
            'match_score': round(score, 1),
            'distance': distance_miles,
            'expiration_date': donation.expiry_date,
            'pickup_time_window': donation.donor.preferred_pickup_time,
            'category': donation.get_category_display(),
            'quantity': donation.quantity_amount,
            'unit': donation.get_quantity_unit_display()
        })
    
    # Sorting logic
    if sort_by == 'expiry':
        scored_donations.sort(key=lambda x: x['expiration_date'])
    elif sort_by == 'distance':
        scored_donations.sort(key=lambda x: x['distance'] if x['distance'] != 'N/A' else float('inf'))
    elif sort_by == 'newest':
        scored_donations.sort(key=lambda x: x['object'].created_at, reverse=True)
    else:  # Default sort by match_score
        scored_donations.sort(key=lambda x: x['match_score'], reverse=True)
    
    # Paginate results
    paginator = Paginator(scored_donations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'sort_by': sort_by,
        'food_item_categories': FoodDonation.CATEGORY_CHOICES,
        'has_preferences': hasattr(recipient, 'preferences'),
        'current_date': timezone.now().date(),
    }
    
    return render(request, 'browse_food.html', context)

# recipient/views.py
@login_required
def donation_detail(request, donation_id):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    donation = get_object_or_404(
        FoodDonation.objects.select_related('donor__user'),
        id=donation_id,
        status='available'
    )
    
    # Get the full request object instead of just checking existence
    existing_request = DonationRequest.objects.filter(
        recipient=recipient,
        donation=donation
    ).first()  # This returns None if no request exists
    
    request_form = None
    if not existing_request:
        request_form = DonationRequestForm(donation=donation, recipient=recipient)
    
    context = {
        'donation': donation,
        'existing_request': existing_request,  # Now either None or a full request object
        'request_form': request_form,
    }
    return render(request, 'donation_detail.html', context)

@login_required
def request_donation(request, donation_id):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    donation = get_object_or_404(FoodDonation, id=donation_id, status='available')
    
    existing_request = DonationRequest.objects.filter(
        recipient=recipient,
        donation=donation
    ).exists()
    
    if existing_request:
        messages.warning(request, "You've already requested this donation.")
        return redirect('recipient:donation_detail', donation_id=donation_id)
    
    if request.method == 'POST':
        form = DonationRequestForm(request.POST, donation=donation, recipient=recipient)
        if form.is_valid():
            donation_request = form.save(commit=False)
            donation_request.recipient = recipient
            donation_request.donation = donation
            donation_request.status = 'pending'
            donation_request.save()
            
            messages.success(request, "Your request has been submitted successfully!")
            return redirect('recipient:my_requests')
    else:
        form = DonationRequestForm(donation=donation, recipient=recipient)
    
    context = {
        'donation': donation,
        'form': form,
    }
    
    return render(request, 'request_donation.html', context)

@login_required
def my_requests(request):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    status_filter = request.GET.get('status', None)
    
    requests = DonationRequest.objects.filter(recipient=recipient)
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    requests = requests.order_by('-requested_at')
    
    # Prepare status choices with counts
    status_choices_with_counts = []
    total_count = DonationRequest.objects.filter(recipient=recipient).count()
    
    for status in DonationRequest.STATUS_CHOICES:
        count = DonationRequest.objects.filter(
            recipient=recipient,
            status=status[0]
        ).count()
        status_choices_with_counts.append({
            'value': status[0],
            'display': status[1],
            'count': count
        })
    
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'requests': page_obj,
        'status_filter': status_filter,
        'status_choices_with_counts': status_choices_with_counts,
        'total_count': total_count,
    }
    
    return render(request, 'track_requests.html', context)

@login_required
def request_detail(request, request_id):
    """View for recipient to see details of a specific request"""
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You need a recipient profile to view requests.")
        return redirect('recipient:profile_setup')
    
    try:
        donation_request = DonationRequest.objects.select_related(
            'donation', 
            'donation__donor__user'
        ).get(
            id=request_id,
            recipient=request.user.recipient_profile
        )
    except DonationRequest.DoesNotExist:
        messages.error(request, "The requested donation request doesn't exist or you don't have permission to view it.")
        return redirect('recipient:my_requests')  # Redirect to requests list
    
    context = {
        'donation_request': donation_request,  # Changed from 'request' to avoid conflict
    }
    return render(request, 'request_detail.html', context)

@login_required
def cancel_request(request, request_id):
    donation_request = get_object_or_404(
        DonationRequest.objects.select_related('donation', 'donation__donor__user'),
        id=request_id,
        recipient=request.user.recipient_profile
    )
    
    # Only allow cancellation of pending requests
    if donation_request.status != 'pending':
        messages.error(request, "Only pending requests can be cancelled.")
        return redirect('recipient:request_detail', request_id=request_id)
    
    if request.method == 'POST':
        form = RequestCancellationForm(request.POST, instance=donation_request)
        if form.is_valid():
            # Double-check the confirmation
            if request.POST.get('confirm_cancellation') == 'true':
                donation_request = form.save(commit=False)
                donation_request.status = 'cancelled'
                donation_request.cancelled_at = timezone.now()
                donation_request.save()
                
                # Send notification to donor
                Notification.objects.create(
                    recipient=donation_request.donation.donor,
                    message=f"Request #{donation_request.id} has been cancelled by the recipient.",
                    related_request=donation_request,
                    notification_type='request_cancelled'
                )
                
                messages.success(request, "Your request has been cancelled.")
                return redirect('recipient:my_requests')
            else:
                messages.error(request, "Cancellation not confirmed.")
    else:
        form = RequestCancellationForm(instance=donation_request)
    
    return render(request, 'cancel_request.html', {
        'donation_request': donation_request,
        'form': form
    })

@login_required
def submit_feedback(request, request_id):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    donation_request = get_object_or_404(
        DonationRequest.objects.select_related('donation__donor__user'),
        id=request_id, 
        recipient=recipient,
        status='completed'
    )
    
    # Check if feedback already exists
    if donation_request.feedback:
        messages.warning(request, "You've already submitted feedback for this request.")
        return redirect('recipient:request_detail', request_id=request_id)
    
    if request.method == 'POST':
        form = DonationFeedbackForm(request.POST, instance=donation_request)
        if form.is_valid():
            # Save feedback and update timestamp
            donation_request = form.save(commit=False)
            donation_request.feedback_submitted_at = timezone.now()
            donation_request.save()
            
            # Create notification for donor
            Notification.objects.create(
                recipient=donation_request.donation.donor,
                message=f"New feedback received for your donation '{donation_request.donation.title}'",
                related_request=donation_request,
                notification_type='feedback_received'
            )
            
            messages.success(request, "Thank you for your feedback!")
            return redirect('recipient:request_detail', request_id=request_id)
    else:
        form = DonationFeedbackForm(instance=donation_request)
    
    context = {
        'request': donation_request,
        'form': form,
        'donation': donation_request.donation,
        'donor': donation_request.donation.donor.user
    }
    
    return render(request, 'submit_feedback.html', context)

@method_decorator(login_required, name='dispatch')
class PickupDetailView(DetailView):
    model = PickupSchedule
    template_name = 'pickup_detail.html'
    context_object_name = 'pickup'
    pk_url_kwarg = 'pickup_id'  # Add this line to specify the URL kwarg

    def get_queryset(self):
        return super().get_queryset().select_related(
            'request__donation__donor__user',
            'request__recipient__user'
        ).filter(
            request__recipient=self.request.user.recipient_profile
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_confirm'] = (
            not self.object.is_completed and 
            self.object.request.status == 'approved'
        )
        return context

@method_decorator(login_required, name='dispatch')
class ConfirmPickupView(FormView):
    template_name = 'recipient/confirm_pickup.html'
    form_class = ConfirmPickupForm

    def dispatch(self, request, *args, **kwargs):
        self.pickup = get_object_or_404(
            PickupSchedule.objects.select_related('request__donation__donor__user'),
            pk=self.kwargs['pickup_id'],
            request__recipient=request.user.recipient_profile,
            is_completed=False,
            request__status='approved'
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.pickup.is_completed = True
        self.pickup.completed_at = timezone.now()
        self.pickup.save()

        self.pickup.request.status = 'completed'
        self.pickup.request.save()

        # Create notification for donor
        Notification.objects.create(
            recipient=self.pickup.request.donation.donor,
            message=f"Pickup for request #{self.pickup.request.id} has been completed.",
            related_request=self.pickup.request,
            notification_type='pickup_completed'
        )

        messages.success(self.request, "Pickup confirmed successfully!")
        return redirect('recipient:pickup_detail', pickup_id=self.pickup.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pickup'] = self.pickup
        return context
    
@login_required
def wishlist(request):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    wishlist_items = WishlistItem.objects.filter(recipient=recipient).order_by('-priority', 'name')
    
    context = {
        'wishlist_items': wishlist_items,
    }
    return render(request, 'wishlist.html', context)

@login_required
def add_wishlist_item(request):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    
    if request.method == 'POST':
        form = WishlistItemForm(request.POST)
        if form.is_valid():
            wishlist_item = form.save(commit=False)
            wishlist_item.recipient = recipient
            wishlist_item.save()
            messages.success(request, "Item added to your wishlist!")
            return redirect('recipient:wishlist')
    else:
        form = WishlistItemForm()
    
    context = {
        'form': form,
    }
    return render(request, 'add_wishlist_item.html', context)

@login_required
def edit_wishlist_item(request, item_id):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, recipient=recipient)
    
    if request.method == 'POST':
        form = WishlistItemForm(request.POST, instance=wishlist_item)
        if form.is_valid():
            form.save()
            messages.success(request, "Wishlist item updated successfully!")
            return redirect('recipient:wishlist')
    else:
        form = WishlistItemForm(instance=wishlist_item)
    
    context = {
        'form': form,
        'item': wishlist_item,
    }
    return render(request, 'edit_wishlist_item.html', context)

@login_required
def delete_wishlist_item(request, item_id):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    wishlist_item = get_object_or_404(WishlistItem, id=item_id, recipient=recipient)
    
    if request.method == 'POST':
        wishlist_item.delete()
        messages.success(request, "Wishlist item deleted successfully!")
        return redirect('recipient:wishlist')
    
    context = {
        'item': wishlist_item,
    }
    return render(request, 'delete_wishlist_item.html', context)

from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.views.decorators.http import require_http_methods

# Notification Views
@login_required
def notification_list(request):
    """View all notifications with filtering options"""
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    notifications = Notification.objects.filter(recipient=recipient)
    
    # Filtering
    notification_type = request.GET.get('type', 'all')
    if notification_type != 'all':
        notifications = notifications.filter(notification_type=notification_type)
    
    # Mark all as read if viewing notifications
    if request.GET.get('mark_read', 'false') == 'true':
        notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, "All notifications marked as read!")
    
    # Pagination
    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Counts for filter tabs
    counts = {
        'all': Notification.objects.filter(recipient=recipient).count(),
        'unread': Notification.objects.filter(recipient=recipient, is_read=False).count(),
        'request': Notification.objects.filter(
            recipient=recipient,
            notification_type='request_update'
        ).count(),
        'match': Notification.objects.filter(
            recipient=recipient,
            notification_type='donation_match'
        ).count(),
        'system': Notification.objects.filter(
            recipient=recipient,
            notification_type='system'
        ).count(),
    }
    
    context = {
        'notifications': page_obj,
        'counts': counts,
        'current_filter': notification_type,
        'notification_types': {
            'request_update': 'Request Updates',
            'donation_match': 'Donation Matches',
            'system': 'System Messages'
        }
    }
    return render(request, 'notifications_list.html', context)

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, pk):
    """Mark a single notification as read (AJAX)"""
    if not hasattr(request.user, 'recipient_profile'):
        return JsonResponse({'status': 'error'}, status=403)
    
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user.recipient_profile
    )
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
@require_http_methods(["POST"])
def delete_notification(request, pk):
    """Delete a notification (AJAX)"""
    if not hasattr(request.user, 'recipient_profile'):
        return JsonResponse({'status': 'error'}, status=403)
    
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user.recipient_profile
    )
    notification.delete()
    return JsonResponse({'status': 'success'})

# Settings Views
@login_required
def notification_settings(request):
    """Manage notification preferences"""
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    
    # Get or create settings
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update notification preferences
        settings.receive_email_notifications = request.POST.get('email_notifications') == 'on'
        settings.receive_sms_notifications = request.POST.get('sms_notifications') == 'on'
        settings.notify_request_updates = request.POST.get('request_updates') == 'on'
        settings.notify_matches = request.POST.get('donation_matches') == 'on'
        settings.notify_system_messages = request.POST.get('system_messages') == 'on'
        settings.save()
        
        messages.success(request, "Notification preferences updated!")
        return redirect('recipient:notification_settings')
    
    context = {
        'settings': settings,
        'notification_types': {
            'request_update': 'Request Status Updates',
            'donation_match': 'New Donation Matches',
            'system': 'System Messages'
        }
    }
    return render(request, 'settings_notifications.html', context)

@login_required
def account_settings(request):
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    user = request.user
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            # Update profile info
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            
            # Update recipient profile fields
            recipient.phone_number = request.POST.get('phone_number', '')
            recipient.address = request.POST.get('address', '')
            recipient.city = request.POST.get('city', '')
            recipient.state = request.POST.get('state', '')
            recipient.postal_code = request.POST.get('postal_code', '')
            recipient.save()
            
            messages.success(request, "Profile updated successfully!")
        
        elif action == 'change_password':
            # Change password logic remains the same
            ...
        
        return redirect('recipient:account_settings')
    
    context = {
        'user': user,
        'recipient': recipient
    }
    return render(request, 'settings_account.html', context)
@require_POST
@csrf_exempt
def set_geolocation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Process and save location data
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def pickups_list(request):
    """
    View to display all upcoming and past pickup schedules for the recipient.
    Uses pagination and filtering for better organization.
    """
    if not hasattr(request.user, 'recipient_profile'):
        messages.error(request, "You don't have a recipient profile.")
        return redirect('recipient:home')
    
    recipient = request.user.recipient_profile
    
    # Get filter parameter from request
    filter_type = request.GET.get('filter', 'upcoming')
    
    # Base queryset
    pickups = PickupSchedule.objects.filter(
        request__recipient=recipient
    ).select_related('request', 'request__donation').order_by('-scheduled_time')
    
    # Apply filters
    if filter_type == 'upcoming':
        pickups = pickups.filter(
            scheduled_time__gte=timezone.now(),
            is_completed=False
        )
    elif filter_type == 'past':
        pickups = pickups.filter(
            Q(scheduled_time__lt=timezone.now()) | Q(is_completed=True)
        )
    elif filter_type == 'completed':
        pickups = pickups.filter(is_completed=True)
    elif filter_type == 'pending':
        pickups = pickups.filter(
            scheduled_time__gte=timezone.now(),
            is_completed=False,
            request__status='approved'
        )
    
    # Counts for filter tabs
    counts = {
        'all': PickupSchedule.objects.filter(request__recipient=recipient).count(),
        'upcoming': PickupSchedule.objects.filter(
            request__recipient=recipient,
            scheduled_time__gte=timezone.now(),
            is_completed=False
        ).count(),
        'past': PickupSchedule.objects.filter(
            Q(scheduled_time__lt=timezone.now()) | Q(is_completed=True),
            request__recipient=recipient
        ).count(),
        'completed': PickupSchedule.objects.filter(
            request__recipient=recipient,
            is_completed=True
        ).count(),
        'pending': PickupSchedule.objects.filter(
            request__recipient=recipient,
            scheduled_time__gte=timezone.now(),
            is_completed=False,
            request__status='approved'
        ).count(),
    }
    
    # Pagination
    paginator = Paginator(pickups, 10)  # Show 10 pickups per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'pickups': page_obj,
        'filter_type': filter_type,
        'counts': counts,
    }
    
    return render(request, 'pickup_list.html', context)


class RecipientPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    form_class = PasswordResetForm
    
    def get_queryset(self):
        # Only allow password reset for users with recipient profiles
        return User.objects.filter(recipient_profile__isnull=False)