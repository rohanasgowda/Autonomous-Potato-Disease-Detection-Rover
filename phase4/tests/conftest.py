from __future__ import annotations

import base64
from pathlib import Path

import pytest


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.fixture()
def tiny_dataset(tmp_path: Path) -> Path:
    for split in ("train", "val", "test"):
        for class_name in ("potato_healthy", "potato_late_blight"):
            class_dir = tmp_path / "dataset" / split / class_name
            class_dir.mkdir(parents=True, exist_ok=True)
            (class_dir / f"{split}_{class_name}.png").write_bytes(PNG_1X1)
    (tmp_path / "dataset" / "train" / "potato_healthy" / "corrupt.jpg").write_bytes(b"not an image")
    return tmp_path / "dataset"

