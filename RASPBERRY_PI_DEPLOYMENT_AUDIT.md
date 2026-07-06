# Raspberry Pi Rover Deployment Audit Report

**Date:** June 2, 2026  
**Status:** Analysis Only — No Code Modifications  
**Objective:** Complete understanding of runtime execution, deployment architecture, and motor controller integration points

---

## Executive Summary

The repository contains a complete Phase 1–6 implementation for a plant disease detection rover. The system is architecturally divided into:

- **Phase 2 (Backend):** FastAPI server running on laptop/local network; NOT required on Pi.
- **Phase 3 (Agent):** OpenRouter client and Telegram notification handler; runs on Pi but requires internet (OPTIONAL for local-only testing).
- **Phase 4 (ML):** TensorFlow Lite inference and OpenCV severity estimation; runs on Pi.
- **Phase 6 (Orchestration):** Grid movement controller, camera capture, session persistence, backend sync, and workflow orchestration; primary Pi runtime.

**Grid movement controller is currently a no-op (placeholder). Motor controller integration requires:**
- New file: `phase6/motor_controller.py` implementing concrete `GridMovementController`
- Modify: `phase6/controller.py` line 83 to accept injected motor controller
- Modify: `phase6/main.py` to instantiate and pass motor controller

**Critical files for Pi deployment:**
- `phase6/main.py` (entry point)
- `phase6/controller.py` (workflow orchestrator)
- `phase4/runs/mobilenetv3/model.tflite` + `labels.json` (pre-exported artifacts)
- `phase3/.env` (API credentials)

---

## 1. Runtime Entry Point Analysis

### Phase 6 CLI Entry Point

**File:** `phase6/main.py`  
**Function:** `main()` (line 27–49)  
**Arguments parsed:**
```python
--env-file (default: ".env")
--phase4-config (optional, default: None)
--source-image (optional, for testing)
--farm-size-acres (float)
--number-of-plants (int)
--row-index, --plant-index (grid coordinates)
--country, --language (location context)
--skip-backend (boolean flag)
--skip-telegram (boolean flag)
```

### Execution Sequence

```
phase6/main.py:main()
  └─ Phase6Settings.from_env() [line 36]
       ├─ Phase3Settings.from_env(.env) [phase3/app/config/settings.py:56]
       ├─ Phase4Config.load_config() [phase4/app/config.py:73]
  
  └─ Phase6WorkflowController.from_settings() [line 39]
       ├─ build_pipeline(phase3_settings) [phase3/app/main.py:14]
       │   ├─ OpenRouterClient(...)
       │   ├─ BackendClient(...)
       │   ├─ TelegramClient(...)
       │   └─ AuditStore(...)
       ├─ CameraCapture(...)
       ├─ LocalSessionStore(...)
  
  └─ controller.run_scan() [line 47]
       ├─ grid_controller.move_to_grid_position(row, plant) [line 117]
       ├─ grid_controller.stop() [line 118]
       ├─ camera.capture() [line 125]
       ├─ run_tflite_prediction() [line 131] → phase4/app/inference.py:47
       ├─ build_detection_payload() [line 134] → phase4/app/inference.py:71
       ├─ openrouter_client.generate_treatment() [line 150]
       ├─ backend_client.upload_detection() [line 159]
       ├─ backend_client.upload_recommendation() [line 162]
       ├─ backend_client.check_inventory() [line 171]
       ├─ telegram_client.send_message() [line 180]
       └─ store.update_session() [multiple lines]
```

### Call Graph: Image Capture

```
camera.capture(session_id, source_image)
  ├─ if source_image:
  │   └─ _copy_source_image() [phase6/camera.py:59]
  │       └─ shutil.copy2() to captures/
  │
  └─ else:
      └─ _capture_camera_image() [phase6/camera.py:68]
         ├─ try: _capture_with_picamera2() [phase6/camera.py:77]
         │   ├─ from picamera2 import Picamera2
         │   ├─ camera.start()
         │   ├─ time.sleep(warmup_seconds)
         │   └─ camera.capture_file(target)
         │
         └─ except:
             └─ _capture_with_opencv() [phase6/camera.py:90]
                 ├─ import cv2
                 ├─ camera = cv2.VideoCapture(camera_index)
                 ├─ camera.read()
                 └─ cv2.imwrite(target, frame)
```

### Call Graph: Disease Detection

```
run_tflite_prediction(model_path, image_path, labels_path, image_size)
  [phase4/app/inference.py:47–74]
  
  ├─ load_labels(labels_path) [phase4/app/labels.py:X]
  ├─ _load_interpreter(model_path) [phase4/app/inference.py:20]
  │   ├─ try: from tflite_runtime.interpreter import Interpreter
  │   └─ except: from tensorflow import tf; Interpreter = tf.lite.Interpreter
  │
  ├─ preprocess_image_file(image_path, image_size, normalize=False)
  │   [phase4/app/preprocessing.py:X]
  │   ├─ import cv2
  │   └─ read_image_dimensions(image_path)
  │
  ├─ interpreter.allocate_tensors()
  ├─ interpreter.get_input_details()
  ├─ interpreter.get_output_details()
  ├─ quantization handling (uint8 vs float32)
  ├─ interpreter.set_tensor() + interpreter.invoke()
  ├─ interpreter.get_tensor() (output)
  ├─ argmax(output) → class index
  ├─ split_crop_disease(class_name) [phase4/app/labels.py:X]
  └─ return PredictionResult(class_name, crop, disease, confidence, inference_time_ms)
```

### Call Graph: Treatment Recommendation

```
openrouter_client.generate_treatment(agent_input)
  [phase3/app/clients/openrouter.py:41–80]
  
  ├─ build_request_payload(agent_input)
  │   ├─ output_json_schema() [phase3/app/prompts/treatment_prompt.py:X]
  │   └─ render_treatment_user_prompt(agent_input)
  │
  ├─ httpx.Client.post(
  │     base_url="/chat/completions",
  │     headers={"Authorization": f"Bearer {api_key}"},
  │     json=request_payload
  │   )
  │
  ├─ parse_openrouter_response(raw_response)
  │   ├─ extract message content
  │   ├─ json.loads(content)
  │   └─ TreatmentAgentOutput.model_validate(json_payload)
  │
  └─ return (TreatmentAgentOutput, request_payload, raw_response)
```

---

## 2. Grid Controller Analysis

### Interface Definition

**File:** `phase6/grid.py` (lines 1–19)

