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
    path('edit/<int:pk>/', views.edit_food, name='edit_food'),
    path('delete/<int:pk>/', views.delete_food, name='delete_food'),
    path('pickup-schedule/', views.pickup_schedule, name='pickup_schedule'),
    path('notifications/', views.notifications, name='notifications'),
    
    # Request management URLs
    #path('requests/', views.request_list, name='request_list'),
    #path('requests/<int:pk>/', views.request_detail, name='request_detail'),
    #path('requests/<int:pk>/status/<str:status>/', views.update_request_status, name='update_request_status'),
    
    
]