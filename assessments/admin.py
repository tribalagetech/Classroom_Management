# assessments/admin.py (entering scores here works until the teacher page exists)
from django.contrib import admin
from .models import Assessment, AssessmentScore


class ScoreInline(admin.TabularInline):
    model = AssessmentScore
    extra = 0
    autocomplete_fields = ('student',)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'year_level', 'year', 'term', 'max_points', 'date')
    list_filter = ('year', 'term', 'year_level', 'subject')
    search_fields = ('title',)
    inlines = [ScoreInline]