from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from socialnetwork.models import Author
import random
from time import time

import uuid


class AuthorApiTests(TestCase):
    def setUp(self):
        # Clear out any existing authors before each test
        Author.objects.all().delete()
        # Set up the client and initial data for testing
        self.client = APIClient()
        self.admin_user = Author.objects.create_superuser(
            email='admin@example.com',
            display_name='Admin',
            password='adminpassword'
        )
        self.client.force_authenticate(user=self.admin_user)
        self.author_list_url = reverse('list_authors')
        self.add_author_url = reverse('add_author')

    def test_list_authors(self):
        response = self.client.get(self.author_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('authors', response.data)  # Check for 'authors' instead of 'items'
        self.assertIsInstance(response.data['authors'], list)  # Ensure 'authors' is a list


    def test_add_author(self):
        # Check current author count
        current_count = Author.objects.count()
        print(f"Current author count: {current_count}")  # Log the current count

        payload = {
            'email': f'newuser_{self._get_unique_suffix()}@example.com',
            'displayName': 'New User',
            'password': 'newuserpassword',
            'host': 'http://localhost',
            'page': f'http://localhost/authors/{uuid.uuid4()}/'  # Only pass 'page', 'id' will be computed
        }

        response = self.client.post(self.add_author_url, payload, format='json')
        print(f"Response for adding new author: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # After adding, check the count again
        self.assertEqual(Author.objects.count(), current_count + 1)  # Check against current count



    def test_get_author(self):
        author = Author.objects.create_user(
            email=f'gettest_{self._get_unique_suffix()}@example.com',
            display_name='Get Test User',
            password='password'
        )
        url = reverse('get_author', args=[author.uid])
        response = self.client.get(url)
        print(f"Response for getting new author: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['displayName'], 'Get Test User')

    def test_delete_author(self):
        author_to_delete = Author.objects.create_user(
            email=f'delete_{self._get_unique_suffix()}@example.com',
            display_name='Delete User',
            password='deletepassword'
        )
        url = reverse('delete_author', args=[author_to_delete.uid])
        response = self.client.delete(url)
        print(f"Response for deleting author: {response.status_code}, {response.data}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Author.objects.filter(uid=author_to_delete.uid).exists())

    def _get_unique_suffix(self):
        """Generate a unique suffix for email addresses using UUID."""
        return str(uuid.uuid4())  #
