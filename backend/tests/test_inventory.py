from fastapi.testclient import TestClient


def test_inventory_crud_flow(
    client: TestClient,
    admin_headers: dict[str, str],
    future_expiry_date: str,
) -> None:
    create_response = client.post(
        "/inventory",
        headers=admin_headers,
        json={
            "medicine_name": "example fungicide name",
            "stock_quantity_kg": 5.0,
            "price_per_kg": 420.0,
            "expiry_date": future_expiry_date,
        },
    )
    assert create_response.status_code == 201
    item_id = create_response.json()["id"]

    list_response = client.get("/inventory", headers=admin_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.put(
        f"/inventory/{item_id}",
        headers=admin_headers,
        json={"stock_quantity_kg": 4.0},
    )
    assert update_response.status_code == 200
    assert update_response.json()["stock_quantity_kg"] == 4.0

    delete_response = client.delete(f"/inventory/{item_id}", headers=admin_headers)
    assert delete_response.status_code == 204


def test_viewer_cannot_create_inventory_item(
    client: TestClient,
    viewer_headers: dict[str, str],
    future_expiry_date: str,
) -> None:
    response = client.post(
        "/inventory",
        headers=viewer_headers,
        json={
            "medicine_name": "restricted item",
            "stock_quantity_kg": 5.0,
            "price_per_kg": 420.0,
            "expiry_date": future_expiry_date,
        },
    )

    assert response.status_code == 403


def test_inventory_check_computes_availability_and_price(
    client: TestClient,
    admin_headers: dict[str, str],
    future_expiry_date: str,
) -> None:
    client.post(
        "/inventory",
        headers=admin_headers,
        json={
            "medicine_name": "example fungicide name",
            "stock_quantity_kg": 5.0,
            "price_per_kg": 420.0,
            "expiry_date": future_expiry_date,
        },
    )

    response = client.post(
        "/inventory/check",
        headers=admin_headers,
        json={
            "session_id": "sess_20260523_001",
            "vendor_id": "vendor_001",
            "items": [
                {
                    "medicine_name": "example fungicide name",
                    "required_quantity_kg": 1.25,
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_estimated_price"] == 525.0
    assert body["items"][0]["is_available"] is True
    assert body["items"][0]["available_quantity_kg"] == 5.0


def test_inventory_check_reports_missing_item_as_unavailable(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.post(
        "/inventory/check",
        headers=admin_headers,
        json={
            "session_id": "sess_20260523_001",
            "items": [
                {
                    "medicine_name": "unknown medicine",
                    "required_quantity_kg": 1.25,
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["is_available"] is False
    assert body["items"][0]["unit_price"] is None
    assert body["total_estimated_price"] == 0.0
