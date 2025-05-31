from fastapi import APIRouter, HTTPException, status
from app.schemas.request import InputData, PredictionResponse
from app.models.predictor import load_model, predict_risk

# Create router without prefix (will be added in main.py)
router = APIRouter()

# Load model once at startup
try:
    model = load_model()
except Exception as e:
    print(f"Warning: Could not load model: {e}")
    model = None

@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Make risk prediction",
    description="Make a neurodevelopmental disorder risk prediction without saving to database"
)
def predict(data: InputData):
    """
    Make a risk prediction based on input data.
    
    Args:
        data: Input data containing responses, age, and sex
        
    Returns:
        Dictionary with estimated risk and details
    """
    try:
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Prediction model is not available"
            )
        
        # Call predict_risk with correct parameters
        result = predict_risk(
            responses=data.responses,
            age=data.age,
            sex=data.sex
        )
        
        # Add formatted risk percentage
        result["estimated_risk"] = f"{result['probability']*100:.2f}%"
        result["status"] = "success"
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )