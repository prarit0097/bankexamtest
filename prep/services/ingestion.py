from pathlib import Path

import requests
from pypdf import PdfReader

from prep.models import ContentAsset, ContentAssetType, CorpusChunk, Exam, IngestionLog, IngestionStatus
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


def build_content_asset_from_upload(*, upload_category: str, uploaded_file, title: str = ""):
    asset_type = _resolve_asset_type(upload_category, uploaded_file.name)
    asset = ContentAsset.objects.create(
        title=title.strip() or Path(uploaded_file.name).stem.replace("_", " ").replace("-", " ").title(),
        asset_type=asset_type,
        uploaded_file=uploaded_file,
        is_public_licensed=True,
        ingestion_status=IngestionStatus.PENDING,
        metadata={"upload_category": upload_category},
    )
    ingest_asset(asset)
    asset.refresh_from_db()
    return asset


def infer_asset_metadata(asset: ContentAsset, text: str):
    content = f"{asset.title}\n{asset.source_notes}\n{text}".strip()
    content_lower = content.lower()

    metadata = {
        "upload_category": asset.metadata.get("upload_category", "upload"),
        "document_year": _infer_year(content),
        "matched_topics": _infer_topics(content_lower),
        "recommended_usage": _recommended_usage(asset.metadata.get("upload_category", "upload")),
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
