from __future__ import annotations

import json
from pathlib import Path


def split_crop_disease(class_name: str) -> tuple[str, str]:
    parts = class_name.strip().lower().split("_", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            "Class names must follow '<crop>_<disease_or_healthy>', "
            f"got {class_name!r}"
        )
    return parts[0], parts[1]


def load_labels(path: str | Path) -> list[str]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "classes" in payload:
        classes = payload["classes"]
    else:
        classes = payload
    if not isinstance(classes, list) or not all(isinstance(item, str) for item in classes):
        raise ValueError("Label file must contain a JSON list or {'classes': [...]}")
    for class_name in classes:
        split_crop_disease(class_name)
    return classes


def save_labels(classes: list[str], path: str | Path) -> Path:
    for class_name in classes:
        split_crop_disease(class_name)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps({"classes": classes}, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    return target

