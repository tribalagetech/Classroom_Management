from django.http import request
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from students.models import Student
from .access import staff_required
# Create your views here.

@login_required
def teacher_dashboard(request):

    if request.user.is_staff:
        return redirect('dashboard:admin_home')   # admins use their own dashboard  

    students = Student.objects.prefetch_related('subjects').all() # prefetch_related loads every student's subjects in ONE extra query
    # (without it, the table would run one query per student)
    
    return render(request, 'dashboard/teacher.html', {'students': students})

@staff_required
def admin_home(request):
    return render(request, 'dashboard/admin_home.html')


# placeholder pages: same template, different title
@staff_required
def resources(request):
    return render(request, 'dashboard/admin_placeholder.html', {'page_title': 'Resources Management'})

@staff_required
def schedules(request):
    return render(request, 'dashboard/admin_placeholder.html', {'page_title': 'Schedules'})

@staff_required
def inventory(request):
    return render(request, 'dashboard/admin_placeholder.html', {'page_title': 'Inventory Management'})
