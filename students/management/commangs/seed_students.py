# students/management/commands/seed_students.py
import random
from django.core.management.base import BaseCommand
from students.models import Student, Subject

CORE = ['Mathematics', 'English', 'Science', 'Social Science']
ELECTIVES = ['Art', 'Music', 'Drama']   # examples of "special" subjects

# (first name, last name, grade)
STUDENTS = [
    ('Joshua', 'Kila', 7), ('Grace', 'Waim', 7), ('Peter', 'Tau', 7),
    ('Mary', 'Kopi', 8), ('Samuel', 'Vagi', 8), ('Naomi', 'Gaudi', 8),
    ('David', 'Aua', 9), ('Ruth', 'Baki', 9), ('Michael', 'Hera', 9),
    ('Esther', 'Dai', 10), ('Joseph', 'Rova', 10), ('Rebecca', 'Karo', 10),
]


class Command(BaseCommand):
    help = 'Creates dummy subjects and students for testing'

    def handle(self, *args, **options):
        rng = random.Random(42)   # fixed seed = same dummy data every run

        # get_or_create = safe to run twice, no duplicates
        subjects = {n: Subject.objects.get_or_create(name=n)[0] for n in CORE + ELECTIVES}

        for i, (first, last, grade) in enumerate(STUDENTS, start=1):
            student, created = Student.objects.get_or_create(
                student_id=f'STU-2026-{i:03d}',   # placeholder format, e.g. STU-2026-001
                defaults={'first_name': first, 'last_name': last, 'grade': grade},
            )
            if created:
                # everyone takes the core subjects, plus 1-2 random electives
                chosen = CORE + rng.sample(ELECTIVES, k=rng.choice([1, 2]))
                student.subjects.set([subjects[n] for n in chosen])
                self.stdout.write(self.style.SUCCESS(f'Created {student}'))
            else:
                self.stdout.write(f'{student.student_id} already exists, skipped')