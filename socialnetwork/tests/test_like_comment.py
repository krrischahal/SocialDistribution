from django.test import TestCase
from django.urls import reverse
from socialnetwork.models import Author, Post, Comment, Like, Likes, Comments
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
from rest_framework.response import Response
from rest_framework.test import APITestCase, APIClient


class LikeCommentTests(TestCase):

    def setUp(self):
        # Clear previous data
        Author.objects.all().delete()
        Post.objects.all().delete()
        Comment.objects.all().delete()
        Like.objects.all().delete()
        Likes.objects.all().delete()
        Comments.objects.all().delete()

        # Setup data
        self.author = Author.objects.create_user(
            email='author@example.com',
            display_name='Author',
            password='password123'
        )
        self.client.login(email='author@example.com', password='password123')

        self.post = Post.objects.create(
            author=self.author,
            title='Test Post',
            description='Test Description',
            content_type='text/markdown',
            content='This is a test post.',
            visibility=Post.PUBLIC_VISIBILITY,
            host='http://localhost',
        )

        self.comments = Comments.objects.create(
            page=f"http://localhost/authors/{self.author.uid}/posts/{self.post.uid}/comments",
            id=f"http://localhost/api/authors/{self.author.uid}/posts/{self.post.uid}/comments"
        )

        # Create a comment with FQIDs
        self.comment = Comment.objects.create(
            author=self.author,
            comment="This is a test comment",
            content_type="text/markdown",
            post=f"http://localhost/api/authors/{self.author.uid}/posts/{self.post.uid}",
            page=f"http://localhost/authors/{self.author.uid}/posts/{self.post.uid}/comments",
            comments=self.comments
        )

        self.like_post_url = reverse('like_post', args=[self.author.uid, self.post.uid])
        self.add_comment_url = reverse('add_comment', args=[self.author.uid, self.post.uid])


    def test_like_post(self):
        """Test liking a post."""
        response = self.client.post(self.like_post_url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    # def test_add_comment(self):
    #     """Test adding a comment to a post."""
    #     # Ensure user is logged in
    #     # response1 = self.client.get(self.add_comment_url, follow=True)
    #     # print(response1.redirect_chain) 

    #     # self.client.login(email='author@example.com', password='password123')

    #     # self.api_client = APIClient()
    #     # self.api_client.login(email='author@example.com', password='password123')
        
    #     comment_payload = {'comment': 'This is a test comment.', 'content_type': 'text/Plaintext'}
        
    #     # Perform the POST request to add a comment
    #     response = self.client.post(self.add_comment_url, comment_payload, follow=True)
    #     print(response.redirect_chain) 
        
    #     # Check that the response status is 201 CREATED
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    #     # Verify comment count in the Comments object
    #     self.assertEqual(response.json().get('comments_count'), 2)

    #     # Validate the FQID of the new comment
    #     new_comment = Comment.objects.get(uid=response.json().get('comment_id'))
    #     expected_id = f"http://localhost/api/authors/{self.author.uid}/commented/{new_comment.uid}"
    #     self.assertEqual(new_comment.id, expected_id)
    #     self.assertEqual(new_comment.comment, comment_payload['comment'])



    # def test_like_comment(self):
    #     """Test liking a comment on a post."""
    #     like_comment_url = reverse('like_comment', args=[self.author.uid, self.comment.uid])

    #     response = self.client.post(like_comment_url)
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    #     # Verify the like count on the comment's Likes object
    #     self.comment.refresh_from_db()
    #     self.assertEqual(self.comment.likes.like_set.count(), 1)


    @patch('requests.get')
    def test_get_post_comments_by_fqid(self, mock_get):
        """Test retrieving comments by post FQID."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"type": "comments", "items": []}
        
        post_fqid = self.post.uid
        url = reverse('get_post_comments_by_fqid', args=[post_fqid])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('type'), 'comments')
        self.assertIsInstance(response.json().get('items'), list)

    @patch('requests.get')
    def test_get_remote_comment(self, mock_get):
        """Test retrieving a remote comment."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"comment": "This is a remote comment"}
        
        mock_comment = MagicMock(spec=Comment)
        mock_comment.post = self.post.page
        mock_comment.id = self.comment.id
        mock_comment.comment = self.comment.comment
        # mock_comment.author_url = self.comment.author_url
        mock_comment.content_type = self.comment.content_type
        mock_comment.published = self.comment.published
        mock_comment.likes = self.comment.likes

        remote_comment_fqid = self.comment.id
        url = reverse('get_remote_comment', args=[self.author.uid, self.post.uid, remote_comment_fqid])
        with patch('socialnetwork.views.like_comment.get_object_or_404', return_value=mock_comment):
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('requests.get')
    def test_get_comment(self, mock_get):
        """Test retrieving a single comment by FQID."""
        # Mock the author data retrieval response
        mock_get.return_value.json.return_value = {
            "type": "author",
            "id": f"http://localhost/api/authors/{self.author.uid}"
        }

        # Ensure the post's Comments object exists
        if not self.post.comments:
            self.post.comments = Comments.objects.create(
                page=f"http://localhost/authors/{self.author.uid}/posts/{self.post.uid}/comments",
                id=f"http://localhost/api/authors/{self.author.uid}/posts/{self.post.uid}/comments"
            )
            self.post.save()

        # Create a mock Comment instance
        mock_comment = MagicMock(spec=Comment)
        mock_comment.post = f"http://localhost/api/authors/{self.author.uid}/posts/{self.post.uid}"
        mock_comment.id = self.comment.id  # Use FQID of the existing comment
        mock_comment.comment = "Sample Comment"
        mock_comment.author = self.author
        mock_comment.content_type = "text/markdown"
        mock_comment.published = self.comment.published
        mock_comment.likes = self.comment.likes

        # Define the URL to fetch the comment by FQID
        url = reverse('get_comment', args=[mock_comment.id])

        # Patch `get_object_or_404` to return the mock Comment instance
        with patch('socialnetwork.views.like_comment.get_object_or_404', return_value=mock_comment):
            response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Validate the response structure
        response_data = response.json()

        # # Check for keys and assert their values
        # expected_keys = ["id", "comment", "post", "author", "content_type", "published", "likes"]
        # for key in expected_keys:
        #     self.assertIn(key, response_data, f"Missing key '{key}' in response")

        self.assertEqual(response_data["id"], mock_comment.id)
        self.assertEqual(response_data["post"], mock_comment.post)
        # self.assertEqual(response_data["content_type"], mock_comment.content_type)

        # Normalize author IDs for comparison
        actual_author_id = response_data["author"]["id"].rstrip('/')
        expected_author_id = mock_get.return_value.json()["id"].strip("'").replace("http://localhost/api", "")
        self.assertEqual(actual_author_id, expected_author_id)

        self.assertIn("likes", response_data)




    def test_get_author_commented_posts(self):
        """Test retrieving all posts commented on by an author."""
        url = reverse('get_author_commented_posts', args=[self.author.uid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_get_post_likes(self):
        """Test retrieving likes for a post."""
        url = reverse('get_post_likes', args=[self.author.uid, self.post.uid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('requests.get')
    def test_get_post_likes_by_fqid(self, mock_get):
        """Test retrieving likes by post FQID."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"type": "likes", "items": []}
        
        post_fqid = self.post.uid  # Or any FQID value
        url = reverse('get_post_likes_by_fqid', args=[post_fqid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_comment_likes(self):
        """Test retrieving likes on an existing comment."""
        # Use the existing comment created in setUp
        url = reverse('get_comment_likes', args=[self.author.uid, self.post.uid, self.comment.uid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_author_liked(self):
        """Test retrieving all posts/comments liked by an author."""
        url = reverse('get_author_liked', args=[self.author.uid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_specific_liked(self):
        """Test retrieving a specific like made by an author."""
        # Use the post's `add_like` method, ensuring `author_url` has a valid URL scheme
        import uuid
        unique_email = f"{uuid.uuid4()}@example.com"
        self.author.email = unique_email
        self.author.id = f"http://localhost/api/authors/{self.author.uid}/"
        self.author.save()  # Save to update the author's URL

        # Now add a like and retrieve it
        like = self.post.add_like(self.author)  # This will use the updated URL

        url = reverse('get_specific_liked', args=[self.author.uid, like.uid])
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "type": "author",
                "id": self.author.id,
                "displayName": self.author.display_name,
            }
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    
    @patch('requests.get')
    def test_get_specific_commented(self, mock_get):
        """Test retrieving a specific comment made by an author."""
        mock_get.return_value.json.return_value = {"type": "author", "id": f"http://localhost/api/authors/{self.author.uid}"}

        url = reverse('get_specific_commented', args=[self.author.uid, self.comment.uid])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("comment", response.json())
        self.assertEqual(response.json()['id'], self.comment.id)
        self.assertEqual(response.json()['post'], self.comment.post)


    
    # # def test_receive_like_inbox(self):
    # #     """Test receiving a like in the inbox."""
    # #     url = reverse('receive_like_inbox', args=[self.author.uid])

    # #     # Define the payload with 'type' to simulate a like activity
    # #     payload = {
    # #         "type": "like",
    # #         "author": {
    # #             "id": f"http://localhost/api/authors/{self.author.uid}",
    # #             "displayName": "Author"
    # #         },
    # #         "object": f"http://localhost/api/posts/{self.post.uid}"
    # #     }

    # #     # Mock the Response for unimplemented "like" handling in the inbox view
    # #     with patch("socialnetwork.views.inbox.Response", return_value=Response(status=status.HTTP_204_NO_CONTENT)):
    # #         response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        
    # #     # Verify that it returns 204 No Content, as we're only testing the structure
    # #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    # # def test_get_single_like(self):
    # #     """Test retrieving a single like by FQID."""
    # #     # Use a valid author_url and object URL if required by the Like model
    # #     like = Like.objects.create(
    # #         object=f"http://localhost/api/authors/{self.author.uid}/posts/{self.post.uid}",
    # #         author_url=f"http://localhost/api/authors/{self.author.uid}"
    # #     )
        
    # #     url = reverse('get_single_like', args=[like.id])
    # #     response = self.client.get(url)
    # #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    # #@patch("requests.get")
    # # def test_get_local_commented(self, mock_get):
    # #     """Test retrieving a local comment by FQID with mocked author data."""
        
    # #     # Mock the external request to return author details
    # #     mock_get.return_value.status_code = 200
    # #     mock_get.return_value.json.return_value = {
    # #         "type": "author",
    # #         "id": self.comment.author_url,
    # #         "displayName": self.author.display_name,
    # #     }
        
    # #     # Patch the comment instance to add a `post` attribute
    # #     with patch.object(Comment, 'post', self.comment.post_id):
    # #         url = reverse('get_local_commented', args=[self.comment.id])
    # #         response = self.client.get(url)
        
    # #     # Verify the response
    # #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    # #     self.assertEqual(response.json().get("type"), "comment")
    # #     self.assertEqual(response.json().get("author")["id"], self.comment.author_url)
    
    # #@patch("socialnetwork.views.like_comment.receive_comment_inbox")
    # # def test_receive_comment_inbox(self, mock_receive_comment_inbox):
    # #     """Test receiving a comment in the inbox with mocked response."""
    # #     mock_receive_comment_inbox.return_value = Response(
    # #         {"message": "Comment received in inbox"}, status=status.HTTP_201_CREATED
    # #     )

    # #     url = reverse('receive_comment_inbox', args=[self.author.uid])
    # #     payload = {"type": "comment", "comment": "This is a test comment in inbox"}
    # #     response = self.client.post(url, data=json.dumps(payload), content_type="application/json")

    # #     # Verify the response
    # #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    # #     self.assertEqual(response.json().get("message"), "Comment received in inbox")
    
    # # @patch("requests.get")
    # # def test_get_post_comments(self, mock_get):
    # #     """Test retrieving comments on a specific post."""
    # #     # Mock the response for the author's URL to avoid actual HTTP requests
    # #     mock_get.return_value.status_code = 200
    # #     mock_get.return_value.json.return_value = {
    # #         "type": "author",
    # #         "id": self.comment.author_url,
    # #         "displayName": self.author.display_name,
    # #     }

    # #     url = reverse('get_post_comments', args=[self.author.uid, self.post.uid])
    #     response = self.client.get(url)
        
    #     # Check response status and format
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.json().get("type"), "comments")
    #     self.assertIsInstance(response.json().get("items"), list)
