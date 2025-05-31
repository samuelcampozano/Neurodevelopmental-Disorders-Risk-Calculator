#!/usr/bin/env python3
"""
Debug script to check FastAPI app configuration and routes
"""

def debug_app():
    """Debug the FastAPI application configuration"""
    print("=" * 60)
    print("DEBUGGING FASTAPI APPLICATION")
    print("=" * 60)
    
    try:
        # Import the app
        print("🔍 Attempting to import FastAPI app...")
        from app.main import app
        print("✅ Successfully imported app")
        
        # Check registered routes
        print("\n🛣️  REGISTERED ROUTES:")
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = list(route.methods) if route.methods else ['GET']
                routes.append((route.path, methods))
                print(f"   {route.path:<30} | Methods: {methods}")
            elif hasattr(route, 'path'):
                routes.append((route.path, ['MOUNT']))
                print(f"   {route.path:<30} | Type: MOUNT/INCLUDE")
        
        print(f"\n📊 Total routes found: {len(routes)}")
        
        # Check for expected routes
        expected_routes = [
            "/",
            "/health", 
            "/api/v1/health",
            "/api/v1/predict",
            "/api/v1/submit",
            "/api/v1/evaluaciones",
            "/api/v1/stats"
        ]
        
        print(f"\n🔍 CHECKING EXPECTED ROUTES:")
        missing_routes = []
        for expected in expected_routes:
            found = any(expected == route[0] for route in routes)
            if found:
                print(f"   ✅ {expected}")
            else:
                print(f"   ❌ {expected} - MISSING")
                missing_routes.append(expected)
        
        if missing_routes:
            print(f"\n🚨 MISSING ROUTES: {missing_routes}")
        
        # Check router imports
        print(f"\n🔍 CHECKING ROUTER IMPORTS:")
        try:
            from app.routes.predict import router as predict_router
            print("   ✅ predict router imported successfully")
            print(f"   📝 Routes in predict router: {len(predict_router.routes)}")
            for route in predict_router.routes:
                if hasattr(route, 'path'):
                    print(f"      - {route.path}")
        except Exception as e:
            print(f"   ❌ predict router import failed: {e}")
        
        try:
            from app.routes.submit import router as submit_router  
            print("   ✅ submit router imported successfully")
            print(f"   📝 Routes in submit router: {len(submit_router.routes)}")
            for route in submit_router.routes:
                if hasattr(route, 'path'):
                    print(f"      - {route.path}")
        except Exception as e:
            print(f"   ❌ submit router import failed: {e}")
        
        # Check database connection
        print(f"\n🔍 CHECKING DATABASE:")
        try:
            from app.database import get_db_info
            db_info = get_db_info()
            print(f"   ✅ Database connection: {db_info}")
        except Exception as e:
            print(f"   ❌ Database connection failed: {e}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Possible fixes:")
        print("   1. Check if all required files exist")
        print("   2. Verify Python path and imports")
        print("   3. Check for syntax errors in route files")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def check_file_structure():
    """Check if all required files exist"""
    print("\n" + "=" * 60)
    print("CHECKING FILE STRUCTURE")
    print("=" * 60)
    
    import os
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/routes/__init__.py", 
        "app/routes/predict.py",
        "app/routes/submit.py",
        "app/models/__init__.py",
        "app/models/predictor.py",
        "app/schemas/__init__.py",
        "app/schemas/request.py",
        "app/schemas/submit.py",
        "app/database.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n🚨 MISSING FILES: {missing_files}")
        print("🔧 These files need to be created for the app to work properly")
    
    return len(missing_files) == 0

def test_individual_imports():
    """Test importing each module individually"""
    print("\n" + "=" * 60)
    print("TESTING INDIVIDUAL IMPORTS")  
    print("=" * 60)
    
    modules_to_test = [
        "app.database",
        "app.models.evaluacion", 
        "app.models.predictor",
        "app.schemas.request",
        "app.schemas.submit",
        "app.routes.predict",
        "app.routes.submit"
    ]
    
    failed_imports = []
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module} - ERROR: {str(e)[:100]}")
            failed_imports.append((module, str(e)))
    
    if failed_imports:
        print(f"\n🚨 FAILED IMPORTS:")
        for module, error in failed_imports:
            print(f"   {module}: {error}")
    
    return len(failed_imports) == 0

if __name__ == "__main__":
    print("Starting comprehensive debug...")
    
    files_ok = check_file_structure()
    imports_ok = test_individual_imports()
    
    if files_ok and imports_ok:
        debug_app()
    else:
        print("\n🚨 Cannot debug app due to missing files or import errors")
        print("🔧 Fix the above issues first, then run this script again")