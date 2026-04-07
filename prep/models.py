from decimal import Decimal

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Exam(TimeStampedModel):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=32, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Section(TimeStampedModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120)
    description = models.TextField(blank=True)
    weightage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["exam__name", "display_order", "name"]
        unique_together = ("exam", "slug")

    def __str__(self) -> str:
        return f"{self.exam.code} - {self.name}"


class Topic(TimeStampedModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120)
    description = models.TextField(blank=True)
    is_high_priority = models.BooleanField(default=False)

    class Meta:
        ordering = ["section__display_order", "name"]
        unique_together = ("section", "slug")

    def __str__(self) -> str:
        return f"{self.section.name} / {self.name}"


class QuestionSourceType(models.TextChoices):
    GENERATED = "generated", "Generated"
    VERIFIED_PAPER = "verified-paper", "Verified Paper"
    VERIFIED_BOOK = "verified-book", "Verified Book"
    VERIFIED_UPLOAD = "verified-upload", "Verified Upload"


class DifficultyLevel(models.TextChoices):
    EASY = "easy", "Easy"
    MEDIUM = "medium", "Medium"
    HARD = "hard", "Hard"


class ExplanationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    MANUAL = "manual", "Manual"
    RAG = "rag", "RAG"
    GENERATED = "generated", "Generated"


class ContentAssetType(models.TextChoices):
    PAPER = "paper", "Past Paper"
    BOOK = "book", "Book"
    PDF = "pdf", "PDF"
    SYLLABUS = "syllabus", "Syllabus"
    UPLOAD = "upload", "Upload"


class IngestionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETE = "complete", "Complete"
    FAILED = "failed", "Failed"


class UploadBatch(TimeStampedModel):
    category = models.CharField(max_length=32)
    label = models.CharField(max_length=255)
    total_files = models.PositiveIntegerField(default=0)
    processed_files = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=32,
        choices=IngestionStatus.choices,
        default=IngestionStatus.PENDING,
    )
    summary = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.label


class ContentAsset(TimeStampedModel):
    title = models.CharField(max_length=255)
    exam = models.ForeignKey(
        Exam,
        on_delete=models.SET_NULL,
        related_name="content_assets",
        null=True,
        blank=True,
    )
    asset_type = models.CharField(max_length=32, choices=ContentAssetType.choices)
    upload_batch = models.ForeignKey(
        UploadBatch,
        on_delete=models.SET_NULL,
        related_name="assets",
        null=True,
        blank=True,
    )
    uploaded_file = models.FileField(upload_to="uploads/%Y/%m/", blank=True)
    source_url = models.URLField(blank=True)
    source_notes = models.TextField(blank=True)
    is_public_licensed = models.BooleanField(default=True)
    ingestion_status = models.CharField(
        max_length=32,
        choices=IngestionStatus.choices,
        default=IngestionStatus.PENDING,
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class IngestionLog(TimeStampedModel):
    asset = models.ForeignKey(ContentAsset, on_delete=models.CASCADE, related_name="ingestion_logs")
    status = models.CharField(max_length=32, choices=IngestionStatus.choices)
    message = models.TextField()
    processed_chunks = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.asset.title} - {self.status}"


class CorpusChunk(TimeStampedModel):
    asset = models.ForeignKey(ContentAsset, on_delete=models.CASCADE, related_name="chunks")
    exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    embedding = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["asset_id", "id"]

    def __str__(self) -> str:
        return f"{self.asset.title} chunk #{self.pk}"


class Question(TimeStampedModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, related_name="questions", null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, related_name="questions", null=True, blank=True)
    stem = models.TextField()
    difficulty = models.CharField(
        max_length=16,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
    )
    source_type = models.CharField(max_length=32, choices=QuestionSourceType.choices)
    source_asset = models.ForeignKey(
        ContentAsset,
        on_delete=models.SET_NULL,
        related_name="questions",
        null=True,
        blank=True,
    )
    source_reference = models.CharField(max_length=255, blank=True)
    explanation_status = models.CharField(
        max_length=16,
        choices=ExplanationStatus.choices,
        default=ExplanationStatus.PENDING,
    )
    is_approved = models.BooleanField(default=True)
    is_prediction_candidate = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["exam", "source_type", "difficulty"]),
            models.Index(fields=["exam", "section", "topic"]),
        ]

    def __str__(self) -> str:
        return self.stem[:80]

    @property
    def correct_option(self):
        return self.options.filter(is_correct=True).first()


class QuestionOption(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=255)
    sort_order = models.PositiveIntegerField(default=0)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "id"]
        unique_together = ("question", "sort_order")

    def __str__(self) -> str:
        return self.text


class ExplanationMode(models.TextChoices):
    MANUAL = "manual", "Manual"
    RAG = "rag", "RAG"
    GENERATED = "generated", "Generated"


class Explanation(TimeStampedModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="explanations")
    mode = models.CharField(max_length=16, choices=ExplanationMode.choices)
    text = models.TextField()
    citations = models.JSONField(default=list, blank=True)
    is_primary = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_primary", "-created_at"]

    def __str__(self) -> str:
        return f"{self.question_id} - {self.mode}"


