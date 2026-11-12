# students/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test

from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import SubjectForm
from .models import Subject
from django.db import transaction
from django.utils import timezone
from .forms import (GuardianForm, PreviousSchoolFormSet, SiblingFormSet,
                    StudentForm, SubjectForm)
from .models import Student, Subject

# only superusers may define subjects
superuser_required = user_passes_test(lambda u: u.is_superuser)


@login_required
@superuser_required
def subject_manage(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()   # INSERT into the database
            messages.success(request, f'Subject "{subject.name}" added.')
            return redirect('students:subjects')
    else:
        form = SubjectForm()

    # annotate adds a student_count to each subject (one query, not one per subject)
    subjects = Subject.objects.annotate(student_count=Count('students'))
    return render(request, 'students/subjects.html', {'form': form, 'subjects': subjects})


@login_required
@superuser_required
@require_POST   # deleting changes data, so POST only
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    name = subject.name
    subject.delete()   # students are NOT deleted, they just lose this subject
    messages.success(request, f'Subject "{name}" deleted.')
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