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
    list_display = (
        'user',
        'chapter',
        'overall_progress',
        'p_book',
        'p_note',
        'p_mcq',
        'p_cq',
        'p_theory',
        'skip',
        'time_given',
    )
    list_filter = (
        'skip',
        'chapter__subject',
        'p_book',
        'p_note',
        'p_mcq',
        'p_cq',
        'p_theory',
    )
    search_fields = ('user__username', 'chapter__title')
    list_select_related = ('user', 'chapter__subject')
    list_per_page = 30

    actions = ['reset_progress']

    def reset_progress(self, request, queryset):
        updated = queryset.update(
            p_book=False,
            p_note=False,
            p_mcq=False,
            p_cq=False,
            p_theory=False,
            overall_progress=0.0,
            time_given=0.0,
            skip=False,
        )
        self.message_user(request, f"{updated} progress records reset.")
    reset_progress.short_description = "Reset selected progress"
