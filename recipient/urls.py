from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import PickupDetailView

app_name = 'recipient'

urlpatterns = [
    # Authentication URLs
    path('', views.home, name='home'),
    path('login/', views.recipient_login, name='login'),
    path('recipient/login', views.recipient_login, name='recipientlogin'),
    path('logout/', views.recipient_logout, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Dashboard and Profile URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.edit_profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('preferences/', views.edit_preferences, name='preferences'),
    
    # Donation Browsing and Request URLs
    path('donations/', views.browse_donations, name='browse_donations'),
    path('donations/<int:donation_id>/', views.donation_detail, name='donation_detail'),
    path('donations/<int:donation_id>/request/', views.request_donation, name='request_donation'),
    
    # Request Management URLs
    path('requests/', views.my_requests, name='my_requests'),
    path('requests/<int:request_id>/', views.request_detail, name='request_detail'),
    path('requests/<int:request_id>/cancel/', views.cancel_request, name='cancel_request'),
    path('requests/<int:request_id>/feedback/', views.submit_feedback, name='submit_feedback'),
     # Pickup Detail View
    path('pickups/<int:pickup_id>/', PickupDetailView.as_view(), name='pickup_detail'),
    path('pickups/<int:pk>/confirm/', views.ConfirmPickupView.as_view(), name='confirm_pickup'),

    
    # Wishlist URLs
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/', views.add_wishlist_item, name='add_wishlist_item'),
    path('wishlist/<int:item_id>/edit/', views.edit_wishlist_item, name='edit_wishlist_item'),
    path('wishlist/<int:item_id>/delete/', views.delete_wishlist_item, name='delete_wishlist_item'),
    
    # Notification URLs
    path('notifications/', views.notification_list, name='notification_list'),
    
    # Keep your other URL patterns
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/<int:pk>/delete/', views.delete_notification, name='delete_notification'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    path('settings/account/', views.account_settings, name='account_settings'),

    path('set-geolocation/', views.set_geolocation, name='set_geolocation'),
    path('pickups/', views.pickups_list, name='pickups_list'),

    # Password reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='recipient/password_reset.html',
             email_template_name='recipient/password_reset_email.html',
             subject_template_name='recipient/password_reset_subject.txt'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='recipient/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='recipient/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='recipient/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    
]