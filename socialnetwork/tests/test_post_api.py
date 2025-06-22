from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from socialnetwork.models import Author, Post
from rest_framework import status

class PostAPITests(APITestCase):

    def setUp(self):
        Author.objects.all().delete()  # Clean up before each test
        Post.objects.all().delete()

        # Create a test user and activate it
        self.test_user = Author.objects.create_user(
            email='testuser@example.com',
            display_name='Test User',
            password='testpassword'
        )
        self.test_user.is_active = True  # Activate the user
        self.test_user.save()

        self.test_user2 = Author.objects.create_user(
            email='john@example.com',
            display_name='Johnny',
            password='pw123'
        )
        self.test_user2.is_active = True  # Activate the user
        self.test_user2.save()

        self.test_post = Post()
        self.test_post.host = "testserver"
        self.test_post.title = "A grand title"
        self.test_post.author = self.test_user
        self.test_post.description = "This is pretty neat"
        self.test_post.content_type = "text/plain"
        self.test_post.content = "Bread is good"
        self.test_post.visibility = Post.PUBLIC_VISIBILITY
        self.test_post.save()
        
        self.create_post_url = reverse('add_post',kwargs={"author_uid": self.test_user.uid})
        self.access_post_url = reverse('access_post',kwargs={"author_uid": self.test_user.uid, "post_uid": self.test_post.uid})

    #POST requests
    def test_create_post_success(self):
        """
        Test a successful post creation
        """
        self.api_client = APIClient()
        self.api_client.login(email='testuser@example.com',password='testpassword')
        post_payload = {
            "title": "My first post",
            "description": "This post is very interesting",
            "contentType": "text/plain",
            "content": "I ate a banana yesterday. It was yummy!",
            "visibility": Post.PUBLIC_VISIBILITY
        }
        #attempt to make new post, check post existence
        response = self.api_client.post(self.create_post_url,post_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(Post.objects.all()),2)
        post = Post.objects.all().filter(title="My first post").first()
        self.assertEqual(self.test_user,post.author)

        #check post fields
        self.assertEqual(post.title,post_payload["title"])
        self.assertEqual(post.description,post_payload["description"])
        self.assertEqual(post.content_type,post_payload["contentType"])
        self.assertEqual(post.content,post_payload["content"])
        self.assertEqual(post.visibility,post_payload["visibility"])

    def test_create_post_fail(self):
        """
        Test a failed post creation due to invalid credentials
        """
        self.api_client = APIClient()
        self.api_client.login(email='john@example.com',password='pw123')
        post_payload = {
            "title": "My first post",
            "description": "This post is very interesting",
            "content_type": "text/plain",
            "content": "I ate a banana yesterday. It was yummy!",
            "visibility": Post.PUBLIC_VISIBILITY
        }
        #attempt to make new post, check post existence
        response = self.api_client.post(self.create_post_url,post_payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(Post.objects.all()),1)

    #DELETE requests
    def test_delete_post_success(self):
        """
        Test a successful post deletion
        """
        self.api_client = APIClient()
        self.api_client.login(email='testuser@example.com',password='testpassword')
        
        #attempt to delete post
        response = self.api_client.delete(self.access_post_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(Post.objects.all().filter(visibility=Post.PUBLIC_VISIBILITY)),0)
        self.assertEqual(len(Post.objects.all().filter(visibility=Post.DELETED_VISIBILITY)),1)
    
    def test_delete_post_fail(self):
        """
        Test a failed post deletion due to invalid credentials
        """
        self.api_client = APIClient()
        self.api_client.login(email='john@example.com',password='pw123')
        
        #attempt to delete post
        response = self.api_client.delete(self.access_post_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(Post.objects.all()),1)

    # #PUT requests
    # def test_update_post_success(self):
    #     """
    #     Test a successful post update
    #     """
    #     self.api_client = APIClient()
    #     self.api_client.login(email='testuser@example.com',password='testpassword')

    #     post_payload = {
    #         "title": "My new post",
    #         "description": "This post is very boring",
    #         "content_type": "text/markdown",
    #         "content": "I ate nothing yesterday. I'm hungry",
    #         "visibility": Post.UNLISTED_VISIBILITY
    #     }
    #     #attempt to make new post, check post existence
    #     response = self.api_client.put(self.access_post_url,post_payload)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(Post.objects.all()),1)
    #     post = Post.objects.all().filter(title="My new post").first()
    #     self.assertEqual(self.test_user,post.author)

    #     #check post fields
    #     self.assertEqual(post.title,post_payload["title"])  
    #     self.assertEqual(post.description,post_payload["description"])
    #     self.assertEqual(post.content_type,post_payload["content_type"])
    #     self.assertEqual(post.content,post_payload["content"])
    #     self.assertEqual(post.visibility,post_payload["visibility"])

    def test_update_post_fail(self):
        """
        Test a failed post creation due to invalid credentials
        """
        self.api_client = APIClient()
        self.api_client.login(email='john@example.com',password='pw123')

        post_payload = {
            "title": "My new post",
            "description": "This post is very boring",
            "content_type": "text/markdown",
            "content": "I ate nothing yesterday. I'm hungry",
            "visibility": Post.UNLISTED_VISIBILITY
        }
        #attempt to make new post, check post existence
        response = self.api_client.put(self.access_post_url,post_payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(len(Post.objects.all()),1)
        post = Post.objects.all().filter(title="My first post").first()

        #check post fields
        self.assertNotEqual(self.test_post.title,post_payload["title"])
        self.assertNotEqual(self.test_post.description,post_payload["description"])
        self.assertNotEqual(self.test_post.content_type,post_payload["content_type"])
        self.assertNotEqual(self.test_post.content,post_payload["content"])
        self.assertNotEqual(self.test_post.visibility,post_payload["visibility"])