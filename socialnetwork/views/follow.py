import base64
import json
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from ..models import Author, Follow, RemoteNode
from ..serializers import *
import requests
from urllib.parse import unquote
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='get',
    operation_description="Check if a foreign author is a follower of a local author.",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="UUID of the local author.",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174111"
        ),
        openapi.Parameter(
            'foreign_author_id',
            openapi.IN_PATH,
            description="UUID of the foreign author.",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174222"
        )
    ],
    responses={
        200: openapi.Response(
            description="Foreign author is a follower of the local author.",
            schema= openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format="uri",
                            description="The ID of the foreign author.",
                            example="http://example.com/authors/123e4567-e89b-12d3-a456-426614174222"
                        ),
                        "displayName": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="The display name of the foreign author.",
                            example="Foreign Author"
                        ),
                        "github": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format="uri",
                            description="GitHub profile URL of the foreign author.",
                            example="http://github.com/foreignauthor"
                        ),
                        "profileImage": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format="uri",
                            description="Profile image URL of the foreign author.",
                            example="http://example.com/images/foreign.jpg"
                        ),
                        "email": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            format="email",
                            description="Email of the foreign author.",
                            example="foreign@example.com"
                        ),
                        "bio": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Short bio of the foreign author.",
                            example="Foreign author's bio"
                        )
                    }
                )
             ),
            
        404: openapi.Response(
            description="Foreign author not found or not a follower."
    )
    }
)

