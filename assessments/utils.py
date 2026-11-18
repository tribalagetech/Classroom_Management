# assessments/utils.py
from django.utils import timezone

from schoolcalendar.models import Term


def current_term(today=None):
    """(year, term number) the school is in today. During a holiday: the term that just finished."""
    today = today or timezone.localdate()
    term = Term.objects.filter(start_date__lte=today, end_date__gte=today).first()
    if term:
        return term.year, term.number
    last = Term.objects.filter(end_date__lt=today).order_by('-end_date').first()
    if last:
        return last.year, last.number
    upcoming = Term.objects.filter(start_date__gt=today).order_by('start_date').first()
    if upcoming:
        return upcoming.year, upcoming.number
    return today.year, 1