# Phase 6 Overview

## Purpose

Phase 6 is the Raspberry Pi integration workflow for the plant disease detection pipeline. It orchestrates image capture, optional grid movement, disease classification, treatment generation, backend synchronization, inventory checking, Telegram notification, and local session persistence.

This module integrates the Phase 3 backend and notification components with Phase 4 inference and configuration components to deliver a deployment-ready Phase 6 experience.

## What Phase 6 provides

- A workflow controller for end-to-end Phase 6 execution.
- Hardware-agnostic grid movement support through `phase6/grid.py`.
- Camera capture from a live camera or a prerecorded source image.
- Disease classification using Phase 4 TFLite inference.
- Treatment generation via the Phase 3 OpenRouter agent client.
- Backend sync for detection, recommendation, and inventory.
- Telegram farmer notification for final results.
- Local SQLite session storage for audit and recovery.

## Core modules

- `phase6/controller.py` — orchestrates the scan workflow and integrates all subsystems.
- `phase6/camera.py` — captures images from Picamera2/OpenCV or copies a source image.
- `phase6/storage.py` — implements `LocalSessionStore` backed by SQLite.
- `phase6/grid.py` — defines the `GridMovementController` abstraction and a no-op default.
- `phase6/settings.py` — loads environment variables and Phase 3/Phase 4 configuration.
- `phase6/main.py` — CLI entrypoint to run Phase 6.

## Architecture diagram

```text
  +--------------------------+
  | phase6/main.py           |
  +-----------+--------------+
              |
              v
  +--------------------------+
  | phase6/controller.py     |
  +--------------------------+
  |  - grid movement         |
  |  - camera capture        |
  |  - inference             |
  |  - treatment generation  |
  |  - backend sync          |
  |  - telegram              |
  |  - session storage       |
  +-----+---------+----------+
        |         |
        v         v
  +-------------+  +----------------+
  | phase6/grid |  | phase6/camera  |
  +-------------+  +----------------+
        |                |
        v                v
  hardware         image file / camera

  +---------------------------------------------+
  | phase6/storage.py                            |
  +---------------------------------------------+

  +---------------------------------------------+
  | phase4.app.inference                         |
  +---------------------------------------------+

  +---------------------------------------------+
  | phase3.app.clients.openrouter                |
  +---------------------------------------------+

  +---------------------------------------------+
  | phase3.app.integrations.backend              |
  +---------------------------------------------+

  +---------------------------------------------+
  | phase3.app.notifications.telegram            |
  +---------------------------------------------+
```

## Inputs and outputs

### Inputs

- `row_index`, `plant_index` — target grid coordinates for the scan.
- `source_image` — optional image file path to bypass live camera capture.
- Phase 6 settings from environment variables or CLI arguments.
- Phase 4 model path, labels path, and config.
- Phase 3 backend, OpenRouter, and Telegram settings.

### Outputs

- A `WorkflowResult` object containing:
  - `session_id`
  - `image_path`
  - `detection_json`
  - `treatment_json`
  - backend sync details
  - Telegram delivery result
  - workflow `sync_status`
  - any recorded errors
- Persistent session rows in the SQLite store.

## Dependencies

Phase 6 depends on repository-local Phase 3 and Phase 4 packages, including:

- `phase3.app.clients.openrouter.OpenRouterClient`
- `phase3.app.integrations.backend.BackendClient`
- `phase3.app.notifications.telegram.TelegramClient`
- `phase4.app.inference.run_tflite_prediction`
- `phase4.app.inference.build_detection_payload`
- `phase4.app.config.Phase4Config`

The implementation is hardware-agnostic and does not require motor drivers unless a concrete `GridMovementController` is provided.

