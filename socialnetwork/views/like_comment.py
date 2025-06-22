from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import Post, Comment, Author, Like, Likes
from ..serializers import *
import requests
from django.contrib.auth.decorators import login_required
from ..utils import are_friends

#helper function for pushing to the post/comment a after a like is made
def push_comment_to_inbox(comment):
    #extract ~/api/authors/~ from ~/api/authors/~/posts/~ or ~/api/authors/~/commented/~
    #NOTE: this works with our stuff, but maybe other people's implementations could
    #break it if they don't follow the specifications properly. In that case, the commented out
    #version below could fix it with a few modifications
    author_id = comment.post
    temp = author_id.find("api/authors")
    end_idx = author_id.find("/",temp+12)
    author_id = author_id[:end_idx+1].rstrip("/")
    author_inbox = author_id.rstrip("/") + "/inbox"

    #send like to inboxes
    serializer = CommentSerializer(comment)
    comment_data = serializer.data

    author = Author.objects.filter(id=author_id)
    if author.exists():
        author = author.get()
        if author.is_remote:
            node_url = author.get_host_no_api()
            print(f"Node URL: {node_url}")
            node = RemoteNode.objects.filter(node_url=node_url)
            if node.exists():
                node = node.get()
                try:
                    print(f"inbox: {author_inbox}")
                    response = requests.post(
                        author_inbox,
                        json=comment_data,
                        auth=(node.username, node.password),
                        timeout=10)
                    print(response.status_code)
                    if response.status_code not in [200, 201]:
                        # print(like_data)
                        print(f"Failed to push comment to {node_url}: {response.status_code}")
                except Exception as e:
                    print(e)
            else:
                print(f"{node_url} does not exist")
        else:
            print("local author")
    
    # serializer = CommentSerializer(comment)
    # comment_data = serializer.data
    # print(comment_data)
    # author_followers = Follow.objects.filter(following=comment.author, status='accepted')\

    # for follow in author_followers:
    #     if not follow.follower.is_remote:
    #         continue

    #     follower_inbox = follow.follower.id.rstrip("/") + "/inbox/"
    #     node_url = follow.follower.get_host_no_api()
    #     node = RemoteNode.objects.filter(node_url=node_url)
    #     if not node.exists():
    #         print(node_url)
    #         continue

    #     node = node.get()

    #     try:
    #         response = requests.post(
    #             follower_inbox,
    #             json=comment_data,
    #             auth=(node.username, node.password),
    #             timeout=10
    #         )
    #         if response.status_code not in [200, 201]:
    #             print(f"Failed to push post to {follower_inbox}: {response.status_code}")
    #     except Exception as e:
    #         print(f"Exception while pushing post to {follower_inbox}: {e}")

#helper function for pushing to the post/comment after a like is made
def push_like_to_inbox(like):
    #extract ~/api/authors/~ from ~/api/authors/~/posts/~ or ~/api/authors/~/commented/~
    #NOTE: this works with our stuff, but maybe other people's implementations could
    #break it if they don't follow the specifications properly. In that case, the commented out
    #version below could fix it with a few modifications
    author_id = like.object
    temp = author_id.find("api/authors")
    end_idx = author_id.find("/",temp+12)
    author_id = author_id[:end_idx+1].rstrip("/")
    author_inbox = author_id.rstrip("/") + "/inbox"

    #send like to inboxes
    serializer = LikeSerializer(like)
    like_data = serializer.data
    print(like_data)
    author = Author.objects.filter(id=author_id)
    print(author,author_id,like.object)
    if author.exists():
        author = author.get()
        if author.is_remote:
            node_url = author.get_host_no_api()
            print(f"Node URL: {node_url}")
            node = RemoteNode.objects.filter(node_url=node_url)
            if node.exists():
                node = node.get()
                try:
                    print(f"inbox: {author_inbox}")
                    response = requests.post(
                        author_inbox,
                        json=like_data,
                        auth=(node.username, node.password),
                        timeout=10)
                    print(response.status_code)
                    if response.status_code not in [200, 201]:
                        print(like_data)
                        print(f"Failed to push like to {node_url}: {response.status_code}")
                except Exception as e:
                    print(e)
            else:
                print(f"{node_url} does not exist")
        else:
            print("local author")
    
    # serializer = LikeSerializer(like)
    # like_data = serializer.data
    # print(like_data)
    # author_followers = Follow.objects.filter(following=like.author, status='accepted')\

    # for follow in author_followers:
    #     if not follow.follower.is_remote:
    #         continue

    #     follower_inbox = follow.follower.id.rstrip("/") + "/inbox/"
    #     node_url = follow.follower.get_host_no_api()
    #     node = RemoteNode.objects.filter(node_url=node_url)
    #     if not node.exists():
    #         print(node_url)
    #         continue

    #     node = node.get()

    #     try:
    #         response = requests.post(
    #             follower_inbox,
    #             json=like_data,
    #             auth=(node.username, node.password),
    #             timeout=10
    #         )
    #         if response.status_code not in [200, 201]:
    #             print(f"Failed to push post to {follower_inbox}: {response.status_code}")
    #     except Exception as e:
    #         print(f"Exception while pushing post to {follower_inbox}: {e}")
