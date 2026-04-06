from datetime import timedelta
import tempfile
from unittest.mock import Mock, patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from prep.models import (
    ContentAsset,
    ContentAssetType,
    CorpusChunk,
    DeliveryStatus,
    Exam,
    Explanation,
    ExplanationMode,
    Question,
    QuestionSourceType,
    PredictionSet,
    TelegramLink,
    TestSession,
    TestStatus,
    UploadBatch,
)
from prep.services.assessment import create_test_session, submit_test_session
from prep.services.ingestion import ingest_asset
from prep.services.notifications import generate_daily_summary, send_daily_summary
from prep.services.rag import get_best_explanation
from prep.services.taxonomy import ensure_default_taxonomy
from prep.forms import TestCreationForm


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    OPENAI_API_KEY="",
    TELEGRAM_BOT_TOKEN="",
    DEFAULT_TELEGRAM_CHAT_ID="712615667",
)
class PrepPlatformTests(TestCase):
    def setUp(self):
        ensure_default_taxonomy()
        self.client = Client()
        self.exam = Exam.objects.get(code="IBPS-PO")
        self.section = self.exam.sections.first()
        self.topic = self.section.topics.first()
        self._media_dir = tempfile.TemporaryDirectory()
        self.override_media = override_settings(MEDIA_ROOT=self._media_dir.name)
        self.override_media.enable()

    def tearDown(self):
        self.override_media.disable()
        self._media_dir.cleanup()

    def test_home_page_loads(self):
        response = self.client.get(reverse("prep:home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Jeena Sikho")
        self.assertNotContains(response, "BANK EXAM PREP")
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Start New Test")
        self.assertContains(response, "Predicted Papers")
        self.assertContains(response, "Profile")
        self.assertContains(response, "Admin Panel")
        self.assertContains(response, "Start a Test")
        self.assertContains(response, "Select a section")
        self.assertContains(response, "Select a topic")
        self.assertContains(response, "Open profile dashboard")
        self.assertContains(response, "Browse predicted papers")
        self.assertNotContains(response, "Telegram")

    def test_predicted_papers_page_loads(self):
        generate_response = self.client.post(reverse("prep:admin-panel"), {"action": "generate_predictions"})
        self.assertEqual(generate_response.status_code, 302)

        response = self.client.get(reverse("prep:predicted-papers"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Predicted Papers")
        self.assertContains(response, "Future Paper Intelligence")
        self.assertContains(response, "Likely Pattern")

    def test_predicted_paper_detail_opens_full_question_list(self):
        self.client.post(reverse("prep:admin-panel"), {"action": "generate_predictions"})
        prediction = PredictionSet.objects.order_by("-id").first()

        response = self.client.get(reverse("prep:predicted-paper-detail", kwargs={"pk": prediction.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Predicted Paper Questions")
        self.assertContains(response, "Likely Pattern")
        self.assertNotContains(response, "[AI Practice]")

    def test_admin_panel_loads(self):
        response = self.client.get(reverse("prep:admin-panel"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Panel")
        self.assertContains(response, "Run Admin Actions")
        self.assertContains(response, "Deep Control Links")
        self.assertContains(response, "Uploading files...")
        self.assertContains(response, "data-upload-form")
        self.assertContains(response, reverse("prep:admin-content-assets"))
        self.assertContains(response, reverse("prep:admin-question-bank"))
        self.assertContains(response, reverse("prep:admin-predictions"))
        self.assertContains(response, reverse("prep:admin-test-sessions"))
        self.assertContains(response, reverse("prep:admin-delivery-logs"))
        self.assertContains(response, reverse("prep:admin-ingestion-logs"))
        self.assertNotContains(response, "Django admin")

    def test_admin_panel_generate_predictions_action(self):
        response = self.client.post(reverse("prep:admin-panel"), {"action": "generate_predictions"})
        self.assertEqual(response.status_code, 302)

        follow_up = self.client.get(reverse("prep:admin-panel"))
        self.assertContains(follow_up, "Generated prediction sets")
        self.assertContains(follow_up, "Recent Prediction Sets")

    def test_admin_panel_upload_previous_year_paper_infers_exam_and_year(self):
        upload_one = SimpleUploadedFile(
            "ibps-po-2023.txt",
            b"IBPS PO 2023 previous year paper. Quantitative Aptitude and Reasoning Ability practice.",
            content_type="text/plain",
        )
        upload_two = SimpleUploadedFile(
            "ibps-clerk-2022.txt",
            b"IBPS Clerk 2022 previous year paper. Puzzles, Arithmetic, and Banking Awareness questions.",
            content_type="text/plain",
        )
        response = self.client.post(
            reverse("prep:admin-panel"),
            {
                "action": "upload_previous_year_paper",
                "title": "IBPS PO 2023 Paper",
                "uploaded_files": [upload_one, upload_two],
            },
        )
        self.assertEqual(response.status_code, 302)
        batch = UploadBatch.objects.latest("id")
        self.assertEqual(batch.category, "previous_year_paper")
        self.assertEqual(batch.total_files, 2)
        self.assertIn("historical-paper-bank", batch.summary["bucket_distribution"])
        asset = ContentAsset.objects.filter(upload_batch=batch).order_by("id").first()
        self.assertEqual(asset.metadata["upload_category"], "previous_year_paper")
        self.assertEqual(asset.metadata["document_year"], "2023")
        self.assertEqual(asset.metadata["inferred_exam_code"], "IBPS-PO")
        self.assertIn("trend analysis", asset.metadata["recommended_usage"])

    def test_admin_panel_upload_test_paper_infers_exam_and_usage(self):
        upload = SimpleUploadedFile(
            "sbi-clerk-mock-2024.txt",
            b"SBI Clerk 2024 mock test paper with arithmetic, puzzles, and English language sections.",
            content_type="text/plain",
        )
        response = self.client.post(
            reverse("prep:admin-panel"),
            {
                "action": "upload_test_paper",
                "title": "SBI Clerk Mock 2024",
                "uploaded_files": [upload],
            },
        )
        self.assertEqual(response.status_code, 302)
        asset = ContentAsset.objects.latest("id")
        self.assertEqual(asset.metadata["upload_category"], "test_paper")
        self.assertEqual(asset.metadata["inferred_exam_code"], "SBI-CLERK")
        self.assertIn("mock test benchmarking", asset.metadata["recommended_usage"])

    def test_admin_panel_upload_study_material_infers_exam_and_usage(self):
        upload = SimpleUploadedFile(
            "rbi-assistant-guide.txt",
            b"RBI Assistant study material covering Indian Economy, Current Affairs, and Reading Comprehension for 2022 revision.",
            content_type="text/plain",
        )
        response = self.client.post(
            reverse("prep:admin-panel"),
            {
                "action": "upload_study_material",
                "title": "RBI Assistant Guide",
                "uploaded_files": [upload],
            },
        )
        self.assertEqual(response.status_code, 302)
        asset = ContentAsset.objects.latest("id")
        self.assertEqual(asset.metadata["upload_category"], "study_material")
        self.assertEqual(asset.metadata["inferred_exam_code"], "RBI-ASST")
        self.assertIn("RAG explanations", asset.metadata["recommended_usage"])

    def test_admin_section_pages_are_accessible(self):
        for route_name in (
            "prep:admin-content-assets",
            "prep:admin-question-bank",
            "prep:admin-predictions",
            "prep:admin-test-sessions",
            "prep:admin-delivery-logs",
            "prep:admin-ingestion-logs",
        ):
            response = self.client.get(reverse(route_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Back to admin panel")
            self.assertNotContains(response, "Django admin")

    def test_profile_page_loads_empty_state(self):
        response = self.client.get(reverse("prep:profile"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Jeena Sikho")
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Start New Test")
        self.assertContains(response, "Profile")
        self.assertContains(response, "Admin Panel")
        self.assertContains(response, "Student Profile")
        self.assertContains(response, "No completed test history yet.")
        self.assertContains(response, "Edit name")
        self.assertNotContains(response, "Telegram")

    def test_profile_page_updates_student_name(self):
        response = self.client.post(reverse("prep:profile"), {"display_name": "Prarit Student"})
        self.assertEqual(response.status_code, 302)

        follow_up = self.client.get(reverse("prep:profile"))
        self.assertContains(follow_up, "Prarit Student")
        self.assertContains(follow_up, "Edit name")

        link = TelegramLink.objects.get(chat_id="712615667")
        self.assertEqual(link.display_name, "Prarit Student")

    def test_profile_page_shows_aggregated_student_data(self):
        completed = create_test_session(
            exam=self.exam,
            mode="topic-wise",
            section=self.section,
            topic=self.topic,
            difficulty="medium",
            question_count=5,
            duration_minutes=15,
            use_prediction=True,
        )
        answers = {}
        for index, session_question in enumerate(completed.session_questions.all()):
            correct_option = session_question.question.correct_option
            if index < 2 and correct_option:
                answers[str(session_question.question_id)] = str(correct_option.id)
        submit_test_session(completed, answers)

        in_progress = create_test_session(
            exam=self.exam,
            mode="mock",
            section=self.section,
            topic=self.topic,
            difficulty="medium",
            question_count=5,
            duration_minutes=15,
        )

        response = self.client.get(reverse("prep:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Overall Performance")
        self.assertContains(response, "Prediction-based tests: 1")
        self.assertContains(response, self.topic.name)
        self.assertContains(response, "Recent Completed Tests")
        self.assertContains(response, "Resume test")
        self.assertContains(response, str(in_progress.pk))
        self.assertNotContains(response, "Telegram")

    def test_bound_form_filters_sections_and_topics_for_selected_exam(self):
        other_section = self.exam.sections.exclude(pk=self.section.pk).first()
        form = TestCreationForm(
            data={
                "mode": "topic-wise",
                "exam": self.exam.id,
                "section": self.section.id,
                "topic": self.topic.id,
                "difficulty": "medium",
                "question_count": 10,
                "duration_minutes": 15,
            }
        )

        self.assertTrue(form.fields["section"].queryset.filter(pk=self.section.pk).exists())
        self.assertFalse(form.fields["topic"].queryset.filter(section=other_section).exists())

    def test_create_test_session_bootstraps_generated_questions(self):
        session = create_test_session(
            exam=self.exam,
            mode="mock",
            section=self.section,
            topic=self.topic,
            difficulty="medium",
            question_count=5,
            duration_minutes=20,
            telegram_chat_id="1001",
        )
        self.assertEqual(session.total_questions, 5)
        self.assertEqual(session.session_questions.count(), 5)
        self.assertTrue(
            Question.objects.filter(
                exam=self.exam,
                topic=self.topic,
                source_type=QuestionSourceType.GENERATED,
            ).exists()
        )

    def test_create_test_session_uses_backend_default_telegram_chat_id(self):
        session = create_test_session(
            exam=self.exam,
            mode="mock",
            section=self.section,
            topic=self.topic,
            difficulty="medium",
            question_count=5,
            duration_minutes=20,
        )
        self.assertIsNotNone(session.telegram_link)
        self.assertEqual(session.telegram_link.chat_id, "712615667")

    def test_submit_session_uses_manual_explanation_when_available(self):
        session = create_test_session(
            exam=self.exam,
            mode="topic-wise",
            section=self.section,
            topic=self.topic,
            difficulty="medium",
            question_count=1,
        )
        session_question = session.session_questions.select_related("question").first()
        question = session_question.question
        question.explanations.all().delete()
        question.explanation_status = "manual"
        question.save(update_fields=["explanation_status", "updated_at"])
        Explanation.objects.create(
            question=question,
            mode=ExplanationMode.MANUAL,
            text="Manual explanation wins over other modes.",
            citations=["admin"],
            is_primary=True,
        )
        correct_option = question.correct_option

        submit_test_session(session, {str(question.id): str(correct_option.id)})
        session.refresh_from_db()

        self.assertEqual(session.status, TestStatus.SUBMITTED)
        self.assertEqual(session.correct_count, 1)
        self.assertEqual(session.result.explanation_payload[0]["mode"], ExplanationMode.MANUAL)

    def test_rag_explanation_uses_ingested_chunks(self):
        asset = ContentAsset.objects.create(
            title="Probability Notes",
            exam=self.exam,
            asset_type=ContentAssetType.PDF,
            source_notes="Probability questions often rely on event outcomes and ratio logic.",
        )
        ingest_asset(asset)
        question = Question.objects.create(
            exam=self.exam,
            section=self.section,
            topic=self.topic,
            stem="How should a probability ratio be interpreted in an aptitude question?",
            difficulty="medium",
            source_type=QuestionSourceType.VERIFIED_UPLOAD,
            source_asset=asset,
            source_reference="Custom upload",
        )
        question.options.create(text="Ignore sample space", sort_order=1, is_correct=False)
        question.options.create(text="Use favorable outcomes over total outcomes", sort_order=2, is_correct=True)
        question.options.create(text="Always multiply by 100", sort_order=3, is_correct=False)
        question.options.create(text="Subtract all outcomes", sort_order=4, is_correct=False)

        explanation = get_best_explanation(question)

        self.assertEqual(explanation.mode, ExplanationMode.RAG)
        self.assertTrue(CorpusChunk.objects.filter(asset=asset).exists())

    @override_settings(TELEGRAM_BOT_TOKEN="")
    def test_daily_summary_generation_and_skipped_delivery_without_token(self):
        telegram_link = TelegramLink.objects.create(chat_id="2002", username="student2002")
        session = create_test_session(
            exam=self.exam,
            mode="mock",
            section=self.section,
            topic=self.topic,
            question_count=1,
            telegram_chat_id=telegram_link.chat_id,
        )
        question = session.session_questions.first().question
        submit_test_session(session, {str(question.id): str(question.correct_option.id)})
        yesterday = timezone.now() - timedelta(days=1)
        session.submitted_at = yesterday
        session.save(update_fields=["submitted_at", "updated_at"])

        text, payload = generate_daily_summary(telegram_link)
        self.assertIn("Tests attempted: 1", text)
        self.assertEqual(payload["tests_attempted"], 1)

        delivery_log = send_daily_summary(telegram_link)
        self.assertEqual(delivery_log.status, DeliveryStatus.SKIPPED)

    @override_settings(TELEGRAM_BOT_TOKEN="test-token")
    def test_daily_summary_marks_failure_when_telegram_api_returns_not_ok(self):
        telegram_link = TelegramLink.objects.create(chat_id="9999", username="student9999")
        mocked_response = Mock()
        mocked_response.raise_for_status.return_value = None
        mocked_response.json.return_value = {"ok": False, "description": "Bad Request: chat not found"}

        with patch("prep.services.notifications.requests.post", return_value=mocked_response):
            delivery_log = send_daily_summary(telegram_link)

        self.assertEqual(delivery_log.status, DeliveryStatus.FAILED)
        self.assertIn("chat not found", delivery_log.error_message.lower())

    def test_student_flow_from_start_to_result(self):
        response = self.client.post(
            reverse("prep:start-test"),
            {
                "mode": "mock",
                "exam": self.exam.id,
                "section": self.section.id,
                "topic": self.topic.id,
                "difficulty": "medium",
                "question_count": 5,
                "duration_minutes": 10,
                "use_prediction": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        session = TestSession.objects.order_by("-id").first()
        self.assertEqual(session.telegram_link.chat_id, "712615667")
        detail = self.client.get(reverse("prep:session-detail", kwargs={"pk": session.pk}))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Dashboard")
        self.assertContains(detail, "Start New Test")
        self.assertContains(detail, "Profile")
        self.assertContains(detail, "Admin Panel")
        self.assertNotContains(detail, "Telegram")

        answers = {}
        for session_question in session.session_questions.all():
            answers[f"question_{session_question.question_id}"] = str(session_question.question.correct_option.id)
        submit = self.client.post(reverse("prep:submit-test", kwargs={"pk": session.pk}), answers)
        self.assertEqual(submit.status_code, 302)
        result = self.client.get(reverse("prep:result", kwargs={"pk": session.pk}))
        self.assertEqual(result.status_code, 200)
        self.assertContains(result, "Dashboard")
        self.assertContains(result, "Start New Test")
        self.assertContains(result, "Profile")
        self.assertContains(result, "Admin Panel")
        self.assertContains(result, "Result Summary")
        self.assertContains(result, "Back to dashboard")
        self.assertContains(result, "Start similar test again")
        self.assertContains(result, "View profile")

    def test_invalid_section_topic_combo_shows_clear_error(self):
        invalid_topic = self.exam.sections.exclude(pk=self.section.pk).first().topics.first()
        response = self.client.post(
            reverse("prep:start-test"),
            {
                "mode": "topic-wise",
                "exam": self.exam.id,
                "section": self.section.id,
                "topic": invalid_topic.id,
                "difficulty": "medium",
                "question_count": 10,
                "duration_minutes": 15,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test session could not be created")
        self.assertContains(response, "Choose a topic that matches the selected exam and section.")
