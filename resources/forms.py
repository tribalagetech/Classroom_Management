# resources/forms.py
from django import forms
from students.models import Subject, YearLevel
from .models import ALLOWED_EXTENSIONS, Resource


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'resource_type', 'subject', 'year_levels', 'file', 'description', 'is_published']
        labels = {'year_levels': 'Year levels', 'is_published': 'Publish now (visible to other users, later to students)'}
        widgets = {'description': forms.Textarea(attrs={'rows': 2}),
                   'year_levels': forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subject'].queryset = Subject.objects.filter(is_active=True)
        self.fields['subject'].empty_label = 'Select a subject...'
        self.fields['year_levels'].queryset = YearLevel.objects.all()
        self.fields['file'].widget.attrs['accept'] = ','.join(f'.{e}' for e in ALLOWED_EXTENSIONS)
        for name, field in self.fields.items():
            w = field.widget
            if isinstance(w, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                w.attrs['class'] = 'form-check-input'
            elif isinstance(w, forms.Select):
                w.attrs['class'] = 'form-select'
            else:
                w.attrs['class'] = 'form-control'

    def clean(self):
        data = super().clean()
        subject, levels = data.get('subject'), data.get('year_levels')
        if subject and levels:
            allowed = set(subject.year_levels.values_list('pk', flat=True))
            if allowed:   # a subject with no year levels set yet allows any
                bad = [l.name for l in levels if l.pk not in allowed]
                if bad:
                    self.add_error('year_levels', f'{subject.name} is not taught in: {", ".join(bad)}.')
        return data