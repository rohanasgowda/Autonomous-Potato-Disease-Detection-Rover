from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path

import numpy as np

from phase4.app.config import load_config
from phase4.app.labels import save_labels
from phase4.app.logging import configure_logging

LOGGER = logging.getLogger(__name__)


def _import_tf():
    try:
        import tensorflow as tf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("TensorFlow is required for Keras model evaluation.") from exc
    return tf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained Phase 4 Keras model.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--dataset-dir", default=None)
    parser.add_argument("--split", default="test", choices=["val", "test"])
    parser.add_argument("--config", default=None)
    parser.add_argument("--output-dir", default="phase4/runs/evaluation")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    config = load_config(args.config, overrides={"dataset_dir": args.dataset_dir})
    tf = _import_tf()
    from sklearn.metrics import classification_report, confusion_matrix  # type: ignore

    split_dir = Path(config.dataset_dir) / args.split
    if not split_dir.exists():
        raise FileNotFoundError(f"Evaluation split not found: {split_dir}")
    dataset = tf.keras.utils.image_dataset_from_directory(
        split_dir,
        labels="inferred",
        label_mode="int",
        image_size=config.image_size_hw,
        batch_size=config.batch_size,
        shuffle=False,
    )
    class_names = list(dataset.class_names)
    model = tf.keras.models.load_model(args.model)

    y_true: list[int] = []
    y_pred: list[int] = []
    inference_times_ms: list[float] = []
    for images, labels in dataset:
        start = time.perf_counter()
        probabilities = model.predict(images, verbose=0)
        inference_times_ms.append((time.perf_counter() - start) * 1000.0 / max(1, int(images.shape[0])))
        y_true.extend([int(item) for item in labels.numpy().tolist()])
        y_pred.extend([int(item) for item in np.argmax(probabilities, axis=1).tolist()])

    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True, zero_division=0)
    matrix = confusion_matrix(y_true, y_pred).tolist()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    save_labels(class_names, output_dir / "labels.json")
    payload = {
        "split": args.split,
        "classes": class_names,
        "classification_report": report,
        "confusion_matrix": matrix,
        "mean_inference_ms_per_image": float(np.mean(inference_times_ms)) if inference_times_ms else None,
    }
    (output_dir / "evaluation_report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    LOGGER.info("Evaluation report written", extra={"_output_dir": str(output_dir)})


if __name__ == "__main__":
    main()

