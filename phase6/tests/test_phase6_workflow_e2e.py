import json
from pathlib import Path

import phase6.controller as controller_module
from phase3.app.schemas.inventory import InventoryCheckResponse
from phase3.app.schemas.pipeline import TelegramDeliveryResult
from phase3.app.schemas.treatment import TreatmentAgentOutput
from phase4.app.config import Phase4Config
from phase4.app.inference import PredictionResult
from phase6.camera import CameraCapture
from phase6.controller import Phase6WorkflowController
from phase6.storage import LocalSessionStore


class FakeOpenRouterClient:
    def __init__(self, treatment):
        self.treatment = treatment

    def generate_treatment(self, agent_input):
        return (
            self.treatment,
            {"input": agent_input.model_dump(mode="json")},
            {"choices": [{"message": {"content": self.treatment.model_dump(mode="json")}}]},
        )


class FakeBackendClient:
    is_configured = True

    def upload_detection(self, detection):
        self.detection = detection
        return {"id": 101, "session_id": detection.session_id}

    def upload_recommendation(self, detection_id, model_name, raw_request, raw_response):
        self.recommendation = {
            "detection_id": detection_id,
            "model_name": model_name,
            "raw_request": raw_request,
            "raw_response": raw_response,
        }
        return {"id": 202, "detection_session_id": detection_id}

    def check_inventory(self, request):
        self.inventory_request = request
        return InventoryCheckResponse.model_validate(
            {
                "session_id": request.session_id,
                "vendor_id": request.vendor_id,
                "items": [
                    {
                        "medicine_name": request.items[0].medicine_name,
                        "required_quantity_kg": request.items[0].required_quantity_kg,
                        "available_quantity_kg": 10.0,
                        "is_available": True,
                        "unit_price": 100.0,
                        "estimated_total_price": 125.0,
                        "expiry_date": "2027-02-15",
                    }
                ],
                "total_estimated_price": 125.0,
                "currency": "INR",
            }
        )


class FakeTelegramClient:
    def send_message(self, message):
        self.message = message
        return TelegramDeliveryResult(
            attempted=True,
            delivered=True,
            detail="sent",
            response_json={"ok": True},
        )


def test_phase6_workflow_runs_capture_to_telegram(monkeypatch, tmp_path):
    sample_detection = json.loads(Path("phase3/examples/detection_sample.json").read_text())
    treatment = TreatmentAgentOutput.model_validate(
        json.loads(Path("phase3/examples/treatment_output_sample.json").read_text())
    )
    source_image = tmp_path / "source.jpg"
    source_image.write_bytes(b"image")

    monkeypatch.setattr(controller_module, "generate_session_id", lambda: "sess_phase6")
    monkeypatch.setattr(
        controller_module,
        "run_tflite_prediction",
        lambda **kwargs: PredictionResult(
            class_name="potato_late_blight",
            crop="potato",
            disease="late_blight",
            confidence=0.92,
            inference_time_ms=10.0,
        ),
    )

    def fake_detection_payload(**kwargs):
        payload = dict(sample_detection)
        payload["session_id"] = "sess_phase6"
        payload["image"] = {
            "local_path": str(kwargs["image_path"]),
            "width": 1280,
            "height": 720,
        }
        payload["runtime"] = {"inference_time_ms": 10.0}
        return payload

    monkeypatch.setattr(controller_module, "build_detection_payload", fake_detection_payload)

    backend = FakeBackendClient()
    telegram = FakeTelegramClient()
    store = LocalSessionStore(tmp_path / "phase6.db", max_sessions=20)
    controller = Phase6WorkflowController(
        camera=CameraCapture(tmp_path / "captures"),
        store=store,
        phase4_config=Phase4Config(),
        model_path=tmp_path / "model.tflite",
        labels_path=tmp_path / "labels.json",
        openrouter_client=FakeOpenRouterClient(treatment),
        backend_client=backend,
        telegram_client=telegram,
        openrouter_model_name="fake-openrouter-model",
        backend_vendor_id="vendor_001",
    )

    result = controller.run_scan(
        farm_size_acres=1.0,
        number_of_plants=500,
        row_index=1,
        plant_index=7,
        source_image=source_image,
    )

    row = store.get_session("sess_phase6")
    assert result.sync_status == "completed"
    assert result.backend.detection_id == 101
    assert result.backend.recommendation_id == 202
    assert result.telegram.delivered is True
    assert row["detection_json"]["session_id"] == "sess_phase6"
    assert row["treatment_json"]["crop"] == "potato"
    assert row["inventory_json"]["items"][0]["is_available"] is True
    assert "Plant disease rover alert" in telegram.message


def test_phase6_workflow_calls_grid_movement_before_capture(monkeypatch, tmp_path):
    events: list[str] = []

    class FakeGridMovementController:
        def move_to_grid_position(self, row_index: int, plant_index: int) -> None:
            events.append(f"move:{row_index}:{plant_index}")

        def stop(self) -> None:
            events.append("stop")

    treatment = TreatmentAgentOutput.model_validate(
        json.loads(Path("phase3/examples/treatment_output_sample.json").read_text())
    )
    source_image = tmp_path / "source.jpg"
    source_image.write_bytes(b"image")

    monkeypatch.setattr(controller_module, "generate_session_id", lambda: "sess_phase6")
    monkeypatch.setattr(
        controller_module,
        "run_tflite_prediction",
        lambda **kwargs: PredictionResult(
            class_name="potato_late_blight",
            crop="potato",
            disease="late_blight",
            confidence=0.92,
            inference_time_ms=10.0,
        ),
    )

    def fake_detection_payload(**kwargs):
        payload = dict(json.loads(Path("phase3/examples/detection_sample.json").read_text()))
        payload["session_id"] = "sess_phase6"
        payload["image"] = {
            "local_path": str(kwargs["image_path"]),
            "width": 1280,
            "height": 720,
        }
        payload["runtime"] = {"inference_time_ms": 10.0}
        return payload

    monkeypatch.setattr(controller_module, "build_detection_payload", fake_detection_payload)

    backend = FakeBackendClient()
    telegram = FakeTelegramClient()
    store = LocalSessionStore(tmp_path / "phase6.db", max_sessions=20)
    controller = Phase6WorkflowController(
        camera=CameraCapture(tmp_path / "captures"),
        store=store,
        phase4_config=Phase4Config(),
        model_path=tmp_path / "model.tflite",
        labels_path=tmp_path / "labels.json",
        openrouter_client=FakeOpenRouterClient(treatment),
        backend_client=backend,
        telegram_client=telegram,
        openrouter_model_name="fake-openrouter-model",
        backend_vendor_id="vendor_001",
        grid_controller=FakeGridMovementController(),
    )

    result = controller.run_scan(
        farm_size_acres=1.0,
        number_of_plants=500,
        row_index=2,
        plant_index=3,
        source_image=source_image,
    )

    assert result.sync_status == "completed"
    assert events == ["move:2:3", "stop"]
