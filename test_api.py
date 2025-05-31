"""
Test script to verify the API functionality.
Run this after starting the server to test all endpoints.
"""

import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_root_endpoint():
    """Test the root endpoint."""
    print("Testing root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_health_endpoint():
    """Test the health check endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("-" * 50)

def test_submit_evaluation():
    """Test submitting a new evaluation."""
    print("Testing submit evaluation...")
    
    # Sample evaluation data
    evaluation_data = {
        "edad": 8,
        "sexo": "M",
        "respuestas": [
            True, False, True, False, True,
            False, True, False, True, False,
            True, False, True, False, True,
            False, True, False, True, False,
            True, False, True, False, True,
            False, True, False, True, False,
            True, False, True, False, True,
            False, True, False, True, False
        ],
        "acepto_consentimiento": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/submit",
        json=evaluation_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        print(f"Evaluation ID: {result['evaluation_id']}")
        print(f"Prediction: {json.dumps(result['prediction'], indent=2)}")
        return result['evaluation_id']
    else:
        print(f"Error: {response.text}")
        return None
    
    print("-" * 50)

def test_get_evaluations():
    """Test getting the list of evaluations."""
    print("Testing get evaluations list...")
    response = requests.get(f"{BASE_URL}/api/v1/evaluaciones")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        evaluations = response.json()
        print(f"Found {len(evaluations)} evaluations")
        if evaluations:
            print(f"Latest evaluation: {json.dumps(evaluations[0], indent=2, default=str)}")
    else:
        print(f"Error: {response.text}")
    print("-" * 50)

def test_get_evaluation_detail(evaluation_id):
    """Test getting detailed evaluation."""
    if not evaluation_id:
        print("Skipping evaluation detail test (no evaluation ID)")
        return
    
    print(f"Testing get evaluation detail for ID {evaluation_id}...")
    response = requests.get(f"{BASE_URL}/api/v1/evaluaciones/{evaluation_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        evaluation = response.json()
        print(f"Evaluation detail: {json.dumps(evaluation, indent=2, default=str)}")
    else:
        print(f"Error: {response.text}")
    print("-" * 50)

def test_get_stats():
    """Test getting evaluation statistics."""
    print("Testing get evaluation statistics...")
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"Statistics: {json.dumps(stats, indent=2)}")
    else:
        print(f"Error: {response.text}")
    print("-" * 50)

def test_predict_endpoint():
    """Test the predict endpoint."""
    print("Testing predict endpoint...")
    
    predict_data = {
        "responses": [
            True, False, True, False, True,
            False, True, False, True, False,
            True, False, True, False, True,
            False, True, False, True, False,
            True, False, True, False, True,
            False, True, False, True, False,
            True, False, True, False, True,
            False, True, False, True, False
        ],
        "age": 10,
        "sex": "F"
    }
    
    # FIXED: Use correct URL with /api/v1 prefix
    response = requests.post(
        f"{BASE_URL}/api/v1/predict",
        json=predict_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        prediction = response.json()
        print(f"Prediction: {json.dumps(prediction, indent=2)}")
    else:
        print(f"Error: {response.text}")
    print("-" * 50)

def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING NEURODEVELOPMENTAL DISORDERS RISK CALCULATOR API")
    print("=" * 60)
    
    try:
        # Test basic endpoints
        test_root_endpoint()
        test_health_endpoint()
        
        # Test the predict endpoint
        test_predict_endpoint()
        
        # Test new database-backed endpoints
        evaluation_id = test_submit_evaluation()
        test_get_evaluations()
        test_get_evaluation_detail(evaluation_id)
        test_get_stats()
        
        print("=" * 60)
        print("ALL TESTS COMPLETED")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the API server.")
        print("Please make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    main()