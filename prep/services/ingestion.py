from pathlib import Path

import requests
from pypdf import PdfReader

from prep.models import ContentAsset, CorpusChunk, IngestionLog, IngestionStatus
from prep.services.ai_client import embed_texts


def ingest_asset(asset: ContentAsset):
    asset.ingestion_status = IngestionStatus.PROCESSING
    asset.save(update_fields=["ingestion_status", "updated_at"])

    try:
        text = _extract_text(asset)
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
