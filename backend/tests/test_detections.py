from fastapi.testclient import TestClient


def test_detection_upload_preserves_raw_json(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_detection_payload: dict,
) -> None:
    response = client.post(
        "/detections",
        headers=admin_headers,
        json=sample_detection_payload,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["session_id"] == sample_detection_payload["session_id"]
    assert body["row_index"] == 1
    assert body["severity_label"] == "moderate"
    assert body["raw_detection_json"]["grid_position"]["plant_index"] == 7


def test_duplicate_detection_session_id_is_rejected(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_detection_payload: dict,
) -> None:
    first = client.post("/detections", headers=admin_headers, json=sample_detection_payload)
    second = client.post("/detections", headers=admin_headers, json=sample_detection_payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_detection_validation_rejects_invalid_confidence(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_detection_payload: dict,
) -> None:
    sample_detection_payload["confidence"] = 1.5

    response = client.post("/detections", headers=admin_headers, json=sample_detection_payload)

    assert response.status_code == 422
