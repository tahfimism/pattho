from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.utils import timezone

from .models import (
    Subject, Chapter, Topic
)

from planner.models import PlannedTask
from users.models import UserProfile


from django_json_widget.widgets import JSONEditorWidget
from django.db import models


class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view))
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        context = {
            'total_users': UserProfile.objects.count(),
            'recent_users': UserProfile.objects.order_by('-id')[:5],
            'active_tasks': PlannedTask.objects.filter(date=timezone.now().date()).count(),
        }
        return render(request, 'admin/dashboard.html', context)


    


# Subject Admin
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'chapter_count', 'chapter_list')
    search_fields = ('name',)
    list_per_page = 20
    
    def chapter_list(self, obj):
        chapters = obj.chapters.all().order_by('chapter_number')[:5]
        names = ", ".join([c.title for c in chapters])
        if obj.chapters.count() > 5:
            names += "..."
        return names
    chapter_list.short_description = 'First 5 Chapters'



# Chapter Admin
@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'chapter_number', 'topic_count', 'importance_summary', 'recommended_time')
    list_filter = ('subject',)
    search_fields = ('title', 'subject__name')
    list_select_related = ('subject',)
    list_per_page = 20
    
    def importance_summary(self, obj):
        return format_html(
            "HSC:{} Eng:{} Med:{}",
            obj.importance.get('hsc', 0),
            obj.importance.get('engineering', 0),
            obj.importance.get('medical', 0)
        )
    importance_summary.short_description = 'Importance'
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }



# Topic Admin
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'order', 'time_percent', 'resources', 'importance_summary')
    list_filter = ('chapter__subject', 'chapter')
    search_fields = ('title', 'description')
    list_select_related = ('chapter__subject',)
    raw_id_fields = ('chapter',)
    list_per_page = 30
    
    def importance_summary(self, obj):
        return format_html(
            "HSC:{} Eng:{} Med:{}",
            obj.importance.get('hsc', 0),
            obj.importance.get('engineering', 0),
            obj.importance.get('medical', 0)
        )
    importance_summary.short_description = 'Importance'
    
    def resources(self, obj):
        if obj.resource_link:
            links = obj.resource_link.split(',')
            return format_html(
                '<div style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">{}</div>',
                ", ".join([link.strip()[:20] + '...' for link in links[:2]])
            )
        return "-"
    resources.short_description = 'Resource Links'









# Custom Admin Site Settings
admin.site.site_header = "StudyTracker Admin"
admin.site.site_title = "StudyTracker Administration"
admin.site.index_title = "Dashboard"