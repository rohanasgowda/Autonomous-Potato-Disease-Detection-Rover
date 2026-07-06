import json

from phase3.app.notifications.telegram import TelegramClient
from phase3.app.schemas.inventory import InventoryCheckResponse
from phase3.app.schemas.pipeline import TelegramDeliveryResult
from phase3.app.schemas.treatment import TreatmentAgentOutput
from phase3.app.services.pipeline import TreatmentPipeline
from phase3.app.storage.audit_store import AuditStore


class FakeOpenRouterClient:
    def __init__(self, treatment: TreatmentAgentOutput):
        self.treatment = treatment

    def generate_treatment(self, agent_input):
        return (
            self.treatment,
            {"model": "fake", "input": agent_input.model_dump(mode="json")},
            {"choices": [{"message": {"content": self.treatment.model_dump(mode="json")}}]},
        )


class FakeBackendClient:
    is_configured = True

    def upload_detection(self, detection):
        return {"id": 11, "session_id": detection.session_id}

    def upload_recommendation(self, detection_id, model_name, raw_request, raw_response):
        return {"id": 22, "detection_session_id": detection_id}

    def check_inventory(self, request):
        return InventoryCheckResponse.model_validate(
            {
                "session_id": request.session_id,
                "vendor_id": request.vendor_id,
                "items": [
                    {
                        "medicine_name": request.items[0].medicine_name,
                        "required_quantity_kg": request.items[0].required_quantity_kg,
                        "available_quantity_kg": 5.0,
                        "is_available": True,
                        "unit_price": 420.0,
                        "estimated_total_price": 525.0,
                        "expiry_date": "2027-02-15",
                    }
                ],
                "total_estimated_price": 525.0,
                "currency": "INR",
            }
        )


class FakeTelegramClient(TelegramClient):
    def __init__(self):
        pass

    def send_message(self, message):
        self.message = message
        return TelegramDeliveryResult(
            attempted=True,
            delivered=True,
            detail="sent",
            response_json={"ok": True},
        )


def test_pipeline_persists_audit_and_returns_backend_results(
    tmp_path,
    sample_detection_payload,
    sample_treatment_output,
):
    treatment = TreatmentAgentOutput.model_validate(sample_treatment_output)
    audit_store = AuditStore(tmp_path / "audit.db")
    telegram = FakeTelegramClient()
    pipeline = TreatmentPipeline(
        openrouter_client=FakeOpenRouterClient(treatment),
        backend_client=FakeBackendClient(),
        telegram_client=telegram,
        audit_store=audit_store,
        model_name="fake-model",
        backend_vendor_id="vendor_001",
    )

    result = pipeline.run(sample_detection_payload, 1.0, 500)
    row = audit_store.get_run(result.run_id)

    assert result.backend.detection_id == 11
    assert result.backend.recommendation_id == 22
    assert result.telegram.delivered is True
    assert row["validation_status"] == "completed"
    parsed = json.loads(row["parsed_response_json"])
    assert parsed["crop"] == "potato"
    assert "Plant disease rover alert" in telegram.message

