from pydantic import BaseModel, Field


class EducationalPlan(BaseModel):
    response: str = Field(description="The complete educational summary/plan generated for the student.")