```python
class GridMovementController(ABC):
    @abstractmethod
    def move_to_grid_position(self, row_index: int, plant_index: int) -> None:
        """Move the rover to the requested row and plant grid location."""
    
    @abstractmethod
    def stop(self) -> None:
        """Stop rover motion at the current grid position."""
```

### Current Implementation (No-Op)

**File:** `phase6/grid.py` (lines 22–32)

```python
class NoOpGridMovementController(GridMovementController):
    def move_to_grid_position(self, row_index: int, plant_index: int) -> None:
        return None
    
    def stop(self) -> None:
        return None
```

### Usages of GridMovementController

| Location | Method | Line | Context |
|----------|--------|------|---------|
| `phase6/controller.py` | `__init__` | 70 | Constructor parameter `grid_controller: GridMovementController \| None = None` |
| `phase6/controller.py` | `__init__` | 80 | Assignment: `self.grid_controller = grid_controller or NoOpGridMovementController()` |
| `phase6/controller.py` | `from_settings` | 107 | Always instantiates with: `grid_controller=NoOpGridMovementController()` |
| `phase6/controller.py` | `run_scan` | 117–118 | Calls: `self.grid_controller.move_to_grid_position(row_index, plant_index)` and `self.grid_controller.stop()` |

### Current Behavior

- `move_to_grid_position(row_index, plant_index)` is called at the start of `run_scan()` [controller.py:117]
- Rover should move to row/plant coordinates, then stop before capture [controller.py:118]
- Capture happens after grid movement completes [controller.py:125]
- **Currently:** No-op returns immediately; workflow continues without actual movement

---

## 3. Motor Controller Integration Plan

### Step 1: Create Motor Controller Class

**File to create:** `phase6/motor_controller.py`

**Template structure:**
```python
# phase6/motor_controller.py

from __future__ import annotations

import RPi.GPIO as GPIO  # Raspberry Pi specific
from phase6.grid import GridMovementController

class RPiMotorGridMovementController(GridMovementController):
    """Concrete motor controller for Raspberry Pi GPIO."""
    
    def __init__(self, gpio_pins: dict[str, int], ...):
        # GPIO setup for L298N driver and 4 DC motors
        self.motor_a_pin = gpio_pins.get("motor_a", 17)  # Example pins
        # ... initialize hardware
    
    def move_to_grid_position(self, row_index: int, plant_index: int) -> None:
        # Calculate distance from current position to target
        # Send PWM signals to motor driver
        pass
    
    def stop(self) -> None:
        # Set all motor pins to stop state
        pass
    
    def cleanup(self):
        GPIO.cleanup()
```

### Step 2: Modify Controller Instantiation

**File:** `phase6/controller.py`  
**Current code (line 83):**
```python
grid_controller=NoOpGridMovementController(),
```

**Change to:**
```python
# At class level: Accept injected motor controller
# Modify __init__ signature (line 53) to accept optional motor_controller param:
# grid_controller: GridMovementController | None = None,

# In from_settings() (line 107): instantiate concrete controller:
# motor_controller = RPiMotorGridMovementController(gpio_config) if GPIO_AVAILABLE else NoOpGridMovementController()
# grid_controller=motor_controller,
```

### Step 3: Update Main Entry Point

**File:** `phase6/main.py`  
**Modification:** Pass motor controller through args

```python
# In parse_args():
parser.add_argument("--gpio-pins", type=str, default="17,27,22,23")
parser.add_argument("--disable-motor-controller", action="store_true")

# In main():
if args.disable_motor_controller:
    grid_controller = NoOpGridMovementController()
else:
    gpio_pins = parse_gpio_pins(args.gpio_pins)
    grid_controller = RPiMotorGridMovementController(gpio_pins)

controller = Phase6WorkflowController.from_settings(
    ...,
    grid_controller=grid_controller,  # NEW
)
```

### Step 4: Dependency Injection Point

**Dependency injection occurs in:**
- `phase6/main.py` (line 39): `Phase6WorkflowController.from_settings()`
- `phase6/controller.py` (line 62): `__init__` accepts `grid_controller` parameter

**Current injection:** Always `NoOpGridMovementController()`  
**Required modification:** Allow caller to specify concrete implementation

---

## 4. Dependency Graph

### Phase 6 Dependencies

```
phase6/main.py
  ├─ phase6.settings.Phase6Settings
  │   ├─ phase3.app.config.settings.Settings
  │   └─ phase4.app.config.Phase4Config
  │
  ├─ phase6.controller.Phase6WorkflowController
  │   ├─ phase6.camera.CameraCapture
  │   │   └─ cv2 (opencv-python-headless)
  │   │   └─ picamera2 (Raspberry Pi Camera)
  │   ├─ phase6.storage.LocalSessionStore
  │   │   └─ sqlite3 (standard library)
  │   ├─ phase6.grid.GridMovementController
  │   │   └─ (abstract; currently NoOpGridMovementController)
  │   ├─ phase3.app.clients.openrouter.OpenRouterClient
  │   │   └─ httpx (HTTP client)
  │   ├─ phase3.app.integrations.backend.BackendClient
  │   │   └─ httpx
  │   ├─ phase3.app.notifications.telegram.TelegramClient
  │   │   └─ httpx
  │   ├─ phase4.app.inference (run_tflite_prediction, build_detection_payload)
  │   │   ├─ tflite_runtime OR tensorflow.lite
  │   │   ├─ numpy
  │   │   ├─ cv2
  │   │   └─ phase4.app.severity (estimate_severity_opencv)
  │   │       └─ cv2
  │   └─ phase3.app.main (build_pipeline, configure_logging)
  │       └─ phase3.app.storage.audit_store.AuditStore
  │           └─ sqlite3
```

### Phase 3 Dependencies (on Pi)

```
phase3/app/clients/openrouter.py
  ├─ httpx==0.28.1
  ├─ phase3.app.prompts.treatment_prompt
  ├─ phase3.app.schemas.treatment.TreatmentAgentOutput

phase3/app/integrations/backend.py
  ├─ httpx
  ├─ phase3.app.schemas.detection.DetectionCreate
  └─ phase3.app.schemas.treatment

phase3/app/notifications/telegram.py
  ├─ httpx
  ├─ phase3.app.schemas.pipeline.TelegramDeliveryResult
```

### Phase 4 Dependencies (on Pi)

```
phase4/app/inference.py
  ├─ tflite_runtime (preferred on Pi) OR tensorflow>=2.15
  ├─ numpy>=1.24
  ├─ cv2 (opencv-python-headless)
  └─ phase4.app.severity (estimate_severity_opencv)
      └─ cv2

phase4/app/severity.py
  ├─ cv2
  ├─ numpy
```

