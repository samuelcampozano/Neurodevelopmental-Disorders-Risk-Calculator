"""
Machine Learning predictor module for neurodevelopmental disorders risk assessment.
Handles model loading and prediction logic.
"""

import os
import joblib
import numpy as np
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the loaded model
_model = None
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
    global _model
    
    if _model is not None:
        return _model
    
    try:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
        
        _model = joblib.load(MODEL_PATH)
        logger.info(f"Model loaded successfully from {MODEL_PATH}")
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
        
        # CRITICAL FIX: Prepare features for prediction
        # Check what the model actually expects
        try:
            # Try with only the 40 responses first (most likely correct)
            features = prepare_features_40(responses)
            probability = model.predict_proba([features])[0][1]
        except Exception as e:
            # If that fails, try with demographics included
            logger.warning(f"40-feature prediction failed: {e}. Trying with demographics...")
            features = prepare_features_42(responses, age, sex)
            probability = model.predict_proba([features])[0][1]
        
        # Determine risk level
        risk_level = get_risk_level(probability)
        
        # Get model confidence (simplified as max probability)
        confidence = max(model.predict_proba([features])[0])
        
        result = {
            "probability": float(probability),
            "risk_level": risk_level,
            "confidence": float(confidence),
            "interpretation": get_interpretation(probability)
        }
        
        logger.info(f"Prediction completed: {probability:.3f} risk probability")
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
    try:
        model = load_model()
        return {
            "model_type": type(model).__name__,
            "feature_count": getattr(model, 'n_features_in_', 'Unknown'),
            "model_path": MODEL_PATH,
            "is_loaded": _model is not None
        }
    except Exception as e:
        return {
            "error": str(e),
            "is_loaded": False
        }