from collections import Counter
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from prep.models import TelegramLink, TestSession, TestStatus


def build_profile_dashboard(chat_id=None):
    target_chat_id = (chat_id or settings.DEFAULT_TELEGRAM_CHAT_ID or "").strip()
    link = TelegramLink.objects.filter(chat_id=target_chat_id).first() if target_chat_id else None

    sessions = (
        TestSession.objects.filter(telegram_link__chat_id=target_chat_id)
        .select_related("exam", "section", "topic", "result", "telegram_link")
        .order_by("-started_at")
        if target_chat_id
        else TestSession.objects.none()
    )
    completed_sessions = sessions.filter(status=TestStatus.SUBMITTED)

    total_started = sessions.count()
    total_completed = completed_sessions.count()
    total_questions = sum(session.total_questions for session in completed_sessions)
    total_correct = sum(session.correct_count for session in completed_sessions)
    total_incorrect = sum(session.incorrect_count for session in completed_sessions)
    total_skipped = sum(session.skipped_count for session in completed_sessions)
    overall_accuracy = _safe_percentage(total_correct, total_questions)
    average_accuracy = round(
        sum(session.accuracy_percentage for session in completed_sessions) / total_completed, 2
    ) if total_completed else 0.0
    completion_rate = _safe_percentage(total_completed, total_started)
    best_accuracy = max((session.accuracy_percentage for session in completed_sessions), default=0.0)
    prediction_tests = sum(1 for session in completed_sessions if session.metadata.get("use_prediction"))

    weak_counter = Counter()
    strength_counter = Counter()
    exam_counter = Counter()
    mode_counter = Counter()
    for session in completed_sessions:
        exam_counter[session.exam.name] += 1
        mode_counter[session.get_mode_display()] += 1
        if hasattr(session, "result"):
            weak_counter.update(_expand_counter_payload(session.result.weak_areas))
            strength_counter.update(_expand_counter_payload(session.result.strengths))

    streak_summary = _compute_streaks(completed_sessions)
    goals = _build_goals(
        total_completed=total_completed,
        overall_accuracy=overall_accuracy,
        total_skipped=total_skipped,
        current_streak=streak_summary["current_streak"],
    )
    opportunities = _build_opportunities(weak_counter, overall_accuracy, total_incorrect)

    return {
        "chat_id": target_chat_id,
        "profile_name": _display_name(link, target_chat_id),
        "telegram_username": link.username if link else "",
        "linked_at": link.linked_at if link else None,
        "last_report_sent_at": link.last_report_sent_at if link else None,
        "has_profile": bool(target_chat_id),
        "has_test_data": total_started > 0,
        "total_started": total_started,
        "total_completed": total_completed,
        "completion_rate": completion_rate,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "total_incorrect": total_incorrect,
        "total_skipped": total_skipped,
        "overall_accuracy": overall_accuracy,
        "average_accuracy": average_accuracy,
        "best_accuracy": best_accuracy,
        "prediction_tests": prediction_tests,
        "current_streak": streak_summary["current_streak"],
        "longest_streak": streak_summary["longest_streak"],
        "last_active_date": streak_summary["last_active_date"],
        "weak_areas": _top_counter_items(weak_counter),
        "strengths": _top_counter_items(strength_counter),
        "exam_mix": _top_counter_items(exam_counter),
        "mode_mix": _top_counter_items(mode_counter),
        "goals": goals,
        "opportunities": opportunities,
        "recent_sessions": list(completed_sessions[:5]),
        "in_progress_sessions": list(sessions.filter(status=TestStatus.IN_PROGRESS)[:3]),
    }


def _safe_percentage(numerator, denominator):
    if not denominator:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _expand_counter_payload(items):
    expanded = Counter()
    for item in items:
        label = item.get("label")
        count = item.get("count", 0)
        if label:
            expanded[label] += count
    return expanded


def _top_counter_items(counter, limit=5):
    return [{"label": label, "count": count} for label, count in counter.most_common(limit)]


def _display_name(link, chat_id):
    if not link:
        return "Profile"
    if link.display_name:
        return link.display_name
    if link.username:
        return f"@{link.username}"
    return f"Chat {chat_id}"


def _compute_streaks(completed_sessions):
    dates = sorted({timezone.localtime(session.submitted_at).date() for session in completed_sessions if session.submitted_at})
    if not dates:
        return {"current_streak": 0, "longest_streak": 0, "last_active_date": None}

    longest = 1
    running = 1
    for previous, current in zip(dates, dates[1:]):
        if current == previous + timedelta(days=1):
            running += 1
            longest = max(longest, running)
        else:
            running = 1

    current_streak = 1
    for previous, current in zip(reversed(dates[:-1]), reversed(dates[1:])):
        if current == previous + timedelta(days=1):
            current_streak += 1
        else:
            break

    return {
        "current_streak": current_streak,
        "longest_streak": longest,
        "last_active_date": dates[-1],
    }


def _build_goals(*, total_completed, overall_accuracy, total_skipped, current_streak):
    goals = []
    accuracy_target = 70 if overall_accuracy < 70 else 80
    goals.append(
        {
            "title": f"Reach {accuracy_target}% accuracy",
            "detail": f"Current overall accuracy is {overall_accuracy}%. Focus on high-frequency weak areas first.",
        }
    )
    tests_goal = 5 if total_completed < 5 else total_completed + 3
    goals.append(
        {
            "title": f"Complete {tests_goal} total tests",
            "detail": f"You have completed {total_completed} tests so far. Keep building exam stamina.",
        }
    )
    skip_target = 0 if total_skipped == 0 else max(1, total_skipped // max(total_completed, 1))
    goals.append(
        {
            "title": "Reduce skipped questions",
            "detail": f"Target {skip_target} or fewer skipped questions per completed test.",
        }
    )
    goals.append(
        {
            "title": "Maintain your streak",
            "detail": f"Current streak is {current_streak} day(s). Try to practice daily for consistency.",
        }
    )
    return goals


def _build_opportunities(weak_counter, overall_accuracy, total_incorrect):
    opportunities = []
    if weak_counter:
        for label, count in weak_counter.most_common(3):
            opportunities.append(
                {
                    "title": f"Improve {label}",
                    "detail": f"{label} appeared as a weak area {count} time(s). A focused topic-wise drill can quickly improve this.",
                }
            )
    if overall_accuracy < 60:
        opportunities.append(
            {
                "title": "Build a stronger accuracy base",
                "detail": "Accuracy is below 60%, so start with easier topic drills before long mocks.",
            }
        )
    if total_incorrect:
        opportunities.append(
            {
                "title": "Review explanation patterns",
                "detail": "Use the result-page explanations to identify repeated mistake patterns and revise those concepts first.",
            }
        )
    return opportunities[:4]
