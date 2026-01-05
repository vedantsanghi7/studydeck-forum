from django.contrib import admin
from .models import (
    UserProfile, Course, Resource, Category, Thread, Reply, 
    Upvote, Tag, ThreadTag, Report
)

admin.site.register(UserProfile)
admin.site.register(Course)
admin.site.register(Resource)
admin.site.register(Category)
admin.site.register(Thread)
admin.site.register(Reply)
admin.site.register(Upvote)
admin.site.register(Tag)
admin.site.register(ThreadTag)
admin.site.register(Report)
