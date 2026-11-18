from django.db import models
# resources/models.py
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator

from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone

MAX_UPLOAD_MB = 25
ALLOWED_EXTENSIONS = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png']


def private_storage():
    # files live OUTSIDE the public media folder: they can only be reached through our download view
    return FileSystemStorage(location=settings.PRIVATE_MEDIA_ROOT)


def upload_path(instance, filename):
    # a random prefix stops two files with the same name overwriting each other
    return f'resources/{timezone.now():%Y/%m}/{uuid.uuid4().hex[:10]}_{os.path.basename(filename)}'


def validate_file_size(f):
    if f.size > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValidationError(f'File too large. The limit is {MAX_UPLOAD_MB} MB.')


class Resource(models.Model):
    class Type(models.TextChoices):
        LESSON_PLAN = 'LESSON_PLAN', 'Lesson plan'
        WORKSHEET = 'WORKSHEET', 'Worksheet'
        NOTES = 'NOTES', 'Notes / handout'
        PRESENTATION = 'PRESENTATION', 'Presentation'
        ASSESSMENT = 'ASSESSMENT', 'Assessment / test'
        REFERENCE = 'REFERENCE', 'Reference material'
        OTHER = 'OTHER', 'Other'

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=20, choices=Type.choices, default=Type.NOTES)

    # PROTECT: a subject that has resources can never be deleted by accident
    subject = models.ForeignKey('students.Subject', on_delete=models.PROTECT, related_name='resources')
    year_levels = models.ManyToManyField('students.YearLevel', related_name='resources')

    file = models.FileField(upload_to=upload_path, storage=private_storage,
                            validators=[FileExtensionValidator(ALLOWED_EXTENSIONS), validate_file_size])
    original_name = models.CharField(max_length=255, blank=True, editable=False)
    file_size = models.PositiveIntegerField(default=0, editable=False)

    is_published = models.BooleanField(default=False,
                                       help_text='Published resources are visible to other users, and later to students.')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL,
                                    related_name='uploaded_resources')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    download_count = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ['-uploaded_at']

    def save(self, *args, **kwargs):
        if self.file and not self.original_name:
            self.original_name = os.path.basename(self.file.name)   # the name the teacher uploaded
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def size_display(self):
        if self.file_size < 1024 * 1024:
            return f'{max(1, self.file_size // 1024)} KB'
        return f'{self.file_size / 1048576:.1f} MB'

    def __str__(self):
        return self.title


@receiver(post_delete, sender=Resource)
def delete_file_with_record(sender, instance, **kwargs):
    # remove the file from disk when its record is deleted, so no orphan files pile up
    if instance.file:
        instance.file.delete(save=False)