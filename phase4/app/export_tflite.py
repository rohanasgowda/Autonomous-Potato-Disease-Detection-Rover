from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import numpy as np

from phase4.app.config import load_config
from phase4.app.logging import configure_logging

LOGGER = logging.getLogger(__name__)


def _import_tf():
    try:
        import tensorflow as tf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("TensorFlow is required for TFLite export.") from exc
    return tf


def model_size_bytes(path: str | Path) -> int:
    return os.path.getsize(path)


def representative_dataset_generator(tf, dataset_dir: Path, image_size: tuple[int, int], sample_count: int):
    train_dir = dataset_dir / "train"
    if not train_dir.exists():
        return None
    dataset = tf.keras.utils.image_dataset_from_directory(
        train_dir,
        labels=None,
        image_size=image_size,
        batch_size=1,
        shuffle=True,
    ).take(sample_count)

    def generator():
        for image in dataset:
            yield [tf.cast(image, tf.float32)]

    return generator


def convert_to_tflite(
    *,
    model_path: str | Path,
    output_path: str | Path,
    quantization: str,
    dataset_dir: str | Path,
    image_size: tuple[int, int],
    representative_samples: int,
) -> Path:
    tf = _import_tf()
    model = tf.keras.models.load_model(model_path)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    if quantization == "float16":
        converter.target_spec.supported_types = [tf.float16]
    elif quantization == "int8":
        generator = representative_dataset_generator(tf, Path(dataset_dir), image_size, representative_samples)
        if generator is None:
            raise FileNotFoundError("Int8 quantization requires a dataset/train directory for calibration.")
        converter.representative_dataset = generator
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.uint8
        converter.inference_output_type = tf.uint8
    elif quantization != "dynamic_range":
        raise ValueError("quantization must be dynamic_range, float16, or int8")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(converter.convert())
    return output


def validate_tflite_model(model_path: str | Path) -> dict[str, object]:
    tf = _import_tf()
    interpreter = tf.lite.Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_shape = input_details[0]["shape"]
    dtype = input_details[0]["dtype"]
    sample = np.zeros(input_shape, dtype=dtype)
    interpreter.set_tensor(input_details[0]["index"], sample)
    interpreter.invoke()
    output = interpreter.get_tensor(output_details[0]["index"])
    return {
        "input_shape": [int(item) for item in input_shape],
        "input_dtype": str(dtype),
        "output_shape": [int(item) for item in output.shape],
        "output_dtype": str(output.dtype),
        "size_bytes": model_size_bytes(model_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a trained Keras model to TensorFlow Lite.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--config", default=None)
    parser.add_argument("--dataset-dir", default=None)
    parser.add_argument("--quantization", default=None, choices=["dynamic_range", "float16", "int8"])
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    config = load_config(
        args.config,
        overrides={"dataset_dir": args.dataset_dir, "quantization": args.quantization},
    )
    output = convert_to_tflite(
        model_path=args.model,
        output_path=args.output,
        quantization=config.quantization,
        dataset_dir=config.dataset_dir,
        image_size=config.image_size_hw,
        representative_samples=config.representative_samples,
    )
    validation = validate_tflite_model(output)
    LOGGER.info("TFLite export complete", extra={"_model_path": str(output), "_validation": validation})


if __name__ == "__main__":
    main()

