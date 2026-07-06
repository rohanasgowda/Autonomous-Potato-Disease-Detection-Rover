# Plant Disease Detection Rover - Project Progress

Date updated: 2026-06-01

## Project Roadmap Status

| Phase | Scope | Status | Notes |
|---|---|---|---|
| Phase 1 | Requirements and architecture | Completed | Requirements, architecture, dataset direction, and JSON schemas documented. |
| Phase 2 | Backend prototype | Completed | Backend prototype and supporting validation workflows completed for project integration. |
| Phase 3 | Treatment agent and inventory workflow | Completed | Treatment-agent and inventory workflow completed separately from ML inference. |
| Phase 4 | ML model training | Completed | MobileNetV3 model trained and exported to TensorFlow Lite for Raspberry Pi edge inference. |
| Phase 5 | Severity estimation | Completed | OpenCV leaf/disease segmentation prototype, severity percentage calculation, label mapping, validation workflow, and documentation completed. |

## Phase 4 ML Workstream Completion Summary

| Workstream Phase | Scope | Status |
|---|---|---|
| Phase 1 | Dataset collection and preparation | Completed |
| Phase 2 | Dataset validation and processing pipeline | Completed |
| Phase 3 | Disease classification training pipeline | Completed |
| Phase 4 | Model training, model evaluation, TFLite export, and real-time inference validation | Completed |

## Phase 4 Final Results

| Category | Result |
|---|---|
| Dataset source | PlantVillage |
| Model | MobileNetV3 transfer learning |
| Framework | TensorFlow 2.17.1 |
| Input size | 224 x 224 x 3 |
| Classes | `potato_healthy`, `potato_early_blight`, `potato_late_blight` |
| Final dataset size | 3101 images |
| Test accuracy | 97.37% |
| Test loss | 0.057 |
| Export format | TensorFlow Lite (`model.tflite`) |
| Model size | 1,110,664 bytes, approximately 1.1 MB |
| TFLite input shape | `[1, 224, 224, 3]` |
| TFLite output shape | `[1, 3]` |
| Validated inference | `potato_late_blight`, confidence `0.999964`, inference time `11.943 ms` |

## Dataset Progress

The original PlantVillage potato dataset had a significant imbalance between healthy and late blight images:

| Class | Original Images |
|---|---:|
| Potato Healthy | 152 |
| Potato Late Blight | 1001 |

Healthy potato leaf images were augmented using horizontal flip, rotation from -15 degrees to +15 degrees, brightness adjustment, and contrast adjustment.

Final Phase 4 dataset:

| Class | Images |
|---|---:|
| Potato Healthy | 1200 |
| Potato Early Blight | 1000 |
| Potato Late Blight | 1001 |
| Total | 3101 |

## Model Improvement

| Model Run | Dataset Size | Classes | Test Accuracy | Test Loss |
|---|---:|---:|---:|---:|
| Initial model | 302 | 2 | 88.00% | Not recorded |
| Improved MobileNetV3 model | 3101 | 3 | 97.37% | 0.057 |

The improved model expanded disease coverage from two classes to three classes and improved test accuracy by 9.37 percentage points.

## Deployment Readiness

Phase 4 is ready for Raspberry Pi integration because:

- TensorFlow Lite export succeeded.
- The exported model is small enough for edge deployment at approximately 1.1 MB.
- The inference pipeline is functional.
- Prediction confidence exceeded 99.99% on the validated sample.
- Inference time was approximately 12 ms for the validated inference path.
- The pipeline supports offline operation.

## Phase 5 Severity Estimation Completion Summary

Phase 5 adds a lightweight OpenCV severity pipeline after disease classification. It segments likely leaf pixels, segments visible diseased regions within the leaf mask, calculates infected leaf area percentage, maps the percentage to the documented severity scale, and preserves Detection JSON compatibility through the existing inference payload builder.

Documentation: `docs/PHASE5_SEVERITY_ESTIMATION.md`

Validation status:

- Focused severity tests pass locally.
- Segmentation masks can be reviewed with `phase4.app.validate_severity`.
- No segmentation accuracy or field-performance metrics have been claimed because manual validation data has not been formally measured.
