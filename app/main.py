"""
Main FastAPI application for Neurodevelopmental Disorders Risk Calculator.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os
from datetime import datetime

# Import database configuration and models
from app.database import create_tables, get_db_info
from app.models.evaluacion import Evaluacion  # Import to register model

# Import routers
from app.routes.predict import router as predict_router
from app.routes.submit import router as submit_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="Neurodevelopmental Disorders Risk Calculator",
    description="AI-powered tool for assessing neurodevelopmental disorder risk using SCQ questionnaire",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with proper prefixes
app.include_router(predict_router, prefix="/api/v1", tags=["predictions"])
app.include_router(submit_router)  # submit_router already has prefix="/api/v1"

@app.on_event("startup")
async def startup_event():
    """
    Application startup event handler.
    Initialize database and perform startup tasks.
    """
    try:
        # Create database tables
        create_tables()
        logger.info("Application startup completed successfully")
        
        # Log database info
        db_info = get_db_info()
        logger.info(f"Database configured: {db_info['dialect']} at {db_info['database_url']}")
        
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event handler.
    """
    logger.info("Application shutdown completed")

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint providing API information.
    """
    return {
        "message": "Neurodevelopmental Disorders Risk Calculator API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/api/v1/predict",
            "submit": "/api/v1/submit",
            "evaluations": "/api/v1/evaluaciones",
            "health": "/health",
            "stats": "/api/v1/stats",
            "docs": "/docs"
        },
        "status": "operational"
    }

@app.get("/health", tags=["monitoring"])
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    try:
        # Check database connection
        db_info = get_db_info()
        
        return {
            "status": "healthy",
            "database": "connected",
            "database_type": db_info["dialect"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Health check failed: {str(e)}"
        )

@app.get("/api/v1/health", tags=["monitoring"])
async def api_health_check():
    """
    API health check endpoint for monitoring.
    """
    try:
        # Check database connection
        db_info = get_db_info()
        
        return {
            "status": "healthy",
            "api_version": "v1",
            "database": "connected",
            "database_type": db_info["dialect"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"API health check failed: {str(e)}"
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )