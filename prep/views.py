from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, TemplateView

from prep.forms import AdminAssetUploadForm, StudentNameForm, TestCreationForm
from prep.models import (
    ContentAsset,
    IngestionLog,
    PredictionSet,
    Question,
    Section,
    TelegramDeliveryLog,
    TestSession,
    TestStatus,
    Topic,
)
from prep.services import (
    build_admin_dashboard,
    build_content_assets_from_uploads,
    build_profile_dashboard,
    create_test_session,
    ensure_default_taxonomy,
    run_admin_action,
    save_profile_name,
    submit_test_session,
)


class HomeView(TemplateView):
    template_name = "prep/home.html"

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        context["form"] = kwargs.get("form") or TestCreationForm()
        context["prediction_sets"] = PredictionSet.objects.select_related("exam")[:5]
        context["content_assets"] = ContentAsset.objects.select_related("exam")[:5]
        context["predicted_papers"] = PredictionSet.objects.select_related("exam").order_by("-generated_for", "-created_at")[:6]
        context["section_catalog"] = [
            {"id": section.id, "label": str(section), "exam_id": section.exam_id}
            for section in Section.objects.select_related("exam").order_by("exam__name", "display_order", "name")
        ]
        context["topic_catalog"] = [
            {
                "id": topic.id,
                "label": topic.name,
                "section_id": topic.section_id,
                "exam_id": topic.section.exam_id,
            }
            for topic in Topic.objects.select_related("section", "section__exam").order_by("section__name", "name")
        ]
        return context


class PredictedPapersView(TemplateView):
    template_name = "prep/predicted_papers.html"

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        prediction_sets = PredictionSet.objects.select_related("exam", "section", "topic").order_by("-generated_for", "-created_at")
        context["prediction_sets"] = prediction_sets
        return context


class PredictedPaperDetailView(DetailView):
    model = PredictionSet
    template_name = "prep/predicted_paper_detail.html"
    context_object_name = "prediction"

    def get_queryset(self):
        return PredictionSet.objects.select_related("exam", "section", "topic").prefetch_related(
            "items__question__options"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prediction_items = self.object.items.select_related("question", "question__section", "question__topic").order_by("-score", "id")
        context["prediction_items"] = prediction_items
        return context


class AdminPanelView(TemplateView):
    template_name = "prep/admin_panel.html"
    http_method_names = ["get", "post"]

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        context["admin_panel"] = build_admin_dashboard()
        context["previous_year_form"] = kwargs.get("previous_year_form") or AdminAssetUploadForm(
            upload_label="Previous year paper file"
        )
        context["test_paper_form"] = kwargs.get("test_paper_form") or AdminAssetUploadForm(
            upload_label="Test paper file"
        )
        context["study_material_form"] = kwargs.get("study_material_form") or AdminAssetUploadForm(
            upload_label="Study material file"
        )
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "").strip()
        if action in {"upload_previous_year_paper", "upload_test_paper", "upload_study_material"}:
            return self._handle_upload(request, action)
        try:
            message = run_admin_action(action)
        except ValueError:
            messages.error(request, "Unknown admin action.")
        else:
            messages.success(request, message)
        return redirect("prep:admin-panel")

    def _handle_upload(self, request, action):
        form_map = {
            "upload_previous_year_paper": ("previous_year_paper", AdminAssetUploadForm(request.POST, request.FILES, upload_label="Previous year paper file")),
            "upload_test_paper": ("test_paper", AdminAssetUploadForm(request.POST, request.FILES, upload_label="Test paper file")),
            "upload_study_material": ("study_material", AdminAssetUploadForm(request.POST, request.FILES, upload_label="Study material file")),
        }
        upload_category, form = form_map[action]
        if form.is_valid():
            result = build_content_assets_from_uploads(
                upload_category=upload_category,
                uploaded_files=form.cleaned_data["uploaded_files"],
                title=form.cleaned_data.get("title", ""),
            )
            batch = result["batch"]
            assets = result["assets"]
            first_asset = assets[0] if assets else None
            inferred_exam = first_asset.metadata.get("inferred_exam_name", "Unknown exam") if first_asset else "Unknown exam"
            inferred_year = first_asset.metadata.get("document_year") or "Unknown year" if first_asset else "Unknown year"
            messages.success(
                request,
                f"Uploaded {len(assets)} file(s) in batch '{batch.label}'. Primary inferred exam: {inferred_exam}. Primary inferred year: {inferred_year}.",
            )
            return redirect("prep:admin-panel")

        messages.error(request, "Upload failed. Please correct the file form and try again.")
        context = {
            "previous_year_form": AdminAssetUploadForm(upload_label="Previous year paper file"),
            "test_paper_form": AdminAssetUploadForm(upload_label="Test paper file"),
            "study_material_form": AdminAssetUploadForm(upload_label="Study material file"),
        }
        if upload_category == "previous_year_paper":
            context["previous_year_form"] = form
        elif upload_category == "test_paper":
            context["test_paper_form"] = form
        else:
            context["study_material_form"] = form
        return self.render_to_response(self.get_context_data(**context))


