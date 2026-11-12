# schoolcalendar/management/commands/seed_calendar.py
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from schoolcalendar.models import CalendarEvent, Term

# PLACEHOLDER term dates. Replace with the dates IEA Madang publishes (edit them in /admin/).
TERM_DATES = {
    2027: [
        (1, date(2027, 1, 25), date(2027, 4, 2)),
        (2, date(2027, 4, 19), date(2027, 6, 25)),
        (3, date(2027, 7, 12), date(2027, 9, 17)),
        (4, date(2027, 10, 4), date(2027, 12, 3)),
    ],
}


def easter_sunday(year):
    """Standard Gregorian Easter algorithm, so we never type Easter dates by hand."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def nth_weekday(year, month, weekday, n):
    """The n-th given weekday of a month (weekday 0 = Monday)."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def png_public_holidays(year):
    easter = easter_sunday(year)
    return [
        ("New Year's Day", date(year, 1, 1)),
        ('Good Friday', easter - timedelta(days=2)),
        ('Holy Saturday', easter - timedelta(days=1)),
        ('Easter Monday', easter + timedelta(days=1)),
        ("King's Birthday", nth_weekday(year, 6, 0, 2)),   # ESTIMATE: 2nd Monday of June
        ('Remembrance Day', date(year, 7, 23)),
        ('Independence Day', date(year, 9, 16)),
        ('Christmas Day', date(year, 12, 25)),
        ('Boxing Day', date(year, 12, 26)),
    ]


class Command(BaseCommand):
    help = 'Loads the starter school calendar (terms + PNG public holidays) for one year'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, default=2027)

    def handle(self, *args, **options):
        year = options['year']

        for number, start, end in TERM_DATES.get(year, []):
            _, created = Term.objects.get_or_create(
                year=year, number=number,
                defaults={'start_date': start, 'end_date': end, 'confirmed': False})
            self.stdout.write(f'Term {number}: {"created" if created else "already exists"}')
        if year not in TERM_DATES:
            self.stdout.write(self.style.WARNING(f'No term dates in the file for {year}: add them in /admin/.'))

        for title, day in png_public_holidays(year):
            # matching on title + type + year means re-running never duplicates or overwrites your edits
            _, created = CalendarEvent.objects.get_or_create(
                title=title, event_type=CalendarEvent.Type.PUBLIC_HOLIDAY, start_date__year=year,
                defaults={'start_date': day, 'end_date': day, 'confirmed': False})
            self.stdout.write(f'{title} ({day:%a %d %b}): {"created" if created else "already exists"}')

        self.stdout.write(self.style.SUCCESS('Done. Everything is marked "not confirmed" until you verify it.'))