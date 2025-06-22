from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from urllib.parse import urlparse

from django.contrib.auth.hashers import make_password

class NodeCredential(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):  # Avoid rehashing an already hashed password
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class LocalVars(models.Model):
    # NOTE: I have left it as a CharField for now instead of a URLField
    # because in the Post model, the host never starts with http:// even though it is URLField
    # so it is technically not a URLField. I didn't want to change it
    # to a charfield and risk screwing things up so I left it for now.
    #
    # when you make a new node just create a single entry and put the host name
    # Example: part3-404-ffe847524acc.herokuapp.com
    #
    # TODO: write script to auto generate node_host on node creation

    # host of current url. 
    node_host = models.CharField(unique=True, max_length=100)

    class Meta:
        verbose_name_plural = "Local Variables"

class RemoteNode(models.Model):
    """
    Model to manage other nodes that this node can connect to.
    """
    node_url = models.URLField(unique=True)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.node_url

class AuthorManager(BaseUserManager):
    def create_user(self, email, display_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Authors must have an email address')
        if not display_name:
            raise ValueError('Authors must have a display name')
        email = self.normalize_email(email)
        author = self.model(email=email, display_name=display_name, **extra_fields)
        author.set_password(password)
        author.save(using=self._db)
        return author

    def create_superuser(self, email, display_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)  # Add this line

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_active') is not True:
            raise ValueError('Superuser must have is_active=True.')

        return self.create_user(email, display_name, password, **extra_fields)

class Author(AbstractBaseUser, PermissionsMixin):
    uid = models.UUIDField(default=uuid.uuid4, editable=False)
    id = models.URLField(unique=True, blank=True, primary_key=True)
    host = models.URLField()
    display_name = models.CharField(max_length=100)
    github = models.URLField(blank=True, null=True)

    #url used for api objects, can't use ImageField b/c it messes with the serializer and
    #also we don't store remote user's profile pictures on our node
    profile_image = models.URLField(blank=True,null=True)
    profile_image_file = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    page = models.URLField(blank=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_remote = models.BooleanField(default=False)  # New field to distinguish remote authors

    objects = AuthorManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"{self.host.rstrip('/')}/authors/{self.uid}"
        self.page = f"{self.get_host_no_api().rstrip('/')}/authors/{self.uid}"
        if self.profile_image_file:
            self.profile_image = f"{self.get_host_no_api().rstrip('/')}/{self.profile_image_file.url.lstrip('/')}"
        if not self.profile_image:
            self.profile_image = "https://upload.wikimedia.org/wikipedia/commons/a/ac/Default_pfp.jpg"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name

    #gets the host url without the api or api/ at the end, if there is one
    def get_host_no_api(self):
        url = self.host
        if url[-3:] == "api":
            url = url[:-3]
        elif url[-4:] == "api/":
            url = url[:-4]
        return url

#class for "comments" object, DO NOT CONFUSE WITH "Comment." Comments contains information
#about the comments that correspond to a post. See the example object
#in the project specs for clarification:
#https://uofa-cmput404.github.io/general/project.html#example-comments-object
class Comments(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    page = models.URLField()
    id = models.URLField()
    size = models.PositiveIntegerField(default=5)

    @property
    def count(self):
        return len(self.comment_set.all())

    @property
    def src(self):
        return self.comment_set.all()

#class for "likes" object, DO NOT CONFUSE WITH "Like." Likes contains information
#about the likes that correspond to a post or comment. See the example object
#in the project specs for clarification:
#https://uofa-cmput404.github.io/general/project.html#example-likes-object
class Likes(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    page = models.URLField()
    id = models.URLField()
    size = models.PositiveIntegerField(default=5)

    @property
    def count(self):
        return len(self.like_set.all())

    @property
    def src(self):
        return self.like_set.all()

class Post(models.Model):
    #uid is serial in the project specs
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host = models.URLField()
    #author_url is automatically assigned based on other values
    author_url = models.URLField(editable=False)

    title = models.CharField(max_length=255)
    #id is automatically assigned based on other values
    id = models.URLField(unique=True,blank=True)  # The full API URL of the post (including node address)
    #TODO maybe don't cascade?
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    comments = models.ForeignKey(Comments, blank=True, null=True, on_delete=models.CASCADE)
    likes = models.ForeignKey(Likes, blank=True, null=True, on_delete=models.CASCADE)
    description = models.TextField()
    content_type = models.CharField(max_length=50, choices=[
        ('text/markdown', 'Markdown'),
        ('text/plain', 'Plaintext'),
        ('application/base64', 'Image'),
        ('image/png;base64', 'PNG'),
        ('image/jpeg;base64', 'JPEG'),
    ])
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='post_images/', blank=True, null=True)
    published_at = models.DateTimeField(auto_now_add=True)

    #constant values for visiblility, I changed them to variables so they're easier to change if we need to
    PUBLIC_VISIBILITY = "PUBLIC"
    UNLISTED_VISIBILITY = "UNLISTED"
    FRIENDS_VISIBILITY = "FRIENDS"
    DELETED_VISIBILITY = "DELETED"
    VISIBILITY_CHOICES = [
        (PUBLIC_VISIBILITY, 'Public'),
        (UNLISTED_VISIBILITY, 'Unlisted'),
        (FRIENDS_VISIBILITY, 'Friends Only'),
        (DELETED_VISIBILITY, 'Deleted'),
    ]
    visibility = models.CharField(max_length=50, choices=VISIBILITY_CHOICES)
    page = models.URLField() # Post page displayed to a client

    # TODO: figure out how to have 'http://' in self.host
    def save(self, *args, **kwargs):
        is_remote = False

        # Ensure unique `id` and `page` values
        if not self.id:
            self.id = f"{self.author.host.rstrip("/")}/authors/{self.author.uid}/posts/{self.uid}"
        elif not self.host:
            is_remote = True
            parsed = urlparse(self.id)
            self.host = parsed.netloc

        if not self.page:
            self.page = f"{self.author.get_host_no_api().rstrip("/")}/authors/{self.author.uid}/posts/{self.uid}"
        if not self.author_url:
            self.author_url = f"{self.author.host.rstrip("/")}/authors/{self.author.uid}"

        # Ensure `comments` and `likes` objects are created
        if not self.comments:
            self.comments = Comments.objects.create(
                page=f"{self.author.get_host_no_api().rstrip("/")}/authors/{self.author.uid}/posts/{self.uid}",
                id=f"{self.author.host.rstrip("/")}/authors/{self.author.uid}/posts/{self.uid}/comments"
            )
        if not self.likes:
            self.likes = Likes.objects.create(
                page=f"{self.author.get_host_no_api().rstrip("/")}/authors/{self.author.uid}/posts/{self.uid}",
                id=f"{self.author.host.rstrip("/")}/authors/{self.author.uid}/posts/{self.uid}/likes"
            )
        
        if self.content_type not in ['text/markdown', 'text/plain'] and not self.content.startswith('data'):
            self.content = f"data:{self.content_type},{self.content}"
        
        if is_remote:
            self.page = f"http://{LocalVars.objects.first().node_host.rstrip("/")}/authors/{self.author.uid}/posts/{self.uid}"

        super().save(*args, **kwargs)

    def add_comment(self, author, comment_text, content_type="text/markdown"):
        comment = Comment(
            author=author,
            comment=comment_text,
            content_type=content_type,
            post=self.id,
            comments=self.comments,
            page=f"{self.page}/comments"
        )
        comment.save()
        return comment

    def add_like(self, author):
        like = Like(
            author=author,
            object=self.id,
            likes=self.likes
        )
        like.save()
        return like

    def __str__(self):
        return f"Post by {self.author_url}: {self.title}"

class Repost(models.Model):
    post_url = models.URLField()    #FQID of reposted post
    reposter = models.ForeignKey(Author,on_delete=models.CASCADE)
    published_at = models.DateTimeField(auto_now_add=True)  #time when this post was reposted


class Comment(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) # API URL for a comment
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    #author_url = models.URLField()  #FQID of author, can't be a foreign key b/c likes from remote authors get stored on our node
    comment = models.TextField()
    content_type = models.CharField(max_length=50, choices=[
        ('text/markdown', 'Markdown'),
        ('text/plain', 'Plaintext'),
        ('application/base64', 'Image'),
        ('image/png;base64', 'PNG'),
        ('image/jpeg;base64', 'JPEG'),
    ])
    published = models.DateTimeField(auto_now_add=True)
    id = models.URLField(unique=True,blank=True)    #FQID of comment
    post = models.URLField()                     #FQID of post comment belongs to
    page = models.URLField()
    comments = models.ForeignKey(Comments, on_delete=models.CASCADE)  #comments object for the post this comment is on
    likes = models.ForeignKey(Likes, blank=True, null=True, on_delete=models.CASCADE)  #likes on this comment

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"{self.author.id.rstrip('/')}/commented/{self.uid}" #TODO maybe also page field
        if not self.likes:
            self.likes = Likes()
            self.likes.page = f"{self.page}"    #TODO maybe make separate
            self.likes.id = f"{self.id}/likes"
            self.likes.save()
        super().save(*args, **kwargs)
    
    def add_like(self, author):
        like = Like(
            author=author,
            object=self.id,
            likes=self.likes
        )
        like.save()
        return like


class Like(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    published = models.DateTimeField(auto_now_add=True)
    id = models.URLField(unique=True, blank=True)
    object = models.URLField()
    likes = models.ForeignKey(Likes, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('author', 'object')

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"{self.author.id.rstrip('/')}/liked/{self.uid}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.author.display_name} liked {self.object}"



class Follow(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    follower = models.ForeignKey(Author, related_name='following_set', on_delete=models.CASCADE)
    following = models.ForeignKey(Author, related_name='followers_set', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.display_name} follows {self.following.display_name} - {self.status}"

class Inbox(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local_author = models.ForeignKey(Author, related_name='inbox_items', on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    activity_data = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Inbox Item for {self.local_author.display_name} - {self.activity_type}"
