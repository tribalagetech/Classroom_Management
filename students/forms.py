# students/forms.py
from django import forms
from django.forms import inlineformset_factory

from .models import Guardian, PreviousSchool, Sibling, Student, Subject


class StyledModelForm(forms.ModelForm):
    """Gives every input the right Bootstrap class, so we never repeat it."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                continue                                    # subjects: styled in the template
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check-input'
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            else:
                widget.attrs['class'] = 'form-control'


class SubjectForm(StyledModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if Subject.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError('This subject already exists.')
        return name


class StudentForm(StyledModelForm):
    # Must be filled in for NEW registrations. Old dummy rows can stay blank in the database.
    REQUIRED = ['date_of_birth', 'gender', 'nationality', 'residential_address',
                'starting_date', 'emergency_contact_name', 'emergency_contact_phone']

    class Meta:
        model = Student
        # student_id is left out on purpose: it is generated automatically
        fields = [
            'photo', 'first_name', 'last_name', 'date_of_birth', 'gender', 'nationality',
            'religion', 'grade', 'starting_date',
            'postal_address', 'residential_address', 'lives_with', 'transport_arrangements',
            'fee_payer', 'fee_payer_name', 'fee_payer_department',
            'emergency_contact_name', 'emergency_contact_phone',
            'home_language', 'other_languages', 'disabilities', 'special_needs',
            'medical_condition', 'doctor_name', 'doctor_phone',
            'subjects', 'heard_about', 'photo_consent', 'declaration_accepted',
        ]
        labels = {'last_name': 'Family name', 'first_name': 'Given names', 'grade': 'Grade applied for'}
        widgets = {
            # type="date" gives a calendar picker instead of typing D D M M Y Y
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'starting_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'postal_address': forms.Textarea(attrs={'rows': 2}),
            'residential_address': forms.Textarea(attrs={'rows': 2}),
            'disabilities': forms.Textarea(attrs={'rows': 2}),
            'special_needs': forms.Textarea(attrs={'rows': 2}),
            'medical_condition': forms.Textarea(attrs={'rows': 2}),
            'subjects': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.REQUIRED:
            self.fields[name].required = True
        # a checkbox must be ticked before the form will save
        self.fields['declaration_accepted'].required = True
        self.fields['declaration_accepted'].label = 'The parent / guardian has signed the declarations on the paper form'


class GuardianForm(StyledModelForm):
    class Meta:
        model = Guardian
        fields = ['name', 'phone', 'fax', 'email', 'employer', 'occupation',
                  'nationality', 'id_type', 'id_number']


class PreviousSchoolForm(StyledModelForm):
    class Meta:
        model = PreviousSchool
        fields = ['year', 'grade', 'school', 'country', 'province']


class SiblingForm(StyledModelForm):
    class Meta:
        model = Sibling
        fields = ['name', 'grade', 'school']


# a formset = several copies of one small form on the same page (3 blank rows each)
PreviousSchoolFormSet = inlineformset_factory(
    Student, PreviousSchool, form=PreviousSchoolForm, extra=3, can_delete=False)
SiblingFormSet = inlineformset_factory(
    Student, Sibling, form=SiblingForm, extra=3, can_delete=False)