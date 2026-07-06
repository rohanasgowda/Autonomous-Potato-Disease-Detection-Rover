from __future__ import annotations

from pathlib import Path

import numpy as np

import phase4.app.inference as inference_module
from phase4.app.inference import PredictionResult, build_detection_payload
from phase4.app.labels import save_labels


class FakeInterpreter:
    def allocate_tensors(self) -> None:
        pass

    def get_input_details(self):
        return [{"index": 0, "dtype": np.float32, "shape": np.array([1, 2, 2, 3])}]

    def get_output_details(self):
        return [{"index": 0, "dtype": np.float32}]

    def set_tensor(self, index, value) -> None:
        self.input_index = index
        self.input_value = value

    def invoke(self) -> None:
        pass

    def get_tensor(self, index):
        return np.array([[0.1, 0.9]], dtype=np.float32)


def test_detection_payload_preserves_required_schema(tiny_dataset: Path) -> None:
    image_path = tiny_dataset / "test" / "potato_late_blight" / "test_potato_late_blight.png"
    prediction = PredictionResult(
        class_name="potato_late_blight",
        crop="potato",
        disease="late_blight",
        confidence=0.91,
        inference_time_ms=12.5,
    )

    payload = build_detection_payload(
        prediction=prediction,
        image_path=image_path,
        model_name="plant_disease_mobilenetv3",
        model_version="0.1.0",
        device_id="rpi_rover_01",
        row_index=1,
        plant_index=7,
        session_id="sess_test",
    )

    assert payload["session_id"] == "sess_test"
    assert payload["crop"] == "potato"
    assert payload["disease"] == "late_blight"
    assert payload["grid_position"] == {"row_index": 1, "plant_index": 7}
    assert payload["model"]["runtime"] == "tflite"
    assert payload["severity"]["label"] in {"healthy", "very_low", "low", "moderate", "high", "severe"}


def test_run_tflite_prediction_parses_top_class(monkeypatch, tmp_path) -> None:
    labels = save_labels(["potato_healthy", "potato_late_blight"], tmp_path / "labels.json")
    monkeypatch.setattr(inference_module, "_load_interpreter", lambda model_path: FakeInterpreter())
    monkeypatch.setattr(
        inference_module,
        "preprocess_image_file",
        lambda image_path, image_size, normalize=False: np.zeros((2, 2, 3), dtype=np.float32),
    )

    prediction = inference_module.run_tflite_prediction(
        model_path=tmp_path / "model.tflite",
        image_path=tmp_path / "image.png",
        labels_path=labels,
        image_size=(2, 2),
    )

    assert prediction.class_name == "potato_late_blight"
    assert prediction.crop == "potato"
    assert prediction.disease == "late_blight"
    assert prediction.confidence == 0.9
