from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from prep.models import (
    DifficultyLevel,
    ExplanationMode,
    Question,
    StudentAnswer,
    TelegramLink,
    TestMode,
    TestResult,
    TestSession,
    TestSessionQuestion,
    TestStatus,
    TestTemplate,
)
from prep.services.bootstrap import ensure_generated_questions
from prep.services.prediction import generate_prediction_set
from prep.services.rag import get_best_explanation


def create_test_session(
    *,
    exam,
    mode=TestMode.MOCK,
    section=None,
    topic=None,
    difficulty=DifficultyLevel.MEDIUM,
    question_count=None,
    duration_minutes=None,
    use_prediction=False,
    telegram_chat_id="",
):
    question_count = question_count or settings.DEFAULT_TEST_QUESTION_COUNT
    duration_minutes = duration_minutes or settings.DEFAULT_TEST_DURATION_MINUTES

    telegram_link = None
    if telegram_chat_id:
        telegram_link, _ = TelegramLink.objects.get_or_create(chat_id=telegram_chat_id.strip())

    queryset = Question.objects.filter(exam=exam, is_approved=True, difficulty=difficulty)
    if section:
        queryset = queryset.filter(section=section)
    if topic:
        queryset = queryset.filter(topic=topic)

    if use_prediction:
        prediction_set = generate_prediction_set(exam, section, topic)
        queryset = queryset.filter(prediction_items__prediction_set=prediction_set).distinct()

    if queryset.count() < question_count:
        ensure_generated_questions(
            exam=exam,
            section=section,
            topic=topic,
            difficulty=difficulty,
            count=question_count,
        )
        queryset = Question.objects.filter(exam=exam, is_approved=True, difficulty=difficulty)
        if section:
            queryset = queryset.filter(section=section)
        if topic:
            queryset = queryset.filter(topic=topic)

    selected_questions = list(queryset.order_by("?")[:question_count])
    template = TestTemplate.objects.create(
        name=f"{exam.code} {mode} {timezone.localtime():%Y-%m-%d %H:%M}",
        mode=mode,
        exam=exam,
        section=section,
        topic=topic,
        difficulty=difficulty,
        total_questions=len(selected_questions),
        duration_minutes=duration_minutes,
        is_prediction_based=use_prediction,
        metadata={"bootstrap_mode": not Question.objects.filter(exam=exam, source_type__startswith="verified").exists()},
    )
    session = TestSession.objects.create(
        test_template=template,
        telegram_link=telegram_link,
        exam=exam,
        section=section,
        topic=topic,
        mode=mode,
        difficulty=difficulty,
        status=TestStatus.IN_PROGRESS,
        started_at=timezone.now(),
        duration_minutes=duration_minutes,
        total_questions=len(selected_questions),
        max_score=Decimal(str(len(selected_questions))),
        metadata={"use_prediction": use_prediction},
    )
    TestSessionQuestion.objects.bulk_create(
        [
            TestSessionQuestion(test_session=session, question=question, position=index)
            for index, question in enumerate(selected_questions, start=1)
        ]
    )
    return session


@transaction.atomic
def submit_test_session(session, answers_by_question_id):
    if session.status == TestStatus.SUBMITTED:
        return session

    correct_count = 0
    incorrect_count = 0
    skipped_count = 0
    weak_area_counter = {}
    strength_counter = {}
    explanation_payload = []

    session_questions = session.session_questions.select_related(
        "question",
        "question__topic",
        "question__section",
    ).prefetch_related("question__options", "question__explanations")

    for session_question in session_questions:
        selected_option_id = answers_by_question_id.get(str(session_question.question_id))
        selected_option = None
        if selected_option_id:
            selected_option = session_question.question.options.filter(pk=selected_option_id).first()

        is_correct = bool(selected_option and selected_option.is_correct)
        StudentAnswer.objects.update_or_create(
            test_session_question=session_question,
            defaults={
                "selected_option": selected_option,
                "is_correct": is_correct,
                "answered_at": timezone.now() if selected_option else None,
            },
        )

        bucket = session_question.question.topic.name if session_question.question.topic else (
            session_question.question.section.name if session_question.question.section else "General"
        )
        if selected_option is None:
            skipped_count += 1
            weak_area_counter[bucket] = weak_area_counter.get(bucket, 0) + 1
        elif is_correct:
            correct_count += 1
            strength_counter[bucket] = strength_counter.get(bucket, 0) + 1
        else:
            incorrect_count += 1
            weak_area_counter[bucket] = weak_area_counter.get(bucket, 0) + 1

        explanation = get_best_explanation(session_question.question)
        explanation_payload.append(
            {
                "question_id": session_question.question_id,
                "question": session_question.question.stem,
                "explanation": explanation.text,
                "citations": explanation.citations,
                "mode": explanation.mode,
                "selected_option_id": selected_option.id if selected_option else None,
                "correct_option_id": session_question.question.correct_option.id if session_question.question.correct_option else None,
            }
        )

    session.correct_count = correct_count
    session.incorrect_count = incorrect_count
    session.skipped_count = skipped_count
    session.score = Decimal(str(correct_count))
    session.status = TestStatus.SUBMITTED
    session.submitted_at = timezone.now()
    session.save(
        update_fields=[
            "correct_count",
            "incorrect_count",
            "skipped_count",
            "score",
            "status",
            "submitted_at",
            "updated_at",
        ]
    )

    TestResult.objects.update_or_create(
        test_session=session,
        defaults={
            "accuracy_percentage": Decimal(str(session.accuracy_percentage)),
            "weak_areas": _ordered_buckets(weak_area_counter),
            "strengths": _ordered_buckets(strength_counter),
            "explanation_payload": explanation_payload,
            "summary": _build_summary(session, weak_area_counter),
        },
    )
    return session


def _ordered_buckets(counter_dict):
    items = sorted(counter_dict.items(), key=lambda item: item[1], reverse=True)
    return [{"label": label, "count": count} for label, count in items]


def _build_summary(session, weak_area_counter):
    if weak_area_counter:
        weakest_topic = max(weak_area_counter.items(), key=lambda item: item[1])[0]
        return (
            f"You scored {session.correct_count}/{session.total_questions}. "
            f"Revise {weakest_topic} first before attempting the next practice set."
        )
    return f"You scored {session.correct_count}/{session.total_questions}. Strong attempt."
