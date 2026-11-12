# schoolcalendar/models.py
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Term(models.Model):
    class BreakAfter(models.TextChoices):
        ONE_WEEK = 'ONE', '1 week term break'
        TWO_WEEKS = 'TWO', '2 weeks term break'
        CHRISTMAS = 'XMAS', 'Christmas holiday'

    year = models.PositiveSmallIntegerField()
    number = models.PositiveSmallIntegerField(choices=[(n, f'Term {n}') for n in range(1, 5)])
    start_date = models.DateField()
    end_date = models.DateField()
    break_after = models.CharField('Holiday after this term', max_length=4,
                                   choices=BreakAfter.choices, blank=True)
    staff_info = models.TextField('Information to staff', blank=True)
    confirmed = models.BooleanField(default=True, help_text='Untick while the dates are provisional.')

    class Meta:
        ordering = ['year', 'number']
        constraints = [
            models.UniqueConstraint(fields=['year', 'number'], name='unique_term_per_year'),
        ]

    @property
    def name(self):
        return f'Term {self.number}'

    @property
    def weeks(self):
        return round(((self.end_date - self.start_date).days + 1) / 7)

    @property
    def planned_break_weeks(self):
        # 1 or 2 for the term breaks; None for Christmas (that one is calculated)
        return {'ONE': 1, 'TWO': 2}.get(self.break_after)

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('The end date cannot be before the start date.')

    def __str__(self):
        return f'{self.name} {self.year}'

class CalendarEvent(models.Model):
    class Type(models.TextChoices):
        PUBLIC_HOLIDAY = 'PUBLIC_HOLIDAY', 'Public holiday (PNG)'
        IEA_SPECIAL = 'IEA_SPECIAL', 'IEA special day'
        SCHOOL_EVENT = 'SCHOOL_EVENT', 'School event'
        SCHEDULE = 'SCHEDULE', 'Class schedule'
        EXAM = 'EXAM', 'Exams / assessment'
        STAFF_DAY = 'STAFF_DAY', 'Staff day (no students)'

    title = models.CharField(max_length=150)
    event_type = models.CharField(max_length=20, choices=Type.choices, default=Type.SCHOOL_EVENT)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text='Leave empty for a one-day event.')
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    confirmed = models.BooleanField(default=True, help_text='Untick while the date is provisional.')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='calendar_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date', 'start_time', 'title']

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('The end date cannot be before the start date.')

    def save(self, *args, **kwargs):
        if self.end_date is None:
            self.end_date = self.start_date   # one-day event: makes date-range queries simple
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} ({self.start_date})'