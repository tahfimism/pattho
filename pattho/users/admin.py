from django.contrib import admin
from .models import UserProfile, UserProgress
from django.utils.html import format_html


# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'stream', 'xp', 'streak', 'show_on_leaderboard', 'progress_bar')
    list_filter = ('stream', 'show_on_leaderboard')
    search_fields = ('username', 'email')
    list_per_page = 20

    def progress_bar(self, obj):
        return format_html(
            '<progress value="{}" max="100"></progress> {}%',
            obj.overall_progress_cache,
            obj.overall_progress_cache
        )
    progress_bar.short_description = 'Progress'


    # UserProgress Admin
@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'status', 'skip', 'time_given',)
    list_filter = ('status', 'skip', 'topic__chapter__subject')
    search_fields = ('user__username', 'topic__title')
    list_select_related = ('user', 'topic__chapter__subject')
    list_per_page = 30
    
    # Add custom action to reset progress
    actions = ['reset_progress']
    
    def reset_progress(self, request, queryset):
        updated = queryset.update(status='NS', time_given=0.0)
        self.message_user(request, f"{updated} progress records reset")
    reset_progress.short_description = "Reset selected progress"