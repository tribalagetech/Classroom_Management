# students/forms.py
from django import forms
from django.forms import inlineformset_factory

from .models import Guardian, PreviousSchool, SchoolClass, Sibling, Student, Subject


# ---------------------------------------------------------------
# Base class FIRST: every form below inherits from it, so it must be defined above them
# ---------------------------------------------------------------
class StyledModelForm(forms.ModelForm):
    """Gives every input the right Bootstrap class, so we never repeat it."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxSelectMultiple):
                continue                                    # styled in the templates
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs['class'] = 'form-check-input'
            elif isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            else:
                widget.attrs['class'] = 'form-control'


class SubjectForm(StyledModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'description', 'year_levels', 'is_core', 'is_active']
        widgets = {'year_levels': forms.CheckboxSelectMultiple}
        labels = {'year_levels': 'Taught in these year levels'}

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if Subject.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This subject already exists.')
        return name


class SchoolClassForm(StyledModelForm):
    class Meta:
        model = SchoolClass
        fields = ['name', 'year_levels', 'is_active']
        widgets = {'year_levels': forms.CheckboxSelectMultiple}

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if SchoolClass.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('A class with this name already exists.')
        return name


class StudentForm(StyledModelForm):
    # must be filled in for NEW registrations; old dummy rows can stay blank in the database
    REQUIRED = ['date_of_birth', 'gender', 'nationality', 'residential_address',
                'starting_date', 'emergency_contact_name', 'emergency_contact_phone']

    class Meta:
        model = Student
        # student_id is left out on purpose: it is generated automatically
        fields = [
            'photo', 'first_name', 'last_name', 'date_of_birth', 'gender', 'nationality',
            'religion', 'year_level', 'starting_date',
            'postal_address', 'residential_address', 'lives_with', 'transport_arrangements',
            'fee_payer', 'fee_payer_name', 'fee_payer_department',
            'emergency_contact_name', 'emergency_contact_phone',
            'home_language', 'other_languages', 'disabilities', 'special_needs',
            'medical_condition', 'doctor_name', 'doctor_phone',
            'heard_about', 'photo_consent', 'declaration_accepted',
        ]
        labels = {'last_name': 'Family name', 'first_name': 'Given names', 'year_level': 'Grade applied for'}
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'starting_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'postal_address': forms.Textarea(attrs={'rows': 2}),
            'residential_address': forms.Textarea(attrs={'rows': 2}),
            'disabilities': forms.Textarea(attrs={'rows': 2}),
            'special_needs': forms.Textarea(attrs={'rows': 2}),
            'medical_condition': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in self.REQUIRED:
            self.fields[name].required = True
        self.fields['year_level'].required = True
        self.fields['year_level'].empty_label = 'Select a grade...'
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