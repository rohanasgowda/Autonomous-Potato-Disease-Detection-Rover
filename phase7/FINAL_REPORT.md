# Final Report — Plant Disease Detection Rover

1. Introduction

This final report consolidates the implemented system across Phases 1–6 and presents the documentation, validation notes, limitations and next steps for submission.

2. Problem Statement

Farmers need lightweight, low-cost tools to detect foliar disease early and get actionable recommendations. This project prototypes an edge-capable rover that captures plant images, runs an offline classifier, estimates severity, generates structured treatment recommendations, checks local vendor inventory and notifies farmers.

3. Objectives

- Implement a demonstrator pipeline that integrates capture, offline inference, severity estimation, treatment recommendation, inventory check and notification.
- Keep components modular so ML, backend, and agent parts can evolve independently.

4. Requirements Analysis

Requirements and JSON schemas are documented in `docs/plant_disease_rover_requirements.md` and implemented across phase modules. The prototype scope excludes automatic spraying, order placement, multi-vendor selection, and GPS navigation.

5. System Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for diagrams and component interactions.

6. Phase-wise Implementation

- Phase 2: FastAPI backend with detection, recommendation, inventory, and dashboard APIs.
- Phase 3: OpenRouter-based treatment agent client, strict JSON schema enforcement, Telegram notification helper, vendor frontend for inventory management.
- Phase 4: Dataset preparation, MobileNetV3 transfer-learning training, evaluation, and TFLite export for Raspberry Pi inference.
- Phase 5: OpenCV-based severity estimation with manual validation utilities.
- Phase 6: Edge orchestration, camera capture, grid movement abstraction, session persistence, backend sync, and notification flow.

7. Disease Classification Results

Phase 4 reports a MobileNetV3-based classifier exported as `model.tflite`. The documented test accuracy is 97.37% on the test split reported in Phase 4 documentation. Exported TFLite model dimensions and example inference outputs are documented in `phase4/docs/`.

8. Severity Estimation Results

Phase 5 implements HSV-based leaf/disease segmentation and a severity percent calculation. Validation tooling is included for visual inspection (`phase4.app.validate_severity`). No pixel-accuracy benchmark is claimed in repository materials.

9. Phase 6 Validation Results

Phase 6 documentation shows the end-to-end workflow is implemented with session persistence and backend integration. The repository includes a Phase 6 validation checklist and example runs; numeric E2E benchmarks on target hardware are not part of the repository.

10. Challenges Faced

- Public dataset bias vs field imagery.
- Class imbalance in the initial potato healthy set (addressed with augmentation).
- Ensuring structured LLM outputs required strict prompt and schema enforcement.

11. Limitations

See [LIMITATIONS.md](LIMITATIONS.md) for the repository-authored limitations, assumptions and constraints.

12. Future Scope

See [FUTURE_SCOPE.md](FUTURE_SCOPE.md) for suggested enhancements.

13. Conclusion

The repository contains a completed prototype and supporting documentation suitable for academic evaluation. This Phase 7 package consolidates existing phase documentation, clarifies installation and deployment steps, and provides a submission-ready final report and validation summary.
