from django.urls import path
from . import views

app_name = 'forum'

urlpatterns = [
    path('', views.forum_home, name='forum_home'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('thread/create/', views.thread_create, name='thread_create'),
    path('thread/<int:pk>/', views.thread_detail, name='thread_detail'),
    path('thread/<int:pk>/edit/', views.thread_edit, name='thread_edit'),
    path('thread/<int:pk>/delete/', views.thread_delete, name='thread_delete'),
    path('thread/<int:pk>/lock/', views.thread_lock, name='thread_lock'),
    path('thread/<int:pk>/reply/', views.reply_create, name='reply_create'),
    path('reply/<int:reply_id>/edit/', views.reply_edit, name='reply_edit'),
    path('reply/<int:reply_id>/delete/', views.reply_delete, name='reply_delete'),
    path('upvote/toggle/', views.upvote_toggle, name='upvote_toggle'),
    path('report/', views.report_create, name='report_create'),
    path('reports/', views.report_list, name='report_list'),
    path('report/<int:report_id>/resolve/', views.report_resolve, name='report_resolve'),
    path('user/<int:user_id>/', views.user_profile, name='user_profile'),
    path('search/', views.search, name='search'),
]