@swagger_auto_schema(
    method='put',
    operation_description="Accept a foreign author as a follower (only the local author can perform this action).",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="UUID of the local author.",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174111"
        ),
        openapi.Parameter(
            'foreign_author_id',
            openapi.IN_PATH,
            description="UUID of the foreign author.",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174222"
        )
    ],
    responses={
        200: "Follower successfully added or updated.",
        403: "Unauthorized action: Only the local author can perform this action.",
        404: "Foreign author not found."
    }
)
@swagger_auto_schema(
    method='delete',
    operation_description="Remove the follow relationship (either the local author or foreign author can perform this action).",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="UUID of the local author.",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174111"
        ),
        openapi.Parameter(
            'foreign_author_id',
            openapi.IN_PATH,
            description="UUID of the foreign author.",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174222"
        )
    ],
    responses={
        204: "Follow relationship successfully removed.",
        403: "Unauthorized action: You do not have permission to perform this action.",
        404: "Follow relationship does not exist or foreign author not found."
    }
)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AllowAny]) 
def follower_detail(request, author_uid, foreign_author_id):
    """
    Handle GET, PUT, DELETE requests for a specific follower.

    **GET**: Check if a foreign author is a follower of a local author.

    **PUT**: Accept a foreign author as a follower (only the local author can perform this action).

    **DELETE**: Remove the follow relationship (either the local author or foreign author can perform this action).

    **Parameters**:
    - `author_uid` (path): UUID of the local author (type: string, format: uuid, required: true)
    - `foreign_author_id` (path): UUID of the foreign author (type: string, format: uuid, required: true)

    **Returns**:
    - 200: Successful GET or PUT request with relevant message or author details.
    - 204: Successful DELETE request when the follow relationship is removed.
    - 403: Unauthorized action for PUT/DELETE request by a user without permissions.
    - 404: Author not found or follow relationship does not exist.

    **Example requests**:
    - `GET /authors/<author_uid>/followers/<foreign_author_id>`
    - `PUT /authors/<author_uid>/followers/<foreign_author_id>`
    - `DELETE /authors/<author_uid>/followers/<foreign_author_id>`
    """
    # Get the local author
    author = get_object_or_404(Author, uid=author_uid)

    # Decode the percent-encoded foreign author ID
    foreign_author_id = unquote(foreign_author_id)

    # Try to retrieve the foreign author
    try:
        print("========================")
        print(foreign_author_id)
        print(type(foreign_author_id))
        print(Author.objects.filter(id=foreign_author_id).exists())
        print(Author.objects.all().first())
        print("========================")
        foreign_author = Author.objects.get(id=foreign_author_id)
    except Author.DoesNotExist:
        # Optionally, you can fetch the author details from the foreign node
        return Response({'error': 'Foreign author not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        # Check if foreign_author is a follower of author
        follow = Follow.objects.filter(follower=foreign_author, following=author, status='accepted').first()
        if follow:
            serializer = AuthorSerializer(foreign_author)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Not a follower'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'PUT':
        # Only the author can accept a follower
        if request.user != author:
            return Response({'error': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

        # Add foreign_author as a follower of author
        follow, created = Follow.objects.get_or_create(
            follower=foreign_author,
            following=author,
            defaults={'status': 'accepted'}
        )
        if not created and follow.status != 'accepted':
            follow.status = 'accepted'
            follow.save()

        return Response({'message': 'Follower added.'}, status=status.HTTP_200_OK)

    if request.method == 'DELETE':
        
        follow = Follow.objects.filter(follower=foreign_author, following=author).first()
        if follow:
            follow.delete()
            return Response({'message': 'Follow relationship removed.'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'Follow relationship does not exist.'}, status=status.HTTP_404_NOT_FOUND)

@swagger_auto_schema(
    method='get',
    operation_description="List all followers of an author.",
    manual_parameters=[
        openapi.Parameter(
            'author_uid',
            openapi.IN_PATH,
            description="UUID of the author.",
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_UUID,
            required=True,
            example="123e4567-e89b-12d3-a456-426614174111"
        )
    ],
    responses={
        200: openapi.Response(
            description="List of followers with the structure.",
            examples={
                "application/json": {
                    "type": "followers",
                    "followers": [
                        {
                            "id": "http://example.com/authors/123e4567-e89b-12d3-a456-426614174111",
                            "displayName": "Follower Name",
                            "github": "http://github.com/follower",
                            "profileImage": "http://example.com/images/follower.jpg",
                            "email": "follower@example.com",
                            "bio": "Follower profile information"
                        },
                        ...
                    ]
                }
            }
        ),
        404: "Author not found."
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])  # Allow both local and remote access
def list_followers(request, author_uid):
    """
    List all followers of an author.

    **When to use**:
    - Retrieve a list of all accepted followers for a specific author.

    **Parameters**:
    - `author_uid` (path): UUID of the author (type: string, format: uuid, required: true)

    **Returns**:
    - 200: List of followers with the structure:
      ```json
      {
          "type": "followers",
          "followers": [
              {
                  "id": "http://example.com/authors/<uuid>",
                  "displayName": "Follower Name",
                  "github": "http://github.com/follower",
                  "profileImage": "http://example.com/images/follower.jpg",
                  "email": "follower@example.com",
                  "bio": "Follower profile information"
              },
              ...
          ]
      }
      ```
    - 404: Author not found.

    **Example request**:
    - `GET /authors/<author_uid>/followers`
    """
    author = get_object_or_404(Author, uid=author_uid)
    followers = Follow.objects.filter(following=author, status='accepted').values_list('follower', flat=True)
    follower_authors = Author.objects.filter(uid__in=followers)
    serializer = AuthorSerializer(follower_authors, many=True)
    return Response({
        "type": "followers",
        "followers": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def follow_author(request):
    """
    Handle follow requests.
    """
    try:
        data = request.data 
        author_id = data.get('author_id')
        print(data)
        if not author_id:
            return JsonResponse({'error': 'Author ID is required.'}, status=400)
        
        # Get the target author
        try:
            target_author = Author.objects.get(id=author_id)
        except Author.DoesNotExist:
            return JsonResponse({'error': 'Author not found.'}, status=404)
        
        # Check if the target author is local
        is_local = (target_author.host == request.build_absolute_uri('/').rstrip('/')+'/api/')
        if is_local:
            # Local follow: Create or update the Follow model
            follow, created = Follow.objects.get_or_create(
                follower=request.user,
                following=target_author,
                defaults={'status': 'pending'}
            )
            if not created:
                if follow.status == 'accepted':
                    return JsonResponse({'message': 'Already following.'}, status=200)
                elif follow.status == 'pending':
                    return JsonResponse({'message': 'Follow request already pending.'}, status=200)
            
            # Optionally notify the target author of the follow request
            return JsonResponse({'message': 'Follow request sent to local author.'}, status=200)
        
        else:
            # Remote follow: Update local copy and send request to remote backend
            follow, created = Follow.objects.get_or_create(
                follower=request.user,
                following=target_author,
                defaults={'status': 'accepted'}
            )
            if not created:
                if follow.status == 'accepted':
                    return JsonResponse({'message': 'Already following.'}, status=200)
                elif follow.status == 'pending':
                    return JsonResponse({'message': 'Follow request already pending.'}, status=200)
            
            # Find the remote node corresponding to the target author
            print(target_author.host)
            remote_node = RemoteNode.objects.filter(node_url=target_author.host.replace('api/', '')).first()

            if not remote_node:
                return JsonResponse({'error': 'Remote node not found.'}, status=404)
            if target_author.github == '':
                github_url = 'None'
            else:
                github_url = target_author.github
            
            # Construct the follow request payload
            follow_payload = {
                "type": "follow",
                "summary": f"{request.user.display_name} wants to follow you.",
                "actor": {
                    "type": "author",
                    "id": request.user.id,
                    "host": request.user.host,
                    "displayName": request.user.display_name,
                    "page": request.user.page,
                    "github": github_url,
                    "profileImage": request.user.profile_image or '',
                },
                "object": {
                    "type": "author",
                    "id": target_author.id,
                    "host": target_author.host,
                    "displayName": target_author.display_name,
                    "page": target_author.page,
                    "github": target_author.github,
                    "profileImage": target_author.profile_image or '',
                }
            }
            print(follow_payload)
            # Send the follow request to the remote node's inbox
            inbox_url = f"{target_author.host}authors/{target_author.uid}/inbox"
            print(inbox_url)
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Basic {base64.b64encode(f'{remote_node.username}:{remote_node.password}'.encode()).decode()}",  # Basic Auth
            }
            
            response = requests.post(inbox_url, headers=headers, json=follow_payload)
            if response.status_code in [200, 201, 202]:
                return JsonResponse({'message': 'Follow request sent to remote author.'}, status=200)
            else:
                # Optionally, rollback the local follow creation if the remote request failed
                follow.delete()
                return JsonResponse({'error': 'Failed to send follow request to remote author.'}, status=500)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
def unfollow_author(request):
    """
    Handle unfollow requests.
    """
    try:
        data = request.data 
        author_id = data.get('author_id')
        if not author_id:
            return JsonResponse({'error': 'Author ID is required.'}, status=400)
        
        # Get the target author
        try:
            target_author = Author.objects.get(id=author_id)
        except Author.DoesNotExist:
            return JsonResponse({'error': 'Author not found.'}, status=404)
        
        # Check if the target author is local
        is_local = (target_author.host == request.build_absolute_uri('/').rstrip('/')+'/api/')
        
        if is_local:
            # Local unfollow: Remove or update the Follow model
            try:
                follow = Follow.objects.get(follower=request.user, following=target_author)
                follow.delete()  # Or set status to 'unfollowed' if you prefer
                return JsonResponse({'message': 'Unfollowed local author.'}, status=200)
            except Follow.DoesNotExist:
                return JsonResponse({'message': 'Not following this author.'}, status=200)
        
        else:
            # Remote unfollow: Update local copy and send request to remote backend
            try:
                follow = Follow.objects.get(follower=request.user, following=target_author)
                follow.delete()
            except Follow.DoesNotExist:
                return JsonResponse({'message': 'Not following this author.'}, status=200)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@api_view(["GET"])
def get_followers_list(request,author_uid):
    author = Author.objects.filter(uid=author_uid,is_remote=False).first()
    follows = Follow.objects.filter(following=author,status='accepted')
    followers = []
    for follow in follows:
        followers.append(follow.follower)
    serializer = AuthorSerializer(followers,many=True)
    data = {"type":"followers","followers":serializer.data}
    return Response(data, status=status.HTTP_200_OK)