"""
def push_like_to_inbox(like):
    print(like.object)
    #extract ~/api/authors/~ from ~/api/authors/~/posts/~ or ~/api/authors/~/commented/~
    author_inbox = like.object
    temp = author_inbox.find("api/authors")
    end_idx = author_inbox.find("/",temp+12)
    author_inbox = author_inbox[:end_idx]
    author_inbox = author_inbox.rstrip("/") + "/inbox"

    result = requests.get(like.object)
    if result.status_code >= 400:
        print("failed to get object")
        return
    result = result.json()
    author_serializer = AuthorSerializer(data=result.get("author"))
    if author_serializer.is_valid():
        author_data = author_serializer.data
        author_id = author_data.get("id")
        author_inbox = f"{author_id.rstrip('/')}/inbox"
        print(author_inbox)
        serializer = LikeSerializer(like)
        like_data = serializer.data

        author = Author.objects.filter(id=author_id)
        if author.exists():
            author = author.get()
            if author.is_remote:
                node_url = author.get_host_no_api()
                print(f"Node URL: {node_url}")
                node = RemoteNode.objects.filter(node_url=node_url)
                if node.exists():
                    node = node.get()
                    try:
                        reponse = requests.post(
                            author_inbox,
                            json=like_data,
                            auth=(node.username, node.password),
                            timeout=10)
                        if response.status_code not in [200, 201]:
                            print(like_data)
                            print(f"Failed to push like to {node_url}: {response.status_code}")
                    except Exception as e:
                        print(e)
                else:
                    print(f"{node_url} does not exist")
            else:
                print("local author")
    else:
        print(serializer.errors)
"""

