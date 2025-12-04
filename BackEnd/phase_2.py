#!/usr/bin/env python3
"""
Phase 2: Call to Adventure & Preparation Routes
Handles quest setup, AI option generation, and preparation completion
"""

from flask import render_template, request, jsonify
from datetime import datetime
from pathlib import Path

# These will be imported from main.py when we integrate
# from main import app, campaign_mgr, dm, GameState


# ============================================================================
# PHASE 2: CALL TO ADVENTURE & PREPARATION
# ============================================================================

def register_phase2_routes(app, campaign_mgr, dm, GameState):
    """Register all Phase 2 routes with the Flask app"""
    
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
        selections = data.get('selections', {})
        # Check if AI is available
        if not dm:
            return jsonify({'error': 'AI not available - Ollama not running or ai_dm_free.py not found'}), 503
        
        if not hasattr(dm, 'ollama_available') or not dm.ollama_available:
            return jsonify({'error': 'Ollama service not running. Start it with: ollama serve'}), 503
        
        try:
            # Get campaign context
            context = campaign_mgr.get_campaign_context(campaign_name)
            campaign = context['campaign']
            
            # Create prompts for each step - each builds on previous selections
            prompt = ""

            if step == 'quest_hook':
                prompt = f"""Generate 5 unique quest hooks for this D&D party.

            Campaign: {campaign['name']}
            Party: {', '.join([c['name'] + ' (' + c['char_class'] + ')' for c in context['characters']])}

            For each QUEST HOOK, provide:
            - A catchy title
            - A 2-sentence description
            - Why this party would care

            Format each option as:
            ## Option X: [Title]
            [Description]
            *Why your party cares:* [Reason]

            Generate 5 diverse options."""

            elif step == 'objective':
                prompt = f"""Based on the chosen quest hook, generate 4 possible main objectives.

            QUEST HOOK SELECTED:
            {selections.get('quest_hook', 'Not yet selected')}

            Each objective should be:
            - Clear and achievable
            - Appropriate for the party level
            - Directly connected to the quest hook above

            Format as:
            ## Option X: [Objective Title]
            [What success looks like and how it connects to the quest hook]"""

            elif step == 'location':
                prompt = f"""Generate 1-4 starting locations for this adventure.

            QUEST HOOK:
            {selections.get('quest_hook', 'Not yet selected')}

            OBJECTIVE:
            {selections.get('objective', 'Not yet selected')}

            Each location should:
            - Match both the quest theme and objective
            - Provide opportunities for exploration
            - Include sensory details that set the mood

            Format as:
            ## Option X: [Location Name]
            [Description with sights, sounds, atmosphere that fits the quest]"""

            elif step == 'npc1':
                prompt = f"""Generate 4 options for the FIRST key NPC for this quest.

            QUEST HOOK:
            {selections.get('quest_hook', 'Not yet selected')}

            OBJECTIVE:
            {selections.get('objective', 'Not yet selected')}

            LOCATION:
            {selections.get('location', 'Not yet selected')}

            For each NPC option include:
            - Name and role
            - Personality trait
            - How they connect to the quest hook and why they'd be at this location

            Format as:
            ## Option X: [NPC Name - Role]
            [Description and quest connection]"""

            elif step == 'npc2':
                prompt = f"""Generate 4 options for the SECOND key NPC for this quest.

            QUEST HOOK:
            {selections.get('quest_hook', 'Not yet selected')}

            OBJECTIVE:
            {selections.get('objective', 'Not yet selected')}

            LOCATION:
            {selections.get('location', 'Not yet selected')}

            FIRST NPC:
            {selections.get('npc1', 'Not yet selected')}

            This NPC should complement or contrast with the first NPC and fit the quest context.

            For each NPC option include:
            - Name and role
            - Personality trait
            - How they relate to the first NPC and the quest

            Format as:
            ## Option X: [NPC Name - Role]
            [Description and connections]"""

            elif step == 'npc3':
                prompt = f"""Generate 4 options for the THIRD key NPC for this quest.

            QUEST CONTEXT:
            Hook: {selections.get('quest_hook', 'Not yet selected')}
            Objective: {selections.get('objective', 'Not yet selected')}
            Location: {selections.get('location', 'Not yet selected')}

            EXISTING NPCs:
            1. {selections.get('npc1', 'Not yet selected')}
            2. {selections.get('npc2', 'Not yet selected')}

            This NPC should add complexity or provide additional quest connections that work with the existing NPCs.

            For each NPC option include:
            - Name and role
            - Personality trait
            - How they connect to the quest or other NPCs

            Format as:
            ## Option X: [NPC Name - Role]
            [Description and connections]"""

            elif step == 'npc4':
                prompt = f"""Generate 4 options for the FOURTH key NPC for this quest.

            QUEST CONTEXT:
            Hook: {selections.get('quest_hook', 'Not yet selected')}
            Objective: {selections.get('objective', 'Not yet selected')}
            Location: {selections.get('location', 'Not yet selected')}

            EXISTING NPCs:
            1. {selections.get('npc1', 'Not yet selected')}
            2. {selections.get('npc2', 'Not yet selected')}
            3. {selections.get('npc3', 'Not yet selected')}

            This final NPC should round out the cast or provide a twist that ties into the overall quest.

            For each NPC option include:
            - Name and role
            - Personality trait
            - How they connect to the quest or other NPCs

            Format as:
            ## Option X: [NPC Name - Role]
            [Description and connections]"""

            elif step == 'equipment':
                prompt = f"""Suggest 4 equipment loadouts for this adventure.

            QUEST CONTEXT:
            Hook: {selections.get('quest_hook', 'Not yet selected')}
            Objective: {selections.get('objective', 'Not yet selected')}
            Location: {selections.get('location', 'Not yet selected')}

            PARTY:
            {', '.join([c['name'] + ' (' + c['char_class'] + ')' for c in context['characters']])}

            Each loadout should include:
            - Essential gear for the quest type and location
            - Tactical items that help achieve the objective
            - Estimated cost

            Format as:
            ## Option X: [Loadout Name]
            [Items and reasoning based on the quest context]"""

            elif step == 'roles':
                prompt = f"""Suggest 4 party role assignments based on the characters and quest.

            QUEST CONTEXT:
            Hook: {selections.get('quest_hook', 'Not yet selected')}
            Objective: {selections.get('objective', 'Not yet selected')}
            Location: {selections.get('location', 'Not yet selected')}

            PARTY:
            {chr(10).join([f"- {c['name']} ({c['char_class']}, Level {c['level']})" for c in context['characters']])}

            EQUIPMENT PLAN:
            {selections.get('equipment', 'Not yet selected')}

            For each suggestion include:
            - Who does what (specific to the quest objective)
            - Tactical synergies for this particular quest
            - Backup plans

            Format as:
            ## Option X: [Strategy Name]
            [Role assignments and reasoning]"""

            else:
                return jsonify({'error': 'Invalid step'}), 400
            
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

