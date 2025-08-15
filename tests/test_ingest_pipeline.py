from __future__ import annotations

import os
from pathlib import Path

import chromadb


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
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    col = client.get_collection("jds")
    res = col.get()
    ids_first = set(res.get("ids", []))
    assert len(ids_first) >= 1

    # Re-run same ingest and ensure idempotency (IDs unchanged)
    for p in sorted(jd_dir.glob("*.txt")):
        n = ing.process_file(p)
        assert n >= 1
    res2 = col.get()
    ids_second = set(res2.get("ids", []))
    assert ids_first == ids_second


