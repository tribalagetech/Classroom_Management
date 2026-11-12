# teachers/admin.py
from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'teacher_file_number', 'class_assigned', 'email')
    search_fields = ('last_name', 'first_name', 'teacher_file_number')