@swagger_auto_schema(
    method='post',
    operation_description="Add a like to a specific post.",
    responses={
        201: openapi.Response(
            description="Like successfully added to the post, with the updated like count.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example="Like added to post."),
                    "likes_count": openapi.Schema(type=openapi.TYPE_INTEGER, example=15)
                }
            )
        ),
        404: "Author or post not found.",
        500: "Unable to add like due to server error."
    }
)
@login_required
@api_view(['POST'])
def like_post(request, author_uid, post_uid):
    like_author = request.user
    post_author = get_object_or_404(Author, uid=author_uid) #TODO think about foreign authors with same serials
    post = get_object_or_404(Post, uid=post_uid, author=post_author)

    if post.visibility == Post.FRIENDS_VISIBILITY:
        if not are_friends(like_author,post_author) and like_author != post_author:
            return Response({"message": "Cannot like friends-only post of user you are not friends with."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the author has already liked the post
    existing_like = Like.objects.filter(author=like_author, object=post.id).first()
    if existing_like:
        return Response({"message": "You have already liked this post."}, status=status.HTTP_400_BAD_REQUEST)

    like = post.add_like(like_author)
    push_like_to_inbox(like)
    return Response({"message": "Like added to post.", "likes_count": post.likes.count}, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='post',
    operation_description="Add a comment to a specific post.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['comment', 'content_type'],
        properties={
            'comment': openapi.Schema(type=openapi.TYPE_STRING, example="This is a comment."),
            'content_type': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=[
                    'text/markdown',
                    'text/plain',
                    'application/base64',
                    'image/png;base64',
                    'image/jpeg;base64'
                ],
                example='text/plain'
            )
        }
    ),
    responses={
        201: openapi.Response(
            description="Comment successfully added to the post.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example="Comment added to post."),
                    "comments_count": openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                    "comment_id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/api/comments/12345abcde")
                }
            )
        ),
        404: openapi.Response(description="Author or post not found."),
        500: openapi.Response(description="Unable to add comment due to server error.")
    }
)
@login_required
@api_view(['POST'])
def add_comment(request, author_uid, post_uid):
    comment_author = request.user
    post_author = get_object_or_404(Author, uid=author_uid)
    post = get_object_or_404(Post, uid=post_uid, author=post_author)

    if post.visibility == Post.FRIENDS_VISIBILITY:
        if not are_friends(comment_author,post_author) and comment_author != post_author:
            return Response({"message": "Cannot comment on friends-only post of user you are not friends with."}, status=status.HTTP_400_BAD_REQUEST)

    comment_text = request.data.get("comment")
    if not comment_text:
        return Response({"error": "Comment text is required."}, status=status.HTTP_400_BAD_REQUEST)

    comment = post.add_comment(comment_author, comment_text)
    push_comment_to_inbox(comment)

    return Response({
        "message": "Comment added to post.",
        "comments_count": post.comments.count,
        "comment_id": comment.uid
    }, status=status.HTTP_201_CREATED)



    # Check if the author has already liked the post
    existing_like = Like.objects.filter(author=like_author, object=post.id).first()
    if existing_like:
        return Response({"message": "You have already liked this post."}, status=status.HTTP_400_BAD_REQUEST)

    like = post.add_like(like_author)
    push_like_to_inbox(like)
    return Response({"message": "Like added to post.", "likes_count": post.likes.count}, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='post',
    operation_description="Add a like to a specific comment.",
    responses={
        201: openapi.Response(
            description="Like successfully added to the comment.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(type=openapi.TYPE_STRING, example="Like added to comment."),
                    "likes_count": openapi.Schema(type=openapi.TYPE_INTEGER, example=8)
                }
            )
        ),
        404: openapi.Response(description="Author or comment not found."),
        500: openapi.Response(description="Unable to add like due to server error.")
    }
)
@api_view(['POST'])
def like_comment(request, author_uid, comment_uid):
    like_author = request.user
    comment_author = get_object_or_404(Author, uid=author_uid)
    comment = get_object_or_404(Comment, uid=comment_uid)

    # Check if the author has already liked the comment
    existing_like = Like.objects.filter(author=like_author, object=comment.id).first()
    if existing_like:
        return Response({"message": "You have already liked this comment."}, status=status.HTTP_400_BAD_REQUEST)

    like = comment.add_like(like_author)
    push_like_to_inbox(like)
    return Response({"message": "Like added to comment.", "likes_count": comment.likes.count}, status=status.HTTP_201_CREATED)

""" TODO not using this, but make sure removing it doesn't break tests
@swagger_auto_schema(
    method='post',
    operation_description="Receive comments into inbox.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "type": openapi.Schema(type=openapi.TYPE_STRING, example="comment"),
            "comment": openapi.Schema(type=openapi.TYPE_STRING, example="This is a comment.")
        }
    ),
    responses={
        201: "Comment received in inbox",
        400: "Missing or invalid data"
    }
)
@api_view(['POST'])
def receive_comment_inbox(request, author_uid):
    data = request.data
    print("Received data:", data)
    if not data or 'type' not in data:
        return Response({"error": "Missing or invalid data"}, status=status.HTTP_400_BAD_REQUEST)

    if data.get('type') == 'comment':
        return Response({"message": "Comment received in inbox"}, status=status.HTTP_201_CREATED)
    else:
        return Response({"error": "Unsupported type"}, status=status.HTTP_400_BAD_REQUEST)
"""

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all comments on a specific post.",
    responses={
        200: openapi.Response(
            description="A JSON response containing all comments on the post.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="comments"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="comment"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        )
                                    }
                                ),
                                "comment": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="Test Comment"
                                ),
                                "contentType": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="text/markdown"
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:18:30.040320Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/commented/d71b7cf2-d3ca-4742-a101-105b1690ccaf"
                                ),
                                "post": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698"
                                ),
                                "page": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698/comments"
                                ),
                                "likes_count": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=0
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Post not found"
    }
)

