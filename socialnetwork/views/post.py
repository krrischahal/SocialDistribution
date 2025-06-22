from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.http import HttpRequest, HttpResponse
from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.decorators import login_required
from rest_framework.parsers import FormParser, MultiPartParser
from ..serializers import PostSerializer
from ..models import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import base64
from django.core.files.base import ContentFile


import requests
from urllib.parse import unquote
from ..utils import are_friends

#helper function for pushing to inboxes after a post is made, updated, or deleted
def push_post_to_inboxes(post):
    serializer = PostSerializer(post)
    post_data = serializer.data

    author_followers = Follow.objects.filter(following=post.author, status='accepted')
    for follow in author_followers:
        if not follow.follower.is_remote:
            print("local follower")
            continue

        follower_inbox = follow.follower.id.rstrip("/") + "/inbox"
        node_url = follow.follower.get_host_no_api()
        node = RemoteNode.objects.filter(node_url=node_url)
        if not node.exists():
            print(f"{node_url} does not exist")
            continue

        node = node.get()

        try:
            print(f"send post to {node_url}")
            response = requests.post(
                follower_inbox,
                json=post_data,
                auth=(node.username, node.password),
                timeout=10
            )
            if response.status_code not in [200, 201]:
                print(post_data)
                print(f"Failed to push post to {follower_inbox}: {response.status_code}")
        except Exception as e:
            print(f"Exception while pushing post to {follower_inbox}: {e}")

