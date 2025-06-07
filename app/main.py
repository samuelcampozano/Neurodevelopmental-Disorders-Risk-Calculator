"""
Main FastAPI application for Neurodevelopmental Disorders Risk Calculator.
Production-ready version with proper error handling and monitoring.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime
from contextlib import asynccontextmanager

# Import database configuration and models
from app.database import create_tables, get_db_info
from app.models.evaluacion import Evaluacion  # Import to register model

# Import routers
from app.routes.predict import router as predict_router
from app.routes.submit import router as submit_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application metadata
APP_VERSION = "1.0.0"
APP_TITLE = "Neurodevelopmental Disorders Risk Calculator"
APP_DESCRIPTION = """
AI-powered tool for assessing neurodevelopmental disorder risk using SCQ questionnaire.

## Features
- Risk prediction based on 40-item SCQ questionnaire
- Demographic-aware analysis (age and sex)
- Secure data storage with consent tracking
- Statistical analytics and reporting
- RESTful API with comprehensive documentation

## Clinical Context
This tool implements screening based on the Social Communication Questionnaire (SCQ),
a validated instrument for autism spectrum disorders and related conditions.
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    try:
        logger.info("=" * 60)
        logger.info(f"Starting {APP_TITLE} v{APP_VERSION}")
        logger.info("=" * 60)
        
        # Create database tables
        create_tables()
        
        # Log database info
        db_info = get_db_info()
        logger.info(f"Database: {db_info['dialect']} at {db_info['database_url']}")
        
        # Validate ML model
        try:
            from app.models.predictor import validate_model, get_model_info
            
            if validate_model():
                model_info = get_model_info()
                logger.info(f"ML Model: {model_info['model_type']} (v{model_info['model_version']})")
                logger.info("Model validation: PASSED")
            else:
                logger.warning("Model validation: FAILED - predictions may not work")
        except Exception as e:
            logger.error(f"Model initialization error: {str(e)}")
            logger.warning("API starting without ML model - predictions will not work")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Application shutting down...")
    logger.info("Shutdown completed")

# Create FastAPI app instance
app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware configuration
# Configure appropriately for production with specific origins
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predict_router, prefix="/api/v1", tags=["predictions"])
app.include_router(submit_router)  # Already has prefix="/api/v1"

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint providing API information and status.
    """
    return {
        "message": APP_TITLE,
        "version": APP_VERSION,
        "status": "operational",
        "endpoints": {
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json"
            },
            "health": {
                "basic": "/health",
                "detailed": "/api/v1/health"
            },
            "api": {
                "predict": "/api/v1/predict",
                "submit": "/api/v1/submit",
                "evaluations": "/api/v1/evaluaciones",
                "evaluation_detail": "/api/v1/evaluaciones/{id}",
                "statistics": "/api/v1/stats"
            }
        },
        "description": "AI-powered screening tool for neurodevelopmental disorders"
    }

@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    Basic health check endpoint for monitoring.
    
    Returns:
        Simple health status with timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": APP_VERSION
    }

@app.get("/api/v1/health", tags=["monitoring"])
async def detailed_health_check():
    """
    Detailed health check with component status.
    
    Returns:
        Comprehensive health status including database and model state
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": APP_VERSION,
        "components": {}
    }
    
    # Check database
    try:
        db_info = get_db_info()
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": db_info["dialect"],
            "connected": True
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "connected": False
        }
        health_status["status"] = "degraded"
    
    # Check ML model
    try:
        from app.models.predictor import get_model_info
        model_info = get_model_info()
        
        health_status["components"]["ml_model"] = {
            "status": "healthy" if model_info.get("is_loaded") else "unhealthy",
            "loaded": model_info.get("is_loaded", False),
            "type": model_info.get("model_type", "unknown"),
            "version": model_info.get("model_version", "unknown")
        }
        
        if not model_info.get("is_loaded"):
            health_status["status"] = "degraded"
            
    except Exception as e:
        health_status["components"]["ml_model"] = {
            "status": "unhealthy",
            "error": str(e),
            "loaded": False
        }
        health_status["status"] = "degraded"
    
    # Overall status
    if health_status["status"] == "degraded":
        raise HTTPException(
            status_code=503,
            detail=health_status
        )
    
    return health_status

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """
    Custom 404 handler with helpful error message.
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested URL {request.url.path} was not found.",
            "available_endpoints": {
                "docs": "/docs",
                "health": "/health",
                "api_v1": "/api/v1/*"
            }
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Don't expose internal errors in production
    if os.getenv("ENV", "development") == "production":
        error_detail = "An internal error occurred"
    else:
        error_detail = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": error_detail,
            "request_id": request.headers.get("X-Request-ID", "N/A"),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Development-only endpoints
if os.getenv("ENV", "development") == "development":
    @app.get("/api/v1/debug/info", tags=["debug"])
    async def debug_info():
        """
        Debug endpoint showing system information.
        Only available in development mode.
        """
        try:
            from app.models.predictor import get_model_info, get_model_metrics
            model_info = get_model_info()
            model_metrics = get_model_metrics()
        except:
            model_info = {"error": "Could not load model info"}
            model_metrics = {"error": "Could not load model metrics"}
        
        return {
            "app_version": APP_VERSION,
            "environment": os.getenv("ENV", "development"),
            "python_version": os.sys.version,
            "model_info": model_info,
            "model_metrics": model_metrics,
            "total_routes": len(app.routes),
            "routes": [
                {
                    "path": route.path,
                    "methods": list(route.methods) if hasattr(route, 'methods') and route.methods else [],
                    "name": route.name if hasattr(route, 'name') else "N/A"
                }
                for route in app.routes
                if hasattr(route, 'path')
            ]
        }

if __name__ == "__main__":
    import uvicorn
    
    # Development server configuration
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )