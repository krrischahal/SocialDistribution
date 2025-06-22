from django.shortcuts import render, redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import urllib.parse
from ..serializers import AuthorSerializer, FollowSerializer, PostSerializer
from ..models import *
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.decorators import permission_classes
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from ..forms import AuthorCreationForm, AuthorProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from ..serializers import PostSerializer1
from rest_framework.permissions import IsAuthenticated
from ..utils import sync_github_activity, fetch_github_activity
from itertools import chain
from datetime import datetime, timezone as dt_timezone  # Use standard library's timezone
from operator import attrgetter
from django.utils import timezone 
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.http import HttpResponse, Http404
import requests
from .post import push_post_to_inboxes
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
def home(request):
    """
    Home Page

    This view renders the home page for the social network application.

    HTTP Methods:
        GET: Retrieve the home page.

    Returns:
        TemplateResponse: Renders the home.html template.
    """

    return view_posts(request)
    # return render(request, 'home.html')
@swagger_auto_schema(
    method='post',
    operation_description="Create a follow request for the specified author.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "type": openapi.Schema(type=openapi.TYPE_STRING, example="follow"),
            "summary": openapi.Schema(type=openapi.TYPE_STRING, example="actor wants to follow object"),
            "actor": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="author"),
                    "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/{actor_id}"),
                    "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com"),
                    "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="Actor's Display Name"),
                    "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/actor.jpg"),
                    "bio": openapi.Schema(type=openapi.TYPE_STRING, example="Actor's biography")
                }
            ),
            "object": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="author"),
                    "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/{author_id}"),
                    "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com"),
                    "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="Author's Display Name"),
                    "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/author.jpg"),
                    "bio": openapi.Schema(type=openapi.TYPE_STRING, example="Author's biography")
                }
            )
        },
        required=["type", "actor", "object"]
    ),
    responses={
        200: openapi.Response(
            description="Follow request sent successfully.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="follow"),
                    "summary": openapi.Schema(type=openapi.TYPE_STRING, example="Follow request sent"),
                    "actor": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(type=openapi.TYPE_STRING, example="author"),
                            "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/{actor_id}"),
                            "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com"),
                            "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="Actor's Display Name"),
                            "github": openapi.Schema(type=openapi.TYPE_STRING, example="http://github.com/author"),
                            "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/actor.jpg"),
                            "page": openapi.Schema(type=openapi.TYPE_STRING, example="http://nodeaaaa/authors/author")
                        }
                    ),
                    "object": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(type=openapi.TYPE_STRING, example="author"),
                            "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/{author_id}"),
                            "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com"),
                            "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="Author's Display Name"),
                            "github": openapi.Schema(type=openapi.TYPE_STRING, example="http://github.com/author"),
                            "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/author.jpg"),
                            "page": openapi.Schema(type=openapi.TYPE_STRING, example="http://nodeaaaa/authors/author")
                        }
                    )
                }
            )
        ),
        400: "Invalid request data",
        403: "Insufficient permissions",
        404: "Author not found"
    }
)

@ensure_csrf_cookie
@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def follow(request, author_id):
    
    author_uid = request.user.uid
    follow_requests = Follow.objects.filter(following=request.user, status='pending')
    serializer = FollowSerializer(follow_requests, many=True)
    context = {
        'follow_requests': serializer.data
    }
    return render(request, 'socialnetwork/follow_request.html', context)

@swagger_auto_schema(
    method='get',
    operation_description="Render the registration page for authors.",
    
    responses={
        200: "Registration page rendered successfully.",
        403: "Access forbidden.",
    }
)

@swagger_auto_schema(
    method='post',
    operation_description="Register a new author in the system, save the account, and sync their GitHub activity.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, example="john@example.com"),
            "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
            "github": openapi.Schema(type=openapi.TYPE_STRING, example="http://github.com/johndoe"),
            "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/johndoe.jpg"),
            "bio": openapi.Schema(type=openapi.TYPE_STRING, example="Software developer and blogger"),
            "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com")
        },
        required=["email", "displayName"]
    ),
    responses={
        200: "Registration page rendered",
        302: "Redirected to login page on successful registration.",
        400: "Invalid registration data.",
        403: "Insufficient permissions or failed GitHub synchronization."
    }
)

