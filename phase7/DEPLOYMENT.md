# Deployment

This document summarises steps to deploy the prototype for a live demo or field run.

Raspberry Pi deployment (summary)
1. Copy repository or required phase folders (`phase4`, `phase6`, `phase3` if using OpenRouter client) to the Pi.
2. Install a Python virtual environment and runtime dependencies. Prefer `tflite-runtime` over full TensorFlow on Pi.
3. Place `phase4/runs/<run>/model.tflite` and `labels.json` on the Pi and set `PHASE6_MODEL_PATH` and `PHASE6_LABELS_PATH`.
4. Ensure the Pi camera is configured and accessible (Picamera2 or OpenCV).
5. Configure environment variables for backend, OpenRouter, and Telegram as required.
6. Run Phase 6: `python -m phase6.main --source-image captures/sample.jpg` or use live camera options.

Camera setup
- For Pi camera use Picamera2 where available; code falls back to OpenCV.
- Test capture with the `phase6.camera` helper or a simple OpenCV capture script.

Local database
- Phase 6 uses SQLite for session persistence. Default path `logs/phase6_sessions.db` or controlled via `PHASE6_LOCAL_DB_PATH`.

Model deployment
- Place the exported `.tflite` and `labels.json` in `phase4/runs/<run>/`.
- Use `tflite-runtime` on Pi. If full TensorFlow is used on a development machine, confirm `tflite` interpreter works the same.

Backend connectivity
- Backend must be reachable from the Pi (use laptop IP or host on same network). Set `BACKEND_BASE_URL` accordingly.

Telegram connectivity
- Obtain `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` and set these in environment. Send a test message using the `phase3` notification helper before running a full workflow.

Troubleshooting tips
- If inference fails, verify `labels.json` corresponds to `model.tflite` and that `PHASE6_MODEL_PATH` points correctly.
- If camera capture is black/blank, confirm camera permissions and warmup delays.
- If backend calls fail, verify network connectivity and that the backend is listening on the configured host/port.
