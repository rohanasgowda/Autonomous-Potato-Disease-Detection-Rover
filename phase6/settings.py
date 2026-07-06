from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from phase3.app.config.settings import Settings as Phase3Settings
from phase4.app.config import Phase4Config, load_config


@dataclass(frozen=True)
class Phase6Settings:
    phase3: Phase3Settings
    phase4: Phase4Config
    model_path: Path
    labels_path: Path
    capture_dir: Path
    local_db_path: Path
    farm_size_acres: float
    number_of_plants: int
    country: str
    language: str
    row_index: int
    plant_index: int
    camera_index: int
    camera_warmup_seconds: float

    @classmethod
    def from_env(
        cls,
        env_file: str | Path | None = None,
        phase4_config_path: str | Path | None = None,
    ) -> "Phase6Settings":
        phase3 = Phase3Settings.from_env(env_file)
        phase4 = load_config(phase4_config_path)
        default_model_dir = Path("phase4") / "runs" / "mobilenetv3"
        return cls(
            phase3=phase3,
            phase4=phase4,
            model_path=Path(os.getenv("PHASE6_MODEL_PATH", default_model_dir / "model.tflite")),
            labels_path=Path(os.getenv("PHASE6_LABELS_PATH", default_model_dir / "labels.json")),
            capture_dir=Path(os.getenv("PHASE6_CAPTURE_DIR", "captures")),
            local_db_path=Path(os.getenv("PHASE6_LOCAL_DB_PATH", "logs/phase6_sessions.db")),
            farm_size_acres=float(os.getenv("FARM_SIZE_ACRES", "1.0")),
            number_of_plants=int(os.getenv("NUMBER_OF_PLANTS", "500")),
            country=os.getenv("COUNTRY", "India"),
            language=os.getenv("LANGUAGE", "English"),
            row_index=int(os.getenv("ROW_INDEX", "0")),
            plant_index=int(os.getenv("PLANT_INDEX", "0")),
            camera_index=int(os.getenv("CAMERA_INDEX", "0")),
            camera_warmup_seconds=float(os.getenv("CAMERA_WARMUP_SECONDS", "0.2")),
        )

