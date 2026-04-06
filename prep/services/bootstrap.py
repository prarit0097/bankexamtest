from collections import Counter

from prep.models import (
    DifficultyLevel,
    Explanation,
    ExplanationMode,
    ExplanationStatus,
    Question,
    QuestionOption,
    QuestionSourceType,
)
from prep.services.ai_client import generate_json


def ensure_generated_questions(exam, section=None, topic=None, difficulty=DifficultyLevel.MEDIUM, count=10):
    queryset = Question.objects.filter(
        exam=exam,
        source_type=QuestionSourceType.GENERATED,
        is_approved=True,
        difficulty=difficulty,
    )
    if section:
        queryset = queryset.filter(section=section)
    if topic:
        queryset = queryset.filter(topic=topic)

    deficit = max(0, count - queryset.count())
    if deficit:
        generated_payloads = _build_question_payloads(
            exam=exam,
            section=section,
            topic=topic,
            difficulty=difficulty,
            count=deficit,
        )
        for payload in generated_payloads:
            _create_generated_question(exam, section, topic, difficulty, payload)
        queryset = Question.objects.filter(
            exam=exam,
            source_type=QuestionSourceType.GENERATED,
            is_approved=True,
            difficulty=difficulty,
        )
        if section:
            queryset = queryset.filter(section=section)
        if topic:
            queryset = queryset.filter(topic=topic)
    return queryset.order_by("-created_at")[:count]


def build_generated_explanation(question):
    explanation = question.explanations.filter(mode=ExplanationMode.GENERATED, is_primary=True).first()
    if explanation:
        return explanation

    text = (
        f"This AI-generated practice question focuses on {question.topic or question.section or question.exam}. "
        "Review the correct option, then revise the underlying concept before attempting similar questions."
    )
    explanation = Explanation.objects.create(
        question=question,
        mode=ExplanationMode.GENERATED,
        text=text,
        citations=[],
        is_primary=True,
    )
    question.explanation_status = ExplanationStatus.GENERATED
    question.save(update_fields=["explanation_status", "updated_at"])
    return explanation


def _build_question_payloads(exam, section, topic, difficulty, count):
    prompt = _build_prompt(exam, section, topic, difficulty, count)
    payload = generate_json(prompt)
    if isinstance(payload, dict):
        payload = payload.get("questions")
    if isinstance(payload, list) and payload:
        return payload
    return _fallback_payloads(exam, section, topic, difficulty, count)


def _build_prompt(exam, section, topic, difficulty, count):
    scope = topic.name if topic else section.name if section else exam.name
    return (
        "Create banking exam practice MCQs as a JSON array under the key 'questions'. "
        "Each item must include stem, options (4 strings), correct_index (0-3), explanation, "
        "historical_pattern, and tags. "
        f"Target exam: {exam.name}. Scope: {scope}. Difficulty: {difficulty}. Count: {count}."
    )


def _fallback_payloads(exam, section, topic, difficulty, count):
    base_label = topic.name if topic else section.name if section else exam.name
    exam_name = exam.name
    patterns = Counter(["trend-frequency", "concept-recall", "mixed-revision"])
    payloads = []
    for index in range(count):
        correct_index = index % 4
        if topic:
            stem = (
                f"For the {exam_name} {topic.name} section, which statement best matches the concept tested in practice set #{index + 1}?"
            )
        elif section:
            stem = (
                f"In {exam_name}, which option is the best fit for the {section.name} pattern highlighted in practice set #{index + 1}?"
            )
        else:
            stem = f"Which option best fits the {exam_name} practice trend highlighted in set #{index + 1}?"
        payloads.append(
            {
                "stem": stem,
                "options": [
                    f"{base_label} concept option A",
                    f"{base_label} concept option B",
                    f"{base_label} concept option C",
                    f"{base_label} concept option D",
                ],
                "correct_index": correct_index,
                "explanation": (
                    f"This generated question trains the {base_label} pattern expected in {exam.name}. "
                    f"Revisit the key rule before retrying similar {difficulty} questions."
                ),
                "historical_pattern": patterns.most_common(1)[0][0],
                "tags": [exam.code.lower(), difficulty, base_label.lower().replace(" ", "-")],
            }
        )
    return payloads


def _create_generated_question(exam, section, topic, difficulty, payload):
    question = Question.objects.create(
        exam=exam,
        section=section,
        topic=topic,
        stem=payload["stem"],
        difficulty=difficulty,
        source_type=QuestionSourceType.GENERATED,
        source_reference=payload.get("historical_pattern", "bootstrap-ai"),
        explanation_status=ExplanationStatus.GENERATED,
        metadata={"tags": payload.get("tags", [])},
        is_approved=True,
        is_prediction_candidate=True,
    )
    for option_index, option_text in enumerate(payload["options"]):
        QuestionOption.objects.create(
            question=question,
            text=option_text,
            sort_order=option_index + 1,
            is_correct=option_index == payload["correct_index"],
        )
    Explanation.objects.create(
        question=question,
        mode=ExplanationMode.GENERATED,
        text=payload.get("explanation", "AI-generated practice explanation."),
        citations=[],
        is_primary=True,
    )
    return question
