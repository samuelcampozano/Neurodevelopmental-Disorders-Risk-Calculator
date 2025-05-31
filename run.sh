#!/bin/bash

# Neurodevelopmental Disorders Risk Calculator - Run Script
# This script starts the FastAPI server with proper configuration

echo "🧠 Starting Neurodevelopmental Disorders Risk Calculator..."
echo "📁 Current directory: $(pwd)"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment is active: $VIRTUAL_ENV"
else
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating your virtual environment first:"
    echo "   Windows: .\\venv\\Scripts\\activate"
    echo "   Linux/Mac: source venv/bin/activate"
fi

# Check if required directories exist
if [ ! -d "app" ]; then
    echo "❌ Error: 'app' directory not found!"
    echo "   Make sure you're running this script from the project root"
    exit 1
fi

if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
fi

# Check if the ML model exists
if [ ! -f "data/modelo_entrenado.pkl" ]; then
    echo "⚠️  Warning: ML model not found at data/modelo_entrenado.pkl"
    echo "   The application will start but predictions may not work"
fi

# Set Python path to include the current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "🚀 Starting server on http://localhost:8000"
echo "📚 API Documentation will be available at http://localhost:8000/docs"
echo "🔄 Press Ctrl+C to stop the server"
echo ""

# Start the server using the app.main module
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload