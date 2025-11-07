from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import secrets
import os
from pathlib import Path
from datetime import datetime
from prompt_templates import PromptTemplates, create_full_prompt




# Import campaign manager
from BackEnd.Classes.campaign_manager import CampaignManager, Character, get_campaign_manager

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

