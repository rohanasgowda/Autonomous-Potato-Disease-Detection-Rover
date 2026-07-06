from phase3.app.notifications.telegram import build_farmer_message
from phase3.app.schemas.detection import DetectionCreate
from phase3.app.schemas.inventory import InventoryCheckResponse
from phase3.app.schemas.treatment import TreatmentAgentOutput


def test_farmer_message_includes_required_information(
    sample_detection_payload,
    sample_treatment_output,
):
    detection = DetectionCreate.model_validate(sample_detection_payload)
    treatment = TreatmentAgentOutput.model_validate(sample_treatment_output)
    inventory = InventoryCheckResponse.model_validate(
        {
            "session_id": "sess_20260523_001",
            "vendor_id": "vendor_001",
            "items": [
                {
                    "medicine_name": "example fungicide name",
                    "required_quantity_kg": 1.25,
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

    message = build_farmer_message(detection, treatment, inventory)

    assert "Crop: Potato" in message
    assert "Disease: Late Blight" in message
    assert "Severity: Moderate (14.6% infected area)" in message
    assert "Grid position: row 1, plant 7" in message
    assert "example fungicide name - 1.25 kg/acre" in message
    assert "Availability: Available" in message
    assert "Estimated price: INR 525.00" in message
    assert "Wear gloves and mask during application" in message
    assert treatment.disclaimer in message

