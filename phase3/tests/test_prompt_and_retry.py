import pytest

from phase3.app.prompts.treatment_prompt import render_treatment_user_prompt
from phase3.app.schemas.detection import DetectionCreate
from phase3.app.services.transformer import detection_to_treatment_input
from phase3.app.utils.retry import RetryPolicy


def test_prompt_contains_input_schema_and_json_only_rules(sample_detection_payload):
    detection = DetectionCreate.model_validate(sample_detection_payload)
    agent_input = detection_to_treatment_input(detection, 1.0, 500)

    prompt = render_treatment_user_prompt(agent_input)

    assert '"required_units": "kg/acre"' in prompt
    assert "Required output JSON Schema" in prompt
    assert "Output one JSON object only" in prompt
    assert "Do not add fields not present in the schema" in prompt


def test_retry_policy_retries_until_success():
    calls = {"count": 0}

    def flaky():
        calls["count"] += 1
        if calls["count"] < 3:
            raise RuntimeError("temporary")
        return "ok"

    result = RetryPolicy(attempts=3, backoff_seconds=0).run("test", flaky)

    assert result == "ok"
    assert calls["count"] == 3


def test_retry_policy_raises_last_error():
    def always_fails():
        raise RuntimeError("still failing")

    with pytest.raises(RuntimeError, match="still failing"):
        RetryPolicy(attempts=2, backoff_seconds=0).run("test", always_fails)