@api_view(['GET'])
def get_post_comments(request, author_uid, post_uid):
    post = get_object_or_404(Post, uid=post_uid)
    comments = post.comments.src.all()
    serializer = CommentSerializer(comments, many=True)
    return Response({"type": "comments", "items": serializer.data})

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all comments on a post by its fully-qualified ID (FQID).",
    responses={
        200: openapi.Response(
            description="A JSON response containing all comments on the post.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="comments"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="comment"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        )
                                    }
                                ),
                                "comment": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="Test Comment"
                                ),
                                "contentType": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="text/markdown"
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:18:30.040320Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/commented/d71b7cf2-d3ca-4742-a101-105b1690ccaf"
                                ),
                                "post": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698"
                                ),
                                "page": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698/comments"
                                ),
                                "likes_count": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=0
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Post not found"
    }
)
@api_view(['GET'])
def get_post_comments_by_fqid(request, post_fqid):
    post = get_object_or_404(Post, id=post_fqid)
    comments = post.comments.src.all()
    serializer = CommentSerializer(comments, many=True)
    return Response({"type": "comments", "items": serializer.data})

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a specific remote comment on a post.",
    responses={
        200: openapi.Response(
            description="A JSON response containing with the details of the remote comment.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="comments"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="comment"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        )
                                    }
                                ),
                                "comment": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="Test Comment"
                                ),
                                "contentType": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="text/markdown"
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:18:30.040320Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/commented/d71b7cf2-d3ca-4742-a101-105b1690ccaf"
                                ),
                                "post": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698"
                                ),
                                "page": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698/comments"
                                ),
                                "likes_count": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=0
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Comment not found"
    }
)
@api_view(['GET'])
def get_remote_comment(request, author_uid, post_uid, remote_comment_fqid):
    comment = get_object_or_404(Comment, id=remote_comment_fqid)
    serializer = CommentSerializer(comment)
    return Response(serializer.data)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve details of a single comment by its fully-qualified ID (FQID).",
    responses={
        200: openapi.Response(
            description="A JSON response with the details of the specified comment.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="comments"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="comment"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        )
                                    }
                                ),
                                "comment": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="Test Comment"
                                ),
                                "contentType": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="text/markdown"
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:18:30.040320Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/commented/d71b7cf2-d3ca-4742-a101-105b1690ccaf"
                                ),
                                "post": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698"
                                ),
                                "page": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698/comments"
                                ),
                                "likes_count": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=0
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Post not found"
    }
)
@api_view(['GET'])
def get_comment(request, comment_fqid):
    comment = get_object_or_404(Comment, id=comment_fqid)
    serializer = CommentSerializer(comment)
    return Response(serializer.data)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve details of a comment made by an author on a post.",
    responses={
        200: openapi.Response(
            description="A JSON response containing the details of the comment.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="comment",
                        description="Indicates the type of response object."
                    ),
                    "author": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        description="Information about the author of the comment.",
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="author",
                                description="Indicates the type of object."
                            ),
                            "id": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_URI,
                                example="http://nodeaaaa/api/authors/111",
                                description="The unique identifier of the author."
                            ),
                            "page": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_URI,
                                example="http://nodeaaaa/authors/greg",
                                description="The URL of the author's profile page."
                            ),
                            "host": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_URI,
                                example="http://nodeaaaa/api/",
                                description="The host URL of the author."
                            ),
                            "displayName": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="Greg Johnson",
                                description="The display name of the author."
                            ),
                            "github": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_URI,
                                example="http://github.com/gjohnson",
                                description="The GitHub profile URL of the author."
                            ),
                            "profileImage": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format=openapi.FORMAT_URI,
                                example="https://i.imgur.com/k7XVwpB.jpeg",
                                description="The URL of the author's profile image."
                            )
                        }
                    ),
                    "comment": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="Sick Olde English",
                        description="The text of the comment."
                    ),
                    "contentType": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="text/markdown",
                        description="The format of the comment content."
                    ),
                    "published": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format=openapi.FORMAT_DATETIME,
                        example="2015-03-09T13:07:04+00:00",
                        description="The timestamp when the comment was published in ISO 8601 format."
                    ),
                    "id": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format=openapi.FORMAT_URI,
                        example="http://nodeaaaa/api/authors/111/commented/130",
                        description="The unique identifier of the comment."
                    ),
                    "post": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format=openapi.FORMAT_URI,
                        example="http://nodebbbb/api/authors/222/posts/249",
                        description="The URL of the post on which the comment was made."
                    ),
                    "page": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format=openapi.FORMAT_URI,
                        example="http://nodebbbb/authors/222/posts/249",
                        description="A URL to view the comment, which may be different from the post's URL."
                    )
                }
            )
        ),
        404: openapi.Response(
            description="Comment not found"
        )
    }
)
@api_view(['GET'])
def get_author_commented_posts(request, author_uid):
    return Response({"type": "comments", "items": []}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve details of a specific comment made by an author.",
    responses={
        200: openapi.Response(
            description="A JSON response containing details of the sepciifc comment made by an author.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="comments"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="comment"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        )
                                    }
                                ),
                                "comment": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="Test Comment"
                                ),
                                "contentType": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="text/markdown"
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:18:30.040320Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/commented/d71b7cf2-d3ca-4742-a101-105b1690ccaf"
                                ),
                                "post": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698"
                                ),
                                "page": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698/comments"
                                ),
                                "likes_count": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=0
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Comment not found"
    }
)
@api_view(['GET'])
def get_specific_commented(request, author_uid, comment_uid):
    comment = get_object_or_404(Comment, uid=comment_uid)
    serializer = CommentSerializer(comment)
    return Response(serializer.data)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve a comment from the local database by its fully-qualified ID (FQID).",
    responses={
        200: openapi.Response(
            description="A JSON response with details of a local comment.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="comments"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="comment"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        )
                                    }
                                ),
                                "comment": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="Test Comment"
                                ),
                                "contentType": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="text/markdown"
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:18:30.040320Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/commented/d71b7cf2-d3ca-4742-a101-105b1690ccaf"
                                ),
                                "post": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698"
                                ),
                                "page": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698/comments"
                                ),
                                "likes_count": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=0
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Comment not found"
    }
)
@api_view(['GET'])
def get_local_commented(request, comment_fqid):
    comment = get_object_or_404(Comment, id=comment_fqid)
    serializer = CommentSerializer(comment)
    return Response(serializer.data)

