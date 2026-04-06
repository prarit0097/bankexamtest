from django import forms

from prep.models import DifficultyLevel, Exam, Section, TestMode, Topic
from prep.services.taxonomy import ensure_default_taxonomy


class TestCreationForm(forms.Form):
    mode = forms.ChoiceField(choices=TestMode.choices)
    exam = forms.ModelChoiceField(queryset=Exam.objects.none())
    section = forms.ModelChoiceField(
        queryset=Section.objects.none(),
        required=False,
        error_messages={"invalid_choice": "Choose a section from the selected exam."},
    )
    topic = forms.ModelChoiceField(
        queryset=Topic.objects.none(),
        required=False,
        error_messages={"invalid_choice": "Choose a topic that matches the selected exam and section."},
    )
    difficulty = forms.ChoiceField(choices=DifficultyLevel.choices, initial=DifficultyLevel.MEDIUM)
    question_count = forms.IntegerField(min_value=5, max_value=50, initial=10)
    duration_minutes = forms.IntegerField(min_value=5, max_value=180, initial=15)
    use_prediction = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        ensure_default_taxonomy()
        super().__init__(*args, **kwargs)
        self.fields["exam"].queryset = Exam.objects.filter(is_active=True)
        self.fields["section"].queryset = self._build_section_queryset()
        self.fields["topic"].queryset = self._build_topic_queryset()
        self.fields["section"].help_text = "Sections are limited to the chosen exam."
        self.fields["topic"].help_text = "Topics are limited to the chosen section."

    def clean(self):
        cleaned = super().clean()
        exam = cleaned.get("exam")
        section = cleaned.get("section")
        topic = cleaned.get("topic")

        if topic and not section:
            cleaned["section"] = topic.section
            section = topic.section

        if section and exam and section.exam_id != exam.id:
            self.add_error("section", "Choose a section from the selected exam.")
        if topic and section and topic.section_id != section.id:
            self.add_error("topic", "Choose a topic from the selected section.")
        if topic and exam and topic.section.exam_id != exam.id:
            self.add_error("topic", "Choose a topic from the selected exam.")
        return cleaned

    def _build_section_queryset(self):
        queryset = Section.objects.select_related("exam")
        exam_id = self._selected_exam_id()
        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)
        return queryset

    def _build_topic_queryset(self):
        queryset = Topic.objects.select_related("section", "section__exam")
        section_id = self._selected_section_id()
        exam_id = self._selected_exam_id()
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        elif exam_id:
            queryset = queryset.filter(section__exam_id=exam_id)
        return queryset

    def _selected_exam_id(self):
        if self.is_bound:
            return self.data.get("exam") or None
        initial_exam = self.initial.get("exam")
        return getattr(initial_exam, "id", initial_exam)

    def _selected_section_id(self):
        if self.is_bound:
            return self.data.get("section") or None
        initial_section = self.initial.get("section")
        return getattr(initial_section, "id", initial_section)


class StudentNameForm(forms.Form):
    display_name = forms.CharField(
        max_length=120,
        min_length=2,
        label="Student name",
        help_text="Choose the name you want to see on your profile page.",
    )
