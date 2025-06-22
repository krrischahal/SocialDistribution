from django.urls import path, include
from django.contrib.auth import views as auth_views

from socialnetwork.views.node import NodeCredentialView, RemoteNodeView
from . import views
from socialnetwork.views.web import edit_post
from socialnetwork.views.like_comment import like_post, add_comment, like_comment
from socialnetwork.views.like_comment import *
from .views import CustomLoginView
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


urlpatterns = [
    #TODO THIS IS A HACK FIX, DO IT PROPERLY
    path('', views.home, name='home'), 
    path('register', views.register, name='register'),
    path('login', CustomLoginView.as_view(), name='login'),
    path('logout', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    path('accounts/login', CustomLoginView.as_view(), name='login_redirect'), # login redirect

    path('follow-requests', views.follow_requests_view, name='follow_requests_view'),

    # Authors Endpoints
    path('api/authors', views.list_authors, name='list_authors'),  # GET all authors
    path('api/authors/add', views.add_author, name='add_author'),  # POST add author
    path('api/authors/<uuid:uid>', views.get_author, name='get_author'),  # GET single author
    path('api/authors/<uuid:uid>/edit', views.update_author, name='update_author'),  # PUT update author
    path('api/authors/<uuid:uid>/delete', views.delete_author, name='delete_author'),  # DELETE author

    # accept and reject follow requests
    path('api/follow-requests/<uuid:follow_id>/accept', views.accept_follow_request, name='accept_follow_request'),
    path('api/follow-requests/<uuid:follow_id>/reject', views.reject_follow_request, name='reject_follow_request'),


    # Authors UI
    path('authors/<uuid:author_id>', views.profile, name='profile'),  # Author profile
    path('authors/<uuid:author_uid>/my-posts', views.my_posts, name='my_posts'),
    path('authors/<uuid:author_uid>/new_post', views.new_post, name='new_post'),
    
    # Posts UI
    path("authors/<uuid:author_uid>/posts/<uuid:post_uid>", views.view_post_page, name="post_page"),
    path('authors/<uuid:author_uid>/posts/<uuid:post_uid>/delete', views.delete_post, name='delete_post'),
    path('authors/<uuid:author_uid>/posts/<uuid:post_uid>/edit', views.web.edit_post, name='edit_post'),
    path("posts", views.view_posts, name="view_posts"),
    path("stream", views.view_stream, name="view_stream"),
    path("compose/post", views.create_post, name="create_post"),    # UI for posting
    
    # Posts Endpoints
    path("api/authors/<uuid:author_uid>/posts", views.add_post, name="add_post"),    # API for posting
    path("api/posts/<path:post_fqid>",views.get_post, name="get_post"),
    path("api/authors/<uuid:author_uid>/posts/<uuid:post_uid>", views.access_post, name="access_post"),    # API for existing posts (get, delete, edit)
    path('api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/image', views.get_post_image_by_author_and_post, name='get_post_image_by_author_and_post'),
    path('api/posts/<path:post_fqid>/image', views.get_post_image_by_fqid, name='get_post_image_by_fqid'),

    path('authors/<uuid:author_uid>/upload_image', views.upload_image, name='upload_image'), #image for commonmark

    path('api/authors/<uuid:author_uid>/followers/', views.get_followers_list, name='get_followers_list'),
    path('api/authors/<uuid:author_uid>/followers/<path:foreign_author_id>', views.follower_detail, name='follower_detail'),

    # Inbox Endpoint
    path('api/authors/<uuid:author_uid>/inbox', views.inbox, name='inbox'),

    # Like and Comment Endpoints
    path("api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/like", like_post, name="like_post"),
    path("api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/comment", add_comment, name="add_comment"),
    # Like and Comment Endpoints
    path("api/authors/<uuid:author_uid>/comments/<uuid:comment_uid>/like", like_comment, name="like_comment"),
    path('follow-requests', views.follow_requests_view, name='follow_requests_view'),
    path('api/follow-requests/<uuid:follow_id>/accept', views.accept_follow_request, name='accept_follow_request'),
    path('api/follow-requests/<uuid:follow_id>/reject', views.reject_follow_request, name='reject_follow_request'),

    #repost endpoint
    path("api/reposts/<path:post_fqid>", views.repost, name="repost"),
    
    # New Comments API Endpoints
    path('api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/comments', get_post_comments, name='get_post_comments'),
    path('api/posts/<path:post_fqid>/comments', get_post_comments_by_fqid, name='get_post_comments_by_fqid'),
    path('api/authors/<uuid:author_uid>/post/<uuid:post_uid>/comment/<path:remote_comment_fqid>', get_remote_comment, name='get_remote_comment'),
    path('api/comment/<path:comment_fqid>', get_comment, name='get_comment'),
    
    # New Commented API Endpoints
    path('api/authors/<uuid:author_uid>/commented', get_author_commented_posts, name='get_author_commented_posts'),
    path('api/authors/<uuid:author_uid>/commented/<uuid:comment_uid>', get_specific_commented, name='get_specific_commented'),
    path('api/commented/<path:comment_fqid>', get_local_commented, name='get_local_commented'),

    # New Likes API Endpoints
    path('api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/likes', get_post_likes, name='get_post_likes'),
    path('api/posts/<path:post_fqid>/likes', get_post_likes_by_fqid, name='get_post_likes_by_fqid'),
    path('api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/comments/<uuid:comment_uid>/likes', get_comment_likes, name='get_comment_likes'),
    path('api/liked/<path:like_fqid>', get_single_like, name='get_single_like'),

    # New Liked API Endpoints
    path('api/authors/<uuid:author_uid>/liked', get_author_liked, name='get_author_liked'),
    path('api/authors/<uuid:author_uid>/liked/<uuid:like_uid>', get_specific_liked, name='get_specific_liked'),

    # Node API Endpoints
    path('api/node/credentials', NodeCredentialView.as_view(), name='node_credentials'),
    path('api/node/remote', RemoteNodeView.as_view(), name='remote_nodes'),


    #===================
    #OUR ORIGINAL URLS
    #===================


    path('', views.home, name='home'), 
    path('register/', views.register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    path('accounts/login/', CustomLoginView.as_view(), name='login_redirect'), # login redirect

    path('follow-requests/', views.follow_requests_view, name='follow_requests_view'),

    # Authors Endpoints
    path('api/authors/', views.list_authors, name='list_authors'),  # GET all authors
    path('api/authors/add/', views.add_author, name='add_author'),  # POST add author
    path('api/authors/<uuid:uid>/', views.get_author, name='get_author'),  # GET single author
    path('api/authors/<uuid:uid>/edit/', views.update_author, name='update_author'),  # PUT update author
    path('api/authors/<uuid:uid>/delete/', views.delete_author, name='delete_author'),  # DELETE author

    # accept and reject follow requests
    path('api/follow-requests/<uuid:follow_id>/accept/', views.accept_follow_request, name='accept_follow_request'),
    path('api/follow-requests/<uuid:follow_id>/reject/', views.reject_follow_request, name='reject_follow_request'),


    # Authors UI
    path('authors/<uuid:author_id>/', views.profile, name='profile'),  # Author profile
    path('authors/<uuid:author_uid>/my-posts', views.my_posts, name='my_posts'),
    path('authors/<uuid:author_uid>/new_post', views.new_post, name='new_post'),
    
    # Posts UI
    path("authors/<uuid:author_uid>/posts/<uuid:post_uid>/", views.view_post_page, name="post_page"),
    path('authors/<uuid:author_uid>/posts/<uuid:post_uid>/delete/', views.delete_post, name='delete_post'),
    path('authors/<uuid:author_uid>/posts/<uuid:post_uid>/edit/', views.web.edit_post, name='edit_post'),
    path("posts/", views.view_posts, name="view_posts"),
    path("stream/", views.view_stream, name="view_stream"),
    path("compose/post", views.create_post, name="create_post"),    # UI for posting
    
    # Posts Endpoints
    path("api/authors/<uuid:author_uid>/posts/", views.add_post, name="add_post"),    # API for posting
    path("api/posts/<path:post_fqid>",views.get_post, name="get_post"),
    path("api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/", views.access_post, name="access_post"),    # API for existing posts (get, delete, edit)
    path('api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/image', views.get_post_image_by_author_and_post, name='get_post_image_by_author_and_post'),
    path('api/posts/<path:post_fqid>/image', views.get_post_image_by_fqid, name='get_post_image_by_fqid'),

    path('authors/<uuid:author_uid>/upload_image/', views.upload_image, name='upload_image'), #image for commonmark


    path('api/authors/<uuid:author_uid>/followers/', views.get_followers_list, name='get_followers_list'),
    path('api/authors/<uuid:author_uid>/followers/<path:foreign_author_id>/', views.follower_detail, name='follower_detail'),

    # Inbox Endpoint
    path('api/authors/<uuid:author_uid>/inbox/', views.inbox, name='inbox'),

    # Like and Comment Endpoints
    path("api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/like/", like_post, name="like_post"),
    path("api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/comment/", add_comment, name="add_comment"),
    # Like and Comment Endpoints
    path("api/authors/<uuid:author_uid>/comments/<uuid:comment_uid>/like/", like_comment, name="like_comment"),
    path('follow-requests/', views.follow_requests_view, name='follow_requests_view'),
    path('api/follow-requests/<uuid:follow_id>/accept/', views.accept_follow_request, name='accept_follow_request'),
    path('api/follow-requests/<uuid:follow_id>/reject/', views.reject_follow_request, name='reject_follow_request'),
    path('api/follow/', views.follow_author, name='follow_author'),
    path('api/unfollow/', views.unfollow_author, name='unfollow_author'),
    #repost endpoint
    path("api/reposts/<path:post_fqid>", views.repost, name="repost"),
    
    # New Comments API Endpoints
    path('api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/comments/', get_post_comments, name='get_post_comments'),
    path('api/posts/<path:post_fqid>/comments/', get_post_comments_by_fqid, name='get_post_comments_by_fqid'),
    path('api/authors/<uuid:author_uid>/post/<uuid:post_uid>/comment/<path:remote_comment_fqid>/', get_remote_comment, name='get_remote_comment'),
    path('api/comment/<path:comment_fqid>/', get_comment, name='get_comment'),
    
    # New Commented API Endpoints
    path('api/authors/<uuid:author_uid>/commented/', get_author_commented_posts, name='get_author_commented_posts'),
    path('api/authors/<uuid:author_uid>/commented/<uuid:comment_uid>/', get_specific_commented, name='get_specific_commented'),
    path('api/commented/<path:comment_fqid>/', get_local_commented, name='get_local_commented'),

    # New Likes API Endpoints
    path('api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/likes/', get_post_likes, name='get_post_likes'),
    path('api/posts/<path:post_fqid>/likes/', get_post_likes_by_fqid, name='get_post_likes_by_fqid'),
    path('api/authors/<uuid:author_uid>/posts/<uuid:post_uid>/comments/<uuid:comment_uid>/likes/', get_comment_likes, name='get_comment_likes'),
    path('api/liked/<path:like_fqid>/', get_single_like, name='get_single_like'),

    # New Liked API Endpoints
    path('api/authors/<uuid:author_uid>/liked/', get_author_liked, name='get_author_liked'),
    path('api/authors/<uuid:author_uid>/liked/<uuid:like_uid>/', get_specific_liked, name='get_specific_liked'),

    # Node API Endpoints
    path('api/node/credentials/', NodeCredentialView.as_view(), name='node_credentials'),
    path('api/node/remote/', RemoteNodeView.as_view(), name='remote_nodes'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)