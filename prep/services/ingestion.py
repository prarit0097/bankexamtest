from pathlib import Path
from collections import Counter

import requests
from pypdf import PdfReader

from prep.models import ContentAsset, ContentAssetType, CorpusChunk, Exam, IngestionLog, IngestionStatus, UploadBatch
from prep.services.ai_client import embed_texts, generate_json
from prep.services.taxonomy import MAJOR_BANKING_TAXONOMY


def ingest_asset(asset: ContentAsset):
    asset.ingestion_status = IngestionStatus.PROCESSING
    asset.save(update_fields=["ingestion_status", "updated_at"])

    try:
        text = _extract_text(asset)
        inferred_metadata = infer_asset_metadata(asset, text)
        asset.metadata = {**asset.metadata, **inferred_metadata}
        inferred_exam_code = inferred_metadata.get("inferred_exam_code")
        if inferred_exam_code and not asset.exam_id:
            asset.exam = Exam.objects.filter(code=inferred_exam_code).first()
        if inferred_metadata.get("resolved_title") and not asset.title:
            asset.title = inferred_metadata["resolved_title"]
        asset.save(update_fields=["metadata", "exam", "title", "updated_at"])
        chunks = _split_text(text)
        embeddings = embed_texts(chunks)
        CorpusChunk.objects.filter(asset=asset).delete()
        CorpusChunk.objects.bulk_create(
            [
                CorpusChunk(
                    asset=asset,
                    exam=asset.exam,
                    text=chunk_text,
                    metadata={"chunk_index": index},
                    embedding=embeddings[index] if index < len(embeddings) else [],
                )
                for index, chunk_text in enumerate(chunks)
            ]
        )
        IngestionLog.objects.create(
            asset=asset,
            status=IngestionStatus.COMPLETE,
            message=f"Ingested {len(chunks)} chunks.",
            processed_chunks=len(chunks),
        )
        asset.ingestion_status = IngestionStatus.COMPLETE
        asset.save(update_fields=["ingestion_status", "updated_at"])
        return len(chunks)
    except Exception as exc:
        IngestionLog.objects.create(
            asset=asset,
            status=IngestionStatus.FAILED,
            message=str(exc),
            processed_chunks=0,
        )
        asset.ingestion_status = IngestionStatus.FAILED
        asset.save(update_fields=["ingestion_status", "updated_at"])
        raise


