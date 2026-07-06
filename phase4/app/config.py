from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Phase4Config:
    seed: int = 42
    dataset_dir: str = "dataset"
    output_dir: str = "phase4/runs/default"
    image_size: tuple[int, int] = (224, 224)
    batch_size: int = 16
    epochs: int = 20
    initial_epoch: int = 0
    learning_rate: float = 3e-4
    fine_tune_learning_rate: float = 3e-5
    fine_tune_at: int | None = None
    backbone: str = "mobilenetv3small"
    dropout: float = 0.2
    weights: str | None = "imagenet"
    model_name: str = "plant_disease_mobilenetv3"
    model_version: str = "0.1.0"
    quantization: str = "dynamic_range"
    representative_samples: int = 100
    device_id: str = "rpi_rover_01"
    max_local_sessions: int = 20

    @property
    def image_size_hw(self) -> tuple[int, int]:
        return (int(self.image_size[0]), int(self.image_size[1]))


def _coerce_value(name: str, value: Any) -> Any:
    if name == "image_size":
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("image_size must be a two-item list such as [224, 224]")
        return (int(value[0]), int(value[1]))
    if name == "weights" and value in ("none", "None", ""):
        return None
    return value


def load_config(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> Phase4Config:
    config_path = Path(path) if path else Path(__file__).resolve().parents[1] / "configs" / "default.json"
    payload: dict[str, Any] = {}
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    elif path:
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if overrides:
        payload.update({key: value for key, value in overrides.items() if value is not None})

    valid_names = {field.name for field in fields(Phase4Config)}
    unknown = sorted(set(payload) - valid_names)
    if unknown:
        raise ValueError(f"Unknown config keys: {', '.join(unknown)}")

    coerced = {key: _coerce_value(key, value) for key, value in payload.items()}
    return Phase4Config(**coerced)


def save_resolved_config(config: Phase4Config, output_dir: str | Path) -> Path:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    path = target / "resolved_config.json"
    payload = config.__dict__.copy()
    payload["image_size"] = list(config.image_size_hw)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return path

