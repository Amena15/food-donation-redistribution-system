# urls.py
from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
LOGIN_URL = reverse_lazy('donorlogin')

app_name = 'fooddonor'

urlpatterns = [

    # Home URL
    path('', views.home, name='home'),

    # Admin URLs
    path('admin/', admin.site.urls),

    # Authentication URLs
    path('register/', views.register_view, name='register'),  
    path('logout/', views.logout, name='logout'),
    path('donor/login/', views.donor_login, name='donorlogin'),
    path('recipient/login', views.recipient_login, name='recipientlogin'),
    path('admin/login', views.admin_login, name='adminlogin'),
    path('choose-login/', views.choose_login, name='chooselogin'),
    
    # Dashboard URLs
    path('dashboard/', views.donor_dashboard, name='donor_dashboard'),
    path('foodlisting/', views.food_listing, name='food_listing'),
    path('add-food/', views.add_food, name='add_food'),

    # Donation listing URLs
    path('donation/create/', views.donation_create, name='donation_create'),
    path('edit/<int:pk>/', views.donation_edit, name='donation_edit'),
    path('delete/<int:pk>/', views.donation_delete, name='donation_delete'),
    path('foodlisting/edit/<int:pk>/', views.edit_food, name='edit_food'),
    path('foodlisting/delete/<int:pk>/', views.delete_food, name='delete_food'),
    path('pickup-schedule/', views.pickup_schedule, name='pickup_schedule'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/delete/', views.delete_notification, name='delete_notification'),
    path('settings/toggle-email-notifications/', views.toggle_email_notifications, name='toggle_email_notifications'),
    path('notifications/toggle-sms/', views.toggle_sms_notifications, name='toggle_sms_notifications'),
    path('notifications/toggle-push/', views.toggle_push_notifications, name='toggle_push_notifications'),

    path('donation-list/', views.donation_list, name='donation_list'),
    path('donation-detail/<int:pk>/', views.donation_detail, name='donation_detail'),
    path('donation-status/<int:pk>/status/<str:status>/', views.update_request_status, name='update_request_status'),
    path('donation-history/', views.donation_history, name='donation_history'),
    

    # Request management URLs
    path('requests/', views.request_list, name='request_list'),
    path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    path('requests/<int:pk>/status/<str:status>/', views.update_request_status, name='update_request_status'),

    path('donation-request/<int:pk>/', views.request_donation, name='request_donation'),

    path('settings/', views.settings, name='settings'),

    # Feedback URL
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
]