""" TODO not using this, but make sure tests don't have it
@swagger_auto_schema(
    method='post',
    operation_description="Receive a like notification in the inbox.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "type": openapi.Schema(type=openapi.TYPE_STRING, example="like"),
            "like": openapi.Schema(type=openapi.TYPE_STRING, example="This is a like.")
        }
    ),
    responses={
        201: "Like received in inbox",
        400: "Missing or invalid data"
    }
)
@api_view(['POST'])
def receive_like_inbox(request, author_uid):
    return Response({"message": "Like received in inbox"}, status=status.HTTP_201_CREATED)
"""

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all likes on a specific post.",
    responses={
        200: openapi.Response(
            description="A JSON response containing all likes on the post.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="likes"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="like"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        )
                                    }
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:32:46.980040Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/liked/efde1d99-c45a-4bb7-9315-9e96d238745f"
                                ),
                                "object": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698"
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Post not found"
    }
)

@api_view(['GET'])
def get_post_likes(request, author_uid, post_uid):
    post = get_object_or_404(Post, uid=post_uid)
    likes = post.likes.src.all()
    serializer = LikeSerializer(likes, many=True)
    return Response({"type": "likes", "items": serializer.data})

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all likes on a specific post.",
    responses={
        200: openapi.Response(
            description="A JSON response containing all likes on the post.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="likes"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="like"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/"
                                        )
                                    }
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:32:46.980040Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/liked/efde1d99-c45a-4bb7-9315-9e96d238745f"
                                ),
                                "object": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/posts/e32e3b8b-4baf-4bae-8ee2-8bfb85375698"
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Post not found"
    }
)

