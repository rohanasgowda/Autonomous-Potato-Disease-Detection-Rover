from __future__ import annotations

import json

from phase3.app.schemas.treatment import TreatmentAgentInput, TreatmentAgentOutput


SYSTEM_PROMPT = (
    "You are a treatment recommendation agent for a college prototype plant "
    "disease detection rover. Return only valid JSON that exactly matches the "
    "provided JSON Schema. Do not include markdown, comments, explanations, "
    "or prose outside the JSON object. Use kg/acre quantities only. Keep "
    "recommendations suitable for demonstration and inventory planning, not "
    "certified agricultural advice. Include a clear prototype disclaimer."
)


def output_json_schema() -> dict:
    return TreatmentAgentOutput.model_json_schema()


def render_treatment_user_prompt(agent_input: TreatmentAgentInput) -> str:
    payload_json = json.dumps(agent_input.model_dump(mode="json"), indent=2, sort_keys=True)
    schema_json = json.dumps(output_json_schema(), indent=2, sort_keys=True)
    return (
        "Generate a treatment recommendation for the following validated "
        "treatment-agent input JSON.\n\n"
        "Input JSON:\n"
        f"{payload_json}\n\n"
        "Required output JSON Schema:\n"
        f"{schema_json}\n\n"
        "Rules:\n"
        "1. Output one JSON object only.\n"
        "2. Do not add fields not present in the schema.\n"
        "3. Do not recommend quantities in any unit other than kg/acre.\n"
        "4. Include safety instructions for each recommendation.\n"
        "5. Include the prototype disclaimer."
    )

