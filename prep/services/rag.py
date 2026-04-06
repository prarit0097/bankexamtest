from collections import Counter

from prep.models import CorpusChunk, Explanation, ExplanationMode, ExplanationStatus
from prep.services.ai_client import cosine_similarity, embed_texts, generate_json
from prep.services.bootstrap import build_generated_explanation


def get_best_explanation(question):
    manual = question.explanations.filter(mode=ExplanationMode.MANUAL, is_primary=True).first()
    if manual:
        question.explanation_status = ExplanationStatus.MANUAL
        question.save(update_fields=["explanation_status", "updated_at"])
        return manual

    relevant_chunks = get_relevant_chunks(question)
    if relevant_chunks:
        primary_rag = question.explanations.filter(mode=ExplanationMode.RAG, is_primary=True).first()
        if primary_rag:
            question.explanation_status = ExplanationStatus.RAG
            question.save(update_fields=["explanation_status", "updated_at"])
            return primary_rag

        chunk_text = "\n\n".join(chunk.text[:700] for chunk in relevant_chunks[:3])
        prompt = (
            "Use the following study material excerpts to explain why the correct answer is right "
            "for this banking exam question.\n"
            f"Question: {question.stem}\n"
            f"Material:\n{chunk_text}\n"
            "Return JSON with keys text and citations."
        )
        payload = generate_json(prompt)
        if not isinstance(payload, dict):
            payload = {
                "text": f"Relevant study material points to the correct option by reinforcing the key concept behind: {question.stem}",
                "citations": [chunk.asset.title for chunk in relevant_chunks[:2]],
            }
        explanation = Explanation.objects.create(
            question=question,
            mode=ExplanationMode.RAG,
            text=payload["text"],
            citations=payload.get("citations", [chunk.asset.title for chunk in relevant_chunks[:2]]),
            is_primary=True,
        )
        question.explanation_status = ExplanationStatus.RAG
        question.save(update_fields=["explanation_status", "updated_at"])
        return explanation

    return build_generated_explanation(question)


def get_relevant_chunks(question, limit=3):
    chunks = CorpusChunk.objects.filter(exam=question.exam)
    if question.section_id:
        scoped = chunks.filter(section=question.section)
        if scoped.exists():
            chunks = scoped
    if question.topic_id:
        scoped = chunks.filter(topic=question.topic)
        if scoped.exists():
            chunks = scoped

    keyword_scores = Counter()
    tokens = _tokenize(question.stem)
    query_embedding = embed_texts([question.stem])[0]
    scored = []
    for chunk in chunks:
        overlap = len(tokens.intersection(_tokenize(chunk.text)))
        similarity = cosine_similarity(query_embedding, chunk.embedding)
        score = overlap + similarity
        if score > 0:
            scored.append((score, chunk))
            keyword_scores[chunk.asset_id] += overlap

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]


def _tokenize(text):
    return {token.lower() for token in text.split() if len(token) > 3}
