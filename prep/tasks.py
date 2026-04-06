from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from prep.models import ContentAsset, TelegramLink
from prep.services.ingestion import ingest_asset
from prep.services.notifications import send_daily_summary


@shared_task
def ingest_content_asset(asset_id):
    asset = ContentAsset.objects.get(pk=asset_id)
    return ingest_asset(asset)


@shared_task
def send_daily_telegram_reports():
    report_date = timezone.localdate() - timedelta(days=1)
    sent_count = 0
    for telegram_link in TelegramLink.objects.filter(is_active=True):
        send_daily_summary(telegram_link, report_date=report_date)
        sent_count += 1
    return sent_count