class PredictionSet(TimeStampedModel):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="prediction_sets")
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        related_name="prediction_sets",
        null=True,
        blank=True,
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        related_name="prediction_sets",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    generated_for = models.DateField(default=timezone.localdate)
    weight_snapshot = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-generated_for", "-created_at"]

    def __str__(self) -> str:
        return self.title


class PredictionSetQuestion(TimeStampedModel):
    prediction_set = models.ForeignKey(
        PredictionSet,
        on_delete=models.CASCADE,
        related_name="items",
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="prediction_items")
    score = models.FloatField(default=0.0)

    class Meta:
        ordering = ["-score", "id"]
        unique_together = ("prediction_set", "question")

    def __str__(self) -> str:
        return f"{self.prediction_set_id} - {self.question_id}"


class TelegramLink(TimeStampedModel):
    chat_id = models.CharField(max_length=128, unique=True)
    username = models.CharField(max_length=64, blank=True)
    display_name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    linked_at = models.DateTimeField(default=timezone.now)
    last_report_sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["username", "chat_id"]

    def __str__(self) -> str:
        return self.username or self.chat_id


class TestMode(models.TextChoices):
    MOCK = "mock", "Mock Test"
    TOPIC_WISE = "topic-wise", "Topic-wise Test"


class TestStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    IN_PROGRESS = "in-progress", "In Progress"
    SUBMITTED = "submitted", "Submitted"


class TestTemplate(TimeStampedModel):
    name = models.CharField(max_length=255)
    mode = models.CharField(max_length=24, choices=TestMode.choices)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="test_templates")
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        related_name="test_templates",
        null=True,
        blank=True,
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        related_name="test_templates",
        null=True,
        blank=True,
    )
    difficulty = models.CharField(
        max_length=16,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
    )
    total_questions = models.PositiveIntegerField(default=10)
    duration_minutes = models.PositiveIntegerField(default=15)
    is_prediction_based = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name


class TestSession(TimeStampedModel):
    test_template = models.ForeignKey(
        TestTemplate,
        on_delete=models.SET_NULL,
        related_name="test_sessions",
        null=True,
        blank=True,
    )
    telegram_link = models.ForeignKey(
        TelegramLink,
        on_delete=models.SET_NULL,
        related_name="test_sessions",
        null=True,
        blank=True,
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="test_sessions")
    section = models.ForeignKey(
        Section,
        on_delete=models.SET_NULL,
        related_name="test_sessions",
        null=True,
        blank=True,
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        related_name="test_sessions",
        null=True,
        blank=True,
    )
    mode = models.CharField(max_length=24, choices=TestMode.choices)
    difficulty = models.CharField(
        max_length=16,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
    )
    status = models.CharField(max_length=24, choices=TestStatus.choices, default=TestStatus.DRAFT)
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=15)
    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    incorrect_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0.00"))
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.exam.code} {self.mode} #{self.pk}"

    @property
    def accuracy_percentage(self) -> float:
        if not self.total_questions:
            return 0.0
        return round((self.correct_count / self.total_questions) * 100, 2)

    @property
    def completion_duration_seconds(self) -> int:
        if not self.started_at or not self.submitted_at:
            return 0
        return max(0, int((self.submitted_at - self.started_at).total_seconds()))

    @property
    def completion_duration_label(self) -> str:
        total_seconds = self.completion_duration_seconds
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        return f"{minutes}m {seconds}s"


class TestSessionQuestion(TimeStampedModel):
    test_session = models.ForeignKey(
        TestSession,
        on_delete=models.CASCADE,
        related_name="session_questions",
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="session_instances")
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["position"]
        unique_together = ("test_session", "position")

    def __str__(self) -> str:
        return f"Session {self.test_session_id} Q{self.position}"


class StudentAnswer(TimeStampedModel):
    test_session_question = models.OneToOneField(
        TestSessionQuestion,
        on_delete=models.CASCADE,
        related_name="student_answer",
    )
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        related_name="student_answers",
        null=True,
        blank=True,
    )
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Answer for session question {self.test_session_question_id}"


class TestResult(TimeStampedModel):
    test_session = models.OneToOneField(
        TestSession,
        on_delete=models.CASCADE,
        related_name="result",
    )
    accuracy_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    weak_areas = models.JSONField(default=list, blank=True)
    strengths = models.JSONField(default=list, blank=True)
    explanation_payload = models.JSONField(default=list, blank=True)
    summary = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Result for session {self.test_session_id}"


class DeliveryStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SENT = "sent", "Sent"
    FAILED = "failed", "Failed"
    SKIPPED = "skipped", "Skipped"


class TelegramDeliveryLog(TimeStampedModel):
    telegram_link = models.ForeignKey(
        TelegramLink,
        on_delete=models.CASCADE,
        related_name="delivery_logs",
    )
    report_date = models.DateField()
    status = models.CharField(max_length=16, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-report_date", "-created_at"]
        unique_together = ("telegram_link", "report_date")

    def __str__(self) -> str:
        return f"{self.telegram_link} - {self.report_date}"
