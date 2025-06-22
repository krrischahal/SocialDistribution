from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from .forms import AuthorCreationForm

class AuthorAdmin(UserAdmin):
    add_form = AuthorCreationForm
    model = Author
    list_display = ('id','email', 'display_name', 'is_active', 'is_staff', 'is_remote')
    list_filter = ('is_active', 'is_staff')
    search_fields = ('email', 'display_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'display_name', 'host', 'github', 'profile_image', 'profile_image_file', 'bio', 'id', 'page')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'display_name', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser','is_remote'),
        }),
    )

class NodeCredentialAdmin(admin.ModelAdmin):
    list_display = ('username', 'created_at', 'updated_at')
    search_fields = ('username',)
    ordering = ('-updated_at',)

class RemoteNodeAdmin(admin.ModelAdmin):
    list_display = ('node_url', 'username', 'created_at', 'updated_at')
    search_fields = ('node_url', 'username')
    ordering = ('-created_at',)

admin.site.register(NodeCredential, NodeCredentialAdmin)
admin.site.register(RemoteNode, RemoteNodeAdmin)

admin.site.register(Author, AuthorAdmin)
admin.site.register(Post)
admin.site.register(Repost)
# admin.site.register(Comments)
admin.site.register(Comment)
# admin.site.register(Likes)
admin.site.register(Like)
admin.site.register(Follow)
admin.site.register(LocalVars)
