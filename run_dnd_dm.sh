#!/bin/bash
# =================================================================
# AI Dungeon Master - Automated Startup Script (Linux/Mac/Pi)
# =================================================================

echo ""
echo "============================================================"
echo "   AI DUNGEON MASTER - STARTING UP"
echo "============================================================"
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "[1/5] Activating virtual environment..."
    source venv/bin/activate
elif [ -d "5thsrd-py3.8" ]; then
    echo "[1/5] Activating virtual environment..."
    source 5thsrd-py3.8/bin/activate
else
    echo "[1/5] No virtual environment found, using system Python..."
fi

echo ""
echo "[2/5] Deleting old templates for fresh regeneration..."
if [ -d "templates" ]; then
    rm -rf templates
    echo "   - Templates folder deleted"
else
    echo "   - No templates folder found"
fi

echo ""
echo "[3/5] Checking required files..."
MISSING_FILES=0

if [ ! -f "flask_campaign_ui.py" ]; then
    echo "   ERROR: flask_campaign_ui.py not found!"
    MISSING_FILES=1
fi
if [ ! -f "campaign_manager.py" ]; then
    echo "   ERROR: campaign_manager.py not found!"
    MISSING_FILES=1
fi
if [ ! -f "ai_dm_query_router.py" ]; then
    echo "   ERROR: ai_dm_query_router.py not found!"
    MISSING_FILES=1
fi
if [ ! -f "ai_dm_free.py" ]; then
    echo "   ERROR: ai_dm_free.py not found!"
    MISSING_FILES=1
fi

if [ $MISSING_FILES -eq 1 ]; then
    echo ""
    echo "   ERROR: Missing required files!"
    echo "   Make sure you're in the correct directory."
    exit 1
fi

echo "   - All required files found!"

echo ""
echo "[4/5] Checking if Ollama is running..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "   - Ollama is running"
else
    echo "   WARNING: Ollama not detected!"
    echo "   Start Ollama with: ollama serve"
    echo ""
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "[5/5] Starting Flask Campaign Manager..."
echo ""
echo "============================================================"
echo "   SERVER STARTING"
echo "============================================================"
echo ""
echo "   DM Interface: http://localhost:5000"
echo "   Player View:  http://localhost:5000/player"
echo ""
echo "   Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

python flask_campaign_ui.py