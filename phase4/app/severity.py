from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

LOGGER = logging.getLogger(__name__)
SEVERITY_METHOD = "leaf_area_segmentation_v1"

HsvRange = tuple[tuple[int, int, int], tuple[int, int, int]]


@dataclass(frozen=True)
class SeverityConfig:
    leaf_hsv_ranges: tuple[HsvRange, ...] = (
        ((25, 35, 35), (95, 255, 255)),
        ((5, 30, 20), (35, 255, 235)),
    )
    disease_hsv_ranges: tuple[HsvRange, ...] = (
        ((5, 30, 20), (35, 255, 235)),
        ((0, 0, 0), (180, 255, 75)),
    )
    kernel_size: int = 3
    leaf_open_iterations: int = 1
    leaf_close_iterations: int = 2
    disease_open_iterations: int = 1
    disease_close_iterations: int = 1
    min_leaf_contour_area: int = 100
    min_disease_contour_area: int = 10


@dataclass(frozen=True)
class SegmentationResult:
    mask: np.ndarray = field(repr=False)
    pixel_count: int


@dataclass(frozen=True)
class SeverityResult:
    label: str
    infected_area_percent: float
    method: str
    leaf_pixel_count: int = 0
    diseased_pixel_count: int = 0


@dataclass(frozen=True)
class SeverityAnalysis:
    result: SeverityResult
    leaf_mask: np.ndarray = field(repr=False)
    diseased_mask: np.ndarray = field(repr=False)


def _import_cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for severity estimation. Install opencv-python-headless.") from exc
    return cv2


def _coerce_hsv_ranges(raw_ranges: Any) -> tuple[HsvRange, ...]:
    ranges: list[HsvRange] = []
    for raw_range in raw_ranges:
        if len(raw_range) != 2:
            raise ValueError("Each HSV range must contain lower and upper bounds.")
        lower = tuple(int(value) for value in raw_range[0])
        upper = tuple(int(value) for value in raw_range[1])
        if len(lower) != 3 or len(upper) != 3:
            raise ValueError("HSV bounds must contain three values.")
        ranges.append((lower, upper))
    return tuple(ranges)


def load_severity_config(path: str | Path | None = None) -> SeverityConfig:
    if path is None:
        return SeverityConfig()

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = set(SeverityConfig.__dataclass_fields__)
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"Unknown severity config keys: {', '.join(unknown)}")

    if "leaf_hsv_ranges" in payload:
        payload["leaf_hsv_ranges"] = _coerce_hsv_ranges(payload["leaf_hsv_ranges"])
    if "disease_hsv_ranges" in payload:
        payload["disease_hsv_ranges"] = _coerce_hsv_ranges(payload["disease_hsv_ranges"])
    return SeverityConfig(**payload)


def _validate_image(image_bgr: np.ndarray) -> None:
    if not isinstance(image_bgr, np.ndarray):
        raise TypeError("image_bgr must be a numpy array.")
    if image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError(f"Expected BGR image with shape HxWx3, got {image_bgr.shape}.")


def _validate_mask(mask: np.ndarray, image_shape: tuple[int, int]) -> None:
    if not isinstance(mask, np.ndarray):
        raise TypeError("mask must be a numpy array.")
    if mask.shape[:2] != image_shape:
        raise ValueError(f"Mask shape {mask.shape[:2]} does not match image shape {image_shape}.")


def _kernel(config: SeverityConfig) -> np.ndarray:
    cv2 = _import_cv2()
    size = max(1, int(config.kernel_size))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))


def _mask_from_hsv_ranges(hsv_image: np.ndarray, ranges: tuple[HsvRange, ...]) -> np.ndarray:
    cv2 = _import_cv2()
    mask = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
    for lower, upper in ranges:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv_image, np.array(lower), np.array(upper)))
    return mask


def _clean_mask(mask: np.ndarray, *, open_iterations: int, close_iterations: int, config: SeverityConfig) -> np.ndarray:
    cv2 = _import_cv2()
    cleaned = mask.copy()
    kernel = _kernel(config)
    if open_iterations > 0:
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=int(open_iterations))
    if close_iterations > 0:
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=int(close_iterations))
    return cleaned


def _filter_small_contours(mask: np.ndarray, min_area: int) -> np.ndarray:
    cv2 = _import_cv2()
    if min_area <= 0:
        return mask

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filtered = np.zeros_like(mask)
    for contour in contours:
        if cv2.contourArea(contour) >= min_area:
            cv2.drawContours(filtered, [contour], contourIdx=-1, color=255, thickness=cv2.FILLED)
    return filtered


