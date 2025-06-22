from django.test import TestCase
from django.urls import reverse
from socialnetwork.models import Author
from rest_framework import status

class AuthorLoginTests(TestCase):

    def setUp(self):
        Author.objects.all().delete()  # Clean up before each test
        self.register_url = reverse('register')
        self.login_url = reverse('login')

        # Create a test user and activate it
        self.test_user = Author.objects.create_user(
            email='testuser@example.com',
            display_name='Test User',
            password='testpassword'
        )
        self.test_user.is_active = True  # Activate the user
        self.test_user.save()


    def test_successful_login(self):
        """Test successful login with valid credentials."""
        login_payload = {
            'username': 'testuser@example.com',
            'password': 'testpassword'
        }

        # Attempt to log in
        response = self.client.post(self.login_url, login_payload)

        # Check if login is successful
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # Expecting redirect after successful login
        profile_url = reverse('profile', kwargs={'author_id': self.test_user.uid})
        self.assertRedirects(response, profile_url)  # Ensure it redirects to the profile page

    def test_login_with_invalid_credentials(self):
        """Test login failure with invalid credentials."""
        login_payload = {
            'username': 'wronguser@example.com',  # Invalid email
            'password': 'wrongpassword'            # Invalid password
        }

        # Attempt to log in
        response = self.client.post(self.login_url, login_payload)

        # Check if the login fails
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should remain on login page
        self.assertContains(response, 'Please enter a correct email and password.')  # Check error message

    def test_login_with_empty_fields(self):
        """Test login failure with empty username and password."""
        login_payload = {
            'username': '',
            'password': ''
        }

        # Attempt to log in
        response = self.client.post(self.login_url, login_payload)

        # Check if the login fails
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should remain on login page
        self.assertContains(response, 'Please enter a correct email and password.')  # Check error message

