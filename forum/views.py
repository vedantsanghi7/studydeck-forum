from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, F, Case, When, IntegerField
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from .models import (
    Category, Thread, Reply, Upvote, Tag, ThreadTag, Report,
    UserProfile, Course, Resource
)
from .forms import ThreadForm, ReplyForm, ReportForm
from .utils import render_markdown


def forum_home(request):
    """Home page showing all categories"""
    categories = Category.objects.annotate(
        thread_count=Count('threads')
    ).all()
    recent_threads = Thread.objects.select_related('author', 'category').order_by('-created_at')[:10]
    
    context = {
        'categories': categories,
        'recent_threads': recent_threads,
    }
    return render(request, 'forum/home.html', context)


def category_detail(request, slug):
    """View threads in a specific category"""
    category = get_object_or_404(Category, slug=slug)
    threads = Thread.objects.filter(category=category).select_related('author', 'category').annotate(
        reply_count=Count('replies', filter=Q(replies__is_deleted=False)),
        upvote_count=Count('upvotes')
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(threads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'forum/category_detail.html', context)


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@ratelimit(key='user', rate='10/h', method='POST', block=True)
@login_required
def thread_create(request):
    """Create a new thread"""
    if request.method == 'POST':
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.save()
            
            tag_names = request.POST.get('tags', '').split(',')
            for tag_name in tag_names:
                tag_name = tag_name.strip().lower()
                if tag_name:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    ThreadTag.objects.get_or_create(thread=thread, tag=tag)
            
            messages.success(request, 'Thread created successfully!')
            return redirect('forum:thread_detail', pk=thread.pk)
    else:
        form = ThreadForm()
    
    context = {
        'form': form,
        'categories': Category.objects.all(),
        'courses': Course.objects.all(),
    }
    return render(request, 'forum/thread_create.html', context)


def thread_detail(request, pk):
    """View thread details and replies"""
    thread = get_object_or_404(Thread.objects.select_related('author', 'category'), pk=pk)
    
    sort_by = request.GET.get('sort', 'latest')
    
    replies = Reply.objects.filter(thread=thread, is_deleted=False).select_related('author').annotate(
        upvote_count=Count('upvotes')
    )
    
    if sort_by == 'popular':
        replies = replies.order_by('-upvote_count', 'created_at')
    else:
        replies = replies.order_by('created_at')
    
    user_upvoted = False
    if request.user.is_authenticated:
        user_upvoted = Upvote.objects.filter(user=request.user, thread=thread).exists()
    
    paginator = Paginator(replies, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'thread': thread,
        'page_obj': page_obj,
        'user_upvoted': user_upvoted,
        'form': ReplyForm() if request.user.is_authenticated else None,
        'sort_by': sort_by,
    }
    return render(request, 'forum/thread_detail.html', context)


@login_required
def thread_edit(request, pk):
    """Edit a thread (only by author or moderator)"""
    thread = get_object_or_404(Thread, pk=pk)
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    if thread.author != request.user and not (user_profile and user_profile.is_moderator):
        messages.error(request, 'You do not have permission to edit this thread.')
        return redirect('forum:thread_detail', pk=pk)
    
    if request.method == 'POST':
        form = ThreadForm(request.POST, instance=thread)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thread updated successfully!')
            return redirect('forum:thread_detail', pk=pk)
    else:
        form = ThreadForm(instance=thread)
    
    context = {
        'form': form,
        'thread': thread,
    }
    return render(request, 'forum/thread_edit.html', context)


@login_required
def thread_delete(request, pk):
    """Delete a thread (only by author or moderator)"""
    thread = get_object_or_404(Thread, pk=pk)
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    if thread.author != request.user and not (user_profile and user_profile.is_moderator):
        messages.error(request, 'You do not have permission to delete this thread.')
        return redirect('forum:thread_detail', pk=pk)
    
    if request.method == 'POST':
        category_slug = thread.category.slug
        thread.delete()
        messages.success(request, 'Thread deleted successfully!')
        return redirect('forum:category_detail', slug=category_slug)
    
    return render(request, 'forum/thread_delete.html', {'thread': thread})


@login_required
def thread_lock(request, pk):
    """Lock/unlock a thread (moderator only)"""
    thread = get_object_or_404(Thread, pk=pk)
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    if not (user_profile and user_profile.is_moderator):
        messages.error(request, 'Only moderators can lock threads.')
        return redirect('forum:thread_detail', pk=pk)
    
    thread.is_locked = not thread.is_locked
    thread.save()
    
    action = 'locked' if thread.is_locked else 'unlocked'
    messages.success(request, f'Thread {action} successfully!')
    return redirect('forum:thread_detail', pk=pk)


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
@ratelimit(key='user', rate='30/h', method='POST', block=True)
@login_required
def reply_create(request, pk):
    """Create a reply to a thread"""
    thread = get_object_or_404(Thread, pk=pk)
    
    if thread.is_locked:
        messages.error(request, 'This thread is locked.')
        return redirect('forum:thread_detail', pk=pk)
    
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            reply.save()
            messages.success(request, 'Reply posted successfully!')
            return redirect('forum:thread_detail', pk=pk)
    
    return redirect('forum:thread_detail', pk=pk)


@login_required
def reply_edit(request, reply_id):
    """Edit a reply (only by author or moderator)"""
    reply = get_object_or_404(Reply, pk=reply_id)
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    if reply.author != request.user and not (user_profile and user_profile.is_moderator):
        messages.error(request, 'You do not have permission to edit this reply.')
        return redirect('forum:thread_detail', pk=reply.thread.pk)
    
    if request.method == 'POST':
        form = ReplyForm(request.POST, instance=reply)
        if form.is_valid():
            form.save()
            messages.success(request, 'Reply updated successfully!')
            return redirect('forum:thread_detail', pk=reply.thread.pk)
    else:
        form = ReplyForm(instance=reply)
    
    context = {
        'form': form,
        'reply': reply,
    }
    return render(request, 'forum/reply_edit.html', context)


@login_required
def reply_delete(request, reply_id):
    """Soft delete a reply (only by author or moderator)"""
    reply = get_object_or_404(Reply, pk=reply_id)
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    if reply.author != request.user and not (user_profile and user_profile.is_moderator):
        messages.error(request, 'You do not have permission to delete this reply.')
        return redirect('forum:thread_detail', pk=reply.thread.pk)
    
    if request.method == 'POST':
        reply.is_deleted = True
        reply.save()
        messages.success(request, 'Reply deleted successfully!')
        return redirect('forum:thread_detail', pk=reply.thread.pk)
    
    return render(request, 'forum/reply_delete.html', {'reply': reply})


@login_required
@require_POST
def upvote_toggle(request):
    """Toggle upvote on a thread or reply"""
    content_type = request.POST.get('content_type')
    content_id = request.POST.get('content_id')
    
    try:
        if content_type == 'thread':
            obj = get_object_or_404(Thread, pk=content_id)
            upvote = Upvote.objects.filter(user=request.user, thread=obj).first()
            if upvote:
                upvote.delete()
                upvoted = False
            else:
                Upvote.objects.create(user=request.user, thread=obj)
                upvoted = True
            count = obj.upvotes.count()
        elif content_type == 'reply':
            obj = get_object_or_404(Reply, pk=content_id)
            upvote = Upvote.objects.filter(user=request.user, reply=obj).first()
            if upvote:
                upvote.delete()
                upvoted = False
            else:
                Upvote.objects.create(user=request.user, reply=obj)
                upvoted = True
            count = obj.upvotes.count()
        else:
            return JsonResponse({'error': 'Invalid content type'}, status=400)
        
        return JsonResponse({
            'upvoted': upvoted,
            'count': count
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def report_create(request):
    """Create a report for inappropriate content"""
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.save()
            messages.success(request, 'Report submitted successfully. Moderators will review it.')
            return redirect('forum:forum_home')
    else:
        thread_id = request.GET.get('thread_id')
        reply_id = request.GET.get('reply_id')
        form = ReportForm(initial={
            'thread': thread_id,
            'reply': reply_id
        })
    
    context = {
        'form': form,
    }
    return render(request, 'forum/report_create.html', context)


@login_required
def report_list(request):
    """List all reports (moderator only)"""
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    if not (user_profile and user_profile.is_moderator):
        messages.error(request, 'Only moderators can view reports.')
        return redirect('forum:forum_home')
    
    reports = Report.objects.select_related('reporter', 'thread', 'reply').order_by('-created_at')
    
    context = {
        'reports': reports,
    }
    return render(request, 'forum/report_list.html', context)


@login_required
def report_resolve(request, report_id):
    """Resolve a report (moderator only)"""
    report = get_object_or_404(Report, pk=report_id)
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None
    
    if not (user_profile and user_profile.is_moderator):
        messages.error(request, 'Only moderators can resolve reports.')
        return redirect('forum:forum_home')
    
    if request.method == 'POST':
        report.status = 'Resolved'
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.save()
        messages.success(request, 'Report resolved successfully!')
        return redirect('forum:report_list')
    
    return render(request, 'forum/report_resolve.html', {'report': report})


def user_profile(request, user_id):
    """View user profile"""
    user = get_object_or_404(User, pk=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)
    threads = Thread.objects.filter(author=user).order_by('-created_at')[:10]
    replies = Reply.objects.filter(author=user, is_deleted=False).order_by('-created_at')[:10]
    
    context = {
        'profile_user': user,
        'profile': profile,
        'threads': threads,
        'replies': replies,
    }
    return render(request, 'forum/user_profile.html', context)


def search(request):
    """Search threads by title, content, or tags with fuzzy search"""
    query = request.GET.get('q', '')
    threads = Thread.objects.none()
    
    if query:
        from django.db import connection
        
        try:
            if connection.vendor == 'postgresql':
                from django.contrib.postgres.search import TrigramSimilarity
                
                threads = Thread.objects.annotate(
                    title_similarity=TrigramSimilarity('title', query),
                    content_similarity=TrigramSimilarity('content', query),
                ).filter(
                    Q(title_similarity__gt=0.1) |
                    Q(content_similarity__gt=0.1) |
                    Q(title__icontains=query) |
                    Q(content__icontains=query) |
                    Q(thread_tags__tag__name__icontains=query)
                ).distinct().select_related('author', 'category').annotate(
                    reply_count=Count('replies', filter=Q(replies__is_deleted=False)),
                    upvote_count=Count('upvotes')
                ).order_by('-title_similarity', '-content_similarity', '-created_at')
            else:
                raise ImportError("Not PostgreSQL")
        except (ImportError, AttributeError):
            threads = Thread.objects.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(thread_tags__tag__name__icontains=query)
            ).distinct().select_related('author', 'category').annotate(
                reply_count=Count('replies', filter=Q(replies__is_deleted=False)),
                upvote_count=Count('upvotes')
            ).order_by('-created_at')
    
    paginator = Paginator(threads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'page_obj': page_obj,
    }
    return render(request, 'forum/search.html', context)