#### NPC #1
{selections.get('npc1', '*Not selected*')}

#### NPC #2
{selections.get('npc2', '*Not selected*')}

#### NPC #3
{selections.get('npc3', '*Not selected*')}

#### NPC #4
{selections.get('npc4', '*Not selected*')}

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
            # If completing Phase 2, initialize Phase 3 components AND update phase
            if phase == "call_to_adventure":
                from component.StoryPackage.story_package_tracker import StoryPackageTracker
                from component.GameState.story_state import StoryState
                from dataclasses import asdict
                
                # Load campaign
                campaign = campaign_mgr.load_campaign(campaign_name)
                campaign_dict = asdict(campaign)
                
                # Update phase to story_package (or whatever the next phase is called)
                campaign_dict['current_phase'] = 'story_package'
                
                # Initialize tracker if not exists
                if 'story_package_tracker' not in campaign_dict:
                    tracker = StoryPackageTracker(campaign_name=campaign_name)
                    tracker.start_package(1)
                    
                    campaign_dict['story_package_tracker'] = tracker.to_dict()
                
                # Initialize story_state if not exists
                if 'story_state' not in campaign_dict:
                    story_state = StoryState(
                        story_package_number=1,
                        package_phase=1
                    )
                    campaign_dict['story_state'] = story_state.to_dict()
                
                # Save everything in one operation
                campaign_mgr._save_campaign_dict(campaign_name, campaign_dict)
            else:
                # For other phases, just mark complete normally
                campaign_mgr.mark_phase_complete(campaign_name, phase)
            
            return jsonify({'success': True})
        except Exception as e:
            print(f"Error completing phase: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 400

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