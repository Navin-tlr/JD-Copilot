from __future__ import annotations

import os
from pathlib import Path

from fastapi.testclient import TestClient


def test_query_and_resume(tmp_path: Path):
    # Configure temp chroma
    os.environ["CHROMA_DIR"] = str(tmp_path / "chroma")
    os.environ["DOCLING_JSON_DIR"] = str(tmp_path / "docling_json")
    os.environ["LANGEXT_JSON_DIR"] = str(tmp_path / "langext_json")
    os.environ["LANGEXT_HTML_DIR"] = str(tmp_path / "langext_html")

    # Ingest a couple of sample JDs
    import ingest.ingest_docling as ing

    jd_dir = tmp_path / "jds"
    jd_dir.mkdir(parents=True, exist_ok=True)
    repo_samples = Path("dev_tools/sample_jd_texts")
    for p in repo_samples.glob("*.txt"):
        (jd_dir / p.name).write_text(p.read_text())
    for p in sorted(jd_dir.glob("*.txt")):
        ing.process_file(p)

    # Start app client
    from app.main import app

    client = TestClient(app)

    # Query endpoint
    resp = client.post(
        "/query",
        json={"question": "What is the CTC?", "filters": {"company": None, "year": None}, "top_k": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "snippets" in data and isinstance(data["snippets"], list)

    # Resume match endpoint
    resp2 = client.post(
        "/query/resume_match",
        json={"resume_text": "Python, SQL, ML projects with FastAPI", "top_k": 2},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "matches" in data2 and isinstance(data2["matches"], list)
    if data2["matches"]:
        m0 = data2["matches"][0]
        assert "missing_skills" in m0


