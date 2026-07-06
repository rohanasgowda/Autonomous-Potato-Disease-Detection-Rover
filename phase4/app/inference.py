from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import numpy as np

from phase4.app.config import load_config
from phase4.app.labels import load_labels, split_crop_disease
from phase4.app.logging import configure_logging
from phase4.app.preprocessing import add_batch_dimension, preprocess_image_file, read_image_dimensions
from phase4.app.severity import estimate_severity_opencv

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PredictionResult:
    class_name: str
    crop: str
    disease: str
    confidence: float
    inference_time_ms: float


def _load_interpreter(model_path: str | Path):
    try:
        from tflite_runtime.interpreter import Interpreter  # type: ignore
    except ImportError:
        try:
            import tensorflow as tf  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Install tflite-runtime on Raspberry Pi or TensorFlow on the training machine.") from exc
        Interpreter = tf.lite.Interpreter
    interpreter = Interpreter(model_path=str(model_path))
    interpreter.allocate_tensors()
    return interpreter


def run_tflite_prediction(model_path: str | Path, image_path: str | Path, labels_path: str | Path, image_size: tuple[int, int]) -> PredictionResult:
    labels = load_labels(labels_path)
    interpreter = _load_interpreter(model_path)
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    image = preprocess_image_file(image_path, image_size, normalize=False)
    input_dtype = input_details[0]["dtype"]
    if input_dtype == np.uint8:
        scale, zero_point = input_details[0].get("quantization", (0.0, 0))
        if scale and scale > 0:
            image = image / scale + zero_point
        image = np.clip(image, 0, 255).astype(np.uint8)
    else:
        image = image.astype(input_dtype)
    input_tensor = add_batch_dimension(image)

    start = time.perf_counter()
    interpreter.set_tensor(input_details[0]["index"], input_tensor)
    interpreter.invoke()
    inference_time_ms = (time.perf_counter() - start) * 1000.0
    output = interpreter.get_tensor(output_details[0]["index"])[0]
    if output_details[0]["dtype"] == np.uint8:
        scale, zero_point = output_details[0].get("quantization", (0.0, 0))
        if scale and scale > 0:
            output = (output.astype(np.float32) - zero_point) * scale
    index = int(np.argmax(output))
    class_name = labels[index]
    crop, disease = split_crop_disease(class_name)
    return PredictionResult(
        class_name=class_name,
        crop=crop,
        disease=disease,
        confidence=round(float(output[index]), 6),
        inference_time_ms=round(inference_time_ms, 3),
    )


def build_detection_payload(
    *,
    prediction: PredictionResult,
    image_path: str | Path,
    model_name: str,
    model_version: str,
    device_id: str,
    row_index: int,
    plant_index: int,
    session_id: str | None = None,
) -> dict[str, object]:
    width, height = read_image_dimensions(image_path)
    severity = estimate_severity_opencv(image_path)
    return {
        "session_id": session_id or f"sess_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}",
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "grid_position": {"row_index": row_index, "plant_index": plant_index},
        "crop": prediction.crop,
        "disease": prediction.disease,
        "confidence": prediction.confidence,
        "severity": {
            "label": severity.label,
            "infected_area_percent": severity.infected_area_percent,
            "method": severity.method,
        },
        "image": {
            "local_path": str(image_path),
            "width": width,
            "height": height,
        },
        "model": {
            "name": model_name,
            "version": model_version,
            "runtime": "tflite",
        },
        "runtime": {
            "inference_time_ms": prediction.inference_time_ms,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Raspberry Pi compatible TFLite disease inference.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--config", default=None)
    parser.add_argument("--row-index", type=int, default=0)
    parser.add_argument("--plant-index", type=int, default=0)
    parser.add_argument("--output", default=None)
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    config = load_config(args.config)
    prediction = run_tflite_prediction(args.model, args.image, args.labels, config.image_size_hw)
    payload = build_detection_payload(
        prediction=prediction,
        image_path=args.image,
        model_name=config.model_name,
        model_version=config.model_version,
        device_id=config.device_id,
        row_index=args.row_index,
        plant_index=args.plant_index,
    )
    output_json = json.dumps(payload, indent=2, ensure_ascii=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output_json, encoding="utf-8")
    else:
        print(output_json)
    LOGGER.info("Inference complete", extra={"_prediction": prediction.__dict__})


if __name__ == "__main__":
    main()
