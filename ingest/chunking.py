from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings
from app.utils import count_tokens


def hybrid_chunk_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Chunk sections using token-aware strategy.

    - Tables/salary-like sections remain atomic.
    - Long textual sections split into chunks near CHUNK_SIZE with CHUNK_OVERLAP.
    """
    cfg = get_settings()
    chunk_size = int(cfg.CHUNK_SIZE)
    overlap = int(cfg.CHUNK_OVERLAP)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", ", ", " "],
    )

    all_chunks: List[Dict[str, Any]] = []
    for sec in sections:
        text = sec.get("text", "") or ""
        sec_type = (sec.get("type") or "text").lower()
        if sec_type == "table" or "salary" in text.lower():
            # keep atomic
            all_chunks.append({**sec, "chunk_idx": 0, "chunk_text": text})
            continue
        tokens = count_tokens(text)
        if tokens <= chunk_size:
            all_chunks.append({**sec, "chunk_idx": 0, "chunk_text": text})
        else:
            parts = splitter.split_text(text)
            for idx, chunk in enumerate(parts):
                all_chunks.append({**sec, "chunk_idx": idx, "chunk_text": chunk})
    return all_chunks


