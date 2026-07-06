from __future__ import annotations

import json
import logging
from typing import Any
from uuid import uuid4

import httpx
from pydantic import ValidationError

from phase3.app.prompts.treatment_prompt import (
    SYSTEM_PROMPT,
    output_json_schema,
    render_treatment_user_prompt,
)
from phase3.app.schemas.treatment import TreatmentAgentInput, TreatmentAgentOutput
from phase3.app.utils.errors import ConfigurationError, StructuredOutputError
from phase3.app.utils.retry import RetryPolicy


logger = logging.getLogger(__name__)


class OpenRouterClient:
    def __init__(
        self,
        api_key: str | None,
        base_url: str,
        model: str,
        temperature: float,
        max_tokens: int,
        timeout_seconds: float,
        retry_policy: RetryPolicy,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.retry_policy = retry_policy

    def build_request_payload(self, agent_input: TreatmentAgentInput) -> dict[str, Any]:
        schema = output_json_schema()
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": render_treatment_user_prompt(agent_input)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "treatment_agent_output",
                    "strict": True,
                    "schema": schema,
                },
            },
        }

    def generate_treatment(
        self,
        agent_input: TreatmentAgentInput,
    ) -> tuple[TreatmentAgentOutput, dict[str, Any], dict[str, Any]]:
        if not self.api_key:
            raise ConfigurationError("OPENROUTER_API_KEY is required for treatment generation.")

        request_payload = self.build_request_payload(agent_input)
        trace_id = str(uuid4())
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "Plant Disease Detection Rover Phase 3",
        }

        def send() -> dict[str, Any]:
            logger.info(
                "Calling OpenRouter",
                extra={"_trace_id": trace_id, "_model": self.model},
            )
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=request_payload,
                )
                response.raise_for_status()
                return response.json()

        raw_response = self.retry_policy.run("openrouter.chat.completions", send)
        parsed = parse_openrouter_response(raw_response)
        return parsed, request_payload, raw_response


def parse_openrouter_response(raw_response: dict[str, Any]) -> TreatmentAgentOutput:
    try:
        message = raw_response["choices"][0]["message"]
        content = message.get("content")
    except (KeyError, IndexError, TypeError) as exc:
        raise StructuredOutputError("OpenRouter response did not contain choices[0].message.content.") from exc

    if isinstance(content, dict):
        parsed_json = content
    elif isinstance(content, str):
        try:
            parsed_json = json.loads(content)
        except json.JSONDecodeError as exc:
            raise StructuredOutputError("OpenRouter response content was not valid JSON.") from exc
    else:
        raise StructuredOutputError("OpenRouter response content was neither a JSON string nor object.")

    try:
        return TreatmentAgentOutput.model_validate(parsed_json)
    except ValidationError as exc:
        raise StructuredOutputError("OpenRouter JSON did not match TreatmentAgentOutput schema.") from exc
