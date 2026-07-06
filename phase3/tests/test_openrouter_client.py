import json

import pytest

from phase3.app.clients.openrouter import OpenRouterClient, parse_openrouter_response
from phase3.app.schemas.detection import DetectionCreate
from phase3.app.services.transformer import detection_to_treatment_input
from phase3.app.utils.errors import StructuredOutputError
from phase3.app.utils.retry import RetryPolicy


def _openrouter_response(content):
    return {"choices": [{"message": {"content": content}}]}


def test_parse_openrouter_response_accepts_valid_json_string(sample_treatment_output):
    parsed = parse_openrouter_response(
        _openrouter_response(json.dumps(sample_treatment_output))
    )

    assert parsed.recommendations[0].medicine_name == "example fungicide name"


def test_parse_openrouter_response_accepts_json_object(sample_treatment_output):
    parsed = parse_openrouter_response(_openrouter_response(sample_treatment_output))

    assert parsed.crop == "potato"


def test_parse_openrouter_response_rejects_malformed_json():
    with pytest.raises(StructuredOutputError):
        parse_openrouter_response(_openrouter_response("not json"))


def test_parse_openrouter_response_rejects_schema_mismatch(sample_treatment_output):
    del sample_treatment_output["recommendations"][0]["quantity_kg_per_acre"]

    with pytest.raises(StructuredOutputError):
        parse_openrouter_response(_openrouter_response(sample_treatment_output))


def test_openrouter_request_uses_structured_json_schema(sample_detection_payload):
    detection = DetectionCreate.model_validate(sample_detection_payload)
    agent_input = detection_to_treatment_input(detection, 1.0, 500)
    client = OpenRouterClient(
        api_key="test",
        base_url="https://openrouter.ai/api/v1",
        model="google/gemini-3.1-flash-lite",
        temperature=0.2,
        max_tokens=1800,
        timeout_seconds=5,
        retry_policy=RetryPolicy(attempts=1, backoff_seconds=0),
    )

    payload = client.build_request_payload(agent_input)

    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 1800
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert "recommendations" in payload["response_format"]["json_schema"]["schema"]["properties"]
