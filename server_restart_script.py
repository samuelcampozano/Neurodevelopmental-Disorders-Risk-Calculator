#!/usr/bin/env python3
"""
Script to properly restart server and test endpoints
"""
import subprocess
import time
import requests
import psutil
import sys
import os

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
                    proc.kill()
                    killed_processes.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if killed_processes:
        print(f"   ✅ Killed {len(killed_processes)} existing processes")
        time.sleep(2)  # Wait for processes to fully terminate
    else:
        print("   ℹ️  No existing uvicorn processes found")

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting FastAPI server...")
    
    # Change to the correct directory
    os.chdir(r"D:\ULEAM\Practicas laborales 2\Neurodevelopmental-Disorders-Risk-Calculator")
    
    # Start server as subprocess
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ]
    
    print(f"   📝 Command: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    print("   ⏳ Waiting for server to start...")
    max_wait = 15
    for i in range(max_wait):
        try:
            response = requests.get("http://localhost:8000/", timeout=2)
            if response.status_code == 200:
                print(f"   ✅ Server started successfully after {i+1} seconds")
                return process
        except:
            pass
        time.sleep(1)
        print(f"   ⏳ Still waiting... ({i+1}/{max_wait})")
    
    # Check if process is still running
    if process.poll() is None:
        print("   ⚠️  Server process is running but not responding")
        # Get stdout and stderr
        try:
            stdout, stderr = process.communicate(timeout=1)
            if stdout:
                print(f"   📋 STDOUT: {stdout}")
            if stderr:
                print(f"   ❌ STDERR: {stderr}")
        except subprocess.TimeoutExpired:
            print("   ⏳ Server is still starting...")
    else:
        print("   ❌ Server process exited")
        stdout, stderr = process.communicate()
        if stdout:
            print(f"   📋 STDOUT: {stdout}")
        if stderr:
            print(f"   ❌ STDERR: {stderr}")
    
    return process

def test_endpoints():
    """Test all endpoints"""
    print("\n🧪 Testing endpoints...")
    
    endpoints = [
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/evaluaciones"),
        ("GET", "/api/v1/stats"),
        ("POST", "/api/v1/predict"),
        ("POST", "/api/v1/submit")
    ]
    
    base_url = "http://localhost:8000"
    
    for method, endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                # Send minimal test data
                test_data = {"test": "data"}
                response = requests.post(url, json=test_data, timeout=5)
            
            status = response.status_code
            if status == 404:
                print(f"   ❌ {method:<4} {endpoint:<25} | 404 NOT FOUND")
            elif status < 400:
                print(f"   ✅ {method:<4} {endpoint:<25} | {status} OK")
            else:
                print(f"   ⚠️  {method:<4} {endpoint:<25} | {status} ERROR")
                
        except requests.exceptions.RequestException as e:
            print(f"   💥 {method:<4} {endpoint:<25} | CONNECTION ERROR: {str(e)[:50]}")

def check_port_usage():
    """Check what's using port 8000"""
    print("\n🔍 Checking port 8000 usage...")
    
    for conn in psutil.net_connections():
        if conn.laddr.port == 8000:
            try:
                proc = psutil.Process(conn.pid)
                print(f"   📍 Port 8000 is used by: PID {conn.pid} ({proc.name()})")
                print(f"      Command: {' '.join(proc.cmdline())}")
            except:
                print(f"   📍 Port 8000 is used by: PID {conn.pid} (unknown process)")

def main():
    print("=" * 70)
    print("FASTAPI SERVER RESTART AND TEST")
    print("=" * 70)
    
    # Step 1: Check current port usage
    check_port_usage()
    
    # Step 2: Kill existing servers
    kill_existing_servers()
    
    # Step 3: Start new server
    server_process = start_server()
    
    # Step 4: Test endpoints
    if server_process:
        test_endpoints()
        
        print("\n" + "=" * 70)
        print("SERVER IS RUNNING")
        print("=" * 70)
        print("Server is running in the background.")
        print("Press Ctrl+C to stop the server when you're done testing.")
        print("You can also run: python test_api.py")
        
        try:
            # Keep script running
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            server_process.terminate()
            server_process.wait()
            print("✅ Server stopped")
    else:
        print("\n❌ Failed to start server")

if __name__ == "__main__":
    main()