from django.contrib import admin

from .models import (
    ContentAsset,
    CorpusChunk,
    Exam,
    Explanation,
    IngestionLog,
    PredictionSet,
    PredictionSetQuestion,
    Question,
    QuestionOption,
    Section,
    TelegramDeliveryLog,
    TelegramLink,
    TestResult,
    TestSession,
    TestSessionQuestion,
    TestTemplate,
    Topic,
)
from .tasks import ingest_content_asset


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4


class ExplanationInline(admin.StackedInline):
    model = Explanation
    extra = 1


class PredictionSetQuestionInline(admin.TabularInline):
    model = PredictionSetQuestion
    extra = 0
    autocomplete_fields = ("question",)


class TestSessionQuestionInline(admin.TabularInline):
    model = TestSessionQuestion
    extra = 0
    autocomplete_fields = ("question",)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    search_fields = ("name", "code")
    list_filter = ("is_active",)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "exam", "weightage_percent", "display_order")
    search_fields = ("name", "exam__name")
    list_filter = ("exam",)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "is_high_priority")
    search_fields = ("name", "section__name", "section__exam__name")
    list_filter = ("section__exam", "is_high_priority")


@admin.action(description="Queue ingestion for selected assets")
def queue_ingestion(modeladmin, request, queryset):
    for asset in queryset:
        ingest_content_asset.delay(asset.pk)


@admin.register(ContentAsset)
class ContentAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "asset_type", "exam", "ingestion_status", "is_public_licensed", "created_at")
    search_fields = ("title", "source_url", "source_notes")
    list_filter = ("asset_type", "ingestion_status", "is_public_licensed", "exam")
    actions = (queue_ingestion,)


@admin.register(CorpusChunk)
class CorpusChunkAdmin(admin.ModelAdmin):
    list_display = ("asset", "exam", "section", "topic", "created_at")
    search_fields = ("asset__title", "text")
    list_filter = ("exam", "section", "topic")


@admin.register(IngestionLog)
class IngestionLogAdmin(admin.ModelAdmin):
    list_display = ("asset", "status", "processed_chunks", "created_at")
    search_fields = ("asset__title", "message")
    list_filter = ("status",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "short_stem",
        "exam",
        "section",
        "topic",
        "difficulty",
        "source_type",
        "is_approved",
        "explanation_status",
    )
    list_filter = ("exam", "source_type", "difficulty", "is_approved", "explanation_status")
    search_fields = ("stem", "source_reference")
    inlines = (QuestionOptionInline, ExplanationInline)

    @staticmethod
    def short_stem(obj):
        return obj.stem[:80]


@admin.register(PredictionSet)
class PredictionSetAdmin(admin.ModelAdmin):
    list_display = ("title", "exam", "generated_for", "is_active")
    list_filter = ("exam", "is_active")
    search_fields = ("title", "description")
    inlines = (PredictionSetQuestionInline,)


@admin.register(TelegramLink)
class TelegramLinkAdmin(admin.ModelAdmin):
    list_display = ("chat_id", "username", "display_name", "is_active", "last_report_sent_at")
    search_fields = ("chat_id", "username", "display_name")
    list_filter = ("is_active",)


@admin.register(TestTemplate)
class TestTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "mode", "exam", "difficulty", "total_questions", "is_prediction_based")
    list_filter = ("mode", "exam", "difficulty", "is_prediction_based")
    search_fields = ("name",)


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "exam",
        "mode",
        "status",
        "score",
        "correct_count",
        "incorrect_count",
        "skipped_count",
        "started_at",
    )
    list_filter = ("exam", "mode", "status", "difficulty")
    search_fields = ("id", "telegram_link__chat_id", "telegram_link__username")
    readonly_fields = ("score", "max_score", "started_at", "submitted_at")
    inlines = (TestSessionQuestionInline,)


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ("test_session", "accuracy_percentage", "created_at")
    search_fields = ("test_session__id", "summary")


@admin.register(TelegramDeliveryLog)
class TelegramDeliveryLogAdmin(admin.ModelAdmin):
    list_display = ("telegram_link", "report_date", "status", "created_at")
    search_fields = ("telegram_link__chat_id", "telegram_link__username", "error_message")
    list_filter = ("status", "report_date")
