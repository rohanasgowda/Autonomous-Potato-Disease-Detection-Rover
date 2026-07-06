# Phase 2 Backend Documentation

## 1. Purpose

This document explains the Phase 2 backend prototype for the Plant Disease
Detection Rover project.

The backend is a local FastAPI server that receives plant disease detection data
from the Raspberry Pi rover, stores treatment recommendations, manages vendor
inventory, checks medicine availability, and provides dashboard summary data.

This phase is backend-only. It does not perform ML inference, control rover
movement, capture camera images, call OpenRouter, or send real Telegram
messages.

## 2. What Phase 2 Implements

Phase 2 implements the backend foundation described in the requirements
document:

- User login with hashed passwords.
- JWT bearer-token authentication.
- Role support for `admin`, `vendor`, and `viewer`.
- Detection upload and storage.
- Treatment recommendation storage.
- Inventory create, read, update, and delete APIs.
- Inventory availability and price checking.
- Dashboard summary API.
- Telegram notification API scaffold.
- SQLite database persistence.
- Automated tests for core backend behavior.

The goal is to make the backend stable enough for later Raspberry Pi,
OpenRouter, Telegram, and dashboard integration phases.

## 3. Technology Stack

The backend uses:

- Python
- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- Uvicorn
- PyJWT
- passlib with bcrypt
- pytest

No PostgreSQL, MongoDB, Redis, Celery, Kafka, GraphQL, Docker, or cloud
infrastructure is used in this phase.

## 4. Folder Structure

```text
backend/
|-- app/
|   |-- api/
|   |   `-- routes/
|   |       |-- auth.py
|   |       |-- dashboard.py
|   |       |-- detections.py
|   |       |-- inventory.py
|   |       |-- notifications.py
|   |       `-- recommendations.py
|   |-- auth/
|   |   `-- dependencies.py
|   |-- core/
|   |   |-- config.py
|   |   |-- logging.py
|   |   `-- security.py
|   |-- db/
|   |   |-- init_db.py
|   |   `-- session.py
|   |-- models/
|   |   |-- detection.py
|   |   |-- inventory.py
|   |   |-- recommendation.py
|   |   `-- user.py
|   |-- schemas/
|   |   |-- auth.py
|   |   |-- dashboard.py
|   |   |-- detection.py
|   |   |-- inventory.py
|   |   |-- notification.py
|   |   `-- recommendation.py
|   |-- services/
|   |   `-- inventory.py
|   `-- main.py
|-- tests/
|-- alembic/
|-- README.md
|-- PHASE2_BACKEND_DOCUMENTATION.md
|-- pytest.ini
`-- requirements.txt
```

## 5. How the Backend Starts

The application starts from:

```text
app/main.py
```

When the server starts:

1. FastAPI creates the application object.
2. Logging is configured.
3. API routers are attached.
4. SQLite tables are created if they do not already exist.
5. Default local users are seeded if missing.

The startup logic is handled by the FastAPI lifespan function in `app/main.py`.

The database file is created at:

```text
backend/plant_rover.db
```

unless `DATABASE_URL` is changed.

## 6. Configuration

Configuration is defined in:

```text
app/core/config.py
```

