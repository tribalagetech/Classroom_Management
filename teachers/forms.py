from django import forms
from .models import Teacher

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
            'class_assigned',
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