@api_view(['GET','POST'])
def register(request):
    
    if request.method == 'POST':
        form = AuthorCreationForm(request.POST, request.FILES)
        if form.is_valid():
            author = form.save(commit=False)
            author.host = request.build_absolute_uri('/api/')
            author.is_active = False  # Wait for admin approval
            author.save()

            # Sync GitHub activity for the newly created author
            github_sync_result = sync_github_activity(author)

            if 'error' in github_sync_result:
                messages.error(request, github_sync_result['error'])
            else:
                messages.success(request, github_sync_result['message'])

            messages.success(request, 'Your account has been created and is pending approval.')

            # Logout any session to ensure the user is treated as unauthenticated
            logout(request)

            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = AuthorCreationForm()

    return render(request, 'registration/register.html', {'form': form})
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve the profile page for a specific author, including their details and posts.",
    manual_parameters=[
        openapi.Parameter(
            'author_id',
            openapi.IN_PATH,
            description="Unique ID of the author whose profile is to be viewed.",
            type=openapi.TYPE_STRING,
            required=True,
            example="12345"
        )
    ],
   responses={
        200: openapi.Response(
            description="Author's Profile Page",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type="author"),
                    "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/<uuid>"),
                    "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com"),
                    "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
                    "github": openapi.Schema(type=openapi.TYPE_STRING, example="http://github.com/johndoe"),
                    "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/johndoe.jpg"),
                    "page": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/<uuid>"),    
                }
            )
        ),
        404: "Author not found."
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Update the profile information for a specific author.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "email": openapi.Schema(type=openapi.TYPE_STRING, example="john@example.com"),
            "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
            "github": openapi.Schema(type=openapi.TYPE_STRING, example="http://github.com/johndoe"),
            "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/johndoe.jpg"),
           "github": openapi.Schema(type=openapi.TYPE_STRING, example="http://github.com/johndoe"),
            "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/johndoe.jpg"),
            "page": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/<uuid>"),
        },
        required=["email", "displayName"]
    ),
    responses={
        302: "Successfully updated the profile (redirect to the same profile page).",
        404: "Author not found.",
        400: "Invalid request data (form errors)."
    }
)
@api_view(['GET','POST'])
@login_required
def profile(request, author_id):
    
    author = get_object_or_404(Author, uid=author_id)

    # Fetch GitHub activity for the author if a GitHub URL is provided
    github_activity = None
    github_posts = []
    if author.github:  # Check if GitHub URL is provided
        github_activity = fetch_github_activity(author.github, event_type_filter=['CreateEvent'])

        # Convert GitHub activities into a simplified format similar to posts
        if github_activity:
            for activity in github_activity:
                post_title = f"GitHub Activity: {activity['type']}"

                # Handle different GitHub activity types
                if activity['type'] == 'PushEvent':
                    post_content = f"User pushed to {activity['repo']['name']}"

                elif activity['type'] == 'CreateEvent':
                    post_content = f"User created {activity['payload']['ref_type']} '{activity['payload']['ref']}' in {activity['repo']['name']}"

                elif activity['type'] == 'ForkEvent':
                    post_content = f"User forked {activity['repo']['name']} to {activity['payload']['forkee']['full_name']}"

                elif activity['type'] == 'WatchEvent':
                    post_content = f"User starred {activity['repo']['name']}"

                elif activity['type'] == 'PullRequestEvent':
                    post_content = f"User {activity['payload']['action']} a pull request in {activity['repo']['name']}"

                elif activity['type'] == 'IssueCommentEvent':
                    post_content = f"User commented on an issue in {activity['repo']['name']}"

                elif activity['type'] == 'IssuesEvent':
                    post_content = f"User {activity['payload']['action']} an issue in {activity['repo']['name']}"

                elif activity['type'] == 'DeleteEvent':
                    post_content = f"User deleted {activity['payload']['ref_type']} '{activity['payload']['ref']}' in {activity['repo']['name']}"

                elif activity['type'] == 'PullRequestReviewEvent':
                    post_content = f"User submitted a pull request review in {activity['repo']['name']}"

                elif activity['type'] == 'ReleaseEvent':
                    post_content = f"User published a release in {activity['repo']['name']}"

                # Convert GitHub activity created_at to timezone-aware datetime
                activity_created_at = datetime.strptime(activity['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                activity_created_at = timezone.make_aware(activity_created_at, dt_timezone.utc)

                # Use a dict-like structure to simulate a Post object
                github_posts.append({
                    'title': post_title,
                    'content': post_content,
                    'published_at': activity_created_at,  # Converted to timezone-aware datetime
                    'is_github_activity': True,  # Flag to differentiate GitHub posts
                    'activity_avatar': activity['actor']['avatar_url'],
                })

    # Fetch public posts for the author
    public_posts = Post.objects.filter(author=author, visibility=Post.PUBLIC_VISIBILITY)


    reposts = Repost.objects.filter(reposter=author)
    reposts_info = []   #dictionaries containing the post api object and date reposted
    for repost in reposts:
        result = requests.get(repost.post_url)  #TODO filter out unlisted etc.
        if result.status_code < 400:
            info = {"type":"repost","post":result.json(),"published_at":repost.published_at}
            reposts_info.append(info)
    
    # Combine GitHub posts and public posts
    combined_posts = sorted(
        chain(public_posts, github_posts, reposts_info), 
        key=lambda x: x['published_at'] if isinstance(x, dict) else x.published_at, 
        reverse=True
    )

    # Check if the logged-in user is following the profile author
    is_following = Follow.objects.filter(follower=request.user, following=author, status='accepted').exists()
    has_requested = Follow.objects.filter(follower=request.user, following=author, status='pending').exists()

    if request.method == 'POST':
        form = AuthorProfileForm(request.POST, request.FILES, instance=author)
        if form.is_valid():
            form.save()
            author.save()   #form.save() doesn't properly save the pfp url for whatever reason so call author.save() to fix that
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile', author_id=author.uid)
    else:
        form = AuthorProfileForm(instance=author)

    context = {
        'author': author,
        'form': form,
        'is_following': is_following,
        'has_requested': has_requested,
        'combined_posts': combined_posts,  # Combined posts to be displayed
    }

    return render(request, 'authors/profile.html', context)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve the form for creating a new post for a specific author.",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="Unique ID of the author creating the post.",
            type=openapi.TYPE_STRING,
            required=True,
            example="12345"
        )
    ],
    responses={
        200: "Successfully retrieved the form for creating a new post.",
        404: "Author not found."
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Create a new post for a specific author.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": openapi.Schema(type=openapi.TYPE_STRING, example="My New Post"),
            "content": openapi.Schema(type=openapi.TYPE_STRING, example="This is the content of my new post."),
            "tags": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), example=["tag1", "tag2"]),
            "is_published": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
        },
        required=["title", "content"]
    ),
    responses={
        201: "Successfully created the new post.",
        404: "Author not found.",
        400: "Invalid request data (form errors)."
    }
)

# for adding new posts through the web UI
@api_view(['POST','GET'])
@login_required
def new_post(request, author_uid):
    if request.method == 'POST':
        data = request.POST.copy()  # Copy POST data
        data.update(request.FILES)  # Include FILES data
            # Handle the content field based on contentType
        content_type = data.get('contentType')
        if content_type in ['application/base64', 'image/png;base64', 'image/jpeg;base64']:
            # Use the image_content field for image content
            data['content'] = data.get('image_content', '')
        else:
            # Use the text content field for text content
            data['content'] = data.get('content', '')

        serializer = PostSerializer(data=data)
        if serializer.is_valid():
            data = serializer.validated_data
            author = get_object_or_404(Author, uid=request.user.uid)
            p = Post(
                host=request.get_host(),
                title=data.get("title"),
                author=author,
                description=data.get("description"),
                content_type=data.get("content_type"),
                content=data.get("content"),
                visibility=data.get("visibility"),
                image=data.get("image"),
            )
            p.save()
            push_post_to_inboxes(p)
            return redirect('home')
        else:
            return render(request, 'posts/create-post.html', {
                'errors': serializer.errors,
                'author_uid': request.user.uid,
            })
    else:
        return render(request, 'posts/create-post.html', {'author_uid': request.user.uid})
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve the image for a specific post by a specific author.",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="Unique ID of the author.",
            type=openapi.TYPE_STRING,
            required=True,
            example="12345"
        ),
        openapi.Parameter(
            'post_uid',
            openapi.IN_PATH,
            description="Unique ID of the post.",
            type=openapi.TYPE_STRING,
            required=True,
            example="67890"
        )
    ],
    responses={
        200: "Successfully retrieved the post image.",
        404: "Post or author not found."
    }
)


