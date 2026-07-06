# Installation

This file summarizes environment setup steps for each major phase. For full phase-specific instructions, consult the phase folders (`phase2`, `phase3`, `phase4`, `phase6`) and their README files.

Prerequisites
- Python 3.11+
- Git
- (For Raspberry Pi) Raspberry Pi OS, camera module and network access

General virtual environment steps (Windows PowerShell)

```powershell
cd "C:\Users\ROHAN A S GOWDA\OneDrive\Dokumen\D&I"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Phase 4 (ML + inference)
- Install: `pip install -r phase4/requirements.txt`.
- To train: `python -m phase4.app.train --config phase4/configs/default.json --dataset-dir dataset --output-dir phase4/runs/mobilenetv3`.
- To export TFLite: `python -m phase4.app.export_tflite --model phase4/runs/mobilenetv3/saved_model.keras --output phase4/runs/mobilenetv3/model.tflite`.

Phase 2 (Backend)
- Steps are documented in `backend/README.md` and `backend/PHASE2_BACKEND_DOCUMENTATION.md`.
- Example quick run:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Phase 3 (OpenRouter treatment agent)
- Configure `.env` from `phase3/.env.example` with `OPENROUTER_API_KEY`, backend URL and optional Telegram credentials.
- Install: `pip install -r phase3/requirements.txt`.
- Run example: `python -m phase3.app.main --input phase3/examples/detection_sample.json --farm-size-acres 1.0 --number-of-plants 500`.

Phase 6 (Raspberry Pi orchestration)
- Ensure `phase4` model and labels are available on the Pi (place `model.tflite` and `labels.json` in `phase4/runs/<run>/`).
- Install runtime requirements: prefer `tflite-runtime` on Pi for lower footprint, plus `opencv-python-headless` and `numpy`.

Environment variables
- Many modules use env variables. Examples: `PHASE6_MODEL_PATH`, `PHASE6_LABELS_PATH`, `OPENROUTER_API_KEY`, `BACKEND_BASE_URL`, `TELEGRAM_BOT_TOKEN`.
- Check phase configs and `.env.example` files for each phase.

Verification steps
- Backend: open `http://localhost:8000/docs` and run example requests.
- Phase 4 inference: run `python -m phase4.app.inference --model phase4/runs/mobilenetv3/model.tflite --labels phase4/runs/mobilenetv3/labels.json --image captures/sample.jpg` and confirm a detection JSON is produced.
- Phase 5 severity validation: `python -m phase4.app.validate_severity --image captures/sample.JPG --output-dir phase4/runs/severity_validation` and inspect mask images and `severity_summary.json`.
