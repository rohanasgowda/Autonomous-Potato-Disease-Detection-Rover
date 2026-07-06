# Validation Results

This document consolidates validation findings present in the repository. It uses only metrics and validation statements documented in phase artifacts.

## Phase 4 Validation (Disease Classification)
- Model: MobileNetV3 transfer-learning
- Dataset: PlantVillage potato classes; final dataset size reported as 3,101 images across `potato_healthy`, `potato_early_blight`, and `potato_late_blight`.
- Reported test accuracy: 97.37% (see `phase4/docs/PHASE4_IMPLEMENTATION_REPORT.md`).
- Reported test loss: 0.057.
- TFLite export: `model.tflite` exported and validated; reported model size ~1.1 MB and input shape `[1,224,224,3]`.
- Example validated inference: `potato_late_blight`, confidence `0.999964`, inference time ~11.943 ms (documented example output).

## Phase 5 Validation (Severity Estimation)
- Implementation: OpenCV HSV-based leaf segmentation and disease color masking in `phase4/app/severity.py`.
- Validation method: manual visual validation workflow provided (`phase4.app.validate_severity`) which produces `leaf_mask.png`, `diseased_mask.png`, `segmentation_overlay.png`, and `severity_summary.json` for inspection.
- No pixel-level segmentation accuracy metrics or dataset-backed segmentation benchmark is claimed in repository documentation.

## Phase 6 Validation (End-to-end)
- Phase 6 documentation includes a validation checklist and claims feature coverage for: grid movement abstraction, camera capture, inference, treatment generation, backend sync, inventory check, Telegram notification, and SQLite session persistence.
- The repository provides integration points, examples, and scripts to exercise end-to-end flows; concrete numeric E2E benchmarks (latency, throughput on Pi hardware) are not included.

## Tests
- Each phase includes unit and integration tests under `phase*/tests` and `backend/tests`. Run `pytest` in the relevant folders to execute the provided test suites.

## Notes and constraints
- All numerical validation figures in this file are taken directly from Phase 4 and project documentation in the repository. No additional experimental numbers were generated or assumed.
