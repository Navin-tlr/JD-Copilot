from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

import numpy as np
from pinecone import Pinecone

from .config import get_settings
from .utils import cosine_similarity, filter_metadata, role_contains, slugify_company
import os
import certifi
import requests


class EmbeddingBackend:
    """Provides embeddings with local model and robust fallback for offline tests."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.dim = 384
        self._model = None
        self._tokenizer = None
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name)
            # Infer output dimension with a quick pass
            test_vec = self._model.encode(["test"], normalize_embeddings=True)
            self.dim = int(test_vec.shape[1]) if hasattr(test_vec, "shape") else len(test_vec[0])
        except Exception:
            self._model = None

    def embed(self, texts: List[str]) -> np.ndarray:
        if self._model is not None:
            try:
                vecs = self._model.encode(texts, normalize_embeddings=True)
                return np.array(vecs, dtype=np.float32)
            except Exception:
                pass
        # Deterministic hashing fallback for offline reliability
        return self._hashing_vectors(texts)

    def _hashing_vectors(self, texts: List[str]) -> np.ndarray:
        rng = np.random.default_rng(42)
        # Fixed random projection matrix seeded for determinism
        projection = rng.standard_normal((1024, self.dim)).astype(np.float32)
        arrs: List[np.ndarray] = []
        for t in texts:
            h = np.frombuffer(t.encode("utf-8", errors="ignore"), dtype=np.uint8)
            if h.size == 0:
                h = np.array([0], dtype=np.uint8)
            # Repeat to length 1024 deterministically
            repeated = np.resize(h, 1024).astype(np.float32)
            vec = repeated @ projection
            # normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            arrs.append(vec.astype(np.float32))
        return np.vstack(arrs)


def get_pinecone_index():
    settings = get_settings()
    if not settings.PINECONE_API_KEY or not settings.PINECONE_INDEX_NAME:
        raise RuntimeError("Pinecone not configured. Set PINECONE_API_KEY and PINECONE_INDEX_NAME.")
    # Harden SSL for Pinecone HTTP client
    try:
        ca = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", ca)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca)
    except Exception:
        pass
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    return pc.Index(settings.PINECONE_INDEX_NAME)


MAX_SNIPPET_CHARS = 400


def retrieve_snippets(question: str, top_k: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    settings = get_settings()
    index = get_pinecone_index()
    embedder = EmbeddingBackend(settings.EMBED_MODEL)
    q_emb = embedder.embed([question])[0]

    # If company filter provided, bias the query by appending a tag and using slug
    company_text = filters.get("company")
    company_slug = slugify_company(company_text) if company_text else None
    if company_slug:
        question = f"[company={company_slug}] {question}"
        q_emb = embedder.embed([question])[0]

    res = index.query(vector=q_emb.tolist(), top_k=max(1, top_k * 2), include_metadata=True, include_values=False)
    matches = res.get("matches", []) if isinstance(res, dict) else getattr(res, "matches", [])
    # We don't store the original document text in Pinecone; return metadata with preview fields
    # To provide text for snippets, include a small slice from metadata if present
    scored = []
    for m in matches:
        meta = m.get("metadata", {}) if isinstance(m, dict) else getattr(m, "metadata", {})
        # Prefer slug exact match when provided
        if company_slug and meta.get("company_slug") != company_slug:
            continue
        if not role_contains(meta, filters.get("role_contains")):
            continue
        full_text = meta.get("chunk_text") or meta.get("preview") or ""
        text = full_text[:MAX_SNIPPET_CHARS]
        scored.append({
            "id": m.get("id") if isinstance(m, dict) else getattr(m, "id", None),
            "text": text,
            "score": float(m.get("score", 0.0) if isinstance(m, dict) else getattr(m, "score", 0.0)),
            "metadata": meta,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def synthesize_answer(question: str, snippets: List[Dict[str, Any]]) -> str | None:
    settings = get_settings()
    if settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            content = _build_prompt(question, snippets)
            model = settings.OPENAI_MODEL or "gpt-4o-mini"
            chat = client.chat.completions.create(
                model=model,
                temperature=0.0,
                max_tokens=220,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for job description analysis. Provide clear, natural, conversational answers using the provided context. Be specific and helpful while staying focused on the question. Include company/role details when relevant and cite sources as [Company | Role]."},
                    {"role": "user", "content": content},
                ],
            )
            return chat.choices[0].message.content
        except Exception:
            pass
    if settings.GEMINI_API_KEY:
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Ordered fallback list. First entry is explicit env override if provided.
            candidates = [
                settings.GEMINI_MODEL,
                "models/gemini-2.5-pro",
                "models/gemini-1.5-pro",
                "models/gemini-1.5-flash",
                "models/gemini-2.0-flash-exp",
            ]
            tried: set[str] = set()
            content = _build_prompt(question, snippets)
            def _extract_text(resp_obj) -> str | None:
                try:
                    txt = getattr(resp_obj, "text", None)
                    if txt:
                        return txt
                    # Fallback to candidates/parts aggregation
                    cand_list = getattr(resp_obj, "candidates", None)
                    if not cand_list:
                        return None
                    chunks: list[str] = []
                    for c in cand_list:
                        content = getattr(c, "content", None)
                        if not content:
                            continue
                        parts = getattr(content, "parts", None)
                        if not parts:
                            continue
                        for p in parts:
                            val = getattr(p, "text", None) or str(getattr(p, "inline_data", ""))
                            if val:
                                chunks.append(val)
                    return "\n".join([s for s in chunks if s]).strip() or None
                except Exception:
                    return None

            for mdl in [m for m in candidates if m and m not in tried]:
                tried.add(mdl)  # type: ignore[arg-type]
                try:
                    gm = genai.GenerativeModel(mdl)  # type: ignore[arg-type]
                    resp = gm.generate_content([
                        "You are a helpful AI assistant for job description analysis. Provide clear, natural, conversational answers using the provided context. Be specific and helpful while staying focused on the question. Include company/role details when relevant and cite sources as [Company | Role].",
                        content,
                    ], generation_config={"max_output_tokens": 300, "temperature": 0.2})
                    text = _extract_text(resp)
                    if text:
                        return text.strip()
                except Exception as inner_e:
                    print(f"Gemini model failed ({mdl}): {inner_e}")
                    continue
        except Exception as e:
            print(f"Error during Gemini synthesis: {e}")
            pass
    # OpenRouter fallback
    if settings.OPENROUTER_API_KEY:
        try:
            # Prepare messages in OpenAI-compatible format
            content = _build_prompt(question, snippets)
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://jd-copilot.local",
                "X-Title": "jd-copilot",
                "Content-Type": "application/json",
            }
            model = settings.OPENROUTER_MODEL or "openai/gpt-oss-20b:free"
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant for job description analysis. Provide concise, natural answers using only the provided context snippets and include inline citations [Company | Role | Year]."},
                    {"role": "user", "content": content},
                ],
                "temperature": 0.2,
                "max_tokens": 300,
            }
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=60)
            if resp.ok:
                data = resp.json()
                txt = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content")
                )
                if txt:
                    return txt.strip()
            else:
                print(f"OpenRouter error: {resp.status_code} {resp.text[:200]}")
        except Exception as e:
            print(f"OpenRouter synthesis failed: {e}")
    return None


def _build_prompt(question: str, snippets: List[Dict[str, Any]]) -> str:
    ctx_lines = []
    for s in snippets:
        meta = s.get("metadata", {})
        cite = f"[{meta.get('company','?')} | {meta.get('role','?')} | {meta.get('year','?')}]"
        ctx_lines.append(f"{cite} {s['text']}")
    context = "\n\n".join(ctx_lines)
    return (
        "Context snippets:\n" + context + "\n\n"
        + "Question: " + question + "\n"
        + "Instructions: Answer only the question, briefly (<=120 words). Use only provided context. Include inline citations in the form [Company | Role | Year]."
    )


