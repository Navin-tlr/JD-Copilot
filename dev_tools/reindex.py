from __future__ import annotations

from pathlib import Path
import shutil

from app.config import get_settings


def main() -> None:
    cfg = get_settings()
    chroma_dir = Path(cfg.CHROMA_DIR)
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir)
    chroma_dir.mkdir(parents=True, exist_ok=True)
    print(f"Cleared Chroma at {chroma_dir}")


if __name__ == "__main__":
    main()