@swagger_auto_schema(
    method='post',
    operation_description="Upload an image for a specific author.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "image": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY, description="Image file to upload.")
        },
        required=["image"]
    ),
    responses={
        201: "Successfully uploaded the image and the url of the image.",
        404: "Author not found.",
        400: "Invalid request data (form errors)."
    }
)
@api_view(['GET', 'POST'])
@login_required
def upload_image(request, author_uid):
    """
    Upload an Image as an Unlisted Post

    **HTTP Method**: POST (for image uploads) / GET (for displaying the upload form)

    **When to use**:
    - To allow authenticated authors to upload an image as a post.
    - For creating unlisted posts containing images.

    **Endpoint**: POST /authors/{author_uid}/upload_image

    **Request Parameters**:
    - author_uid (str): The unique ID of the author uploading the image.

    **Request Body**:
    - image (file): The image file to be uploaded.

    **Returns**:
    - On success: A JSON response containing the URL of the uploaded image.
    - On failure: An error message if no image is uploaded.

 

    **Example Request**:
    - POST /authors/12345/upload_image
      ```json
      {
          "image": "binary image file here"
      }
      ```

    **Response Codes**:
    - 200: Successfully uploaded the image.
    - 400: No image uploaded or invalid request.
    """
    if request.method == 'POST':
        image_file = request.FILES.get('image')
        if image_file:
            # Save the image as an unlisted post
            p = Post(
                host=request.get_host(),
                title=image_file.name,
                author=request.user,
                description='',
                content_type='image/png;base64' if image_file.content_type == 'image/png' else 'image/jpeg;base64',
                visibility=Post.UNLISTED_VISIBILITY,
                content='',
                image=image_file
            )
            p.save()
            # Provide the full image URL to the user
            image_url = request.build_absolute_uri(p.image.url)
            return JsonResponse({'image_url': image_url})
        else:
            return JsonResponse({'error': 'No image uploaded'}, status=400)
    else:
        return render(request, 'posts/upload_image.html', {'author_uid': author_uid})

def are_friends(user1, user2):
    """
    Check if Two Users Are Friends

    **HTTP Method**: GET

    **When to use**:
    - To determine if two users have a mutual follow relationship, indicating they are friends.

    **Request Parameters**:
    - user1 (User): The first user object to check friendship for.
    - user2 (User): The second user object to check friendship for.

    **Returns**:
    - bool: True if the two users are friends (mutual follows), False otherwise.

    **Field Descriptions**:
    - user1_follows_user2: Boolean indicating if user1 follows user2 with an accepted friendship status.
    - user2_follows_user1: Boolean indicating if user2 follows user1 with an accepted friendship status.


    **Response Codes**:
    - 200: Successfully retrieved friendship status.
    """
    user1_follows_user2 = Follow.objects.filter(follower=user1, following=user2, status='accepted').exists()
    user2_follows_user1 = Follow.objects.filter(follower=user2, following=user1, status='accepted').exists()
    return user1_follows_user2 and user2_follows_user1


