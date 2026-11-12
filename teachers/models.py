from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings

# Create your models here.

#only digits, optional leading +, 8 - 11 characters
phone_validation = RegexValidator(
    regex=r'^\+?\d{8,11}$',
    message="Phone number must be entered in the format: '+999999999'. Up to 11 digits allowed."
)

class Teacher(models.Model):
    #1-3 Names (other names is optional):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    other_names = models.CharField(max_length=30, blank=True, null=True) #blank =True means can be filled but not required, null=True means can be empty in the database

    #Ethnicity / Nationality
    ethnicity_nationality = models.CharField('Ethnicity / Nationality', max_length=50, blank=True, null=True)

    #IDENTIFICATION
    teacher_file_number = models.CharField(max_length=50, unique=True)
    school_id_number = models.CharField(max_length=50, unique=True)

    #class assignment
    class_assigned = models.CharField(max_length=50, blank=True, null=True)

    #contact information
    residential_address = models.TextField()
    contact = models.CharField(max_length=25, validators=[phone_validation], blank=True, null=True)
    email = models.EmailField(max_length=254, unique=True)

    #Link to the login account. Empty until credentials are created
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,related_name='teacher_profile')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']  # Order by last name, then first name

        def __str__(self):
            return f"{self.first_name} {self.last_name} ({self.teacher_file_number})"
        