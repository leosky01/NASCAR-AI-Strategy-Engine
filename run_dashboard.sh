#!/bin/bash

# NASCAR AI Strategy Engine - Dashboard Launcher

echo "=========================================="
echo "  NASCAR AI Strategy Engine Dashboard"
echo "=========================================="
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🚀 Starting dashboard..."
echo ""
echo "Dashboard will open at: http://localhost:8501"
echo "Press Ctrl+C to stop"
echo ""

# Start Streamlit
streamlit run app.py --server.port 8501 --server.headless false
