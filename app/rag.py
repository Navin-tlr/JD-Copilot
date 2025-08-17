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

# Add Gemini import
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


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

    # --- ADVANCED SYSTEM PROMPT (Final, "Uncaged" Version) ---
    system_prompt = """
You are JD-GPT, a seasoned AI career coach and industry expert. Your primary goal is to provide students with insightful, comprehensive, and well-reasoned answers about job descriptions.

**Your Core Principles:**
1.  **Synthesize, Don't Just Summarize:** Use the provided text as your primary source, but you are encouraged to **enrich your answer with your own general knowledge** about the job market, career paths, and corporate roles.
2.  **Explain the "Why":** When you make an inference or connect concepts (e.g., explaining that "Business Development" is a form of marketing), you must clearly explain your reasoning.
3.  **Adopt a Conversational and Encouraging Tone:** Speak directly to the student. Be a helpful guide, not a robot. Use formatting like bold text and bullet points to make your advice easy to digest.
4.  **Be Honest About Missing Information:** If the provided text is missing critical details (like a specific salary range), state that clearly, but you can also provide a general market estimate based on your own knowledge.

**Example of a good response:**

*User Question:* "Is this a marketing role?"

*Your Answer:*
Yes, absolutely. While the official title is **Business Development Associate**, this is fundamentally a marketing and sales role. In the tech industry, "Business Development" often involves a mix of sales, relationship-building, and strategic marketing to grow the company.

Based on the job description, you can see this clearly:
* The role focuses heavily on **lead generation** using techniques like cold calling and LinkedIn outreach, which are classic sales and digital marketing activities.
* The goal of **partnership development** is a form of business-to-business (B2B) marketing, where you are essentially selling the value of TAP Academy's students to other companies.
* The fact that a **degree in Marketing** is listed as a preferred qualification is a strong indicator that the company itself views this as a marketing-oriented position.
"""

    # --- Build the final prompt for the API call ---
    context = "\n\n".join(
        f"[{s.get('metadata', {}).get('company','?')} | {s.get('metadata', {}).get('role','?')} | {s.get('metadata', {}).get('year','?')}] {s['text']}"
        for s in snippets
    )
    
    final_prompt = (
        "CONTEXT:\n"
        "---------------------\n"
        f"{context}\n"
        "---------------------\n\n"
        f"QUESTION: {question}"
    )

    # If Gemini is configured, use it for synthesis
    if settings.GEMINI_API_KEY and GEMINI_AVAILABLE:
        print(f"🟢 Attempting synthesis with Gemini model: {settings.GEMINI_MODEL or 'gemini-2.0-flash-exp'}")
        try:
            # Configure Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Use the specified model or default to a reliable one
            gemini_model = settings.GEMINI_MODEL or "gemini-2.0-flash-exp"
            
            # Create the model instance
            model = genai.GenerativeModel(gemini_model)
            
            # Combine system prompt and user prompt for Gemini
            combined_prompt = f"{system_prompt}\n\n{final_prompt}"
            
            # Generate content with safety settings disabled for professional documents
            response = model.generate_content(
                combined_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=1024,
                ),
                safety_settings=[
                    {
                        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                    {
                        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        "threshold": HarmBlockThreshold.BLOCK_NONE,
                    },
                ]
            )
            
            if response and response.text:
                print("✅ Successfully received answer from Gemini.")
                return response.text.strip()
            else:
                return "The model generated an empty response. Please try rephrasing your question."
                
        except Exception as e:
            print(f"❌ Error while calling Gemini: {e}")
            import traceback
            traceback.print_exc()
            return f"Error calling Gemini: {e}"

    # If we reach here, Gemini was not configured or its call failed.
    # Skip synthesis and return None so the API returns retrieved snippets only.
    print("🔴 No Gemini API key configured or Gemini generation failed. Skipping synthesis.")
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


