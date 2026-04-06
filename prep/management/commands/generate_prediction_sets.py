from django.core.management.base import BaseCommand

from prep.models import Exam
from prep.services.prediction import generate_prediction_set
from prep.services.taxonomy import ensure_default_taxonomy


class Command(BaseCommand):
    help = "Generate likely-question practice sets for all active exams."

    def handle(self, *args, **options):
        ensure_default_taxonomy()
        created = 0
        for exam in Exam.objects.filter(is_active=True):
            generate_prediction_set(exam)
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Generated {created} prediction sets."))
