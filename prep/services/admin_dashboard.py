from collections import Counter

from django.utils import timezone

from prep.models import (
    ContentAsset,
    Exam,
    IngestionLog,
    IngestionStatus,
    PredictionSet,
    Question,
    QuestionSourceType,
    Section,
    TelegramDeliveryLog,
    TestResult,
    TestSession,
    TestStatus,
    TestTemplate,
    Topic,
)
from prep.services.ingestion import ingest_asset
from prep.services.prediction import generate_prediction_set
from prep.services.taxonomy import ensure_default_taxonomy


def build_admin_dashboard():
    ensure_default_taxonomy()

    assets = ContentAsset.objects.select_related("exam").order_by("-created_at")
    sessions = TestSession.objects.select_related("exam", "section", "topic").order_by("-started_at")
    predictions = PredictionSet.objects.select_related("exam").order_by("-generated_for", "-created_at")
    ingestion_logs = IngestionLog.objects.select_related("asset").order_by("-created_at")

    question_source_counts = Counter(
        Question.objects.values_list("source_type", flat=True)
    )
    session_status_counts = Counter(
        TestSession.objects.values_list("status", flat=True)
    )
    asset_status_counts = Counter(
        ContentAsset.objects.values_list("ingestion_status", flat=True)
    )
    delivery_status_counts = Counter(
        TelegramDeliveryLog.objects.values_list("status", flat=True)
    )

    return {
        "overview": {
            "exams": Exam.objects.count(),
            "sections": Section.objects.count(),
            "topics": Topic.objects.count(),
            "questions": Question.objects.count(),
            "content_assets": ContentAsset.objects.count(),
            "prediction_sets": PredictionSet.objects.count(),
            "test_templates": TestTemplate.objects.count(),
            "test_sessions": TestSession.objects.count(),
            "test_results": TestResult.objects.count(),
        },
        "operations": {
            "pending_assets": asset_status_counts.get(IngestionStatus.PENDING, 0),
            "failed_assets": asset_status_counts.get(IngestionStatus.FAILED, 0),
            "generated_questions": question_source_counts.get(QuestionSourceType.GENERATED, 0),
            "verified_questions": (
                question_source_counts.get(QuestionSourceType.VERIFIED_PAPER, 0)
                + question_source_counts.get(QuestionSourceType.VERIFIED_BOOK, 0)
                + question_source_counts.get(QuestionSourceType.VERIFIED_UPLOAD, 0)
            ),
            "in_progress_tests": session_status_counts.get(TestStatus.IN_PROGRESS, 0),
            "submitted_tests": session_status_counts.get(TestStatus.SUBMITTED, 0),
            "failed_reports": delivery_status_counts.get("failed", 0),
        },
        "recent_assets": list(assets[:5]),
        "recent_sessions": list(sessions[:6]),
        "recent_predictions": list(predictions[:5]),
        "recent_ingestion_logs": list(ingestion_logs[:6]),
        "attention_items": _build_attention_items(asset_status_counts, session_status_counts, delivery_status_counts),
        "admin_links": [
            {"label": "Manage content assets", "url": "/admin-panel/content-assets/"},
            {"label": "Review question bank", "url": "/admin-panel/questions/"},
            {"label": "Inspect prediction sets", "url": "/admin-panel/predictions/"},
            {"label": "Monitor test sessions", "url": "/admin-panel/test-sessions/"},
            {"label": "Open delivery logs", "url": "/admin-panel/delivery-logs/"},
            {"label": "Inspect ingestion logs", "url": "/admin-panel/ingestion-logs/"},
        ],
        "generated_at": timezone.localtime(),
    }


def run_admin_action(action: str):
    ensure_default_taxonomy()
    if action == "seed_taxonomy":
        ensure_default_taxonomy()
        return "Exam taxonomy is ready."

    if action == "generate_predictions":
        created = 0
        for exam in Exam.objects.filter(is_active=True):
            generate_prediction_set(exam)
            created += 1
        return f"Generated prediction sets for {created} active exams."

    if action == "ingest_pending_assets":
        processed = 0
        for asset in ContentAsset.objects.filter(ingestion_status=IngestionStatus.PENDING):
            ingest_asset(asset)
            processed += 1
        return f"Ingested {processed} pending content assets."

    if action == "approve_generated_questions":
        updated = Question.objects.filter(
            source_type=QuestionSourceType.GENERATED,
            is_approved=False,
        ).update(is_approved=True)
        return f"Approved {updated} generated questions."

    raise ValueError("Unknown admin action.")


def _build_attention_items(asset_status_counts, session_status_counts, delivery_status_counts):
    items = []
    failed_assets = asset_status_counts.get(IngestionStatus.FAILED, 0)
    if failed_assets:
        items.append(f"{failed_assets} content asset(s) need ingestion retry.")

    pending_assets = asset_status_counts.get(IngestionStatus.PENDING, 0)
    if pending_assets:
        items.append(f"{pending_assets} content asset(s) are waiting for ingestion.")

    in_progress = session_status_counts.get(TestStatus.IN_PROGRESS, 0)
    if in_progress:
        items.append(f"{in_progress} test session(s) are still in progress.")

    failed_reports = delivery_status_counts.get("failed", 0)
    if failed_reports:
        items.append(f"{failed_reports} report delivery attempt(s) failed.")

    if not items:
        items.append("No immediate operational alerts. The platform looks healthy.")
    return items
