# students/models.py
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.core.validators import RegexValidator


def generate_student_id():
    """Builds the next ID, e.g. STU-2026-001. Change the rule here only."""
    prefix = f'STU-{timezone.now().year}-'
    existing = Student.objects.filter(student_id__startswith=prefix).values_list('student_id', flat=True)
    numbers = [int(s[len(prefix):]) for s in existing if s[len(prefix):].isdigit()]
    return f'{prefix}{max(numbers, default=0) + 1:03d}'

class YearLevel(models.Model):
    class Stage(models.TextChoices):
        ELEMENTARY = 'ELEM', 'Elementary (Kindergarten to Grade 2)'
        LOWER = 'LOWER', 'Lower primary (Grades 3 to 5)'
        UPPER = 'UPPER', 'Upper primary (Grades 6 to 8)'

    code = models.CharField(max_length=4, unique=True)          # K, P, G1 ... G8
    name = models.CharField(max_length=30)
    order = models.PositiveSmallIntegerField(unique=True, help_text='Sorting position, lowest first.')
    stage = models.CharField(max_length=5, choices=Stage.choices)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


subject_code_validator = RegexValidator(r'^[A-Z0-9-]+$', 'Use capital letters, numbers and hyphens only.')


class Subject(models.Model):
    code = models.CharField('Subject code', max_length=12, unique=True, null=True, blank=True,
                            validators=[subject_code_validator],
                            help_text='Short unique code, e.g. ENG. Leave blank to generate one.')
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    year_levels = models.ManyToManyField(YearLevel, blank=True, related_name='subjects')
    is_core = models.BooleanField('National curriculum subject', default=True,
                                  help_text='Untick for school-specific electives such as Music or Drama.')
    is_active = models.BooleanField(default=True,
                                    help_text='Untick to retire a subject without losing its history.')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['name']

    def _generate_code(self):
        # first 4 letters/digits of the name, with a number added if that code is taken
        base = ''.join(ch for ch in self.name.upper() if ch.isalnum())[:4] or 'SUBJ'
        code, n = base, 2
        while Subject.objects.filter(code=code).exclude(pk=self.pk).exists():
            code = f'{base}{n}'
            n += 1
        return code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper() if self.code else self._generate_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SchoolClass(models.Model):
    """A teaching group made of one or more year levels, e.g. Class 678 = Grades 6, 7 and 8."""
    name = models.CharField(max_length=50, unique=True)
    year_levels = models.ManyToManyField(YearLevel, related_name='classes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'school classes'

    def __str__(self):
        return self.name
    
class Student(models.Model):

    GENDER_CHOICES = [('F', 'Female'), ('M', 'Male')]
    FEE_PAYER_CHOICES = [
        ('PARENT', 'Parent / Guardian'),
        ('COMPANY', 'Company'),
        ('GOVERNMENT', 'Government'),
    ]
    HEARD_ABOUT_CHOICES = [
        ('TV', 'TV'), ('RADIO', 'Radio'), ('NEWSPAPER', 'Newspaper'),
        ('STAFF', 'Direct approach by MIS staff'), ('FRIEND', 'A friend'),
        ('PARENT', 'Already a parent'), ('IEA', 'Another IEA school'), ('OTHER', 'Other'),
    ]
    # (stored value, label shown to users): Grade 1 to Grade 12
    GRADE_CHOICES = [(g, f'Grade {g}') for g in range(1, 13)]

    # unique=True: two students can never share an ID. We'll add the format rule later.
    student_id = models.CharField('ID number', max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    grade = models.PositiveSmallIntegerField(choices=GRADE_CHOICES, null=True, blank=True)   # legacy, to be removed
    year_level = models.ForeignKey(YearLevel, null=True, blank=True, on_delete=models.PROTECT, 
                                   related_name='students', verbose_name='Grade applied for')

    # subject line was deleted to be replaced later.
   


    created_at = models.DateTimeField(auto_now_add=True)

    photo = models.ImageField(upload_to='students/photos/', blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    nationality = models.CharField('Nationality / Ethnicity', max_length=100, blank=True)
    religion = models.CharField(max_length=100, blank=True)
    starting_date = models.DateField(null=True, blank=True)

    # ---- Contact and home
    postal_address = models.TextField(blank=True)
    residential_address = models.TextField(blank=True)
    lives_with = models.CharField('Child lives with', max_length=255, blank=True)
    transport_arrangements = models.CharField('Transport to / from school', max_length=255, blank=True)

    # ---- Who pays the school fee
    fee_payer = models.CharField(max_length=10, choices=FEE_PAYER_CHOICES, blank=True)
    fee_payer_name = models.CharField('Company name', max_length=150, blank=True)
    fee_payer_department = models.CharField('Government department', max_length=150, blank=True)

    # ---- Emergency contact
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True)

    # ---- Languages and health
    home_language = models.CharField('Language spoken at home', max_length=100, blank=True)
    other_languages = models.CharField('Other languages spoken', max_length=200, blank=True)
    disabilities = models.TextField(blank=True)
    special_needs = models.TextField(blank=True)
    medical_condition = models.TextField(blank=True)
    doctor_name = models.CharField("Student's doctor", max_length=150, blank=True)
    doctor_phone = models.CharField(max_length=30, blank=True)

    # ---- Declaration
    heard_about = models.CharField('Heard about the school through', max_length=10,
                                   choices=HEARD_ABOUT_CHOICES, blank=True)
    photo_consent = models.BooleanField("School may use the child's photo for marketing", default=False)
    declaration_accepted = models.BooleanField(default=False)   # the paper form was signed
    declaration_date = models.DateField(null=True, blank=True)

    # ---- OFFICE USE ONLY (edited in the admin, not on the registration form)
    admitted_grade = models.PositiveSmallIntegerField(choices=GRADE_CHOICES, null=True, blank=True)
    family_account = models.CharField(max_length=50, blank=True)
    admission_number = models.CharField(max_length=50, blank=True)
    admission_date = models.DateField(null=True, blank=True)
    house = models.CharField(max_length=50, blank=True)
    student_key = models.CharField(max_length=50, blank=True)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tag = models.CharField(max_length=50, blank=True)
    birth_certificate_sighted = models.BooleanField('Birth certificate / passport sighted', default=False)
    transfer_certificate_provided = models.BooleanField(default=False)
    student_report_provided = models.BooleanField(default=False)

    class Meta:
        ordering = ['year_level__order', 'last_name', 'first_name']

    @property
    def full_name(self):
        # lets templates write {{ student.full_name }}
        return f'{self.first_name} {self.last_name}'

    def save(self, *args, **kwargs):
        # only generate an ID for new students that don't have one yet
        if not self.student_id:
            self.student_id = generate_student_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.student_id} - {self.full_name}'

class Guardian(models.Model):
    RELATIONSHIP_CHOICES = [('FATHER', 'Father / Guardian'), ('MOTHER', 'Mother / Guardian')]
    ID_TYPE_CHOICES = [('NID', 'NID'), ('PASSPORT', 'Passport'), ('LICENCE', 'Driving licence')]

        # CASCADE: deleting a student deletes their guardian rows too
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='guardians')
    relationship = models.CharField(max_length=10, choices=RELATIONSHIP_CHOICES)
    name = models.CharField(max_length=150)
    phone = models.CharField('Business phone / mobile', max_length=30, blank=True)
    fax = models.CharField('Business fax', max_length=30, blank=True)
    email = models.EmailField(blank=True)
    employer = models.CharField(max_length=150, blank=True)
    occupation = models.CharField(max_length=150, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    id_type = models.CharField('Parent ID type', max_length=10, choices=ID_TYPE_CHOICES, blank=True)
    id_number = models.CharField('Parent ID number', max_length=50, blank=True)

    def __str__(self):
            return f'{self.name} ({self.get_relationship_display()})'

class PreviousSchool(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='previous_schools')
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    school = models.CharField(max_length=150)
    country = models.CharField(max_length=100, blank=True)
    province = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.school} ({self.year})'

class Sibling(models.Model):
    """Other children of the family attending this school or another."""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='siblings')
    name = models.CharField(max_length=150)
    grade = models.CharField(max_length=20, blank=True)
    school = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.name

