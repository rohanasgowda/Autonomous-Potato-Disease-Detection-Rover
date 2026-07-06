from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from phase4.app.severity import (
    SeverityConfig,
    calculate_severity_percent,
    estimate_severity_opencv,
    segment_diseased_region,
    segment_leaf,
    severity_label_from_percent,
)


def test_severity_scale_matches_requirements_document() -> None:
    assert severity_label_from_percent(0) == "healthy"
    assert severity_label_from_percent(0.5) == "very_low"
    assert severity_label_from_percent(3) == "low"
    assert severity_label_from_percent(12) == "moderate"
    assert severity_label_from_percent(30) == "high"
    assert severity_label_from_percent(55) == "severe"


def test_severity_label_boundaries_are_exact() -> None:
    assert severity_label_from_percent(1.0) == "very_low"
    assert severity_label_from_percent(1.01) == "low"
    assert severity_label_from_percent(5.0) == "low"
    assert severity_label_from_percent(5.01) == "moderate"
    assert severity_label_from_percent(20.0) == "moderate"
    assert severity_label_from_percent(20.01) == "high"
    assert severity_label_from_percent(40.0) == "high"
    assert severity_label_from_percent(40.01) == "severe"


def test_calculate_severity_percent_validates_pixel_counts() -> None:
    assert calculate_severity_percent(0, 0) == 0.0
    assert calculate_severity_percent(25, 100) == 25.0

    with pytest.raises(ValueError):
        calculate_severity_percent(-1, 100)
    with pytest.raises(ValueError):
        calculate_severity_percent(101, 100)
    with pytest.raises(ValueError):
        severity_label_from_percent(100.01)


def _synthetic_leaf_image() -> np.ndarray:
    cv2 = pytest.importorskip("cv2")
    hsv = np.zeros((40, 40, 3), dtype=np.uint8)
    hsv[10:30, 10:30] = (60, 200, 200)
    hsv[15:25, 15:25] = (20, 200, 180)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def test_segmentation_outputs_are_bounded() -> None:
    image = _synthetic_leaf_image()
    config = SeverityConfig(min_leaf_contour_area=0, min_disease_contour_area=0)

    leaf = segment_leaf(image, config)
    diseased = segment_diseased_region(image, leaf.mask, config)

    assert leaf.pixel_count > 0
    assert diseased.pixel_count > 0
    assert diseased.pixel_count <= leaf.pixel_count


def test_estimate_severity_opencv_returns_detection_json_fields(tmp_path: Path) -> None:
    cv2 = pytest.importorskip("cv2")
    image_path = tmp_path / "leaf.png"
    cv2.imwrite(str(image_path), _synthetic_leaf_image())

    result = estimate_severity_opencv(image_path)

    assert result.method == "leaf_area_segmentation_v1"
    assert result.label in {"healthy", "very_low", "low", "moderate", "high", "severe"}
    assert 0 <= result.infected_area_percent <= 100
    assert result.leaf_pixel_count > 0
    assert result.diseased_pixel_count <= result.leaf_pixel_count
