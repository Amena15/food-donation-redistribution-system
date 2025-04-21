# In foodadmin/urls.py
from django.urls import path
from . import views

app_name = 'foodadmin'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('users/', views.manage_users, name='manage_users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('donations/', views.manage_donations, name='manage_donations'),
    path('requests/', views.manage_requests, name='manage_requests'),
    path('requests/approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('requests/reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('analytics/', views.analytics, name='analytics'),
    path('donor/login/', views.donor_login, name='donorlogin'),
    path('recipient/login', views.recipient_login, name='recipientlogin'),
    path('admin/login', views.admin_login, name='adminlogin'),


]