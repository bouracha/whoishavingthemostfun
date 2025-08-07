#!/bin/bash

# Script to start the Flask server in the virtual environment

echo "🚀 Starting Flask server..."
echo "📦 Activating virtual environment..."

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "❌ Flask not found. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "✅ Dependencies ready"
echo "🌐 Starting server at http://localhost:8080"
echo "   Press Ctrl+C to stop"
echo ""

# Start the server
python server.py