### Runtime-Critical Modules

| Module | Critical | Reason |
|--------|----------|--------|
| `phase6/main.py` | YES | Entry point |
| `phase6/controller.py` | YES | Workflow orchestration |
| `phase4/app/inference.py` | YES | Disease classification |
| `phase3/app/clients/openrouter.py` | CONDITIONAL | Only if OpenRouter enabled |
| `phase3/app/integrations/backend.py` | CONDITIONAL | Only if backend sync enabled |
| `phase3/app/notifications/telegram.py` | CONDITIONAL | Only if Telegram enabled |
| `phase6/camera.py` | YES | Image capture |
| `phase6/grid.py` | YES | Movement abstraction (currently no-op) |
| `phase6/storage.py` | YES | Session persistence |

---

## 5. Backend Dependency Analysis

### Dependency Classification

#### A. Direct Python Dependency

**Backend modules imported on rover:**
- `phase3/app/integrations/backend.py` imports:
  - `phase3.app.schemas.detection.DetectionCreate`
  - `phase3.app.schemas.inventory`
  - `phase3.app.schemas.treatment`

**Classification:** Direct Python dependency (schemas only; no ORM or database connection)

#### B. HTTP/API Dependency

**Backend API calls from Pi:**
```python
# phase3/app/integrations/backend.py:BackendClient

POST /auth/login
  → phase3/app/integrations/backend.py:57 (login method)
  
POST /detections
  → phase3/app/integrations/backend.py:75 (upload_detection method)

GET /detections (duplicate check)
  → phase3/app/integrations/backend.py:96 (find_detection_by_session_id method)

POST /recommendations
  → phase3/app/integrations/backend.py:112 (upload_recommendation method)

POST /inventory/check
  → phase3/app/integrations/backend.py:145 (check_inventory method)
```

#### C. No Dependency (Optional)

- Backend server **not required** on Raspberry Pi
- Backend can run on laptop/server and accessed via HTTP
- If `BACKEND_BASE_URL` is not set, backend sync is skipped
- See `phase3/app/integrations/backend.py:43` (`is_configured` property)

### Backend URLs

| Variable | File | Default | Used for |
|----------|------|---------|----------|
| `BACKEND_BASE_URL` | `phase3/app/config/settings.py:78` | (None) | Base URL for HTTP calls |
| `BACKEND_USERNAME` | `phase3/app/config/settings.py:79` | (None) | Login credential |
| `BACKEND_PASSWORD` | `phase3/app/config/settings.py:80` | (None) | Login credential |
| `BACKEND_VENDOR_ID` | `phase3/app/config/settings.py:81` | `vendor_001` | Inventory vendor ID |

### Backend Server Deployment

**Conclusion:** Backend **must stay on laptop/server**. Do NOT deploy to Pi.

**Rationale:**
- FastAPI + Uvicorn + SQLAlchemy + SQLite are backend-only
- Pi accesses backend via HTTP only
- Backend provides centralized data persistence for multi-device scenarios

---

## 6. Model Audit

### Model File Locations

| File | Path | Size | Purpose |
|------|------|------|---------|
| `model.tflite` | `phase4/runs/mobilenetv3/model.tflite` | ~1.1 MB | Compiled TensorFlow Lite model |
| `labels.json` | `phase4/runs/mobilenetv3/labels.json` | ~500 B | Class labels (potato_healthy, etc) |
| `resolved_config.json` | `phase4/runs/mobilenetv3/resolved_config.json` | ~1 KB | Training config metadata |

### Model Runtime Loading

**File:** `phase6/settings.py` (lines 40–41)
```python
model_path=Path(os.getenv("PHASE6_MODEL_PATH", default_model_dir / "model.tflite")),
labels_path=Path(os.getenv("PHASE6_LABELS_PATH", default_model_dir / "labels.json")),
```

**Default search path:**
```
phase4/runs/mobilenetv3/model.tflite
phase4/runs/mobilenetv3/labels.json
```

**Runtime load sequence:**

1. `phase6/settings.py:40` (Phase6Settings.from_env) → Set model_path
2. `phase6/main.py:39` (Phase6WorkflowController.from_settings) → Pass model_path to controller
3. `phase6/controller.py:40,41` (store model_path as instance variable)
4. `phase6/controller.py:131` (run_scan calls run_tflite_prediction with model_path)
5. `phase4/app/inference.py:47` (run_tflite_prediction loads model)
6. `phase4/app/inference.py:20` (_load_interpreter):
   ```python
   try:
       from tflite_runtime.interpreter import Interpreter  # Preferred on Pi
   except ImportError:
       import tensorflow as tf
       Interpreter = tf.lite.Interpreter  # Fallback on dev machine
   interpreter = Interpreter(model_path=str(model_path))
   ```

### Model Deployment Requirements

**Must copy to Pi:**
```
phase4/runs/mobilenetv3/model.tflite
phase4/runs/mobilenetv3/labels.json
```

**Optional (metadata):**
```
phase4/runs/mobilenetv3/resolved_config.json  # For reference
```

**Do NOT copy:**
```
phase4/runs/mobilenetv3/saved_model.keras     # Training artifact only
phase4/runs/mobilenetv3/checkpoints/          # Training artifact only
phase4/runs/mobilenetv3/tensorboard/          # Training artifact only
```

---

## 7. Environment Variables Audit

### Phase 6 Runtime Variables

| Variable | File | Line | Default | Required | Purpose |
|----------|------|------|---------|----------|---------|
| `PHASE6_MODEL_PATH` | `phase6/settings.py` | 40 | `phase4/runs/mobilenetv3/model.tflite` | NO | Path to TFLite model |
| `PHASE6_LABELS_PATH` | `phase6/settings.py` | 41 | `phase4/runs/mobilenetv3/labels.json` | NO | Path to class labels |
| `PHASE6_CAPTURE_DIR` | `phase6/settings.py` | 42 | `captures` | NO | Where to save captured images |
| `PHASE6_LOCAL_DB_PATH` | `phase6/settings.py` | 43 | `logs/phase6_sessions.db` | NO | SQLite session database |
| `FARM_SIZE_ACRES` | `phase6/settings.py` | 44 | `1.0` | NO | For treatment dose calculation |
| `NUMBER_OF_PLANTS` | `phase6/settings.py` | 45 | `500` | NO | For treatment dose calculation |
| `COUNTRY` | `phase6/settings.py` | 46 | `India` | NO | Geolocation context for LLM |
| `LANGUAGE` | `phase6/settings.py` | 47 | `English` | NO | Telegram message language |
| `ROW_INDEX` | `phase6/settings.py` | 48 | `0` | NO | Grid row starting position |
| `PLANT_INDEX` | `phase6/settings.py` | 49 | `0` | NO | Grid plant starting position |
| `CAMERA_INDEX` | `phase6/settings.py` | 50 | `0` | NO | OpenCV camera index (0 = first camera) |
| `CAMERA_WARMUP_SECONDS` | `phase6/settings.py` | 51 | `0.2` | NO | Camera warm-up delay |

