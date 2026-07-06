# Architecture Overview

This document ties the phase-level implementations into a single architecture view and explains component responsibilities and interactions.

## High-level flow (Rover workflow)

Grid Movement → Image Capture → Disease Detection → Severity Estimation → Treatment Generation → Backend Sync → Inventory Check → Telegram Notification

## Components

- Phase 6 (Edge Orchestration)
  - `phase6/controller.py` — workflow coordinator.
  - `phase6/grid.py` — grid movement abstraction (no-op default provided).
  - `phase6/camera.py` — capture helper (Picamera2/OpenCV fallback).
  - `phase6/storage.py` — SQLite-backed `LocalSessionStore`.

- Phase 4 (ML and Severity)
  - `phase4/app/inference.py` — TFLite runtime inference and detection JSON builder.
  - `phase4/app/severity.py` — OpenCV-based severity estimator (Phase 5 integration point).
  - `phase4/runs/...` — training/export artifacts (not committed by default).

- Phase 3 (Treatment Agent & Notifications)
  - `phase3/app/clients/openrouter.py` — OpenRouter client and structured output parsing.
  - `phase3/app/notifications/telegram.py` — Telegram formatter and sender.
  - `phase3/frontend/` — vendor inventory helper UI (static files).

- Phase 2 (Backend)
  - `backend/app` — FastAPI server, detection and recommendation storage, inventory APIs.

## Backend Architecture

- API surface: `/auth/login`, `/detections`, `/recommendations`, `/inventory`, `/inventory/check`, `/dashboard/summary`, `/notifications/telegram` (scaffold).
- Persistence: SQLite via SQLAlchemy, flattened detection fields + raw JSON for traceability.
- Auth: JWT-based, seeded prototype users.

## AI Agent Architecture

- OpenRouter integration: structured JSON output enforced by Pydantic schemas and prompt `response_format`.
- Treatment workflow: detection JSON → `TreatmentAgentInput` → OpenRouter → validated `TreatmentAgentOutput` → backend upload → inventory check → Telegram.

## Disease Classification Architecture

- MobileNetV3 transfer-learning trained in Phase 4.
- Exported to TensorFlow Lite for Raspberry Pi edge inference; input size 224×224, output shape `[1,3]` for the potato model.

## Severity Estimation Architecture

- Phase 5 uses HSV-based leaf segmentation and color-based lesion detection implemented in `phase4/app/severity.py`.
- Severity percent = diseased_leaf_pixels / total_leaf_pixels * 100.
- Label mapping follows documented bins: `healthy, very_low, low, moderate, high, severe`.

## Rover Workflow Sequence (mermaid)

```mermaid
flowchart LR
  A[Grid Movement] --> B[Capture Image]
  B --> C[Phase4 TFLite Inference]
  C --> D[Severity Estimation]
  D --> E[Treatment Agent (OpenRouter)]
  E --> F[Backend Sync (FastAPI)]
  F --> G[Inventory Check]
  G --> H[Telegram Notification]
  H --> I[Session Persistence (SQLite)]
```

## Integration Notes
- The repository keeps ML artifacts out of source control. Exported `.tflite` and `labels.json` are expected to be placed under `phase4/runs/<run>/` prior to inference.
- The grid controller is intentionally abstracted so physical motor integration can be added without changing workflow logic.
