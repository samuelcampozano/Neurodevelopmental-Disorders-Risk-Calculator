"""
Retrain router for model management endpoints.
"""

import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json

from app.models.predictor import get_predictor, reload_predictor
from app.database import SessionLocal
from app.models.evaluacion import Evaluacion

# Create router
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

@router.post("/retrain-model")
async def retrain_model(background_tasks: BackgroundTasks):
    """
    Retrain the model using current database data.
    This runs the training in the background and reloads the model.
    """
    try:
        logger.info("Model retraining requested")
        
        # Check if we have enough data
        db = SessionLocal()
        try:
            eval_count = db.query(Evaluacion).count()
            if eval_count < 10:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": f"Insufficient data for training. Found {eval_count} evaluations, need at least 10.",
                        "metrics": {},  # Always provide metrics key
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
        finally:
            db.close()
        
        # Add training task to background
        background_tasks.add_task(run_training_task)
        
        return {
            "success": True,
            "message": "Model retraining started in background",
            "status": "training_started",
            "data_count": eval_count,
            "metrics": {},  # Provide empty metrics initially
            "version": "training_in_progress",
            "model_path": "",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting model retraining: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Retraining failed: {str(e)}",
                "metrics": {},  # Always provide metrics key
                "version": "error",
                "model_path": "",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/training-status")
async def get_training_status():
    """
    Get the status of model training and available models.
    """
    try:
        # Check for training log
        log_file = Path("training.log")
        training_active = False
        last_log_entry = None
        
        if log_file.exists():
            # Read last few lines of log to check if training is active
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_log_entry = lines[-1].strip()
                    # Simple heuristic - if last log is recent and mentions training
                    if "training" in last_log_entry.lower():
                        training_active = True
        
        # Get current model info
        predictor = get_predictor()
        model_info = predictor.get_model_info()
        
        # Get database stats
        db = SessionLocal()
        try:
            eval_count = db.query(Evaluacion).count()
        finally:
            db.close()
        
        return {
            "training_active": training_active,
            "last_log_entry": last_log_entry,
            "current_model": model_info,
            "database_records": eval_count,
            "metrics": model_info.get('metrics', {}),  # Safely get metrics
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting training status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Error getting training status: {str(e)}",
                "training_active": False,
                "metrics": {},  # Always provide metrics key
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/available-models")
async def list_available_models():
    """
    List all available trained models.
    """
    try:
        models_dir = Path("data/models")
        available_models = []
        
        if models_dir.exists():
            # Look for metadata files
            for metadata_file in models_dir.glob("metadata_*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                        # Ensure metrics key exists in each model metadata
                        if 'metrics' not in metadata:
                            metadata['metrics'] = {}
                        available_models.append(metadata)
                except Exception as e:
                    logger.warning(f"Could not read metadata file {metadata_file}: {str(e)}")
        
        # Sort by timestamp (newest first)
        available_models.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Get current model info
        current_version_file = Path("data/current_model_version.json")
        current_version = None
        current_metrics = {}
        if current_version_file.exists():
            try:
                with open(current_version_file, 'r') as f:
                    current_info = json.load(f)
                    current_version = current_info.get('current_version')
                    current_metrics = current_info.get('metrics', {})
            except Exception as e:
                logger.warning(f"Could not read current version file: {str(e)}")
        
        return {
            "models": available_models,
            "current_version": current_version,
            "current_metrics": current_metrics,
            "total_models": len(available_models),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error listing available models: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Error listing models: {str(e)}",
                "models": [],
                "current_metrics": {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )

async def run_training_task():
    """
    Background task to run model training.
    """
    training_result = {
        "success": False,
        "message": "",
        "metrics": {},
        "version": "unknown",
        "model_path": "",
        "error": None
    }
    
    try:
        logger.info("Starting background training task")
        
        # Get the path to the training script
        script_path = Path(__file__).parent.parent.parent / "scripts" / "train_model.py"
        
        if not script_path.exists():
            # Try alternative path
            script_path = Path("scripts/train_model.py")
        
        if not script_path.exists():
            error_msg = f"Training script not found at {script_path}"
            logger.error(error_msg)
            training_result["error"] = error_msg
            training_result["message"] = "Training script not found"
            return training_result
        
        # Run the training script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("Training completed successfully")
            training_result["success"] = True
            training_result["message"] = "Model trained successfully"
            
            # Try to parse training output for metrics
            try:
                if result.stdout:
                    # Attempt to parse JSON output from training script
                    output_lines = result.stdout.strip().split('\n')
                    for line in reversed(output_lines):  # Check from last line
                        try:
                            parsed_output = json.loads(line)
                            if isinstance(parsed_output, dict) and 'metrics' in parsed_output:
                                training_result["metrics"] = parsed_output.get('metrics', {})
                                training_result["version"] = parsed_output.get('version', 'unknown')
                                training_result["model_path"] = parsed_output.get('model_path', '')
                                break
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.warning(f"Could not parse training output for metrics: {str(e)}")
            
            # Reload the model in the current process
            reload_success = reload_predictor()
            if reload_success:
                logger.info("Model reloaded successfully after training")
                # Try to get updated metrics from the reloaded model
                try:
                    predictor = get_predictor()
                    model_info = predictor.get_model_info()
                    if 'metrics' in model_info:
                        training_result["metrics"].update(model_info['metrics'])
                except Exception as e:
                    logger.warning(f"Could not get metrics from reloaded model: {str(e)}")
            else:
                logger.warning("Failed to reload model after training")
                training_result["message"] += " (Warning: Model reload failed)"
                
        else:
            error_msg = f"Training failed with return code {result.returncode}"
            logger.error(error_msg)
            logger.error(f"Training stderr: {result.stderr}")
            training_result["error"] = f"{error_msg}: {result.stderr}"
            training_result["message"] = "Training process failed"
            
    except subprocess.TimeoutExpired:
        error_msg = "Training timed out after 5 minutes"
        logger.error(error_msg)
        training_result["error"] = error_msg
        training_result["message"] = "Training timed out"
    except Exception as e:
        error_msg = f"Background training task failed: {str(e)}"
        logger.error(error_msg)
        training_result["error"] = error_msg
        training_result["message"] = "Training task failed with exception"
    
    # Save training result to a status file for later retrieval
    try:
        status_file = Path("data/last_training_status.json")
        status_file.parent.mkdir(exist_ok=True)
        with open(status_file, 'w') as f:
            json.dump({
                **training_result,
                "timestamp": datetime.utcnow().isoformat()
            }, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not save training status: {str(e)}")
    
    return training_result

@router.get("/last-training-result")
async def get_last_training_result():
    """
    Get the result of the last training operation.
    """
    try:
        status_file = Path("data/last_training_status.json")
        if status_file.exists():
            with open(status_file, 'r') as f:
                training_status = json.load(f)
                # Ensure all required keys exist
                result = {
                    "success": training_status.get('success', False),
                    "message": training_status.get('message', 'Unknown status'),
                    "metrics": training_status.get('metrics', {}),
                    "version": training_status.get('version', 'unknown'),
                    "model_path": training_status.get('model_path', ''),
                    "error": training_status.get('error'),
                    "timestamp": training_status.get('timestamp', datetime.utcnow().isoformat())
                }
                return result
        else:
            return {
                "success": False,
                "message": "No previous training results found",
                "metrics": {},
                "version": "none",
                "model_path": "",
                "error": "No training history",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error getting last training result: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Error getting training result: {str(e)}",
                "metrics": {},
                "version": "error",
                "model_path": "",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@router.get("/model-metrics")
async def get_model_metrics():
    """
    Get detailed metrics for the current model.
    """
    try:
        predictor = get_predictor()
        
        # Get model info and validation
        model_info = predictor.get_model_info()
        validation = predictor.validate_model()
        detailed_stats = predictor.get_detailed_stats()
        
        # Try to get training metrics from version file
        training_metrics = {}
        version_file = Path("data/current_model_version.json")
        if version_file.exists():
            try:
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
                    training_metrics = version_data.get('metrics', {})
            except Exception as e:
                logger.warning(f"Could not read training metrics: {str(e)}")
        
        # Combine all metrics safely
        combined_metrics = {}
        
        # Add metrics from model_info
        if isinstance(model_info, dict) and 'metrics' in model_info:
            combined_metrics.update(model_info['metrics'])
        
        # Add training metrics
        combined_metrics.update(training_metrics)
        
        # Add validation metrics if available
        if isinstance(validation, dict) and 'metrics' in validation:
            combined_metrics.update(validation['metrics'])
        
        return {
            "model_info": model_info,
            "validation": validation,
            "detailed_stats": detailed_stats,
            "training_metrics": training_metrics,
            "combined_metrics": combined_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting model metrics: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Error getting model metrics: {str(e)}",
                "model_info": {},
                "validation": {},
                "detailed_stats": {},
                "training_metrics": {},
                "combined_metrics": {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )