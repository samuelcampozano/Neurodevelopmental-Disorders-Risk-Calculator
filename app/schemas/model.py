from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class ModelMetrics(BaseModel):
    """Model performance metrics"""
    accuracy: float
    f1_score: float
    roc_auc: float
    precision: float
    recall: float
    training_samples: int

class ModelInfo(BaseModel):
    """Model information and metadata"""
    version: str
    created_at: datetime
    model_type: str
    file_path: str
    metrics: ModelMetrics
    hyperparameters: Dict[str, Any]
    training_duration: Optional[float] = None

class RetrainResponse(BaseModel):
    """Response from model retraining endpoint"""
    success: bool
    message: str
    new_model_version: str
    metrics: ModelMetrics
    training_time: float
    previous_model: Optional[str] = None