# students/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (GuardianForm, PreviousSchoolFormSet, SchoolClassForm,
                    SiblingFormSet, StudentForm, SubjectForm)
from .models import SchoolClass, Student, Subject, YearLevel

# only superusers may define subjects
superuser_required = user_passes_test(lambda u: u.is_superuser)

@login_required
@permission_required('students.change_schoolclass', raise_exception=True)
def class_manage(request, pk=None):
    instance = get_object_or_404(SchoolClass, pk=pk) if pk else None
    form = SchoolClassForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        saved = form.save()
        messages.success(request, f'{saved.name} {"updated" if instance else "added"}.')
        return redirect('students:classes')

    classes = (SchoolClass.objects.prefetch_related('year_levels')
               .annotate(teacher_count=Count('teachers', distinct=True),
                         student_count=Count('year_levels__students', distinct=True)))
    return render(request, 'students/classes.html',
                  {'form': form, 'classes': classes, 'editing': instance})


@login_required
@permission_required('students.delete_schoolclass', raise_exception=True)
@require_POST
def class_delete(request, pk):
    school_class = get_object_or_404(SchoolClass, pk=pk)
    if school_class.teachers.exists():
        messages.error(request, f'{school_class.name} still has teachers assigned. '
                                f'Reassign them first, or untick Active to retire the class.')
        return redirect('students:classes')
    name = school_class.name
    school_class.delete()
    messages.success(request, f'{name} deleted.')
    return redirect('students:classes')

@login_required
@superuser_required
def subject_manage(request):
    form = SubjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        subject = form.save(commit=False)
        subject.created_by = request.user
        subject.save()
        form.save_m2m()    # saves the ticked year levels
        messages.success(request, f'Subject "{subject.name}" ({subject.code}) added.')
        return redirect('students:subjects')

    subjects = (Subject.objects.prefetch_related('year_levels')
                .annotate(student_count=Count('year_levels__students', distinct=True),
                          resource_count=Count('resources', distinct=True)))
    level = request.GET.get('level', '')
    if level.isdigit():
        subjects = subjects.filter(year_levels__pk=int(level))
    return render(request, 'students/subjects.html', {
        'form': form, 'subjects': subjects, 'levels': YearLevel.objects.all(), 'level': level,
    })


@login_required
@superuser_required
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=subject)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Subject "{subject.name}" updated.')
        return redirect('students:subjects')
    return render(request, 'students/subject_edit.html', {'form': form, 'subject': subject})


@login_required
@superuser_required
@require_POST
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    students, files = subject.students.count(), subject.resources.count()
    if students or files:
        # deleting would erase history, so retire it instead
        messages.error(request, f'"{subject.name}" is used by {students} student(s) and {files} resource(s), '
                                f'so it cannot be deleted. Edit it and untick Active to retire it.')
        return redirect('students:subjects')
    files, tests = subject.resources.count(), subject.assessments.count()
    if files or tests:
        messages.error(request, f'"{subject.name}" has {files} resource(s) and {tests} assessment(s), '
                                f'so it cannot be deleted. Edit it and untick Active to retire it instead.')
        return redirect('students:subjects')


@login_required
@permission_required('students.add_student', raise_exception=True)
def student_register(request):
    data = request.POST or None     # None on a normal page load, so the forms start empty
    files = request.FILES or None   # the uploaded photo

    form = StudentForm(data, files)
    # prefix keeps the two guardian blocks apart (father-name, mother-name)
    # empty_permitted: a completely blank block is skipped instead of raising errors
    father_form = GuardianForm(data, prefix='father', empty_permitted=True, use_required_attribute=False)
    mother_form = GuardianForm(data, prefix='mother', empty_permitted=True, use_required_attribute=False)
    schools_fs = PreviousSchoolFormSet(data, prefix='schools')
    siblings_fs = SiblingFormSet(data, prefix='siblings')

    if request.method == 'POST':
        # a list (not "and") so every form is checked and ALL errors show at once
        checks = [form.is_valid(), father_form.is_valid(), mother_form.is_valid(),
                  schools_fs.is_valid(), siblings_fs.is_valid()]
        if all(checks):
            with transaction.atomic():   # all-or-nothing: no half-saved students
                student = form.save(commit=False)
                student.declaration_date = timezone.localdate()
                student.save()           # this generates the student ID
                form.save_m2m()          # saves the ticked subjects

                for gform, relationship in ((father_form, 'FATHER'), (mother_form, 'MOTHER')):
                    if gform.has_changed():   # skip a block left empty
                        guardian = gform.save(commit=False)
                        guardian.student = student
                        guardian.relationship = relationship
                        guardian.save()

                schools_fs.instance = student   # attach the rows to the new student
                schools_fs.save()
                siblings_fs.instance = student
                siblings_fs.save()

                messages.success(request, f'{student.full_name} registered with ID {student.student_id}.')
                return redirect('students:register')   # was: dashboard:teacher. Stay here, ready for the next student

    return render(request, 'students/register.html', {
        'form': form, 'father_form': father_form, 'mother_form': mother_form,
        'schools_fs': schools_fs, 'siblings_fs': siblings_fs,
    })