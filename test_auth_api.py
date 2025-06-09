#!/usr/bin/env python3
"""
Test script to verify authentication and protected endpoints.
Run this after starting the server to test the auth system.
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "your-api-key-change-this-in-production")

# Store token globally
access_token = None

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"🔐 {title}")
    print("=" * 70)

def test_public_endpoints():
    """Test endpoints that don't require authentication."""
    print_section("Testing Public Endpoints")
    
    public_endpoints = [
        ("GET", "/", "Root"),
        ("GET", "/health", "Health Check"),
        ("GET", "/api/v1/stats/public", "Public Stats"),
        ("POST", "/api/v1/predict", "Prediction (Public)"),
        ("POST", "/api/v1/submit", "Submit Evaluation (Public)"),
    ]
    
    for method, endpoint, name in public_endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                # Prepare test data for POST endpoints
                if "predict" in endpoint:
                    data = {
                        "responses": [True, False] * 20,  # 40 responses
                        "age": 8,
                        "sex": "M"
                    }
                elif "submit" in endpoint:
                    data = {
                        "edad": 7,
                        "sexo": "F",
                        "respuestas": [True, False, True, False] * 10,
                        "acepto_consentimiento": True
                    }
                else:
                    data = {}
                response = requests.post(url, json=data, timeout=5)
            
            status = "✅" if response.status_code < 400 else "❌"
            print(f"{status} {name:<25} | Status: {response.status_code}")
            
        except Exception as e:
            print(f"💥 {name:<25} | Error: {str(e)[:30]}")

def test_login():
    """Test login endpoint to get JWT token."""
    global access_token
    
    print_section("Testing Authentication Login")
    
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_data = {"api_key": API_KEY}
    
    try:
        response = requests.post(login_url, json=login_data, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            access_token = result.get("access_token")
            print(f"✅ Login successful!")
            print(f"   Token type: {result.get('token_type')}")
            print(f"   Token (first 20 chars): {access_token[:20]}...")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Login error: {str(e)}")
        return False

def test_protected_endpoints():
    """Test endpoints that require authentication."""
    if not access_token:
        print("\n⚠️  No access token available. Skipping protected endpoint tests.")
        return
    
    print_section("Testing Protected Endpoints")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    protected_endpoints = [
        ("GET", "/api/v1/auth/verify", "Verify Token"),
        ("GET", "/api/v1/evaluaciones", "List Evaluations"),
        ("GET", "/api/v1/stats", "Statistics"),
        ("GET", "/api/v1/model/info", "Model Info"),
        ("GET", "/api/v1/model/retrain/status", "Retrain Status"),
    ]
    
    for method, endpoint, name in protected_endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url, headers=headers, timeout=5)
            status = "✅" if response.status_code < 400 else "❌"
            print(f"{status} {name:<25} | Status: {response.status_code}")
            
            if response.status_code == 200 and "stats" in endpoint:
                stats = response.json()
                print(f"   📊 Total evaluations: {stats.get('total_evaluations', 0)}")
                
        except Exception as e:
            print(f"💥 {name:<25} | Error: {str(e)[:30]}")

def test_unauthorized_access():
    """Test that protected endpoints reject unauthorized access."""
    print_section("Testing Unauthorized Access (Should Fail)")
    
    protected_endpoints = [
        "/api/v1/evaluaciones",
        "/api/v1/stats",
        "/api/v1/model/retrain",
    ]
    
    for endpoint in protected_endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            # Try without token
            response = requests.get(url, timeout=5)
            if response.status_code == 401:
                print(f"✅ {endpoint:<30} | Correctly rejected (401)")
            else:
                print(f"❌ {endpoint:<30} | Should be 401, got {response.status_code}")
                
        except Exception as e:
            print(f"💥 {endpoint:<30} | Error: {str(e)[:30]}")

def test_admin_token():
    """Test getting admin token (development only)."""
    if os.getenv("ENV") != "development":
        print("\n⚠️  Admin token endpoint only available in development mode")
        return
    
    print_section("Testing Admin Token (Dev Only)")
    
    url = f"{BASE_URL}/api/v1/auth/admin-token"
    params = {"api_key": API_KEY}
    
    try:
        response = requests.post(url, params=params, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Admin token obtained!")
            print(f"   Expires in: {result.get('expires_in')} seconds")
            print(f"   Usage: {result.get('usage')}")
            return result.get("access_token")
        else:
            print(f"❌ Failed to get admin token: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")
    
    return None

def test_model_retrain(admin_token=None):
    """Test model retraining endpoint (requires admin token)."""
    if not admin_token:
        print("\n⚠️  No admin token available. Skipping retrain test.")
        return
    
    print_section("Testing Model Retrain (Admin Only)")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    url = f"{BASE_URL}/api/v1/model/retrain"
    
    try:
        response = requests.post(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Retrain initiated!")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
        elif response.status_code == 400:
            print(f"⚠️  Retrain rejected: {response.json().get('detail')}")
        else:
            print(f"❌ Retrain failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {str(e)}")

def main():
    """Run all authentication tests."""
    print("=" * 70)
    print("🔐 NEURODEVELOPMENTAL DISORDERS RISK CALCULATOR")
    print("🧪 AUTHENTICATION SYSTEM TEST SUITE")
    print("=" * 70)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing API at: {BASE_URL}")
    print(f"🔑 Using API Key: {API_KEY[:10]}...")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        print(f"\n✅ Server is running!")
    except:
        print(f"\n❌ Server is not running at {BASE_URL}")
        print("💡 Start the server with: uvicorn app.main:app --reload")
        return
    
    # Run tests
    test_public_endpoints()
    
    if test_login():
        test_protected_endpoints()
        test_unauthorized_access()
        
        # Test admin features in development
        if os.getenv("ENV") == "development":
            admin_token = test_admin_token()
            if admin_token:
                test_model_retrain(admin_token)
    
    print("\n" + "=" * 70)
    print("🏁 AUTHENTICATION TESTS COMPLETED")
    print("=" * 70)
    
    print("\n📋 Summary for your teammate:")
    print("1. Public endpoints work without authentication")
    print("2. Use /api/v1/auth/login with API key to get JWT token")
    print("3. Include token in Authorization header: Bearer <token>")
    print("4. Protected endpoints require valid token")
    print("5. Admin operations require special permissions")

if __name__ == "__main__":
    main()