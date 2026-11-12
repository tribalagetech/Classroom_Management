# schoolcalendar/views.py
import calendar
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from dashboard.access import home_for
from .forms import EventForm, TermForm
from .models import CalendarEvent, Term


def year_summary(year):
    """Each term with its length, plus the holiday that follows it."""
    terms = list(Term.objects.filter(year=year))
    following = Term.objects.filter(year=year + 1, number=1).first()   # for the summer holiday
    rows = []
    for i, term in enumerate(terms):
        nxt = terms[i + 1] if i + 1 < len(terms) else following
        brk = None
        if nxt:
            b_start = term.end_date + timedelta(days=1)
            b_end = nxt.start_date - timedelta(days=1)
            brk = {'start': b_start, 'end': b_end, 'planned': False,
                   'weeks': round(((b_end - b_start).days + 1) / 7)}
        elif term.planned_break_weeks:
            # no next term yet: show the break that was chosen in the pop-up
            d = term.end_date + timedelta(weeks=term.planned_break_weeks)
            next_start = d + timedelta(days=(0 - d.weekday()) % 7)   # the Monday on or after d
            brk = {'start': term.end_date + timedelta(days=1), 'end': next_start - timedelta(days=1),
                   'planned': True, 'weeks': term.planned_break_weeks}
        elif term.break_after == Term.BreakAfter.CHRISTMAS and terms[0].number == 1:
            # estimate: next year's Term 1 starts on the same weekday, 364 days after this year's
            est = terms[0].start_date + timedelta(days=364)
            brk = {'start': term.end_date + timedelta(days=1), 'end': est - timedelta(days=1),
                   'planned': True, 'weeks': round(((est - term.end_date).days - 1) / 7)}
        rows.append({'term': term, 'brk': brk})
    return rows


