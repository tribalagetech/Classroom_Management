# students/admin.py
from django.contrib import admin
from .models import Guardian, PreviousSchool, Sibling, Student, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


# inlines show the related rows on the student's own page
class GuardianInline(admin.StackedInline):
    model = Guardian
    extra = 0
    max_num = 2

class PreviousSchoolInline(admin.TabularInline):
    model = PreviousSchool
    extra = 0

class SiblingInline(admin.TabularInline):
    model = Sibling
    extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'last_name', 'first_name', 'grade', 'subject_list', 'created_at')
    list_filter = ('grade', 'gender', 'subjects', 'created_at')
    search_fields = ('student_id', 'first_name', 'last_name')
    ordering = ('grade', 'last_name')
    readonly_fields = ('student_id', 'created_at')
    filter_horizontal = ('subjects',)
    inlines = [GuardianInline, PreviousSchoolInline, SiblingInline]

    fieldsets = [
        ('Student', {'fields': ['student_id', 'photo', 'first_name', 'last_name', 'date_of_birth',
                                'gender', 'nationality', 'religion', 'grade', 'starting_date', 'subjects']}),
        ('Contact and home', {'fields': ['postal_address', 'residential_address',
                                         'lives_with', 'transport_arrangements']}),
        ('School fee payer', {'fields': ['fee_payer', 'fee_payer_name', 'fee_payer_department']}),
        ('Emergency contact', {'fields': ['emergency_contact_name', 'emergency_contact_phone']}),
        ('Languages and health', {'fields': ['home_language', 'other_languages', 'disabilities',
                                             'special_needs', 'medical_condition',
                                             'doctor_name', 'doctor_phone']}),
        ('Declaration', {'fields': ['heard_about', 'photo_consent',
                                    'declaration_accepted', 'declaration_date']}),
        ('OFFICE USE ONLY', {'fields': ['admitted_grade', 'family_account', 'admission_number',
                                        'admission_date', 'house', 'student_key', 'tuition_fee',
                                        'discount', 'tag', 'birth_certificate_sighted',
                                        'transfer_certificate_provided', 'student_report_provided',
                                        'created_at']}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('subjects')

    @admin.display(description='Subjects')
    def subject_list(self, obj):
        return ', '.join(s.name for s in obj.subjects.all()) or '-'