from pydantic import BaseModel
from typing import Optional

class ValidationResult(BaseModel):
    indicator: str
    measured_value: float
    reference_value: Optional[float]
    absolute_error: Optional[float]
    percentage_error: Optional[float]
    is_valid: bool
    status_message: str

class ValidationSummary(BaseModel):
    neighborhood_id: int
    city: str
    district: str
    overall_accuracy: Optional[float]
    validations: list[ValidationResult]
