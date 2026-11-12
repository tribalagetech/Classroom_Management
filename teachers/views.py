# teachers/views.py
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST

from .forms import TeacherForm
from .models import Teacher

# only staff (admins) may manage teachers
staff_required = user_passes_test(lambda u: u.is_staff)


@login_required
@staff_required
def register_teacher(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST)   # fill the form with submitted data
        if form.is_valid():                # runs all validation
            teacher = form.save()          # INSERTs the row into the database
            messages.success(request, f'{teacher.first_name} {teacher.last_name} registered.')
            return redirect('teachers:list')
    else:
        form = TeacherForm()               # GET request: show an empty form
    return render(request, 'teachers/register.html', {'form': form})


@login_required
@staff_required
def teacher_list(request):
    teachers = Teacher.objects.select_related('user')  # fetch linked users in one query
    return render(request, 'teachers/list.html', {'teachers': teachers})


@login_required
@staff_required
@require_POST   # creating an account changes data, so POST only
def create_credentials(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)   # 404 if the id doesn't exist
    User = get_user_model()

    if teacher.user:
        messages.info(request, 'This teacher already has a login.')
        return redirect('teachers:list')

    username = teacher.teacher_file_number        # file number doubles as the username
    if User.objects.filter(username=username).exists():
        messages.error(request, f'Username {username} is already taken.')
        return redirect('teachers:list')

    temp_password = get_random_string(10)         # random one-time password
    user = User.objects.create_user(              # create_user hashes the password
        username=username,
        password=temp_password,
        email=teacher.email,
        first_name=teacher.first_name,
        last_name=teacher.last_name,
    )
    teacher.user = user                           # link login to the teacher record
    teacher.save()

    # shown once on screen so you can hand it to the teacher
    messages.success(request, f'Login created. Username: {username} | Temporary password: {temp_password}')
    return redirect('teachers:list')