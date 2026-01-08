from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse


class UserProfile(models.Model):
    """Extended user profile with metadata"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True)
    image = models.URLField(blank=True, null=True)
    bits_email = models.EmailField(unique=True, null=True, blank=True)
    is_moderator = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.user.username

    def get_absolute_url(self):
        return reverse('forum:user_profile', kwargs={'user_id': self.user.id})


class Course(models.Model):
    """Course model representing academic courses"""
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title}"


class Resource(models.Model):
    """Resource model for course materials"""
    RESOURCE_TYPES = [
        ('PDF', 'PDF'),
        ('Video', 'Video'),
        ('Link', 'Link'),
    ]

    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    link = models.URLField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Category(models.Model):
    """Forum categories for organizing discussions"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('forum:category_detail', kwargs={'slug': self.slug})


class Tag(models.Model):
    """Tags for categorizing threads"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Thread(models.Model):
    """Discussion thread - starting point of a conversation"""
    title = models.CharField(max_length=255)
    content = models.TextField()
    content_html = models.TextField(blank=True, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='threads')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='threads')
    resource = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True, related_name='threads')
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        from .utils import render_markdown
        if self.content:
            self.content_html = render_markdown(self.content)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('forum:thread_detail', kwargs={'pk': self.pk})

    def get_reply_count(self):
        return self.replies.filter(is_deleted=False).count()

    def get_upvote_count(self):
        return self.upvotes.count()


class ThreadTag(models.Model):
    """Many-to-many relationship between Threads and Tags"""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='thread_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='thread_tags')

    class Meta:
        unique_together = ['thread', 'tag']

    def __str__(self):
        return f"{self.thread.title} - {self.tag.name}"


class Reply(models.Model):
    """Reply/Post within a thread"""
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    content_html = models.TextField(blank=True, editable=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name_plural = "Replies"

    def __str__(self):
        return f"Reply by {self.author.username} on {self.thread.title}"

    def save(self, *args, **kwargs):
        from .utils import render_markdown
        if self.content:
            self.content_html = render_markdown(self.content)
        super().save(*args, **kwargs)

    def get_upvote_count(self):
        return self.upvotes.count()


class Upvote(models.Model):
    """Upvote/Like system for threads and replies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upvotes')
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='upvotes', null=True, blank=True)
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name='upvotes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ['user', 'thread'],
            ['user', 'reply']
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(thread__isnull=False, reply__isnull=True) |
                    models.Q(thread__isnull=True, reply__isnull=False)
                ),
                name='upvote_must_have_thread_or_reply'
            )
        ]

    def __str__(self):
        if self.thread:
            return f"{self.user.username} upvoted {self.thread.title}"
        return f"{self.user.username} upvoted reply {self.reply.id}"


class Report(models.Model):
    """Reporting system for inappropriate content"""
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Resolved', 'Resolved'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(thread__isnull=False, reply__isnull=True) |
                    models.Q(thread__isnull=True, reply__isnull=False)
                ),
                name='report_must_have_thread_or_reply'
            )
        ]

    def __str__(self):
        content = self.thread.title if self.thread else f"Reply {self.reply.id}"
        return f"Report on {content} by {self.reporter.username}"
