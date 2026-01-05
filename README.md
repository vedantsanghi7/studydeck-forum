# StudyDeck Forum

StudyDeck Forum is a community-driven discussion platform built with Django. It serves the student platform body by providing easy access to notes, PYQs (Previous Year Questions), and course handouts, along with a forum for discussions and resource sharing.

## Quick Start

Quick setup:
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Features

### Bonus Features Implemented

- PostgreSQL Database - Full PostgreSQL support with fuzzy search
- Markdown Support - Rich text rendering in posts with sanitization
- Rate Limiting - Spam prevention on forms (5 threads/min, 10 replies/min)
- Email Notifications - Automatic notifications for thread replies
- Fuzzy Search - PostgreSQL trigram similarity for better search results
- Sorting Options - Sort threads/replies by latest, popular, or most upvoted

### Phase 0: Base Architecture

- Authentication & User Profiles
  - Google OAuth login via Django AllAuth
  - BITs email authentication support
  - User profiles with full name, image, and email metadata
  - Extended user profile model with moderator capabilities

- Foundation Models
  - Course Model: Stores course information (Code, Title, Department)
  - Resource Model: Stores course resources (Title, Type, Link)

### Phase 1: Core Forum Features

- User Roles & Permissions
  - Student User: Default role, can create threads, reply, and like posts. Can only edit/delete own content.
  - Moderator: Privileged role with ability to delete any content, lock threads, and resolve reports.

- Categories
  - Organized discussion categories (e.g., "General Queries", "Exam Prep")
  - Each category has a unique slug for URL generation
  - Threads must belong to a specific category

- Threads (Discussions)
  - Core discussion starting point
  - Fields: Title, Content, Author, Created Timestamp
  - Can be linked to Courses or Resources
  - Pagination support (10 threads per page)
  - Thread locking capability (moderator only)

- Replies (Posts)
  - Replies to threads from community members
  - Proper permission enforcement (users can only edit/delete own replies)
  - Soft delete functionality (is_deleted boolean field)
  - Moderators can delete any reply

- Interactivity
  - Upvotes/Likes: Users can upvote threads and replies
  - Tags: Flexible tagging system (e.g., #midsem, #quiz1, #urgent)
  - Tag-based filtering and search

- Reporting System
  - Users can report inappropriate content
  - Reason field for explanation
  - Resolution status (Pending, Resolved)
  - Moderators can view and resolve reports

## Technical Stack

- Framework: Django 5.2.8
- Database: PostgreSQL (with SQLite fallback for development)
- Authentication: Django AllAuth with Google OAuth
- Frontend: Bootstrap 5.3.0
- Markdown: markdown + bleach for sanitization
- Rate Limiting: django-ratelimit
- Deployment: Compatible with Render, Python Anywhere, Heroku, AWS, etc.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd studydeck
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root (optional, for production):
   ```
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com
   DATABASE_URL=postgresql://user:password@localhost/dbname
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Forum: http://127.0.0.1:8000/forum/
   - Admin: http://127.0.0.1:8000/admin/

## Google OAuth Configuration

To enable Google OAuth login:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URIs:
   - `http://127.0.0.1:8000/accounts/google/login/callback/` (development)
   - `https://yourdomain.com/accounts/google/login/callback/` (production)
6. Add credentials to Django admin:
   - Go to `/admin/sites/site/` and ensure Site is configured
   - Go to `/admin/socialaccount/socialapp/` and add Google provider
   - Add your Client ID and Secret Key

## Feature Walkthrough

### For Students

1. **Registration/Login**
   - Click "Sign Up" or "Login" in the navigation bar
   - Use Google OAuth or email/password
   - BITs email validation is supported

2. **Creating a Thread**
   - Click "New Thread" in navigation
   - Fill in title, content, select category
   - Optionally link to a course or resource
   - Add tags (comma-separated)
   - Submit

3. **Participating in Discussions**
   - Browse categories or search for topics
   - Click on a thread to view details
   - Reply to threads (if not locked)
   - Upvote helpful threads/replies
   - Report inappropriate content

4. **Managing Your Content**
   - Edit or delete your own threads/replies
   - View your profile to see all your contributions

### For Moderators

1. **Moderation Tools**
   - Access "Reports" link in navigation
   - View all reported content
   - Resolve reports by marking them as resolved
   - Lock/unlock threads to prevent further replies
   - Delete any content (not just your own)

2. **User Management**
   - Promote users to moderators via Django admin
   - Manage user profiles and permissions

## Design Decisions

### Database Structure

- UserProfile: Extended user model to store additional metadata (full_name, image, bits_email, is_moderator)
- Course & Resource: Foundation models for linking forum discussions to academic content
- Category: Hierarchical organization of discussions
- Thread & Reply: Core discussion models with proper relationships
- Upvote: Many-to-many relationship for likes (prevents duplicate upvotes)
- Tag & ThreadTag: Flexible tagging system with many-to-many relationship
- Report: Reporting system with status tracking and resolution

### Permission System

Permission checks are implemented at the view level. Users can only edit/delete their own content. Moderators bypass ownership checks. Soft delete for replies preserves data integrity.

### Pagination

Threads and replies are paginated with 10 items per page using Django's Paginator.

### Frontend Design

Bootstrap 5.3.0 provides responsive UI with Bootstrap Icons. Card-based layout ensures better visual hierarchy and works on both mobile and desktop.

## Deployment

### Python Anywhere

1. Upload your code via Git or file upload
2. Create a web app and configure it to use your virtual environment
3. Set up static files using WhiteNoise or Python Anywhere's static files configuration
4. Configure environment variables
5. Run migrations: `python manage.py migrate`
6. Collect static files: `python manage.py collectstatic`

### Render

1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `gunicorn studydeck.wsgi:application`
4. Add environment variables
5. Deploy

### AWS / Other Platforms

Follow standard Django deployment practices:
- Set `DEBUG=False` in production
- Configure `ALLOWED_HOSTS`
- Use PostgreSQL database
- Set up static file serving (WhiteNoise or S3)
- Configure environment variables securely

## Project Structure

```
studydeck/
├── manage.py
├── requirements.txt
├── README.md
├── studydeck/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── forum/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── signals.py
│   ├── adapters.py
└── templates/
    ├── base.html
    └── forum/
        ├── home.html
        ├── category_detail.html
        ├── thread_detail.html
        ├── thread_create.html
        ├── thread_edit.html
        ├── thread_delete.html
        ├── reply_edit.html
        ├── reply_delete.html
        ├── report_create.html
        ├── report_list.html
        ├── report_resolve.html
        ├── user_profile.html
        └── search.html
```

## Contributing

This is a project for StudyDeck. For contributions, please follow standard Django best practices and ensure all tests pass.

## License

This project is developed for StudyDeck platform.

## Support

For issues or questions, please contact the StudyDeck technical team.
