from django.contrib import admin
from .models import ToDoItem

# Register your models here.
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