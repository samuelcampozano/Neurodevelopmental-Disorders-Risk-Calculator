"""
Routes for handling evaluation submissions and database operations.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.evaluacion import Evaluacion
from app.models.predictor import predict_risk
from app.schemas.submit import (
    EvaluacionRequest, 
    EvaluacionResponse, 
    ErrorResponse,
    EvaluacionSummary,
    EvaluacionDetail,
    PredictionResult
)

# Create router instance
router = APIRouter(
    prefix="/api/v1",
    tags=["evaluations"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)

@router.post(
    "/submit",
    response_model=EvaluacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit new evaluation",
    description="Submit a new neurodevelopmental disorder risk evaluation with SCQ responses"
)
async def submit_evaluation(
    request: EvaluacionRequest,
    db: Session = Depends(get_db)
) -> EvaluacionResponse:
    """
    Submit a new evaluation for neurodevelopmental disorder risk assessment.
    
    This endpoint:
    1. Validates the input data
    2. Makes a prediction using the ML model
    3. Saves the evaluation to the database
    4. Returns the prediction results
    """
    try:
        # Make prediction using the ML model
        prediction_result = predict_risk(
            responses=request.respuestas,
            age=request.edad,
            sex=request.sexo
        )
        
        # Create new evaluation record
        nueva_evaluacion = Evaluacion(
            sexo=request.sexo,
            edad=request.edad,
            respuestas=request.respuestas,  # Will be stored as JSON
            riesgo_estimado=prediction_result["probability"],
            acepto_consentimiento=request.acepto_consentimiento,
            fecha=datetime.utcnow()
        )
        
        # Save to database
        db.add(nueva_evaluacion)
        db.commit()
        db.refresh(nueva_evaluacion)
        
        # Prepare response
        prediction = PredictionResult(**prediction_result)
        
        response = EvaluacionResponse(
            success=True,
            message="Evaluación guardada exitosamente",
            evaluation_id=nueva_evaluacion.id,
            prediction=prediction,
            timestamp=nueva_evaluacion.fecha
        )
        
        return response
        
    except ValueError as e:
        # Input validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Database or model errors
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get(
    "/evaluaciones",
    response_model=List[EvaluacionSummary],
    summary="Get evaluations list",
    description="Retrieve a list of all evaluations (summary view)"
)
async def get_evaluaciones(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[EvaluacionSummary]:
    """
    Get a list of evaluations with pagination.
    
    Args:
        limit: Maximum number of records to return (default: 100)
        offset: Number of records to skip (default: 0)
        db: Database session
        
    Returns:
        List of evaluation summaries
    """
    try:
        evaluaciones = db.query(Evaluacion)\
                        .order_by(Evaluacion.fecha.desc())\
                        .offset(offset)\
                        .limit(limit)\
                        .all()
        
        return [EvaluacionSummary.from_orm(eval) for eval in evaluaciones]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving evaluations: {str(e)}"
        )

@router.get(
    "/evaluaciones/{evaluation_id}",
    response_model=EvaluacionDetail,
    summary="Get evaluation details",
    description="Retrieve detailed information for a specific evaluation"
)
async def get_evaluacion_detail(
    evaluation_id: int,
    db: Session = Depends(get_db)
) -> EvaluacionDetail:
    """
    Get detailed information for a specific evaluation.
    
    Args:
        evaluation_id: ID of the evaluation to retrieve
        db: Database session
        
    Returns:
        Detailed evaluation information including responses
    """
    try:
        evaluacion = db.query(Evaluacion)\
                      .filter(Evaluacion.id == evaluation_id)\
                      .first()
        
        if not evaluacion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Evaluation with ID {evaluation_id} not found"
            )
        
        return EvaluacionDetail.from_orm(evaluacion)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving evaluation: {str(e)}"
        )

@router.get(
    "/stats",
    summary="Get evaluation statistics",
    description="Get basic statistics about stored evaluations"
)
async def get_evaluation_stats(db: Session = Depends(get_db)):
    """
    Get basic statistics about stored evaluations.
    
    Returns:
        Dictionary with evaluation statistics
    """
    try:
        total_evaluations = db.query(Evaluacion).count()
        
        # Count by risk level
        high_risk = db.query(Evaluacion)\
                     .filter(Evaluacion.riesgo_estimado >= 0.7)\
                     .count()
        
        medium_risk = db.query(Evaluacion)\
                       .filter(Evaluacion.riesgo_estimado >= 0.3)\
                       .filter(Evaluacion.riesgo_estimado < 0.7)\
                       .count()
        
        low_risk = db.query(Evaluacion)\
                    .filter(Evaluacion.riesgo_estimado < 0.3)\
                    .count()
        
        # Count by demographics
        male_count = db.query(Evaluacion)\
                      .filter(Evaluacion.sexo == 'M')\
                      .count()
        
        female_count = db.query(Evaluacion)\
                        .filter(Evaluacion.sexo == 'F')\
                        .count()
        
        return {
            "total_evaluations": total_evaluations,
            "risk_distribution": {
                "high_risk": high_risk,
                "medium_risk": medium_risk,
                "low_risk": low_risk
            },
            "gender_distribution": {
                "male": male_count,
                "female": female_count
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting statistics: {str(e)}"
        )