@api_view(['GET'])
def get_post_likes_by_fqid(request, post_fqid):
    post = get_object_or_404(Post, id=post_fqid)
    likes = post.likes.src.all()
    serializer = LikeSerializer(likes, many=True)
    return Response({"type": "likes", "items": serializer.data})

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all likes on a specific comment within a post.",
    responses={
        200: openapi.Response(
            description="A JSON response containing all likes on the comment.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="likes"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="like"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User 2"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test2"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image_8ju2b80.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/0402fb8f-f599-46e6-be16-a70029e3a848/"
                                        )
                                    }
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:35:43.825531Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/liked/d8bace62-f161-4d0e-8b48-5078c9165fd8"
                                ),
                                "object": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/commented/d71b7cf2-d3ca-4742-a101-105b1690ccaf"
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Comment not found"
    }
)

@api_view(['GET'])
def get_comment_likes(request, author_uid, post_uid, comment_uid):
    comment = get_object_or_404(Comment, uid=comment_uid)
    likes = comment.likes.src.all()
    serializer = LikeSerializer(likes, many=True)
    return Response({"type": "likes", "items": serializer.data})

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve details of a single like by its fully-qualified ID (FQID).",
     responses={
        200: openapi.Response(
            description="A JSON response the details of the specific like.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="likes"
                    ),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="like"
                                ),
                                "author": openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "type": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="author"
                                        ),
                                        "id": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/"
                                        ),
                                        "host": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/api/"
                                        ),
                                        "displayName": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="Test User 2"
                                        ),
                                        "github": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="https://github.com/Test2"
                                        ),
                                        "profileImage": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/media/profile_images/test_image_8ju2b80.jpg"
                                        ),
                                        "page": openapi.Schema(
                                            type=openapi.TYPE_STRING,
                                            example="http://127.0.0.1:8000/authors/0402fb8f-f599-46e6-be16-a70029e3a848/"
                                        )
                                    }
                                ),
                                "published": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="2024-11-24T22:35:43.825531Z"
                                ),
                                "id": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/0402fb8f-f599-46e6-be16-a70029e3a848/liked/d8bace62-f161-4d0e-8b48-5078c9165fd8"
                                ),
                                "object": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="http://127.0.0.1:8000/api/authors/dbee8cd0-be7f-4cd9-be14-029db6ee8ff6/commented/d71b7cf2-d3ca-4742-a101-105b1690ccaf"
                                )
                            }
                        )
                    )
                }
            )
        ),
        404: "Like not found"
    }
)
@api_view(['GET'])
def get_single_like(request, like_fqid):
    like = get_object_or_404(Like, id=like_fqid)
    serializer = LikeSerializer(like)
    return Response(serializer.data)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve all posts or comments liked by a specific author.",
    responses={
        200: openapi.Response(
            description="A JSON response containing a list of items liked by the author.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type=openapi.TYPE_STRING, example="likes"),
                    "items": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "like_id": openapi.Schema(type=openapi.TYPE_STRING, example="54321edcba"),
                                "item_type": openapi.Schema(type=openapi.TYPE_STRING, example="post"),
                                "item_id": openapi.Schema(type=openapi.TYPE_STRING, example="123postid"),
                                "timestamp": openapi.Schema(type=openapi.TYPE_STRING, example="2024-11-04T14:56:78Z")
                            }
                        )
                    )
                }
            )
        ),
        404: "Author not found"
    }
)
@api_view(['GET'])
def get_author_liked(request, author_uid):
    return Response({"type": "likes", "items": []}, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve details of a specific like made by an author.",
    responses={
        200: openapi.Response(
            description="A JSON response with details of the specific like.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "like_id": openapi.Schema(type=openapi.TYPE_STRING, example="54321edcba"),
                    "author_uid": openapi.Schema(type=openapi.TYPE_STRING, example="xyz789"),
                    "item_type": openapi.Schema(type=openapi.TYPE_STRING, example="post"),
                    "item_id": openapi.Schema(type=openapi.TYPE_STRING, example="123postid"),
                    "timestamp": openapi.Schema(type=openapi.TYPE_STRING, example="2024-11-04T14:56:78Z")
                }
            )
        ),
        404: "Like not found"
    }
)
@api_view(['GET'])
def get_specific_liked(request, author_uid, like_uid):
    like = get_object_or_404(Like, uid=like_uid)
    serializer = LikeSerializer(like)
    return Response(serializer.data)