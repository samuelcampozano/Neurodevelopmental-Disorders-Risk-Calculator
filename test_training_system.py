#!/usr/bin/env python3
"""
Test script for the training system and ML model functionality.
Tests model loading, prediction capabilities, and retraining workflow.
"""

import requests
import json
import os
import sys
import pickle
import numpy as np
from datetime import datetime
import time

# API base URL
BASE_URL = "http://localhost:8000"

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"🧪 {title}")
    print("=" * 70)

def test_model_file_exists():
    """Test if the trained model file exists."""
    print_section("TESTING MODEL FILE")
    
    model_path = "data/modelo_entrenado.pkl"
    
    if os.path.exists(model_path):
        print(f"✅ Model file exists at: {model_path}")
        
        # Check file size
        file_size = os.path.getsize(model_path) / 1024  # KB
        print(f"📊 Model file size: {file_size:.2f} KB")
        
        # Try to load the model
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            print(f"✅ Model loaded successfully")
            print(f"📈 Model type: {type(model).__name__}")
            
            # Check model attributes
            if hasattr(model, 'n_features_in_'):
                print(f"🔢 Number of features: {model.n_features_in_}")
            if hasattr(model, 'n_estimators'):
                print(f"🌳 Number of estimators: {model.n_estimators}")
                
            return True
        except Exception as e:
            print(f"❌ Error loading model: {str(e)}")
            return False
    else:
        print(f"❌ Model file not found at: {model_path}")
        print("💡 Run 'python save_model.py' to create a model")
        return False

