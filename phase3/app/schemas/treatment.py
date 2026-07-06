from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LocationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    country: str = Field(default="India", min_length=1, max_length=100)
    language: str = Field(default="English", min_length=1, max_length=50)


class TreatmentAgentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crop: str = Field(min_length=1, max_length=100)
    disease: str = Field(min_length=1, max_length=150)
    severity_label: str = Field(min_length=1, max_length=50)
    infected_area_percent: float = Field(ge=0, le=100)
    farm_size_acres: float = Field(gt=0)
    number_of_plants: int = Field(gt=0)
    location_context: LocationContext = Field(default_factory=LocationContext)
    required_units: Literal["kg/acre"] = "kg/acre"


class TreatmentRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1, max_length=50)
    medicine_name: str = Field(min_length=1, max_length=200)
    active_ingredient: str = Field(min_length=1, max_length=200)
    quantity_kg_per_acre: float = Field(gt=0)
    application_frequency: str = Field(min_length=1, max_length=400)
    safety_instructions: list[str] = Field(min_length=1, max_length=8)

    @field_validator("safety_instructions")
    @classmethod
    def safety_instructions_must_be_non_empty(cls, values: list[str]) -> list[str]:
        for value in values:
            if not value.strip():
                raise ValueError("safety instruction cannot be blank")
        return values


class TreatmentAgentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crop: str = Field(min_length=1, max_length=100)
    disease: str = Field(min_length=1, max_length=150)
    severity_label: str = Field(min_length=1, max_length=50)
    recommendations: list[TreatmentRecommendation] = Field(min_length=1, max_length=5)
    disclaimer: str = Field(min_length=1, max_length=500)

