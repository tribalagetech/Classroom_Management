# schoolcalendar/admin.py
from django.contrib import admin
from .models import CalendarEvent, Term


@admin.action(description='Mark selected as confirmed')
def mark_confirmed(modeladmin, request, queryset):
    queryset.update(confirmed=True)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'start_date', 'end_date', 'weeks', 'confirmed')
    list_filter = ('year', 'confirmed')
    actions = [mark_confirmed]


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'confirmed')
    list_filter = ('event_type', 'confirmed')
    search_fields = ('title',)
    date_hierarchy = 'start_date'
    actions = [mark_confirmed]