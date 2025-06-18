# foodrecipient/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from django.urls import include

app_name = 'recipient'

urlpatterns = [
    # Dashboard and main screens
    path('dashboard/', views.recipient_dashboard, name='recipient_dashboard'),
    #path('profile/', views.recipient_profile, name='profile'),
    #path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('donor/login/', views.donor_login, name='donorlogin'),
    path('recipient/login', views.recipient_login, name='recipientlogin'),
    path('admin/login', views.admin_login, name='adminlogin'),
    path('register/', views.register_view, name='recipientregister'),  # Add the URL for registration
    path('logout/', views.recipient_logout, name='recipient_logout'),

    # Add other URL patterns for your dashboard, etc.
    

    # Donations browsing and requesting
    #path('donations/', views.available_donations, name='available_donations'),
    #path('donations/<int:donation_id>/', views.donation_detail, name='donation_detail'),
    #path('donations/<int:donation_id>/request/', views.request_donation, name='request_donation'),
    
    # Managing requests
    #path('my-requests/', views.my_requests, name='my_requests'),
    #path('my-requests/<int:request_id>/', views.request_detail, name='request_detail'),
    #path('my-requests/<int:request_id>/cancel/', views.cancel_request, name='cancel_request'),
    
    # Received donations
    #path('received-donations/', views.received_donations, name='received_donations'),
    #path('received-donations/<int:donation_id>/confirm/', views.confirm_received, name='confirm_received'),
    
    # Search and filtering
    #path('search/', views.search_donations, name='search_donations'),
    
    # Notifications
    #path('notifications/', views.notifications, name='notifications'),
    #path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    
    # Registration and authentication
    #path('register/', views.recipient_register, name='register'),
    #path('preferences/', views.set_preferences, name='preferences'),
]