@swagger_auto_schema(
    method='put',
    operation_description="Update an existing post in the stream for the logged-in user.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "post_id": openapi.Schema(type=openapi.TYPE_STRING, example="post_id"),
            "title": openapi.Schema(type=openapi.TYPE_STRING, example="Updated Stream Post"),
            "content": openapi.Schema(type=openapi.TYPE_STRING, example="This is the updated content of the stream post."),
            "tags": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), example=["tag1", "tag2"]),
            "is_published": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
        },
        required=["post_id", "title", "content"]
    ),
    responses={
        200: "Successfully updated the post in the stream.",
        401: "Unauthorized access.",
        404: "Post not found.",
        400: "Invalid request data (form errors)."
    }
)
@api_view(['GET','POST', 'PUT'])
@login_required
def view_stream(request):
    """
    View stream of currently logged in user.

    **HTTP Method**: GET

    **Description**: 
    Retrieves and renders a stream of posts for the currently logged-in user,
    ensuring that visibility restrictions are honored.

    **Args**:
        request (Request): The HTTP request object.

    **Returns**:
        TemplateResponse: Renders the view-posts.html template with the stream of posts.

    **Field Descriptions**:
    - posts: A list of posts visible to the user, formatted for rendering.
    - post_objects: All posts retrieved from the database.
    
    **Example Usage**:
    - Accessed by the logged-in user to view their personalized feed.

    **Response Codes**:
    - 200: Successfully rendered the stream of posts.
    - 403: Access denied if user is not logged in.
    """

    user = request.user
    posts = []

    # Fetch posts visible to the logged-in user
    post_objects = Post.objects.filter(
        visibility__in=[Post.PUBLIC_VISIBILITY, Post.FRIENDS_VISIBILITY, Post.UNLISTED_VISIBILITY]
    )

    for post in post_objects:
        author = post.author

        # Skip posts with visibility restrictions
        if author != user:
            if post.visibility == Post.FRIENDS_VISIBILITY and not are_friends(author, user):
                continue
            elif post.visibility == Post.UNLISTED_VISIBILITY and not Follow.objects.filter(follower=user,following=author,status='accepted').exists():
                continue

        comments_count = Comment.objects.filter(post=post.id).count()

        posts.append({
            "title": post.title,
            "description": post.description,
            "content_type": post.content_type,
            "content": post.content,
            "image": post.image.url if post.image else None,
            "published_at": post.published_at,
            "author": {
                "uid": post.author.uid,
                "display_name": post.author.display_name,
                "profile_image": post.author.profile_image if post.author.profile_image else None,
            },
            "uid": post.uid,
            "id": post.id,
            "likes_count": post.likes.count if post.likes else 0,
            "comments_count": comments_count,
            "date": post.published_at,
            "is_github_activity": False,
        })

    # Fetch GitHub posts from all authors
    github_posts = []
    authors_with_github = Author.objects.exclude(github=None).exclude(github="")

    for author in authors_with_github:
        github_activities = fetch_github_activity(author.github, event_type_filter=['CreateEvent'])


        if github_activities:
            for activity in github_activities:
                # if activity['type'] == 'CreateEvent':  # Filter for CreateEvent only
                activity_created_at = datetime.strptime(activity['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                activity_created_at = timezone.make_aware(activity_created_at, dt_timezone.utc)

                github_posts.append({
                    "title": f"GitHub Activity: {activity['type']}",
                    "description": activity.get('payload', {}).get('ref', ''),
                    "content_type": "text/plain",
                    "content": activity.get('repo', {}).get('name', ''),
                    "image": activity['actor']['avatar_url'] if 'actor' in activity else None,
                    "published_at": activity_created_at,
                    "author": {
                        "uid": str(author.uid),
                        "display_name": author.display_name,
                        "profile_image": author.profile_image,
                        "github": author.github,
                    },
                    "uid": f"github-{activity['id']}",
                    "id": f"github-{activity['id']}",
                    "likes_count": 0,
                    "comments_count": 0,
                    "date": activity_created_at,
                    "is_github_activity": True,
                })

    # Combine posts
    combined_posts = sorted(
        chain(posts, github_posts),
        key=lambda x: x.get("date", timezone.now()),
        reverse=True
    )

    return render(request, "posts/view-posts.html", {"page_title": "Stream", "posts": combined_posts})
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a list of posts.",
    responses={
        200: "Successfully rendered public posts.",
        404: "Posts not found."
    }
)

@api_view(['GET','POST'])
def view_posts(request):
    """
    View all public posts available to the node.

    **HTTP Method**: GET

    **Description**: 
    Retrieves and renders all public posts, ensuring only publicly visible content is displayed.

    **Args**:
        request (Request): The HTTP request object.

    **Returns**:
        TemplateResponse: Renders the view-posts.html template with public posts.

    **Field Descriptions**:
    - posts: A list of public posts formatted for rendering.
    - post_objects: All public posts retrieved from the database.
    
    **Example Usage**:
    - Accessed by any user to view posts that are publicly available.

    **Response Codes**:
    - 200: Successfully rendered public posts.
    """

    """
    View all public posts available to the node, including GitHub activities.
    """
    posts = []
    post_objects = Post.objects.filter(visibility=Post.PUBLIC_VISIBILITY)

    for post in post_objects:
        comments_count = Comment.objects.filter(post=post.id).count()

        posts.append({
            "title": post.title,
            "description": post.description,
            "content_type": post.content_type,
            "content": post.content,
            "image": post.image.url if post.image else None,
            "published_at": post.published_at,
            "author": {
                "uid": str(post.author.uid),
                "display_name": post.author.display_name,
                "profile_image": post.author.profile_image if post.author.profile_image else None,
            },
            "uid": str(post.uid),
            "id": str(post.id),
            "likes_count": post.likes.count if post.likes else 0,
            "comments_count": comments_count,
            "date": post.published_at,
            "is_github_activity": False,
        })

    # Fetch GitHub posts
    github_posts = []
    authors_with_github = Author.objects.exclude(github=None).exclude(github="")

    for author in authors_with_github:
        github_activities = fetch_github_activity(author.github, event_type_filter=['CreateEvent'])

        if github_activities:
            for activity in github_activities:
                # Parse GitHub activity creation time
                activity_created_at = datetime.strptime(activity['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                activity_created_at = timezone.make_aware(activity_created_at, dt_timezone.utc)

                github_posts.append({
                    "title": f"GitHub Activity: {activity['type']}",
                    "description": activity.get('payload', {}).get('ref', ''),
                    "content_type": "text/plain",
                    "content": activity.get('repo', {}).get('name', ''),
                    "image": activity['actor']['avatar_url'] if 'actor' in activity else None,
                    "published_at": activity_created_at,
                    "author": {
                        "uid": str(author.uid),
                        "display_name": author.display_name,
                        "profile_image": author.profile_image,
                        "github": author.github,  # Add GitHub URL here
                    },
                    "uid": f"github-{activity['id']}",
                    "id": f"github-{activity['id']}",
                    "likes_count": 0,
                    "comments_count": 0,
                    "date": activity_created_at,
                    "is_github_activity": True,
                })


    # Combine posts
    combined_posts = sorted(
        chain(posts, github_posts),
        key=lambda x: x.get("date", timezone.now()),
        reverse=True
    )

    return render(request, "posts/view-posts.html", {"page_title": "Public Posts", "posts": combined_posts})
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve and render a specific post page, ensuring the user has access based on the post's visibility.",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="Unique ID of the post's author.",
            type=openapi.TYPE_STRING,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174111"
        ),
        openapi.Parameter(
            'post_uid',
            openapi.IN_PATH,
            description="Unique ID of the post.",
            type=openapi.TYPE_STRING,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174000"
        )
    ],
   responses={
        200: openapi.Response(
            description="Successfully retrieved post",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="post", 
                        description="The type of the object, which is always 'post'"
                    ),
                    "title": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="Hello", 
                        description="Title of the post"
                    ),
                    "id": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="/authors/example-author-id/posts/example-post-id",
                        description="Unique identifier for the post"
                    ),
                    "page": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="/authors/example-author-id/posts/example-post-id",
                        description="URL to access the post"
                    ),
                    "description": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="bye", 
                        description="Brief description of the post"
                    ),
                    "contentType": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="text/plain", 
                        description="Content type of the post"
                    ),
                    "content": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="Hello", 
                        description="Main body of the post"
                    ),
                    "visibility": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="PUBLIC", 
                        description="Visibility level of the post"
                    ),
                    "author": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="author", 
                                description="Type of the object, which is 'author'"
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/",
                                description="Unique identifier for the author"
                            ),
                            "host": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="example.com", 
                                description="Host URL of the author"
                            ),
                            "displayName": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="example_display_name", 
                                description="Display name of the author"
                            ),
                            "github": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="https://github.com/example-user", 
                                description="GitHub profile of the author"
                            ),
                            "profileImage": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="https://example.com/profile-image.jpg", 
                                description="Profile image of the author"
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/",
                                description="URL to access the author's page"
                            ),
                        }
                    ),
                    "comments": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="comments", 
                                description="Type of the object, which is 'comments'"
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/comments",
                                description="URL to access the comments for this post"
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/comments",
                                description="Unique identifier for the comments section"
                            ),
                            "page_number": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=1, 
                                description="Current page number of comments"
                            ),
                            "size": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=5, 
                                description="Number of comments per page"
                            ),
                            "count": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=0, 
                                description="Total number of comments"
                            ),
                            "src": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                example=[], 
                                description="Array of comment objects"
                            ),
                        }
                    ),
                    "likes": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="likes", 
                                description="Type of the object, which is 'likes'"
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/likes",
                                description="URL to access the likes for this post"
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/likes",
                                description="Unique identifier for the likes section"
                            ),
                            "page_number": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=1, 
                                description="Current page number of likes"
                            ),
                            "size": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=5, 
                                description="Number of likes per page"
                            ),
                            "count": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=0, 
                                description="Total number of likes"
                            ),
                            "src": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                example=[], 
                                description="Array of like objects"
                            ),
                        }
                    ),
                    "likes_count": openapi.Schema(
                        type=openapi.TYPE_INTEGER, 
                        example=0, 
                        description="Total number of likes for this post"
                    ),
                    "comments_count": openapi.Schema(
                        type=openapi.TYPE_INTEGER, 
                        example=0, 
                        description="Total number of comments for this post"
                    ),
                    "published": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="2024-11-23T22:14:12.093506Z", 
                        description="Timestamp when the post was published"
                    ),
                }
            )
        ),
        404: "Post not found.",
        302: "Redirects if the user does not have access."
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Submit data to view a specific post page, ensuring the user has access based on the post's visibility.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "author_uid": openapi.Schema(type=openapi.TYPE_STRING, example="123e4567-e89b-12d3-a456-426614174111"),
            "post_uid": openapi.Schema(type=openapi.TYPE_STRING, example="123e4567-e89b-12d3-a456-426614174000")
        },
        required=["author_uid", "post_uid"]
    ),
    responses={
        200: "Successfully rendered the post page.",
        404: "Post not found.",
        302: "Redirects if the user does not have access."
    }
)
@api_view(['GET','POST'])
def view_post_page(request, author_uid, post_uid):
    """
    Renders the UI for viewing the page of an existing post.

    **HTTP Method**: GET

    **Description**: 
    Retrieves and renders a specific post page, ensuring the user has access
    based on the post's visibility.

    **Args**:
        request (Request): The HTTP request object.
        author_uid: The unique ID of the post's author.
        post_uid: The unique ID of the post.

    **Returns**:
        TemplateResponse: Renders the post-page.html template with the requested post.

    **Field Descriptions**:
    - post: The post object being accessed.

    **Example Usage**:
    - Accessed by users to view a specific post.

    **Example of `post` Object**:
    ```json
    {
        "uid": "123e4567-e89b-12d3-a456-426614174000",
        "author": {
            "uid": "123e4567-e89b-12d3-a456-426614174111",
            "username": "john_doe",
            "display_name": "John Doe",
            "profile_picture_url": "/media/profiles/john_doe.jpg"
        },
        "title": "My First Post",
        "content": "This is the content of the post.",
        "content_type": "text/plain",
        "visibility": "PUBLIC",
        "published_at": "2024-10-01T14:30:00Z",
        "image": "/media/posts/my-first-post.jpg",
        "page": "/posts/123e4567-e89b-12d3-a456-426614174000/"
    }
    ```

    **Response Codes**:
    - 200: Successfully rendered the post page.
    - 404: Post not found.
    - 302: Redirects if the user does not have access.
    """

    post = get_object_or_404(Post, uid=post_uid)

    if post.visibility in [Post.FRIENDS_VISIBILITY, Post.DELETED_VISIBILITY] and request.user.is_anonymous:
        return redirect("home")

    if post.visibility == Post.DELETED_VISIBILITY and not request.user.is_staff:
        return redirect("home")

    if post.visibility == Post.FRIENDS_VISIBILITY and author_uid != request.user.uid:
        author = get_object_or_404(Author, uid=author_uid)
        if not are_friends(request.user, author):
            return redirect("home")


    return render(request, "posts/post-page.html", {"post":post, "author":post.author})