def _extract_text(asset: ContentAsset):
    if asset.uploaded_file:
        suffix = Path(asset.uploaded_file.name).suffix.lower()
        if suffix == ".pdf":
            reader = PdfReader(asset.uploaded_file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        return asset.uploaded_file.read().decode("utf-8", errors="ignore")

    if asset.source_url:
        response = requests.get(asset.source_url, timeout=10)
        response.raise_for_status()
        return response.text

    if asset.source_notes:
        return asset.source_notes
    raise ValueError("No asset content available for ingestion.")


def _split_text(text: str, chunk_size: int = 900, overlap: int = 120):
    if not text.strip():
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


def build_content_assets_from_uploads(*, upload_category: str, uploaded_files, title: str = ""):
    uploaded_files = list(uploaded_files)
    batch = UploadBatch.objects.create(
        category=upload_category,
        label=_build_batch_label(upload_category, uploaded_files, title),
        total_files=len(uploaded_files),
        processed_files=0,
        status=IngestionStatus.PROCESSING if uploaded_files else IngestionStatus.PENDING,
        summary={},
    )

    created_assets = []
    for index, uploaded_file in enumerate(uploaded_files, start=1):
        asset = _create_asset_for_upload(
            upload_category=upload_category,
            uploaded_file=uploaded_file,
            title=title if len(uploaded_files) == 1 else "",
            upload_batch=batch,
            index=index,
        )
        ingest_asset(asset)
        asset.refresh_from_db()
        created_assets.append(asset)

    batch.processed_files = len(created_assets)
    batch.status = IngestionStatus.COMPLETE if created_assets else IngestionStatus.PENDING
    batch.summary = summarize_upload_batch(batch, created_assets)
    batch.save(update_fields=["processed_files", "status", "summary", "updated_at"])

    return {"batch": batch, "assets": created_assets}


def _create_asset_for_upload(*, upload_category: str, uploaded_file, title: str = "", upload_batch=None, index: int = 1):
    asset_type = _resolve_asset_type(upload_category, uploaded_file.name)
    asset = ContentAsset.objects.create(
        title=title.strip() or Path(uploaded_file.name).stem.replace("_", " ").replace("-", " ").title(),
        asset_type=asset_type,
        upload_batch=upload_batch,
        uploaded_file=uploaded_file,
        is_public_licensed=True,
        ingestion_status=IngestionStatus.PENDING,
        metadata={"upload_category": upload_category, "batch_index": index},
    )
    return asset


def _build_batch_label(upload_category: str, uploaded_files, title: str = ""):
    category_label = {
        "previous_year_paper": "Previous Year Papers",
        "test_paper": "Test Papers",
        "study_material": "Study Materials",
    }.get(upload_category, "Upload Batch")
    if title.strip():
        return title.strip()
    return f"{category_label} Batch ({len(uploaded_files)} files)"


def infer_asset_metadata(asset: ContentAsset, text: str):
    content = f"{asset.title}\n{asset.source_notes}\n{text}".strip()
    content_lower = content.lower()

    metadata = {
        "upload_category": asset.metadata.get("upload_category", "upload"),
        "document_year": _infer_year(content),
        "matched_topics": _infer_topics(content_lower),
        "recommended_usage": _recommended_usage(asset.metadata.get("upload_category", "upload")),
        "recommended_bucket": _recommended_bucket(asset.metadata.get("upload_category", "upload")),
        "resolved_title": asset.title or Path(asset.uploaded_file.name).stem.replace("_", " ").replace("-", " ").title(),
    }

    inferred_exam = _infer_exam(content_lower)
    if inferred_exam:
        metadata["inferred_exam_code"] = inferred_exam["code"]
        metadata["inferred_exam_name"] = inferred_exam["name"]

    ai_metadata = _infer_via_ai(asset, text)
    if ai_metadata:
        metadata.update({key: value for key, value in ai_metadata.items() if value})

    return metadata


def summarize_upload_batch(batch: UploadBatch, assets):
    exam_counter = Counter()
    year_counter = Counter()
    bucket_counter = Counter()
    usage_list = []

    for asset in assets:
        exam_name = asset.metadata.get("inferred_exam_name") or "Unknown exam"
        exam_counter[exam_name] += 1
        year = asset.metadata.get("document_year") or "Unknown year"
        year_counter[year] += 1
        bucket = asset.metadata.get("recommended_bucket") or "general-support"
        bucket_counter[bucket] += 1
        usage = asset.metadata.get("recommended_usage")
        if usage and usage not in usage_list:
            usage_list.append(usage)

    return {
        "exam_distribution": dict(exam_counter),
        "year_distribution": dict(year_counter),
        "bucket_distribution": dict(bucket_counter),
        "usage_guidance": usage_list[:3],
        "arrangement_notes": _batch_arrangement_notes(batch.category, bucket_counter, exam_counter, year_counter),
    }


def _resolve_asset_type(upload_category: str, filename: str):
    suffix = Path(filename).suffix.lower()
    if upload_category == "study_material":
        return ContentAssetType.BOOK if suffix in {".pdf", ".doc", ".docx"} else ContentAssetType.UPLOAD
    return ContentAssetType.PAPER


def _infer_year(content: str):
    import re

    years = re.findall(r"\b(20\d{2})\b", content)
    return years[0] if years else ""


def _infer_exam(content_lower: str):
    aliases = {
        "IBPS-PO": ["ibps po", "ibps probationary officer", "po prelims", "po mains"],
        "IBPS-CLERK": ["ibps clerk", "clerk prelims", "clerk mains"],
        "SBI-PO": ["sbi po", "sbi probationary officer"],
        "SBI-CLERK": ["sbi clerk"],
        "RBI-ASST": ["rbi assistant", "rbi asst"],
        "NABARD-A": ["nabard grade a", "nabard a", "nabard assistant manager"],
    }
    for exam_data in MAJOR_BANKING_TAXONOMY:
        code = exam_data["code"]
        candidates = [exam_data["name"].lower(), code.lower().replace("-", " ")] + aliases.get(code, [])
        if any(candidate in content_lower for candidate in candidates):
            return {"code": code, "name": exam_data["name"]}
    return None


def _infer_topics(content_lower: str):
    topic_hits = []
    for exam_data in MAJOR_BANKING_TAXONOMY:
        for section_name, topics in exam_data["sections"].items():
            if section_name.lower() in content_lower:
                topic_hits.append(section_name)
            for topic in topics:
                if topic.lower() in content_lower:
                    topic_hits.append(topic)
    deduped = []
    for item in topic_hits:
        if item not in deduped:
            deduped.append(item)
    return deduped[:6]


def _recommended_usage(upload_category: str):
    if upload_category == "previous_year_paper":
        return "Use for exam trend analysis, likely-question prediction, and verified-paper review."
    if upload_category == "test_paper":
        return "Use for mock test benchmarking, practice-set enrichment, and difficulty calibration."
    if upload_category == "study_material":
        return "Use for RAG explanations, topic revision support, and study references."
    return "Use as a general supporting content asset."


def _recommended_bucket(upload_category: str):
    if upload_category == "previous_year_paper":
        return "historical-paper-bank"
    if upload_category == "test_paper":
        return "mock-and-practice-bank"
    if upload_category == "study_material":
        return "study-reference-bank"
    return "general-support"


def _batch_arrangement_notes(upload_category: str, bucket_counter, exam_counter, year_counter):
    category_name = {
        "previous_year_paper": "previous year papers",
        "test_paper": "test papers",
        "study_material": "study materials",
    }.get(upload_category, "documents")
    top_exam = exam_counter.most_common(1)[0][0] if exam_counter else "mixed exams"
    top_year = year_counter.most_common(1)[0][0] if year_counter else "mixed years"
    top_bucket = bucket_counter.most_common(1)[0][0] if bucket_counter else "general-support"
    return (
        f"Arrange these {category_name} under {top_bucket}, prioritize {top_exam}, "
        f"and use {top_year} as the primary year grouping where available."
    )


def _infer_via_ai(asset: ContentAsset, text: str):
    sample = text[:3500]
    if not sample.strip():
        return None

    prompt = (
        "You are classifying a banking exam preparation document. "
        "Return JSON with keys inferred_exam_code, inferred_exam_name, document_year, "
        "recommended_usage, and resolved_title. "
        f"Upload category: {asset.metadata.get('upload_category', 'upload')}. "
        f"Current title: {asset.title}. "
        f"Document sample:\n{sample}"
    )
    payload = generate_json(prompt)
    return payload if isinstance(payload, dict) else None
