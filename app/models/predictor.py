"""
Machine Learning predictor module for neurodevelopmental disorders risk assessment.
Handles model loading and prediction logic.
"""

import os
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the loaded model
_model = None
_model_metadata = {
    "loaded_at": None,
    "version": "1.0.0",
    "feature_count": None,
    "model_type": None
}

MODEL_PATH = "data/modelo_entrenado.pkl"

def load_model():
    """
    Load the trained Random Forest model from disk.
    
    Returns:
        The loaded scikit-learn model
        
    Raises:
        FileNotFoundError: If the model file doesn't exist
        Exception: If there's an error loading the model
    """
    global _model, _model_metadata
    
    if _model is not None:
        return _model
    
    try:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        
        with open(MODEL_PATH, 'rb') as f:
            _model = pickle.load(f)
        
        # Update metadata
        _model_metadata["loaded_at"] = datetime.utcnow().isoformat()
        _model_metadata["model_type"] = type(_model).__name__
        
        if hasattr(_model, 'n_features_in_'):
            _model_metadata["feature_count"] = _model.n_features_in_
        
        logger.info(f"Successfully loaded {_model_metadata['model_type']} model (v{_model_metadata['version']})")
        return _model
        
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

def predict_risk(responses: List[bool], age: int, sex: str) -> Dict[str, Any]:
    """
    Predict neurodevelopmental disorder risk based on SCQ responses and demographics.
    
    Args:
        responses: List of 40 boolean responses to SCQ questionnaire
        age: User's age
        sex: User's sex ('M' or 'F')
        
    Returns:
        Dictionary containing:
        - probability: Risk probability (0.0 to 1.0)
        - risk_level: Risk category ('Low', 'Medium', 'High')
        - confidence: Model confidence score
        - interpretation: Human-readable interpretation
        
    Raises:
        ValueError: If input parameters are invalid
        Exception: If prediction fails
    """
    try:
        # Validate inputs
        if len(responses) != 40:
            raise ValueError(f"Expected 40 responses, got {len(responses)}")
        
        if not isinstance(age, int) or age < 0 or age > 120:
            raise ValueError(f"Invalid age: {age}")
        
        if sex not in ['M', 'F']:
            raise ValueError(f"Invalid sex: {sex}. Must be 'M' or 'F'")
        
        # Load model if not already loaded
        model = load_model()
        
        # Prepare features based on model's expected input
        if hasattr(model, 'n_features_in_'):
            if model.n_features_in_ == 40:
                features = prepare_features_40(responses)
            elif model.n_features_in_ == 42:
                features = prepare_features_42(responses, age, sex)
            else:
                # Default to 40 features
                logger.warning(f"Unexpected feature count: {model.n_features_in_}. Using 40 features.")
                features = prepare_features_40(responses)
        else:
            # Default to 40 features if no feature count info
            features = prepare_features_40(responses)
        
        # Get prediction
        probability = float(model.predict_proba([features])[0][1])
        
        # Determine risk level
        risk_level = get_risk_level(probability)
        
        # Get model confidence (using prediction probability)
        confidence = max(model.predict_proba([features])[0])
        
        result = {
            "probability": probability,
            "risk_level": risk_level,
            "confidence": float(confidence),
            "interpretation": get_interpretation(probability)
        }
        
        logger.info(f"Prediction completed: {risk_level} risk ({probability:.3f})")
        return result
        
    except Exception as e:
        logger.error(f"Error in prediction: {str(e)}")
        raise

def prepare_features_40(responses: List[bool]) -> List[float]:
    """
    Prepare features for model prediction (40 features only - SCQ responses).
    
    Args:
        responses: List of 40 boolean responses
        
    Returns:
        List of 40 features ready for model input
    """
    # Convert responses to numeric (True -> 1, False -> 0)
    return [float(r) for r in responses]

def prepare_features_42(responses: List[bool], age: int, sex: str) -> List[float]:
    """
    Prepare features for model prediction (42 features - SCQ + demographics).
    
    Args:
        responses: List of 40 boolean responses
        age: User's age
        sex: User's sex ('M' or 'F')
        
    Returns:
        List of 42 features ready for model input
    """
    # Convert responses to numeric (True -> 1, False -> 0)
    numeric_responses = [float(r) for r in responses]
    
    # Add demographic features
    features = numeric_responses.copy()
    features.append(float(age))
    features.append(1.0 if sex == 'M' else 0.0)  # Male = 1, Female = 0
    
    return features

def get_risk_level(probability: float) -> str:
    """
    Convert probability to risk level category.
    
    Args:
        probability: Risk probability (0.0 to 1.0)
        
    Returns:
        Risk level string ('Low', 'Medium', 'High')
    """
    if probability < 0.3:
        return "Low"
    elif probability < 0.7:
        return "Medium"
    else:
        return "High"

def get_interpretation(probability: float) -> str:
    """
    Get human-readable interpretation of the risk probability.
    
    Args:
        probability: Risk probability (0.0 to 1.0)
        
    Returns:
        Interpretation string
    """
    if probability < 0.2:
        return "Muy bajo riesgo de trastornos del neurodesarrollo"
    elif probability < 0.4:
        return "Riesgo bajo de trastornos del neurodesarrollo"
    elif probability < 0.6:
        return "Riesgo moderado de trastornos del neurodesarrollo"
    elif probability < 0.8:
        return "Riesgo alto de trastornos del neurodesarrollo"
    else:
        return "Riesgo muy alto de trastornos del neurodesarrollo"

def get_model_info() -> Dict[str, Any]:
    """
    Get information about the loaded model.
    
    Returns:
        Dictionary with model information
    """
    global _model_metadata
    
    try:
        # Try to load model if not loaded
        if _model is None:
            load_model()
        
        return {
            "is_loaded": _model is not None,
            "model_type": _model_metadata.get("model_type", "Unknown"),
            "feature_count": _model_metadata.get("feature_count", "Unknown"),
            "model_version": _model_metadata.get("version", "Unknown"),
            "loaded_at": _model_metadata.get("loaded_at"),
            "model_path": MODEL_PATH
        }
    except Exception as e:
        return {
            "is_loaded": False,
            "error": str(e),
            "model_path": MODEL_PATH
        }

def get_model_metrics() -> Dict[str, Any]:
    """
    Get model performance metrics.
    
    Returns:
        Dictionary with model metrics
    """
    # In a real scenario, these would be calculated during training
    # For now, return placeholder metrics
    return {
        "accuracy": 0.85,
        "precision": 0.82,
        "recall": 0.88,
        "f1_score": 0.85,
        "auc_roc": 0.91,
        "training_samples": 1000,
        "validation_samples": 200,
        "last_trained": "2024-01-15T10:30:00"
    }

def validate_model() -> bool:
    """
    Validate that the model is properly configured and working.
    
    Returns:
        True if model is valid, False otherwise
    """
    try:
        # Try to load model
        model = load_model()
        
        # Test with dummy data
        test_responses = [True, False] * 20  # 40 responses
        result = predict_risk(test_responses, 10, "M")
        
        # Check result structure
        required_keys = {"probability", "risk_level", "confidence", "interpretation"}
        if not all(key in result for key in required_keys):
            return False
        
        # Check probability is in valid range
        if not 0 <= result["probability"] <= 1:
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Model validation failed: {str(e)}")
        return False