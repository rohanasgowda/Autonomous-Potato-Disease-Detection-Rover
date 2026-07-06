from __future__ import annotations

from phase3.app.schemas.detection import DetectionCreate
from phase3.app.schemas.inventory import InventoryCheckRequest, InventoryCheckRequestItem
from phase3.app.schemas.treatment import LocationContext, TreatmentAgentInput, TreatmentAgentOutput


def detection_to_treatment_input(
    detection: DetectionCreate,
    farm_size_acres: float,
    number_of_plants: int,
    country: str = "India",
    language: str = "English",
) -> TreatmentAgentInput:
    return TreatmentAgentInput(
        crop=detection.crop,
        disease=detection.disease,
        severity_label=detection.severity.label,
        infected_area_percent=detection.severity.infected_area_percent,
        farm_size_acres=farm_size_acres,
        number_of_plants=number_of_plants,
        location_context=LocationContext(country=country, language=language),
        required_units="kg/acre",
    )


def treatment_to_inventory_request(
    treatment: TreatmentAgentOutput,
    agent_input: TreatmentAgentInput,
    session_id: str,
    vendor_id: str,
    treatment_recommendation_id: int | None = None,
) -> InventoryCheckRequest:
    return InventoryCheckRequest(
        session_id=session_id,
        vendor_id=vendor_id,
        treatment_recommendation_id=treatment_recommendation_id,
        items=[
            InventoryCheckRequestItem(
                medicine_name=item.medicine_name,
                required_quantity_kg=round(item.quantity_kg_per_acre * agent_input.farm_size_acres, 4),
            )
            for item in treatment.recommendations
        ],
    )

