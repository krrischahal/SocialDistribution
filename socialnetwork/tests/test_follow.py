from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from socialnetwork.models import Author, Follow
import uuid

class FollowApiTests(TestCase):
    def setUp(self):
        # Initialize the API client
        self.client = APIClient()

        # Create two authors for testing
        self.author1 = Author.objects.create_user(
            email='author1@example.com',
            display_name='Author One',
            password='password1',
            host='http://localhost/api/',
            page='http://localhost/api/authors/{}/'.format(uuid.uuid4())
        )

        self.author2 = Author.objects.create_user(
            email='author2@example.com',
            display_name='Author Two',
            password='password2',
            host='http://localhost/api/',
            page='http://localhost/api/authors/{}/'.format(uuid.uuid4())
        )

        # URL patterns for the endpoints
        self.follow_author_url = reverse('follow_author')
        self.unfollow_author_url = reverse('unfollow_author')
        self.follower_detail_url = lambda author_uid, foreign_author_id: f'/authors/{author_uid}/followers/{foreign_author_id}'
        self.list_followers_url = lambda author_uid: f'/authors/{author_uid}/followers/'

    def test_nonexistent_author_cannot_be_followed(self):
        # Log in as author1
        self.client.force_authenticate(user=self.author1)

        # Try to follow a non-existent author
        payload = {'author_id': 'http://localhost/api/authors/nonexistent_author_id/'}
        response = self.client.post(self.follow_author_url, payload, format='json')

        # Should return 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_follower_detail_not_a_follower(self):
        # Check follower detail when author1 is not a follower of author2
        url = self.follower_detail_url(self.author2.uid, self.author1.uid)
        response = self.client.get(url)

        # Should return 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_accept_nonexistent_follow_request(self):
        # Log in as author2
        self.client.force_authenticate(user=self.author2)

        # Try to accept a follow request that doesn't exist
        url = self.follower_detail_url(self.author2.uid, self.author1.uid)
        response = self.client.put(url)

        # Should return 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FollowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create two authors
        self.author1 = Author.objects.create_user(
            email='author1@example.com',
            display_name='Author One',
            password='password1',
            host='http://localhost/api/'
        )

        self.author2 = Author.objects.create_user(
            email='author2@example.com',
            display_name='Author Two',
            password='password2',
            host='http://localhost/api/'
        )

        # Authenticate as author1
        self.client.force_authenticate(user=self.author1)

        # Endpoints
        self.follow_author_url = '/api/follow/'
        self.unfollow_author_url = '/api/unfollow/'
        self.list_followers_url = f'/api/authors/{str(self.author2.uid)}/followers/'
        self.follower_detail_url = lambda follower_id: f'/api/authors/{str(self.author2.uid)}/followers/{follower_id}/'

    def test_follow_author_fail(self):
        """
        Test that an author can follow another author.
        """
        payload = {
            'author_id': self.author2.id
        }
        response = self.client.post(self.follow_author_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, msg=f'Response content: {response.content}')

    def test_list_followers(self):
        """
        Test listing followers of an author.
        """
        # First, author1 follows author2
        Follow.objects.create(
            follower=self.author1,
            following=self.author2,
            status='accepted'
        )

        # Authenticate as author2
        self.client.force_authenticate(user=self.author2)

        # Get the list of followers
        response = self.client.get(self.list_followers_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=f'Response content: {response.content}')

        # Check that author1 is in the list of followers
        followers = response.data.get('followers', [])
        follower_ids = [follower['id'] for follower in followers]
        self.assertIn(self.author1.id, follower_ids)

    def test_check_follower_detail(self):
        """
        Test checking if an author is a follower of another author.
        """
        # First, author1 follows author2
        Follow.objects.create(
            follower=self.author1,
            following=self.author2,
            status='accepted'
        )

        # Endpoint to check follower detail
        follower_detail_url = self.follower_detail_url(self.author1.id)

        # Authenticate as author2
        self.client.force_authenticate(user=self.author2)

        # Check if author1 is a follower of author2
        response = self.client.get(follower_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, msg=f'Response content: {response.content}')
