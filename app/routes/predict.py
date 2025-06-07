"""
Prediction endpoint for neurodevelopmental disorder risk assessment.
This endpoint provides predictions without storing data.
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.request import InputData, PredictionResponse
from app.models.predictor import predict_risk, get_model_info
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create router without prefix (will be added in main.py)
router = APIRouter()

@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Make risk prediction",
    description="Make a neurodevelopmental disorder risk prediction without saving to database",
    responses={
        200: {
            "description": "Successful prediction",
            "model": PredictionResponse
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": {"detail": "Validation error: Expected exactly 40 responses"}
                }
            }
        },
        503: {
            "description": "Model not available",
            "content": {
                "application/json": {
                    "example": {"detail": "Prediction model is not available"}
                }
            }
        }
    }
)
async def predict(data: InputData):
    """
    Make a risk prediction based on input data.
    
    This endpoint:
    - Validates input data (40 SCQ responses, age, sex)
    - Uses ML model to predict risk
    - Returns probability, risk level, and interpretation
    - Does NOT store any data
    
    Args:
        data: Input data containing responses, age, and sex
        
    Returns:
        PredictionResponse with risk assessment
    """
    try:
        # Check if model is available
        model_info = get_model_info()
        if not model_info.get("is_loaded"):
            logger.error("Model not loaded")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Prediction model is not available"
            )
        
        # Make prediction
        result = predict_risk(
            responses=data.responses,
            age=data.age,
            sex=data.sex
        )
        
        # Format response
        response = PredictionResponse(
            probability=result['probability'],
            risk_level=result['risk_level'],
            confidence=result['confidence'],
            interpretation=result['interpretation'],
            estimated_risk=f"{result['probability']*100:.2f}%",
            status="success"
        )
        
        logger.info(f"Prediction completed successfully: {result['risk_level']} risk")
        return response
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during prediction"
        )