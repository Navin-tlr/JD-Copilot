from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    path = Path("data/alerts.json")
    if not path.exists():
        print("[]")
        return
    try:
        print(json.dumps(json.loads(path.read_text()), indent=2))
    except Exception:
        print("[]")


if __name__ == "__main__":
    main()


