#!/usr/bin/env python3
"""
Script to properly restart server and test endpoints.
Updated to detect and handle route prefix issues.
"""
import subprocess
import time
import requests
import psutil
import sys
import os
import signal
from datetime import datetime

def kill_existing_servers():
    """Kill any existing uvicorn processes on port 8000"""
    print("🔍 Checking for existing servers on port 8000...")
    
    killed_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and any('uvicorn' in str(cmd) for cmd in cmdline):
                if any('8000' in str(cmd) for cmd in cmdline):
                    print(f"   🔪 Killing existing uvicorn process: PID {proc.info['pid']}")
                    proc.terminate()
                    killed_processes.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed_processes:
        print(f"   ✅ Killed {len(killed_processes)} existing processes")
        time.sleep(3)  # Wait for processes to fully terminate
    else:
        print("   ℹ️  No existing uvicorn processes found")
    
    # Also check if port is still in use
    for conn in psutil.net_connections():
        if hasattr(conn, 'laddr') and conn.laddr.port == 8000:
            try:
                proc = psutil.Process(conn.pid)
                print(f"   🔪 Force killing process using port 8000: PID {conn.pid}")
                proc.kill()
                time.sleep(1)
            except:
                pass

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting FastAPI server...")
    
    # Get the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    print(f"   📁 Working directory: {project_dir}")
    
    # Check if virtual environment is activated
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        print(f"   🐍 Using virtual environment: {venv_path}")
    else:
        print("   ⚠️  No virtual environment detected")
    
    # Start server as subprocess
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload",
        "--log-level", "info"
    ]
    
    print(f"   📝 Command: {' '.join(cmd)}")
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = project_dir
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        env=env
    )
    
    # Wait for server to start
    print("   ⏳ Waiting for server to start...")
    server_ready = False
    max_wait = 20
    start_time = time.time()
    
    # Read output while waiting
    for i in range(max_wait):
        try:
            # Check if server responds
            response = requests.get("http://localhost:8000/", timeout=1)
            if response.status_code == 200:
                print(f"\n   ✅ Server started successfully after {i+1} seconds!")
                server_ready = True
                break
        except:
            pass
        
        # Show server output
        if process.poll() is None:  # Process is still running
            print(f"   ⏳ Still waiting... ({i+1}/{max_wait})")
            time.sleep(1)
        else:
            # Process exited
            print("   ❌ Server process exited unexpectedly!")
            break
    
    if not server_ready:
        print("\n   ❌ Server failed to start properly")
        # Try to get any error output
        try:
            output, _ = process.communicate(timeout=1)
            if output:
                print("   📋 Server output:")
                print(output)
        except:
            pass
        return None
    
    return process

def detect_route_structure():
    """Detect the actual route structure by checking different URL patterns"""
    print("\n🔍 Detecting route structure...")
    
    base_url = "http://localhost:8000"
    
    # Check OpenAPI schema to understand routes
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi = response.json()
            paths = list(openapi.get('paths', {}).keys())
            print(f"   📋 Found {len(paths)} registered paths:")
            for path in paths[:10]:  # Show first 10
                print(f"      - {path}")
            if len(paths) > 10:
                print(f"      ... and {len(paths) - 10} more")
            return paths
    except:
        pass
    
    # Fallback: test common patterns
    test_patterns = [
        "/api/v1/submit",
        "/api/v1/api/v1/submit",  # Double prefix (your case)
        "/submit",
        "/api/submit"
    ]
    
    working_patterns = []
    print("   🧪 Testing common URL patterns...")
    
    for pattern in test_patterns:
        try:
            # Test with minimal data
            test_data = {
                "edad": 5,
                "sexo": "M",
                "respuestas": [True] * 40,
                "acepto_consentimiento": True
            }
            response = requests.post(
                f"{base_url}{pattern}",
                json=test_data,
                timeout=2
            )
            if response.status_code in [200, 201, 422]:  # 422 is validation error but means endpoint exists
                working_patterns.append(pattern)
                print(f"      ✅ {pattern} - EXISTS (status: {response.status_code})")
            else:
                print(f"      ❌ {pattern} - NOT FOUND")
        except:
            print(f"      ❌ {pattern} - ERROR")
    
    return working_patterns

