#!/usr/bin/env python3
"""
AI Dungeon Master - Main Application
Orchestrates all campaign phases and routes
"""

from flask import Flask
from flask_socketio import SocketIO
import secrets
import os
from pathlib import Path

# Import route blueprints
from phase1 import phase1_bp, register_phase1_routes
from phase2 import phase2_bp, register_phase2_routes
from phase3 import phase3_bp, register_phase3_routes
from main import main_bp, register_main_routes

# Import shared components
from campaign_manager import get_campaign_manager
from prompt_templates import PromptTemplates

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize shared systems
campaign_mgr = get_campaign_manager()
prompt_templates = PromptTemplates()

# Initialize AI DM if available
SRD_PATH = "./srd_story_cycle"
dm = None

try:
    from ai_dm_free import OllamaDM
    if os.path.exists(SRD_PATH):
        dm = OllamaDM(SRD_PATH, default_model="llama3.2:3b")
        print("✓ AI DM initialized with Ollama")
    else:
        print(f"⚠ SRD path not found: {SRD_PATH}")
except ImportError:
    print("⚠ AI DM modules not available")

# Store shared components in app config for access in blueprints
app.config['CAMPAIGN_MGR'] = campaign_mgr
app.config['PROMPT_TEMPLATES'] = prompt_templates
app.config['DM'] = dm
app.config['SRD_PATH'] = SRD_PATH

# Register all blueprints
app.register_blueprint(main_bp)
app.register_blueprint(phase1_bp, url_prefix='/campaign')
app.register_blueprint(phase2_bp, url_prefix='/campaign')
app.register_blueprint(phase3_bp, url_prefix='/campaign')

# Register routes (pass shared components)
register_main_routes(app, campaign_mgr, prompt_templates)
register_phase1_routes(app, campaign_mgr)
register_phase2_routes(app, campaign_mgr, dm, SRD_PATH)
register_phase3_routes(app, campaign_mgr, dm)


def create_templates():
    """Create HTML templates if they don't exist"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Check if templates already exist
    if (templates_dir / 'campaign_list.html').exists():
        return
    
    print("Creating HTML templates...")
    
    # Import template creation from main
    from main import create_all_templates
    create_all_templates()
    
    print("✓ Templates created")


if __name__ == '__main__':
    # Create templates if needed
    create_templates()
    
    print("\n" + "="*60)
    print("🎲 AI Dungeon Master - Campaign System")
    print("="*60)
    
    if dm and hasattr(dm, 'ollama_available') and dm.ollama_available:
        print("✓ Ollama is running")
        print(f"✓ Model: {dm.default_model}")
    else:
        print("⚠ Ollama not detected - AI features disabled")
    
    print(f"\n📡 Server starting...")
    print(f"   Campaign Manager: http://localhost:5000")
    print("="*60 + "\n")
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)