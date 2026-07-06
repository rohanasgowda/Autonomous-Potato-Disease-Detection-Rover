# Plant Disease Detection Rover Backend

Phase 2 backend prototype for the Plant Disease Detection Rover project.

This backend implements only the documented Phase 2 scope:

- FastAPI REST API
- SQLite persistence through SQLAlchemy
- Simple account login with hashed passwords and bearer tokens
- Detection upload storage
- Treatment recommendation storage
- Single-vendor inventory CRUD
- Inventory availability and price checks
- Basic dashboard summary API
- Telegram notification endpoint scaffold only

It does not implement ML inference, Raspberry Pi camera control, rover movement,
OpenRouter calls, Telegram delivery, order placement, payments, GPS, queues, or
cloud deployment.

## Requirements

- Python 3.11+
- Dependencies listed in `requirements.txt`

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Configuration

Environment variables are optional for local prototype runs.

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./plant_rover.db` | SQLite database location |
| `SECRET_KEY` | `change-this-development-secret` | JWT signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `120` | Token lifetime |
| `DEFAULT_ADMIN_USERNAME` | `admin` | Seeded admin username |
| `DEFAULT_ADMIN_PASSWORD` | `admin123` | Seeded admin password |
| `DEFAULT_VENDOR_USERNAME` | `vendor` | Seeded vendor username |
| `DEFAULT_VENDOR_PASSWORD` | `vendor123` | Seeded vendor password |
| `DEFAULT_VENDOR_ID` | `vendor_001` | Inventory check response vendor id |
| `LOW_STOCK_THRESHOLD_KG` | `1.0` | Dashboard low stock threshold |
| `CURRENCY` | `INR` | Inventory check currency |

Change the default passwords before any shared demo.

## Run Locally

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

OpenAPI docs:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Authentication

Login uses JSON:

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

Use the returned token:

```http
Authorization: Bearer <access_token>
```

Inventory mutations require `admin` or `vendor`. Read APIs and upload APIs
require a valid authenticated user.

## Detection Upload Example

```http
POST /detections
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "session_id": "sess_20260523_001",
  "device_id": "rpi_rover_01",
  "timestamp": "2026-05-23T10:30:00+05:30",
  "grid_position": {
    "row_index": 1,
    "plant_index": 7
  },
  "crop": "potato",
  "disease": "late_blight",
  "confidence": 0.92,
  "severity": {
    "label": "moderate",
    "infected_area_percent": 14.6,
    "method": "leaf_area_segmentation_v1"
  },
  "image": {
    "local_path": "captures/sess_20260523_001.jpg",
    "width": 1280,
    "height": 720
  },
  "model": {
    "name": "plant_disease_mobilenetv3",
    "version": "0.1.0",
    "runtime": "tflite"
  }
}
```

The backend stores the flattened fields in `detection_sessions` and preserves
the complete payload in `raw_detection_json`.

## Inventory Check Example

```http
POST /inventory/check
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "session_id": "sess_20260523_001",
  "vendor_id": "vendor_001",
  "items": [
    {
      "medicine_name": "example fungicide name",
      "required_quantity_kg": 1.25
    }
  ]
}
```

Response shape follows the requirements document:

```json
{
  "session_id": "sess_20260523_001",
  "vendor_id": "vendor_001",
  "items": [
    {
      "medicine_name": "example fungicide name",
      "required_quantity_kg": 1.25,
      "available_quantity_kg": 5.0,
      "is_available": true,
      "unit_price": 420.0,
      "estimated_total_price": 525.0,
      "expiry_date": "2027-02-15"
    }
  ],
  "total_estimated_price": 525.0,
  "currency": "INR"
}
```

## Tests

```powershell
cd backend
pytest
```

## Documented Assumptions

- Medicine matching is exact after lowercase/whitespace normalization. No synonym
  table is implemented in Phase 2.
- `inventory_items.medicine_name` is unique for deterministic single-vendor
  inventory checks.
- `POST /recommendations` requires the internal `detection_session_id` because
  the documented database schema links recommendations by that foreign key.
- `POST /inventory/check` accepts an optional `treatment_recommendation_id`; when
  omitted, the check is still persisted with a nullable foreign key to support
  manual dashboard/vendor checks.
- Default users are seeded on startup because the requirements include login but
  do not define a user-registration endpoint.
- `/notifications/telegram` is a scaffold only. Real Telegram delivery belongs
  to a later phase.
