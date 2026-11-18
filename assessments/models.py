# assessments/models.py
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Assessment(models.Model):
    """One test / assignment / exam for one subject in one grade in one term."""

    class Kind(models.TextChoices):
        TEST = 'TEST', 'Test'
        ASSIGNMENT = 'ASSIGNMENT', 'Assignment'
        PROJECT = 'PROJECT', 'Project'
        PRACTICAL = 'PRACTICAL', 'Practical'
        EXAM = 'EXAM', 'Exam'
        OTHER = 'OTHER', 'Other'

    title = models.CharField(max_length=150)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.TEST)
    # PROTECT: a subject or grade with assessments can never be deleted by accident
    subject = models.ForeignKey('students.Subject', on_delete=models.PROTECT, related_name='assessments')
    year_level = models.ForeignKey('students.YearLevel', on_delete=models.PROTECT, related_name='assessments')
    year = models.PositiveSmallIntegerField(help_text='School year, e.g. 2027')
    term = models.PositiveSmallIntegerField(choices=[(n, f'Term {n}') for n in range(1, 5)])
    max_points = models.DecimalField(max_digits=6, decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.01'))])
    date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['year', 'term', 'subject__code', 'date', 'title']

    def clean(self):
        # the subject must be taught in this grade (when the subject has grades set)
        if self.subject_id and self.year_level_id:
            levels = self.subject.year_levels
            if levels.exists() and not levels.filter(pk=self.year_level_id).exists():
                raise ValidationError(f'{self.subject.name} is not taught in {self.year_level.name}. '
                                      f'Link it to that grade on the Subjects page first.')

    def __str__(self):
        return f'{self.subject.code} {self.year_level.code} T{self.term} {self.year}: {self.title}'


class AssessmentScore(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='scores')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='scores')
    points = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='+')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # one score per student per assessment
            models.UniqueConstraint(fields=['assessment', 'student'], name='one_score_per_student'),
        ]

    def clean(self):
        if self.assessment_id and self.points is not None and self.points > self.assessment.max_points:
            raise ValidationError({'points': f'Cannot be more than {self.assessment.max_points}.'})
        if self.assessment_id and self.student_id and self.student.year_level_id != self.assessment.year_level_id:
            raise ValidationError("This student is not in the assessment's grade.")

    def __str__(self):
        return f'{self.student_id}: {self.points}/{self.assessment.max_points}'