def segment_leaf(image_bgr: np.ndarray, config: SeverityConfig | None = None) -> SegmentationResult:
    """Segment visible plant/leaf pixels from the image background."""
    cv2 = _import_cv2()
    config = config or SeverityConfig()
    _validate_image(image_bgr)

    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    leaf_mask = _mask_from_hsv_ranges(hsv, config.leaf_hsv_ranges)
    leaf_mask = _clean_mask(
        leaf_mask,
        open_iterations=config.leaf_open_iterations,
        close_iterations=config.leaf_close_iterations,
        config=config,
    )
    leaf_mask = _filter_small_contours(leaf_mask, config.min_leaf_contour_area)
    pixel_count = int(cv2.countNonZero(leaf_mask))
    LOGGER.debug("Leaf segmentation complete", extra={"_leaf_pixel_count": pixel_count})
    return SegmentationResult(mask=leaf_mask, pixel_count=pixel_count)


def segment_diseased_region(
    image_bgr: np.ndarray,
    leaf_mask: np.ndarray,
    config: SeverityConfig | None = None,
) -> SegmentationResult:
    """Segment likely diseased pixels inside the already segmented leaf area."""
    cv2 = _import_cv2()
    config = config or SeverityConfig()
    _validate_image(image_bgr)
    _validate_mask(leaf_mask, image_bgr.shape[:2])

    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    disease_mask = _mask_from_hsv_ranges(hsv, config.disease_hsv_ranges)
    disease_mask = cv2.bitwise_and(disease_mask, leaf_mask)
    disease_mask = _clean_mask(
        disease_mask,
        open_iterations=config.disease_open_iterations,
        close_iterations=config.disease_close_iterations,
        config=config,
    )
    disease_mask = _filter_small_contours(disease_mask, config.min_disease_contour_area)
    disease_mask = cv2.bitwise_and(disease_mask, leaf_mask)
    pixel_count = int(cv2.countNonZero(disease_mask))
    LOGGER.debug("Disease segmentation complete", extra={"_diseased_pixel_count": pixel_count})
    return SegmentationResult(mask=disease_mask, pixel_count=pixel_count)


def calculate_severity_percent(diseased_leaf_pixels: int, total_leaf_pixels: int) -> float:
    if diseased_leaf_pixels < 0 or total_leaf_pixels < 0:
        raise ValueError("Pixel counts must be non-negative.")
    if total_leaf_pixels == 0:
        return 0.0
    if diseased_leaf_pixels > total_leaf_pixels:
        raise ValueError("Diseased pixels cannot exceed total leaf pixels.")
    return round((diseased_leaf_pixels / total_leaf_pixels) * 100.0, 2)


def severity_label_from_percent(percent: float) -> str:
    if percent < 0:
        raise ValueError("Severity percent must be non-negative.")
    if percent > 100:
        raise ValueError("Severity percent cannot exceed 100.")
    if percent <= 0:
        return "healthy"
    if percent <= 1:
        return "very_low"
    if percent <= 5:
        return "low"
    if percent <= 20:
        return "moderate"
    if percent <= 40:
        return "high"
    return "severe"


def analyze_severity_image(image_path: str | Path, config: SeverityConfig | None = None) -> SeverityAnalysis:
    cv2 = _import_cv2()
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {image_path}")

    leaf = segment_leaf(image, config)
    diseased = segment_diseased_region(image, leaf.mask, config)
    percent = calculate_severity_percent(diseased.pixel_count, leaf.pixel_count)
    result = SeverityResult(
        label=severity_label_from_percent(percent),
        infected_area_percent=percent,
        method=SEVERITY_METHOD,
        leaf_pixel_count=leaf.pixel_count,
        diseased_pixel_count=diseased.pixel_count,
    )
    LOGGER.info(
        "Severity estimation complete",
        extra={
            "_leaf_pixel_count": result.leaf_pixel_count,
            "_diseased_pixel_count": result.diseased_pixel_count,
            "_infected_area_percent": result.infected_area_percent,
            "_severity_label": result.label,
        },
    )
    return SeverityAnalysis(result=result, leaf_mask=leaf.mask, diseased_mask=diseased.mask)


def estimate_severity_opencv(image_path: str | Path) -> SeverityResult:
    """Backward-compatible Phase 4 inference entry point for Phase 5 severity."""
    try:
        return analyze_severity_image(image_path).result
    except RuntimeError:
        LOGGER.warning("Severity skipped because OpenCV is unavailable", exc_info=True)
        return SeverityResult("healthy", 0.0, f"{SEVERITY_METHOD}_opencv_unavailable")
    except ValueError:
        LOGGER.warning("Severity skipped because the image could not be analyzed", exc_info=True)
        return SeverityResult("healthy", 0.0, f"{SEVERITY_METHOD}_not_estimated")