@swagger_auto_schema(
    method='get',
    operation_description="Displays all posts created by the logged-in user, ensuring visibility rules are applied.",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="Unique ID of the post's author.",
            type=openapi.TYPE_STRING,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174111"
        )
    ],
    responses={
        200: openapi.Response(
            description="Successfully retrieved post",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="post", 
                        description="The type of the object, which is always 'post'"
                    ),
                    "title": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="Hello", 
                        description="Title of the post"
                    ),
                    "id": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="/authors/example-author-id/posts/example-post-id",
                        description="Unique identifier for the post"
                    ),
                    "page": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="/authors/example-author-id/posts/example-post-id",
                        description="URL to access the post"
                    ),
                    "description": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="bye", 
                        description="Brief description of the post"
                    ),
                    "contentType": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="text/plain", 
                        description="Content type of the post"
                    ),
                    "content": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="Hello", 
                        description="Main body of the post"
                    ),
                    "visibility": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="PUBLIC", 
                        description="Visibility level of the post"
                    ),
                    "author": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="author", 
                                description="Type of the object, which is 'author'"
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/",
                                description="Unique identifier for the author"
                            ),
                            "host": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="example.com", 
                                description="Host URL of the author"
                            ),
                            "displayName": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="example_display_name", 
                                description="Display name of the author"
                            ),
                            "github": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="https://github.com/example-user", 
                                description="GitHub profile of the author"
                            ),
                            "profileImage": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="https://example.com/profile-image.jpg", 
                                description="Profile image of the author"
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/",
                                description="URL to access the author's page"
                            ),
                        }
                    ),
                    "comments": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="comments", 
                                description="Type of the object, which is 'comments'"
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/comments",
                                description="URL to access the comments for this post"
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/comments",
                                description="Unique identifier for the comments section"
                            ),
                            "page_number": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=1, 
                                description="Current page number of comments"
                            ),
                            "size": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=5, 
                                description="Number of comments per page"
                            ),
                            "count": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=0, 
                                description="Total number of comments"
                            ),
                            "src": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                example=[], 
                                description="Array of comment objects"
                            ),
                        }
                    ),
                    "likes": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="likes", 
                                description="Type of the object, which is 'likes'"
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/likes",
                                description="URL to access the likes for this post"
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/likes",
                                description="Unique identifier for the likes section"
                            ),
                            "page_number": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=1, 
                                description="Current page number of likes"
                            ),
                            "size": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=5, 
                                description="Number of likes per page"
                            ),
                            "count": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=0, 
                                description="Total number of likes"
                            ),
                            "src": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                example=[], 
                                description="Array of like objects"
                            ),
                        }
                    ),
                    "likes_count": openapi.Schema(
                        type=openapi.TYPE_INTEGER, 
                        example=0, 
                        description="Total number of likes for this post"
                    ),
                    "comments_count": openapi.Schema(
                        type=openapi.TYPE_INTEGER, 
                        example=0, 
                        description="Total number of comments for this post"
                    ),
                    "published": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="2024-11-23T22:14:12.093506Z", 
                        description="Timestamp when the post was published"
                    ),
                }
            )
        ),
        403: "Access denied if the user tries to view someone else's posts."
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Create a new post for the logged-in user.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": openapi.Schema(type=openapi.TYPE_STRING, example="New Post"),
            "content": openapi.Schema(type=openapi.TYPE_STRING, example="This is the content of the new post."),
            "tags": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), example=["tag1", "tag2"]),
            "is_published": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True)
        },
        required=["title", "content"]
    ),
   responses={
        200: openapi.Response(
            description="Successfully retrieved post",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="post", 
                        description="The type of the object, which is always 'post'"
                    ),
                    "title": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="Hello", 
                        description="Title of the post"
                    ),
                    "id": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="/authors/example-author-id/posts/example-post-id",
                        description="Unique identifier for the post"
                    ),
                    "page": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="/authors/example-author-id/posts/example-post-id",
                        description="URL to access the post"
                    ),
                    "description": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="bye", 
                        description="Brief description of the post"
                    ),
                    "contentType": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="text/plain", 
                        description="Content type of the post"
                    ),
                    "content": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="Hello", 
                        description="Main body of the post"
                    ),
                    "visibility": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="PUBLIC", 
                        description="Visibility level of the post"
                    ),
                    "author": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="author", 
                                description="Type of the object, which is 'author'"
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/",
                                description="Unique identifier for the author"
                            ),
                            "host": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="example.com", 
                                description="Host URL of the author"
                            ),
                            "displayName": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="example_display_name", 
                                description="Display name of the author"
                            ),
                            "github": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="https://github.com/example-user", 
                                description="GitHub profile of the author"
                            ),
                            "profileImage": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="https://example.com/profile-image.jpg", 
                                description="Profile image of the author"
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/",
                                description="URL to access the author's page"
                            ),
                        }
                    ),
                    "comments": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="comments", 
                                description="Type of the object, which is 'comments'"
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/comments",
                                description="URL to access the comments for this post"
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/comments",
                                description="Unique identifier for the comments section"
                            ),
                            "page_number": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=1, 
                                description="Current page number of comments"
                            ),
                            "size": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=5, 
                                description="Number of comments per page"
                            ),
                            "count": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=0, 
                                description="Total number of comments"
                            ),
                            "src": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                example=[], 
                                description="Array of comment objects"
                            ),
                        }
                    ),
                    "likes": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="likes", 
                                description="Type of the object, which is 'likes'"
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/likes",
                                description="URL to access the likes for this post"
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                example="/authors/example-author-id/posts/example-post-id/likes",
                                description="Unique identifier for the likes section"
                            ),
                            "page_number": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=1, 
                                description="Current page number of likes"
                            ),
                            "size": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=5, 
                                description="Number of likes per page"
                            ),
                            "count": openapi.Schema(
                                type=openapi.TYPE_INTEGER, 
                                example=0, 
                                description="Total number of likes"
                            ),
                            "src": openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT),
                                example=[], 
                                description="Array of like objects"
                            ),
                        }
                    ),
                    "likes_count": openapi.Schema(
                        type=openapi.TYPE_INTEGER, 
                        example=0, 
                        description="Total number of likes for this post"
                    ),
                    "comments_count": openapi.Schema(
                        type=openapi.TYPE_INTEGER, 
                        example=0, 
                        description="Total number of comments for this post"
                    ),
                    "published": openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        example="2024-11-23T22:14:12.093506Z", 
                        description="Timestamp when the post was published"
                    ),
                }
            )
        ),
        400: "Invalid request data (form errors)."
    }
)
@api_view(['GET','POST'])
@login_required
def my_posts(request, author_uid):
    """
    Renders all the posts for a given author.

    **HTTP Method**: GET

    **Description**: 
    Displays all posts created by the logged-in user, ensuring visibility rules are applied.

    **Args**:
        request (Request): The HTTP request object.
        author_uid: The unique ID of the post's author.

    **Returns**:
        TemplateResponse: Renders the my-posts.html template with the author's posts.

    **Field Descriptions**:
    - author: The author object whose posts are being viewed.
    - posts: A list of posts by the author, excluding deleted ones.

    **Example Usage**:
    - Accessed by the author to manage and view their posts.

    **Example of `author` Object**:
    ```json
    {
        "uid": "123e4567-e89b-12d3-a456-426614174111",
        "username": "john_doe",
        "display_name": "John Doe",
        "profile_picture_url": "/media/profiles/john_doe.jpg"
    }
    ```

    **Example of `posts` List**:
    ```json
    [
        {
            "uid": "123e4567-e89b-12d3-a456-426614174000",
            "title": "First Post",
            "content": "This is the content of the first post.",
            "content_type": "text/plain",
            "visibility": "PUBLIC",
            "published_at": "2024-10-01T14:30:00Z",
            "image": "/media/posts/first-post.jpg",
            "page": "/posts/123e4567-e89b-12d3-a456-426614174000/"
        },
        {
            "uid": "223e4567-e89b-12d3-a456-426614174001",
            "title": "Second Post",
            "content": "Content for the second post.",
            "content_type": "text/plain",
            "visibility": "FRIENDS",
            "published_at": "2024-10-02T15:00:00Z",
            "image": "/media/posts/second-post.jpg",
            "page": "/posts/223e4567-e89b-12d3-a456-426614174001/"
        }
    ]
    ```

    **Response Codes**:
    - 200: Successfully rendered the author's posts.
    - 403: Access denied if the user tries to view someone else's posts.
    """

    # Make sure only the author can view their posts
    if author_uid != request.user.uid:
        return HttpResponseRedirect(reverse("profile", kwargs={"author_id": author_uid}))

    author = get_object_or_404(Author, uid=author_uid)

    # Exclude deleted posts
    posts = Post.objects.filter(author=author).exclude(visibility=Post.DELETED_VISIBILITY)

    # If you're a superuser, you might want to see all posts, including deleted ones
    if request.user.is_superuser:
        posts = Post.objects.filter(author=author)

    return render(request, 'posts/my-posts.html', {"posts": posts, "author": author})
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve the form for editing an existing post.",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="Unique ID of the post's author.",
            type=openapi.TYPE_STRING,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174111"
        ),
        openapi.Parameter(
            'post_uid',
            openapi.IN_PATH,
            description="Unique ID of the post.",
            type=openapi.TYPE_STRING,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174000"
        )
    ],
    responses={
        200: "Successfully rendered the edit form.",
        404: "Post not found."
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Submit changes to edit an existing post.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": openapi.Schema(type=openapi.TYPE_STRING, example="Updated Post Title"),
            "content": openapi.Schema(type=openapi.TYPE_STRING, example="This is the updated content of the post Hey Hi Hello."),
            "contentType": openapi.Schema(type=openapi.TYPE_STRING, example="Plain Text"),
            "description": openapi.Schema(type=openapi.TYPE_STRING, example="This is the updated content of the post."),
            "visibility": openapi.Schema(type=openapi.TYPE_STRING, example="PUBLIC"),
        },
        required=["title", "description"]
    ),
    responses={
        302: "Redirected on successful update.",
        404: "Post not found.",
        400: "Invalid request data (form errors)."
    }
)
@swagger_auto_schema(
    method='put',
    operation_description="Update an existing post.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": openapi.Schema(type=openapi.TYPE_STRING, example="Updated Post Title"),
            "content": openapi.Schema(type=openapi.TYPE_STRING, example="This is the updated content of the post Hey Hi Hello."),
            "contentType": openapi.Schema(type=openapi.TYPE_STRING, example="Plain Text"),
            "description": openapi.Schema(type=openapi.TYPE_STRING, example="This is the updated content of the post."),
            "visibility": openapi.Schema(type=openapi.TYPE_STRING, example="PUBLIC"),
        },
        required=["title", "description"]
    ),
    responses={
        200: "Successfully updated the post.",
        404: "Post not found.",
        400: "Invalid request data (form errors)."
    }
)

