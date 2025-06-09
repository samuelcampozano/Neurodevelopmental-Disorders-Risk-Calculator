#!/usr/bin/env python3
"""
Dynamic Model Training Script for Neurodevelopmental Disorders Risk Calculator
Trains models using real saved evaluation data from the database.
Fixed version with proper error handling and path management.
"""

import os
import sys
import json
import pickle
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd

# Fix import path issues - add project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent  # Go up one level to project root

# Add both project root and app directory to Python path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'app'))

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, classification_report, confusion_matrix
    from sklearn.preprocessing import StandardScaler
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: sklearn not available: {e}")
    SKLEARN_AVAILABLE = False

import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ModelTrainer:
    """Handles model training, evaluation, and versioning."""
    
    def __init__(self, models_dir: str = None, min_samples: int = 10):
        """
        Initialize the ModelTrainer.
        
        Args:
            models_dir: Directory to save trained models
            min_samples: Minimum number of samples required for training
        """
        if models_dir is None:
            # Default to data/models in project root
            models_dir = project_root / "data" / "models"
        
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.min_samples = min_samples
        self.model_metadata = {}
        
        # Check if sklearn is available
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn is not available. Please install it with: pip install scikit-learn")
            raise ImportError("scikit-learn is required for model training")
        
    def extract_data_from_db(self) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """
        Extract training data from the database.
        
        Returns:
            Tuple of (X, y, raw_data) where:
            - X: Feature matrix (40 responses per evaluation)
            - y: Target vector (binary risk labels)
            - raw_data: List of raw evaluation dictionaries
        """
        logger.info("Extracting data from database...")
        
        try:
            # Try to import database modules with proper error handling
            try:
                from database import SessionLocal, engine
                from models.evaluacion import Evaluacion
            except ImportError:
                try:
                    from app.database import SessionLocal, engine
                    from app.models.evaluacion import Evaluacion
                except ImportError:
                    # Last resort - try direct path import
                    import importlib.util
                    
                    # Import database module
                    db_path = project_root / "app" / "database.py"
                    if not db_path.exists():
                        raise ImportError(f"Database module not found at {db_path}")
                        
                    spec = importlib.util.spec_from_file_location("database", db_path)
                    db_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(db_module)
                    
                    SessionLocal = db_module.SessionLocal
                    engine = db_module.engine
                    
                    # Import model
                    model_path = project_root / "app" / "models" / "evaluacion.py"
                    if not model_path.exists():
                        raise ImportError(f"Evaluacion model not found at {model_path}")
                        
                    spec = importlib.util.spec_from_file_location("evaluacion", model_path)
                    model_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(model_module)
                    
                    Evaluacion = model_module.Evaluacion
            
            db = SessionLocal()
            
            # Get all evaluations from database
            evaluations = db.query(Evaluacion).all()
            
            if len(evaluations) < self.min_samples:
                raise ValueError(f"Insufficient data: {len(evaluations)} samples found, minimum {self.min_samples} required")
            
            logger.info(f"Found {len(evaluations)} evaluations in database")
            
            # Prepare features (X) and targets (y)
            X_list = []
            y_list = []
            raw_data = []
            
            for eval_record in evaluations:
                # Parse responses (assuming they're stored as JSON string or list)
                if isinstance(eval_record.respuestas, str):
                    responses = json.loads(eval_record.respuestas)
                else:
                    responses = eval_record.respuestas
                
                # Ensure we have exactly 40 responses
                if len(responses) != 40:
                    logger.warning(f"Evaluation {eval_record.id} has {len(responses)} responses, expected 40. Skipping.")
                    continue
                
                # Convert responses to binary features
                X_features = [int(bool(response)) for response in responses]
                X_list.append(X_features)
                
                # Convert estimated_risk to binary label (threshold at 0.5)
                y_binary = 1 if eval_record.riesgo_estimado >= 0.5 else 0
                y_list.append(y_binary)
                
                # Store raw data for analysis
                raw_data.append({
                    'id': eval_record.id,
                    'age': eval_record.edad,
                    'sex': eval_record.sexo,
                    'estimated_risk': eval_record.riesgo_estimado,
                    'binary_label': y_binary,
                    'date': eval_record.fecha.isoformat() if eval_record.fecha else None
                })
            
            X = np.array(X_list, dtype=np.float32)
            y = np.array(y_list, dtype=np.int32)
            
            logger.info(f"Processed {len(X)} valid samples")
            logger.info(f"Feature matrix shape: {X.shape}")
            logger.info(f"Target distribution: {np.bincount(y)}")
            
            return X, y, raw_data
            
        except Exception as e:
            logger.error(f"Error extracting data from database: {str(e)}")
            logger.error(f"Project root: {project_root}")
            logger.error(f"Current working directory: {os.getcwd()}")
            logger.error(f"Python path: {sys.path}")
            raise
        finally:
            try:
                db.close()
            except:
                pass
    
    def generate_synthetic_data(self, n_samples: int = 100) -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
        """
        Generate synthetic training data when database is not available.
        
        Args:
            n_samples: Number of synthetic samples to generate
            
        Returns:
            Tuple of (X, y, raw_data)
        """
        logger.warning(f"Generating {n_samples} synthetic samples for training")
        
        np.random.seed(42)
        
        # Generate synthetic features (40 binary responses)
        X = np.random.binomial(1, 0.3, size=(n_samples, 40)).astype(np.float32)
        
        # Generate synthetic labels based on number of positive responses
        positive_counts = X.sum(axis=1)
        # Higher number of positive responses = higher risk
        risk_probs = np.clip(positive_counts / 20.0, 0.1, 0.9)
        y = np.random.binomial(1, risk_probs).astype(np.int32)
        
        # Generate synthetic metadata
        raw_data = []
        for i in range(n_samples):
            raw_data.append({
                'id': f'synthetic_{i}',
                'age': np.random.randint(18, 72),
                'sex': np.random.choice(['M', 'F']),
                'estimated_risk': float(risk_probs[i]),
                'binary_label': int(y[i]),
                'date': datetime.now().isoformat(),
                'synthetic': True
            })
        
        logger.info(f"Generated synthetic data: {X.shape}")
        logger.info(f"Synthetic target distribution: {np.bincount(y)}")
        
        return X, y, raw_data
    
    def train_model(self, X: np.ndarray, y: np.ndarray) -> Tuple[Any, Dict[str, float]]:
        """
        Train a RandomForestClassifier model.
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            Tuple of (trained_model, metrics_dict)
        """
        logger.info("Training model...")
        
        # Check class balance
        unique, counts = np.unique(y, return_counts=True)
        class_distribution = dict(zip(unique, counts))
        logger.info(f"Class distribution: {class_distribution}")
        
        # Handle case where we have only one class
        if len(unique) == 1:
            logger.warning("Only one class present in data. Adding synthetic minority class samples.")
            # Add a few samples from the minority class
            minority_class = 1 - unique[0]
            minority_samples = 3
            
            # Create synthetic minority samples
            X_minority = np.random.binomial(1, 0.5, size=(minority_samples, X.shape[1])).astype(np.float32)
            y_minority = np.full(minority_samples, minority_class, dtype=np.int32)
            
            # Combine with original data
            X = np.vstack([X, X_minority])
            y = np.hstack([y, y_minority])
            
            # Update class distribution
            unique, counts = np.unique(y, return_counts=True)
            class_distribution = dict(zip(unique, counts))
            logger.info(f"Updated class distribution: {class_distribution}")
        
        # Split data for training and testing
        test_size = min(0.2, max(0.1, 1.0 / len(y)))  # Adaptive test size
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Initialize model with balanced class weights
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=max(2, len(X_train) // 50),
            min_samples_leaf=max(1, len(X_train) // 100),
            class_weight='balanced',
            random_state=42,
            n_jobs=1  # Use single thread for stability
        )
        
        # Train the model
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, -1]  # Probability of highest class
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Handle AUC calculation (requires at least one positive and one negative sample)
        try:
            if len(np.unique(y_test)) > 1:
                auc = roc_auc_score(y_test, y_pred_proba)
            else:
                auc = 0.5  # Default AUC when only one class in test set
        except ValueError as e:
            logger.warning(f"Could not calculate AUC: {str(e)}")
            auc = 0.5
        
        # Cross-validation scores (if we have enough data)
        try:
            if len(X_train) >= 5:
                cv_folds = min(5, len(X_train))
                cv_scores = cross_val_score(model, X_train, y_train, cv=cv_folds, scoring='accuracy')
                cv_mean = cv_scores.mean()
                cv_std = cv_scores.std()
            else:
                cv_mean = accuracy
                cv_std = 0.0
        except Exception as e:
            logger.warning(f"Cross-validation failed: {str(e)}")
            cv_mean = accuracy
            cv_std = 0.0
        
        metrics = {
            'accuracy': float(accuracy),
            'auc': float(auc),
            'f1_score': float(f1),
            'cv_accuracy_mean': float(cv_mean),
            'cv_accuracy_std': float(cv_std),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'class_distribution': class_distribution
        }
        
        # Feature importance
        feature_importance = model.feature_importances_
        top_features = sorted(enumerate(feature_importance), key=lambda x: x[1], reverse=True)[:10]
        metrics['top_10_features'] = [(f"question_{idx+1}", float(importance)) for idx, importance in top_features]
        
        logger.info(f"Model training completed:")
        logger.info(f"  Accuracy: {accuracy:.4f}")
        logger.info(f"  AUC: {auc:.4f}")
        logger.info(f"  F1-Score: {f1:.4f}")
        logger.info(f"  CV Accuracy: {cv_mean:.4f} ± {cv_std:.4f}")
        
        # Detailed classification report
        logger.info("Classification Report:")
        try:
            logger.info(f"\n{classification_report(y_test, y_pred)}")
        except:
            logger.info("Could not generate detailed classification report")
        
        return model, metrics
    
    def save_model(self, model: Any, metrics: Dict[str, float], raw_data: List[Dict]) -> str:
        """
        Save the trained model with metadata and versioning.
        
        Args:
            model: Trained model object
            metrics: Dictionary of model metrics
            raw_data: Raw training data for reference
            
        Returns:
            Path to the saved model file
        """
        # Generate version number based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"v{timestamp}"
        
        # Model filename
        model_filename = f"modelo_entrenado_{version}.pkl"
        model_path = self.models_dir / model_filename
        
        # Metadata
        metadata = {
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'model_type': 'RandomForestClassifier',
            'training_samples': len(raw_data),
            'feature_count': 40,
            'metrics': metrics,
            'model_filename': model_filename,
            'sklearn_version': getattr(__import__('sklearn'), '__version__', 'unknown'),
            'python_version': sys.version
        }
        
        # Save model using joblib (more efficient for sklearn models)
        joblib.dump(model, model_path)
        logger.info(f"Model saved to: {model_path}")
        
        # Save metadata
        metadata_path = self.models_dir / f"metadata_{version}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata saved to: {metadata_path}")
        
        # Save training data summary
        data_summary_path = self.models_dir / f"data_summary_{version}.json"
        with open(data_summary_path, 'w') as f:
            json.dump(raw_data, f, indent=2, default=str)
        logger.info(f"Data summary saved to: {data_summary_path}")
        
        # Update current model reference
        current_model_path = self.models_dir / "modelo_entrenado.pkl"
        
        if current_model_path.exists():
            current_model_path.unlink()  # Remove existing file
        
        # Copy the new model to the standard location
        shutil.copy2(model_path, current_model_path)
        logger.info(f"Current model updated: {current_model_path}")
        
        # Save current version info
        current_version_path = self.models_dir / "current_model_version.json"
        with open(current_version_path, 'w') as f:
            json.dump({
                'current_version': version,
                'model_path': model_filename,
                'updated_at': datetime.now().isoformat(),
                'metrics': metrics
            }, f, indent=2)
        
        self.model_metadata = metadata
        return str(model_path)
    
    def get_current_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        current_version_path = self.models_dir / "current_model_version.json"
        if current_version_path.exists():
            with open(current_version_path, 'r') as f:
                return json.load(f)
        return {}
    
    def list_available_models(self) -> List[Dict[str, Any]]:
        """List all available trained models."""
        models = []
        for metadata_file in self.models_dir.glob("metadata_*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    models.append(metadata)
            except Exception as e:
                logger.warning(f"Could not read metadata file {metadata_file}: {e}")
        
        # Sort by timestamp (newest first)
        models.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return models

    def run_full_training(self) -> Dict[str, Any]:
        """
        Run the complete training process and return results.
        This is the main method that should be called from the test script.
        
        Returns:
            Dictionary with training results
        """
        try:
            logger.info("Starting full training process...")
            
            # Extract data from database (with fallback to synthetic data)
            try:
                X, y, raw_data = self.extract_data_from_db()
                data_source = "database"
            except Exception as db_error:
                logger.warning(f"Could not extract data from database: {db_error}")
                logger.info("Falling back to synthetic data generation")
                X, y, raw_data = self.generate_synthetic_data(100)
                data_source = "synthetic"
            
            # Train model
            model, metrics = self.train_model(X, y)
            
            # Add data source info to metrics
            metrics['data_source'] = data_source
            
            # Save model
            model_path = self.save_model(model, metrics, raw_data)
            
            logger.info("="*50)
            logger.info("TRAINING COMPLETED SUCCESSFULLY")
            logger.info(f"Data source: {data_source}")
            logger.info(f"Model saved to: {model_path}")
            logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
            logger.info(f"AUC: {metrics['auc']:.4f}")
            logger.info(f"F1-Score: {metrics['f1_score']:.4f}")
            logger.info("="*50)
            
            return {
                'success': True,
                'model_path': model_path,
                'metrics': metrics,
                'version': self.model_metadata['version'],
                'data_source': data_source
            }
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

def train_model_wrapper():
    """
    Function wrapper for backward compatibility with the test script.
    Returns the result of training, not the trainer instance.
    """
    trainer = ModelTrainer()
    return trainer.run_full_training()

def main():
    """Main training function."""
    try:
        logger.info("Starting model training process...")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Initialize trainer
        trainer = ModelTrainer()
        
        # Run full training process
        result = trainer.run_full_training()
        
        if result['success']:
            logger.info("Training completed successfully!")
            return result
        else:
            logger.error(f"Training failed: {result['error']}")
            return result
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    result = main()
    if not result['success']:
        sys.exit(1)
    else:
        print(f"\nTraining completed successfully!")
        print(f"Model version: {result.get('version', 'unknown')}")
        print(f"Accuracy: {result.get('metrics', {}).get('accuracy', 0):.4f}")
        sys.exit(0)