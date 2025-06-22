import base64
from rest_framework import serializers
from .models import *
import requests

class AuthorSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='author', read_only=True)
    id = serializers.URLField(required=False)#read_only=True)   #TODO test extensively
    host = serializers.URLField()
    displayName = serializers.CharField(source='display_name')
    github = serializers.URLField(allow_blank=True, allow_null=True, required=False)
    profileImage = serializers.URLField(source='profile_image', required=False, allow_null=True)
    page = serializers.URLField(read_only=True)

    class Meta:
        model = Author
        fields = ['type', 'id', 'host', 'displayName', 'github', 'profileImage', 'page']

    # def create(self, validated_data):
    #     if validated_data.get('github') == '' or validated_data.get('github') == 'None':
    #         validated_data['github'] = None
    #     return Author.objects.create(**validated_data)
    
    # def validate_github(self, value):
    #     github = value
    #     if github == '' or github == 'None':
    #         value = None
    #     return value

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'initial_data'):
            if self.initial_data.get("github") in ["None", ""]:
                self.initial_data["github"] = None

class LikeSerializer(serializers.Serializer):
    type = serializers.CharField(default="like")
    author = AuthorSerializer()
    published = serializers.DateTimeField()
    id = serializers.URLField()
    object = serializers.URLField()

    """#method field methods
    def get_author(self,obj):
        #Note: when a superuser is created from the command line, its host field
        #won't be set, which'll mess up the url and cause an error. Manually setting
        #the host field in the admin panel fixes this (users created through signup
        #work normally).
        result = requests.get(obj.author_url)
        return result.json()"""

#serializer for all likes on a post
class LikesSerializer(serializers.Serializer):
    type = serializers.CharField(default="likes")
    page = serializers.URLField()
    id = serializers.URLField()
    page_number = serializers.IntegerField(min_value=1,default=1)
    size = serializers.IntegerField(min_value=1)
    count = serializers.IntegerField(min_value=0)
    src = LikeSerializer(many=True)

#serializer for a single comment
class CommentSerializer(serializers.Serializer):
    type = serializers.CharField(default="comment")
    author = AuthorSerializer()
    comment = serializers.CharField()
    contentType = serializers.ChoiceField(source="content_type",choices=[
        ('text/markdown', 'Markdown'),
        ('text/plain', 'Plaintext'),
        ('application/base64', 'Image'),
        ('image/png;base64', 'PNG'),
        ('image/jpeg;base64', 'JPEG'),
    ])
    published = serializers.DateTimeField()
    id = serializers.URLField()
    post = serializers.URLField()
    page = serializers.URLField(required=False)
    likes_count = serializers.SerializerMethodField()
    likes = LikesSerializer(required=False)
    #method field methods
    """def get_author(self,obj):
        #Note: when a superuser is created from the command line, its host field
        #won't be set, which'll mess up the url and cause an error. To fix this, you
        #need to update the host and id fields manually(users created through signup
        #work normally).
        result = requests.get(obj.author_url)
        return result.json()"""

    def get_likes_count(self, obj):
        # Ensure obj has `likes` attribute before accessing it
        if hasattr(obj, 'likes') and obj.likes:
            return obj.likes.count
        return 0

#serializer for all comments on a post
class CommentsSerializer(serializers.Serializer):
    type = serializers.CharField(default="comments")
    page = serializers.URLField(required=False)
    id = serializers.URLField()
    page_number = serializers.IntegerField(min_value=1,default=1)
    size = serializers.IntegerField(min_value=1)
    count = serializers.IntegerField(min_value=0)
    src = CommentSerializer(many=True)
    
class PostSerializer(serializers.Serializer):
    type = serializers.CharField(default="post")
    title = serializers.CharField(max_length=255)
    id = serializers.URLField(required=False)
    page = serializers.URLField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    contentType = serializers.ChoiceField(source="content_type", choices=[
        ('text/markdown', 'Markdown'),
        ('text/plain', 'Plaintext'),
        ('application/base64', 'Base64'),
        ('image/png;base64', 'PNG Image'),
        ('image/jpeg;base64', 'JPEG Image'),
    ])
    content = serializers.CharField(required=False, allow_blank=True)
    visibility = serializers.ChoiceField(choices=Post.VISIBILITY_CHOICES)
    author = AuthorSerializer(required=False)
    comments = CommentsSerializer(read_only=True)
    likes = LikesSerializer(read_only=True)
    published = serializers.DateTimeField(source="published_at", required=False)

    def validate(self, data):
        content_type = data.get('content_type')
        content = data.get('content', '')
        print('Content Type in validate:', content_type)
        print('Content Length in validate:', len(content))
        if content_type in ['application/base64', 'image/png;base64', 'image/jpeg;base64']:
            if not content:
                raise serializers.ValidationError("Content is required for image content types.")
        else:
            if not content:
                raise serializers.ValidationError("Content is required for text content types.")

        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        content_type = representation.get('contentType')
        if content_type in ['application/base64', 'image/png;base64', 'image/jpeg;base64']:
            if not representation.get('content'):
                # Read the image file and encode it to base64
                if instance.image:
                    try:
                        with instance.image.open('rb') as image_file:
                            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                            representation['content'] = encoded_image
                    except Exception as e:
                        representation['content'] = ''
                else:
                    representation['content'] = ''
        return representation




class FollowSerializer(serializers.ModelSerializer):
    type = serializers.CharField(default='follow')
    summary = serializers.CharField(required=False, allow_blank=True)
    actor = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), source='follower')
    object = serializers.PrimaryKeyRelatedField(queryset=Author.objects.all(), source='following')

    class Meta:
        model = Follow
        fields = ['id', 'type', 'summary', 'actor', 'object', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

class FollowersSerializer(serializers.Serializer):
    type = serializers.CharField(default="followers")
    followers = serializers.ListField(
        child=AuthorSerializer()
    )
    """followers = serializers.SerializerMethodField()

    def get_followers(self,obj):
        return AuthorSerializer(obj,many=True)"""

class PostSerializer1(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    id = serializers.URLField(read_only=True)
    page = serializers.URLField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)
    content_type = serializers.ChoiceField(choices=[
        ('text/markdown', 'Markdown'),
        ('text/plain', 'Plaintext'),
        ('application/base64', 'Image'),
        ('image/png;base64', 'PNG'),
        ('image/jpeg;base64', 'JPEG'),
    ])
    content = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False, allow_null=True)
    visibility = serializers.ChoiceField(choices=Post.VISIBILITY_CHOICES)
    author = AuthorSerializer(read_only=True)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.content_type = validated_data.get('content_type', instance.content_type)
        instance.content = validated_data.get('content', instance.content)
        instance.visibility = validated_data.get('visibility', instance.visibility)

        # Update image if provided
        if 'image' in validated_data:
            instance.image = validated_data.get('image')

        instance.save()
        return instance

    def validate(self, data):
        content_type = data.get('content_type')
        content = data.get('content', '')
        image = data.get('image')

        if content_type in ['application/base64', 'image/png;base64', 'image/jpeg;base64']:
            if not content and not image and not self.instance.image:
                raise serializers.ValidationError("Image content or base64 data is required for image content types.")
        else:
            if not content:
                raise serializers.ValidationError("Content is required for text content types.")

        return data


