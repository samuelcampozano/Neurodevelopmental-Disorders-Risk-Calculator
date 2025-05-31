from pydantic import BaseModel, Field, validator
from typing import List

class InputData(BaseModel):
    """Schema for prediction input data"""
    responses: List[bool] = Field(..., description="40 boolean responses to SCQ questionnaire")
    age: int = Field(..., ge=1, le=120, description="User's age in years")
    sex: str = Field(..., description="User's sex (M or F)")
    
    @validator('responses')
    def validate_responses_length(cls, v):
        if len(v) != 40:
            raise ValueError(f'Expected exactly 40 responses, got {len(v)}')
        return v
    
    @validator('sex')
    def validate_sex(cls, v):
        if v.upper() not in ['M', 'F']:
            raise ValueError('Sex must be M or F')
        return v.upper()

class PredictionResponse(BaseModel):
    """Schema for prediction response"""
    probability: float = Field(..., description="Risk probability (0.0 to 1.0)")
    risk_level: str = Field(..., description="Risk category (Low, Medium, High)")
    confidence: float = Field(..., description="Model confidence score")
    interpretation: str = Field(..., description="Human-readable interpretation")
    estimated_risk: str = Field(..., description="Risk percentage as string")
    status: str = Field(default="success", description="Response status")