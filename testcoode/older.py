#!/usr/bin/env python3
"""
AI Dungeon Master - Complete Application
Integrates all phases into a single working app with enhanced Phase 3
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO
from dataclasses import asdict  
import secrets
import os
from pathlib import Path
from datetime import datetime

# Import Files
from campaign_manager import get_campaign_manager, Character
from prompt_templates import PromptTemplates, create_full_prompt
from search_engine import SRDSearchEngine, create_search_api, FAISS_AVAILABLE, EMBEDDINGS_AVAILABLE


# Import AI DM components with better error handling
OllamaDM = None
GameState = None
QueryRouter = None
SRDContentLoader = None
Phase3QueryRouter = None
create_phase3_prompt = None
Phase3SRDLoader = None

try:
    from ai_dm_free import OllamaDM, GameState
    print("✓ AI DM core modules loaded")
except ImportError as e:
    print(f"⚠ AI DM modules not found: {e}")

try:
    from ai_dm_query_router import QueryRouter
    print("✓ Query router loaded (Phase 2)")
except ImportError:
    print("⚠ Query router not found - Phase 2 will work without SRD content")

try:
    from ai_dm_free import SRDContentLoader
    print("✓ SRD content loader available")
except (ImportError, AttributeError):
    print("⚠ SRD content loader not available")

# Import Phase 3 enhanced router
try:
    from BackEnd.Classes.phase3_DM import (
        Phase3QueryRouter, 
        create_phase3_prompt,
        SRDContentLoader as Phase3SRDLoader
    )
    print("✓ Phase 3 enhanced router loaded")
except ImportError as e:
    print(f"⚠ Phase 3 router not found: {e}")

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
# PHASE 1: SETUP & CHARACTER CREATION
# ============================================================================

@app.route('/campaign/<campaign_name>/setup')
def setup_phase(campaign_name):
    """Setup and character creation phase"""
    try:
        campaign = campaign_mgr.load_campaign(campaign_name)
        characters = campaign_mgr.get_characters(campaign_name)
        
        return render_template('HTML/setup_phase.html', 
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
# CHARACTER MANAGEMENT ENDPOINTS 
# ============================================================================

@app.route('/campaign/<campaign_name>/character/<character_name>/update', methods=['POST'])
def update_character(campaign_name, character_name):
    """Update an existing character"""
    data = request.json
    
    try:
        # Load existing character
        char = campaign_mgr.get_character(campaign_name, character_name)
        if not char:
            return jsonify({'error': 'Character not found'}), 404
        
        # Update fields 
        char.hp = int(data.get('hp', char.hp))
        char.max_hp = int(data.get('max_hp', char.max_hp))
        char.ac = int(data.get('ac', char.ac))
        char.level = int(data.get('level', char.level))
        
        if 'alignment' in data:
            char.alignment = data['alignment']
        if 'notes' in data:
            char.notes = data['notes']
        if 'has_inspiration' in data:
            char.has_inspiration = data['has_inspiration']
        
        # Update character in campaign
        campaign_mgr.update_character(campaign_name, char)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/campaign/<campaign_name>/character/<character_name>/currency/add', methods=['POST'])
def add_character_currency(campaign_name, character_name):
    """Add currency to a character"""
    data = request.json
    coin_type = data.get('coin_type')  # 'cp', 'sp', 'ep', 'gp', 'pp'
    amount = int(data.get('amount', 0))
    
    if not coin_type or amount <= 0:
        return jsonify({'error': 'Invalid coin_type or amount'}), 400
    
    try:
        char = campaign_mgr.get_character(campaign_name, character_name)
        if not char:
            return jsonify({'error': 'Character not found'}), 404
        
        char.add_currency(coin_type, amount)
        campaign_mgr.update_character(campaign_name, char)
        
        return jsonify({
            'success': True,
            'currency': char.currency,
            'total_gp': char.get_total_gold_value()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/campaign/<campaign_name>/character/<character_name>/currency/remove', methods=['POST'])
def remove_character_currency(campaign_name, character_name):
    """Remove currency from a character"""
    data = request.json
    coin_type = data.get('coin_type')
    amount = int(data.get('amount', 0))
    
    if not coin_type or amount <= 0:
        return jsonify({'error': 'Invalid coin_type or amount'}), 400
    
    try:
        char = campaign_mgr.get_character(campaign_name, character_name)
        if not char:
            return jsonify({'error': 'Character not found'}), 404
        
        success = char.remove_currency(coin_type, amount)
        
        if not success:
            return jsonify({'error': 'Insufficient funds'}), 400
        
        campaign_mgr.update_character(campaign_name, char)
        
        return jsonify({
            'success': True,
            'currency': char.currency,
            'total_gp': char.get_total_gold_value()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/campaign/<campaign_name>/character/<character_name>/currency/pay', methods=['POST'])
def pay_cost(campaign_name, character_name):
    """Pay a cost in gold (auto-converts currency)"""
    data = request.json
    cost_gp = float(data.get('cost', 0))
    
    if cost_gp <= 0:
        return jsonify({'error': 'Invalid cost'}), 400
    
    try:
        char = campaign_mgr.get_character(campaign_name, character_name)
        if not char:
            return jsonify({'error': 'Character not found'}), 404
        
        success = char.pay_cost(cost_gp)
        
        if not success:
            return jsonify({
                'error': 'Insufficient funds',
                'required': cost_gp,
                'available': char.get_total_gold_value()
            }), 400
        
        campaign_mgr.update_character(campaign_name, char)
        
        return jsonify({
            'success': True,
            'paid': cost_gp,
            'remaining_currency': char.currency,
            'remaining_gp': char.get_total_gold_value()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/campaign/<campaign_name>/character/<character_name>/currency/convert', methods=['POST'])
def convert_currency(campaign_name, character_name):
    """Convert currency between denominations"""
    data = request.json
    from_type = data.get('from_type')
    to_type = data.get('to_type')
    amount = int(data.get('amount', 0))
    
    if not from_type or not to_type or amount <= 0:
        return jsonify({'error': 'Invalid parameters'}), 400
    
    try:
        char = campaign_mgr.get_character(campaign_name, character_name)
        if not char:
            return jsonify({'error': 'Character not found'}), 404
        
        success = char.convert_currency(from_type, to_type, amount)
        
        if not success:
            return jsonify({'error': 'Conversion failed (insufficient funds or invalid amount)'}), 400
        
        campaign_mgr.update_character(campaign_name, char)
        
        return jsonify({
            'success': True,
            'currency': char.currency,
            'total_gp': char.get_total_gold_value()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/campaign/<campaign_name>/character/<character_name>/inventory/add', methods=['POST'])
def add_inventory_item(campaign_name, character_name):
    """Add item to character inventory"""
    data = request.json
    item = data.get('item', '').strip()
    
    if not item:
        return jsonify({'error': 'No item provided'}), 400
    
    try:
        char = campaign_mgr.get_character(campaign_name, character_name)
        if not char:
            return jsonify({'error': 'Character not found'}), 404
        
        char.inventory.append(item)
        campaign_mgr.update_character(campaign_name, char)
        
        return jsonify({
            'success': True,
            'inventory': char.inventory
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/campaign/<campaign_name>/character/<character_name>/inventory/remove', methods=['POST'])
def remove_inventory_item(campaign_name, character_name):
    """Remove item from character inventory"""
    data = request.json
    item = data.get('item', '').strip()
    
    if not item:
        return jsonify({'error': 'No item provided'}), 400
    
    try:
        char = campaign_mgr.get_character(campaign_name, character_name)
        if not char:
            return jsonify({'error': 'Character not found'}), 404
        
        if item in char.inventory:
            char.inventory.remove(item)
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'inventory': char.inventory
            })
        else:
            return jsonify({'error': 'Item not found in inventory'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/campaign/<campaign_name>/character/<character_name>/inspiration/toggle', methods=['POST'])
def toggle_inspiration(campaign_name, character_name):
    """Toggle inspiration for a character"""
    try:
        char = campaign_mgr.get_character(campaign_name, character_name)
        if not char:
            return jsonify({'error': 'Character not found'}), 404
        
        char.has_inspiration = not char.has_inspiration
        campaign_mgr.update_character(campaign_name, char)
        
        return jsonify({
            'success': True,
            'has_inspiration': char.has_inspiration
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/campaign/<campaign_name>/character/<character_name>', methods=['GET'])
def get_character_sheet(campaign_name, character_name):
    """Get full character sheet data"""
    try:
        char = campaign_mgr.get_character(campaign_name, character_name)
        if not char:
            return jsonify({'error': 'Character not found'}), 404
        
        return jsonify({
            'success': True,
            'character': asdict(char)
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
        return render_template('HTML/adventure_phase.html', context=context)
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
# PHASE 3: ACTIVE CAMPAIGN (ENHANCED)
# ============================================================================

@app.route('/campaign/<campaign_name>/play')
def active_campaign(campaign_name):
    """Active campaign gameplay"""
    try:
        context = campaign_mgr.get_campaign_context(campaign_name)
        return render_template('HTML/active_campaign.html', context=context)
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
    """Get AI assistance in current phase - ENHANCED for Phase 3"""
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
        
        # ENHANCED: Use Phase 3 router for active campaign
        srd_content = ""
        routing_info = None
        
        if phase == 'active' and Phase3QueryRouter and Phase3SRDLoader:
            try:
                # Use enhanced Phase 3 router
                router = Phase3QueryRouter(SRD_PATH)
                
                # Route the query with context
                routing_info = router.route_query(
                    query, 
                    context={
                        'active_combat': campaign_context['active_combat'],
                        'session_number': campaign_context['session_number']
                    }
                )
                
                # Load SRD content
                loader = Phase3SRDLoader(SRD_PATH)
                srd_content = loader.load_files(
                    routing_info['files_to_load'],
                    max_chars=15000
                )
                
                # Log what we're using
                print(f"[Phase 3 Router] Categories: {routing_info['matched_categories']}")
                print(f"[Phase 3 Router] Files: {len(routing_info['files_to_load'])}")
                
            except Exception as e:
                print(f"Phase 3 routing warning: {e}")
                # Fall back to basic routing if needed
                
        elif phase == 'prep' and QueryRouter and SRDContentLoader:
            # Use Phase 2 router for prep
            try:
                router = QueryRouter(SRD_PATH)
                story_phase = '03_call_to_adventure'
                routing = router.route_query(query, current_phase=story_phase)
                
                if routing['files_to_load']:
                    loader = SRDContentLoader(SRD_PATH)
                    srd_content = loader.load_files(
                        routing['files_to_load'][:3], 
                        max_chars=10000
                    )
            except Exception as e:
                print(f"Phase 2 routing warning: {e}")
        
        # Create full prompt using appropriate system
        if phase == 'active' and create_phase3_prompt:
            # Use enhanced Phase 3 prompt
            base_prompt = prompt_templates.get_prompt('active')
            full_prompt = create_phase3_prompt(
                campaign_context=campaign_context,
                query=query,
                srd_content=srd_content,
                base_prompt=base_prompt
            )
        else:
            # Use standard prompt template
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
            campaign_mgr._save_campaign(campaign)
        
        # Include routing info in response for debugging
        response_data = {
            'response': ai_response,
            'query': query,
            'phase': phase
        }
        
        if routing_info:
            response_data['routing_info'] = {
                'categories': routing_info['matched_categories'],
                'files_loaded': len(routing_info['files_to_load'])
            }
        
        return jsonify(response_data)
        
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
    
    if (templates_dir / 'HTML/campaign_list.html').exists():
        return
    
    print("Creating HTML templates...")
    try:
        from extract_templates import create_all_templates
        create_all_templates()
    except ImportError:
        print("⚠ extract_templates.py not found - run it manually to create templates")
    print("✓ Templates check complete")

# Add search API endpoints
if search_engine:
    create_search_api(app, search_engine)

@app.route('/campaign/<campaign_name>/search-panel')
def search_panel(campaign_name):
    """Render search panel for active campaign"""
    try:
        campaign = campaign_mgr.load_campaign(campaign_name)
        stats = search_engine.get_stats() if search_engine else {'status': 'not_available'}
        return render_template('HTML/search_panel.html', campaign=campaign, stats=stats)
    except Exception as e:
        return f"Error: {e}", 404
    
@app.route('/srd-search')
def srd_search_page():
    return render_template('HTML/srd_search.html')

@app.route('/api/srd/file', methods=['POST'])
def get_srd_file():
    """Serve SRD markdown file content"""
    data = request.json
    file_path = data.get('file_path', '')
    
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
    
    # Security: ensure path doesn't escape SRD directory
    if '..' in file_path or file_path.startswith('/'):
        return jsonify({'error': 'Invalid file path'}), 400
    
    try:
        full_path = Path(SRD_PATH) / file_path
        
        if not full_path.exists():
            return jsonify({'error': 'File not found'}), 404
        
        if not full_path.is_file():
            return jsonify({'error': 'Not a file'}), 400
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'content': content,
            'file_path': file_path
        })
        
    except Exception as e:
        print(f"Error serving SRD file: {e}")
        return jsonify({'error': str(e)}), 500



# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Create templates if needed
    create_templates()
    
    print("\n" + "="*60)
    print(" AI Dungeon Master - Campaign System")
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