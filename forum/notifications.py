from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from .models import Thread, Reply


def send_reply_notification(reply):
    """Send email notification when someone replies to a thread"""
    thread = reply.thread
    thread_author = thread.author
    
    # Don't send notification if the reply author is the thread author
    if reply.author == thread_author:
        return
    
    # Check if user has email
    if not thread_author.email:
        return
    
    subject = f'New reply to your thread: {thread.title}'
    
    # Get all users who have replied to this thread (excluding the current reply author)
    mentioned_users = extract_mentions(reply.content)
    
    # Send to thread author
    context = {
        'thread': thread,
        'reply': reply,
        'reply_author': reply.author,
        'site_url': settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost:8000',
    }
    
    html_message = render_to_string('forum/emails/reply_notification.html', context)
    plain_message = render_to_string('forum/emails/reply_notification.txt', context)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[thread_author.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending email notification: {e}")
    
    # Send to mentioned users
    for username in mentioned_users:
        try:
            user = User.objects.get(username=username)
            if user.email and user != reply.author:
                send_mail(
                    subject=f'You were mentioned in: {thread.title}',
                    message=f'{reply.author.get_full_name() or reply.author.username} mentioned you in a reply.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
        except User.DoesNotExist:
            pass


def extract_mentions(text):
    """Extract @username mentions from text"""
    import re
    mentions = re.findall(r'@(\w+)', text)
    return list(set(mentions))  # Remove duplicates