@swagger_auto_schema(
    method='post',
    operation_description="Create a new post for an author.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "type": openapi.Schema(type=openapi.TYPE_STRING, example="post", description="The type of the object, which is always 'post'"),
            "title": openapi.Schema(type=openapi.TYPE_STRING, description="Title of the post", example="My first post"),
            "id": openapi.Schema(type=openapi.TYPE_STRING, description="Unique identifier of the post URL", example="http://example.com/authors/1/posts/2"),
            "description": openapi.Schema(type=openapi.TYPE_STRING, description="Brief description of the post", example="This post is very interesting"),
            "content_type": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Format of the content",
                example="text/plain",
                enum=[
                    "text/markdown",
                    "text/plain",
                    "application/base64",
                    "image/png;base64",
                    "image/jpeg;base64"
                ]
            ),
            "content": openapi.Schema(type=openapi.TYPE_STRING, description="Main body of the post", example="I ate a banana yesterday. It was yummy!"),
            "visibility": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Who can see the post",
                example="PUBLIC",
                enum=["PUBLIC", "UNLISTED", "FRIENDS", "DELETED"]
            ),
            "image": openapi.Schema(type=openapi.TYPE_STRING, format="binary", description="Optional image file associated with the post"),
        },
        required=["title", "content", "content_type", "visibility"]
    ),
    responses={
        201: openapi.Response(
            description="Post created successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="post"),
                    "title": openapi.Schema(type=openapi.TYPE_STRING, example="My first post"),
                    "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/1/posts/2"),
                    "description": openapi.Schema(type=openapi.TYPE_STRING, example="This post is very interesting"),
                    "content_type": openapi.Schema(type=openapi.TYPE_STRING, example="text/plain"),
                    "content": openapi.Schema(type=openapi.TYPE_STRING, example="I ate a banana yesterday. It was yummy!"),
                    "visibility": openapi.Schema(type=openapi.TYPE_STRING, example="PUBLIC"),
                    "image": openapi.Schema(type=openapi.TYPE_STRING, description="URL of the uploaded image, if provided"),
                    "published_at": openapi.Schema(type=openapi.FORMAT_DATETIME, example="2024-11-23T12:34:56Z"),
                }
            )
        ),
        400: "Invalid request data",
        403: "Unauthorized attempt to create post for a different author"
    }
)
@login_required
@api_view(['POST'])
def add_post(request,author_uid):
    client_author_serial = request.user.uid
    author = get_object_or_404(Author, uid=client_author_serial)
    
    if (client_author_serial != author_uid) or author.is_remote:
        return Response(status=status.HTTP_403_FORBIDDEN)

    #turn JSON into dictionary
    serializer = PostSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.data

        host_name = request.get_host()

        p = Post()
        p.host = host_name
        p.title = data.get("title")
        p.author = author
        p.description = data.get("description")
        p.content_type = data.get("contentType")
        p.content = data.get("content")
        p.visibility = data.get("visibility")
        p.save()
        push_post_to_inboxes(p)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_post_image_by_author_and_post(request, author_uid, post_uid):
    # Fetch the post
    post = get_object_or_404(Post, author__uid=author_uid, uid=post_uid)

    if post.content_type in ['image/png;base64', 'image/jpeg;base64', 'application/base64']:
        if post.content:
            try:
                # Decode the base64 image data
                image_data = base64.b64decode(post.content)

                # Determine content type
                if post.content_type == 'image/png;base64':
                    content_type = 'image/png'
                elif post.content_type == 'image/jpeg;base64':
                    content_type = 'image/jpeg'
                else:
                    content_type = 'application/octet-stream'

                response = HttpResponse(image_data, content_type=content_type)
                response['Content-Disposition'] = 'inline; filename="image"'
                return response
            except Exception as e:
                return Response({'detail': 'Error decoding image data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({'detail': 'Image data not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({'detail': 'Not an image post'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_post_image_by_fqid(request, post_fqid):
    # Fetch the post
    post = get_object_or_404(Post, id=post_fqid)

    if post.content_type in ['image/png;base64', 'image/jpeg;base64', 'application/base64']:
        if post.content:
            try:
                # Decode the base64 image data
                image_data = base64.b64decode(post.content)

                # Determine content type
                if post.content_type == 'image/png;base64':
                    content_type = 'image/png'
                elif post.content_type == 'image/jpeg;base64':
                    content_type = 'image/jpeg'
                else:
                    content_type = 'application/octet-stream'

                response = HttpResponse(image_data, content_type=content_type)
                response['Content-Disposition'] = 'inline; filename="image"'
                return response
            except Exception as e:
                return Response({'detail': 'Error decoding image data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            # Fetch image data from remote node
            try:
                # Construct the remote image URL
                remote_image_url = f"{post.id}/image"
                remote_response = requests.get(remote_image_url)
                if remote_response.status_code == 200:
                    content_type = remote_response.headers.get('Content-Type', 'application/octet-stream')
                    return HttpResponse(remote_response.content, content_type=content_type)
                else:
                    return Response({'detail': 'Remote image not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'detail': 'Error fetching remote image'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'detail': 'Not an image post'}, status=status.HTTP_404_NOT_FOUND)


@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a specific post by its UUID.",
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
        403: "Access denied if user lacks permissions to view the post",
        401: "Unauthorized if not logged in",
        404: "Post not found for the provided UUID"
    }
)
@swagger_auto_schema(
    method='delete',
    operation_description="Delete a post by its UUID.",
    responses={
        204: "Post successfully deleted",
        403: "If the user is not the author of the post",
        401: "Unauthorized if not logged in"
    }
)
@swagger_auto_schema(
    method='put',
    operation_description="Update a specific post's details by its UUID.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "title": openapi.Schema(type=openapi.TYPE_STRING, description="Title of the post", example="My updated post"),
            "description": openapi.Schema(type=openapi.TYPE_STRING, description="Brief description of the post", example="Updated description"),
            "content_type": openapi.Schema(type=openapi.TYPE_STRING, description="Type of content", example="text/markdown"),
            "content": openapi.Schema(type=openapi.TYPE_STRING, description="Main body content of the post", example="New content"),
            "visibility": openapi.Schema(type=openapi.TYPE_STRING, description="Visibility level of the post", example="unlisted"),
        },
        required=["title", "content"]
    ),
    responses={
        200: openapi.Response(
            description="Successfully updated post",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="post"),
                    "title": openapi.Schema(type=openapi.TYPE_STRING, example="My updated post"),
                    "description": openapi.Schema(type=openapi.TYPE_STRING, example="Updated description"),
                    "content_type": openapi.Schema(type=openapi.TYPE_STRING, example="text/markdown"),
                    "content": openapi.Schema(type=openapi.TYPE_STRING, example="New content"),
                    "visibility": openapi.Schema(type=openapi.TYPE_STRING, example="unlisted"),
                }
            )
        ),
        400: "Invalid request data",
        403: "Unauthorized attempt to update post for a different author",
        404: "Post not found"
    }
)
@api_view(['GET','DELETE','PUT'])
def access_post(request,author_uid,post_uid):
    post = get_object_or_404(Post, uid=post_uid)

    if request.method == "GET":
        if post.visibility == Post.DELETED_VISIBILITY:
            return Response(status=status.HTTP_403_FORBIDDEN)
        #check if user is logged in and friends with poster
        if post.visibility == Post.FRIENDS_VISIBILITY:
            if request.user.is_authenticated:
                if not are_friends(request.user,post.author):
                    if request.user != post.author:
                        return Response(status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = PostSerializer(post)
        return Response(serializer.data,status=status.HTTP_200_OK)  #TODO implement
    elif request.method == "DELETE":
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        if request.user == post.author:
            post.visibility = Post.DELETED_VISIBILITY
            post.save()
            push_post_to_inboxes(post)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
    elif request.method == "PUT":
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if request.user == post.author:
            #turn JSON into dictionary
            serializer = PostSerializer(data=request.data)
            if serializer.is_valid():
                data = serializer.data

                host_name = request.get_host()
                author_serial = request.user.uid
                author = get_object_or_404(Author, uid=author_serial)

                post.title = data.get("title")
                post.description = data.get("description")
                post.content_type = data.get("content_type")
                post.content = data.get("content")
                post.visibility = data.get("visibility")
                push_post_to_inboxes(post)
                post.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
    else:
        return Response(serializer.data, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@swagger_auto_schema(
    method='get',
    operation_description="Retrieve details of a specific post.",
    responses={
        200: openapi.Response(
            description="Post details retrieved successfully.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="post"),
                    "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/1/posts/2"),
                    "author": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/1"),
                    "title": openapi.Schema(type=openapi.TYPE_STRING, example="Sample Post"),
                    "description": openapi.Schema(type=openapi.TYPE_STRING, example="This is a sample post description."),
                    "content_type": openapi.Schema(type=openapi.TYPE_STRING, example="text/plain"),
                    "content": openapi.Schema(type=openapi.TYPE_STRING, example="This is the post content."),
                    "visibility": openapi.Schema(type=openapi.TYPE_STRING, example="public"),
                    "published": openapi.Schema(type=openapi.TYPE_STRING, example="2024-11-17T10:00:00Z"),
                }
            )
        ),
        404: "Post not found.",
        403: "Forbidden: User lacks permission to view this post.",
    }
)
@api_view(['GET'])
def get_post(request,post_fqid):
    result = requests.get(unquote(post_fqid))
    return Response(result.json(),result.status_code)

@login_required
@api_view(['GET'])
def create_post(request):
    return render(request,"posts/create-post.html",{"author_uid":request.user.uid})


@swagger_auto_schema(
    method='post',
    operation_description="Repost an existing post.",
    request_body=None,
    responses={
        201: openapi.Response(
            description="Post reposted successfully.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="repost"),
                    "original_post": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/1/posts/2"),
                    "author": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/2"),
                    "visibility": openapi.Schema(type=openapi.TYPE_STRING, example="public"),
                    "published": openapi.Schema(type=openapi.TYPE_STRING, example="2024-11-17T10:00:00Z"),
                }
            )
        ),
        404: "Original post not found.",
        403: "Forbidden: User lacks permission to repost this content.",
    }
)
@login_required
@api_view(["POST"])
def repost(request,post_fqid):
    result = requests.get(post_fqid)
    visibility = result.json().get("visibility")
    if visibility != Post.PUBLIC_VISIBILITY:
        return Response(status=status.HTTP_403_FORBIDDEN)

    rp = Repost()
    rp.reposter = request.user
    rp.post_url = unquote(post_fqid)
    rp.save()
    return Response(status=status.HTTP_201_CREATED)