The backend reads optional environment variables. If no variables are set, local
prototype defaults are used.

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./plant_rover.db` | SQLite database path |
| `SECRET_KEY` | `change-this-development-secret` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `120` | Login token lifetime |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `DEFAULT_ADMIN_USERNAME` | `admin` | Seeded admin username |
| `DEFAULT_ADMIN_PASSWORD` | `admin123` | Seeded admin password |
| `DEFAULT_VENDOR_USERNAME` | `vendor` | Seeded vendor username |
| `DEFAULT_VENDOR_PASSWORD` | `vendor123` | Seeded vendor password |
| `DEFAULT_VENDOR_ID` | `vendor_001` | Default vendor ID in inventory checks |
| `CURRENCY` | `INR` | Inventory price currency |
| `LOW_STOCK_THRESHOLD_KG` | `1.0` | Dashboard low-stock threshold |

For a demo shared with others, change `SECRET_KEY` and the default passwords.

## 7. How to Run the Backend

Open PowerShell in the project directory.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

After the server starts, open:

```text
http://localhost:8000/docs
```

This opens the automatic FastAPI Swagger UI where all APIs can be tested.

For Raspberry Pi testing on the same local network, use the laptop IP address:

```text
http://<laptop-local-ip>:8000
```

## 8. How to Run Tests

From the `backend` folder:

```powershell
pytest
```

The test suite covers:

- Login success and failure.
- Detection upload.
- Detection validation.
- Duplicate detection rejection.
- Inventory CRUD.
- Role restriction for inventory mutation.
- Inventory availability and price calculation.
- Missing inventory item behavior.
- Recommendation storage.
- Dashboard summary output.

## 9. Authentication Flow

Authentication is implemented in:

```text
app/api/routes/auth.py
app/core/security.py
app/auth/dependencies.py
```

The login process works like this:

1. A client sends username and password to `POST /auth/login`.
2. The backend finds the user in the `users` table.
3. The submitted password is checked against the stored password hash.
4. If valid, the backend creates a JWT access token.
5. The client sends this token in later requests using:

```http
Authorization: Bearer <access_token>
```

Passwords are never stored directly. Only `password_hash` is stored.

Roles:

- `admin`: can access APIs and manage inventory.
- `vendor`: can access APIs and manage inventory.
- `viewer`: can access read/upload style APIs but cannot mutate inventory.

This is intentionally simple authentication for a college prototype. OAuth,
SSO, and complex RBAC are not implemented.

## 10. Database Tables

Database models are in:

```text
app/models/
```

SQLAlchemy creates the SQLite tables.

### 10.1 users

Stores backend users.

| Field | Purpose |
|---|---|
| `id` | Internal primary key |
| `username` | Unique login username |
| `password_hash` | Hashed password |
| `role` | `admin`, `vendor`, or `viewer` |
| `created_at` | User creation timestamp |

### 10.2 detection_sessions

Stores one plant detection event uploaded by the Raspberry Pi.

| Field | Purpose |
|---|---|
| `id` | Internal primary key |
| `session_id` | External session ID from the Pi |
| `device_id` | Rover device ID |
| `timestamp` | Detection time from the Pi |
| `row_index` | Crop row position |
| `plant_index` | Plant position in row |
| `crop` | Predicted crop |
| `disease` | Predicted disease |
| `confidence` | Model confidence from 0 to 1 |
| `severity_label` | Disease severity label |
| `infected_area_percent` | Estimated infected area from 0 to 100 |
| `image_path` | Optional image path from the Pi |
| `raw_detection_json` | Full original detection JSON |

The backend flattens important fields for dashboard queries but also stores the
original JSON for future compatibility.

### 10.3 treatment_recommendations

Stores treatment recommendation data produced outside this backend.

| Field | Purpose |
|---|---|
| `id` | Internal primary key |
| `detection_session_id` | Linked detection record |
| `model_provider` | Usually `openrouter` |
| `model_name` | Selected treatment model name |
| `raw_request_json` | Treatment-agent input JSON |
| `raw_response_json` | Treatment-agent output JSON |
| `created_at` | Storage timestamp |

The backend does not call OpenRouter in Phase 2. The Raspberry Pi or later agent
module sends the recommendation JSON here.

### 10.4 inventory_items

Stores the single vendor inventory.

| Field | Purpose |
|---|---|
| `id` | Internal primary key |
| `medicine_name` | Medicine or treatment name |
| `stock_quantity_kg` | Available stock in kg |
| `price_per_kg` | Price in INR per kg |
| `expiry_date` | Expiry date |
| `created_at` | Creation timestamp |
| `updated_at` | Last update timestamp |

Medicine names are unique in this prototype so inventory checks remain
deterministic.

### 10.5 inventory_checks

Stores each inventory availability calculation.

| Field | Purpose |
|---|---|
| `id` | Internal primary key |
| `treatment_recommendation_id` | Optional linked recommendation |
| `medicine_name` | Requested medicine |
| `required_quantity_kg` | Requested quantity |
| `available_quantity_kg` | Stock available at check time |
| `is_available` | Whether enough stock exists |
| `estimated_total_price` | Required quantity multiplied by unit price |
| `checked_at` | Check timestamp |

## 11. API Endpoints

All endpoints except `/auth/login` require a bearer token.

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/login` | Login and receive access token |
| `POST` | `/detections` | Upload detection JSON |
| `GET` | `/detections` | List detection records |
| `GET` | `/detections/{id}` | Get one detection |
| `POST` | `/recommendations` | Store treatment recommendation |
| `GET` | `/recommendations/{id}` | Get one recommendation |
| `POST` | `/inventory/check` | Check medicine availability |
| `GET` | `/inventory` | List inventory |
| `POST` | `/inventory` | Create inventory item |
| `PUT` | `/inventory/{id}` | Update inventory item |
| `DELETE` | `/inventory/{id}` | Delete inventory item |
| `POST` | `/notifications/telegram` | Notification scaffold |
| `GET` | `/dashboard/summary` | Dashboard summary data |

