from django.urls import path
from . import views

app_name = 'foodadmin'

urlpatterns = [
    path('login/', views.admin_login, name='adminlogin'),
    path('dashboard/', views.admin_dashboard, name='admindashboard'),
    path('users/', views.manage_users, name='adminusersmanagement'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('donations/', views.manage_donations, name='admindonations'),
    path('requests/', views.manage_requests, name='adminrequests'),
    path('requests/approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('requests/reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('analytics/', views.analytics, name='analytics'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('foodlistings/', views.food_listings, name='adminfoodlistings'),

]
