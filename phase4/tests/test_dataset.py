from __future__ import annotations

from pathlib import Path

from phase4.app.dataset import scan_dataset, write_manifest


def test_scan_dataset_counts_valid_corrupt_and_duplicates(tiny_dataset: Path, tmp_path: Path) -> None:
    records, report = scan_dataset(tiny_dataset)

    assert report.valid_images == 6
    assert report.corrupt_images == 1
    assert report.duplicate_images == 5
    assert report.class_counts["train"]["potato_healthy"] == 1

    manifest = write_manifest(records, tmp_path / "manifest.csv")
    assert manifest.exists()
    assert "is_duplicate" in manifest.read_text(encoding="utf-8")

