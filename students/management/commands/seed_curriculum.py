# students/management/commands/seed_curriculum.py
from django.core.management.base import BaseCommand
from students.models import Subject, YearLevel

# (code, name, sort order, stage)
YEAR_LEVELS = [
    ('K', 'Kindergarten', 0, 'ELEM'), ('P', 'Prep', 1, 'ELEM'),
    ('G1', 'Grade 1', 2, 'ELEM'), ('G2', 'Grade 2', 3, 'ELEM'),
    ('G3', 'Grade 3', 4, 'LOWER'), ('G4', 'Grade 4', 5, 'LOWER'), ('G5', 'Grade 5', 6, 'LOWER'),
    ('G6', 'Grade 6', 7, 'UPPER'), ('G7', 'Grade 7', 8, 'UPPER'), ('G8', 'Grade 8', 9, 'UPPER'),
]

ALL = ['K', 'P', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8']
ELEM = ['P', 'G1', 'G2']
LOWER = ['G3', 'G4', 'G5']
UPPER = ['G6', 'G7', 'G8']

# (code, name, year levels, national curriculum?, description)
# Based on the PNG Department of Education syllabus lists. Adjust to what IEA Madang teaches.
SUBJECTS = [
    ('ENG', 'English', ALL, True, ''),
    ('MATH', 'Mathematics', ALL, True, ''),
    ('LANG', 'Language', ELEM, True, 'Elementary language (community language / Tok Pisin)'),
    ('CC', 'Culture and Community', ELEM, True, 'Elementary community-based subject'),
    ('CCVE', 'Citizenship and Christian Values Education', ELEM + LOWER + UPPER, True, ''),
    ('SCI', 'Science', LOWER + UPPER, True, ''),
    ('SS', 'Social Science', LOWER + UPPER, True, ''),
    ('ARTS', 'Arts', LOWER + UPPER, True, ''),
    ('HLTH', 'Health', LOWER, True, ''),
    ('PE', 'Physical Education', LOWER, True, ''),
    ('HPE', 'Health and Physical Education', UPPER, True, 'Combined in Grades 6 to 8'),
    ('MAL', 'Making a Living', UPPER, True, ''),
    # my assumption, not the current syllabus: listed in an older teacher guide
    ('ENVS', 'Environmental Studies', ['K', 'P', 'G1', 'G2'], False, 'School-added: early years'),
    # school-specific electives: no year levels yet, assign them on the Subjects page
    ('MUS', 'Music', [], False, 'School elective'),
    ('DRA', 'Drama', [], False, 'School elective'),
]

RENAMES = {'Art': 'Arts'}   # the old dummy-data name becomes the PNG syllabus name


class Command(BaseCommand):
    help = 'Loads year levels and the starter PNG subject list. Safe to run again.'

    def handle(self, *args, **options):
        levels = {}
        for code, name, order, stage in YEAR_LEVELS:
            levels[code], _ = YearLevel.objects.get_or_create(
                code=code, defaults={'name': name, 'order': order, 'stage': stage})

        for old, new in RENAMES.items():
            if Subject.objects.filter(name=old).exists() and not Subject.objects.filter(name=new).exists():
                Subject.objects.filter(name=old).update(name=new)

        for code, name, level_codes, core, description in SUBJECTS:
            subject = Subject.objects.filter(name__iexact=name).first()
            created = subject is None
            if created:
                subject = Subject(name=name, description=description, is_core=core)
            if not subject.code and not Subject.objects.filter(code=code).exclude(pk=subject.pk).exists():
                subject.code = code
            subject.save()
            # only fill the year levels if none are set, so your own edits are never overwritten
            if not subject.year_levels.exists() and level_codes:
                subject.year_levels.set([levels[c] for c in level_codes])
            self.stdout.write(f'{"Created" if created else "Updated"} {subject.code} {subject.name}')

        # subjects you added by hand earlier get a code too
        for subject in Subject.objects.filter(code__isnull=True):
            subject.save()

        self.stdout.write(self.style.SUCCESS('Curriculum loaded.'))