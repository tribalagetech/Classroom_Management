# students/management/commands/link_classes.py
import re

from django.core.management.base import BaseCommand

from students.models import SchoolClass, Student, YearLevel
from teachers.models import Teacher

YEAR_LEVELS = [
    ('K', 'Kindergarten', 0, 'ELEM'), ('P', 'Prep', 1, 'ELEM'),
    ('G1', 'Grade 1', 2, 'ELEM'), ('G2', 'Grade 2', 3, 'ELEM'),
    ('G3', 'Grade 3', 4, 'LOWER'), ('G4', 'Grade 4', 5, 'LOWER'), ('G5', 'Grade 5', 6, 'LOWER'),
    ('G6', 'Grade 6', 7, 'UPPER'), ('G7', 'Grade 7', 8, 'UPPER'), ('G8', 'Grade 8', 9, 'UPPER'),
]


def grades_from_text(text):
    """'678' -> [6, 7, 8];  'Grade 6-8' -> [6, 7, 8];  'Class 3' -> [3];  anything else -> []"""
    text = text or ''
    m = re.search(r'([1-8])\s*(?:-|–|to)\s*([1-8])', text)
    if m and int(m.group(1)) <= int(m.group(2)):
        return list(range(int(m.group(1)), int(m.group(2)) + 1))
    digits = re.sub(r'\D', '', text)
    if digits and set(digits) <= set('12345678'):
        return sorted({int(d) for d in digits})
    return []


class Command(BaseCommand):
    help = 'Links existing students to year levels and existing teachers to classes. Safe to re-run.'

    def handle(self, *args, **options):
        levels = {}
        for code, name, order, stage in YEAR_LEVELS:
            levels[code], _ = YearLevel.objects.get_or_create(
                code=code, defaults={'name': name, 'order': order, 'stage': stage})

        # 1. students: old grade number -> year level
        linked = unmatched = 0
        for s in Student.objects.filter(year_level__isnull=True, grade__isnull=False):
            level = levels.get(f'G{s.grade}')
            if level:
                Student.objects.filter(pk=s.pk).update(year_level=level)
                linked += 1
            else:
                unmatched += 1
        self.stdout.write(f'Students linked to a year level: {linked}')
        if unmatched:
            self.stdout.write(self.style.WARNING(
                f'{unmatched} student(s) are in grades above 8, which this school does not teach. '
                f'Set their year level by hand in /admin/.'))

        # 2. teachers: old class text -> class
        for t in Teacher.objects.filter(school_class__isnull=True):
            grades = grades_from_text(t.class_assigned)
            if not grades:
                self.stdout.write(self.style.WARNING(
                    f'Teacher {t} has class text "{t.class_assigned}", which I could not read. Assign a class by hand.'))
                continue
            name = 'Class ' + ''.join(str(g) for g in grades)
            school_class, created = SchoolClass.objects.get_or_create(name=name)
            if created or not school_class.year_levels.exists():
                school_class.year_levels.set([levels[f'G{g}'] for g in grades])
            t.school_class = school_class
            t.save(update_fields=['school_class'])
            self.stdout.write(f'Teacher {t} -> {school_class.name}')

        self.stdout.write(self.style.SUCCESS('Done.'))