from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def sample_detection_payload() -> dict:
    return json.loads(
        Path("phase3/examples/detection_sample.json").read_text(encoding="utf-8")
    )


@pytest.fixture()
def sample_treatment_output() -> dict:
    return json.loads(
        Path("phase3/examples/treatment_output_sample.json").read_text(encoding="utf-8")
    )

