# Phase 5 Severity Estimation Documentation

## System Overview

Phase 5 estimates plant disease severity after the existing Phase 4 disease classifier has produced a crop/disease prediction. Classification answers what disease is visible. Severity estimation answers how much of the detected leaf area appears infected.

The implementation is a Raspberry Pi compatible OpenCV prototype. It does not retrain the MobileNetV3 classifier, replace the TFLite inference pipeline, or add a heavy segmentation model. Its output keeps the existing Detection JSON severity fields:

```json
{
  "severity": {
    "label": "moderate",
    "infected_area_percent": 14.6,
    "method": "leaf_area_segmentation_v1"
  }
}
```

## Architecture Flow

```text
Image
  -> Leaf Segmentation
  -> Disease Segmentation
  -> Severity Calculation
  -> Severity Label
  -> Detection JSON
```

1. Leaf segmentation loads the image and builds a binary mask for likely leaf pixels.
2. Disease segmentation builds a lesion/discoloration mask and restricts it to the leaf mask.
3. Severity calculation counts diseased pixels and total leaf pixels.
4. Severity label mapping converts the percentage into the exact requirements scale.
5. Detection JSON integration reuses `phase4.app.inference.build_detection_payload`.

## Modules

### `phase4/app/severity.py`

Purpose: Phase 5 severity estimation core.

Inputs:

- BGR image arrays from OpenCV
- image paths
- optional JSON threshold configuration

Outputs:

- `SegmentationResult`: mask plus pixel count
- `SeverityResult`: label, infected area percent, method, leaf pixel count, diseased pixel count
- `SeverityAnalysis`: result plus leaf and diseased masks for validation

Processing logic:

- Convert BGR image to HSV.
- Build configurable HSV masks.
- Clean masks with morphology.
- Remove small contours.
- Count nonzero mask pixels.
- Calculate percent and label.

Dependencies:

- `opencv-python-headless`
- `numpy`

### `phase4/app/validate_severity.py`

Purpose: Small validation workflow for manually checked sample images.

Inputs:

- `--image`
- optional `--config`
- optional `--output-dir`

Outputs:

- `severity_summary.json`
- `leaf_mask.png`
- `diseased_mask.png`
- `segmentation_overlay.png`

## Leaf Segmentation

Leaf segmentation uses HSV thresholding because hue/saturation/value ranges are easier to explain and tune than raw RGB values under changing brightness. The default mask includes green tissue and brown/yellow lesion tones so infected regions remain part of the total leaf area.

Processing steps:

1. Convert image from BGR to HSV.
2. Apply configured leaf HSV ranges.
3. Apply morphological open/close operations to reduce noise and fill small gaps.
4. Extract contours and remove very small regions.
5. Count leaf pixels with `cv2.countNonZero`.

OpenCV was chosen because it is lightweight, fast enough for Raspberry Pi 4, explainable for a college prototype, and already listed as the recommended severity helper in the requirements.

## Disease Segmentation

Disease segmentation searches inside the leaf mask for visible lesion colors. The default configuration targets brown/yellow discoloration and very dark necrotic regions. The diseased mask is always intersected with the leaf mask so background pixels are not counted as infected leaf area.

Assumptions:

- The camera captures a visible leaf surface.
- Lighting is reasonably controlled.
- Lesions are visually separable by color from healthy tissue.
- This is not a validated medical or agronomic severity model.

No lesion dataset, pixel-level benchmark, or measured segmentation accuracy is claimed.

## Severity Calculation

The requirements formula is implemented directly:

```text
severity_percent = diseased_leaf_pixels / total_leaf_pixels * 100
```

Input validation:

- negative pixel counts raise `ValueError`
- diseased pixels greater than total leaf pixels raise `ValueError`
- zero leaf pixels return `0.0` to avoid divide-by-zero

Worked examples:

```text
diseased = 18,500
leaf = 125,000
severity_percent = 18,500 / 125,000 * 100 = 14.8
label = moderate
```

```text
diseased = 0
leaf = 125,000
severity_percent = 0
label = healthy
```

## Severity Labels

The implementation uses the exact requirements mapping:

