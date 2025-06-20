from django.contrib import admin
from .models import AdminActivity

@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'target_user', 'target_donation', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('description',)
