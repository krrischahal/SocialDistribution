from django.test import TestCase
from django.urls import reverse
from socialnetwork.models import Author
from rest_framework import status

class AuthorRegistrationTests(TestCase):

    def setUp(self):
        Author.objects.all().delete()  # Clean up before each test
        self.register_url = reverse('register')

    def test_successful_registration(self):
        """Test successful registration of a new user."""
        registration_payload = {
            'email': 'newuser@example.com',
            'display_name': 'New User',
            'github': 'https://github.com/newuser',
            'profile_image': '',  # Can be omitted if not required
            'bio': 'This is a test bio.',
            'password1': 'testpassword',
            'password2': 'testpassword'
        }

        # Register the user
        response = self.client.post(self.register_url, registration_payload)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)  # Expecting redirect after successful registration

        # Check if the user was created
        new_user = Author.objects.get(email='newuser@example.com')
        self.assertIsNotNone(new_user)  # Ensure the user exists
        self.assertEqual(new_user.display_name, 'New User')  # Check if display name is set correctly

    def test_registration_with_mismatched_passwords(self):
        """Test registration failure due to mismatched passwords."""
        registration_payload = {
            'email': 'mismatchuser@example.com',
            'display_name': 'Mismatch User',
            'github': 'https://github.com/mismatchuser',
            'profile_image': '',  # Can be omitted if not required
            'bio': 'This is a test bio.',
            'password1': 'testpassword',
            'password2': 'differentpassword'  # Mismatched password
        }

        # Attempt to register the user
        response = self.client.post(self.register_url, registration_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should remain on registration page
        self.assertContains(response, 'The two password fields didn’t match.')  # Check error message
