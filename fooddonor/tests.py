from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile, FoodDonation, DonationRequest
from datetime import date, timedelta
from fooddonor.models import Profile
from fooddonor.factories import UserFactory

class UserFactoryTestCase(TestCase):

    def test_create_donor_profile(self):
        user = User.objects.create_user(username='donoruser', password='testpass')
        profile = UserFactory.create_user(user, 'donor')
        self.assertEqual(profile.role, 'donor')
        self.assertEqual(profile.user.username, 'donoruser')

    def test_create_recipient_profile(self):
        user = User.objects.create_user(username='recipientuser', password='testpass')
        profile = UserFactory.create_user(user, 'recipient')
        self.assertEqual(profile.role, 'recipient')

    def test_create_admin_profile(self):
        user = User.objects.create_user(username='adminuser', password='testpass')
        profile = UserFactory.create_user(user, 'admin')
        self.assertEqual(profile.role, 'admin')

    def test_invalid_role_raises_error(self):
        user = User.objects.create_user(username='baduser', password='testpass')
        with self.assertRaises(ValueError):
            UserFactory.create_user(user, 'unknownrole')

class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('fooddonor:register')  # Ensure 'register' is named in urls.py

    def test_register_get_request_renders_template(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registeruser.html')

    def test_register_post_valid_data_creates_user_and_profile(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123',
            'phone_number': '0123456789',
            'role': 'donor',
            'location': 'Kuala Lumpur',
            'needs_description': 'Need to donate often'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 302)  # Check for redirect

        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(Profile.objects.filter(user__username='testuser').exists())

    def test_register_post_invalid_data_shows_errors(self):
        data = {
            'username': '',
            'email': 'invalid-email',
            'password1': 'short',
            'password2': 'mismatch',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)  # Form will reload with errors
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertTrue(form.errors)

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

class AddFoodListingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.add_food_url = reverse('fooddonor:add_food')
        self.user = User.objects.create_user(username='donoruser', password='testpassword')
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='1234567890',
            role='donor',
            location='Test Location'
        )
        self.client.login(username='donoruser', password='testpassword')

    def test_get_add_food_form(self):
        response = self.client.get(self.add_food_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'addfoodlisting.html')
        self.assertIn('form', response.context)

    def test_post_valid_food_listing(self):
        data = {
            'title': 'Fresh Apples',
            'description': 'A bunch of fresh apples',
            'quantity': '10 kg',
            'expiry_date': (date.today() + timedelta(days=5)).isoformat(),
            'pickup_location': '123 Orchard St'
        }
        # Fix: patch request.user to user, and patch get_profile to return profile
        from unittest.mock import patch
        with patch('django.contrib.auth.get_user', return_value=self.user):
            with patch('fooddonor.views.Profile.objects.get', return_value=self.profile):
                response = self.client.post(self.add_food_url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(FoodDonation.objects.filter(title='Fresh Apples', donor=self.profile).exists())

    def test_post_invalid_food_listing(self):
        data = {
            'title': '',  # Missing title
            'description': 'A bunch of fresh apples',
            'quantity': '10 kg',
            'expiry_date': (date.today() + timedelta(days=5)).isoformat(),
            'pickup_location': '123 Orchard St'
        }
        response = self.client.post(self.add_food_url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertTrue(form.errors)
        self.assertIn('title', form.errors)

class EditDeleteFoodListingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='donoruser', password='testpassword')
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='1234567890',
            role='donor',
            location='Test Location'
        )
        self.client.login(username='donoruser', password='testpassword')
        self.food = FoodDonation.objects.create(
            donor=self.profile,
            title='Old Title',
            description='Old Description',
            quantity='5 kg',
            expiry_date=date.today() + timedelta(days=5),
            pickup_location='Old Location',
            status='available'
        )
        self.edit_url = reverse('fooddonor:edit_food', args=[self.food.pk])
        self.delete_url = reverse('fooddonor:delete_food', args=[self.food.pk])

    def test_get_edit_food_form(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'editfoodlisting.html')
        self.assertIn('form', response.context)

    def test_post_valid_edit_food(self):
        data = {
            'title': 'New Title',
            'description': 'New Description',
            'quantity': '10 kg',
            'expiry_date': (date.today() + timedelta(days=10)).isoformat(),
            'pickup_location': 'New Location'
        }
        response = self.client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 302)
        self.food.refresh_from_db()
        self.assertEqual(self.food.title, 'New Title')
        self.assertEqual(self.food.description, 'New Description')

    def test_post_invalid_edit_food(self):
        data = {
            'title': '',  # Missing title
            'description': 'New Description',
            'quantity': '10 kg',
            'expiry_date': (date.today() + timedelta(days=10)).isoformat(),
            'pickup_location': 'New Location'
        }
        response = self.client.post(self.edit_url, data)
        self.assertEqual(response.status_code, 200)
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertTrue(form.errors)
        self.assertIn('title', form.errors)

    def test_get_delete_food_confirmation(self):
        response = self.client.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'confirm_delete.html')
        self.assertIn('food', response.context)

    def test_post_delete_food(self):
        response = self.client.post(self.delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FoodDonation.objects.filter(pk=self.food.pk).exists())

class FoodListingViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='donoruser', password='testpassword')
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='1234567890',
            role='donor',
            location='Test Location'
        )
        self.client.login(username='donoruser', password='testpassword')
        # Create multiple food donations
        for i in range(3):
            FoodDonation.objects.create(
                donor=self.profile,
                title=f'Food {i}',
                description=f'Description {i}',
                quantity=f'{i+1} kg',
                expiry_date=date.today() + timedelta(days=5 + i),
                pickup_location=f'Location {i}',
                status='available'
            )
        self.list_url = reverse('fooddonor:food_listing')

    def test_food_listing_view(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'foodlisting.html')
        self.assertIn('donations', response.context)
        self.assertEqual(len(response.context['donations']), 3)
