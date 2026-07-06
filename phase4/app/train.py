from __future__ import annotations

import argparse
import logging
import random
from pathlib import Path

import numpy as np

from phase4.app.config import load_config, save_resolved_config
from phase4.app.labels import save_labels
from phase4.app.logging import configure_logging
from phase4.app.models import build_classifier

LOGGER = logging.getLogger(__name__)


def _import_tf():
    try:
        import tensorflow as tf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("TensorFlow is required for training. Install phase4/requirements.txt.") from exc
    return tf


def set_reproducible_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    tf = _import_tf()
    tf.keras.utils.set_random_seed(seed)


def load_split_dataset(tf, dataset_dir: Path, split: str, image_size: tuple[int, int], batch_size: int, shuffle: bool):
    split_dir = dataset_dir / split
    if not split_dir.exists():
        return None
    return tf.keras.utils.image_dataset_from_directory(
        split_dir,
        labels="inferred",
        label_mode="int",
        image_size=image_size,
        batch_size=batch_size,
        shuffle=shuffle,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the Phase 4 crop-disease classifier.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--dataset-dir", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--backbone", default=None)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--resume", default=None, help="Optional checkpoint/model path to resume from.")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    config = load_config(
        args.config,
        overrides={
            "dataset_dir": args.dataset_dir,
            "output_dir": args.output_dir,
            "backbone": args.backbone,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
        },
    )
    set_reproducible_seed(config.seed)
    tf = _import_tf()

    output_dir = Path(config.output_dir)
    checkpoints_dir = output_dir / "checkpoints"
    tensorboard_dir = output_dir / "tensorboard"
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    save_resolved_config(config, output_dir)

    dataset_dir = Path(config.dataset_dir)
    train_ds = load_split_dataset(tf, dataset_dir, "train", config.image_size_hw, config.batch_size, True)
    if train_ds is None:
        raise FileNotFoundError(f"Training split not found: {dataset_dir / 'train'}")
    val_ds = load_split_dataset(tf, dataset_dir, "val", config.image_size_hw, config.batch_size, False)
    test_ds = load_split_dataset(tf, dataset_dir, "test", config.image_size_hw, config.batch_size, False)

    class_names = list(train_ds.class_names)
    save_labels(class_names, output_dir / "labels.json")
    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(autotune)
    if val_ds is not None:
        val_ds = val_ds.prefetch(autotune)
    if test_ds is not None:
        test_ds = test_ds.prefetch(autotune)

    if args.resume:
        model = tf.keras.models.load_model(args.resume)
        LOGGER.info("Resumed model", extra={"_resume_path": args.resume})
    else:
        build = build_classifier(
            num_classes=len(class_names),
            image_size=config.image_size_hw,
            backbone_name=config.backbone,
            dropout=config.dropout,
            learning_rate=config.learning_rate,
            weights=config.weights,
            fine_tune_at=config.fine_tune_at,
        )
        model = build.model

    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(checkpoints_dir / "best.keras"),
            monitor="val_accuracy" if val_ds is not None else "accuracy",
            save_best_only=True,
        ),
        tf.keras.callbacks.TensorBoard(log_dir=str(tensorboard_dir)),
        tf.keras.callbacks.CSVLogger(str(output_dir / "training_history.csv"), append=bool(args.resume)),
    ]
    history = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=config.epochs,
        initial_epoch=config.initial_epoch,
        callbacks=callbacks,
    )
    final_model_path = output_dir / "saved_model.keras"
    model.save(final_model_path)
    if test_ds is not None:
        metrics = model.evaluate(test_ds, return_dict=True)
        LOGGER.info("Test evaluation complete", extra={"_metrics": metrics})
    LOGGER.info(
        "Training complete",
        extra={"_model_path": str(final_model_path), "_history_keys": list(history.history.keys())},
    )


if __name__ == "__main__":
    main()

