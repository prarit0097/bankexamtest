from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
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
    reset_upload_category,
    run_admin_action,
    save_profile_name,
    submit_test_session,
)


class AppLoginView(LoginView):
    template_name = "prep/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return self.get_redirect_url() or reverse("prep:home")


class AppLogoutView(LogoutView):
    next_page = "prep:login"


class HomeView(LoginRequiredMixin, TemplateView):
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


class PredictedPapersView(LoginRequiredMixin, TemplateView):
    template_name = "prep/predicted_papers.html"

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        prediction_sets = PredictionSet.objects.select_related("exam", "section", "topic").order_by("-generated_for", "-created_at")
        context["prediction_sets"] = prediction_sets
        context["covered_exams_count"] = prediction_sets.values("exam_id").distinct().count()
        return context


class PredictedPaperDetailView(LoginRequiredMixin, DetailView):
    model = PredictionSet
    template_name = "prep/predicted_paper_detail.html"
    context_object_name = "prediction"

    def get_queryset(self):
        return PredictionSet.objects.select_related("exam", "section", "topic").prefetch_related(
            "items__question__options"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prediction_items = (
            self.object.items.select_related("question", "question__section", "question__topic")
            .exclude(question__metadata__is_placeholder_generated=True)
            .exclude(question__stem__startswith="[AI Practice]")
            .order_by("-score", "id")
        )
        context["prediction_items"] = prediction_items
        context["paper_sections"] = _group_prediction_items(prediction_items)
        return context


class AdminPanelView(LoginRequiredMixin, TemplateView):
    template_name = "prep/admin_panel.html"
    http_method_names = ["get", "post"]

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response

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
        reset_action = request.POST.get("action", "").strip()
        upload_action = request.POST.get("upload_action", "").strip()
        if upload_action in {"upload_previous_year_paper", "upload_test_paper", "upload_study_material"}:
            return self._handle_upload(request, upload_action)
        if reset_action in {"reset_previous_year_paper", "reset_test_paper", "reset_study_material"}:
            return self._handle_reset(reset_action)
        try:
            message = run_admin_action(reset_action)
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
            inferred_exam = first_asset.metadata.get("inferred_exam_name", "Pending scan") if first_asset else "Pending scan"
            inferred_year = first_asset.metadata.get("document_year") or "Pending scan" if first_asset else "Pending scan"
            messages.success(
                request,
                f"Uploaded {len(assets)} file(s) in batch '{batch.label}'. Ingestion is running in background. Primary inferred exam: {inferred_exam}. Primary inferred year: {inferred_year}.",
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

    def _handle_reset(self, action):
        category_map = {
            "reset_previous_year_paper": "previous_year_paper",
            "reset_test_paper": "test_paper",
            "reset_study_material": "study_material",
        }
        upload_category = category_map[action]
        result = reset_upload_category(upload_category)
        message = (
            f"Your data of {upload_category.replace('_', ' ')} is successfully reset. "
            f"Deleted {result['deleted_assets']} asset(s), {result['deleted_questions']} question(s), "
            f"and {result['deleted_batches']} batch(es)."
        )
        messages.success(
            self.request,
            message,
        )
        if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
            counts = build_admin_dashboard()["upload_category_counts"]
            return JsonResponse(
                {
                    "ok": True,
                    "message": message,
                    "counts": counts,
                    "redirect_url": f"{reverse('prep:admin-panel')}?refresh={result['reset_batch_id']}",
                }
            )
        return redirect("prep:admin-panel")


class PaginatedAdminSectionView(LoginRequiredMixin, TemplateView):
    template_name = "prep/admin_section.html"
    paginate_by = 25
    section_title = ""
    section_intro = ""
    item_type = ""

    def get_section_queryset(self):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        ensure_default_taxonomy()
        context = super().get_context_data(**kwargs)
        paginator = Paginator(self.get_section_queryset(), self.paginate_by)
        page_number = self.request.GET.get("page", 1)
        page_obj = paginator.get_page(page_number)
        context["section_title"] = self.section_title
        context["section_intro"] = self.section_intro
        context["section_items"] = page_obj
        context["page_obj"] = page_obj
        context["item_type"] = self.item_type
        return context


class AdminContentAssetsView(PaginatedAdminSectionView):
    section_title = "Content Assets"
    section_intro = "Review uploads, ingestion status, and manage content visibility from this in-app control view."
    item_type = "content"

    def get_section_queryset(self):
        return ContentAsset.objects.select_related("exam").order_by("-created_at")


class AdminQuestionBankView(PaginatedAdminSectionView):
    section_title = "Question Bank"
    section_intro = "Inspect approved/generated questions, difficulty, and source coverage."
    item_type = "question"

    def get_section_queryset(self):
        return Question.objects.select_related("exam", "section", "topic").order_by("-created_at")


class AdminPredictionSetsView(PaginatedAdminSectionView):
    section_title = "Prediction Sets"
    section_intro = "Open recent likely-question practice sets and check exam coverage."
    item_type = "prediction"

    def get_section_queryset(self):
        return PredictionSet.objects.select_related("exam", "section", "topic").order_by("-generated_for", "-created_at")


class AdminTestSessionsView(PaginatedAdminSectionView):
    section_title = "Test Sessions"
    section_intro = "Track active and submitted tests, score patterns, and question load."
    item_type = "session"

    def get_section_queryset(self):
        return TestSession.objects.select_related("exam", "section", "topic").order_by("-started_at")


class AdminDeliveryLogsView(PaginatedAdminSectionView):
    section_title = "Delivery Logs"
    section_intro = "Review outbound report delivery status and failure reasons."
    item_type = "delivery"

    def get_section_queryset(self):
        return TelegramDeliveryLog.objects.select_related("telegram_link").order_by("-report_date", "-created_at")


class AdminIngestionLogsView(PaginatedAdminSectionView):
    section_title = "Ingestion Logs"
    section_intro = "Inspect ingestion outcomes, chunk counts, and error messages."
    item_type = "ingestion"

    def get_section_queryset(self):
        return IngestionLog.objects.select_related("asset").order_by("-created_at")


class ProfileView(LoginRequiredMixin, TemplateView):
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


class StartTestView(LoginRequiredMixin, FormView):
    form_class = TestCreationForm
    template_name = "prep/home.html"
    http_method_names = ["post"]

    def form_valid(self, form):
        last_session = TestSession.objects.order_by("-started_at").first()
        if last_session and (timezone.now() - last_session.started_at).total_seconds() < 5:
            messages.warning(self.request, "Please wait a few seconds before starting another test.")
            return redirect("prep:home")
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


class TestSessionDetailView(LoginRequiredMixin, DetailView):
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


class SubmitTestView(LoginRequiredMixin, DetailView):
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
        submit_test_session(session, answers_by_question_id, submitted_at=timezone.now())
        messages.success(request, "Test submitted successfully.")
        return redirect("prep:result", pk=session.pk)


class TestResultView(LoginRequiredMixin, DetailView):
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


def _group_prediction_items(prediction_items):
    grouped = []
    seen = {}
    for index, item in enumerate(prediction_items, start=1):
        section_name = item.question.section.name if item.question.section else "General Paper"
        bucket = seen.get(section_name)
        if bucket is None:
            bucket = {"name": section_name, "items": []}
            seen[section_name] = bucket
            grouped.append(bucket)
        bucket["items"].append((index, item))
    return grouped