@api_view(['PUT','GET','POST'])
@login_required
def edit_post(request, author_uid, post_uid):
    """
    Renders the UI for editing an existing post.

    **HTTP Method**: GET, POST

    **Description**: 
    Allows the author to edit a specific post, handling both GET requests for the form and
    POST requests to submit changes.

    **Args**:
        request (Request): The HTTP request object.
        author_uid: The unique ID of the post's author.
        post_uid: The unique ID of the post.

    **Returns**:
        TemplateResponse: Renders the edit-post.html template for GET, or redirects to my_posts on success for POST.

    **Field Descriptions**:
    - post: The post object being edited.
    - serializer: The serializer instance for the post.
    
    **Example Usage**:
    - Accessed by the author to update their existing posts.

    **Response Codes**:
    - 200: Successfully rendered the edit form.
    - 302: Redirected on successful update.
    - 404: Post not found.
    """
    if author_uid != request.user.uid:
        return HttpResponseRedirect(reverse("profile", kwargs={"author_id": author_uid}))

    post = get_object_or_404(Post, uid=post_uid, author__uid=author_uid)

    if request.method == 'POST':
        data = request.POST.copy()
        data.update(request.FILES)

        # Handle the content field based on content_type
        content_type = data.get('content_type')
        if content_type in ['application/base64', 'image/png;base64', 'image/jpeg;base64']:
            data['content'] = data.get('image_content', '')
        else:
            data['content'] = data.get('content', '')

        serializer = PostSerializer1(instance=post, data=data)

        if serializer.is_valid():
            serializer.save()
            push_post_to_inboxes(post)
            return redirect('my_posts', author_uid=author_uid)
        else:
            print("Serializer Errors:", serializer.errors)
            return render(request, 'posts/edit-post.html', {
                'serializer': serializer,
                'author_uid': author_uid,
                'post_uid': post_uid,
                'errors': serializer.errors,
            })

    else:
        serializer = PostSerializer1(instance=post)

    return render(request, 'posts/edit-post.html', {
        'serializer': serializer,
        'author_uid': author_uid,
        'post_uid': post_uid
    })


