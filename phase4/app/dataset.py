from __future__ import annotations

import argparse
import csv
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

from phase4.app.labels import split_crop_disease
from phase4.app.logging import configure_logging

LOGGER = logging.getLogger(__name__)
VALID_SPLITS = ("train", "val", "test")
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass(frozen=True)
class ImageRecord:
    split: str
    class_name: str
    path: str
    sha256: str
    is_duplicate: bool


@dataclass(frozen=True)
class DatasetReport:
    dataset_dir: str
    total_images: int
    valid_images: int
    corrupt_images: int
    duplicate_images: int
    class_counts: dict[str, dict[str, int]]
    corrupt_paths: list[str]


def _looks_like_image(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            header = handle.read(16)
    except OSError:
        return False
    return (
        header.startswith(b"\xff\xd8\xff")
        or header.startswith(b"\x89PNG\r\n\x1a\n")
        or header.startswith(b"BM")
        or header.startswith(b"RIFF")
    )


def _is_readable_image(path: Path) -> bool:
    if not _looks_like_image(path):
        return False
    try:
        import cv2  # type: ignore
        import numpy as np
    except ImportError:
        return True
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) is not None


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_dataset(dataset_dir: str | Path) -> tuple[list[ImageRecord], DatasetReport]:
    root = Path(dataset_dir)
    if not root.exists():
        raise FileNotFoundError(f"Dataset directory not found: {root}")

    records: list[ImageRecord] = []
    corrupt_paths: list[str] = []
    seen_hashes: set[str] = set()
    class_counts: dict[str, dict[str, int]] = {split: {} for split in VALID_SPLITS}
    total_images = 0
    duplicate_images = 0

    for split in VALID_SPLITS:
        split_dir = root / split
        if not split_dir.exists():
            LOGGER.warning("Dataset split missing", extra={"_split": split, "_path": str(split_dir)})
            continue
        for class_dir in sorted(path for path in split_dir.iterdir() if path.is_dir()):
            split_crop_disease(class_dir.name)
            class_counts[split].setdefault(class_dir.name, 0)
            for image_path in sorted(class_dir.rglob("*")):
                if not image_path.is_file() or image_path.suffix.lower() not in VALID_EXTENSIONS:
                    continue
                total_images += 1
                if not _is_readable_image(image_path):
                    corrupt_paths.append(str(image_path))
                    LOGGER.warning("Corrupted image skipped", extra={"_path": str(image_path)})
                    continue
                digest = file_sha256(image_path)
                is_duplicate = digest in seen_hashes
                if is_duplicate:
                    duplicate_images += 1
                seen_hashes.add(digest)
                class_counts[split][class_dir.name] += 1
                records.append(
                    ImageRecord(
                        split=split,
                        class_name=class_dir.name,
                        path=str(image_path),
                        sha256=digest,
                        is_duplicate=is_duplicate,
                    )
                )

    report = DatasetReport(
        dataset_dir=str(root),
        total_images=total_images,
        valid_images=len(records),
        corrupt_images=len(corrupt_paths),
        duplicate_images=duplicate_images,
        class_counts=class_counts,
        corrupt_paths=corrupt_paths,
    )
    return records, report


def write_manifest(records: list[ImageRecord], output_path: str | Path) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["split", "class_name", "path", "sha256", "is_duplicate"],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)
    return target


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Phase 4 dataset structure and image readability.")
    parser.add_argument("--dataset-dir", default="dataset")
    parser.add_argument("--manifest", default="phase4/runs/dataset_manifest.csv")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    records, report = scan_dataset(args.dataset_dir)
    manifest = write_manifest(records, args.manifest)
    LOGGER.info(
        "Dataset scan complete",
        extra={
            "_dataset_dir": report.dataset_dir,
            "_valid_images": report.valid_images,
            "_corrupt_images": report.corrupt_images,
            "_duplicate_images": report.duplicate_images,
            "_manifest": str(manifest),
        },
    )


if __name__ == "__main__":
    main()

