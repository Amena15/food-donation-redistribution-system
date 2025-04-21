from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RecipientRegistrationForm  # Assuming you've created this form
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
            return redirect('foodrecipient:recipient_dashboard')  # Redirect to the recipient dashboard
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

def recipient_register(request):
    if request.method == 'POST':
        print("POST request received")
        form = RecipientRegistrationForm(request.POST)
        if form.is_valid():
            print("Form is valid")
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()

            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                print("User authenticated")
                login(request, user)
                messages.success(request, "Registration successful!")
                return redirect('foodrecipient:recipient_dashboard')
            else:
                print("Authentication failed")
                messages.error(request, "Authentication failed after registration!")
                return redirect('foodrecipient:recipientregister')
        else:
            print("Form errors:", form.errors)
            messages.error(request, "Please correct the errors below.")
            return render(request, 'recipientregister.html', {'form': form})
    else:
        form = RecipientRegistrationForm()
    return render(request, 'recipientregister.html', {'form': form})


@login_required
def recipient_dashboard(request):
    return render(request, 'recipientdashboard.html', {'title': 'My Dashboard'})

def recipient_logout(request):
    """
    Log out the user and redirect to the home page of fooddonor.
    """
    logout(request)
    return redirect('fooddonor:home')  # Redirect to the homepage of the fooddonor app

def home(request):
    return render(request, 'fooddonor/home.html')
