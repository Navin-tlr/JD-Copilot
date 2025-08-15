from __future__ import annotations

from pathlib import Path
import shutil

from app.config import get_settings


def main() -> None:
    cfg = get_settings()
    # Previously cleared local Chroma DB. Switch to Pinecone (cloud-first); no local reindex step.
    print("Reindex tool is deprecated: this project now uses Pinecone (cloud-first). Use Pinecone console or API to manage indexes.")


if __name__ == "__main__":
    main()


