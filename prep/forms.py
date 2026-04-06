from django import forms

from prep.models import DifficultyLevel, Exam, Section, TestMode, Topic
from prep.services.taxonomy import ensure_default_taxonomy


class TestCreationForm(forms.Form):
    mode = forms.ChoiceField(choices=TestMode.choices)
    exam = forms.ModelChoiceField(queryset=Exam.objects.none())
    section = forms.ModelChoiceField(queryset=Section.objects.none(), required=False)
    topic = forms.ModelChoiceField(queryset=Topic.objects.none(), required=False)
    difficulty = forms.ChoiceField(choices=DifficultyLevel.choices, initial=DifficultyLevel.MEDIUM)
    question_count = forms.IntegerField(min_value=5, max_value=50, initial=10)
    duration_minutes = forms.IntegerField(min_value=5, max_value=180, initial=15)
    use_prediction = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        ensure_default_taxonomy()
        super().__init__(*args, **kwargs)
        self.fields["exam"].queryset = Exam.objects.filter(is_active=True)
        self.fields["section"].queryset = Section.objects.select_related("exam")
        self.fields["topic"].queryset = Topic.objects.select_related("section", "section__exam")

    def clean(self):
        cleaned = super().clean()
        exam = cleaned.get("exam")
        section = cleaned.get("section")
        topic = cleaned.get("topic")

        if section and exam and section.exam_id != exam.id:
            self.add_error("section", "Choose a section from the selected exam.")
        if topic and section and topic.section_id != section.id:
            self.add_error("topic", "Choose a topic from the selected section.")
        if topic and exam and topic.section.exam_id != exam.id:
            self.add_error("topic", "Choose a topic from the selected exam.")
        return cleaned
