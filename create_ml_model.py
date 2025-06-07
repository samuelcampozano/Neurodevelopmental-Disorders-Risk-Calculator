#!/usr/bin/env python3
"""
Script to create a properly configured ML model for the NDD Risk Calculator.
This ensures the model has all required attributes and works with the predictor module.
"""

import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import os
from datetime import datetime

def create_and_save_model():
    """Create, train, and save a properly configured Random Forest model."""
    
    print("🧠 Creating ML Model for Neurodevelopmental Disorders Risk Calculator")
    print("=" * 60)
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Generate synthetic training data
    print("📊 Generating synthetic training data...")
    n_samples = 1000
    
    # Create feature matrix (40 SCQ responses)
    # Simulate realistic patterns
    np.random.seed(42)  # For reproducibility
    
    # Generate base patterns
    X = np.random.randint(0, 2, size=(n_samples, 40))
    
    # Create target variable with some correlation to features
    # High risk: many positive responses (>25)
    # Medium risk: moderate responses (15-25)
    # Low risk: few responses (<15)
    
    y = []
    for responses in X:
        positive_count = np.sum(responses)
        if positive_count > 25:
            # 80% chance of high risk
            y.append(np.random.choice([1, 0], p=[0.8, 0.2]))
        elif positive_count > 15:
            # 50% chance of risk
            y.append(np.random.choice([1, 0], p=[0.5, 0.5]))
        else:
            # 20% chance of risk
            y.append(np.random.choice([1, 0], p=[0.2, 0.8]))
    
    y = np.array(y)
    
    print(f"   ✅ Generated {n_samples} samples")
    print(f"   📈 Positive class ratio: {np.mean(y):.2%}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Create and train model
    print("\n🔧 Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    print("   ✅ Model trained successfully")
    
    # Evaluate model
    print("\n📊 Model Evaluation:")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"   🎯 Accuracy: {accuracy:.2%}")
    
    # Feature importance
    print(f"\n📈 Feature Importance Statistics:")
    importances = model.feature_importances_
    print(f"   Most important feature: Question {np.argmax(importances) + 1}")
    print(f"   Least important feature: Question {np.argmin(importances) + 1}")
    print(f"   Average importance: {np.mean(importances):.4f}")
    
    # Verify model attributes
    print("\n🔍 Verifying model attributes:")
    print(f"   ✅ n_features_in_: {model.n_features_in_}")
    print(f"   ✅ n_estimators: {model.n_estimators}")
    print(f"   ✅ classes_: {model.classes_}")
    
    # Save model
    model_path = "data/modelo_entrenado.pkl"
    print(f"\n💾 Saving model to {model_path}...")
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Verify saved model
    print("\n🔍 Verifying saved model...")
    with open(model_path, 'rb') as f:
        loaded_model = pickle.load(f)
    
    # Test prediction
    test_input = np.array([[1, 0, 1, 0] * 10])  # 40 features
    test_proba = loaded_model.predict_proba(test_input)[0]
    
    print(f"   ✅ Model loaded successfully")
    print(f"   ✅ Test prediction: {test_proba[1]:.2%} risk probability")
    
    # Save model metadata
    metadata = {
        "created_at": datetime.now().isoformat(),
        "model_type": "RandomForestClassifier",
        "n_features": 40,
        "n_samples_trained": len(X_train),
        "accuracy": float(accuracy),
        "feature_names": [f"SCQ_Q{i+1}" for i in range(40)],
        "description": "Random Forest model for NDD risk prediction based on SCQ responses"
    }
    
    metadata_path = "data/model_metadata.json"
    print(f"\n📝 Saving metadata to {metadata_path}...")
    
    import json
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ MODEL CREATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📁 Model saved to: {os.path.abspath(model_path)}")
    print(f"📊 Model expects: 40 binary features (SCQ responses)")
    print(f"🎯 Model accuracy: {accuracy:.2%}")
    print("\n🚀 Your ML model is ready to use!")

if __name__ == "__main__":
    create_and_save_model()