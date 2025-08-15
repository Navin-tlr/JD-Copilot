from __future__ import annotations

import os
from pathlib import Path


def main() -> None:
    # Avoid hf_transfer dependency for portability
    os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")
    try:
        import certifi  # type: ignore

        ca_path = certifi.where()
        os.environ.setdefault("SSL_CERT_FILE", ca_path)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_path)
    except Exception:
        pass

    # Fetch the full repo snapshot to ensure all LFS artifacts are present
    from huggingface_hub import snapshot_download
    path = snapshot_download("ds4sd/docling-models")
    base = Path(path)
    # Ensure expected path exists; if not, try to locate and mirror
    expected_dir = base / "model_artifacts" / "layout" / "beehive_v0.0.5"
    expected_file = expected_dir / "model.pt"
    if not expected_file.exists():
        # Fallback 1: search elsewhere in snapshot
        candidates = list(base.glob("**/beehive_v0.0.5/**/model.*")) + list(base.glob("**/beehive*/**/model.*"))
        if candidates:
            expected_dir.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(candidates[0], expected_file)
            print(f"Mirrored beehive model to {expected_file}")
        else:
            # Fallback 2: direct HTTP download from HF
            import requests
            expected_dir.mkdir(parents=True, exist_ok=True)
            url = "https://huggingface.co/ds4sd/docling-models/resolve/main/model_artifacts/layout/beehive_v0.0.5/model.pt"
            print(f"Downloading beehive model from {url} ...")
            with requests.get(url, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(expected_file, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
            if not expected_file.exists() or expected_file.stat().st_size == 0:
                raise RuntimeError("Direct download of beehive model failed or empty file.")
            print(f"Downloaded beehive model to {expected_file}")
    print(f"Prefetched Docling models at: {base}")


if __name__ == "__main__":
    main()


