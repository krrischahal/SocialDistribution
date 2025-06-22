import uuid
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from ..models import Author, Follow, Post
from ..serializers import *
import json
from urllib.parse import urlparse
import base64
from django.core.files.base import ContentFile
from urllib.parse import urlparse
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    operation_description="Handle incoming activities for an author's inbox.",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'type': openapi.Schema(type=openapi.TYPE_STRING, description="Type of activity (follow, post, like, comment)", example="follow"),
            'actor': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_STRING, description="Actor ID", example="http://example.com/authors/123"),
                    'host': openapi.Schema(type=openapi.TYPE_STRING, description="Actor host", example="http://example.com"),
                    'displayName': openapi.Schema(type=openapi.TYPE_STRING, description="Actor display name", example="John Doe"),
                    'github': openapi.Schema(type=openapi.TYPE_STRING, description="Actor GitHub profile", example="http://github.com/johndoe"),
                    'profileImage': openapi.Schema(type=openapi.TYPE_STRING, description="Actor profile image", example="http://example.com/images/johndoe.jpg"),
                    'url': openapi.Schema(type=openapi.TYPE_STRING, description="Actor URL", example="http://example.com/authors/123")
                }
            ),
            'object': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_STRING, description="Object ID", example="http://example.com/authors/456"),
                    'host': openapi.Schema(type=openapi.TYPE_STRING, description="Object host", example="http://example.com")
                }
            )
        }
    ),
    responses={
        201: openapi.Response(description="Activity processed successfully"),
        400: openapi.Response(description="Invalid request data"),
        404: openapi.Response(description="Target author not found")
    }
)
@api_view(['POST'])
def inbox(request, author_uid):
    target_author = get_object_or_404(Author, uid=author_uid)
    data = request.data

    activity_type = data.get('type')
    if activity_type:
        activity_type = activity_type.lower()
    else:
        return Response({"error": "Unsupported activity type."}, status=status.HTTP_400_BAD_REQUEST)

    if activity_type == 'follow':
        follower_data = data.get('actor')
        followee_data = data.get('object')

        # Extract follower details
        follower_id = follower_data.get('id')
        follower_host = follower_data.get('host')
        followee_host = followee_data.get('host')

        # Check if the request is from a remote server
        follower_host_netloc = urlparse(follower_host).netloc
        followee_host_netloc = urlparse(followee_host).netloc
        request_host_netloc = request.get_host()  # Already host:port

        print(f"Follower host netloc: {follower_host_netloc}")
        print(f"Followee host netloc: {followee_host_netloc}")
        print(f"Request host netloc: {request_host_netloc}")

        # Determine if the request is from a remote author
        is_remote_request = follower_host_netloc != request_host_netloc

        print(f"Remote request: {is_remote_request}")
        # Try to get the follower author by 'id'
        follower = Author.objects.filter(id=follower_id).first()
        if not follower:
            # Extract UUID from follower_id
            try:
                # Assuming the UUID is the last part of the URL
                uuid_str = follower_id.rstrip('/').split('/')[-1]
                follower_uuid = str(uuid_str)
            except (IndexError, ValueError) as e:
                print(f"Failed to parse UUID from {follower_id}: {e}")

            # Create new author
            follower = Author.objects.create(
                uid=follower_uuid,
                id=follower_id,
                host=follower_data.get('host'),
                display_name=follower_data.get('displayName'),
                github=follower_data.get('github'),
                profile_image=follower_data.get('profileImage'),
                page=follower_data.get('url'),
                is_active=False,  # Since this may be a remote author
                email=None,  # Remote authors may not have email addresses
                is_remote=True
            )
            print(f"Added remote author to local database: {follower.display_name}")

        # Determine follow status based on whether the follower and target are remote
        if not follower.is_remote and target_author.is_remote:
            follow_status = 'accepted'
        else:
            follow_status = 'pending'

        # Create or update the follow request
        follow_request, created = Follow.objects.get_or_create(
            follower=follower,
            following=target_author,
            defaults={'status': follow_status}
        )

        if not created and follow_request.status != follow_status:
            follow_request.status = follow_status
            follow_request.save()

        return Response({"message": "Follow request received."}, status=status.HTTP_201_CREATED)

    elif activity_type == 'post':
        print(data)
        if request.data.get('author').get('github') == 'None' or request.data.get('author').get('github') == '':
            request.data['author']["github"] = None

        profile_image = request.data['author']["profileImage"]
        if not all([urlparse(str(profile_image)).scheme, urlparse(str(profile_image)).netloc]):
            request.data['author']["profileImage"] = None
        
        # Handle incoming posts
        serializer = PostSerializer(data=request.data)
        print(serializer.is_valid())
        if serializer.is_valid():
            data = serializer.data
            author_serializer = AuthorSerializer(data=data.get("author"))
            print(author_serializer.is_valid())
            if author_serializer.is_valid():
                author_data = author_serializer.data

                author_id = author_data.get("id")
                post_id = data.get("id")
                if author_data.get("github") == "None":
                    author_data["github"] = None
                author, author_created = Author.objects.get_or_create(id=author_id)
                if author_created:
                    author.id = author_data.get("id")
                    author.host = author_data.get("host")
                    author.display_name = author_data.get("displayName")
                    author.page = author_data.get("page")
                    author.github = author_data.get("github")
                    author.profile_image = author_data.get("profileImage")
                    author.is_remote = True
                    author.save()

                # Get or create the post instance
                p = Post.objects.filter(id=post_id)
                if p.exists():
                    p = p.get()
                else:
                    p = Post()
                p.title = data.get("title")
                p.id = post_id
                parsed = urlparse(post_id)
                if not (parsed.scheme and parsed.netloc):
                    print(parsed)
                    return Response({"error": "Invalid ID."}, status=status.HTTP_400_BAD_REQUEST)
                print("1")
                p.page = data.get("page")
                p.description = data.get("description")
                p.content_type = data.get("contentType")
                p.author = author
                p.visibility = data.get("visibility")
                p.published_at = data.get("published")

                content_type = data.get("contentType")
                content = data.get("content")

                if content_type in ['image/png;base64', 'image/jpeg;base64', 'application/base64']:
                    # Decode the base64 content and save to the image field
                    try:
                        img_data = base64.b64decode(content+'==')
                        # Set file extension based on content type
                        if content_type == 'image/png;base64':
                            ext = 'png'
                        elif content_type == 'image/jpeg;base64':
                            ext = 'jpeg'
                        else:
                            ext = 'bin'  # For 'application/base64', use a generic extension
                        file_name = f"{p.uid}.{ext}"
                        p.image.save(file_name, ContentFile(img_data), save=False)
                        print("image saved successfully")
                        # Optionally, you can leave p.content empty or keep the content
                        p.content = data.get("content")
                        print("got content successfully", p.content)
                    except Exception as e:
                        print("image data invalid inside try catch")
                        return Response({'detail': 'Invalid image data'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # For non-image content types, save content to the content field
                    p.content = content

                p.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                print("image data invalid in author serializer")
                return Response(author_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            print(serializer.data)
            print(serializer.errors)
            print("image data invalid in post serializer")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    elif activity_type == 'like':
        if request.data.get('author').get('github') == 'None' or request.data.get('author').get('github') == '':
            request.data['author']["github"] = None

        profile_image = request.data['author']["profileImage"]
        if not all([urlparse(str(profile_image)).scheme, urlparse(str(profile_image)).netloc]):
            request.data['author']["profileImage"] = None

        # Handle incoming likes
        serializer = LikeSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            author_serializer = AuthorSerializer(data=data.get("author"))
            if author_serializer.is_valid():
                author_data = author_serializer.data

                author_id = author_data.get("id")
                like_id = data.get("id")

                author, author_created = Author.objects.get_or_create(id=author_id)
                if author_created:
                    author.id = author_data.get("id")
                    author.host = author_data.get("host")
                    author.display_name = author_data.get("displayName")
                    author.page = author_data.get("page")
                    author.github = author_data.get("github")
                    author.profile_image = author_data.get("profileImage")
                    author.is_remote = True
                    author.save()

                if Like.objects.filter(id=like_id).exists():
                    return Response({"error": "Like already exists."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    like = Like()

                like.author = author
                like.published = data.get("published")

                like.id = like_id
                parsed = urlparse(like_id)
                if not (parsed.scheme and parsed.netloc):
                    print(parsed)
                    return Response({"error": "Invalid ID."}, status=status.HTTP_400_BAD_REQUEST)

                like.object = data.get("object")
                parsed = urlparse(like.object)
                if not (parsed.scheme and parsed.netloc):
                    return Response({"error": "Invalid object."}, status=status.HTTP_400_BAD_REQUEST)

                like_object = Post.objects.filter(id=like.object)
                if not like_object.exists():
                    like_object = Comment.objects.filter(id=like.object)
                    if not like_object.exists():
                        return Response({"error": "Object not found."}, status=status.HTTP_400_BAD_REQUEST)
                like_object = like_object.get()

                like.likes = like_object.likes

                like.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.data)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif activity_type == 'comment':
        if request.data.get('author').get('github') == 'None' or request.data.get('author').get('github') == '':
            request.data['author']["github"] = None

        profile_image = request.data['author']["profileImage"]
        if not all([urlparse(str(profile_image)).scheme, urlparse(str(profile_image)).netloc]):
            request.data['author']["profileImage"] = None

        # Handle incoming comments
        print(request.data)
        serializer = CommentSerializer(data=request.data)
        print(serializer.is_valid())
        if serializer.is_valid():
            data = serializer.data
            author_serializer = AuthorSerializer(data=data.get("author"))
            if author_serializer.is_valid():
                author_data = author_serializer.data

                author_id = author_data.get("id")
                comment_id = data.get("id")

                author, author_created = Author.objects.get_or_create(id=author_id)
                if author_created:
                    author.id = author_data.get("id")
                    author.host = author_data.get("host")
                    author.display_name = author_data.get("displayName")
                    author.page = author_data.get("page")
                    author.github = author_data.get("github")
                    author.profile_image = author_data.get("profileImage")
                    author.is_remote = True
                    author.save()

                if Comment.objects.filter(id=comment_id).exists():
                    return Response({"error": "Comment already exists."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    comment = Comment()

                comment.author = author
                comment.comment = data.get("comment")
                comment.content_type = data.get("contentType")
                comment.published = data.get("published")

                comment.id = comment_id
                parsed = urlparse(comment_id)
                if not (parsed.scheme and parsed.netloc):
                    print(parsed)
                    return Response({"error": "Invalid ID."}, status=status.HTTP_400_BAD_REQUEST)

                comment.page = data.get("page")
                if comment.page == None:
                    comment.page = 'https://lol/'
                # parsed = urlparse(comment.page)
                # if not (parsed.scheme and parsed.netloc):
                #     return Response({"error": "Invalid page."}, status=status.HTTP_400_BAD_REQUEST)

                comment.post = data.get("post")
                parsed = urlparse(comment.post)
                if not (parsed.scheme and parsed.netloc):
                    return Response({"error": "Invalid post."}, status=status.HTTP_400_BAD_REQUEST)

                comment_post = Post.objects.filter(id=comment.post)
                if not comment_post.exists():
                    return Response({"error": "Invalid post."}, status=status.HTTP_400_BAD_REQUEST)
                comment_post = comment_post.get()

                comment.comments = comment_post.comments

                comment.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(serializer.data)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    else:
        return Response({"error": "Unsupported activity type."}, status=status.HTTP_400_BAD_REQUEST)