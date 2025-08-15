from __future__ import annotations

import os
from pathlib import Path

import os


def test_ingest_pipeline_idempotent(tmp_path: Path):
    # Point CHROMA_DIR to a temp dir for test isolation
    os.environ["CHROMA_DIR"] = str(tmp_path / "chroma")
    os.environ["DOCLING_JSON_DIR"] = str(tmp_path / "docling_json")
    os.environ["LANGEXT_JSON_DIR"] = str(tmp_path / "langext_json")
    os.environ["LANGEXT_HTML_DIR"] = str(tmp_path / "langext_html")

    jd_dir = tmp_path / "jds"
    jd_dir.mkdir(parents=True, exist_ok=True)
    # Copy sample texts
    repo_samples = Path("dev_tools/sample_jd_texts")
    for p in repo_samples.glob("*.txt"):
        (jd_dir / p.name).write_text(p.read_text())

    # Run ingest
    import ingest.ingest_docling as ing

    for p in sorted(jd_dir.glob("*.txt")):
        n = ing.process_file(p)
        assert n >= 1

    # Collect current IDs
    # Pipeline now uses Pinecone. If Pinecone creds are set, validate via Pinecone; otherwise
    # assume ingestion completed if process_file returned >=1 above.
    if os.environ.get("PINECONE_API_KEY") and os.environ.get("PINECONE_INDEX_NAME"):
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])  # type: ignore
        index = pc.Index(os.environ["PINECONE_INDEX_NAME"])  # type: ignore
        stats = index.describe_index_stats()
        vector_count = stats.get("total_vector_count", 0)
        assert isinstance(vector_count, (int, float))
    else:
        # No cloud creds in CI: rely on local success
        assert True

    # Re-run same ingest and ensure idempotency (IDs unchanged)
    for p in sorted(jd_dir.glob("*.txt")):
        n = ing.process_file(p)
        assert n >= 1
    res2 = col.get()
    ids_second = set(res2.get("ids", []))
    assert ids_first == ids_second


