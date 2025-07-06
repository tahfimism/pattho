from django.contrib import admin
from .models import StudyRoutine, PlannedTask

# Register your models here.
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