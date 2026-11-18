from django.http import request
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from students.models import Student
from .access import staff_required
from collections import defaultdict
from decimal import Decimal

from django.db.models import F, Sum

from assessments.models import Assessment, AssessmentScore
from assessments.utils import current_term
from schoolcalendar.models import Term
from students.models import Student, Subject
# Create your views here.

@login_required
def teacher_dashboard(request):
    if request.user.is_staff:
        return redirect('dashboard:admin_home')       # admins use their own dashboard

    teacher = getattr(request.user, 'teacher_profile', None)
    school_class = teacher.school_class if teacher else None
    levels = list(school_class.year_levels.all()) if school_class else []
    level_ids = [l.pk for l in levels]

    # which term to show: ?year=2026&term=3, otherwise the term the school is in today
    now_year, now_term = current_term()
    try:
        year = int(request.GET.get('year', now_year))
        term = int(request.GET.get('term', now_term))
    except ValueError:
        year, term = now_year, now_term
    if not 2000 <= year <= 2100:
        year = now_year
    if term not in (1, 2, 3, 4):
        term = now_term

    # only students in the grades of THIS teacher's class
    students = []
    if levels:
        students = list(Student.objects.filter(year_level__in=levels).select_related('year_level'))
    student_ids = [s.pk for s in students]

    # subjects per grade (the grade is what links a subject to its students)
    through = Subject.year_levels.through
    by_level = defaultdict(list)
    links = (through.objects.filter(yearlevel_id__in=level_ids, subject__is_active=True)
             .select_related('subject').order_by('subject__code'))
    for link in links:
        by_level[link.yearlevel_id].append(link.subject)

    # TOTAL assessment points: per grade and subject, for this term
    totals = {
        (r['year_level'], r['subject']): r['total']
        for r in Assessment.objects.filter(year=year, term=term, year_level__in=level_ids)
        .values('year_level', 'subject').annotate(total=Sum('max_points'))
    }
    # CURRENT points: per student and subject, for this term
    earned = {
        (r['student'], r['assessment__subject']): r['pts']
        for r in AssessmentScore.objects
        .filter(assessment__year=year, assessment__term=term, student_id__in=student_ids,
                assessment__year_level=F('student__year_level'))
        .values('student', 'assessment__subject').annotate(pts=Sum('points'))
    }

    for s in students:
        cells = []
        for subject in by_level.get(s.year_level_id, []):
            total = totals.get((s.year_level_id, subject.pk), Decimal('0'))
            points = earned.get((s.pk, subject.pk), Decimal('0'))
            cells.append({'code': subject.code, 'name': subject.name, 'points': points,
                          'total': total, 'css': '' if total else 'pts-empty'})
        s.subject_cells = cells

    # the Term 1 to 4 buttons
    term_rows = {t.number: t for t in Term.objects.filter(year=year)}
    term_links = []
    for n in (1, 2, 3, 4):
        t = term_rows.get(n)
        term_links.append({
            'label': f'Term {n}',
            'url': f'?year={year}&term={n}',
            'css': 'active' if n == term else '',
            'mark': ' •' if (year, n) == (now_year, now_term) else '',
            'dates': f'{t.start_date:%d %b} to {t.end_date:%d %b}' if t else 'Dates not set',
        })

    return render(request, 'dashboard/teacher.html', {
        'teacher': teacher,
        'school_class': school_class,
        'class_levels': levels,
        'level_names': ', '.join(l.name for l in levels),
        'students': students,
        'year': year,
        'term': term,
        'term_links': term_links,
        'prev_year_url': f'?year={year - 1}&term={term}',
        'next_year_url': f'?year={year + 1}&term={term}',
    })
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