@swagger_auto_schema(
    method='delete',
    operation_description="Delete an existing post.",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="Unique ID of the post's author.",
            type=openapi.TYPE_STRING,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174111"
        ),
        openapi.Parameter(
            'post_uid',
            openapi.IN_PATH,
            description="Unique ID of the post.",
            type=openapi.TYPE_STRING,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174000"
        )
    ],
    responses={
        200: "Successfully marked the post as deleted.",
        405: "Method not allowed if not a DELETE request."
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Delete an existing post.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "author_uid": openapi.Schema(type=openapi.TYPE_STRING, example="123e4567-e89b-12d3-a456-426614174111"),
            "post_uid": openapi.Schema(type=openapi.TYPE_STRING, example="123e4567-e89b-12d3-a456-426614174000")
        },
        required=["author_uid", "post_uid"]
    ),
    responses={
        200: "Successfully marked the post as deleted.",
        405: "Method not allowed if not a POST request."
    }
)
@swagger_auto_schema(
    method='get',
    operation_description="Retrieve the form for deleting an existing post.",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="Unique ID of the post's author.",
            type=openapi.TYPE_STRING,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174111"
        ),
        openapi.Parameter(
            'post_uid',
            openapi.IN_PATH,
            description="Unique ID of the post.",
            type=openapi.TYPE_STRING,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174000"
        )
    ],
    responses={
        200: "Successfully retrieved the delete form.",
        405: "Method not allowed if not a GET request."
    }
)

@api_view(['DELETE','POST','GET'])
@login_required
def delete_post(request, author_uid, post_uid):
    """
    Delete an existing post.

    **HTTP Method**: POST

    **Description**: 
    Marks a post as deleted, ensuring only the author can perform the action.

    **Args**:
        request (Request): The HTTP request object.
        author_uid: The unique ID of the post's author.
        post_uid: The unique ID of the post.

    **Returns**:
        HttpResponse: Redirects to the author's posts on success, or returns 405 for invalid method.

    **Field Descriptions**:
    - post: The post object being deleted.
    
    **Example Usage**:
    - Accessed by the author to remove their posts.

    **Response Codes**:
    - 200: Successfully marked the post as deleted.
    - 405: Method not allowed if not a POST request.
    """
    if request.method == 'POST':
        # Make sure only the author can delete their posts
        if request.user.uid != author_uid:
            return HttpResponseRedirect(reverse("my_posts", kwargs={"author_uid": author_uid}))

        post = get_object_or_404(Post, uid=post_uid)
        post.visibility = Post.DELETED_VISIBILITY
        post.save()
        push_post_to_inboxes(post)
        return HttpResponseRedirect(reverse("my_posts", kwargs={"author_uid": author_uid}))
    else:
        return HttpResponse(status=405)  # Method Not Allowed

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'  # Adjust this to point to your actual login template

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(self.get_success_url())
        else:
            messages.error(request, 'Please enter a correct email and password.')
            return render(request, self.template_name, {'form': self.get_form(), 'messages': messages.get_messages(request)})  # Add messages to context

    def get_success_url(self):
        return reverse('profile', kwargs={'author_id': self.request.user.uid})

