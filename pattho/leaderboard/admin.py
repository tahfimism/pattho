from django.contrib import admin
from .models import Badge, UserBadge

# Register your models here.
# Badge Admin
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'xp_reward', 'user_count')
    search_fields = ('name', 'description')
    list_per_page = 20
    
    def user_count(self, obj):
        return obj.users.count()
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
    
