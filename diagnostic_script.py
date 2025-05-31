#!/usr/bin/env python3
"""
Diagnostic script to check FastAPI routes and identify 404 issues
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def check_routes():
    """Check all registered routes in the FastAPI app"""
    print("=" * 60)
    print("ROUTE DIAGNOSIS FOR FASTAPI APPLICATION")
    print("=" * 60)
    
    # Test if server is running
    try:
        response = requests.get(BASE_URL)
        print(f"✅ Server is running at {BASE_URL}")
        print(f"Root response: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Server is not running at {BASE_URL}")
        print("Please start the server with: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    
    # List of endpoints to test
    endpoints = [
        "/",
        "/health",
        "/api/v1/health", 
        "/api/v1/predict",
        "/api/v1/submit",
        "/api/v1/evaluaciones",
        "/api/v1/stats",
        "/docs",
        "/openapi.json"
    ]
    
    print("\n" + "=" * 60)
    print("TESTING ALL ENDPOINTS")
    print("=" * 60)
    
    working_endpoints = []
    broken_endpoints = []
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            if endpoint == "/api/v1/submit":
                # POST request for submit endpoint
                test_data = {
                    "edad_gestacional": 35,
                    "peso_nacer": 2800,
                    "apgar_1min": 8,
                    "apgar_5min": 9,
                    "edad_materna": 28,
                    "complicaciones_embarazo": False,
                    "parto_prematuro": False,
                    "infecciones_neonatales": False,
                    "ventilacion_mecanica": False,
                    "hospitalizacion_prolongada": False
                }
                response = requests.post(url, json=test_data, timeout=5)
            else:
                # GET request for other endpoints
                response = requests.get(url, timeout=5)
            
            status = response.status_code
            if status == 404:
                broken_endpoints.append((endpoint, status, "Not Found"))
                print(f"❌ {endpoint:<25} | Status: {status} | Not Found")
            elif status < 400:
                working_endpoints.append((endpoint, status))
                print(f"✅ {endpoint:<25} | Status: {status} | Working")
            else:
                broken_endpoints.append((endpoint, status, response.text[:100]))
                print(f"⚠️  {endpoint:<25} | Status: {status} | Error")
                
        except requests.exceptions.Timeout:
            broken_endpoints.append((endpoint, "TIMEOUT", "Request timed out"))
            print(f"⏱️  {endpoint:<25} | TIMEOUT")
        except Exception as e:
            broken_endpoints.append((endpoint, "ERROR", str(e)))
            print(f"💥 {endpoint:<25} | ERROR: {str(e)[:50]}...")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Working endpoints: {len(working_endpoints)}")
    print(f"❌ Broken endpoints: {len(broken_endpoints)}")
    
    if working_endpoints:
        print("\n🟢 WORKING:")
        for endpoint, status in working_endpoints:
            print(f"   {endpoint} ({status})")
    
    if broken_endpoints:
        print("\n🔴 BROKEN:")
        for endpoint, status, error in broken_endpoints:
            print(f"   {endpoint} ({status}) - {error}")
    
    # Specific diagnosis
    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    
    if "/" in [ep for ep, _ in working_endpoints] and len(broken_endpoints) > 0:
        print("🧠 LIKELY ISSUE: Routes are not properly registered")
        print("   • Root endpoint works (app is running)")
        print("   • API endpoints return 404 (routes not included)")
        print("\n🔧 SUGGESTED FIXES:")
        print("   1. Check if routers are properly included in main.py")
        print("   2. Verify router prefixes and tags")
        print("   3. Ensure all route files are imported")
        print("   4. Check for typos in route definitions")
        
    elif len(working_endpoints) == 0:
        print("🧠 LIKELY ISSUE: Server configuration problem")
        print("   • No endpoints are working")
        print("   • Check server startup and configuration")
        
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Check your app/main.py file for router includes")
    print("2. Verify route file imports")
    print("3. Check FastAPI router configuration")
    print("4. Look at server startup logs for errors")

if __name__ == "__main__":
    check_routes()