| Label | Range |
|---|---:|
| healthy | 0% |
| very_low | >0% to 1% |
| low | >1% to 5% |
| moderate | >5% to 20% |
| high | >20% to 40% |
| severe | >40% |

## Detection JSON Integration

`phase4/app/inference.py` still calls `estimate_severity_opencv(image_path)`. That function is now the compatibility entry point for the Phase 5 pipeline and returns:

```json
{
  "label": "moderate",
  "infected_area_percent": 14.6,
  "method": "leaf_area_segmentation_v1"
}
```

The Detection JSON field names are unchanged.

## Validation Guide

Run validation on a manually selected image:

```powershell
python -m phase4.app.validate_severity --image captures/sample.JPG --output-dir phase4/runs/severity_validation
```

Review:

- `leaf_mask.png`: white pixels should match visible leaf area.
- `diseased_mask.png`: white pixels should match visible lesion/discoloration regions.
- `segmentation_overlay.png`: green overlay marks leaf area; red overlay marks disease area.
- `severity_summary.json`: contains pixel counts, percent, label, and method.

Threshold tuning:

1. Copy the default values from `SeverityConfig` in `phase4/app/severity.py`.
2. Create a small JSON config containing only changed fields.
3. Rerun validation with `--config`.
4. Compare masks against manual visual inspection.

Example config:

```json
{
  "leaf_hsv_ranges": [
    [[25, 35, 35], [95, 255, 255]],
    [[5, 30, 20], [35, 255, 235]]
  ],
  "disease_hsv_ranges": [
    [[5, 30, 20], [35, 255, 235]],
    [[0, 0, 0], [180, 255, 75]]
  ],
  "min_leaf_contour_area": 100,
  "min_disease_contour_area": 10
}
```

## Setup Guide

Install dependencies in the project environment:

```powershell
pip install -r phase4/requirements.txt
```

Run tests:

```powershell
python -m pytest phase4/tests/test_severity.py -q
```

Run the full existing inference pipeline with severity:

```powershell
python -m phase4.app.inference --model phase4/runs/mobilenetv3/model.tflite --labels phase4/runs/mobilenetv3/labels.json --image captures/sample.JPG --row-index 1 --plant-index 7
```

Configuration options are available through `SeverityConfig`:

- `leaf_hsv_ranges`
- `disease_hsv_ranges`
- morphology iteration counts
- contour area minimums
- kernel size

## Raspberry Pi Deployment Guide

Runtime requirements:

- Raspberry Pi 4
- Python environment with `numpy` and `opencv-python-headless`
- existing Phase 4 TFLite model and labels
- captured image from Pi Camera or stored file

Deployment process:

1. Copy the Phase 4 project folder to the Pi.
2. Install `phase4/requirements.txt`, using `tflite-runtime` for inference if TensorFlow is not installed.
3. Keep `model.tflite` and `labels.json` from Phase 4.
4. Run `phase4.app.inference` after each image capture.
5. Store or transmit the generated Detection JSON.

Performance expectations:

- The method is CPU-only and uses simple thresholding, morphology, and contour filtering.
- It should be lightweight compared with the CNN classifier.
- Exact timing must be measured on the target Pi before reporting performance numbers.

Optimization considerations:

- Resize very large camera images before segmentation if needed.
- Keep validation thresholds crop/camera specific.
- Use controlled lighting to reduce HSV threshold drift.

## Token-Efficient Development Strategy

This phase intentionally uses OpenCV segmentation and modular Python functions instead of U-Net, DeepLab, Mask R-CNN, SAM, or transformer segmentation systems.

Reasons:

- The requirements call for a prototype severity helper.
- Raspberry Pi compatibility matters more than segmentation research complexity.
- No pixel-level lesion masks are available in the project.
- The existing classifier and inference JSON should be reused, not rebuilt.
- Small functions are easier to test, tune, and document.

## Future Enhancements

Possible future work:

- Lite U-Net or MobileNet-backed segmentation if pixel masks are collected.
- DeepLab-style segmentation for stronger boundaries.
- Disease-specific lesion thresholds.
- Hybrid severity using classifier confidence and disease type.
- Field-specific calibration profiles for camera, crop, and lighting.

These are future enhancements only and are not part of Phase 5.
