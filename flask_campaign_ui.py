#!/usr/bin/env python3
"""
Flask UI with Phased Campaign System
Integrates Campaign Manager with AI DM
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import secrets
import os
from pathlib import Path

# Import campaign manager
from campaign_manager import CampaignManager, Character, get_campaign_manager

# Import AI DM components
try:
    from ai_dm_query_router import QueryRouter
    from ai_dm_free import OllamaDM, GameState
except ImportError:
    print("Warning: AI DM modules not found")
    OllamaDM = None
    GameState = None

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize systems
campaign_mgr = get_campaign_manager()
SRD_PATH = "./srd_story_cycle"
dm = None
if os.path.exists(SRD_PATH) and OllamaDM:
    dm = OllamaDM(SRD_PATH, default_model="llama3.2:3b")


# ============================================================================
# Campaign Management Routes
# ============================================================================

@app.route('/')
def index():
    """Main landing page - campaign selection"""
    campaigns = campaign_mgr.list_campaigns()
    return render_template('campaign_list.html', campaigns=campaigns)

@app.route('/campaign/new', methods=['GET', 'POST'])
def new_campaign():
    """Create new campaign"""
    if request.method == 'POST':
        data = request.json
        try:
            campaign = campaign_mgr.create_campaign(
                name=data['name'],
                party_size=int(data['party_size']),
                description=data.get('description', '')
            )
            return jsonify({'success': True, 'campaign': campaign.name})
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    return render_template('new_campaign.html')

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
# Phase 1: Setup & Character Creation
# ============================================================================

@app.route('/campaign/<campaign_name>/setup')
def setup_phase(campaign_name):
    """Setup and character creation phase"""
    try:
        campaign = campaign_mgr.load_campaign(campaign_name)
        characters = campaign_mgr.get_characters(campaign_name)
        
        return render_template('setup_phase.html', 
                             campaign=campaign,
                             characters=characters)
    except Exception as e:
        return f"Error: {e}", 404

@app.route('/campaign/<campaign_name>/character/add', methods=['POST'])
def add_character(campaign_name):
    """Add a new character"""
    data = request.json
    
    try:
        character = Character(
            name=data['name'],
            race=data['race'],
            char_class=data['class'],
            background=data['background'],
            level=int(data.get('level', 1)),
            hp=int(data.get('hp', 10)),
            max_hp=int(data.get('max_hp', 10)),
            ac=int(data.get('ac', 10)),
            stats=data.get('stats', {}),
            inventory=data.get('inventory', []),
            notes=data.get('notes', '')
        )
        
        campaign = campaign_mgr.add_character(campaign_name, character)
        
        return jsonify({
            'success': True,
            'setup_complete': campaign.setup_complete,
            'characters_count': len(campaign.characters),
            'party_size': campaign.party_size
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/campaign/<campaign_name>/advance', methods=['POST'])
def advance_phase(campaign_name):
    """Advance to next phase"""
    try:
        campaign = campaign_mgr.advance_phase(campaign_name)
        return jsonify({
            'success': True,
            'new_phase': campaign.current_phase
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Phase 2: Call to Adventure & Preparation
# ============================================================================

@app.route('/campaign/<campaign_name>/adventure')
def adventure_phase(campaign_name):
    """Call to adventure and preparation phase"""
    try:
        context = campaign_mgr.get_campaign_context(campaign_name)
        return render_template('adventure_phase.html', context=context)
    except Exception as e:
        return f"Error: {e}", 404

@app.route('/campaign/<campaign_name>/ai-assist', methods=['POST'])
def ai_assist(campaign_name):
    """Get AI assistance in current phase"""
    data = request.json
    query = data.get('query', '').strip()
    
    if not query or not dm or not dm.ollama_available:
        return jsonify({'error': 'AI not available'}), 503
    
    try:
        # Get campaign context
        context = campaign_mgr.get_campaign_context(campaign_name)
        campaign = context['campaign']
        
        # Create game state based on phase
        game_state = GameState(
            current_phase=context['available_story_phases'][0],  # Use first available story phase
            party_level=1,
            location=campaign['name'],
            active_combat=False,
            recent_events=[]
        )
        
        # Get AI response with campaign context
        result = dm.get_response(query, game_state)
        
        if 'error' in result:
            return jsonify(result), 500
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/campaign/<campaign_name>/complete-phase', methods=['POST'])
def complete_phase(campaign_name):
    """Mark current phase as complete"""
    data = request.json
    phase = data.get('phase')
    
    try:
        campaign = campaign_mgr.mark_phase_complete(campaign_name, phase)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Phase 3: Active Campaign
# ============================================================================

@app.route('/campaign/<campaign_name>/play')
def active_campaign(campaign_name):
    """Active campaign gameplay"""
    try:
        context = campaign_mgr.get_campaign_context(campaign_name)
        return render_template('active_campaign.html', context=context)
    except Exception as e:
        return f"Error: {e}", 404

@app.route('/campaign/<campaign_name>/session/new', methods=['POST'])
def new_session(campaign_name):
    """Start a new session"""
    try:
        session_num = campaign_mgr.start_new_session(campaign_name)
        return jsonify({'success': True, 'session_number': session_num})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================================
# Template Creation
# ============================================================================

def create_templates():
    """Create HTML templates"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Campaign List Template
    campaign_list_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Campaign Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d1b3d 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        h1 {
            color: #ff6b6b;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2.5em;
        }
        .campaigns-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .campaign-card {
            background: rgba(30, 30, 46, 0.8);
            border: 2px solid #4a4a6a;
            border-radius: 10px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .campaign-card:hover {
            transform: translateY(-5px);
            border-color: #ff6b6b;
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.3);
        }
        .campaign-name {
            font-size: 1.5em;
            color: #ff6b6b;
            margin-bottom: 10px;
        }
        .campaign-info {
            color: #b0b0b0;
            font-size: 0.9em;
            margin: 5px 0;
        }
        .phase-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8em;
            margin-top: 10px;
        }
        .phase-setup { background: #ff6b6b; }
        .phase-adventure { background: #51cf66; }
        .phase-active { background: #4dabf7; }
        .new-campaign-btn {
            display: block;
            width: 200px;
            margin: 0 auto 30px;
            padding: 15px;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .new-campaign-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.5);
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎲 Campaign Manager</h1>
        
        <button class="new-campaign-btn" onclick="location.href='/campaign/new'">
            ⚔️ New Campaign
        </button>
        
        {% if campaigns %}
        <div class="campaigns-grid">
            {% for campaign in campaigns %}
            <div class="campaign-card" onclick="location.href='/campaign/{{ campaign.name }}'">
                <div class="campaign-name">{{ campaign.name }}</div>
                <div class="campaign-info">👥 Party: {{ campaign.party_size }}</div>
                <div class="campaign-info">📅 Created: {{ campaign.created_date.split('T')[0] }}</div>
                <div class="campaign-info">📖 Sessions: {{ campaign.session_number }}</div>
                <span class="phase-badge phase-{{ campaign.current_phase }}">
                    {{ campaign.current_phase.replace('_', ' ').title() }}
                </span>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty-state">
            <h2>No campaigns yet!</h2>
            <p>Create your first campaign to begin your adventure.</p>
        </div>
        {% endif %}
    </div>
</body>
</html>"""
    
    with open(templates_dir / 'campaign_list.html', 'w', encoding='utf-8') as f:
        f.write(campaign_list_html)
    
    # New Campaign Template
    new_campaign_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Campaign</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d1b3d 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 40px 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: rgba(30, 30, 46, 0.8);
            border: 2px solid #4a4a6a;
            border-radius: 10px;
            padding: 40px;
        }
        h1 {
            color: #ff6b6b;
            margin-bottom: 30px;
            text-align: center;
        }
        label {
            display: block;
            margin: 20px 0 8px;
            color: #b0b0b0;
            font-weight: bold;
        }
        input, textarea, select {
            width: 100%;
            padding: 12px;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #4a4a6a;
            border-radius: 6px;
            color: #e0e0e0;
            font-size: 16px;
        }
        textarea {
            min-height: 100px;
            resize: vertical;
        }
        .party-size-selector {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin: 15px 0;
        }
        .party-btn {
            padding: 15px;
            background: rgba(74, 74, 106, 0.5);
            border: 2px solid #4a4a6a;
            border-radius: 6px;
            color: #e0e0e0;
            cursor: pointer;
            transition: all 0.3s;
        }
        .party-btn:hover {
            border-color: #ff6b6b;
        }
        .party-btn.selected {
            background: #ff6b6b;
            border-color: #ff6b6b;
        }
        button {
            width: 100%;
            padding: 15px;
            margin-top: 30px;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(255, 107, 107, 0.5);
        }
        .back-btn {
            background: #666;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚔️ Create New Campaign</h1>
        
        <form id="campaign-form">
            <label>Campaign Name *</label>
            <input type="text" id="name" required placeholder="The Lost Mines of Phandelver">
            
            <label>Party Size * (max 8)</label>
            <div class="party-size-selector">
                <div class="party-btn" onclick="selectPartySize(1)">1</div>
                <div class="party-btn" onclick="selectPartySize(2)">2</div>
                <div class="party-btn" onclick="selectPartySize(3)">3</div>
                <div class="party-btn" onclick="selectPartySize(4)">4</div>
                <div class="party-btn" onclick="selectPartySize(5)">5</div>
                <div class="party-btn" onclick="selectPartySize(6)">6</div>
                <div class="party-btn" onclick="selectPartySize(7)">7</div>
                <div class="party-btn" onclick="selectPartySize(8)">8</div>
            </div>
            <input type="hidden" id="party-size" required>
            
            <label>Campaign Description</label>
            <textarea id="description" placeholder="A classic adventure of heroes seeking fortune and glory..."></textarea>
            
            <button type="submit">Create Campaign</button>
            <button type="button" class="back-btn" onclick="location.href='/'">Cancel</button>
        </form>
    </div>
    
    <script>
        let selectedPartySize = null;
        
        function selectPartySize(size) {
            selectedPartySize = size;
            document.getElementById('party-size').value = size;
            
            // Update UI
            document.querySelectorAll('.party-btn').forEach(btn => {
                btn.classList.remove('selected');
            });
            event.target.classList.add('selected');
        }
        
        document.getElementById('campaign-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!selectedPartySize) {
                alert('Please select a party size');
                return;
            }
            
            const data = {
                name: document.getElementById('name').value,
                party_size: selectedPartySize,
                description: document.getElementById('description').value
            };
            
            const response = await fetch('/campaign/new', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                location.href = '/campaign/' + result.campaign;
            } else {
                alert('Error: ' + result.error);
            }
        });
    </script>
</body>
</html>"""
    
    with open(templates_dir / 'new_campaign.html', 'w', encoding='utf-8') as f:
        f.write(new_campaign_html)
    
    # Setup Phase Template
    setup_phase_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setup - {{ campaign.name }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d1b3d 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #ff6b6b;
            margin-bottom: 10px;
        }
        .phase-header {
            background: rgba(30, 30, 46, 0.8);
            border: 2px solid #4a4a6a;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .progress {
            margin: 15px 0;
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b 0%, #51cf66 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .panel {
            background: rgba(30, 30, 46, 0.8);
            border: 2px solid #4a4a6a;
            border-radius: 10px;
            padding: 20px;
        }
        h2 {
            color: #ff6b6b;
            margin-bottom: 15px;
        }
        .character-list {
            margin: 15px 0;
        }
        .character-card {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 3px solid #51cf66;
        }
        .character-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #51cf66;
        }
        .character-info {
            color: #b0b0b0;
            font-size: 0.9em;
            margin-top: 5px;
        }
        input, select {
            width: 100%;
            padding: 10px;
            margin: 8px 0;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #4a4a6a;
            border-radius: 6px;
            color: #e0e0e0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 10px 0;
        }
        .stat-wrapper {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(0, 0, 0, 0.2);
            padding: 8px;
            border-radius: 6px;
        }
        .stat-label {
            font-weight: bold;
            color: #ff6b6b;
            min-width: 45px;
            font-size: 14px;
        }
        .stat-input {
            flex: 1;
            text-align: center;
            margin: 0 !important;
            padding: 8px !important;
        }
        #points-remaining {
            padding: 10px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 6px;
        }
        #points-remaining.over-budget {
            background: rgba(255, 107, 107, 0.3);
            color: #ff6b6b;
        }
        button {
            width: 100%;
            padding: 12px;
            margin-top: 10px;
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            border: none;
            border-radius: 6px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(255, 107, 107, 0.4);
        }
        button:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
        }
        .advance-btn {
            background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="phase-header">
            <h1>⚔️ {{ campaign.name }}</h1>
            <p>📍 Phase 1: Setup & Character Creation</p>
            
            <div class="progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ (characters|length / campaign.party_size * 100)|int }}%">
                        {{ characters|length }} / {{ campaign.party_size }} Characters
                    </div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="panel">
                <h2>Create Character</h2>
                
                <form id="character-form">
                    <input type="text" id="char-name" placeholder="Character Name" required>
                    
                    <select id="char-race" required>
                        <option value="">Select Race</option>
                        <option value="Human">Human</option>
                        <option value="Elf">Elf</option>
                        <option value="Dwarf">Dwarf</option>
                        <option value="Halfling">Halfling</option>
                        <option value="Dragonborn">Dragonborn</option>
                        <option value="Gnome">Gnome</option>
                        <option value="Half-Elf">Half-Elf</option>
                        <option value="Half-Orc">Half-Orc</option>
                        <option value="Tiefling">Tiefling</option>
                    </select>
                    
                    <select id="char-class" required>
                        <option value="">Select Class</option>
                        <option value="Barbarian">Barbarian</option>
                        <option value="Bard">Bard</option>
                        <option value="Cleric">Cleric</option>
                        <option value="Druid">Druid</option>
                        <option value="Fighter">Fighter</option>
                        <option value="Monk">Monk</option>
                        <option value="Paladin">Paladin</option>
                        <option value="Ranger">Ranger</option>
                        <option value="Rogue">Rogue</option>
                        <option value="Sorcerer">Sorcerer</option>
                        <option value="Warlock">Warlock</option>
                        <option value="Wizard">Wizard</option>
                    </select>
                    
                    <select id="char-background" required>
                        <option value="">Select Background</option>
                        <option value="Acolyte">Acolyte</option>
                        <option value="Criminal">Criminal</option>
                        <option value="Folk Hero">Folk Hero</option>
                        <option value="Noble">Noble</option>
                        <option value="Sage">Sage</option>
                        <option value="Soldier">Soldier</option>
                    </select>
                    
                    <h3 style="margin-top: 15px;">Ability Scores (60 points total)</h3>
                    <div id="points-remaining" style="text-align: center; font-size: 1.2em; color: #51cf66; margin-bottom: 10px;">
                        Points Remaining: <span id="points-left">0</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 10px 0;">
                        <div class="stat-wrapper">
                            <label class="stat-label">STR</label>
                            <input type="number" class="stat-input" id="str" min="1" max="20" value="10" onchange="updatePoints()">
                        </div>
                        <div class="stat-wrapper">
                            <label class="stat-label">DEX</label>
                            <input type="number" class="stat-input" id="dex" min="1" max="20" value="10" onchange="updatePoints()">
                        </div>
                        <div class="stat-wrapper">
                            <label class="stat-label">CON</label>
                            <input type="number" class="stat-input" id="con" min="1" max="20" value="10" onchange="updatePoints()">
                        </div>
                        <div class="stat-wrapper">
                            <label class="stat-label">INT</label>
                            <input type="number" class="stat-input" id="int" min="1" max="20" value="10" onchange="updatePoints()">
                        </div>
                        <div class="stat-wrapper">
                            <label class="stat-label">WIS</label>
                            <input type="number" class="stat-input" id="wis" min="1" max="20" value="10" onchange="updatePoints()">
                        </div>
                        <div class="stat-wrapper">
                            <label class="stat-label">CHA</label>
                            <input type="number" class="stat-input" id="cha" min="1" max="20" value="10" onchange="updatePoints()">
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                        <div class="stat-wrapper">
                            <label class="stat-label">HP</label>
                            <input type="number" class="stat-input" id="char-hp" min="1" value="10">
                        </div>
                        <div class="stat-wrapper">
                            <label class="stat-label">AC</label>
                            <input type="number" class="stat-input" id="char-ac" min="1" value="10">
                        </div>
                    </div>
                    
                    <button type="submit">Add Character</button>
                </form>
            </div>
            
            <div class="panel">
                <h2>Party Members ({{ characters|length}}/{{ campaign.party_size }})</h2>
                
                <div class="character-list">
                    {% if characters %}
                        {% for char in characters %}
                        <div class="character-card">
                            <div class="character-name">{{ char.name }}</div>
                            <div class="character-info">
                                {{ char.race }} {{ char.char_class }} | {{ char.background }}
                            </div>
                            <div class="character-info">
                                HP: {{ char.hp }}/{{ char.max_hp }} | AC: {{ char.ac }}
                            </div>
                        </div>
                        {% endfor %}
                    {% else %}
                        <p style="color: #888; text-align: center; padding: 40px 0;">
                            No characters yet. Create your first character!
                        </p>
                    {% endif %}
                </div>
                
                {% if campaign.setup_complete %}
                <button class="advance-btn" onclick="advancePhase()">
                    ✨ Advance to Call to Adventure
                </button>
                {% else %}
                <button disabled>
                    Add {{ campaign.party_size - characters|length }} more character(s)
                </button>
                {% endif %}
            </div>
        </div>
    </div>
    
    <script>
        const MAX_POINTS = 60;
        
        function updatePoints() {
            const str = parseInt(document.getElementById('str').value) || 0;
            const dex = parseInt(document.getElementById('dex').value) || 0;
            const con = parseInt(document.getElementById('con').value) || 0;
            const int = parseInt(document.getElementById('int').value) || 0;
            const wis = parseInt(document.getElementById('wis').value) || 0;
            const cha = parseInt(document.getElementById('cha').value) || 0;
            
            const total = str + dex + con + int + wis + cha;
            const remaining = MAX_POINTS - total;
            
            const pointsLeftSpan = document.getElementById('points-left');
            const pointsDiv = document.getElementById('points-remaining');
            
            pointsLeftSpan.textContent = remaining;
            
            if (remaining < 0) {
                pointsDiv.classList.add('over-budget');
                pointsLeftSpan.style.color = '#ff6b6b';
            } else {
                pointsDiv.classList.remove('over-budget');
                pointsLeftSpan.style.color = '#51cf66';
            }
        }
        
        // Initialize on load
        window.onload = updatePoints;
        
        document.getElementById('character-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Check point total
            const str = parseInt(document.getElementById('str').value);
            const dex = parseInt(document.getElementById('dex').value);
            const con = parseInt(document.getElementById('con').value);
            const int = parseInt(document.getElementById('int').value);
            const wis = parseInt(document.getElementById('wis').value);
            const cha = parseInt(document.getElementById('cha').value);
            
            const total = str + dex + con + int + wis + cha;
            
            if (total > MAX_POINTS) {
                alert(`Total ability points (${total}) exceeds maximum of ${MAX_POINTS}!`);
                return;
            }
            
            const data = {
                name: document.getElementById('char-name').value,
                race: document.getElementById('char-race').value,
                class: document.getElementById('char-class').value,
                background: document.getElementById('char-background').value,
                hp: parseInt(document.getElementById('char-hp').value),
                max_hp: parseInt(document.getElementById('char-hp').value),
                ac: parseInt(document.getElementById('char-ac').value),
                stats: {
                    strength: str,
                    dexterity: dex,
                    constitution: con,
                    intelligence: int,
                    wisdom: wis,
                    charisma: cha
                }
            };
            
            const response = await fetch('/campaign/{{ campaign.name }}/character/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                location.reload();
            } else {
                alert('Error: ' + result.error);
            }
        });
        
        async function advancePhase() {
            if (!confirm('Ready to move to the next phase?')) return;
            
            const response = await fetch('/campaign/{{ campaign.name }}/advance', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                location.href = '/campaign/{{ campaign.name }}';
            } else {
                alert('Error: ' + result.error);
            }
        }
    </script>
</body>
</html>"""
    
    with open(templates_dir / 'setup_phase.html', 'w', encoding='utf-8') as f:
        f.write(setup_phase_html)
    
    print("✓ Campaign templates created")


if __name__ == '__main__':
    # Create templates if they don't exist
    if not Path('templates/campaign_list.html').exists():
        print("Creating campaign templates...")
        create_templates()
    
    print("\n" + "="*60)
    print("🎲 AI Dungeon Master - Campaign System")
    print("="*60)
    
    if dm and dm.ollama_available:
        print("✓ Ollama is running")
        print(f"✓ Model: {dm.default_model}")
    else:
        print("⚠ Ollama not detected")
    
    print(f"\n📡 Server starting...")
    print(f"   Campaign Manager: http://localhost:5000")
    print("="*60 + "\n")
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)