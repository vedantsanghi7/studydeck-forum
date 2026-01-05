import markdown
import bleach
from django.utils.safestring import mark_safe
from django.conf import settings


def render_markdown(text):
    """Render markdown text to HTML with sanitization"""
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=settings.MARKDOWN_EXTENSIONS)
    html = md.convert(text)
    
    # Allowed HTML tags
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'a', 'img',
        'table', 'thead', 'tbody', 'tr', 'th', 'td'
    ]
    
    # Allowed attributes
    allowed_attributes = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'code': ['class'],
    }
    
    # Sanitize HTML
    cleaned = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )
    
    return mark_safe(cleaned)
