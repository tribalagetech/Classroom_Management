# assessments/management/commands/seed_assessments.py
import random
from decimal import Decimal

from django.core.management.base import BaseCommand

from assessments.models import Assessment, AssessmentScore
from assessments.utils import current_term
from students.models import Student, YearLevel

# every subject gets these three assessments per term
KINDS = [('Test 1', 'TEST', 20), ('Assignment', 'ASSIGNMENT', 30), ('Exam', 'EXAM', 50)]


class Command(BaseCommand):
    help = 'Creates dummy assessments and scores so the dashboard has numbers. Safe to re-run.'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, help='School year (default: the current school year)')

    def handle(self, *args, **options):
        now_year, now_term = current_term()
        year = options['year'] or now_year
        rng = random.Random(42)
        made = scored = 0

        for level in YearLevel.objects.all():
            students = list(Student.objects.filter(year_level=level))
            for subject in level.subjects.filter(is_active=True):
                for term in (1, 2, 3, 4):
                    for i, (title, kind, max_points) in enumerate(KINDS):
                        assessment, new = Assessment.objects.get_or_create(
                            subject=subject, year_level=level, year=year, term=term, title=title,
                            defaults={'kind': kind, 'max_points': max_points})
                        made += new

                        # past terms are fully marked, the current term has its first two marked, future terms none
                        if year < now_year or (year == now_year and (term < now_term or (term == now_term and i < 2))):
                            for s in students:
                                points = Decimal(str(round(rng.uniform(0.4, 0.95) * max_points, 1)))
                                _, created = AssessmentScore.objects.get_or_create(
                                    assessment=assessment, student=s, defaults={'points': points})
                                scored += created

        self.stdout.write(self.style.SUCCESS(
            f'{made} assessments created, {scored} scores created for {year}. '
            f'(Current term: {now_term} {now_year}.)'))