def test_endpoints():
    """Test all API endpoints with automatic detection of route structure"""
    print("\n🧪 Testing all API endpoints...")
    
    # First detect the actual route structure
    detected_routes = detect_route_structure()
    
    # Determine if we have double prefix issue
    has_double_prefix = "/api/v1/api/v1/submit" in detected_routes
    
    if has_double_prefix:
        print("\n⚠️  DETECTED: Double prefix issue! Routes are at /api/v1/api/v1/*")
        print("   This happens when the router already includes the prefix.")
        submit_prefix = "/api/v1/api/v1"
    else:
        submit_prefix = "/api/v1"
    
    endpoints = [
        # Basic endpoints (these seem to work correctly)
        {"method": "GET", "path": "/", "name": "Root"},
        {"method": "GET", "path": "/health", "name": "Health Check"},
        {"method": "GET", "path": "/api/v1/health", "name": "API Health"},
        {"method": "GET", "path": "/docs", "name": "API Documentation"},
        {"method": "GET", "path": "/openapi.json", "name": "OpenAPI Schema"},
        
        # Prediction endpoint (works correctly)
        {
            "method": "POST", 
            "path": "/api/v1/predict", 
            "name": "Prediction",
            "data": {
                "responses": [True, False] * 20,  # 40 responses
                "age": 8,
                "sex": "M"
            }
        },
        
        # Submit endpoints (with detected prefix)
        {
            "method": "POST",
            "path": f"{submit_prefix}/submit",
            "name": "Submit Evaluation",
            "data": {
                "edad": 7,
                "sexo": "F",
                "respuestas": [True, False, True, False] * 10,  # 40 responses
                "acepto_consentimiento": True
            }
        },
        
        # Query endpoints (with detected prefix)
        {"method": "GET", "path": f"{submit_prefix}/evaluaciones", "name": "List Evaluations"},
        {"method": "GET", "path": f"{submit_prefix}/evaluaciones/1", "name": "Get Evaluation #1"},
        {"method": "GET", "path": f"{submit_prefix}/stats", "name": "Statistics"},
    ]
    
    base_url = "http://localhost:8000"
    results = {"success": 0, "failed": 0}
    
    print(f"\n{'Method':<8} {'Endpoint':<40} {'Status':<8} {'Result'}")
    print("-" * 80)
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint['path']}"
        try:
            if endpoint['method'] == "GET":
                response = requests.get(url, timeout=5)
            elif endpoint['method'] == "POST":
                response = requests.post(
                    url, 
                    json=endpoint.get('data', {}),
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
            
            status = response.status_code
            
            if status < 400:
                results["success"] += 1
                print(f"{endpoint['method']:<8} {endpoint['path']:<40} {status:<8} ✅ {endpoint['name']}")
                
                # Show sample response for key endpoints
                if endpoint['path'].endswith('/predict') or endpoint['path'].endswith('/submit'):
                    if status in [200, 201]:
                        data = response.json()
                        if 'prediction' in data:
                            prob = data['prediction']['probability']
                            risk = data['prediction']['risk_level']
                            print(f"{'':>58} └─ Risk: {prob:.2f} ({risk})")
                        elif 'probability' in data:
                            print(f"{'':>58} └─ Risk: {data['probability']:.2f} ({data['risk_level']})")
            else:
                results["failed"] += 1
                print(f"{endpoint['method']:<8} {endpoint['path']:<40} {status:<8} ❌ {endpoint['name']}")
                if response.text and len(response.text) < 100:
                    print(f"{'':>58} └─ {response.text[:50]}")
                
        except requests.exceptions.RequestException as e:
            results["failed"] += 1
            print(f"{endpoint['method']:<8} {endpoint['path']:<40} {'ERROR':<8} 💥 {str(e)[:30]}")
    
    # Summary
    print("\n" + "=" * 80)
    print(f"📊 ENDPOINT TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {results['success']} endpoints")
    print(f"❌ Failed: {results['failed']} endpoints")
    
    if has_double_prefix:
        print("\n🔧 FIX NEEDED: Remove duplicate prefix in main.py")
        print("   Change: app.include_router(submit_router, prefix='/api/v1')")
        print("   To:     app.include_router(submit_router)")
        print("   (The submit_router already has prefix='/api/v1' defined)")
    
    return results["failed"] == 0

def check_project_files():
    """Check if all required project files exist"""
    print("\n📁 Checking project structure...")
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/database.py",
        "app/models/predictor.py",
        "app/models/evaluacion.py",
        "app/routes/predict.py",
        "app/routes/submit.py",
        "app/schemas/request.py",
        "app/schemas/submit.py",
        "data/modelo_entrenado.pkl",
        "requirements.txt"
    ]
    
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - MISSING")
            missing.append(file)
    
    if missing:
        print(f"\n   ⚠️  Missing {len(missing)} files!")
        return False
    else:
        print("\n   ✅ All required files present")
        return True

def check_router_configuration():
    """Check router configuration in main.py"""
    print("\n🔍 Checking router configuration...")
    
    try:
        with open("app/main.py", "r") as f:
            content = f.read()
            
        # Check for duplicate prefix
        if 'app.include_router(submit_router, prefix="/api/v1"' in content:
            print("   ⚠️  Found: submit_router with prefix='/api/v1' in main.py")
            
            # Check submit.py for existing prefix
            with open("app/routes/submit.py", "r") as f:
                submit_content = f.read()
                if 'prefix="/api/v1"' in submit_content:
                    print("   ⚠️  Also found: prefix='/api/v1' in submit.py router definition")
                    print("   ❌ DOUBLE PREFIX DETECTED! This creates /api/v1/api/v1/* routes")
                    return False
        
        print("   ✅ Router configuration looks correct")
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking configuration: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("🧠 NEURODEVELOPMENTAL DISORDERS RISK CALCULATOR")
    print("🔄 SERVER RESTART AND TEST SCRIPT")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check project files
    if not check_project_files():
        print("\n❌ Please fix missing files before continuing")
        return
    
    # Step 2: Check router configuration
    check_router_configuration()
    
    # Step 3: Kill existing servers
    kill_existing_servers()
    
    # Step 4: Start new server
    server_process = start_server()
    
    if not server_process:
        print("\n❌ Failed to start server. Check the error messages above.")
        return
    
    # Give server a moment to fully initialize
    time.sleep(2)
    
    # Step 5: Test endpoints
    all_tests_passed = test_endpoints()
    
    print("\n" + "=" * 80)
    print("🏁 SERVER STATUS")
    print("=" * 80)
    
    if all_tests_passed:
        print("✅ Server is running correctly!")
    else:
        print("⚠️  Server is running but has configuration issues")
    
    print("\n📍 API URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🧪 Run tests: python test_api.py")
    print("🔬 Test ML system: python test_training_system.py")
    
    print("\n💡 Server is running in the background.")
    print("Press Ctrl+C to stop the server when you're done testing.")
    
    try:
        # Keep script running and show server logs
        print("\n📋 Server logs:")
        print("-" * 80)
        while True:
            output = server_process.stdout.readline()
            if output:
                print(output.strip())
            elif server_process.poll() is not None:
                print("\n❌ Server process terminated unexpectedly!")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
        print("✅ Server stopped")
        print(f"🕐 Ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()