### Phase 3 OpenRouter Variables

| Variable | File | Line | Default | Required | Purpose |
|----------|------|------|---------|----------|---------|
| `OPENROUTER_API_KEY` | `phase3/app/config/settings.py` | 64 | (None) | YES (if OpenRouter enabled) | API authentication |
| `OPENROUTER_BASE_URL` | `phase3/app/config/settings.py` | 65–68 | `https://openrouter.ai/api/v1` | NO | OpenRouter endpoint |
| `OPENROUTER_MODEL` | `phase3/app/config/settings.py` | 69–72 | `google/gemini-3.1-flash-lite` | NO | Model selection |
| `OPENROUTER_TEMPERATURE` | `phase3/app/config/settings.py` | 73 | `0.2` | NO | LLM temperature (lower = more deterministic) |
| `OPENROUTER_MAX_TOKENS` | `phase3/app/config/settings.py` | 74 | `1800` | NO | Max response tokens |

### Phase 3 Backend Variables

| Variable | File | Line | Default | Required | Purpose |
|----------|------|------|---------|----------|---------|
| `BACKEND_BASE_URL` | `phase3/app/config/settings.py` | 78 | (None) | NO (optional) | Backend server URL (e.g., `http://laptop-ip:8000`) |
| `BACKEND_USERNAME` | `phase3/app/config/settings.py` | 79 | (None) | NO (if backend used) | Login username |
| `BACKEND_PASSWORD` | `phase3/app/config/settings.py` | 80 | (None) | NO (if backend used) | Login password |
| `BACKEND_VENDOR_ID` | `phase3/app/config/settings.py` | 81 | `vendor_001` | NO | Vendor ID for inventory checks |

### Phase 3 Telegram Variables

| Variable | File | Line | Default | Required | Purpose |
|----------|------|------|---------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | `phase3/app/config/settings.py` | 82 | (None) | NO (optional) | Telegram bot authentication |
| `TELEGRAM_CHAT_ID` | `phase3/app/config/settings.py` | 83 | (None) | NO (if Telegram used) | Target chat for notifications |
| `TELEGRAM_BASE_URL` | `phase3/app/config/settings.py` | 84–87 | `https://api.telegram.org` | NO | Telegram API endpoint |

### Phase 3 Logging & Retry

| Variable | File | Line | Default | Required | Purpose |
|----------|------|------|---------|----------|---------|
| `REQUEST_TIMEOUT_SECONDS` | `phase3/app/config/settings.py` | 73 | `30.0` | NO | HTTP timeout |
| `RETRY_ATTEMPTS` | `phase3/app/config/settings.py` | 74 | `3` | NO | API retry count |
| `RETRY_BACKOFF_SECONDS` | `phase3/app/config/settings.py` | 75 | `1.0` | NO | Retry backoff delay |
| `AUDIT_DB_PATH` | `phase3/app/config/settings.py` | 88 | `logs/phase3_audit.db` | NO | SQLite audit log |
| `LOG_LEVEL` | `phase3/app/config/settings.py` | 89 | `INFO` | NO | Logging verbosity |

### Environment File

**Location:** `.env` (loaded by both phase3 and phase6)  
**File:** `phase3/.env.example` (template provided)

**Minimal .env for Pi with no backend/Telegram:**
```ini
PHASE6_MODEL_PATH=phase4/runs/mobilenetv3/model.tflite
PHASE6_LABELS_PATH=phase4/runs/mobilenetv3/labels.json
FARM_SIZE_ACRES=1.0
NUMBER_OF_PLANTS=500
```

**Full .env for Pi with all features:**
```ini
# Phase 6
PHASE6_MODEL_PATH=phase4/runs/mobilenetv3/model.tflite
PHASE6_LABELS_PATH=phase4/runs/mobilenetv3/labels.json
PHASE6_CAPTURE_DIR=captures
PHASE6_LOCAL_DB_PATH=logs/phase6_sessions.db
FARM_SIZE_ACRES=1.0
NUMBER_OF_PLANTS=500
CAMERA_INDEX=0
CAMERA_WARMUP_SECONDS=0.2

# Phase 3 - OpenRouter
OPENROUTER_API_KEY=sk-your-api-key
OPENROUTER_MODEL=google/gemini-3.1-flash-lite
OPENROUTER_TEMPERATURE=0.2

# Phase 3 - Backend (optional, laptop IP)
BACKEND_BASE_URL=http://192.168.1.100:8000
BACKEND_USERNAME=admin
BACKEND_PASSWORD=admin123

# Phase 3 - Telegram (optional)
TELEGRAM_BOT_TOKEN=123456:bot-token-here
TELEGRAM_CHAT_ID=123456789
```

---

## 8. Storage Audit

### SQLite Databases

| Database | Path | Created by | Tables | Purpose |
|----------|------|------------|--------|---------|
| `phase6_sessions.db` | `logs/phase6_sessions.db` (default, env: `PHASE6_LOCAL_DB_PATH`) | `phase6/storage.py:_init_db()` | `phase6_sessions` | Local session persistence (image path, detection JSON, treatment JSON, sync status, backend response, inventory result, Telegram result) |
| `phase3_audit.db` | `logs/phase3_audit.db` (default, env: `AUDIT_DB_PATH`) | `phase3/app/storage/audit_store.py` | `phase3_audit_runs` | Treatment agent call audit trail |

### Capture Directory

**Path:** `captures` (configurable via `PHASE6_CAPTURE_DIR`)  
**Contents:** JPEG images named `sess_<timestamp>_<random>.jpg`  
**Growth rate:** 1 image per scan cycle (~3–5 MB per image with 1280×720 resolution)  
**Retention:** Controlled by `max_local_sessions` config (default: 20 sessions)

### Log Directory

**Path:** `logs`  
**Contents:**
- `phase6_sessions.db` (SQLite for session persistence)
- `phase3_audit.db` (SQLite for OpenRouter call audit)
- `phase3.log` (structured logs if logging configured)

### Folders Required on Raspberry Pi

