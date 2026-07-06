# Deployment

## Environment and prerequisites

Phase 6 requires the repository-local Phase 3 and Phase 4 packages to be importable. The workspace root should be on `PYTHONPATH` or installed in the target environment.

Required runtime resources:

- Phase 4 model file referenced by `PHASE6_MODEL_PATH`
- Phase 4 labels file referenced by `PHASE6_LABELS_PATH`
- Phase 4 configuration file loaded by `phase6.settings.Phase6Settings`

### Recommended file layout

```text
<workspace>/phase6/
<workspace>/phase4/runs/mobilenetv3/model.tflite
<workspace>/phase4/runs/mobilenetv3/labels.json
<workspace>/phase4/configs/<config>.json
```

## Configuration options

Phase 6 settings are loaded from environment variables and command-line arguments.

### Phase 6 environment variables

- `PHASE6_MODEL_PATH` — path to Phase 4 TFLite model.
- `PHASE6_LABELS_PATH` — path to Phase 4 labels JSON.
- `PHASE6_CAPTURE_DIR` — image capture directory, default `captures`.
- `PHASE6_LOCAL_DB_PATH` — SQLite file path, default `logs/phase6_sessions.db`.
- `FARM_SIZE_ACRES` — default farm size, default `1.0`.
- `NUMBER_OF_PLANTS` — default plant count, default `500`.
- `COUNTRY` — default language country, default `India`.
- `LANGUAGE` — default language, default `English`.
- `ROW_INDEX` — default grid row index, default `0`.
- `PLANT_INDEX` — default grid plant index, default `0`.
- `CAMERA_INDEX` — OpenCV camera index, default `0`.
- `CAMERA_WARMUP_SECONDS` — camera warmup delay, default `0.2`.

### Phase 3 / Phase 4 configuration

- Phase 6 loads `Phase3Settings` with `phase3/app/config/settings.py` from the same environment.
- Phase 6 loads `Phase4Config` via `phase4.app.config.load_config()`.
- `max_local_sessions` is taken from Phase 4 config and used by `LocalSessionStore`.

## Deployment steps

1. Ensure the Python environment can import both `phase3` and `phase4` package modules.
2. Install any required system dependencies for camera capture if using live capture.
3. Set or source the required environment variables.
4. Run `python -m phase6.main` from the workspace root.

## Execution examples

Run a normal Phase 6 scan:

```bash
python -m phase6.main --farm-size-acres 1.0 --number-of-plants 500
```

Run using a saved image instead of the live camera:

```bash
python -m phase6.main --source-image captures/sample.jpg --skip-backend --skip-telegram
```

Override grid position from CLI:

```bash
python -m phase6.main --row-index 2 --plant-index 3
```

Skip backend sync or Telegram notification when testing:

```bash
python -m phase6.main --skip-backend --skip-telegram
```

## Raspberry Pi deployment notes

- If a Pi camera is available, Phase 6 camera capture attempts to use Picamera2 first and falls back to OpenCV.
- If hardware movement integration is required, provide a concrete implementation of `phase6.grid.GridMovementController`.
- The default grid movement controller in Phase 6 is a no-op, so the workflow remains hardware-agnostic.
- Ensure the capture directory and SQLite database directory are writable by the running user.

