# Phase 3 Treatment Agent and Notification Module

This folder implements only Phase 3 of the Plant Disease Detection Rover prototype.
It runs on the Raspberry Pi side after local disease detection has already produced
the documented detection JSON.

The module:

- validates Raspberry Pi detection JSON,
- transforms it into the documented treatment-agent input JSON,
- calls OpenRouter with JSON Schema structured output,
- validates the treatment JSON,
- stores local request/response audit records,
- uploads detection and recommendation records to the Phase 2 FastAPI backend,
- checks single-vendor inventory through the backend,
- and sends a Telegram message to the farmer when Telegram credentials are configured.

It does not implement ML inference, camera control, rover movement, GPS, dashboards,
orders, payments, multi-vendor selection, or certified agricultural advice.

## Quick Setup

```powershell
cd phase3
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set at least `OPENROUTER_API_KEY`. Backend and Telegram settings
are optional for isolated testing, but are required for the full demo path.

## Run

From the workspace root:

```powershell
python -m phase3.app.main --input phase3/examples/detection_sample.json --farm-size-acres 1.0 --number-of-plants 500
```

For OpenRouter-only testing without backend sync or Telegram delivery:

```powershell
python -m phase3.app.main --input phase3/examples/detection_sample.json --farm-size-acres 1.0 --number-of-plants 500 --skip-backend --skip-telegram
```

Local audit records are stored in `logs/phase3_audit.db` by default.

## Tests

```powershell
python -m pytest phase3/tests
```

## Documentation

Detailed technical documentation is available in:

- `docs/PHASE3_TECHNICAL_DOCUMENTATION.md`

## Phase 3 Part 2 Frontend

A friendly vendor inventory page is available in `frontend/`. It lets a
vendor/admin log in, add/edit/delete stock, and import CSV inventory rows without
using backend code or Swagger manually.

```powershell
.\phase3\.venv\Scripts\python.exe -m http.server 5500 -d phase3\frontend
```

Open `http://localhost:5500` while the backend is running on
`http://localhost:8000`.