@swagger_auto_schema(
    method='get',
    operation_description="View Incoming Follow Requests. Displays a list of pending follow requests for the currently logged-in user.",
    responses={
        200: "Successfully rendered the list of follow requests."
    }
)
@swagger_auto_schema(
    method='post',
    operation_description="Submit a follow request or respond to a follow request.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={

            
            "type": openapi.Schema(type=openapi.TYPE_STRING, example="follow"),
            "summary": openapi.Schema(type=openapi.TYPE_STRING, example="actor wants to follow object"),
            "actor": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="author"),
                    "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/{actor_id}"),
                    "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com"),
                    "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="Actor's Display Name"),
                    "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/actor.jpg"),
                    "bio": openapi.Schema(type=openapi.TYPE_STRING, example="Actor's biography")
                }
            ),
            "object": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="author"),
                    "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/{author_id}"),
                    "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com"),
                    "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="Author's Display Name"),
                    "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/author.jpg"),
                    "bio": openapi.Schema(type=openapi.TYPE_STRING, example="Author's biography")
                }
            )
        },
        required=["actor", "object", "action"]
    ),
    responses={
        200: "Successfully processed the follow request.",
        400: "Invalid request data (form errors)."
    }
)
@api_view(['GET', 'POST'])
@login_required
def follow_requests_view(request):
    """
    View Incoming Follow Requests

    Displays a list of pending follow requests for the currently logged-in user.

    **HTTP Method**: GET

    **Description**:
    This view provides a list of incoming follow requests, allowing the user to see who has requested to follow them. 
    Each follow request object includes details about the requesting author (`actor`) and the requested author (`object`).

    **Args**:
        request (Request): The HTTP request object.

    **Returns**:
        TemplateResponse: A rendered template displaying:
        - `pending_requests`: List of follow requests with structure:
          ```json
          {
              "type": "follow",
              "summary": "actor wants to follow object",
              "actor": {
                  "type": "author",
                  // The rest of the author object for the author who wants to follow
              },
              "object": {
                  "type": "author",
                  // The rest of the author object for the author they want to follow
              }
          }
          ```
        - `followers`: List of authors who have already been accepted as followers.
        - `authors_with_status`: List of other authors on the platform, including their follow status (accepted or pending) relative to the current user.

    **Example Usage**:
    - Accessed by the user to view their pending follow requests and current followers.

    **Response Codes**:
    - 200: Successfully rendered the list of follow requests.

    **Permissions**:
    - Requires the user to be authenticated (login required).
    """
    user = request.user

    # Determine the local host dynamically from the request
    local_host = request.build_absolute_uri('/api/')

    # Get all pending follow requests where the logged-in user is the 'following' author
    pending_requests = Follow.objects.filter(following=user, status='pending')

    # Get accepted followers
    followers = Follow.objects.filter(following=user, status='accepted').values_list('follower', flat=True)
    follower_authors = Author.objects.filter(uid__in=followers)

    # Get local authors to follow (exclude the current user and remote authors)
    local_authors = Author.objects.filter(host=local_host).exclude(uid=user.uid)
    print(local_host)
    print(f"Local authors: {local_authors}")
    authors_with_status = []
    for author in local_authors:
        existing_follow = Follow.objects.filter(follower=user, following=author).first()
        is_following = existing_follow.status == 'accepted' if existing_follow else False
        has_requested = existing_follow.status == 'pending' if existing_follow else False
        authors_with_status.append({
            'author': author,
            'is_following': is_following,
            'has_requested': has_requested,
        })

    # Fetch authors from remote nodes
    remote_nodes = RemoteNode.objects.all()
    for node in remote_nodes:
        try:
            response = requests.get(
                f"{node.node_url}/api/authors/",
                auth=(node.username, node.password),
                timeout=10
            )
            print(response.json())
            if response.status_code == 200:
                remote_authors = response.json().get('authors', [])
                for remote_author_data in remote_authors:
                    full_id = remote_author_data.get('id')  # Full ID from remote node
                    try:
                        # Extract UUID from the full ID (last part of the URL path)
                        uuid_str = full_id.rstrip('/').split('/')[-1]
                        author_uuid = uuid.UUID(uuid_str)
                    except (IndexError, ValueError) as e:
                        print(f"Failed to parse UUID from {full_id}: {e}")
                        continue

                    # Try to get the author by 'id'
                    author = Author.objects.filter(id=full_id).first()
                    if not author:
                        # Create new author
                        author = Author.objects.create(
                            uid=author_uuid,
                            id=full_id,
                            host=remote_author_data.get('host'),
                            display_name=remote_author_data.get('displayName'),
                            github=remote_author_data.get('github'),
                            profile_image=remote_author_data.get('profileImage'),
                            page=remote_author_data.get('page'),
                            email=remote_author_data.get('email'),
                            bio=remote_author_data.get('bio', ''),
                            is_active=False,  
                            is_staff=False,  # Remote authors are not staff
                            is_remote=True,  # Mark as remote author
                        )
                        print(f"Added remote author to local database: {author}")
                    else:
                        # Update existing author if necessary
                        author.host = remote_author_data.get('host')
                        author.display_name = remote_author_data.get('displayName')
                        author.github = remote_author_data.get('github')
                        author.profile_image = remote_author_data.get('profileImage')
                        author.page = remote_author_data.get('page')
                        author.email = remote_author_data.get('email')
                        author.bio = remote_author_data.get('bio', '')
                        author.save()
                        print(f"Updated existing author in local database: {author.display_name}")

                    # Check follow status
                    is_following = Follow.objects.filter(
                        follower=user,
                        following=author,
                        status='accepted'
                    ).exists()
                    print(f"Is following {author.display_name}: {is_following}")

                    authors_with_status.append({
                        'author': {
                            'id': author.id,  # Keep the full ID for rendering
                            'host': author.host,
                            'display_name': author.display_name,
                            'github': author.github,
                            'profile_image': author.profile_image if author.profile_image else '',
                            'page': author.page,
                            'email': author.email,
                            'bio': author.bio,
                        },
                        'is_following': is_following,
                        'has_requested': False,
                        'credentials': {
                            'username': node.username,
                            'password': node.password,
                        }
                    })
            else:
                print(f"Failed to fetch authors from {node.node_url}. Status Code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching authors from {node.node_url}: {e}")
    context = {
        'pending_requests': pending_requests,
        'followers': follower_authors,
        'authors_with_status': authors_with_status,
    }
    return render(request, 'authors/follow_requests.html', context)


@swagger_auto_schema(
    method='post',
    operation_description="Accept a follow request.",
    manual_parameters=[
        openapi.Parameter(
            'follow_id',
            openapi.IN_PATH,
            description="ID of the follow request to accept.",
            type=openapi.TYPE_STRING,
            required=True,
            example="12345"
        )
    ],
    responses={
        200: openapi.Response(description="Follow request accepted successfully."),
        404: openapi.Response(description="Follow request not found."),
        400: openapi.Response(description="Invalid request data.")
    }
)
@swagger_auto_schema(
    method='get',
    operation_description="Accept a follow request.",
    manual_parameters=[
        openapi.Parameter(
            'follow_id',
            openapi.IN_PATH,
            description="ID of the follow request to accept.",
            type=openapi.TYPE_STRING,
            required=True,
            example="12345"
        )
    ],
    responses={
        200: openapi.Response(description="Follow request accepted successfully."),
        404: openapi.Response(description="Follow request not found."),
        400: openapi.Response(description="Invalid request data.")
    }
)
@api_view(['POST','GET'])
@permission_classes([IsAuthenticated])
def accept_follow_request(request, follow_id):
    follow_request = get_object_or_404(Follow, id=follow_id)

    # Ensure the current user is the intended recipient
    if request.user != follow_request.following:
        return Response({'error': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

    follow_request.status = 'accepted'
    follow_request.save()

    return Response({'message': 'Follow request accepted.'}, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='post',
    operation_description="Reject a follow request.",
    manual_parameters=[
        openapi.Parameter(
            'follow_id',
            openapi.IN_PATH,
            description="ID of the follow request to reject.",
            type=openapi.TYPE_STRING,
            required=True,
            example="12345"
        )
    ],
    responses={
        200: openapi.Response(description="Follow request rejected successfully."),
        404: openapi.Response(description="Follow request not found."),
        400: openapi.Response(description="Invalid request data.")
    }
)
@swagger_auto_schema(
    method='get',
    operation_description="Reject a follow request.",
    manual_parameters=[
        openapi.Parameter(
            'follow_id',
            openapi.IN_PATH,
            description="ID of the follow request to reject.",
            type=openapi.TYPE_STRING,
            required=True,
            example="12345"
        )
    ],
    responses={
        200: openapi.Response(description="Follow request rejected successfully."),
        404: openapi.Response(description="Follow request not found."),
        400: openapi.Response(description="Invalid request data.")
    }
)
@api_view(['POST','GET'])
@permission_classes([IsAuthenticated])
def reject_follow_request(request, follow_id):
    follow_request = get_object_or_404(Follow, id=follow_id)

    # Ensure the current user is the intended recipient
    if request.user != follow_request.following:
        return Response({'error': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

    #follow_request.status = 'rejected'
    #follow_request.save()
    follow_request.delete()

    return Response({'message': 'Follow request rejected.'}, status=status.HTTP_200_OK)