@login_required   # everyone logged in can VIEW the calendar
def month_view(request, year=None, month=None):
    today = timezone.localdate()
    year = year or today.year
    month = month or today.month
    if not (1 <= month <= 12 and 2000 <= year <= 2100):
        raise Http404

    selected_date = None
    if request.GET.get('day'):
        try:
            selected_date = date.fromisoformat(request.GET['day'])
        except ValueError:
            pass

    can_edit = request.user.has_perm('schoolcalendar.change_calendarevent')

    first = date(year, month, 1)
    prev_month = first - timedelta(days=1)
    next_month = (first + timedelta(days=31)).replace(day=1)
    month_end = next_month - timedelta(days=1)

    grid = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    grid_start, grid_end = grid[0][0], grid[-1][-1]
    events = list(CalendarEvent.objects.filter(start_date__lte=grid_end, end_date__gte=grid_start))
    terms = list(Term.objects.filter(year__in={grid_start.year, grid_end.year}))
    has_terms = bool(terms)

    weeks = []
    day_data = {}    # what the day pop-up shows, keyed by YYYY-MM-DD
    for week in grid:
        row = []
        for d in week:
            day_events = [e for e in events if e.start_date <= d <= e.end_date]
            term = next((t for t in terms if t.start_date <= d <= t.end_date), None)
            weekend = d.weekday() >= 5
            status = None
            if has_terms and not weekend:
                status = 'term' if term else 'break'
            week_no = ((d - term.start_date).days // 7 + 1) if term else None
            row.append({
                'date': d,
                'in_month': d.month == month,
                'weekend': weekend,
                'today': d == today,
                'events': day_events,
                'public_holiday': any(e.event_type == CalendarEvent.Type.PUBLIC_HOLIDAY for e in day_events),
                'status': status,
                'term': term,
                'week_no': week_no,
                'term_week': week_no if (term and d.weekday() == 0) else None,
            })
            day_data[d.isoformat()] = {
                'label': f'{d:%A}, {d.day} {d:%B %Y}',      # avoids %-d, which fails on Windows
                'term': term.name if term else '',
                'week': week_no,
                'status': status or '',
                'weekend': weekend,
                'events': [{
                    'title': e.title,
                    'type': e.event_type,
                    'type_label': e.get_event_type_display(),
                    'time': (e.start_time.strftime('%H:%M') + (f' to {e.end_time:%H:%M}' if e.end_time else ''))
                            if e.start_time else '',
                    'description': e.description,
                    'confirmed': e.confirmed,
                    'edit_url': reverse('schoolcalendar:event_edit', args=[e.pk]) if can_edit else '',
                } for e in day_events],
            }
        weeks.append(row)

    selected_day = next((c for w in weeks for c in w if c['date'] == selected_date), None)

    can_manage_terms = (request.user.has_perm('schoolcalendar.add_term')
                        and request.user.has_perm('schoolcalendar.change_term'))
    terms_data = []
    if can_manage_terms:
        terms_data = [{'year': t.year, 'number': t.number,
                       'start': t.start_date.isoformat(), 'end': t.end_date.isoformat(),
                       'break_after': t.break_after, 'staff_info': t.staff_info,
                       'confirmed': t.confirmed}
                      for t in Term.objects.all()]

    context = {
        'weeks': weeks,
        'weekday_names': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'month_label': first.strftime('%B %Y'),
        'prev': prev_month,
        'next': next_month,
        'year_summary': year_summary(year),
        'year': year,
        'month': month,
        'today': today,
        'selected_day': selected_day,
        'month_events': [e for e in events if e.start_date <= month_end and e.end_date >= first],
        'can_edit': can_edit,
        'can_add_event': request.user.has_perm('schoolcalendar.add_calendarevent'),
        'event_types': CalendarEvent.Type.choices,
        'day_data': day_data,
        'can_manage_terms': can_manage_terms,
        'terms_data': terms_data,
        'home_url': reverse(home_for(request.user)),
    }
    template = 'schoolcalendar/month_admin.html' if request.user.is_staff else 'schoolcalendar/month_teacher.html'
    return render(request, template, context)


#what the pop-up’s add form calls:
@login_required
@require_POST
def event_quick_add(request):
    """Called by the day pop-up in the background. Always answers with JSON."""
    if not request.user.has_perm('schoolcalendar.add_calendarevent'):
        return JsonResponse({'ok': False, 'errors': {
            '__all__': ['You do not have permission to add events.']}}, status=403)
    form = EventForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': {k: list(v) for k, v in form.errors.items()}}, status=400)
    event = form.save(commit=False)
    event.created_by = request.user
    event.save()
    messages.success(request, f'"{event.title}" added to the calendar.')
    return JsonResponse({'ok': True})


@login_required
@require_POST
def term_save(request):
    """Called by the pop-up in the background. Always answers with JSON, never a redirect."""
    if not (request.user.has_perm('schoolcalendar.add_term')
            and request.user.has_perm('schoolcalendar.change_term')):
        return JsonResponse({'ok': False, 'errors': {
            '__all__': ['You do not have permission to change the school calendar.']}}, status=403)

    form = TermForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': {k: list(v) for k, v in form.errors.items()}}, status=400)

    d = form.cleaned_data
    # the year comes from the start date; saving an existing term number updates it
    term, created = Term.objects.update_or_create(
        year=d['start_date'].year, number=d['number'],
        defaults={'start_date': d['start_date'], 'end_date': d['end_date'],
                  'break_after': d['break_after'], 'staff_info': d['staff_info'],
                  'confirmed': d['confirmed']})
    messages.success(request, f'{term} {"added" if created else "updated"}: '
                              f'{term.start_date:%d-%m-%Y} to {term.end_date:%d-%m-%Y} ({term.weeks} weeks).')
    return JsonResponse({'ok': True})


def _back_to_month(event):
    return redirect('schoolcalendar:month_ym', year=event.start_date.year, month=event.start_date.month)


@login_required
@permission_required('schoolcalendar.add_calendarevent', raise_exception=True)
def event_create(request):
    initial = {}
    if request.GET.get('date'):
        initial['start_date'] = request.GET['date']
    form = EventForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False)
        event.created_by = request.user
        event.save()
        messages.success(request, f'"{event.title}" added to the calendar.')
        return _back_to_month(event)
    return render(request, 'schoolcalendar/event_form.html', {'form': form, 'heading': 'Add event'})


@login_required
@permission_required('schoolcalendar.change_calendarevent', raise_exception=True)
def event_edit(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    form = EventForm(request.POST or None, instance=event)
    if request.method == 'POST' and form.is_valid():
        event = form.save()
        messages.success(request, f'"{event.title}" updated.')
        return _back_to_month(event)
    return render(request, 'schoolcalendar/event_form.html',
                  {'form': form, 'heading': 'Edit event', 'event': event})


@login_required
@permission_required('schoolcalendar.delete_calendarevent', raise_exception=True)
@require_POST
def event_delete(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    title = event.title
    response = _back_to_month(event)
    event.delete()
    messages.success(request, f'"{title}" deleted.')
    return response