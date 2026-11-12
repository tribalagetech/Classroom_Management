# schoolcalendar/forms.py
from django import forms
from .models import CalendarEvent, Term


class EventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ['title', 'event_type', 'start_date', 'end_date',
                  'start_time', 'end_time', 'description', 'confirmed']
        labels = {'end_date': 'End date (leave empty for one day)',
                  'confirmed': 'This date is confirmed'}
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'start_time': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'end_time': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs['class'] = 'form-check-input'
            elif isinstance(w, forms.Select):
                w.attrs['class'] = 'form-select'
            else:
                w.attrs['class'] = 'form-control'

    def clean(self):
        data = super().clean()
        start, end = data.get('start_date'), data.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'The end date cannot be before the start date.')
        return data


class TermForm(forms.Form):
    """Validates what the pop-up sends. A plain Form, because the year comes from the start date."""
    number = forms.TypedChoiceField(choices=[(n, f'Term {n}') for n in range(1, 5)], coerce=int)
    weeks = forms.IntegerField(min_value=1, max_value=20)
    start_date = forms.DateField()
    end_date = forms.DateField()
    break_after = forms.ChoiceField(choices=[('', '')] + Term.BreakAfter.choices, required=False)
    staff_info = forms.CharField(required=False, max_length=2000)
    confirmed = forms.BooleanField(required=False)

    def clean(self):
        data = super().clean()
        start, end = data.get('start_date'), data.get('end_date')
        weeks, number = data.get('weeks'), data.get('number')
        if not (start and end and number):
            return data   # a field error already explains the problem

        if end < start:
            self.add_error('end_date', 'The end date cannot be before the start date.')
            return data
        if end.year != start.year:
            self.add_error('end_date', 'A term must start and end in the same calendar year.')
            return data

        spans = round(((end - start).days + 1) / 7)
        if weeks and weeks != spans:
            self.add_error('weeks', f'These dates span about {spans} weeks, not {weeks}.')

        # terms must not overlap and must stay in order (Term 2 after Term 1, and so on)
        earlier = Term.objects.filter(year=start.year, number__lt=number, end_date__gte=start).first()
        if earlier:
            self.add_error('start_date',
                           f'{earlier.name} ends on {earlier.end_date:%d-%m-%Y}. This term must start after it.')
        later = Term.objects.filter(year=start.year, number__gt=number, start_date__lte=end).first()
        if later:
            self.add_error('end_date',
                           f'{later.name} starts on {later.start_date:%d-%m-%Y}. This term must finish before it.')
        return data