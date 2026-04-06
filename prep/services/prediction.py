from collections import Counter, defaultdict

from django.conf import settings
from django.utils import timezone

from prep.models import PredictionSet, PredictionSetQuestion, Question, QuestionSourceType
from prep.services.bootstrap import ensure_generated_questions


def generate_prediction_set(exam, section=None, topic=None):
    lookback_floor = timezone.localdate().year - settings.PREDICTION_LOOKBACK_YEARS
    queryset = Question.objects.filter(exam=exam, is_approved=True)
    if section:
        queryset = queryset.filter(section=section)
    if topic:
        queryset = queryset.filter(topic=topic)

    verified_queryset = queryset.filter(source_type=QuestionSourceType.VERIFIED_PAPER)
    if verified_queryset.exists():
        queryset = verified_queryset

    if not queryset.exists():
        queryset = ensure_generated_questions(exam, section, topic, count=15)

    topic_weights = Counter()
    question_scores = defaultdict(float)
    for question in queryset:
        exam_year = question.metadata.get("exam_year", timezone.localdate().year)
        recency_bonus = 1.0 if exam_year >= lookback_floor else 0.5
        key = question.topic_id or question.section_id or question.id
        topic_weights[key] += recency_bonus
        question_scores[question.id] += recency_bonus

    prediction_set = PredictionSet.objects.create(
        exam=exam,
        section=section,
        topic=topic,
        title=f"Likely-question practice set for {exam.name}",
        description="Probability-guided practice set assembled from historical trends and approved question bank.",
        generated_for=timezone.localdate(),
        weight_snapshot={"topic_weights": dict(topic_weights)},
        is_active=True,
    )

    for question in queryset[:25]:
        weight_key = question.topic_id or question.section_id or question.id
        PredictionSetQuestion.objects.create(
            prediction_set=prediction_set,
            question=question,
            score=question_scores[question.id] + topic_weights[weight_key],
        )
    return prediction_set
