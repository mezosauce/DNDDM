#!/usr/bin/env python3
"""
AI Dungeon Master - Complete Application
Modular structure with separate phase files
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
from dataclasses import asdict  
import secrets
import os
from pathlib import Path
from datetime import datetime

# Import core modules
from component.campaign_manager import get_campaign_manager, Character
from LLM_Comp.prompt_templates import PromptTemplates, create_full_prompt
from FAISS.search_engine import SRDSearchEngine, create_search_api, FAISS_AVAILABLE, EMBEDDINGS_AVAILABLE

# Import AI DM components with better error handling
OllamaDM = None
GameState = None
QueryRouter = None
SRDContentLoader = None
Phase3QueryRouter = None
create_phase3_prompt = None
Phase3SRDLoader = None


try:
    from LLM_Comp.ai_dm_free import OllamaDM, GameState
    print("✓ AI DM core modules loaded")
except ImportError as e:
    print(f"⚠ AI DM modules not found: {e}")


try:
    from LLM_Comp.ai_dm_query_router import QueryRouter
    print("✓ Query router loaded (Phase 2)")
except ImportError:
    print("⚠ Query router not found - Phase 2 will work without SRD content")

try:
    from LLM_Comp.ai_dm_free import SRDContentLoader
    print("✓ SRD content loader available")
except (ImportError, AttributeError):
    print("⚠ SRD content loader not available")

# Import Phase 3 enhanced router
try:
    from LLM_Comp.phase3_DM import (
        Phase3QueryRouter, 
        create_phase3_prompt,
        SRDContentLoader as Phase3SRDLoader
    )
    print("✓ Phase 3 enhanced router loaded")
except ImportError as e:
    print(f"⚠ Phase 3 router not found: {e}")

# Import phase route modules
try:
    from phase_1 import register_phase1_routes
    print("✓ Phase 1 routes module loaded")
except ImportError as e:
    print(f"⚠ Phase 1 routes not found: {e}")
    register_phase1_routes = None

try:
    from phase_2 import register_phase2_routes
    print("✓ Phase 2 routes module loaded")
except ImportError as e:
    print(f"⚠ Phase 2 routes not found: {e}")
    register_phase2_routes = None

try:
    from phase_3 import register_phase3_routes
    print("✓ Phase 3 routes module loaded")
except ImportError as e:
    print(f"⚠ Phase 3 routes not found: {e}")
    register_phase3_routes = None

# Initialize Flask app with proper template path
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../FrontEnd/templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../FrontEnd/static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize systems
prompt_templates = PromptTemplates()
campaign_mgr = get_campaign_manager()
SRD_PATH = "../srd_story_cycle"
dm = None

# Initialize AI DM if available
if OllamaDM:
    try:
        dm = OllamaDM(SRD_PATH, default_model="llama3.2:3b")  
        print("✓ AI DM initialized successfully")
    except Exception as e:
        print(f"⚠ Could not initialize AI DM: {e}")
        dm = None
else:
    print("⚠ AI DM not available - install ai_dm_free.py")

# Initialize Search Engine
search_engine = None

if FAISS_AVAILABLE and EMBEDDINGS_AVAILABLE:
    try:
        search_engine = SRDSearchEngine(SRD_PATH)
        search_engine.load_index()
        print("✓ Search engine loaded successfully")
    except FileNotFoundError:
        print("⚠️  Search index not built. Run: python search_engine.py --build")
    except Exception as e:
        print(f"⚠️  Could not initialize search engine: {e}")
else:
    print("⚠️  Search engine not available")


# ============================================================================
# MAIN ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main landing page - campaign selection"""
    campaigns = campaign_mgr.list_campaigns()
    return render_template('HTML/campaign_list.html', campaigns=campaigns)


@app.route('/campaign/new', methods=['GET', 'POST'])
def new_campaign():
    """Create new campaign"""
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        try:
            campaign = campaign_mgr.create_campaign(
                name=data['name'],
                party_size=int(data['party_size']),
                description=data.get('description', '')
            )
            return jsonify({'success': True, 'campaign': campaign.name})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    return render_template('HTML/new_campaign.html')


@app.route('/campaign/<campaign_name>')
def campaign_home(campaign_name):
    """Campaign home - redirects based on current phase"""
    try:
        campaign = campaign_mgr.load_campaign(campaign_name)
        
        if campaign.current_phase == "setup":
            return redirect(url_for('setup_phase', campaign_name=campaign_name))
        elif campaign.current_phase == "call_to_adventure":
            return redirect(url_for('adventure_phase', campaign_name=campaign_name))
        else:
            return redirect(url_for('active_campaign', campaign_name=campaign_name))
    except Exception as e:
        return f"Error loading campaign: {e}", 404


# ============================================================================
# REGISTER PHASE ROUTES
# ============================================================================

# Phase 1: Setup & Character Creation
if register_phase1_routes:
    register_phase1_routes(app, campaign_mgr, Character)
    print("✓ Phase 1 routes registered")
else:
    print("⚠ Phase 1 routes not registered")

# Phase 2: Call to Adventure & Preparation
if register_phase2_routes:
    register_phase2_routes(app, campaign_mgr, dm, GameState)
    print("✓ Phase 2 routes registered")
else:
    print("⚠ Phase 2 routes not registered")

# Phase 3: Active Campaign
if register_phase3_routes:
    register_phase3_routes(
        app, campaign_mgr, dm, SRD_PATH, prompt_templates,
        Phase3QueryRouter, Phase3SRDLoader, create_phase3_prompt,
        QueryRouter, SRDContentLoader, create_full_prompt
    )
    print("✓ Phase 3 routes registered")
else:
    print("⚠ Phase 3 routes not registered")


# ============================================================================
# SEARCH API INTEGRATION
# ============================================================================

# Add search API endpoints
if search_engine:
    create_search_api(app, search_engine)
    print("✓ Search API endpoints registered")


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Create templates if needed
    
    print("\n" + "="*60)
    print("🎲 AI Dungeon Master - Campaign System")
    print("="*60)
    
    if dm and hasattr(dm, 'ollama_available') and dm.ollama_available:
        print("✓ Ollama is running")
        print(f"✓ Model: {dm.default_model}")
    else:
        print("⚠ Ollama not detected - AI features disabled")
        print("  To enable AI: Install Ollama and run 'ollama serve'")
    
    if Phase3QueryRouter:
        print("✓ Phase 3 Enhanced Router active")
    else:
        print("⚠ Phase 3 router not available")
    
    if not QueryRouter:
        print("⚠ Phase 2 router not available")
    
    print(f"\n📡 Server starting...")
    print(f"   Campaign Manager: http://localhost:5000")
    print("="*60 + "\n")
    
    # Run the server
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        print(f"⚠️  Socket.io not available: {e}")
        print("   Running without websocket support")
        app.run(host='0.0.0.0', port=5000, debug=True)