| Folder | Required | Reason | Writable |
|--------|----------|--------|----------|
| `captures/` | YES | Image storage | YES |
| `logs/` | YES | Database and logs | YES |
| `phase4/runs/mobilenetv3/` | YES | Model + labels | NO (read-only) |
| `phase3/` | YES | Treatment agent code | NO (read-only) |
| `phase6/` | YES | Orchestration code | NO (read-only) |
| `phase4/app/` | YES | Inference module | NO (read-only) |
| `.env` | YES | Runtime configuration | YES (optional, could be in /etc) |

### Runtime-Generated Data Summary

```
Startup:
  ├─ logs/phase6_sessions.db (created if missing)
  ├─ logs/phase3_audit.db (created if missing)
  └─ captures/ (created if missing)

Per Scan Cycle:
  ├─ captures/sess_<id>.jpg (~3–5 MB)
  ├─ logs/phase6_sessions.db += 1 row
  ├─ logs/phase3_audit.db += 1 row (if OpenRouter used)
  └─ Memory: ~50–100 MB temporary (image processing, HTTP responses)
```

---

## 9. Raspberry Pi Compatibility Audit

### Critical Package Analysis

| Package | Version | Pi Compatibility | Issue | Recommendation |
|---------|---------|-----------------|-------|-----------------|
| `tensorflow` | `>=2.15,<2.18` | ❌ INCOMPATIBLE | Full TensorFlow is x86/ARM64; Pi needs `tflite-runtime` | Use `tflite-runtime` on Pi (ARM32/ARM64) |
| `tflite-runtime` | (not in requirements) | ✅ COMPATIBLE | Lightweight interpreter; available as ARM wheel | Install separately on Pi: `pip install tflite-runtime` |
| `opencv-python-headless` | `>=4.8,<5` | ✅ COMPATIBLE | No GUI; ARM builds available | Keep as-is |
| `numpy` | `>=1.24` | ✅ COMPATIBLE | NumPy has ARM32/ARM64 wheels | Keep as-is |
| `httpx` | `==0.28.1` | ✅ COMPATIBLE | Pure Python HTTP client | Keep as-is |
| `pydantic` | `==2.10.4` | ✅ COMPATIBLE | Data validation; pure Python | Keep as-is |
| `picamera2` | (not in requirements) | ✅ COMPATIBLE | Official Raspberry Pi camera library | Install on Pi if using Pi Camera: `pip install picamera2` |
| `RPi.GPIO` | (not in requirements) | ✅ COMPATIBLE | Official Raspberry Pi GPIO library | Install on Pi if using GPIO motors: `pip install RPi.GPIO` |

### Camera Dependencies

| Camera Type | Driver | Package | Pi Compatibility | Notes |
|-------------|--------|---------|-----------------|-------|
| Pi Camera V2 | Picamera2 | `picamera2` | ✅ NATIVE | Preferred; official library |
| Generic USB Camera | OpenCV | `opencv-python-headless` | ✅ COMPATIBLE | Via `cv2.VideoCapture()` |

**Camera fallback chain:**
1. Try `picamera2` (Raspberry Pi Camera)
2. Fallback to `cv2.VideoCapture()` (USB camera)
3. Raise error if both fail

### GPIO/Motor Dependencies

| Component | Package | Pi Compatibility | Notes |
|-----------|---------|-----------------|-------|
| L298N Motor Driver | `RPi.GPIO` | ✅ COMPATIBLE | Not in current requirements; must add |
| DC Motors | (hardware) | ✅ COMPATIBLE | No Python dependency |
| Geared Motors | (hardware) | ✅ COMPATIBLE | No Python dependency |

### Python Version Requirement

**Minimum:** Python 3.11+  
**Recommendation:** Python 3.11 or 3.12 on Raspberry Pi OS  
**Compatibility:** All dependencies tested on Python 3.11+

### ARM Architecture Support

| Architecture | Support | Notes |
|--------------|---------|-------|
| ARM64 (Pi 4, Pi 5) | ✅ FULL | All packages have ARM64 wheels |
| ARM32 (Pi 3, Pi Zero W) | ⚠️ PARTIAL | Some packages (numpy) have limited ARM32 support; `tflite-runtime` available |

### Installation on Raspberry Pi

**Recommended steps:**

```bash
# On Raspberry Pi running Raspberry Pi OS (64-bit preferred)

# 1. System dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv libopenjp2-7 libtiff6

# 2. Create virtual environment
python3.11 -m venv /home/pi/rover-venv
source /home/pi/rover-venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install phase4 requirements (replace tensorflow with tflite-runtime)
pip install -r phase4/requirements.txt --no-deps
pip uninstall -y tensorflow
pip install tflite-runtime

# 5. Install phase3 requirements
pip install -r phase3/requirements.txt

# 6. Install camera-specific packages
pip install picamera2

# 7. Install GPIO library (for motor controller)
pip install RPi.GPIO
```

**Resultant Pi environment requirements:**

```
opencv-python-headless>=4.8,<5
numpy>=1.24
pydantic==2.10.4
httpx==0.28.1
tflite-runtime (in place of tensorflow)
picamera2
RPi.GPIO
```

### Known Incompatibilities

| Issue | Workaround |
|-------|-----------|
| Full TensorFlow too large for Pi | Use `tflite-runtime` instead (50 MB vs 500+ MB) |
| Training code (Phase 4 training) requires TensorFlow | Install TensorFlow on laptop only; export `.tflite` to Pi |
| FastAPI + SQLAlchemy runs on Pi | Backend intentionally stays on laptop; Pi only calls via HTTP |

---

## 10. Deployment Classification

### Folder Classification

| Folder | Classification | Justification |
|--------|-----------------|---------------|
| `phase6/` | A. Must copy to Pi | Orchestration, camera, storage, grid abstraction |
| `phase4/app/` | A. Must copy to Pi | Inference, severity, labels, preprocessing |
| `phase4/runs/mobilenetv3/` | A. Must copy to Pi | Model artifacts (model.tflite, labels.json) |
| `phase3/app/` | A. Must copy to Pi | Treatment agent, backend client, Telegram client |
| `backend/` | B. Must stay on Laptop | FastAPI server, SQLAlchemy ORM, database |
| `dataset/` | B. Must stay on Laptop | Training data; not used by inference |
| `phase4/configs/` | C. Optional (if retraining on Pi) | Config files; typically read-only on Pi |
| `docs/` | C. Optional | Documentation; not runtime-critical |
| `phase7/` | C. Optional | Documentation; not runtime-critical |
| `.venv/` | N/A (Recreate) | Virtual environment; create new on Pi |

