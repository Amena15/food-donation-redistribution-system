from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile, FoodDonation, DonationRequest
from datetime import date, timedelta

class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='1234567890',
            role='donor',
            location='Test Location'
        )
    
    def test_profile_creation(self):
        self.assertEqual(self.profile.user.username, 'testuser')
        self.assertEqual(self.profile.role, 'donor')
        self.assertEqual(str(self.profile), 'testuser - Food Donor')

class FoodDonationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='donor', password='12345')
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='1234567890',
            role='donor',
            location='Test Location'
        )
        self.donation = FoodDonation.objects.create(
            donor=self.profile,
            title='Test Donation',
            description='Test Description',
            quantity='5 kg',
            expiry_date=date.today() + timedelta(days=5),
            pickup_location='Test Pickup',
            status='available'
        )
    
    def test_donation_creation(self):
        self.assertEqual(self.donation.title, 'Test Donation')
        self.assertEqual(self.donation.status, 'available')
        self.assertEqual(str(self.donation), 'Test Donation by donor')

class UserSignupTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
    
    def test_signup_donor(self):
        response = self.client.post(self.signup_url, {
            'username': 'newdonor',
            'email': 'donor@test.com',
            'password1': 'securepassword123',
            'password2': 'securepassword123',
            'phone_number': '1234567890',
            'role': 'donor',
            'location': 'Test Location'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirects on success
        self.assertTrue(User.objects.filter(username='newdonor').exists())
        self.assertTrue(Profile.objects.filter(user__username='newdonor', role='donor').exists())
    
    def test_signup_recipient(self):
        response = self.client.post(self.signup_url, {
            'username': 'newrecipient',
            'email': 'recipient@test.com',
            'password1': 'securepassword123',
            'password2': 'securepassword123',
            'phone_number': '0987654321',
            'role': 'recipient',
            'needs_description': 'Test needs description'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirects on success
        self.assertTrue(User.objects.filter(username='newrecipient').exists())
        self.assertTrue(Profile.objects.filter(user__username='newrecipient', role='recipient').exists())

class DonationProcessTest(TestCase):
    def setUp(self):
        # Create donor user
        self.donor = User.objects.create_user(username='donor', password='12345')
        self.donor_profile = Profile.objects.create(
            user=self.donor,
            phone_number='1234567890',
            role='donor',
            location='Donor Location'
        )
        
        # Create recipient user
        self.recipient = User.objects.create_user(username='recipient', password='12345')
        self.recipient_profile = Profile.objects.create(
            user=self.recipient,
            phone_number='0987654321',
            role='recipient',
            needs_description='Need food assistance'
        )
        
        # Create donation
        self.donation = FoodDonation.objects.create(
            donor=self.donor_profile,
            title='Test Food',
            description='Fresh vegetables',
            quantity='10 kg',
            expiry_date=date.today() + timedelta(days=3),
            pickup_location='123 Main St',
            status='available'
        )
        
        self.client = Client()
    
    def test_donation_request_flow(self):
        # Login as recipient
        self.client.login(username='recipient', password='12345')
        
        # Create request for donation
        request_data = {
            'message': 'I would like to request this donation'
        }
        response = self.client.post(reverse('request_donation', args=[self.donation.id]), request_data)
        self.assertEqual(response.status_code, 302)
        
        # Verify request was created
        self.assertTrue(DonationRequest.objects.filter(
            recipient=self.recipient_profile,
            donation=self.donation
        ).exists())
        
        # Logout recipient and login as donor
        self.client.logout()
        self.client.login(username='donor', password='12345')
        
        # Approve the request
        request = DonationRequest.objects.get(
            recipient=self.recipient_profile,
            donation=self.donation
        )
        response = self.client.get(reverse('approve_request', args=[request.id]))
        self.assertEqual(response.status_code, 302)
        
        # Verify request and donation status were updated
        request.refresh_from_db()
        self.donation.refresh_from_db()
        self.assertEqual(request.status, 'approved')
        self.assertEqual(self.donation.status, 'claimed')