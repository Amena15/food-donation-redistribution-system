from django.urls import path
from . import views

app_name = 'foodadmin'

urlpatterns = [
    path('login/', views.admin_login, name='adminlogin'),
    path('dashboard/', views.admindashboard, name='admindashboard'),

    path('users/', views.manage_users, name='adminusersmanagement'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/deactivate/<int:user_id>/', views.deactivate_user, name='deactivate_user'),
    path('users/edit/', views.edit_user, name='edit_user'),

    path('donations/', views.admindonations, name='admindonations'),

    path('requests/', views.manage_requests, name='adminrequests'),
    path('requests/approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('requests/reject/<int:request_id>/', views.reject_request, name='reject_request'),

    path('analytics/', views.adminreports, name='adminreports'),
    path('logout/', views.admin_logout, name='admin_logout'),

    path('foodlistings/', views.food_listings, name='adminfoodlistings'),
    path('foodlistings/delete/<int:donation_id>/', views.delete_food, name='delete_food'),

    path('feedback/', views.adminfeedback, name='adminfeedback'),

]
