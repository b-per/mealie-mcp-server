from pydantic import BaseModel, field_validator


class FoodLabelAssignment(BaseModel):
    food_id: str
    label_id: str

    @field_validator("food_id", "label_id")
    @classmethod
    def require_identifier(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Food and label identifiers cannot be blank")
        return value
