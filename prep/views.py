from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, TemplateView

from prep.forms import StudentNameForm, TestCreationForm
from prep.models import ContentAsset, PredictionSet, Section, TestSession, TestStatus, Topic
from prep.services import (
    build_profile_dashboard,
    create_test_session,
    ensure_default_taxonomy,
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
