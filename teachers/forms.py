from django import forms
from .models import Teacher
from students.models import SchoolClass

class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = [
            'first_name',
            'last_name',
            'other_names',
            'ethnicity_nationality',
            'teacher_file_number',
            'school_id_number',
            'school_class',
            'residential_address',
            'contact',
            'email',
        ]
        widgets = {
            'residential_address': forms.Textarea(attrs={'rows': 3}),
        }
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            #add the Bootstrap class to every input so we dont repeat it in the template
            for field in self.fields.values():
                field.widget.attrs['class'] = 'form-control'
            self.fields['school_class'].queryset = SchoolClass.objects.filter(is_active=True)
            self.fields['school_class'].empty_label = '--- Select a class ---'
            self.fields['school_class'].required = True
            self.fields['school_class'].widget.attrs['class'] = 'form-select'