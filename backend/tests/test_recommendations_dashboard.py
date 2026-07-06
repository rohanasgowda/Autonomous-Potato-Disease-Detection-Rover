from fastapi.testclient import TestClient


def test_recommendation_storage_and_dashboard_summary(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_detection_payload: dict,
    future_expiry_date: str,
) -> None:
    detection_response = client.post(
        "/detections",
        headers=admin_headers,
        json=sample_detection_payload,
    )
    detection_id = detection_response.json()["id"]

    recommendation_response = client.post(
        "/recommendations",
        headers=admin_headers,
        json={
            "detection_session_id": detection_id,
            "model_provider": "openrouter",
            "model_name": "google/gemini-3.1-flash-lite",
            "raw_request_json": {
                "crop": "potato",
                "disease": "late_blight",
                "severity_label": "moderate",
                "infected_area_percent": 14.6,
                "farm_size_acres": 1.0,
                "number_of_plants": 500,
                "location_context": {"country": "India", "language": "English"},
                "required_units": "kg/acre",
            },
            "raw_response_json": {
                "crop": "potato",
                "disease": "late_blight",
                "severity_label": "moderate",
                "recommendations": [
                    {
                        "type": "chemical",
                        "medicine_name": "example fungicide name",
                        "active_ingredient": "example active ingredient",
                        "quantity_kg_per_acre": 1.25,
                        "application_frequency": "Apply once every 7 days",
                        "safety_instructions": ["Wear gloves and mask"],
                    }
                ],
                "disclaimer": "Prototype recommendation.",
            },
        },
    )
    assert recommendation_response.status_code == 201
    recommendation_id = recommendation_response.json()["id"]

    get_response = client.get(f"/recommendations/{recommendation_id}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json()["raw_response_json"]["crop"] == "potato"

    client.post(
        "/inventory",
        headers=admin_headers,
        json={
            "medicine_name": "low stock medicine",
            "stock_quantity_kg": 0.5,
            "price_per_kg": 300.0,
            "expiry_date": future_expiry_date,
        },
    )

    summary_response = client.get("/dashboard/summary", headers=admin_headers)
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total_detections"] == 1
    assert summary["diseased_plants_count"] == 1
    assert summary["healthy_plants_count"] == 0
    assert summary["latest_detections"][0]["session_id"] == "sess_20260523_001"
    assert summary["low_stock_medicines"][0]["medicine_name"] == "low stock medicine"
