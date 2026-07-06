from __future__ import annotations

import json

import pytest

from phase4.app.config import load_config
from phase4.app.labels import load_labels, save_labels, split_crop_disease


def test_split_crop_disease() -> None:
    assert split_crop_disease("potato_late_blight") == ("potato", "late_blight")
    with pytest.raises(ValueError):
        split_crop_disease("lateblight")


def test_label_round_trip(tmp_path) -> None:
    path = save_labels(["potato_healthy", "potato_late_blight"], tmp_path / "labels.json")
    assert load_labels(path) == ["potato_healthy", "potato_late_blight"]


def test_load_config_with_overrides(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"image_size": [160, 160], "batch_size": 4}), encoding="utf-8")
    config = load_config(path, overrides={"epochs": 3})
    assert config.image_size_hw == (160, 160)
    assert config.batch_size == 4
    assert config.epochs == 3

