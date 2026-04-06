import json
import math
import re
from typing import Iterable

from django.conf import settings
from openai import OpenAI


def get_client():
    if not settings.OPENAI_API_KEY:
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _extract_json_block(raw_text: str):
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    return None


def generate_json(prompt: str):
    client = get_client()
    if client is None:
        return None

    try:
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=f"{prompt}\nReturn JSON only.",
        )
    except Exception:
        return None

    output_text = getattr(response, "output_text", "")
    if not output_text:
        return None
    return _extract_json_block(output_text)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    clean_texts = [text for text in texts if text]
    if not clean_texts:
        return []

    client = get_client()
    if client is None:
        return [_naive_embedding(text) for text in clean_texts]

    try:
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=clean_texts,
        )
        return [item.embedding for item in response.data]
    except Exception:
        return [_naive_embedding(text) for text in clean_texts]


def cosine_similarity(first: list[float], second: list[float]) -> float:
    if not first or not second or len(first) != len(second):
        return 0.0
    numerator = sum(a * b for a, b in zip(first, second))
    first_norm = math.sqrt(sum(a * a for a in first))
    second_norm = math.sqrt(sum(b * b for b in second))
    if not first_norm or not second_norm:
        return 0.0
    return numerator / (first_norm * second_norm)


def _naive_embedding(text: str) -> list[float]:
    buckets = [0.0] * 12
    for index, token in enumerate(re.findall(r"[a-z0-9]+", text.lower())):
        bucket = index % len(buckets)
        buckets[bucket] += float((len(token) % 7) + 1)
    return buckets