### Deployment Table: What Goes Where

```
┌──────────────────────────────┬────────┬──────────┬─────────────┐
│ Component                    │ Laptop │ Pi       │ Notes       │
├──────────────────────────────┼────────┼──────────┼─────────────┤
│ Backend (FastAPI)            │   ✓    │          │ Central DB  │
│ Phase 6 (Orchestration)      │        │    ✓     │ Entry point │
│ Phase 4 (Inference)          │   ✓    │    ✓     │ Pi = TFLite  │
│ Phase 3 (Agent)              │   ✓    │    ✓     │ Pi calls OR  │
│ Model (TFLite)               │   ✓    │    ✓     │ Export once │
│ Labels (JSON)                │   ✓    │    ✓     │ Export once │
│ Training data                │   ✓    │          │ Not on Pi    │
│ .env config                  │   ✓    │    ✓     │ Different!  │
│ Virtual environment          │   ✓    │    ✓     │ Separate    │
│ SQLite logs (phase3_audit)   │   ✓    │    ✓     │ Each tracks │
│ SQLite sessions (phase6)     │        │    ✓     │ Pi only      │
└──────────────────────────────┴────────┴──────────┴─────────────┘
```

### Minimal Pi Deployment Package

**Size estimate:** ~300 MB (code + models + dependencies)

```
phase6/
  ├─ __init__.py
  ├─ main.py                   # Entry point
  ├─ controller.py             # Workflow
  ├─ camera.py                 # Capture
  ├─ grid.py                   # Grid abstraction
  ├─ storage.py                # SQLite sessions
  ├─ settings.py               # Config loading
  └─ motor_controller.py        # NEW: GPIO motor control

phase4/
  ├─ app/
  │   ├─ __init__.py
  │   ├─ inference.py          # TFLite runtime
  │   ├─ severity.py           # OpenCV severity
  │   ├─ labels.py             # Label parsing
  │   ├─ preprocessing.py      # Image prep
  │   ├─ config.py             # Config dataclass
  │   └─ logging.py            # Structured logging
  └─ runs/mobilenetv3/
      ├─ model.tflite          # Compiled model (~1.1 MB)
      └─ labels.json           # Class labels (~500 B)

phase3/
  ├─ app/
  │   ├─ __init__.py
  │   ├─ main.py               # Pipeline builder
  │   ├─ config/
  │   │   └─ settings.py       # Env var loading
  │   ├─ clients/
  │   │   └─ openrouter.py     # LLM client
  │   ├─ integrations/
  │   │   └─ backend.py        # Backend HTTP client
  │   ├─ notifications/
  │   │   └─ telegram.py       # Telegram client
  │   ├─ schemas/              # Pydantic models
  │   ├─ services/             # Transformers
  │   ├─ prompts/              # LLM prompts
  │   ├─ utils/                # Logging, retry, errors
  │   └─ storage/
  │       └─ audit_store.py    # SQLite audit
  └─ .env                      # Runtime config (Pi-specific)

captures/                       # Captured images (created at runtime)
logs/                          # SQLite databases (created at runtime)
.env                           # Configuration file
requirements.txt               # Filtered: no tensorflow, no backend deps
```

---

## 11. Hardware Integration Readiness

### Current Software Status vs Hardware Requirements

| Hardware | Component | Software Status | Integration Missing |
|----------|-----------|-----------------|---------------------|
| Raspberry Pi 4 | Core compute | ✅ READY | None (all Python code runs) |
| Pi Camera V2 | Image capture | ✅ READY | Optional: `picamera2` library |
| L298N Motor Driver | PWM control for motors | ❌ NOT IMPLEMENTED | `RPi.GPIO` library + motor_controller.py |
| 4 DC Geared Motors | Movement | ❌ NOT IMPLEMENTED | GPIO pin mapping + PWM signals |
| Battery Pack | Power | ✅ READY | Hardware only; no software |
| LM2596 Buck Converter | Voltage regulation | ✅ READY | Hardware only; no software |

### Missing Software Pieces

#### 1. Motor Controller Class (CRITICAL)

**What's missing:**
```python
# phase6/motor_controller.py (does not exist)
class RPiMotorGridMovementController(GridMovementController):
    def move_to_grid_position(self, row_index: int, plant_index: int) -> None:
        # Calculate movement distance
        # Send PWM signals to L298N motor driver pins
        # Poll motor feedback (if encoders present) or time-based movement
        # Stop when position reached
    
    def stop(self) -> None:
        # Set all motor pins to LOW
        # Stop PWM
```

**Location:** `phase6/motor_controller.py` (NEW FILE)

#### 2. GPIO Pin Configuration

**What's missing:**
```python
# GPIO pin mapping for L298N + 4 motors
GPIO_CONFIG = {
    'motor_a_enable': 17,      # PWM pin for Motor A speed
    'motor_a_in1': 27,         # Direction pin
    'motor_a_in2': 22,         # Direction pin
    'motor_b_enable': 23,      # PWM pin for Motor B speed
    'motor_b_in1': 24,         # Direction pin
    'motor_b_in2': 25,         # Direction pin
    # ... similarly for motors C and D
}
```

#### 3. Motor Encoder Support (Optional)

**What's missing (if using feedback):**
- Encoder interrupt handlers
- Distance calculation logic
- Feedback-based movement termination

#### 4. Startup/Shutdown Handlers

**What's missing:**
```python
# In phase6/main.py:
def cleanup():
    motor_controller.cleanup()  # Reset GPIO pins
    
signal.signal(signal.SIGINT, lambda *args: (cleanup(), sys.exit(0)))
```

### Integration Checklist

- [ ] **Install `RPi.GPIO`** on Pi: `pip install RPi.GPIO`
- [ ] **Create `phase6/motor_controller.py`** implementing `GridMovementController` for L298N + 4 motors
- [ ] **Map GPIO pins** for:
  - Motor A (2 direction pins + 1 PWM enable)
  - Motor B (2 direction pins + 1 PWM enable)
  - Motor C (2 direction pins + 1 PWM enable)
  - Motor D (2 direction pins + 1 PWM enable)
- [ ] **Implement movement logic:**
  - Calculate distance from current → target grid position
  - Send appropriate PWM to motors
  - Stop when target reached
- [ ] **Implement stop logic:** Set all motor pins LOW
- [ ] **Add GPIO cleanup** on process exit
- [ ] **Test motor movement** independently before integration
- [ ] **Test Phase 6 grid movement** with mock motor controller
- [ ] **Connect motors and test full workflow**

