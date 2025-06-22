from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from ..models import Author, Post, Like, Follow, Comment
from ..serializers import AuthorSerializer, LikeSerializer, CommentSerializer, PostSerializer
from uuid import uuid4
from ..models import LocalVars

class InboxSerializerTests(APITestCase):

    def setUp(self):
        # Generate a valid UUID for the local author
        self.author_uid = uuid4()
        self.author = Author.objects.create(
            uid=self.author_uid,
            id=f'http://localhost:8000/authors/{self.author_uid}',
            host='http://localhost:8000/',
            display_name='Test Author',
            github='',
            profile_image='',
            page=f'http://localhost:8000/authors/{self.author_uid}',
            is_remote=False,
        )
        self.inbox_url = reverse('inbox', kwargs={'author_uid': self.author.uid})
        LocalVars.objects.create(node_host='localhost:8000')

    def test_follow_activity(self):
        """Test handling a 'follow' activity."""
        # Generate a valid UUID for the remote author
        remote_author_uid = uuid4()
        data = {
            "type": "Follow",
            "actor": {
                "id": f"http://remotehost.com/authors/{remote_author_uid}",
                "host": "http://remotehost.com/",
                "displayName": "Remote Author",
                "github": "",
                "profileImage": "",
                "url": f"http://remotehost.com/authors/{remote_author_uid}"
            },
            "object": {
                "id": self.author.id,
                "host": self.author.host
            }
        }

        response = self.client.post(self.inbox_url, data, format='json')
        self.assertEqual(response.status_code, 201)

        # Verify that the remote author was created
        follower = Author.objects.get(id=f"http://remotehost.com/authors/{remote_author_uid}")
        self.assertTrue(follower.is_remote)
        self.assertEqual(follower.display_name, "Remote Author")

        # Verify that the follow request was created
        follow = Follow.objects.get(follower=follower, following=self.author)
        self.assertEqual(follow.status, 'pending')

    def test_post_activity(self):
        """Test handling a 'post' activity."""
        # Generate valid UUIDs for the remote author and post
        remote_author_uid = uuid4()
        post_uid = uuid4()
        data = {
            "type": "post",
            "title": "Test Post",
            "id": f"http://remotehost.com/posts/{post_uid}",
            "page": f"http://remotehost.com/posts/{post_uid}",
            "description": "A test post",
            "contentType": "text/plain",
            "content": "This is a test post.",
            "visibility": "PUBLIC",
            "author": {
                "id": f"http://remotehost.com/authors/{remote_author_uid}",
                "host": "http://remotehost.com/",
                "displayName": "Remote Author",
                "github": "",
                "profileImage": "",
                "page": f"http://remotehost.com/authors/{remote_author_uid}"
            },
            "published": timezone.now().isoformat()
        }

        response = self.client.post(self.inbox_url, data, format='json')
        self.assertEqual(response.status_code, 201)

        # Verify that the post was created
        post = Post.objects.get(id=f"http://remotehost.com/posts/{post_uid}")
        self.assertEqual(post.title, "Test Post")
        self.assertEqual(post.content, "This is a test post.")

        # Verify that the author was created
        author = Author.objects.get(id=f"http://remotehost.com/authors/{remote_author_uid}")
        self.assertTrue(author.is_remote)
        self.assertEqual(author.display_name, "Remote Author")

    def test_like_activity(self):
        """Test handling a 'like' activity."""
        # Create a local post to be liked
        post_uid = uuid4()
        post = Post.objects.create(
            id=f"http://localhost:8000/posts/{post_uid}",
            title="Local Post",
            author=self.author,
            content="Local post content",
            visibility="PUBLIC",
            published_at=timezone.now()
        )

        # Generate a valid UUID for the remote author and like
        remote_author_uid = uuid4()
        like_uid = uuid4()
        data = {
            "type": "like",
            "author": {
                "id": f"http://remotehost.com/authors/{remote_author_uid}",
                "host": "http://remotehost.com/",
                "displayName": "Remote Author",
                "github": "",
                "profileImage": "",
                "page": f"http://remotehost.com/authors/{remote_author_uid}"
            },
            "published": timezone.now().isoformat(),
            "id": f"http://remotehost.com/likes/{like_uid}",
            "object": post.id
        }

        response = self.client.post(self.inbox_url, data, format='json')
        self.assertEqual(response.status_code, 201)

        # Verify that the like was created
        like = Like.objects.get(id=f"http://remotehost.com/likes/{like_uid}")
        self.assertEqual(like.object, post.id)
        self.assertEqual(like.author.id, f"http://remotehost.com/authors/{remote_author_uid}")

    def test_comment_activity(self):
        """Test handling a 'comment' activity."""
        # Create a local post to comment on
        post_uid = uuid4()
        post = Post.objects.create(
            id=f"http://localhost:8000/posts/{post_uid}",
            title="Local Post",
            author=self.author,
            content="Local post content",
            visibility="PUBLIC",
            published_at=timezone.now()
        )

        # Generate valid UUIDs for the remote author and comment
        remote_author_uid = uuid4()
        comment_uid = uuid4()
        data = {
            "type": "comment",
            "author": {
                "id": f"http://remotehost.com/authors/{remote_author_uid}",
                "host": "http://remotehost.com/",
                "displayName": "Remote Author",
                "github": "",
                "profileImage": "",
                "page": f"http://remotehost.com/authors/{remote_author_uid}"
            },
            "comment": "This is a test comment.",
            "contentType": "text/plain",
            "published": timezone.now().isoformat(),
            "id": f"http://remotehost.com/comments/{comment_uid}",
            "post": post.id,
            "page": f"http://remotehost.com/comments/{comment_uid}"
        }

        response = self.client.post(self.inbox_url, data, format='json')
        self.assertEqual(response.status_code, 201)

        # Verify that the comment was created
        comment = Comment.objects.get(id=f"http://remotehost.com/comments/{comment_uid}")
        self.assertEqual(comment.comment, "This is a test comment.")
        self.assertEqual(comment.post, post.id)
        self.assertEqual(comment.author.id, f"http://remotehost.com/authors/{remote_author_uid}")

    def test_invalid_activity_type(self):
        """Test handling an unsupported activity type."""
        data = {
            "type": "unknown",
            "actor": {},
            "object": {}
        }

        response = self.client.post(self.inbox_url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Unsupported activity type', response.data['error'])

