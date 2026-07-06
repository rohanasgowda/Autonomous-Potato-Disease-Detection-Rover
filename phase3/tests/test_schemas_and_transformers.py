from pydantic import ValidationError
import pytest

from phase3.app.schemas.detection import DetectionCreate
from phase3.app.schemas.treatment import TreatmentAgentOutput
from phase3.app.services.transformer import (
    detection_to_treatment_input,
    treatment_to_inventory_request,
)


def test_detection_schema_accepts_documented_payload(sample_detection_payload):
    detection = DetectionCreate.model_validate(sample_detection_payload)

    assert detection.session_id == "sess_20260523_001"
    assert detection.severity.label == "moderate"


def test_detection_schema_rejects_extra_fields(sample_detection_payload):
    sample_detection_payload["unexpected"] = True

    with pytest.raises(ValidationError):
        DetectionCreate.model_validate(sample_detection_payload)


def test_detection_to_treatment_input_matches_documented_shape(sample_detection_payload):
    detection = DetectionCreate.model_validate(sample_detection_payload)
    agent_input = detection_to_treatment_input(detection, 1.0, 500)

    assert agent_input.model_dump(mode="json") == {
        "crop": "potato",
        "disease": "late_blight",
        "severity_label": "moderate",
        "infected_area_percent": 14.6,
        "farm_size_acres": 1.0,
        "number_of_plants": 500,
        "location_context": {"country": "India", "language": "English"},
        "required_units": "kg/acre",
    }


def test_inventory_request_multiplies_kg_per_acre_by_farm_size(
    sample_detection_payload,
    sample_treatment_output,
):
    detection = DetectionCreate.model_validate(sample_detection_payload)
    agent_input = detection_to_treatment_input(detection, 2.0, 500)
    treatment = TreatmentAgentOutput.model_validate(sample_treatment_output)

    request = treatment_to_inventory_request(
        treatment=treatment,
        agent_input=agent_input,
        session_id=detection.session_id,
        vendor_id="vendor_001",
        treatment_recommendation_id=10,
    )

    assert request.items[0].required_quantity_kg == 2.5
    assert request.items[1].required_quantity_kg == 4.0
    assert request.treatment_recommendation_id == 10