### Prototype Motor Controller Skeleton

```python
# phase6/motor_controller.py (TEMPLATE FOR IMPLEMENTATION)

from __future__ import annotations

import logging
import RPi.GPIO as GPIO
import time
from phase6.grid import GridMovementController

LOGGER = logging.getLogger(__name__)

GPIO_PINS = {
    'motor_a_enable': 17,
    'motor_a_in1': 27,
    'motor_a_in2': 22,
    'motor_b_enable': 23,
    'motor_b_in1': 24,
    'motor_b_in2': 25,
    # Add motors C, D as needed
}

class RPiMotorGridMovementController(GridMovementController):
    def __init__(self, gpio_pins: dict[str, int] | None = None):
        self.gpio_pins = gpio_pins or GPIO_PINS
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup all pins
        for pin in self.gpio_pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        # Setup PWM for enable pins
        self.pwm_a = GPIO.PWM(self.gpio_pins['motor_a_enable'], 1000)
        self.pwm_b = GPIO.PWM(self.gpio_pins['motor_b_enable'], 1000)
        # ... etc for C, D
        
        self.current_row = 0
        self.current_plant = 0
    
    def move_to_grid_position(self, row_index: int, plant_index: int) -> None:
        LOGGER.info(f"Moving to row {row_index}, plant {plant_index}")
        
        # Placeholder: calculate direction and distance
        # For now: assume each row is 1m, each plant is 0.5m spacing
        
        # TODO: Implement actual movement logic
        # This is where PWM signals would be sent
        
        self.current_row = row_index
        self.current_plant = plant_index
    
    def stop(self) -> None:
        LOGGER.info("Stopping motors")
        self.pwm_a.stop()
        self.pwm_b.stop()
        # ... stop C, D
        
        for pin in self.gpio_pins.values():
            GPIO.output(pin, GPIO.LOW)
    
    def cleanup(self):
        LOGGER.info("Cleaning up GPIO")
        GPIO.cleanup()
```

---

## 12. Deployment Plan

### Phase 1: Prepare Laptop

```bash
# 1. Ensure backend is running
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Export Phase 4 model (if not already done)
cd phase4
python -m phase4.app.export_tflite --model runs/mobilenetv3/saved_model.keras --output runs/mobilenetv3/model.tflite

# 3. Prepare Pi package
# Copy phase4, phase3, phase6 folders to USB stick or network share
```

### Phase 2: Prepare Raspberry Pi

```bash
# 1. Install OS and updates
# Use Raspberry Pi Imager to flash Raspberry Pi OS (64-bit recommended)

# 2. Connect to network and SSH
ssh pi@raspberrypi.local

# 3. Install system dependencies
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv libopenjp2-7 libtiff6 libatlas-base-dev

# 4. Copy code from laptop
# Via USB, SCP, or network mount
cp -r /mnt/usb/phase4 /home/pi/rover/
cp -r /mnt/usb/phase3 /home/pi/rover/
cp -r /mnt/usb/phase6 /home/pi/rover/

# 5. Create virtual environment
cd /home/pi/rover
python3.11 -m venv venv
source venv/bin/activate

# 6. Install dependencies (tflite-runtime instead of tensorflow)
pip install --upgrade pip
pip install opencv-python-headless numpy pydantic httpx picamera2 RPi.GPIO

# 7. Install tflite-runtime
pip install tflite-runtime

# 8. Create runtime directories
mkdir -p captures logs
```

### Phase 3: Create Motor Controller

```bash
# On Pi or laptop (before copying to Pi):

# Create phase6/motor_controller.py with GPIO integration
# See skeleton above

# Test motor controller independently
python3 -c "from phase6.motor_controller import RPiMotorGridMovementController; c = RPiMotorGridMovementController(); c.move_to_grid_position(1, 0); c.stop()"
```

### Phase 4: Configure Environment

```bash
# On Pi: Create .env file with Pi-specific values

cat > /home/pi/rover/.env <<EOF
# Phase 6
PHASE6_MODEL_PATH=/home/pi/rover/phase4/runs/mobilenetv3/model.tflite
PHASE6_LABELS_PATH=/home/pi/rover/phase4/runs/mobilenetv3/labels.json
PHASE6_CAPTURE_DIR=/home/pi/rover/captures
PHASE6_LOCAL_DB_PATH=/home/pi/rover/logs/phase6_sessions.db
FARM_SIZE_ACRES=1.0
NUMBER_OF_PLANTS=500
CAMERA_INDEX=0

# Phase 3 - OpenRouter (if using)
OPENROUTER_API_KEY=sk-your-key
OPENROUTER_MODEL=google/gemini-3.1-flash-lite

# Phase 3 - Backend (laptop IP address!)
BACKEND_BASE_URL=http://192.168.1.100:8000
BACKEND_USERNAME=admin
BACKEND_PASSWORD=admin123

# Phase 3 - Telegram (if using)
TELEGRAM_BOT_TOKEN=123456:token
TELEGRAM_CHAT_ID=123456789
EOF
```

### Phase 5: Test Individual Components

```bash
# On Pi:

# Test camera capture
python3 -m phase6.camera --test

# Test model loading and inference
python3 -c "from phase4.app.inference import run_tflite_prediction; print('Model loads OK')"

# Test grid controller
python3 -c "from phase6.grid import NoOpGridMovementController; c = NoOpGridMovementController(); c.move_to_grid_position(1, 0); c.stop(); print('Grid controller OK')"

# Test Phase 3 OpenRouter (if API key set)
python3 -m phase3.app.main --input phase3/examples/detection_sample.json --farm-size-acres 1.0 --number-of-plants 500 --skip-backend --skip-telegram
```

### Phase 6: Run Full Workflow

```bash
# On Pi:

# Test with source image (no camera required)
python3 -m phase6.main \
  --source-image /path/to/sample.jpg \
  --farm-size-acres 1.0 \
  --number-of-plants 500 \
  --row-index 1 \
  --plant-index 7

# Test with live camera (if available)
python3 -m phase6.main \
  --farm-size-acres 1.0 \
  --number-of-plants 500

# Verify output: should see detection JSON printed to console
# Verify SQLite: check logs/phase6_sessions.db created and populated
# Verify captures: check captures/ folder has .jpg file
```

---

## 13. Recommended Next Steps

### Immediate (Before any Pi connection)

1. **✅ Code Review:**
   - Review `phase6/main.py` entry point
   - Review `phase6/controller.py` workflow
   - Identify GPIO pin mapping needed for your motor driver

