from collections import Counter, defaultdict

from django.conf import settings
from django.utils import timezone

from prep.models import PredictionSet, PredictionSetQuestion, Question, QuestionSourceType
from prep.services.ai_client import generate_json
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
    else:
        queryset = queryset.exclude(stem__startswith="[AI Practice]")

    if not queryset.exists():
        queryset = ensure_generated_questions(exam, section, topic, count=15)
    elif hasattr(queryset, "exclude"):
        filtered_queryset = queryset.exclude(stem__startswith="[AI Practice]")
        if filtered_queryset.exists():
            queryset = filtered_queryset

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

    selected_questions = list(queryset[:25])
    for question in selected_questions:
        weight_key = question.topic_id or question.section_id or question.id
        PredictionSetQuestion.objects.create(
            prediction_set=prediction_set,
            question=question,
            score=question_scores[question.id] + topic_weights[weight_key],
        )

    ai_payload = _build_prediction_ai_payload(exam, selected_questions, topic_weights)
    prediction_set.description = ai_payload["summary"]
    prediction_set.weight_snapshot = {
        **prediction_set.weight_snapshot,
        "predicted_paper_title": ai_payload["predicted_paper_title"],
        "predicted_pattern": ai_payload["predicted_pattern"],
        "predicted_focus_areas": ai_payload["predicted_focus_areas"],
    }
    prediction_set.save(update_fields=["description", "weight_snapshot", "updated_at"])
    return prediction_set


def _build_prediction_ai_payload(exam, selected_questions, topic_weights):
    topic_names = []
    for question in selected_questions[:12]:
        if question.topic and question.topic.name not in topic_names:
            topic_names.append(question.topic.name)
        elif question.section and question.section.name not in topic_names:
            topic_names.append(question.section.name)

    fallback = {
        "predicted_paper_title": f"Future predicted paper for {exam.name}",
        "summary": (
            f"Future predicted paper draft for {exam.name}. This paper prioritizes historically repeated sections, "
            "verified question-bank signals, and the strongest topic trends currently available."
        ),
        "predicted_pattern": "Balanced paper with heavier emphasis on recurring high-frequency sections and recent trend topics.",
        "predicted_focus_areas": topic_names[:5],
    }

    if not settings.OPENAI_API_KEY:
        return fallback

    prompt = (
        "You are helping a banking exam prep platform create a future predicted paper view. "
        "Return JSON with keys predicted_paper_title, summary, predicted_pattern, predicted_focus_areas. "
        f"Exam: {exam.name}. "
        f"Detected recurring topic signals: {topic_names[:8]}. "
        f"Topic weights: {dict(list(topic_weights.items())[:10])}. "
        "Keep the summary under 70 words. predicted_focus_areas should be a short list of strings."
    )
    payload = generate_json(prompt)
    if not isinstance(payload, dict):
        return fallback

    return {
        "predicted_paper_title": payload.get("predicted_paper_title") or fallback["predicted_paper_title"],
        "summary": payload.get("summary") or fallback["summary"],
        "predicted_pattern": payload.get("predicted_pattern") or fallback["predicted_pattern"],
        "predicted_focus_areas": payload.get("predicted_focus_areas") or fallback["predicted_focus_areas"],
    }
