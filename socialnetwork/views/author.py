from django.shortcuts import render, redirect, get_object_or_404
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..serializers import AuthorSerializer, PostSerializer
from ..models import Author, Post, Follow
from ..forms import AuthorCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from .pagination import AuthorPagination

@swagger_auto_schema(
    method='get',
    operation_description="Get a paginated list of all authors.",
    responses={
        200: openapi.Response(
            description="Paginated list of authors",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type="authors"),
                    "authors": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(type=openapi.TYPE_STRING, example="author"),
                                "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/<uuid>"),
                                "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com"),
                                "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
                                "url": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/<uuid>"),
                                "github": openapi.Schema(type=openapi.TYPE_STRING, example="http://github.com/johndoe"),
                                "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/johndoe.jpg"),
                                "page": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/<uuid>"),                           }
                        )
                    ),
                    "page": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                    "size": openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                    "next": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors?page=2"),
                    "previous": openapi.Schema(type=openapi.TYPE_STRING, example=None),
                    "count": openapi.Schema(type=openapi.TYPE_INTEGER, example=100)
                }
            )
        ),
        400: "Invalid size parameter"
    }
)

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([]) 
def list_authors(request):

    paginator = AuthorPagination()
    size = request.GET.get('size', 10)
    page = request.GET.get('page', 1)
    
    try:
        size = int(size)
        if size <= 0:
            raise ValueError
    except ValueError:
        return Response({'error': 'Invalid size parameter'}, status=status.HTTP_400_BAD_REQUEST)
    
    paginator.page_size = size

    # Exclude admin author and remote authors
    authors = Author.objects.exclude(host='').filter(is_remote=False)
    result_page = paginator.paginate_queryset(authors, request)
    serializer = AuthorSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializer.data)

@swagger_auto_schema(
    method='get',
    operation_description="Retrieve details of a specific author by their UUID.",
    responses={
        200: openapi.Response(
            description="Author found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "type": openapi.Schema(type="author"),
                    "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/api/authors/<uuid>"),
                    "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/api/"),
                    "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
                    "github": openapi.Schema(type=openapi.TYPE_STRING, example="http://github.com/johndoe"),
                    "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/johndoe.jpg"),
                    "page": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/<uuid>"),
                }
            )
        ),
        404: "No Author matches the given query."
    }
)
@api_view(['GET'])
def get_author(request, uid):
    author = get_object_or_404(Author, uid=uid)
    serializer = AuthorSerializer(author)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='delete',
    operation_description="Delete an author account.",
    responses={
        204: "Author successfully deleted",
        404: "No Author matches the given query.",
        403: "Authentication credentials were not provided.",
        403: "You do not have permission to perform this action."
    }
)
@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_author(request, uid):
    author = get_object_or_404(Author, uid=uid)
    author.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@swagger_auto_schema(
    method='post',
    operation_description="Create a new author account.",
    request_body=AuthorSerializer,
    responses={
        201: openapi.Response(
            description="Author created successfully",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                            properties={
                                "type": openapi.Schema(type="author"),
                                "id": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/<uuid>"),
                                "host": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com"),
                                "displayName": openapi.Schema(type=openapi.TYPE_STRING, example="John Doe"),
                                "github": openapi.Schema(type=openapi.TYPE_STRING, example="http://github.com/johndoe"),
                                "profileImage": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/images/johndoe.jpg"),
                                "page": openapi.Schema(type=openapi.TYPE_STRING, example="http://example.com/authors/<uuid>"),                           }
            )
        ),
        400: "Invalid request data",
        403: "You do not have permission to perform this action."
    }
)
@api_view(['POST'])
@permission_classes([IsAdminUser])
def add_author(request):
    serializer = AuthorSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method='put',
    operation_description="Update an existing author's information.",
    request_body=AuthorSerializer,
    responses={
        200: openapi.Response(
            description="Author updated successfully",
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
        400: "Invalid request data",
        403: "Insufficient permissions",
        404: "Author not found"
    }
)
@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_author(request, uid):
    author = get_object_or_404(Author, uid=uid)
    serializer = AuthorSerializer(author, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)