"""
Pydantic schemas for the submit endpoint.
Defines request and response models for evaluation submission.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator

class EvaluacionRequest(BaseModel):
    """
    Request schema for submitting a new evaluation.
    """
    edad: int = Field(..., ge=1, le=120, description="User's age (1-120)")
    sexo: str = Field(..., pattern="^[MF]$", description="User's sex (M/F)")
    respuestas: List[bool] = Field(..., min_items=40, max_items=40, description="40 SCQ questionnaire responses")
    acepto_consentimiento: bool = Field(..., description="User consent acceptance")
    
    @validator('respuestas')
    def validate_responses(cls, v):
        """Validate that exactly 40 responses are provided."""
        if len(v) != 40:
            raise ValueError('Exactly 40 responses are required')
        return v
    
    @validator('sexo')
    def validate_sex(cls, v):
        """Validate sex value."""
        if v not in ['M', 'F']:
            raise ValueError('Sex must be either M or F')
        return v.upper()
    
    class Config:
        schema_extra = {
            "example": {
                "edad": 8,
                "sexo": "M",
                "respuestas": [True, False, True] + [False] * 37,  # 40 responses total
                "acepto_consentimiento": True
            }
        }

class PredictionResult(BaseModel):
    """
    Schema for prediction results.
    """
    probability: float = Field(..., ge=0.0, le=1.0, description="Risk probability (0.0 to 1.0)")
    risk_level: str = Field(..., description="Risk level category (Low/Medium/High)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    interpretation: str = Field(..., description="Human-readable interpretation")

class EvaluacionResponse(BaseModel):
    """
    Response schema for successful evaluation submission.
    """
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    evaluation_id: int = Field(..., description="Database ID of the saved evaluation")
    prediction: PredictionResult = Field(..., description="Risk prediction results")
    timestamp: datetime = Field(..., description="Evaluation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Evaluación guardada exitosamente",
                "evaluation_id": 123,
                "prediction": {
                    "probability": 0.35,
                    "risk_level": "Medium",
                    "confidence": 0.78,
                    "interpretation": "Riesgo moderado de trastornos del neurodesarrollo"
                },
                "timestamp": "2024-01-15T10:30:00"
            }
        }

class ErrorResponse(BaseModel):
    """
    Schema for error responses.
    """
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": "Validation error",
                "detail": "Age must be between 1 and 120"
            }
        }

class EvaluacionSummary(BaseModel):
    """
    Schema for evaluation summary (used in list endpoints).
    """
    id: int = Field(..., description="Evaluation ID")
    edad: int = Field(..., description="User's age")
    sexo: str = Field(..., description="User's sex")
    riesgo_estimado: float = Field(..., description="Estimated risk probability")
    fecha: datetime = Field(..., description="Evaluation date")
    acepto_consentimiento: bool = Field(..., description="Consent status")
    
    class Config:
        from_attributes = True  # For SQLAlchemy model compatibility

class EvaluacionDetail(EvaluacionSummary):
    """
    Schema for detailed evaluation view (includes responses).
    """
    respuestas: List[bool] = Field(..., description="SCQ questionnaire responses")
    
    class Config:
        from_attributes = True