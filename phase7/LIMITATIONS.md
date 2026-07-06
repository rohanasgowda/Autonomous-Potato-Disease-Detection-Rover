# Limitations, Assumptions, and Known Constraints

This document lists real, documented limitations and assumptions present in the repository and its phase documentation. It does not propose or describe future work as missing functionality.

## Current Limitations
- Public-dataset bias: Phase 4 training uses PlantVillage images and the documentation explicitly warns that lab-style images may not generalize to field images captured by the rover.
- Severity estimator: Phase 5 implements a lightweight OpenCV-based method with manual validation tooling; the repository does not claim pixel-level segmentation accuracy or clinical/agronomic certification.
- Inventory matching: Backend inventory checks use exact normalized-name matching (lowercase + trim). No fuzzy/synonym matching is implemented in the repository.
- Telegram and OpenRouter: These integrations rely on external services and require API credentials; delivery and agent behavior depend on those services.
- Hardware integration: The grid movement controller is an abstraction; physical motor drivers are not provided by default (no-op controller included).

## Assumptions
- Model artifacts (TFLite, labels) are supplied to the runtime environment and are not committed to the repository.
- Prototype security: seeded default credentials exist for local demos; not production-ready.
- The system is a demonstrator and is explicitly not a certified agronomic advisory product.

## Known Constraints
- Performance numbers (inference time) are illustrative and were measured on the development environment; per-device benchmarking on target Raspberry Pi hardware is required before reporting production performance.
- The repository intentionally excludes heavy segmentation models and complex motor drivers to keep the prototype lightweight and maintainable.
