# Workflow

## Phase 6 end-to-end workflow

Phase 6 executes a single scan as a sequence of coordinated stages. The workflow is implemented in `phase6/controller.py` via `Phase6WorkflowController.run_scan()`.

```text
Grid Movement
→ Stop
→ Capture
→ Classification
→ Severity Estimation
→ Treatment
→ Backend Sync
→ Inventory Check
→ Telegram Notification
→ Session Persistence
```

## Step-by-step flow

1. **Grid Movement**
   - `GridMovementController.move_to_grid_position(row_index, plant_index)` is invoked if a grid controller is supplied.
   - This abstracts rover movement to a target plant position.
2. **Stop**
   - `GridMovementController.stop()` is called immediately after movement.
   - This ensures the rover halts before capture.
3. **Capture**
   - `CameraCapture.capture(session_id, source_image)` obtains an image.
   - If `source_image` is provided, the file is copied into the capture directory.
   - Otherwise, the code attempts capture via Picamera2 and falls back to OpenCV.
4. **Classification**
   - `run_tflite_prediction()` from Phase 4 runs disease classification on the captured image.
   - `build_detection_payload()` constructs the detection JSON payload.
5. **Severity Estimation**
   - Phase 6 passes the inference payload into the treatment generation path.
   - Severity-related metadata is included in the detection payload and contributes to treatment recommendation.
6. **Treatment**
   - `OpenRouterClient.generate_treatment()` is called with the transformed detection input.
   - The result is persisted as `treatment_json` in SQLite.
7. **Backend Sync**
   - If configured, `BackendClient.upload_detection()` and `upload_recommendation()` sync the detection and treatment data.
8. **Inventory Check**
   - `BackendClient.check_inventory()` verifies whether recommended inputs are available.
9. **Telegram Notification**
   - `TelegramClient.send_message()` sends the farmer alert message.
   - If Telegram delivery fails, the failure is recorded but earlier workflow state is preserved.
10. **Session Persistence**
    - Each workflow stage updates the SQLite session row through `LocalSessionStore.update_session()`.

## Architecture sequence

```text
[Grid Controller] -> [Phase6WorkflowController] -> [CameraCapture] -> [Phase4 Inference]
        |                |                   |
        v                v                   v
   move_to_grid_position   capture         run_tflite_prediction
        |                |                   |
        v                |                   v
       stop              |            build_detection_payload
                         v                   |
                   session image             v
                                          treatment flow
```

## Workflow details

- `run_scan()` always creates a session row before capture.
- Capture stage stores `image_path` and `sync_status = captured`.
- Detection stage produces `detection_json` and updates status to `detected`.
- Treatment stage updates status to `treated`.
- Backend sync updates status to `backend_synced` or `backend_skipped`.
- Telegram stage sets final `sync_status` to `completed`, `completed_with_errors`, or `telegram_failed`.

## Inputs

- `farm_size_acres`
- `number_of_plants`
- `country`
- `language`
- `row_index`
- `plant_index`
- `source_image`
- `sync_backend`
- `send_telegram`

## Outputs

- Final `WorkflowResult`
- SQLite session row containing all intermediate JSON payloads and statuses
- Telegram message payload if enabled
- Backend sync result objects if backend integration is configured

## Phase 6 validation checklist

Before moving to Phase 7, verify the following:

- [ ] `phase6.main` runs successfully from the workspace root.
- [ ] `Phase6Settings` loads environment variables and Phase 4 config correctly.
- [ ] `GridMovementController` integration is available and a no-op fallback works.
- [ ] `CameraCapture` handles both live capture and `--source-image` mode.
- [ ] Inference runs through `run_tflite_prediction()` and `build_detection_payload()`.
- [ ] Treatment recommendation generation is executed and persisted.
- [ ] Backend sync updates detection, recommendation, and inventory JSON when configured.
- [ ] Telegram notifications are sent when enabled, and failures are recorded.
- [ ] Session data is stored in SQLite with updated `sync_status` values.
- [ ] Existing end-to-end Phase 6 tests pass.

