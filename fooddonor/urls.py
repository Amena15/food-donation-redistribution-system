# urls.py
from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

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
    #path('recipient/', views.recipient_dashboard, name='recipient_dashboard'),
    #path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Donation Management URLs
    #path('donations/request/<int:donation_id>/', views.request_donation, name='request_donation'),
    #path('donations/manage/<int:donation_id>/', views.manage_requests, name='manage_requests'),
    #path('requests/approve/<int:request_id>/', views.approve_request, name='approve_request'),

    # Donation listing URLs
    #path('donations/', views.donation_list, name='donation_list'),
    #path('donations/<int:pk>/', views.donation_detail, name='donation_detail'),
    #path('donations/create/', views.donation_create, name='donation_create'),
    #path('donations/<int:pk>/edit/', views.donation_edit, name='donation_edit'),
    #path('donations/<int:pk>/delete/', views.donation_delete, name='donation_delete'),
    
    # Request management URLs
    #path('requests/', views.request_list, name='request_list'),
    #path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    #path('requests/<int:pk>/status/<str:status>/', views.update_request_status, name='update_request_status'),
    
]