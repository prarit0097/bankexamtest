from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from prep.models import DeliveryStatus, TelegramDeliveryLog, TestSession, TestStatus


def generate_daily_summary(telegram_link, report_date=None):
    report_date = report_date or timezone.localdate() - timedelta(days=1)
    sessions = TestSession.objects.filter(
        telegram_link=telegram_link,
        status=TestStatus.SUBMITTED,
        submitted_at__date=report_date,
    ).select_related("result")

    total_tests = sessions.count()
    total_score = sum(float(session.score) for session in sessions)
    total_possible = sum(float(session.max_score) for session in sessions)
    weak_areas = []
    for session in sessions:
        if hasattr(session, "result"):
            weak_areas.extend(item["label"] for item in session.result.weak_areas[:2])

    accuracy = round((total_score / total_possible) * 100, 2) if total_possible else 0.0
    payload = {
        "report_date": str(report_date),
        "tests_attempted": total_tests,
        "score": total_score,
        "possible_score": total_possible,
        "accuracy": accuracy,
        "weak_areas": weak_areas[:3],
    }
    text = (
        f"Daily Banking Prep Summary ({report_date})\n"
        f"Tests attempted: {total_tests}\n"
        f"Score: {int(total_score)}/{int(total_possible) if total_possible else 0}\n"
        f"Accuracy: {accuracy}%\n"
        f"Weak areas: {', '.join(payload['weak_areas']) if payload['weak_areas'] else 'No major weak area detected'}"
    )
    return text, payload


def send_daily_summary(telegram_link, report_date=None):
    report_date = report_date or timezone.localdate() - timedelta(days=1)
    text, payload = generate_daily_summary(telegram_link, report_date=report_date)
    log, _ = TelegramDeliveryLog.objects.get_or_create(
        telegram_link=telegram_link,
        report_date=report_date,
        defaults={"payload": payload},
    )
    log.payload = payload

    if not settings.TELEGRAM_BOT_TOKEN:
        log.status = DeliveryStatus.SKIPPED
        log.error_message = "TELEGRAM_BOT_TOKEN not configured"
        log.save(update_fields=["payload", "status", "error_message", "updated_at"])
        return log

    try:
        response = requests.post(
            f"{settings.TELEGRAM_API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": telegram_link.chat_id, "text": text},
            timeout=10,
        )
        response.raise_for_status()
        log.status = DeliveryStatus.SENT
        log.error_message = ""
        telegram_link.last_report_sent_at = timezone.now()
        telegram_link.save(update_fields=["last_report_sent_at", "updated_at"])
    except Exception as exc:
        log.status = DeliveryStatus.FAILED
        log.error_message = str(exc)

    log.save(update_fields=["payload", "status", "error_message", "updated_at"])
    return log
