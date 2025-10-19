#!/usr/bin/env python3
"""
AI Dungeon Master - Complete Application
Integrates all phases into a single working app
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
import secrets
import os
from pathlib import Path
from datetime import datetime

# Import campaign manager
from campaign_manager import get_campaign_manager, Character
from prompt_templates import PromptTemplates, create_full_prompt

# Import AI DM components with better error handling
OllamaDM = None
GameState = None
QueryRouter = None
SRDContentLoader = None

try:
    from ai_dm_free import OllamaDM, GameState
    print("✓ AI DM core modules loaded")
except ImportError as e:
    print(f"⚠ AI DM modules not found: {e}")

try:
    from ai_dm_query_router import QueryRouter
    print("✓ Query router loaded")
except ImportError:
    print("⚠ Query router not found - AI will work without SRD content")

try:
    from ai_dm_free import SRDContentLoader
    print("✓ SRD content loader available")
except (ImportError, AttributeError):
    print("⚠ SRD content loader not available")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize systems
prompt_templates = PromptTemplates()
campaign_mgr = get_campaign_manager()
SRD_PATH = "./srd_story_cycle"
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


# ============================================================================
# MAIN ROUTES
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
# SETTINGS ROUTES
# ============================================================================

@app.route('/settings/prompts')
def prompt_settings():
    """Prompt template editor"""
    prep_prompt = prompt_templates.get_prompt('prep')
    active_prompt = prompt_templates.get_prompt('active')
    
    return render_template('prompt_settings.html', 
                         prep_prompt=prep_prompt,
                         active_prompt=active_prompt)


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


# ============================================================================
# PHASE 1: SETUP & CHARACTER CREATION
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
# PHASE 2: CALL TO ADVENTURE & PREPARATION
# ============================================================================

@app.route('/campaign/<campaign_name>/adventure')
def adventure_phase(campaign_name):
    """Call to adventure and preparation phase"""
    try:
        context = campaign_mgr.get_campaign_context(campaign_name)
        return render_template('adventure_phase.html', context=context)
    except Exception as e:
        return f"Error: {e}", 404


@app.route('/campaign/<campaign_name>/generate-options', methods=['POST'])
def generate_options(campaign_name):
    """Generate AI options for a specific quest setup step"""
    data = request.json
    step = data.get('step', '')
    
    # Check if AI is available
    if not dm:
        return jsonify({'error': 'AI not available - Ollama not running or ai_dm_free.py not found'}), 503
    
    if not hasattr(dm, 'ollama_available') or not dm.ollama_available:
        return jsonify({'error': 'Ollama service not running. Start it with: ollama serve'}), 503
    
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
            context_str = "Previous selections:\n"
            for key, value in selections.items():
                context_str += f"{key}: {value}\n"
            prompt = context_str + "\n" + prompts[step]
        
        # Create game state if GameState is available
        game_state = None
        if GameState:
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


@app.route('/campaign/<campaign_name>/save-quest-setup', methods=['POST'])
def save_quest_setup(campaign_name):
    """Save quest setup selections to markdown file"""
    data = request.json
    selections = data.get('selections', {})
    
    try:
        campaign = campaign_mgr.load_campaign(campaign_name)
        folder = campaign_mgr._get_campaign_folder(campaign_name)
        characters = campaign_mgr.get_characters(campaign_name)
        
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
# PHASE 3: ACTIVE CAMPAIGN
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


@app.route('/campaign/<campaign_name>/ai-assist', methods=['POST'])
def ai_assist(campaign_name):
    """Get AI assistance in current phase"""
    data = request.json
    query = data.get('query', '').strip()
    
    # Check if AI is available
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    if not dm:
        return jsonify({'error': 'AI not available - Ollama not running or ai_dm_free.py not found'}), 503
    
    if not hasattr(dm, 'ollama_available') or not dm.ollama_available:
        return jsonify({'error': 'Ollama service not running. Start it with: ollama serve'}), 503
    
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
        
        # Load relevant SRD content (if available)
        srd_content = ""
        if QueryRouter and SRDContentLoader:
            try:
                router = QueryRouter(SRD_PATH)
                # Use first available story phase as current phase
                story_phase = ''
                if hasattr(campaign_mgr, 'get_available_story_phases'):
                    phases = campaign_mgr.get_available_story_phases(campaign.current_phase)
                    if phases:
                        story_phase = phases[0]
                
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


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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


def create_templates():
    """Create HTML templates if they don't exist"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    if (templates_dir / 'campaign_list.html').exists():
        return
    
    print("Creating HTML templates...")
    try:
        from extract_templates import create_all_templates
        create_all_templates()
    except ImportError:
        print("⚠ extract_templates.py not found - run it manually to create templates")
    print("✓ Templates check complete")


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

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
        print("  To enable AI: Install Ollama and run 'ollama serve'")
    
    if not QueryRouter:
        print("⚠ Query router not available - AI will work without SRD context")
    
    print(f"\n📡 Server starting...")
    print(f"   Campaign Manager: http://localhost:5000")
    print("="*60 + "\n")
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)