#!/bin/bash
# Start API Server Script

cd "$(dirname "$0")"

echo "Starting Climate Context Space API Server..."
echo "============================================"

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
fi

# Start the server
echo "Starting server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
python api_server.py


