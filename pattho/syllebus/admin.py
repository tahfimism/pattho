from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.utils import timezone

from .models import (
    UserProfile, Subject, Chapter, Topic, UserProgress, StudyRoutine,
    PlannedTask, ToDoItem, Badge, UserBadge
)

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


    



# UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'stream', 'xp', 'streak', 'show_on_leaderboard', 'progress_bar')
    list_filter = ('stream', 'show_on_leaderboard')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user',)
    list_per_page = 20
    
    def progress_bar(self, obj):
        return format_html(
            '<progress value="{}" max="100"></progress> {}%',
            obj.overall_progress_cache,
            obj.overall_progress_cache
        )
    progress_bar.short_description = 'Progress'

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

# UserProgress Admin
@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'status', 'skip', 'time_given',)
    list_filter = ('status', 'skip', 'topic__chapter__subject')
    search_fields = ('user__user__username', 'topic__title')
    raw_id_fields = ('user', 'topic')
    list_select_related = ('user__user', 'topic__chapter__subject')
    list_per_page = 30
    
    # Add custom action to reset progress
    actions = ['reset_progress']
    
    def reset_progress(self, request, queryset):
        updated = queryset.update(status='NS', time_given=0.0)
        self.message_user(request, f"{updated} progress records reset")
    reset_progress.short_description = "Reset selected progress"

# StudyRoutine Admin
@admin.register(StudyRoutine)
class StudyRoutineAdmin(admin.ModelAdmin):
    list_display = ('user', 'daily_minutes', 'start_date', 'end_date', 'duration_days')
    list_filter = ('start_date', 'end_date')
    search_fields = ('user__user__username',)
    raw_id_fields = ('user',)
    list_per_page = 20
    
    def duration_days(self, obj):
        return (obj.end_date - obj.start_date).days
    duration_days.short_description = 'Duration (days)'

# PlannedTask Admin
@admin.register(PlannedTask)
class PlannedTaskAdmin(admin.ModelAdmin):
    list_display = ('date', 'routine', 'topic', 'allocated_minutes', 'completed')
    list_filter = ('completed', 'date', 'routine__user')
    search_fields = ('topic__title', 'routine__user__user__username')
    raw_id_fields = ('routine', 'topic')
    list_select_related = ('topic__chapter__subject', 'routine__user__user')
    date_hierarchy = 'date'
    list_per_page = 30

# ToDoItem Admin
@admin.register(ToDoItem)
class ToDoItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'completed', 'created_short')
    list_filter = ('completed',)
    search_fields = ('title', 'user__user__username')
    raw_id_fields = ('user',)
    list_per_page = 30
    
    def created_short(self, obj):
        return obj.created_at.strftime("%b %d") if obj.created_at else ""
    created_short.short_description = 'Created'
    created_short.admin_order_field = 'created_at'

# Badge Admin
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'xp_reward', 'user_count')
    search_fields = ('name', 'description')
    list_per_page = 20
    
    def user_count(self, obj):
        return obj.userbadge_set.count()
    user_count.short_description = 'Users'

# UserBadge Admin
@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', )
    list_filter = ('badge',)
    search_fields = ('user__user__username', 'badge__name')
    raw_id_fields = ('user', 'badge')
    list_select_related = ('user__user', 'badge')
    list_per_page = 30
    


# Custom Admin Site Settings
admin.site.site_header = "StudyTracker Admin"
admin.site.site_title = "StudyTracker Administration"
admin.site.index_title = "Dashboard"