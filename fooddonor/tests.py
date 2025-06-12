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
        self.signup_url = reverse('fooddonor:register')
    
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

    def test_signup_donor_missing_location(self):
        response = self.client.post(self.signup_url, {
            'username': 'donormissingloc',
            'email': 'donormissingloc@test.com',
            'password1': 'securepassword123',
            'password2': 'securepassword123',
            'phone_number': '1234567890',
            'role': 'donor',
            # 'location' is missing
        })
        # Form should be invalid, so status code 200 with form errors
        self.assertEqual(response.status_code, 200)
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertIn('Location is required for Food Donors.', form.non_field_errors())
        self.assertFalse(User.objects.filter(username='donormissingloc').exists())

    def test_get_registration_form(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registeruser.html')
        self.assertIn('form', response.context)

    def test_signup_short_username(self):
        response = self.client.post(self.signup_url, {
            'username': 'short',
            'email': 'short@test.com',
            'password1': 'securepassword123',
            'password2': 'securepassword123',
            'phone_number': '1234567890',
            'role': 'donor',
            'location': 'Test Location'
        })
        self.assertEqual(response.status_code, 200)
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertIn('Username must be at least 6 characters long.', form.errors.get('username', []))
        self.assertFalse(User.objects.filter(username='short').exists())

    def test_signup_missing_required_fields(self):
        response = self.client.post(self.signup_url, {
            'username': '',
            'email': '',
            'password1': '',
            'password2': '',
            'phone_number': '',
            'role': '',
            'location': ''
        })
        self.assertEqual(response.status_code, 200)
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertIn('This field is required.', form.errors.get('username', []))
        self.assertIn('This field is required.', form.errors.get('email', []))
        self.assertIn('This field is required.', form.errors.get('password1', []))
        self.assertIn('This field is required.', form.errors.get('password2', []))
        self.assertIn('This field is required.', form.errors.get('phone_number', []))
        self.assertIn('This field is required.', form.errors.get('role', []))
        self.assertFalse(User.objects.filter(username='').exists())

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

class DonorLoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('fooddonor:donorlogin')
        self.user = User.objects.create_user(username='donoruser', password='testpassword')
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='1234567890',
            role='donor',
            location='Test Location'
        )

    def test_get_login_page(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login')
        self.assertIn('form', response.context)

    def test_post_valid_login(self):
        response = self.client.post(self.login_url, {
            'username': 'donoruser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('fooddonor:donor_dashboard'))

    def test_post_invalid_login(self):
        response = self.client.post(self.login_url, {
            'username': 'donoruser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        # Adjusted assertion to check for form errors instead of specific error message text
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertTrue(form.errors)
        self.assertIn('__all__', form.errors)
        self.assertIn('form', response.context)

    def test_post_login_with_next_redirect(self):
        next_url = reverse('fooddonor:donor_dashboard')
        response = self.client.post(self.login_url + '?next=' + next_url, {
            'username': 'donoruser',
            'password': 'testpassword',
            'next': next_url
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, next_url)