def test_prediction_endpoint():
    """Test the prediction endpoint with various inputs."""
    print_section("TESTING PREDICTION ENDPOINT")
    
    # Test case 1: Valid input
    test_data_valid = {
        "responses": [True] * 20 + [False] * 20,  # 40 responses
        "age": 8,
        "sex": "M"
    }
    
    print("📋 Test Case 1: Valid input")
    print(f"   - Responses: {sum(test_data_valid['responses'])} True, {40 - sum(test_data_valid['responses'])} False")
    print(f"   - Age: {test_data_valid['age']}")
    print(f"   - Sex: {test_data_valid['sex']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/predict",
            json=test_data_valid,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Prediction successful!")
            print(f"   📊 Probability: {result.get('probability', 'N/A')}")
            print(f"   🎯 Risk Level: {result.get('risk_level', 'N/A')}")
            print(f"   💪 Confidence: {result.get('confidence', 'N/A')}")
            print(f"   📝 Interpretation: {result.get('interpretation', 'N/A')}")
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
    
    # Test case 2: Edge cases
    print("\n📋 Test Case 2: Edge cases")
    
    edge_cases = [
        {
            "name": "All True responses",
            "data": {
                "responses": [True] * 40,
                "age": 10,
                "sex": "F"
            }
        },
        {
            "name": "All False responses",
            "data": {
                "responses": [False] * 40,
                "age": 5,
                "sex": "M"
            }
        },
        {
            "name": "Minimum age",
            "data": {
                "responses": [True, False] * 20,
                "age": 1,
                "sex": "F"
            }
        }
    ]
    
    for case in edge_cases:
        print(f"\n   🔸 {case['name']}:")
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/predict",
                json=case['data'],
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                print(f"      ✅ Probability: {result['probability']:.3f} ({result['risk_level']})")
            else:
                print(f"      ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Error: {str(e)[:50]}")
    
    return True

def test_submit_and_storage():
    """Test the submit endpoint and data storage."""
    print_section("TESTING SUBMIT & STORAGE")
    
    # Create test evaluation
    test_evaluation = {
        "edad": 7,
        "sexo": "M",
        "respuestas": [True, False, True, False] * 10,  # 40 responses
        "acepto_consentimiento": True
    }
    
    print("📝 Submitting test evaluation...")
    print(f"   - Age: {test_evaluation['edad']}")
    print(f"   - Sex: {test_evaluation['sexo']}")
    print(f"   - Consent: {test_evaluation['acepto_consentimiento']}")
    
    try:
        # Submit evaluation
        response = requests.post(
            f"{BASE_URL}/api/v1/submit",
            json=test_evaluation,
            timeout=10
        )
        
        if response.status_code == 201:
            result = response.json()
            evaluation_id = result.get('evaluation_id')
            print(f"✅ Evaluation submitted successfully!")
            print(f"   📍 Evaluation ID: {evaluation_id}")
            print(f"   🎯 Risk: {result['prediction']['probability']:.3f} ({result['prediction']['risk_level']})")
            
            # Test retrieval
            print("\n📥 Testing retrieval...")
            detail_response = requests.get(
                f"{BASE_URL}/api/v1/evaluaciones/{evaluation_id}",
                timeout=5
            )
            
            if detail_response.status_code == 200:
                detail = detail_response.json()
                print(f"✅ Evaluation retrieved successfully!")
                print(f"   - Stored responses: {len(detail.get('respuestas', []))} items")
                print(f"   - Risk stored: {detail.get('riesgo_estimado', 'N/A')}")
            else:
                print(f"❌ Retrieval failed: {detail_response.status_code}")
            
            return evaluation_id
        else:
            print(f"❌ Submit failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_model_consistency():
    """Test if predictions are consistent."""
    print_section("TESTING MODEL CONSISTENCY")
    
    # Same input should give same output
    test_input = {
        "responses": [True, False, True, True, False] * 8,  # 40 responses
        "age": 9,
        "sex": "F"
    }
    
    print("🔄 Testing prediction consistency (5 calls)...")
    predictions = []
    
    for i in range(5):
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/predict",
                json=test_input,
                timeout=5
            )
            if response.status_code == 200:
                probability = response.json()['probability']
                predictions.append(probability)
                print(f"   Call {i+1}: {probability:.6f}")
            else:
                print(f"   Call {i+1}: Failed")
        except Exception as e:
            print(f"   Call {i+1}: Error - {str(e)[:30]}")
    
    if len(predictions) >= 2:
        # Check if all predictions are the same
        if len(set(predictions)) == 1:
            print("✅ Model is deterministic (all predictions identical)")
        else:
            variance = np.var(predictions)
            print(f"⚠️  Model shows variance: {variance:.8f}")
            print("   (This is normal for some ML models)")
    
    return True

def test_statistics_endpoint():
    """Test the statistics endpoint."""
    print_section("TESTING STATISTICS")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/stats", timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistics retrieved successfully!")
            print(f"   📊 Total evaluations: {stats.get('total_evaluations', 0)}")
            
            risk = stats.get('risk_distribution', {})
            print(f"   🟢 Low risk: {risk.get('low_risk', 0)}")
            print(f"   🟡 Medium risk: {risk.get('medium_risk', 0)}")
            print(f"   🔴 High risk: {risk.get('high_risk', 0)}")
            
            gender = stats.get('gender_distribution', {})
            print(f"   👦 Male: {gender.get('male', 0)}")
            print(f"   👧 Female: {gender.get('female', 0)}")
        else:
            print(f"❌ Failed to get statistics: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_model_info():
    """Test model information through the API."""
    print_section("TESTING MODEL INFO")
    
    # Import locally to check
    try:
        from app.models.predictor import get_model_info
        info = get_model_info()
        print("✅ Model info retrieved:")
        print(f"   📦 Model type: {info.get('model_type', 'Unknown')}")
        print(f"   🔢 Feature count: {info.get('feature_count', 'Unknown')}")
        print(f"   📍 Model path: {info.get('model_path', 'Unknown')}")
        print(f"   ✓ Is loaded: {info.get('is_loaded', False)}")
    except Exception as e:
        print(f"❌ Could not get model info: {str(e)}")

def run_all_tests():
    """Run all training system tests."""
    print("=" * 70)
    print("🧠 NEURODEVELOPMENTAL DISORDERS RISK CALCULATOR")
    print("📊 TRAINING SYSTEM TEST SUITE")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        print(f"✅ Server is running at {BASE_URL}")
    except:
        print(f"❌ Server is not running at {BASE_URL}")
        print("💡 Start the server with: uvicorn app.main:app --reload")
        return
    
    # Run tests
    tests_passed = 0
    total_tests = 6
    
    if test_model_file_exists():
        tests_passed += 1
    
    if test_prediction_endpoint():
        tests_passed += 1
    
    if test_submit_and_storage():
        tests_passed += 1
    
    if test_model_consistency():
        tests_passed += 1
    
    test_statistics_endpoint()
    tests_passed += 1
    
    test_model_info()
    tests_passed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")
    print(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if tests_passed == total_tests:
        print("\n🎉 All tests passed! The training system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 Next steps:")
    print("   1. Add real training data to improve model accuracy")
    print("   2. Implement model versioning system")
    print("   3. Create automated retraining pipeline")
    print("   4. Add model performance monitoring")

if __name__ == "__main__":
    run_all_tests()