class AdminContentAssetsView(TemplateView):
    template_name = "prep/admin_section.html"

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        context["section_title"] = "Content Assets"
        context["section_intro"] = "Review uploads, ingestion status, and manage content visibility from this in-app control view."
        context["section_items"] = ContentAsset.objects.select_related("exam").order_by("-created_at")[:25]
        context["item_type"] = "content"
        return context


class AdminQuestionBankView(TemplateView):
    template_name = "prep/admin_section.html"

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        context["section_title"] = "Question Bank"
        context["section_intro"] = "Inspect approved/generated questions, difficulty, and source coverage."
        context["section_items"] = Question.objects.select_related("exam", "section", "topic").order_by("-created_at")[:30]
        context["item_type"] = "question"
        return context


class AdminPredictionSetsView(TemplateView):
    template_name = "prep/admin_section.html"

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        context["section_title"] = "Prediction Sets"
        context["section_intro"] = "Open recent likely-question practice sets and check exam coverage."
        context["section_items"] = PredictionSet.objects.select_related("exam", "section", "topic").order_by("-generated_for", "-created_at")[:25]
        context["item_type"] = "prediction"
        return context


class AdminTestSessionsView(TemplateView):
    template_name = "prep/admin_section.html"

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        context["section_title"] = "Test Sessions"
        context["section_intro"] = "Track active and submitted tests, score patterns, and question load."
        context["section_items"] = TestSession.objects.select_related("exam", "section", "topic").order_by("-started_at")[:30]
        context["item_type"] = "session"
        return context


class AdminDeliveryLogsView(TemplateView):
    template_name = "prep/admin_section.html"

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        context["section_title"] = "Delivery Logs"
        context["section_intro"] = "Review outbound report delivery status and failure reasons."
        context["section_items"] = TelegramDeliveryLog.objects.select_related("telegram_link").order_by("-report_date", "-created_at")[:30]
        context["item_type"] = "delivery"
        return context


class AdminIngestionLogsView(TemplateView):
    template_name = "prep/admin_section.html"

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        context["section_title"] = "Ingestion Logs"
        context["section_intro"] = "Inspect ingestion outcomes, chunk counts, and error messages."
        context["section_items"] = IngestionLog.objects.select_related("asset").order_by("-created_at")[:30]
        context["item_type"] = "ingestion"
        return context


class ProfileView(TemplateView):
    template_name = "prep/profile.html"
    http_method_names = ["get", "post"]

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        profile = build_profile_dashboard()
        initial_name = "" if profile["profile_name"] == "Student" else profile["profile_name"]
        context["profile"] = profile
        context["name_form"] = kwargs.get("name_form") or StudentNameForm(initial={"display_name": initial_name})
        return context

    def post(self, request, *args, **kwargs):
        form = StudentNameForm(request.POST)
        if form.is_valid():
            save_profile_name(form.cleaned_data["display_name"])
            messages.success(request, "Student name updated successfully.")
            return redirect("prep:profile")

        messages.error(request, "Student name could not be updated. Please correct the field and try again.")
        return self.render_to_response(self.get_context_data(name_form=form))


class StartTestView(FormView):
    form_class = TestCreationForm
    template_name = "prep/home.html"
    http_method_names = ["post"]

    def form_valid(self, form):
        session = create_test_session(
            exam=form.cleaned_data["exam"],
            mode=form.cleaned_data["mode"],
            section=form.cleaned_data.get("section"),
            topic=form.cleaned_data.get("topic"),
            difficulty=form.cleaned_data["difficulty"],
            question_count=form.cleaned_data["question_count"],
            duration_minutes=form.cleaned_data["duration_minutes"],
            use_prediction=form.cleaned_data["use_prediction"],
        )
        messages.success(self.request, "Test session created.")
        return redirect("prep:session-detail", pk=session.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Test session could not be created. Check the section/topic combination and try again.")
        return self.render_to_response(self.get_context_data(form=form))


class TestSessionDetailView(DetailView):
    model = TestSession
    template_name = "prep/session_detail.html"
    context_object_name = "session"

    def get_queryset(self):
        return TestSession.objects.select_related(
            "exam",
            "section",
            "topic",
            "telegram_link",
        ).prefetch_related("session_questions__question__options")


class SubmitTestView(DetailView):
    model = TestSession
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        session = self.get_object()
        if session.status == TestStatus.SUBMITTED:
            return redirect("prep:result", pk=session.pk)

        answers_by_question_id = {
            key.replace("question_", ""): value
            for key, value in request.POST.items()
            if key.startswith("question_")
        }
        submit_test_session(session, answers_by_question_id)
        messages.success(request, "Test submitted successfully.")
        return redirect("prep:result", pk=session.pk)


class TestResultView(DetailView):
    model = TestSession
    template_name = "prep/result.html"
    context_object_name = "session"

    def get_queryset(self):
        return TestSession.objects.select_related(
            "exam",
            "section",
            "topic",
            "result",
            "telegram_link",
        ).prefetch_related("session_questions__question__options")

    def dispatch(self, request, *args, **kwargs):
        session = self.get_object()
        if session.status != TestStatus.SUBMITTED:
            messages.info(request, "Submit the test before viewing results.")
            return HttpResponseRedirect(reverse("prep:session-detail", kwargs={"pk": session.pk}))
        return super().dispatch(request, *args, **kwargs)
