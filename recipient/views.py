from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RecipientSignUpForm  # Assuming you've created this form
from django.contrib.auth import login, authenticate
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as django_logout 
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


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
            return redirect(reverse('donorlogin'))
        elif user_type == 'foodrecipient':
            return redirect(reverse('recipientlogin'))
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Log the user in
            login(request, user)
            return redirect('recipient:recipient_dashboard')  # Redirect to the recipient dashboard
        else:
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

def register_view(request):
    if request.method == 'POST':
        form = RecipientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log the user in
            login(request, user)
            
            # Send welcome notification
            notification_manager = NotificationManager()
            notification_manager.send_notification(
                user,
                "Welcome to our food donation system! Your recipient account has been created successfully."
            )
            
            messages.success(request, 'Your recipient account was created successfully!')
            return redirect('recipient:recipient_dashboard')
        
        else:
            # Add error messages for each field
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = RecipientSignUpForm()
    
    return render(request, 'recipientregister.html', {'form': form})

@login_required
def recipient_dashboard(request):
    return render(request, 'recipientdashboard.html')

def recipient_logout(request):
    """
    Log out the user and redirect to the home page of fooddonor.
    """
    logout(request)
    return redirect('fooddonor:home')  # Redirect to the homepage of the fooddonor app

def home(request):
    return render(request, 'fooddonor/home.html')


class NotificationManager:
    def send_notification(self, user, message):
        print(f"[NOTIFICATION] To: {user.username} — {message}")
        # Later: send email or SMS here
