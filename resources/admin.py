from django.contrib import admin
from .models import Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'resource_type', 'uploaded_by', 'uploaded_at', 'is_published', 'download_count')
    list_filter = ('subject', 'resource_type', 'is_published', 'year_levels')
    search_fields = ('title', 'original_name')
    readonly_fields = ('original_name', 'file_size', 'download_count', 'uploaded_at', 'updated_at')