## 12. Main Backend Workflows

### 12.1 Login Workflow

1. User sends username and password.
2. Backend checks the user table.
3. Backend verifies password hash.
4. Backend returns a JWT token.
5. Client uses that token for protected APIs.

Example:

```http
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

### 12.2 Detection Upload Workflow

The Raspberry Pi sends detection JSON to:

```http
POST /detections
```

The backend validates:

- Required fields exist.
- `confidence` is between 0 and 1.
- `infected_area_percent` is between 0 and 100.
- `severity.label` is one of:
  - `healthy`
  - `very_low`
  - `low`
  - `moderate`
  - `high`
  - `severe`
- Unknown extra fields are rejected.

Then the backend:

1. Extracts important values.
2. Stores them in `detection_sessions`.
3. Stores the full original payload in `raw_detection_json`.
4. Rejects duplicate `session_id` values.

### 12.3 Recommendation Storage Workflow

The Pi or treatment-agent side sends recommendation data to:

```http
POST /recommendations
```

The backend:

1. Checks that the linked detection exists.
2. Stores the model provider and model name.
3. Stores the complete request JSON.
4. Stores the complete response JSON.

The backend does not generate the recommendation in Phase 2.

### 12.4 Inventory CRUD Workflow

Vendors or admins manage inventory using:

```text
GET    /inventory
POST   /inventory
PUT    /inventory/{id}
DELETE /inventory/{id}
```

Each inventory item contains:

- Medicine name.
- Stock quantity in kg.
- Price per kg.
- Expiry date.

Only `admin` and `vendor` users can create, update, or delete inventory.

### 12.5 Inventory Check Workflow

The Pi, dashboard, or later notification flow calls:

```http
POST /inventory/check
```

Input example:

```json
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

The backend:

1. Normalizes the requested medicine name by lowercasing and trimming spaces.
2. Looks for the medicine in `inventory_items`.
3. Reads available stock and price.
4. Compares stock against required quantity.
5. Calculates estimated total price:

```text
required_quantity_kg * price_per_kg
```

6. Stores the check in `inventory_checks`.
7. Returns availability and price data.

If a medicine is not found:

- `available_quantity_kg` becomes `0.0`.
- `is_available` becomes `false`.
- `unit_price` becomes `null`.
- `estimated_total_price` becomes `0.0`.

No fuzzy matching or synonym matching is implemented in Phase 2.

### 12.6 Dashboard Summary Workflow

The dashboard calls:

```http
GET /dashboard/summary
```

The backend calculates:

- Total detections.
- Diseased plant count.
- Healthy plant count.
- High severity plant count.
- Low stock medicines.
- Latest detection records.

This is API-only. No frontend dashboard UI is implemented here.

### 12.7 Telegram Notification Scaffold

The endpoint exists:

```http
POST /notifications/telegram
```

It returns a `not_implemented` response.

This preserves the documented API surface, but real Telegram bot integration is
reserved for a later phase.

## 13. Validation Behavior

Validation is handled by Pydantic schemas in:

```text
app/schemas/
```

Important validation rules:

