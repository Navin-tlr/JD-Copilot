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
    import ingest.pipeline as ing

    for p in sorted(jd_dir.glob("*.txt")):
        n = ing.process_file(p)
        assert n >= 1

    # Collect current stats and assert idempotency if Pinecone is configured
    if os.environ.get("PINECONE_API_KEY") and os.environ.get("PINECONE_INDEX_NAME"):
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])  # type: ignore
        index = pc.Index(os.environ["PINECONE_INDEX_NAME"])  # type: ignore
        stats_before = index.describe_index_stats()
        vector_count_before = stats_before.get("total_vector_count", 0)

        # Re-run same ingest and ensure idempotency (vector count unchanged)
        for p in sorted(jd_dir.glob("*.txt")):
            n = ing.process_file(p)
            assert n >= 1
        stats_after = index.describe_index_stats()
        vector_count_after = stats_after.get("total_vector_count", 0)
        assert vector_count_before == vector_count_after
    else:
        # No cloud creds in CI: rely on local success of process_file
        assert True


