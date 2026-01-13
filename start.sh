#!/bin/bash
# Start script for Render

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Create necessary directories
mkdir -p data logs

# Run the application
exec uvicorn empathai_full:app --host 0.0.0.0 --port ${PORT:-8000}