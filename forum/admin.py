from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, Course, Resource, Category, Thread, Reply, 
    Upvote, Tag, ThreadTag, Report
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'bits_email', 'is_moderator', 'created_at']
    list_filter = ['is_moderator', 'created_at']
    search_fields = ['user__username', 'user__email', 'full_name', 'bits_email']
    list_editable = ['is_moderator']
    raw_id_fields = ['user']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = ['full_name', 'bits_email', 'image', 'is_moderator']


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_is_moderator')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    
    def get_is_moderator(self, obj):
        try:
            return obj.profile.is_moderator
        except UserProfile.DoesNotExist:
            return False
    get_is_moderator.boolean = True
    get_is_moderator.short_description = 'Moderator'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

admin.site.register(Course)
admin.site.register(Resource)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'is_locked', 'created_at']
    list_filter = ['category', 'is_locked', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    raw_id_fields = ['author', 'category', 'course', 'resource']

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['thread', 'author', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['content', 'author__username', 'thread__title']
    raw_id_fields = ['thread', 'author']

admin.site.register(Upvote)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']

admin.site.register(ThreadTag)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'status', 'content_type', 'created_at', 'resolved_by']
    list_filter = ['status', 'created_at']
    search_fields = ['reason', 'reporter__username']
    raw_id_fields = ['reporter', 'thread', 'reply', 'resolved_by']
    
    def content_type(self, obj):
        return 'Thread' if obj.thread else 'Reply'
    content_type.short_description = 'Type'