2. **✅ Create Motor Controller Skeleton:**
   - New file: `phase6/motor_controller.py`
   - Implement `RPiMotorGridMovementController(GridMovementController)`
   - Start with no-op, then add GPIO signals incrementally

3. **✅ Update Dependency Injection:**
   - Modify `phase6/main.py` to accept `--gpio-pins` argument
   - Modify `phase6/controller.py` to accept motor_controller parameter in `from_settings()`
   - Modify `phase6/controller.py:80` to use injected controller instead of always `NoOpGridMovementController()`

4. **✅ Prepare Requirements for Pi:**
   - Create `requirements-pi.txt` without tensorflow, with tflite-runtime
   - Document installation steps on Pi

### Short-term (Before Pi deployment)

5. **Test on Laptop First:**
   ```bash
   python -m phase6.main --source-image captures/sample.jpg --skip-backend --skip-telegram
   ```
   Should produce detection JSON without backend or Telegram

6. **Prepare Pi Deployment Package:**
   - Raspberry Pi OS 64-bit
   - Python 3.11 virtual environment
   - All required packages
   - Exported TFLite model + labels

7. **GPIO Hardware Testing:**
   - Test L298N motor driver wiring
   - Test GPIO pin connectivity
   - Validate PWM signals with multimeter or oscilloscope

### Medium-term (After Pi connection)

8. **Motor Controller Development:**
   - Implement movement calculation (grid spacing → distance)
   - Implement PWM signal generation
   - Test each motor independently
   - Test coordinated 4-motor movement
   - Test stop() cleanup

9. **Integration Testing:**
   - Run Phase 6 workflow with live camera
   - Verify grid movement → capture sequence
   - Verify all output files created
   - Verify backend sync (if configured)
   - Verify Telegram delivery (if configured)

10. **Performance Tuning:**
    - Measure end-to-end latency on Pi
    - Optimize image size if needed
    - Adjust camera warmup timing
    - Profile memory usage during workflow

### Validation Checklist

Before declaring deployment ready:

- [ ] Motor controller compiles without errors
- [ ] Grid movement accepted/injected correctly
- [ ] Phase 6 runs from Pi with --source-image
- [ ] Phase 6 captures image from live camera
- [ ] Phase 4 inference produces detection JSON
- [ ] Phase 3 agent (if enabled) calls OpenRouter successfully
- [ ] Backend sync (if enabled) uploads to laptop backend
- [ ] Telegram notification (if enabled) sends message
- [ ] SQLite session data persisted correctly
- [ ] Images stored in captures/ directory
- [ ] Motor controller GPIO initialization works
- [ ] Motor movement executes without errors
- [ ] Full end-to-end workflow runs without crashes
- [ ] Performance acceptable for field deployment

---

## Summary Table: Files to Modify/Create

| Action | File | Purpose | Impact |
|--------|------|---------|--------|
| **CREATE** | `phase6/motor_controller.py` | GPIO motor control implementation | HIGH (enables hardware) |
| **MODIFY** | `phase6/controller.py` line 62–80 | Accept injected motor controller | MEDIUM (dependency injection) |
| **MODIFY** | `phase6/main.py` lines 27–49 | Pass motor controller from CLI | MEDIUM (entry point) |
| **CREATE** | `requirements-pi.txt` | Pi-specific dependencies (no TF) | LOW (documentation) |
| **CREATE** | `.env.pi.example` | Pi-specific .env template | LOW (configuration) |
| **KEEP** | All other files | No changes needed | — |

---

## Architecture Diagrams (Text-based)

### Hardware Integration Points

```
Raspberry Pi 4
├─ GPIO Pins (BCM)
│   ├─ 17 (Motor A enable/PWM)
│   ├─ 27 (Motor A direction 1)
│   ├─ 22 (Motor A direction 2)
│   ├─ 23 (Motor B enable/PWM)
│   ├─ ... (motors C, D similar)
│   └─ GND (common ground)
│
├─ Camera Interface
│   ├─ Picamera2 (Pi Camera V2)
│   └─ USB (generic camera via OpenCV)
│
├─ Storage
│   ├─ microSD Card (~32 GB recommended)
│   │   ├─ Raspberry Pi OS
│   │   ├─ Python virtual environment
│   │   ├─ Code (phase3, phase4, phase6)
│   │   ├─ Model artifacts (1.1 MB TFLite)
│   │   ├─ captures/ (images, grows to ~100 GB)
│   │   └─ logs/ (SQLite, small)
│   │
│   └─ Laptop (over network)
│       ├─ Backend server
│       └─ Central database
│
└─ Network
    ├─ Ethernet/WiFi to Laptop
    │   ├─ Backend API calls (HTTP)
    │   └─ Backend database sync
    │
    └─ Internet (for Pi only if using)
        ├─ OpenRouter API (treatment agent)
        └─ Telegram Bot API (notifications)
```

### Software Integration Stack

```
Entry Point: phase6/main.py:main()
  │
  ├─ Settings loaded (phase6/settings.py)
  │   ├─ Phase3Settings (OpenRouter, Backend, Telegram)
  │   ├─ Phase4Config (model, inference)
  │   └─ Environment variables (.env file)
  │
  ├─ WorkflowController created (phase6/controller.py)
  │   ├─ GridMovementController (INJECTED)
  │   ├─ CameraCapture (Pi camera or OpenCV)
  │   ├─ LocalSessionStore (SQLite)
  │   ├─ OpenRouterClient (LLM agent, if enabled)
  │   ├─ BackendClient (HTTP to laptop, if enabled)
  │   └─ TelegramClient (Telegram Bot API, if enabled)
  │
  └─ run_scan() workflow
      ├─ grid_controller.move_to_grid_position(row, plant) ← MOTOR CONTROL
      ├─ grid_controller.stop() ← MOTOR STOP
      ├─ camera.capture(session_id) ← IMAGE CAPTURE
      ├─ run_tflite_prediction(model, image, labels) ← INFERENCE
      ├─ openrouter_client.generate_treatment(...) ← LLM (optional)
      ├─ backend_client.upload_detection(...) ← BACKEND SYNC (optional)
      ├─ backend_client.check_inventory(...) ← INVENTORY CHECK (optional)
      ├─ telegram_client.send_message(...) ← NOTIFICATION (optional)
      └─ store.update_session(...) ← LOCAL PERSISTENCE
```

---

**Report Generated:** June 2, 2026  
**Analysis Type:** Repository-Specific Audit  
**Code Modifications:** None (Analysis Only)  
**Recommendations:** See Section 13
