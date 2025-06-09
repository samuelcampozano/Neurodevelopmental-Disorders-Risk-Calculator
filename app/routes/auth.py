"""
Protected route for model retraining.
Requires admin authentication to execute.
"""

import os
import pickle
import numpy as np
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

from app.database import get_db
from app.models.evaluacion import Evaluacion
from app.auth import require_retrain_permission, TokenData
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/model",
    tags=["model-management"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
    },
)

# Global variable to track retraining status
retraining_status = {
    "is_retraining": False,
    "last_retrain": None,
    "last_result": None
}

async def retrain_model_task(db: Session):
    """
    Background task to retrain the model with data from database.
    """
    global retraining_status
    
    try:
        retraining_status["is_retraining"] = True
        logger.info("Starting model retraining...")
        
        # Fetch all evaluations from database
        evaluations = db.query(Evaluacion).all()
        
        if len(evaluations) < 50:  # Minimum data requirement
            raise ValueError(f"Insufficient data for retraining. Found {len(evaluations)} evaluations, need at least 50.")
        
        # Prepare training data
        X = []
        y = []
        
        for eval in evaluations:
            # Extract features (40 SCQ responses)
            X.append(eval.respuestas)
            # Target is binary: high risk (>= 0.7) or not
            y.append(1 if eval.riesgo_estimado >= 0.7 else 0)
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train new model
        new_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        new_model.fit(X_train, y_train)
        
        # Evaluate new model
        y_pred = new_model.predict(X_test)
        y_proba = new_model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        auc_score = roc_auc_score(y_test, y_proba)
        
        # Only save if performance is acceptable
        if accuracy >= 0.7:  # Minimum accuracy threshold
            # Backup current model
            model_path = "data/modelo_entrenado.pkl"
            backup_path = f"data/modelo_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
            
            if os.path.exists(model_path):
                os.rename(model_path, backup_path)
                logger.info(f"Backed up current model to {backup_path}")
            
            # Save new model
            with open(model_path, 'wb') as f:
                pickle.dump(new_model, f)
            
            result = {
                "status": "success",
                "message": "Model retrained and saved successfully",
                "metrics": {
                    "accuracy": float(accuracy),
                    "auc_score": float(auc_score),
                    "training_samples": len(X_train),
                    "test_samples": len(X_test),
                    "total_evaluations": len(evaluations)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Model retrained successfully. Accuracy: {accuracy:.2%}, AUC: {auc_score:.2%}")
        else:
            result = {
                "status": "rejected",
                "message": f"New model performance ({accuracy:.2%}) below threshold (70%)",
                "metrics": {
                    "accuracy": float(accuracy),
                    "auc_score": float(auc_score)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.warning(f"Model retraining rejected due to low accuracy: {accuracy:.2%}")
        
        retraining_status["last_retrain"] = datetime.utcnow()
        retraining_status["last_result"] = result
        
    except Exception as e:
        logger.error(f"Error during model retraining: {str(e)}")
        retraining_status["last_result"] = {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        retraining_status["is_retraining"] = False

@router.post("/retrain", 
    summary="Retrain ML model",
    description="Retrain the machine learning model with accumulated data. Requires admin privileges."
)
async def retrain_model(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(require_retrain_permission)
):
    """
    Trigger model retraining with data from database.
    
    This endpoint:
    1. Requires admin authentication
    2. Fetches all evaluations from database
    3. Retrains the Random Forest model
    4. Evaluates performance
    5. Saves new model if performance is acceptable
    
    The retraining happens in the background.
    """
    if retraining_status["is_retraining"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Model retraining is already in progress"
        )
    
    # Check if we have enough data
    evaluation_count = db.query(Evaluacion).count()
    if evaluation_count < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient data for retraining. Found {evaluation_count} evaluations, need at least 50."
        )
    
    # Start retraining in background
    background_tasks.add_task(retrain_model_task, db)
    
    return {
        "status": "started",
        "message": "Model retraining initiated in background",
        "evaluation_count": evaluation_count,
        "initiated_by": token_data.username,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/retrain/status",
    summary="Get retraining status",
    description="Check the status of model retraining process"
)
async def get_retrain_status(
    token_data: TokenData = Depends(require_retrain_permission)
):
    """
    Get the current status of model retraining.
    
    Returns:
        Current retraining status and last result
    """
    return {
        "is_retraining": retraining_status["is_retraining"],
        "last_retrain": retraining_status["last_retrain"].isoformat() if retraining_status["last_retrain"] else None,
        "last_result": retraining_status["last_result"]
    }

@router.get("/info",
    summary="Get model information",
    description="Get information about the current model"
)
async def get_model_info():
    """
    Get information about the currently loaded model.
    
    This endpoint is public and doesn't require authentication.
    """
    try:
        from app.models.predictor import get_model_info as get_predictor_info
        model_info = get_predictor_info()
        
        # Add versioning info
        model_path = "data/modelo_entrenado.pkl"
        if os.path.exists(model_path):
            model_info["file_modified"] = datetime.fromtimestamp(
                os.path.getmtime(model_path)
            ).isoformat()
            model_info["file_size_kb"] = os.path.getsize(model_path) / 1024
        
        return model_info
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting model info: {str(e)}"
        )