- Extra fields are rejected in request payloads where strict schemas are used.
- Detection confidence must be `0 <= confidence <= 1`.
- Infected area must be `0 <= infected_area_percent <= 100`.
- Inventory stock and prices cannot be negative.
- Required inventory quantity must be greater than zero.
- IDs must be positive where required.

Invalid request bodies return FastAPI validation errors with HTTP status `422`.

## 14. Error Handling

Common error responses:

| Status | Meaning |
|---|---|
| `401` | Missing, invalid, or expired token |
| `403` | User role not allowed |
| `404` | Requested record not found |
| `409` | Duplicate unique value, such as detection `session_id` |
| `422` | Request validation failed |

The backend avoids silent failures. If a linked detection or recommendation is
missing, the API returns an explicit error.

## 15. Logging

Logging is configured in:

```text
app/core/logging.py
```

The backend logs:

- Successful and failed authentication attempts.
- Detection uploads.
- Recommendation storage.
- Inventory checks.
- Inventory create, update, and delete operations.

This is simple structured logging suitable for a local prototype.

## 16. Example End-to-End Backend Flow

This is what happens during a normal backend demo:

1. Start the backend with Uvicorn.
2. Login as `admin` or `vendor`.
3. Create inventory items.
4. Upload a detection JSON from the Pi or Swagger UI.
5. Upload a treatment recommendation linked to that detection.
6. Call `/inventory/check` with required medicines.
7. Call `/dashboard/summary` to see detection and inventory summary data.

The backend database now contains:

- A detection record.
- A treatment recommendation record.
- Inventory item records.
- Inventory check history.

## 17. Important Design Choices

### Store Flattened Fields and Raw JSON

The detection payload is stored twice:

- Important fields are flattened into columns for easy filtering and dashboard
  summaries.
- The original JSON is stored in `raw_detection_json` for traceability and future
  compatibility.

This allows the backend to support dashboards now without losing the exact
Raspberry Pi upload structure.

### Keep Inventory Matching Deterministic

Medicine names are matched after lowercase and whitespace normalization only.

This avoids guessing. Synonym tables and fuzzy matching are useful later, but
they are not part of Phase 2.

### Keep Authentication Simple

The project needs login and roles, but not production-grade identity management.
So the backend uses local users, bcrypt password hashes, and JWT bearer tokens.

### Keep Telegram as a Scaffold

The requirements mention a notification endpoint, but full Telegram integration
belongs to a later phase. The endpoint exists so future code can integrate
without changing the API plan.

## 18. What Is Not Included in Phase 2

The backend intentionally does not include:

- ML model training.
- TensorFlow or TFLite inference.
- Camera capture.
- Rover movement control.
- OpenRouter API calls.
- Telegram bot delivery.
- Automatic spraying.
- GPS.
- Multi-vendor comparison.
- Order placement.
- Payment flow.
- Websocket streaming.
- Background task queues.
- Cloud deployment.
- Frontend dashboard UI.

These are future phases or explicitly excluded prototype features.

## 19. Troubleshooting

### `python` is not recognized

Install Python 3.11+ and make sure it is added to PATH. On Windows, the Python
installer has an "Add Python to PATH" option.

### Dependencies fail to install

Run:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If using a restricted network, dependency downloads may be blocked.

### Login works but protected APIs fail

Check that the request includes:

```http
Authorization: Bearer <access_token>
```

### Database changes are not visible

Make sure the server is running from the `backend` folder. The default SQLite
file is relative to the current working directory.

### Inventory check says unavailable

Check that the medicine name in the request matches the inventory item name.
Only lowercase and extra whitespace are normalized.

## 20. Demo Credentials

Default users are created on startup:

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | `admin` |
| `vendor` | `vendor123` | `vendor` |

These are for local prototype use only.

## 21. Summary

The Phase 2 backend is the local data and API foundation of the rover ecosystem.
It receives detection results, stores recommendation records, manages inventory,
checks treatment availability, and serves dashboard-ready summary data.

The implementation is intentionally modular so later phases can add Raspberry Pi
syncing, OpenRouter recommendation generation, real Telegram notifications, ML
inference, and dashboard UI without rewriting the backend foundation.
