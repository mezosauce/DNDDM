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
from datetime import datetime
from prompt_templates import PromptTemplates, create_full_prompt

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
prompt_templates = PromptTemplates()
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
        # Load campaign
        campaign = campaign_mgr.load_campaign(campaign_name)
        characters = campaign_mgr.get_characters(campaign_name)
        
        # Determine phase (prep or active)
        if campaign.current_phase == "call_to_adventure":
            phase = 'prep'
        else:
            phase = 'active'
        
        # Build campaign context
        campaign_context = {
            'name': campaign.name,
            'description': campaign.description,
            'party_size': campaign.party_size,
            'characters': [
                {
                    'name': char.name,
                    'race': char.race,
                    'char_class': char.char_class,
                    'level': char.level,
                    'hp': char.hp,
                    'max_hp': char.max_hp,
                    'ac': char.ac,
                    'stats': char.stats
                }
                for char in characters
            ],
            'session_number': campaign.session_number,
            'current_location': getattr(campaign, 'current_location', 'Unknown'),
            'active_combat': getattr(campaign, 'active_combat', False),
            'recent_events': getattr(campaign, 'recent_events', [])
        }
        
        # Load relevant SRD content
        srd_content = ""
        try:
            from ai_dm_query_router import QueryRouter
            from ai_dm_free import SRDContentLoader
            
            router = QueryRouter(SRD_PATH)
            # Use first available story phase as current phase
            story_phase = campaign_mgr.get_available_story_phases(campaign.current_phase)[0] if hasattr(campaign_mgr, 'get_available_story_phases') else ''
            routing = router.route_query(query, current_phase=story_phase)
            
            # Load more files for active phase, fewer for prep
            max_files = 5 if phase == 'active' else 3
            max_chars = 15000 if phase == 'active' else 10000
            
            if routing['files_to_load']:
                loader = SRDContentLoader(SRD_PATH)
                srd_content = loader.load_files(
                    routing['files_to_load'][:max_files], 
                    max_chars=max_chars
                )
        except Exception as e:
            print(f"SRD loading warning: {e}")
        
        # Create full prompt using template system
        full_prompt = create_full_prompt(
            phase=phase,
            campaign_context=campaign_context,
            query=query,
            srd_content=srd_content
        )
        
        # Get AI response using Ollama
        import requests
        
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": dm.default_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 500 if phase == 'active' else 400,
                "repeat_penalty": 1.1
            }
        }
        
        response = requests.post(ollama_url, json=payload, timeout=60)
        response.raise_for_status()
        
        ai_response = response.json().get('response', '').strip()
        
        # Update recent events if in active phase
        if phase == 'active':
            if not hasattr(campaign, 'recent_events'):
                campaign.recent_events = []
            campaign.recent_events.append(f"Player: {query[:100]}")
            campaign.recent_events.append(f"DM: {ai_response[:100]}")
            # Keep only last 10 events
            campaign.recent_events = campaign.recent_events[-10:]
            campaign_mgr.save_campaign(campaign)
        
        return jsonify({
            'response': ai_response,
            'query': query,
            'phase': phase
        })
        
    except Exception as e:
        print(f"Error in ai_assist: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    

@app.route('/campaign/<campaign_name>/generate-options', methods=['POST'])
def generate_options(campaign_name):
    """Generate AI options for a specific quest setup step"""
    data = request.json
    step = data.get('step', '')
    
    if not dm or not dm.ollama_available:
        return jsonify({'error': 'AI not available'}), 503
    
    try:
        # Get campaign context
        context = campaign_mgr.get_campaign_context(campaign_name)
        campaign = context['campaign']
        
        # Create prompts for each step
        prompts = {
            'quest_hook': f"""Generate 5 unique quest hooks for this D&D party.

Campaign: {campaign['name']}
Party: {', '.join([c['name'] + ' (' + c['char_class'] + ')' for c in context['characters']])}

For each quest hook, provide:
- A catchy title
- A 2-sentence description
- Why this party would care

Format each option as:
## Option X: [Title]
[Description]
*Why your party cares:* [Reason]

Generate 5 diverse options.""",
            
            'objective': """Based on the chosen quest hook, generate 4 possible main objectives.

Each objective should be:
- Clear and achievable
- Appropriate for the party level
- Connected to the quest hook

Format as:
## Option X: [Objective Title]
[What success looks like]""",
            
            'location': """Generate 4 starting locations for this adventure.

Each location should:
- Match the quest theme
- Provide opportunities for exploration
- Include sensory details

Format as:
## Option X: [Location Name]
[Description with sights, sounds, atmosphere]""",
            
            'npcs': """Generate 4 key NPCs for this quest.

For each NPC include:
- Name and role
- Personality trait
- How they connect to the quest

Format as:
## Option X: [NPC Name - Role]
[Description and quest connection]""",
            
            'equipment': """Suggest 4 equipment loadouts for this adventure.

Each loadout should include:
- Essential gear for the quest type
- Tactical items
- Estimated cost

Format as:
## Option X: [Loadout Name]
[Items and reasoning]""",
            
            'roles': """Suggest 4 party role assignments based on the characters.

For each suggestion include:
- Who does what
- Tactical synergies
- Backup plans

Format as:
## Option X: [Strategy Name]
[Role assignments and reasoning]"""
        }
        
        prompt = prompts.get(step, '')
        if not prompt:
            return jsonify({'error': 'Invalid step'}), 400
        
        # Add previous selections if they exist
        selections = data.get('selections', {})
        if selections:
            prompt = f"Previous selections:\n"
            for key, value in selections.items():
                prompt += f"{key}: {value}\n"
            prompt += f"\n{prompts[step]}"
        
        # Create game state
        game_state = GameState(
            current_phase='02_call_to_adventure',
            party_level=1,
            location=campaign['name'],
            active_combat=False,
            recent_events=[]
        )
        
        # Get AI response
        result = dm.get_response(prompt, game_state)
        
        if 'error' in result:
            return jsonify(result), 500
        
        # Parse options from response
        options = parse_options(result['response'])
        
        return jsonify({
            'options': options,
            'raw_response': result['response']
        })
        
    except Exception as e:
        print(f"Error generating options: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def parse_options(response):
    """Parse AI response into individual options"""
    options = []
    lines = response.split('\n')
    current_option = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('## Option'):
            if current_option:
                options.append(current_option)
            # Extract title from "## Option X: Title"
            title = line.split(':', 1)[1].strip() if ':' in line else line
            current_option = {'title': title, 'content': ''}
        elif current_option and line:
            current_option['content'] += line + '\n'
    
    if current_option:
        options.append(current_option)
    
    return options


           
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

def parse_options(response):
    """Parse AI response into individual options"""
    options = []
    lines = response.split('\n')
    current_option = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('## Option'):
            if current_option:
                options.append(current_option)
            # Extract title from "## Option X: Title"
            title = line.split(':', 1)[1].strip() if ':' in line else line
            current_option = {'title': title, 'content': ''}
        elif current_option and line:
            current_option['content'] += line + '\n'
    
    if current_option:
        options.append(current_option)
    
    return options


# ADD THIS COMPLETE FUNCTION HERE:
@app.route('/campaign/<campaign_name>/save-quest-setup', methods=['POST'])
def save_quest_setup(campaign_name):
    """Save quest setup selections to markdown file"""
    data = request.json
    selections = data.get('selections', {})
    
    try:
        # Get campaign folder
        campaign = campaign_mgr.load_campaign(campaign_name)
        folder = campaign_mgr._get_campaign_folder(campaign_name)
        
        # Get character info for the file
        characters = campaign_mgr.get_characters(campaign_name)
        
        # Create quest setup file
        quest_file = folder / "preparations.md"
        
        content = f"""# Quest Preparation - {campaign.name}

**Campaign:** {campaign.name}  
**Date Prepared:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  
**Prepared By:** Campaign Manager  

---

## 👥 Party Composition

"""
        
        for char in characters:
            content += f"### {char.name}\n"
            content += f"- **Race:** {char.race}\n"
            content += f"- **Class:** {char.char_class}\n"
            content += f"- **Level:** {char.level}\n"
            content += f"- **Background:** {char.background}\n"
            content += f"- **HP:** {char.hp}/{char.max_hp} | **AC:** {char.ac}\n"
            content += f"- **Stats:** STR {char.stats.get('strength', 10)}, "
            content += f"DEX {char.stats.get('dexterity', 10)}, "
            content += f"CON {char.stats.get('constitution', 10)}, "
            content += f"INT {char.stats.get('intelligence', 10)}, "
            content += f"WIS {char.stats.get('wisdom', 10)}, "
            content += f"CHA {char.stats.get('charisma', 10)}\n\n"
        
        content += f"""---

## 🎯 Quest Setup

### Quest Hook
{selections.get('quest_hook', '*Not selected*')}

### Main Objective
{selections.get('objective', '*Not selected*')}

### Starting Location
{selections.get('location', '*Not selected*')}

### Key NPCs
{selections.get('npcs', '*Not selected*')}

### Equipment Needed
{selections.get('equipment', '*Not selected*')}

### Party Roles & Strategy
{selections.get('roles', '*Not selected*')}

---

## 📝 Notes for the DM

*This quest setup was completed during the Call to Adventure phase.*  
*The adventure is ready to begin with Session 1.*

**Next Steps:**
- Review the quest hook and prepare opening narration
- Prepare NPC dialogue and motivations
- Set up initial encounter or scene
- Consider potential player choices and consequences

---

*Generated by AI Dungeon Master Campaign System*
"""
        
        with open(quest_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error saving quest setup: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


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
        <button class="new-campaign-btn" onclick="location.href='/settings/prompts'" 
        style="background: linear-gradient(135deg, #4dabf7 0%, #3b9ae1 100%); margin-bottom: 10px;">
    ⚙️ AI Prompt Settings
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
    
    # Adventure Phase Template
    adventure_phase_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quest Builder - {{ context.campaign.name }}</title>
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
            max-width: 1400px;
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
        .phase-badge {
            display: inline-block;
            padding: 8px 15px;
            background: #51cf66;
            border-radius: 6px;
            font-weight: bold;
            margin-top: 10px;
        }
        .content {
            display: grid;
            grid-template-columns: 2fr 1fr;
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
        
        /* Step Display */
        .step-container {
            margin-bottom: 20px;
        }
        .step-title {
            font-size: 1.3em;
            color: #51cf66;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .step-number {
            background: #51cf66;
            color: #1e1e2e;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        /* Options Display */
        .options-container {
            display: grid;
            gap: 15px;
            margin-top: 20px;
        }
        .option-card {
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #4a4a6a;
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .option-card:hover {
            border-color: #51cf66;
            transform: translateX(5px);
            background: rgba(81, 207, 102, 0.1);
        }
        .option-card.selected {
            border-color: #51cf66;
            background: rgba(81, 207, 102, 0.2);
        }
        .option-title {
            font-weight: bold;
            color: #51cf66;
            margin-bottom: 8px;
            font-size: 1.1em;
        }
        .option-content {
            color: #b0b0b0;
            line-height: 1.6;
        }
        
        /* Buttons */
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
        .generate-btn {
            background: linear-gradient(135deg, #4dabf7 0%, #3b9ae1 100%);
        }
        .next-btn {
            background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
        }
        .advance-btn {
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            color: #1e1e2e;
        }
        
        /* Loading */
        .loading {
            text-align: center;
            padding: 40px;
            color: #4dabf7;
        }
        .spinner {
            display: inline-block;
            width: 30px;
            height: 30px;
            border: 4px solid rgba(77, 171, 247, 0.3);
            border-radius: 50%;
            border-top-color: #4dabf7;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Checklist */
        .checklist {
            list-style: none;
            padding: 0;
        }
        .checklist li {
            padding: 12px;
            margin: 8px 0;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 6px;
            border-left: 3px solid #4a4a6a;
            transition: all 0.3s;
        }
        .checklist li.completed {
            border-left-color: #51cf66;
            background: rgba(81, 207, 102, 0.1);
        }
        .checklist li.active {
            border-left-color: #4dabf7;
            background: rgba(77, 171, 247, 0.1);
        }
        .checklist li::before {
            content: "○ ";
            color: #4a4a6a;
            font-size: 1.2em;
            margin-right: 10px;
        }
        .checklist li.completed::before {
            content: "✓ ";
            color: #51cf66;
        }
        .checklist li.active::before {
            content: "→ ";
            color: #4dabf7;
        }
        
        /* Party Summary */
        .party-summary {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .character-mini {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            margin: 5px 0;
            background: rgba(81, 207, 102, 0.1);
            border-radius: 4px;
        }
        
        /* Selections Summary */
        .selections-summary {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .selection-item {
            margin: 10px 0;
            padding: 10px;
            background: rgba(81, 207, 102, 0.1);
            border-left: 3px solid #51cf66;
            border-radius: 4px;
        }
        .selection-label {
            font-weight: bold;
            color: #51cf66;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .selection-value {
            color: #e0e0e0;
            font-size: 0.95em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="phase-header">
            <h1>📜 {{ context.campaign.name }}</h1>
            <p>📍 Phase 2: Guided Quest Builder</p>
            <span class="phase-badge">Step-by-Step Setup</span>
        </div>
        
        <div class="content">
            <!-- Main Quest Builder -->
            <div>
                <div class="panel">
                    <div id="step-display"></div>
                    <div id="options-container"></div>
                    <div id="button-container"></div>
                </div>
            </div>
            
            <!-- Sidebar -->
            <div>
                <div class="panel">
                    <h2>👥 Party</h2>
                    <div class="party-summary">
                        {% for char in context.characters %}
                        <div class="character-mini">
                            <span>{{ char.name }}</span>
                            <span style="color: #888;">{{ char.char_class }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                
                <div class="panel">
                    <h2>✅ Progress</h2>
                    <ul class="checklist" id="progress-checklist">
                        <li data-step="quest_hook">Quest Hook</li>
                        <li data-step="objective">Main Objective</li>
                        <li data-step="location">Starting Location</li>
                        <li data-step="npcs">Key NPCs</li>
                        <li data-step="equipment">Equipment Needed</li>
                        <li data-step="roles">Party Roles</li>
                    </ul>
                </div>
                
                <div class="panel">
                    <h2>📋 Your Selections</h2>
                    <div class="selections-summary" id="selections-display">
                        <p style="text-align: center; color: #888;">No selections yet</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const steps = [
            { key: 'quest_hook', name: 'Quest Hook', description: 'Choose the adventure that will draw your party in' },
            { key: 'objective', name: 'Main Objective', description: 'What does success look like?' },
            { key: 'location', name: 'Starting Location', description: 'Where does the adventure begin?' },
            { key: 'npcs', name: 'Key NPCs', description: 'Who will the party interact with?' },
            { key: 'equipment', name: 'Equipment', description: 'What should the party bring?' },
            { key: 'roles', name: 'Party Roles', description: 'How will the party work together?' }
        ];
        
        let currentStep = 0;
        let selections = {};
        let currentOptions = [];
        let selectedOptionIndex = null;
        
        function init() {
            updateProgress();
            showStep();
        }
        
        function updateProgress() {
            const items = document.querySelectorAll('#progress-checklist li');
            items.forEach((item, index) => {
                item.classList.remove('completed', 'active');
                if (index < currentStep) {
                    item.classList.add('completed');
                } else if (index === currentStep) {
                    item.classList.add('active');
                }
            });
        }
        
        function showStep() {
            const step = steps[currentStep];
            const stepDisplay = document.getElementById('step-display');
            const optionsContainer = document.getElementById('options-container');
            const buttonContainer = document.getElementById('button-container');
            
            stepDisplay.innerHTML = `
                <div class="step-container">
                    <div class="step-title">
                        <div class="step-number">${currentStep + 1}</div>
                        <span>${step.name}</span>
                    </div>
                    <p style="color: #b0b0b0; margin-bottom: 20px;">${step.description}</p>
                </div>
            `;
            
            optionsContainer.innerHTML = '';
            buttonContainer.innerHTML = `
                <button class="generate-btn" onclick="generateOptions()">
                    ✨ Generate ${step.name} Options
                </button>
            `;
            
            updateSelectionsDisplay();
        }
        
        async function generateOptions() {
            const step = steps[currentStep];
            const optionsContainer = document.getElementById('options-container');
            const buttonContainer = document.getElementById('button-container');
            
            optionsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating options...</p></div>';
            buttonContainer.innerHTML = '';
            
            try {
                const response = await fetch('/campaign/{{ context.campaign.name }}/generate-options', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        step: step.key,
                        selections: selections
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    optionsContainer.innerHTML = `<p style="color: #ff6b6b;">Error: ${data.error}</p>`;
                    return;
                }
                
                currentOptions = data.options;
                displayOptions();
                
            } catch (error) {
                optionsContainer.innerHTML = `<p style="color: #ff6b6b;">Error: ${error.message}</p>`;
            }
        }
        
        function displayOptions() {
            const optionsContainer = document.getElementById('options-container');
            const buttonContainer = document.getElementById('button-container');
            
            optionsContainer.innerHTML = `
                <div class="options-container">
                    ${currentOptions.map((option, index) => `
                        <div class="option-card" onclick="selectOption(${index})">
                            <div class="option-title">${option.title}</div>
                            <div class="option-content">${option.content}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            buttonContainer.innerHTML = `
                <button onclick="regenerateOptions()" style="background: #666;">
                    🔄 Regenerate Options
                </button>
                <button class="next-btn" onclick="confirmSelection()" disabled id="next-btn">
                    → Continue to Next Step
                </button>
            `;
        }
        
        function selectOption(index) {
            selectedOptionIndex = index;
            
            // Update visual selection
            document.querySelectorAll('.option-card').forEach((card, i) => {
                card.classList.toggle('selected', i === index);
            });
            
            // Enable next button
            document.getElementById('next-btn').disabled = false;
        }
        
        function regenerateOptions() {
            generateOptions();
        }
        
        function confirmSelection() {
            if (selectedOptionIndex === null) return;
            
            const step = steps[currentStep];
            const selected = currentOptions[selectedOptionIndex];
            
            selections[step.key] = selected.title;
            
            currentStep++;
            selectedOptionIndex = null;
            
            if (currentStep < steps.length) {
                updateProgress();
                showStep();
            } else {
                showCompletion();
            }
        }
        
        function updateSelectionsDisplay() {
            const display = document.getElementById('selections-display');
            
            if (Object.keys(selections).length === 0) {
                display.innerHTML = '<p style="text-align: center; color: #888;">No selections yet</p>';
                return;
            }
            
            display.innerHTML = Object.entries(selections).map(([key, value]) => {
                const step = steps.find(s => s.key === key);
                return `
                    <div class="selection-item">
                        <div class="selection-label">${step ? step.name : key}</div>
                        <div class="selection-value">${value}</div>
                    </div>
                `;
            }).join('');
        }
        
        function showCompletion() {
            const stepDisplay = document.getElementById('step-display');
            const optionsContainer = document.getElementById('options-container');
            const buttonContainer = document.getElementById('button-container');
            
            stepDisplay.innerHTML = `
                <div class="step-container">
                    <div class="step-title">
                        <div class="step-number">✓</div>
                        <span>Quest Setup Complete!</span>
                    </div>
                    <p style="color: #51cf66; margin-bottom: 20px;">
                        All preparation steps are complete. You're ready to begin your adventure!
                    </p>
                </div>
            `;
            
            optionsContainer.innerHTML = `
                <div style="background: rgba(81, 207, 102, 0.1); padding: 20px; border-radius: 8px; border: 2px solid #51cf66;">
                    <h3 style="color: #51cf66; margin-bottom: 15px;">📋 Quest Summary</h3>
                    ${Object.entries(selections).map(([key, value]) => {
                        const step = steps.find(s => s.key === key);
                        return `<p style="margin: 10px 0;"><strong>${step ? step.name : key}:</strong> ${value}</p>`;
                    }).join('')}
                </div>
            `;
            
            buttonContainer.innerHTML = `
                <button class="advance-btn" onclick="beginAdventure()">
                    ⚔️ Begin Adventure (Start Session 1)
                </button>
            `;
            
            updateProgress();
        }
        
        async function beginAdventure() {
    if (!confirm('Ready to begin the adventure? This will start Session 1.')) return;
    
    try {
        // Save quest setup to markdown file
        await fetch('/campaign/{{ context.campaign.name }}/save-quest-setup', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({selections: selections})
        });
        
        // Mark phase complete
        await fetch('/campaign/{{ context.campaign.name }}/complete-phase', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phase: 'call_to_adventure'})
        });
                
                // Advance to next phase
                const response = await fetch('/campaign/{{ context.campaign.name }}/advance', {
                    method: 'POST'
                });
                
                const result = await response.json();
        
        if (result.success) {
            alert('✓ Quest preparation saved to preparations.md!');
            location.href = '/campaign/{{ context.campaign.name }}';
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
        
        // Initialize on page load
        window.onload = init;
    </script>
</body>
</html>"""

    with open(templates_dir / 'adventure_phase.html', 'w', encoding='utf-8') as f:
        f.write(adventure_phase_html)
    
    # Active Campaign Template
    active_campaign_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Session {{ context.campaign.session_number }} - {{ context.campaign.name }}</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
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
            max-width: 1600px;
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
        .session-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }
        .phase-badge {
            display: inline-block;
            padding: 8px 15px;
            background: #4dabf7;
            border-radius: 6px;
            font-weight: bold;
        }
        .content {
            display: grid;
            grid-template-columns: 1fr 2fr 1fr;
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
            font-size: 1.3em;
        }
        h3 {
            color: #51cf66;
            margin: 15px 0 10px;
            font-size: 1.1em;
        }
        
        /* Chat Area */
        .chat-container {
            height: 500px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .message {
            margin-bottom: 15px;    
            padding: 12px;
            border-radius: 8px;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message-dm {
            background: rgba(255, 107, 107, 0.2);
            border-left: 3px solid #ff6b6b;
        }
        .message-player {
            background: rgba(81, 207, 102, 0.2);
            border-left: 3px solid #51cf66;
        }
        .message-system {
            background: rgba(77, 171, 247, 0.2);
            border-left: 3px solid #4dabf7;
            text-align: center;
        }
        .message-label {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        
        /* Character Panels */
        .character-card {
            background: rgba(0, 0, 0, 0.3);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 3px solid #51cf66;
        }
        .char-name {
            font-size: 1.1em;
            font-weight: bold;
            color: #51cf66;
            margin-bottom: 5px;
        }
        .char-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 5px;
            font-size: 0.9em;
            color: #b0b0b0;
        }
        .hp-bar {
            margin-top: 8px;
        }
        .hp-fill {
            height: 8px;
            background: #51cf66;
            border-radius: 4px;
            transition: width 0.3s;
        }
        
        /* Dice Roller */
        .dice-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin: 10px 0;
        }
        .dice-btn {
            padding: 12px;
            background: rgba(74, 74, 106, 0.5);
            border: 2px solid #4a4a6a;
            border-radius: 6px;
            color: #e0e0e0;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .dice-btn:hover {
            border-color: #ff6b6b;
            background: rgba(255, 107, 107, 0.2);
        }
        .dice-result {
            text-align: center;
            padding: 15px;
            background: rgba(81, 207, 102, 0.2);
            border-radius: 8px;
            margin: 10px 0;
            font-size: 1.5em;
            font-weight: bold;
        }
        .natural-20 {
            background: rgba(255, 215, 0, 0.3);
            color: #ffd700;
        }
        .natural-1 {
            background: rgba(255, 0, 0, 0.3);
            color: #ff6b6b;
        }
        
        /* Initiative Tracker */
        .initiative-list {
            list-style: none;
        }
        .initiative-item {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            margin: 5px 0;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 6px;
            border-left: 3px solid #4a4a6a;
        }
        .initiative-item.active {
            border-left-color: #ff6b6b;
            background: rgba(255, 107, 107, 0.2);
        }
        
        /* Inputs */
        input, textarea {
            width: 100%;
            padding: 10px;
            margin: 8px 0;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #4a4a6a;
            border-radius: 6px;
            color: #e0e0e0;
            font-size: 14px;
        }
        textarea {
            min-height: 60px;
            resize: vertical;
        }
        
        /* Buttons */
        button {
            width: 100%;
            padding: 10px;
            margin-top: 8px;
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
        .btn-secondary {
            background: #666;
        }
        
        /* Loading */
        .loading {
            text-align: center;
            padding: 15px;
            color: #ff6b6b;
        }
        .spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 3px solid rgba(255, 107, 107, 0.3);
            border-radius: 50%;
            border-top-color: #ff6b6b;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Quick Actions */
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin: 10px 0;
        }
        .quick-btn {
            padding: 10px;
            background: rgba(74, 74, 106, 0.5);
            border: 2px solid #4a4a6a;
            border-radius: 6px;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.3s;
        }
        .quick-btn:hover {
            border-color: #51cf66;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="phase-header">
            <h1>⚔️ {{ context.campaign.name }}</h1>
            <div class="session-info">
                <div>
                    <span class="phase-badge">Session {{ context.campaign.session_number }}</span>
                </div>
                <button onclick="endSession()" style="width: auto; padding: 8px 20px; background: #666;">
                    End Session
                </button>
            </div>
        </div>
        
        <div class="content">
            <!-- Left Sidebar: Party -->
            <div>
                <div class="panel">
                    <h2>👥 Party</h2>
                    {% for char in context.characters %}
                    <div class="character-card">
                        <div class="char-name">{{ char.name }}</div>
                        <div class="char-stats">
                            <div>{{ char.race }} {{ char.char_class }}</div>
                            <div>Level {{ char.level }}</div>
                            <div>HP: {{ char.hp }}/{{ char.max_hp }}</div>
                            <div>AC: {{ char.ac }}</div>
                        </div>
                        <div class="hp-bar">
                            <div class="hp-fill" style="width: {{ (char.hp / char.max_hp * 100)|int }}%"></div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <div class="panel">
                    <h2>🎲 Dice Roller</h2>
                    <div class="dice-grid">
                        <button class="dice-btn" onclick="roll('d4')">d4</button>
                        <button class="dice-btn" onclick="roll('d6')">d6</button>
                        <button class="dice-btn" onclick="roll('d8')">d8</button>
                        <button class="dice-btn" onclick="roll('d10')">d10</button>
                        <button class="dice-btn" onclick="roll('d12')">d12</button>
                        <button class="dice-btn" onclick="roll('d20')">d20</button>
                    </div>
                    <input type="text" id="custom-dice" placeholder="2d6+3">
                    <button onclick="rollCustom()">Roll Custom</button>
                    <div id="dice-result"></div>
                </div>
                
                <div class="panel">
                    <h2>⚡ Quick Actions</h2>
                    <div class="quick-actions">
                        <button class="quick-btn" onclick="quickAction('I attack')">⚔️ Attack</button>
                        <button class="quick-btn" onclick="quickAction('I cast a spell')">✨ Cast Spell</button>
                        <button class="quick-btn" onclick="quickAction('I search the room')">🔍 Search</button>
                        <button class="quick-btn" onclick="quickAction('I investigate')">📖 Investigate</button>
                        <button class="quick-btn" onclick="quickAction('I try to persuade')">💬 Persuade</button>
                        <button class="quick-btn" onclick="quickAction('I take a rest')">🛌 Rest</button>
                    </div>
                </div>
            </div>
            
            <!-- Center: Main Chat -->
            <div>
                <div class="panel">
                    <h2>🎭 Adventure Log</h2>
                    <div class="chat-container" id="chat-container"></div>
                    <textarea id="action-input" placeholder="What do you do?"></textarea>
                    <button onclick="takeAction()">Take Action</button>
                </div>
            </div>
            
            <!-- Right Sidebar: Combat & Tools -->
            <div>
                <div class="panel">
                    <h2>⚔️ Initiative Tracker</h2>
                    <ul class="initiative-list" id="initiative-list">
                        <li style="text-align: center; color: #888; padding: 20px;">
                            No combat active
                        </li>
                    </ul>
                    <input type="text" id="init-name" placeholder="Name">
                    <input type="number" id="init-value" placeholder="Initiative" min="1">
                    <button onclick="addInitiative()">Add to Initiative</button>
                    <button class="btn-secondary" onclick="clearInitiative()">Clear All</button>
                </div>
                
                <div class="panel">
                    <h2>📝 Session Notes</h2>
                    <textarea id="session-notes" placeholder="Take notes about this session..." style="min-height: 150px;"></textarea>
                    <button onclick="saveNotes()">Save Notes</button>
                </div>
                
                <div class="panel">
                    <h2>📍 Current Context</h2>
                    <div style="font-size: 0.9em; color: #b0b0b0;">
                        <p><strong>Phase:</strong> {{ context.phase_info.name }}</p>
                        <p><strong>Location:</strong> <span id="current-location">Unknown</span></p>
                        <p><strong>Combat:</strong> <span id="combat-status">No</span></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        let isLoading = false;
        let currentTurn = 0;
        
        // Add welcome message
        window.onload = () => {
            addMessage('Session {{ context.campaign.session_number }} begins! What do you do?', 'system');
        };
        
        async function takeAction() {
            if (isLoading) return;
            
            const input = document.getElementById('action-input');
            const action = input.value.trim();
            if (!action) return;
            
            addMessage(action, 'player');
            input.value = '';
            isLoading = true;
            
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.innerHTML = '<div class="spinner"></div> DM is responding...';
            document.getElementById('chat-container').appendChild(loadingDiv);
            
            try {
                const response = await fetch('/campaign/{{ context.campaign.name }}/ai-assist', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: action})
                });
                
                const data = await response.json();
                loadingDiv.remove();
                
                if (data.error) {
                    addMessage(`Error: ${data.error}`, 'dm');
                } else {
                    addMessage(data.response, 'dm');
                }
            } catch (error) {
                loadingDiv.remove();
                addMessage(`Error: ${error.message}`, 'dm');
            }
            
            isLoading = false;
        }
        
        function addMessage(text, type) {
            const container = document.getElementById('chat-container');
            const div = document.createElement('div');
            div.className = `message message-${type}`;
            
            let label = '';
            if (type === 'player') label = '🎲 Player';
            else if (type === 'dm') label = '🎭 DM';
            else if (type === 'system') label = '📢 System';
            
            div.innerHTML = `
                ${label ? `<div class="message-label">${label}</div>` : ''}
                <div>${text}</div>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
        
        async function roll(dice) {
            const response = await fetch('/api/dice/roll', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dice})
            });
            const data = await response.json();
            displayDiceResult(data);
            addMessage(`Rolled ${data.dice}: ${data.total}`, 'system');
        }
        
        async function rollCustom() {
            const dice = document.getElementById('custom-dice').value;
            const response = await fetch('/api/dice/roll', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dice})
            });
            const data = await response.json();
            displayDiceResult(data);
            addMessage(`Rolled ${data.dice}: ${data.total}`, 'system');
        }
        
        function displayDiceResult(data) {
            const resultDiv = document.getElementById('dice-result');
            let className = 'dice-result';
            if (data.natural_20) className += ' natural-20';
            if (data.natural_1) className += ' natural-1';
            
            resultDiv.className = className;
            resultDiv.innerHTML = `
                ${data.dice}: ${data.total}
                ${data.natural_20 ? '<br>🌟 CRITICAL!' : ''}
                ${data.natural_1 ? '<br>💀 FUMBLE!' : ''}
            `;
        }
        
        function quickAction(action) {
            document.getElementById('action-input').value = action;
            takeAction();
        }
        
        async function addInitiative() {
            const name = document.getElementById('init-name').value;
            const value = document.getElementById('init-value').value;
            
            if (!name || !value) return;
            
            await fetch('/api/initiative', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name,
                    initiative: parseInt(value)
                })
            });
            
            document.getElementById('init-name').value = '';
            document.getElementById('init-value').value = '';
            
            loadInitiative();
            document.getElementById('combat-status').textContent = 'Yes';
        }
        
        async function loadInitiative() {
            const response = await fetch('/api/initiative');
            const data = await response.json();
            
            const list = document.getElementById('initiative-list');
            if (data.initiative.length === 0) {
                list.innerHTML = '<li style="text-align: center; color: #888; padding: 20px;">No combat active</li>';
            } else {
                list.innerHTML = data.initiative.map((item, index) => `
                    <li class="initiative-item ${index === currentTurn ? 'active' : ''}">
                        <span>${item.name}</span>
                        <span>${item.initiative}</span>
                    </li>
                `).join('');
            }
        }
        
        async function clearInitiative() {
            if (!confirm('Clear initiative tracker?')) return;
            
            await fetch('/api/initiative', {method: 'DELETE'});
            loadInitiative();
            document.getElementById('combat-status').textContent = 'No';
            addMessage('Combat ended', 'system');
        }
        
        function saveNotes() {
            const notes = document.getElementById('session-notes').value;
            localStorage.setItem('session_{{ context.campaign.session_number }}_notes', notes);
            alert('Notes saved!');
        }
        
        async function endSession() {
            if (!confirm('End this session?')) return;
            
            const notes = document.getElementById('session-notes').value;
            // Save notes logic here
            
            alert('Session ended! Notes saved.');
            location.href = '/campaign/{{ context.campaign.name }}';
        }
        
        // Keyboard shortcuts
        document.getElementById('action-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                takeAction();
            }
        });
        
        // Load saved notes
        const savedNotes = localStorage.getItem('session_{{ context.campaign.session_number }}_notes');
        if (savedNotes) {
            document.getElementById('session-notes').value = savedNotes;
        }
    </script>
</body>
</html>"""
    
    with open(templates_dir / 'active_campaign.html', 'w', encoding='utf-8') as f:
        f.write(active_campaign_html)
    
    print("✓ Campaign templates created")


@app.route('/settings/prompts')
def prompt_settings():
    """Prompt template editor"""
    prep_prompt = prompt_templates.get_prompt('prep')
    active_prompt = prompt_templates.get_prompt('active')
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Prompt Settings</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d1b3d 100%);
            color: #e0e0e0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #ff6b6b;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            text-align: center;
            color: #b0b0b0;
            margin-bottom: 30px;
        }
        .info-box {
            background: rgba(33, 150, 243, 0.15);
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .prompt-section {
            background: rgba(30, 30, 46, 0.8);
            border: 2px solid #4a4a6a;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }
        h2 {
            color: #ff6b6b;
            margin-bottom: 10px;
        }
        .phase-desc {
            color: #b0b0b0;
            margin-bottom: 15px;
            font-size: 0.95em;
        }
        textarea {
            width: 100%;
            min-height: 400px;
            background: rgba(0, 0, 0, 0.3);
            border: 2px solid #4a4a6a;
            border-radius: 6px;
            color: #e0e0e0;
            padding: 15px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 14px;
            resize: vertical;
            line-height: 1.5;
        }
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }
        .save-btn {
            background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
            color: white;
            flex: 1;
        }
        .save-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(81, 207, 102, 0.4);
        }
        .reset-btn {
            background: #f44336;
            color: white;
            flex: 1;
        }
        .reset-btn:hover {
            background: #da190b;
            transform: translateY(-2px);
        }
        .back-btn {
            background: #666;
            color: white;
            padding: 12px 24px;
            display: inline-block;
            text-decoration: none;
            border-radius: 6px;
            transition: all 0.3s;
        }
        .back-btn:hover {
            background: #555;
            transform: translateY(-2px);
        }
        .footer {
            text-align: center;
            margin-top: 30px;
        }
        .success-msg {
            background: rgba(81, 207, 102, 0.2);
            border: 2px solid #51cf66;
            color: #51cf66;
            padding: 12px;
            border-radius: 6px;
            margin-top: 10px;
            display: none;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎲 AI Prompt Templates</h1>
        <p class="subtitle">Customize how your AI Dungeon Master behaves</p>
        
        <div class="info-box">
            <strong>💡 What are prompt templates?</strong><br>
            These prompts tell the AI how to act as your Dungeon Master. Edit them to change the AI's 
            personality, style, and behavior. Changes take effect immediately!
        </div>
        
        <div class="prompt-section">
            <h2>📜 Preparation Phase Prompt</h2>
            <p class="phase-desc">
                Used during quest planning and adventure setup (Phase 2: Call to Adventure)
            </p>
            <textarea id="prep-prompt">""" + prep_prompt.replace('</textarea>', '&lt;/textarea&gt;') + """</textarea>
            <div id="prep-success" class="success-msg">✓ Prep prompt saved!</div>
            <div class="button-group">
                <button class="save-btn" onclick="savePrompt('prep')">💾 Save Prep Prompt</button>
                <button class="reset-btn" onclick="resetPrompt('prep')">🔄 Reset to Default</button>
            </div>
        </div>
        
        <div class="prompt-section">
            <h2>⚔️ Active Campaign Prompt</h2>
            <p class="phase-desc">
                Used during actual gameplay sessions (Phase 3: Active Campaign)
            </p>
            <textarea id="active-prompt">""" + active_prompt.replace('</textarea>', '&lt;/textarea&gt;') + """</textarea>
            <div id="active-success" class="success-msg">✓ Active prompt saved!</div>
            <div class="button-group">
                <button class="save-btn" onclick="savePrompt('active')">💾 Save Active Prompt</button>
                <button class="reset-btn" onclick="resetPrompt('active')">🔄 Reset to Default</button>
            </div>
        </div>
        
        <div class="footer">
            <a href="/" class="back-btn">← Back to Campaigns</a>
        </div>
    </div>
    
    <script>
        function showSuccess(phase) {
            const msg = document.getElementById(phase + '-success');
            msg.style.display = 'block';
            setTimeout(() => {
                msg.style.display = 'none';
            }, 3000);
        }
        
        async function savePrompt(phase) {
            const content = document.getElementById(phase + '-prompt').value;
            
            try {
                const response = await fetch('/settings/prompts/save', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phase: phase, content: content })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showSuccess(phase);
                } else {
                    alert('✗ Error: ' + data.error);
                }
            } catch (error) {
                alert('✗ Error saving prompt: ' + error);
            }
        }
        
        async function resetPrompt(phase) {
            if (!confirm('Reset this prompt to default? This cannot be undone.')) {
                return;
            }
            
            try {
                const response = await fetch('/settings/prompts/reset', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ phase: phase })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    location.reload();
                } else {
                    alert('✗ Error: ' + data.error);
                }
            } catch (error) {
                alert('✗ Error resetting prompt: ' + error);
            }
        }
    </script>
</body>
</html>"""
    return html


@app.route('/settings/prompts/save', methods=['POST'])
def save_prompt():
    """Save edited prompt template"""
    try:
        data = request.json
        phase = data.get('phase')
        content = data.get('content')
        
        if not phase or not content:
            return jsonify({'success': False, 'error': 'Missing phase or content'})
        
        prompt_templates.update_prompt(phase, content)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/settings/prompts/reset', methods=['POST'])
def reset_prompt():
    """Reset prompt to default"""
    try:
        data = request.json
        phase = data.get('phase')
        
        if not phase:
            return jsonify({'success': False, 'error': 'Missing phase'})
        
        # Delete the file to force recreation of default
        import os
        if phase == 'prep':
            filepath = 'prompts/prep_phase_prompt.txt'
        elif phase == 'active':
            filepath = 'prompts/active_phase_prompt.txt'
        else:
            return jsonify({'success': False, 'error': 'Invalid phase'})
        
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Recreate defaults
        prompt_templates._create_default_templates()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

    


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