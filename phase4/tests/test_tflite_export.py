from __future__ import annotations

import numpy as np

import phase4.app.export_tflite as export_module
from phase4.app.export_tflite import model_size_bytes


class FakeInterpreter:
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path

    def allocate_tensors(self) -> None:
        pass

    def get_input_details(self):
        return [{"index": 0, "shape": np.array([1, 2, 2, 3]), "dtype": np.float32}]

    def get_output_details(self):
        return [{"index": 1}]

    def set_tensor(self, index, value) -> None:
        self.input_index = index
        self.input_value = value

    def invoke(self) -> None:
        pass

    def get_tensor(self, index):
        return np.zeros((1, 2), dtype=np.float32)


class FakeLite:
    Interpreter = FakeInterpreter


class FakeTensorFlow:
    lite = FakeLite()


def test_model_size_bytes(tmp_path) -> None:
    path = tmp_path / "model.tflite"
    path.write_bytes(b"tflite")
    assert model_size_bytes(path) == 6


def test_validate_tflite_model_reports_io_metadata(monkeypatch, tmp_path) -> None:
    path = tmp_path / "model.tflite"
    path.write_bytes(b"tflite")
    monkeypatch.setattr(export_module, "_import_tf", lambda: FakeTensorFlow())

    report = export_module.validate_tflite_model(path)

    assert report["input_shape"] == [1, 2, 2, 3]
    assert report["output_shape"] == [1, 2]
    assert report["size_bytes"] == 6
