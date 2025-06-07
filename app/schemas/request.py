"""
Pydantic schemas for prediction requests.
Updated for Pydantic V2 compatibility.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List

class InputData(BaseModel):
    """Schema for prediction input data"""
    responses: List[bool] = Field(..., description="40 boolean responses to SCQ questionnaire")
    age: int = Field(..., ge=1, le=120, description="User's age in years")
    sex: str = Field(..., description="User's sex (M or F)")
    
    @field_validator('responses')
    @classmethod
    def validate_responses_length(cls, v):
        if len(v) != 40:
            raise ValueError(f'Expected exactly 40 responses, got {len(v)}')
        return v
    
    @field_validator('sex')
    @classmethod
    def validate_sex(cls, v):
        if v.upper() not in ['M', 'F']:
            raise ValueError('Sex must be M or F')
        return v.upper()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "responses": [True, False] * 20,  # 40 responses
                "age": 8,
                "sex": "M"
            }
        }
    )

class PredictionResponse(BaseModel):
    """Schema for prediction response"""
    probability: float = Field(..., description="Risk probability (0.0 to 1.0)")
    risk_level: str = Field(..., description="Risk category (Low, Medium, High)")
    confidence: float = Field(..., description="Model confidence score")
    interpretation: str = Field(..., description="Human-readable interpretation")
    estimated_risk: str = Field(..., description="Risk percentage as string")
    status: str = Field(default="success", description="Response status")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "probability": 0.35,
                "risk_level": "Medium",
                "confidence": 0.78,
                "interpretation": "Riesgo moderado de trastornos del neurodesarrollo",
                "estimated_risk": "35.00%",
                "status": "success"
            }
        }
    )