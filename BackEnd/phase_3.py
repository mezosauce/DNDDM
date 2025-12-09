#!/usr/bin/env python3
"""
Phase 3: Story Package Routes
Backend Flask routes for the 15-step Story Package System

This file implements all routes needed to connect the frontend to the 
story package backend components (story_state, story_package_tracker, story_package_flow).
"""

from flask import render_template, redirect, url_for, request, jsonify, session, flash
from dataclasses import asdict
from typing import Tuple, Dict, Optional, Any
import json
import requests
from pathlib import Path
from urllib.parse import unquote

# Import backend components
from component.campaign_manager import CampaignManager
from component.StoryPackage.story_package_tracker import StoryPackageTracker
from component.GameState.story_state import StoryState
from component.StoryPackage.story_package_flow import StoryPackageFlow
from component.GameState.combat_state import CombatState, CombatParticipant
from component.GameState.dice_state import DiceRollState, DiceType, PlayerStats, RollType
from component.GameState.question_state import QuestioningState, QuestionType, PlayerResponse
from component.Class import character_from_dict


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_monster_choice(ai_response: str, monster_index: str) -> Optional[str]:
        """
        Validate that the AI chose a monster from the index.
        
        Returns:
            Monster name if valid, None if not found
        """
        import re
        
        # Extract monster names from index
        pattern = r'\* \[([^\]]+)\]'
        available_monsters = re.findall(pattern, monster_index)
        available_monsters_lower = [m.lower() for m in available_monsters]
        
        # Check if AI's response mentions any valid monster
        ai_response_lower = ai_response.lower()
        
        for i, monster_name in enumerate(available_monsters_lower):
            if monster_name in ai_response_lower:
                return available_monsters[i]  # Return original case
        
        return None

def decode_campaign_name(campaign_name: str) -> str:
    """Decode URL-encoded campaign name."""
    return unquote(campaign_name)

def load_story_package_data(campaign_name: str) -> Tuple[Any, StoryPackageTracker, StoryState, StoryPackageFlow]:
    """
    Load all story package components for a campaign.
    
    Returns:
        (campaign, tracker, story_state, flow)
    """
    manager = CampaignManager()
    campaign = manager.load_campaign(campaign_name)
    
    # Convert campaign to dict for accessing custom fields
    campaign_dict = asdict(campaign)
    
    # Load or initialize tracker
    tracker_data = campaign_dict.get('story_package_tracker')
    if tracker_data is not None and isinstance(tracker_data, dict):
        # Load existing tracker
        tracker = StoryPackageTracker.from_dict(tracker_data)
    else:
        # First time or corrupted data - initialize at package 1, step 1
        tracker = StoryPackageTracker(campaign_name=campaign_name)
        tracker.start_package(1)
    
    # Load or initialize story_state
    story_state_data = campaign_dict.get('story_state')
    if story_state_data is not None and isinstance(story_state_data, dict):
        # Load existing story state
        story_state = StoryState.from_dict(story_state_data)
    else:
        # First time or corrupted data - initialize
        story_state = StoryState(
            story_package_number=1,
            package_phase=1
        )
    
    # Create flow orchestrator
    flow = StoryPackageFlow(tracker, story_state)
    
    return campaign, tracker, story_state, flow


def save_story_package_data(
    campaign_name: str,
    tracker: StoryPackageTracker,
    story_state: StoryState
):
    """
    Save tracker and story_state to campaign JSON.
    """
    manager = CampaignManager()
    campaign = manager.load_campaign(campaign_name)
    
    # Convert to dict and add story package data
    campaign_dict = asdict(campaign)
    campaign_dict['story_package_tracker'] = tracker.to_dict()
    campaign_dict['story_state'] = story_state.to_dict()
    
    # Save back to campaign
    manager._save_campaign_dict(campaign_name, campaign_dict)


def parse_preparations(preparations_text: str) -> Dict:
    """
    Parse preparations.md to extract key sections for LLM context.
    
    Returns:
        {
            'quest_hook': str,
            'main_objective': str,
            'starting_location': str,
            'key_npc_1': str,
            'equipment_needed': str,
            'party_roles': str
        }
    """
    sections = {
        'quest_hook': '',
        'main_objective': '',
        'starting_location': '',
        'key_npc_1': '',
        'equipment_needed': '',
        'party_roles': ''
    }
    
    if not preparations_text:
        return sections
    
    lines = preparations_text.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        # Detect section headers
        if '### Quest Hook' in line:
            current_section = 'quest_hook'
            current_content = []
        elif '### Main Objective' in line:
            current_section = 'main_objective'
            current_content = []
        elif '### Starting Location' in line:
            current_section = 'starting_location'
            current_content = []
        elif '#### NPC #1' in line:
            current_section = 'key_npc_1'
            current_content = []
        elif '### Equipment Needed' in line:
            current_section = 'equipment_needed'
            current_content = []
        elif '### Party Roles & Strategy' in line:
            current_section = 'party_roles'
            current_content = []
        # Stop collecting when we hit another major section or end marker
        elif line.startswith('###') and current_section and line not in ['### Quest Hook', '### Main Objective', '### Starting Location', '### Equipment Needed', '### Party Roles & Strategy']:
            # Hit a different section (like Key NPCs or Notes)
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            current_section = None
            current_content = []
        elif line.startswith('---') or line.startswith('## 📝'):
            # End of relevant sections
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            break
        elif current_section:
            # Collect content for current section
            current_content.append(line)
    
    # Save any remaining content
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections


def build_story_context(campaign_name: str) -> Dict:
    """
    Build complete context for AI prompts.
    
    Returns:
        {
            'characters': list,
            'campaign': dict,
            'preparations': dict (parsed sections),
            'preparations_full': str (full text),
            'session_notes': str,
            'monster_index': str (INDEX.md content)
        }
    """
    manager = CampaignManager()
    context = manager.get_campaign_context(campaign_name)
    
    # Load preparations markdown if it exists
    prep_path = Path(__file__).parent.parent / "campaigns" / campaign_name / "preparations.md"
    preparations_full = ""
    preparations_parsed = {}
    
    if prep_path.exists():
        with open(prep_path, 'r', encoding='utf-8') as f:
            preparations_full = f.read()
            preparations_parsed = parse_preparations(preparations_full)
    
    # Load monster INDEX.md for combat encounters
    monster_index_path = Path(__file__).parent.parent / "srd_story_cycle" / "08_monsters_and_npcs" / "INDEX.md"
    monster_index = ""
    
    if monster_index_path.exists():
        with open(monster_index_path, 'r', encoding='utf-8') as f:
            monster_index = f.read()
    else:
        print(f"Warning: Monster INDEX.md not found at {monster_index_path}")
    
    # Build character summaries
    characters = []
    for char in context.get('characters', []):
        # Handle both dict and Character object formats
        if isinstance(char, dict):
            characters.append({
                'name': char.get('name', 'Unknown'),
                'race': char.get('race', 'Unknown'),
                'class': char.get('char_class', char.get('class', 'Unknown')),
                'level': char.get('level', 1),
                'hp': char.get('hp', 0),
                'max_hp': char.get('max_hp', 0),
                'stats': char.get('stats', {})
            })
        else:
            # Character object
            characters.append({
                'name': char.name,
                'race': char.race,
                'class': char.char_class,
                'level': char.level,
                'hp': char.hp,
                'max_hp': char.max_hp,
                'stats': char.stats
            })
    
    return {
        'characters': characters,
        'campaign': {
            'name': context['campaign']['name'],        
            'description': context['campaign']['description'],
            'session_number': context['campaign']['session_number']
        },
        'preparations': preparations_parsed,
        'preparations_full': preparations_full,
        'session_notes': context.get('session_notes', ''),
        'monster_index': monster_index  # Add monster index
    }


def call_claude_api(prompt: str, max_tokens: int = 1000) -> str:
    """
    Call Claude API with prompt.
    
    Returns:
        AI response text
    """
    # Using Ollama as proxy (you can modify this to use direct Anthropic API)
    try:
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3.2:3b",  # Or your preferred model
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": max_tokens,
                "repeat_penalty": 1.1
            }
        }
        
        response = requests.post(ollama_url, json=payload, timeout=120)
        response.raise_for_status()
        
        ai_response = response.json().get('response', '').strip()
        return ai_response
        
    except Exception as e:
        print(f"Error calling AI API: {e}")
        raise


def extract_monster_info_from_response(ai_response: str, monster_index: str = None) -> Optional[Dict]:
    """
    Parse AI response for monster information with validation.
    
    Returns monster data dict if found, None otherwise.
    """
    import re
    
    print(f"[DEBUG] Extracting monster from response: {ai_response[:200]}...")
    print(f"[DEBUG] Monster index provided: {monster_index is not None}")
    
    monster_name = None
    count = 1
    
    # Try multiple patterns to extract monster information
    patterns = [
        # Pattern 1: **2 Goblins**: or **Goblin**:
        r'\*\*(?:(\d+)\s+)?([a-zA-Z\s\-]+?)\*\*\s*:',
        
        # Pattern 2: encounter 2 goblins, face 3 wolves, etc.
        r'(?:encounter|face|fight|battle|confront)\s+(?:(\d+)\s+)?([a-zA-Z\s\-]+?)(?:\s|,|\.|!)',
        
        # Pattern 3: 3 goblins appear/attack/emerge
        r'(\d+)\s+([a-zA-Z\s\-]+?)\s+(?:appear|attack|emerge|step|block|rise|charge)',
        
        # Pattern 4: A goblin appears, The dragon attacks
        r'(?:a|an|the)\s+([a-zA-Z\s\-]+?)\s+(?:appear|attack|emerge|step|block|rise|charge)',
        
        # Pattern 5: Goblin(s) in the area
        r'([a-zA-Z\s\-]+?)(?:\(s\))?\s+(?:in the area|nearby|ahead)',
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, ai_response, re.IGNORECASE)
        if match:
            print(f"[DEBUG] Pattern {i+1} matched: {match.group(0)}")
            
            if len(match.groups()) == 2:
                # Pattern with count
                count_str, monster_name = match.groups()
                if count_str and count_str.isdigit():
                    count = int(count_str)
                else:
                    count = 1
            else:
                # Pattern without count
                monster_name = match.group(1)
                count = 1
            
            monster_name = monster_name.strip()
            break
    
    if not monster_name:
        print("[WARNING] No monster name found in response using patterns")
        
        # Last resort: look for common monster names directly in text
        from component.Class.monsters.monster_parser import MonsterParser
        parser = MonsterParser()
        
        # Try to find any monster name mentioned in the response
        response_lower = ai_response.lower()
        for potential_monster in ['goblin', 'orc', 'wolf', 'skeleton', 'zombie', 'kobold', 'bandit', 'swarm of bats']:
            if potential_monster in response_lower:
                monster_name = potential_monster
                # Try to extract count
                count_pattern = rf'(\d+)\s+{potential_monster}'
                count_match = re.search(count_pattern, response_lower)
                if count_match:
                    count = int(count_match.group(1))
                print(f"[DEBUG] Found common monster name: {monster_name} (count: {count})")
                break
    
    if not monster_name:
        print("[ERROR] Could not extract monster name from response")
        return None
    
    # Clean up monster name - remove plurals
    monster_name = monster_name.title()  # Capitalize properly
    
    if count > 1:
        # Remove plural endings
        if monster_name.endswith('ies'):
            monster_name = monster_name[:-3] + 'y'
        elif monster_name.endswith('ves'):
            monster_name = monster_name[:-3] + 'f'
        elif monster_name.endswith('es') and not monster_name.endswith(('shes', 'ches', 'xes', 'ses', 'zes', 'sses')):
            monster_name = monster_name[:-2]
        elif monster_name.endswith('s') and not monster_name.endswith('ss'):
            monster_name = monster_name[:-1]
    
    # Store the display name (with spaces)
    display_name = monster_name
    
    # Create lookup name (with underscores for file matching)
    lookup_name = monster_name.lower().replace(' ', '_')
    
    print(f"[DEBUG] Display name: '{display_name}' | Lookup name: '{lookup_name}' (count: {count})")
    
    # Try to find monster in SRD
    from component.Class.monsters.monster_parser import MonsterParser
    parser = MonsterParser()
    
    # Try lookup with underscored version first
    monster = parser.find_monster_by_name(lookup_name)
    
    if not monster:
        # Try with display name (title case with spaces)
        monster = parser.find_monster_by_name(display_name)
    
    if monster:
        print(f"[DEBUG] Found monster in SRD: {monster.name}")
        return {
            'count': count,
            'name': monster.name,  # Use the official name from SRD
            'description': ai_response[:200],
            'monster_data': monster.to_dict()
        }
    else:
        # Try alternative spellings or partial matches
        print(f"[WARNING] Monster '{display_name}' (lookup: '{lookup_name}') not found in SRD, trying alternatives...")
        
        # Try removing all non-alphanumeric except underscores
        lookup_clean = re.sub(r'[^a-z0-9_]', '', lookup_name)
        if lookup_clean != lookup_name:
            monster = parser.find_monster_by_name(lookup_clean)
        
        if not monster:
            # Try first word only (e.g., "Giant Spider" -> "spider")
            words = lookup_name.split('_')
            if len(words) > 1:
                monster = parser.find_monster_by_name(words[-1])
        
        if not monster:
            # Try last word from display name
            display_words = display_name.split()
            if len(display_words) > 1:
                monster = parser.find_monster_by_name(display_words[-1])
        
        if monster:
            print(f"[DEBUG] Found alternative monster: {monster.name}")
            return {
                'count': count,
                'name': monster.name,
                'description': ai_response[:200],
                'monster_data': monster.to_dict()
            }
        
        # Complete fallback - use generic monster
        print(f"[WARNING] Using fallback generic monster for: {display_name}")
        return {
            'count': count,
            'name': display_name,  # Use display name for generic monsters
            'description': ai_response[:200],
            'monster_data': {
                'name': display_name,
                'monster_type': 'humanoid',
                'size': 'Medium',
                'alignment': 'unaligned',
                'challenge_rating': 0.5,
                'xp': 100,
                'hp': 15,
                'ac': 12,
                'speed': {'walk': 30},
                'stats': {
                    'strength': 10,
                    'dexterity': 12,
                    'constitution': 10,
                    'intelligence': 8,
                    'wisdom': 10,
                    'charisma': 8
                },
                'abilities': [],
                'actions': [
                    'Slam. Melee Weapon Attack: +2 to hit, reach 5 ft., one target. Hit: 1d6 bludgeoning damage.'
                ],
                'legendary_actions': [],
                'lair_actions': []
            }
        }
    
def extract_dice_situation_from_response(ai_response: str) -> Optional[Dict]:
    """
    Parse AI response for dice roll requirements.
    
    Returns dice situation dict if found, None otherwise.
    """
    import re
    
    # Look for DC mentions
    dc_match = re.search(r'DC\s*(\d+)', ai_response, re.IGNORECASE)
    dc = int(dc_match.group(1)) if dc_match else 15
    
    # Look for skill/stat mentions
    skills = ['athletics', 'acrobatics', 'stealth', 'perception', 'investigation']
    skill = None
    for s in skills:
        if s in ai_response.lower():
            skill = s
            break
    
    # Look for stat mentions
    stats = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
    stat = 'strength'  # default
    for st in stats:
        if st in ai_response.lower():
            stat = st
            break
    
    if dc_match or skill:
        return {
            'situation': ai_response[:200],
            'dc': dc,
            'stat': stat,
            'skill': skill,
            'dice_type': 'd20'
        }
    
    return None


def extract_question_from_response(ai_response: str) -> Optional[Dict]:
    """
    Parse AI response for binary question with improved extraction.
    
    Returns question data dict if found, None otherwise.
    """
    import re
    
    # Look for ***QUEST*** markers first (as shown in prompt template)
    quest_pattern = r'\*\*\*QUEST\*\*\*\s*(.*?)\s*\*\*\*QUEST\*\*\*'
    quest_match = re.search(quest_pattern, ai_response, re.DOTALL | re.IGNORECASE)
    
    if quest_match:
        question_text = quest_match.group(1).strip()
        return {
            'question_text': question_text,
            'full_context': ai_response
        }
    
    # Fallback: Look for sentences with question marks
    sentences = re.split(r'[.!]\s+', ai_response)
    for sentence in sentences:
        if '?' in sentence:
            # Clean up the sentence
            question_text = sentence.strip()
            if not question_text.endswith('?'):
                question_text = question_text.split('?')[0] + '?'
            
            return {
                'question_text': question_text,
                'full_context': ai_response
            }
    
    # Last resort: use entire response
    if ai_response.strip():
        return {
            'question_text': ai_response.strip(),
            'full_context': ai_response
        }
    
    return None



# ============================================================================
# ROUTE REGISTRATION FUNCTION
# ============================================================================

def register_story_package_routes(app):
    """Register all story package routes with the Flask app"""
    
    # ========================================================================
    # 1. HUB/ROUTER ROUTE
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/story-package')
    def story_package_hub(campaign_name):
        """Main entry point that routes to correct state page based on tracker"""
        try:
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            # Get current state type from tracker
            state_type = tracker.get_current_state_type()
            
            print(f"[HUB] Campaign: {campaign_name}")
            print(f"[HUB] Package: {tracker.current_package}, Step: {tracker.current_step}")
            print(f"[HUB] State Type: {state_type}")
            
            # Route to appropriate page based on state
            if state_type == 'story':
                return redirect(url_for('story_state_page', campaign_name=campaign_name))
            elif state_type == 'question':
                return redirect(url_for('question_state_page', campaign_name=campaign_name))
            elif state_type == 'dice':
                return redirect(url_for('dice_state_page', campaign_name=campaign_name))
            elif state_type == 'combat':
                return redirect(url_for('combat_state_page', campaign_name=campaign_name))
            else:
                print(f"[HUB ERROR] Invalid state type: {state_type}")
                return f"Invalid state type: {state_type}", 500
                
        except Exception as e:
            print(f"[HUB ERROR] Error in story_package_hub: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", 500
    
    # ========================================================================
    # 2. STORY STATE PAGE
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/story-state')
    def story_state_page(campaign_name):
        """Display story narration and DM dialogue"""
        try:
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            # Get current step definition
            current_step = tracker.current_step
            step_definition = flow.get_step_definition(current_step)
            
            # Check if we have cached narrative content
            cache_key = f"step_{current_step}_content"
            narrative_content = session.get(cache_key, None)
            
            # Determine if this is the conditional evaluation step
            is_conditional = (current_step == 11)
            
            # Build context data

            context_data = {
            'campaign_name': campaign_name,
            'tracker': tracker.to_dict(),
            'story_state': story_state.to_dict(),
            'current_step': current_step,
            'step_definition': {
                'name': step_definition.get('description', 'Story Step'),
                'description': step_definition.get('purpose', ''),
                'state_type': step_definition.get('state', 'story'),
                'requires_ai': step_definition.get('requires_ai', True),
                'is_transition': step_definition.get('next_state_trigger') is not None,
                'next_state_type': step_definition.get('state', 'story')
            },
            'narrative_content': narrative_content,
            'show_continue_button': True,
            'is_conditional_evaluation': is_conditional,
            'package_number': tracker.current_package,
            'package_progress': f"{current_step}/15"
        }
            
            return render_template('HTML/story_state.html', **context_data)
            
        except Exception as e:
            print(f"Error in story_state_page: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", 500
    
    
    # ========================================================================
    # 3. STORY STATE ADVANCE
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/story-state/advance', methods=['POST'])
    def story_state_advance(campaign_name):
        """Player clicks Continue button to advance story"""
        try:
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            current_step = tracker.current_step
            step_def = flow.get_step_definition(current_step)
            
            # Special handling for step 11 (conditional evaluation)
            if current_step == 11:
                # Get last dice result
                last_dice_result = story_state.last_dice_result
                
                if not last_dice_result:
                    return jsonify({'error': 'No dice result found for conditional evaluation'}), 400
                
                # Determine if conditional combat triggers based on dice success
                success = last_dice_result.get('success', False)
                
                if success:
                    # Dice roll succeeded - skip conditional combat (steps 12-14)
                    tracker.skip_conditional_combat()
                    story_state.add_story_event(
                        event_type="conditional_skip",
                        narrative_text="Dice roll succeeded - skipping conditional combat",
                        metadata={"dice_result": last_dice_result}
                    )
                else:
                    # Dice roll failed - trigger conditional combat
                    tracker.trigger_conditional_combat()
                    story_state.add_story_event(
                        event_type="conditional_trigger",
                        narrative_text="Dice roll failed - triggering conditional combat",
                        metadata={"dice_result": last_dice_result}
                    )
                
                # Clear cached content for new step
                session.pop(f"step_{current_step}_content", None)
                
            else:
                # Normal advancement
                tracker.advance_step()
                
                # Clear cached content
                session.pop(f"step_{current_step}_content", None)
            
            # Save everything
            save_story_package_data(campaign_name, tracker, story_state)
            
            # Return success with redirect
            return jsonify({
                'success': True,
                'redirect': url_for('story_package_hub', campaign_name=campaign_name)
            })
            
        except Exception as e:
            print(f"Error in story_state_advance: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str    (e)}), 500
    
    # ========================================================================
    # 4. STORY STATE AI GENERATE
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/story-state/ai-generate', methods=['POST'])
    def story_state_ai_generate(campaign_name):
        """AJAX endpoint to generate AI content for current step"""
        try:
            data = request.json
            force_regenerate = data.get('force_regenerate', False)
            
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            current_step = tracker.current_step
            step_def = flow.get_step_definition(current_step)
            
            # Check cache first
            cache_key = f"step_{current_step}_content"
            if not force_regenerate and cache_key in session:
                return jsonify({
                    'success': True,
                    'content': session[cache_key],
                    'step': current_step,
                    'state_type': 'story',
                    'cached': True
                })
            
            # Build context for AI
            context_data = build_story_context(campaign_name)
            context_data['current_step'] = current_step
            context_data['step_definition'] = step_def
            context_data['story_state'] = story_state.to_dict()
            context_data['tracker'] = tracker.to_dict()
            
            # Generate prompt
            prompt = flow.generate_ai_prompt_for_step(current_step, context_data)
            
            # Call AI
            ai_response = call_claude_api(prompt, max_tokens=800)
            
            # Parse response for state transition hints
            if current_step == 6:
                # Extract monster info for upcoming combat
                monster_info = extract_monster_info_from_response(ai_response, context_data.get('monster_index'))

                if monster_info:
                    story_state.pending_monster = monster_info
            
            elif current_step in [4, 9]:
                # Extract dice situation
                dice_situation = extract_dice_situation_from_response(ai_response)
                if dice_situation:
                    story_state.pending_dice_situation = dice_situation
            
            elif current_step == 2:
                # Extract question
                question = extract_question_from_response(ai_response)
                if question:
                    story_state.pending_question = question
            
            # Cache the response
            session[cache_key] = ai_response
            
            # Save story_state
            save_story_package_data(campaign_name, tracker, story_state)
            
            return jsonify({
                'success': True,
                'content': ai_response,
                'step': current_step,
                'state_type': 'story',
                'cached': False
            })
            
        except Exception as e:
            print(f"Error in story_state_ai_generate: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    
    # ========================================================================
    # 5. QUESTION STATE PAGE
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/question-state')
    def question_state_page(campaign_name):
        """Display binary Accept/Decline choice"""
        try:
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            # Get question data from story_state
            question_data = story_state.pending_question or {}
            
            # If no question exists, generate one
            if not question_data or not question_data.get('question_text'):
                print("[Question State] No pending question found, generating...")
                
                # Build context for AI
                context_data_build = build_story_context(campaign_name)
                context_data_build['current_step'] = tracker.current_step
                context_data_build['story_state'] = story_state.to_dict()
                context_data_build['tracker'] = tracker.to_dict()
                
                # Generate prompt using flow
                prompt = flow.generate_ai_prompt_for_step(tracker.current_step, context_data_build)
                
                # Call AI
                ai_response = call_claude_api(prompt, max_tokens=600)
                
                # Extract question from response
                question_data = extract_question_from_response(ai_response)
                
                if not question_data:
                    # Fallback parsing if extract function fails
                    question_data = {
                        'question_text': ai_response,
                        'full_context': ai_response
                    }
                
                # Store in story_state
                story_state.pending_question = question_data
                save_story_package_data(campaign_name, tracker, story_state)
                
                print(f"[Question State] Generated question: {question_data.get('question_text', '')[:100]}...")
            
            context_data = {
                'campaign_name': campaign_name,
                'tracker': tracker.to_dict(),
                'story_state': story_state.to_dict(),
                'question_text': question_data.get('question_text', 'Do you accept this quest?'),
                'question_context': question_data.get('full_context', ''),
                'consequences_accept': 'You will embark on this quest.',
                'consequences_decline': 'You will seek another path.'
            }
            
            return render_template('HTML/question_state.html', **context_data)
        except Exception as e:
            print(f"Error in question_state_page: {e}")
            return f"Error: {str(e)}", 500
    
    
    # ========================================================================
    # 6. QUESTION STATE SUBMIT
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/question-state/submit', methods=['POST'])
    def question_state_submit(campaign_name):
        """Process player's Accept/Decline response"""
        try:
            campaign_name = decode_campaign_name(campaign_name)
            
            data = request.json
            answer = data.get('answer', '').lower()
            
            if answer not in ['accept', 'decline']:
                return jsonify({'error': 'Invalid answer. Must be accept or decline'}), 400
            
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            # Store decision in story_state
            story_state.last_question_answer = {
                'answer': answer,
                'question': story_state.pending_question
            }
            
            # Record in player decisions
            story_state.add_player_decision(
                decision=answer,
                outcome= f"Player chose to {answer}"
            )
            
            # Clear pending question
            story_state.pending_question = None
            
            # Advance tracker
            tracker.advance_step()
            
            # Save
            save_story_package_data(campaign_name, tracker, story_state)
            
            return redirect(url_for('story_package_hub', campaign_name=campaign_name))
            
        except Exception as e:
            print(f"Error in question_state_submit: {e}")
            return jsonify({'error': str(e)}), 500
    
    
    # ========================================================================
    # 7. DICE ROLL STATE PAGE
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/dice-state')
    def dice_state_page(campaign_name):
        """Display dice rolling interface"""
        try:
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            # Get dice situation from story_state
            dice_situation = story_state.pending_dice_situation or {}
            
            # Get character for stat modifiers
            manager = CampaignManager()
            characters = manager.get_characters(campaign_name)
            character = characters[0] if characters else None
            
            if not character:
                return "No character found in campaign", 400
            
            # Prepare template data
            from BackEnd.component.GameState.dice_state import DiceType, RollType, DifficultyLevel
            
            # Build difficulty levels dict
            difficulty_levels = {
                'Trivial': DifficultyLevel.TRIVIAL.value,
                'Easy': DifficultyLevel.EASY.value,
                'Medium': DifficultyLevel.MEDIUM.value,
                'Hard': DifficultyLevel.HARD.value,
                'Very Hard': DifficultyLevel.VERY_HARD.value,
                'Nearly Impossible': DifficultyLevel.NEARLY_IMPOSSIBLE.value
            }
            
            # Build dice types list
            dice_types = [dt.name for dt in DiceType]
            
            # Build roll types list
            roll_types = [rt.value for rt in RollType]
            
            # Build player stats dict
            player_stats = {
                'strength': character.stats.get('strength', 10),
                'dexterity': character.stats.get('dexterity', 10),
                'constitution': character.stats.get('constitution', 10),
                'intelligence': character.stats.get('intelligence', 10),
                'wisdom': character.stats.get('wisdom', 10),
                'charisma': character.stats.get('charisma', 10),
                'proficiency_bonus': 2,  # Could calculate from level
                'equipment_bonus': 0,
                'temporary_bonus': 0,
                'proficient_skills': []  # Could get from character
            }
            
            context_data = {
                'campaign_name': campaign_name,
                'tracker': tracker.to_dict(),
                'story_state': story_state.to_dict(),
                'dice_situation': dice_situation,
                'character': asdict(character),
                'roll_type': 'normal',
                'dc': dice_situation.get('dc', 15),
                'stat': dice_situation.get('stat', 'strength'),
                'skill': dice_situation.get('skill', None),
                # Template-required variables
                'difficulty_levels': difficulty_levels,
                'dice_types': dice_types,
                'roll_types': roll_types,
                'player_stats': player_stats,
                'statistics': {
                    'total_rolls': 0,
                    'critical_successes': 0,
                    'successes': 0,
                    'failures': 0,
                    'critical_failures': 0,
                    'success_rate': 0,
                    'average_roll': 0,
                    'current_active': False
                },
                'roll_history': []
            }
            
            return render_template('HTML/dice_roll_state.html', **context_data)
            
        except Exception as e:
            print(f"Error in dice_state_page: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", 500
    
    # ========================================================================
    # 8. DICE ROLL EXECUTE
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/dice-state/roll', methods=['POST'])
    def dice_roll_execute(campaign_name):
        """Execute dice roll and calculate result"""
        try:
            data = request.json
            
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            # Get character stats
            manager = CampaignManager()
            characters = manager.get_characters(campaign_name)
            character = characters[0] if characters else None
            
            if not character:
                return jsonify({'error': 'No character found'}), 400
            
            # Create PlayerStats from character
            player_stats = PlayerStats(
                strength=character.stats.get('strength', 10),
                dexterity=character.stats.get('dexterity', 10),
                constitution=character.stats.get('constitution', 10),
                intelligence=character.stats.get('intelligence', 10),
                wisdom=character.stats.get('wisdom', 10),
                charisma=character.stats.get('charisma', 10),
                proficiency_bonus=2  # Could be calculated from level
            )
            
            # Create DiceRollState
            dice_state = DiceRollState(player_stats=player_stats)
            
            # Get situation
            situation = story_state.pending_dice_situation or {}
            
            # Activate roll
            dice_state.activate_roll(
                situation=situation.get('situation', 'Make a check'),
                dice_type=DiceType.D20,
                target_number=situation.get('dc', 15),
                relevant_stat=situation.get('stat', 'strength'),
                skill=situation.get('skill', None),
                roll_type=RollType.NORMAL
            )
            
            # Execute roll
            result = dice_state.execute_roll()
            
            # Store result in story_state
            story_state.last_dice_result = {
                'total': result.total_score,
                'target': result.target_number,
                'success': result.total_score >= result.target_number,
                'outcome': result.outcome.value,
                'margin': result.margin,
                'raw_roll': result.selected_roll
            }
            
            # Clear pending situation
            story_state.pending_dice_situation = None
            
            # Advance tracker
            tracker.advance_step()
            
            # Save
            save_story_package_data(campaign_name, tracker, story_state)
            
            return jsonify({
                'success': True,
                'result': story_state.last_dice_result,
                'narrative': result.get_narrative_result(),
                'breakdown': result.get_roll_breakdown(),
                'redirect': url_for('story_package_hub', campaign_name=campaign_name)
            })
            
        except Exception as e:
            print(f"Error in dice_roll_execute: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    # ========================================================================
    # 9. COMBAT STATE PAGE
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/combat-state')
    def combat_state_page(campaign_name):
        """Display combat encounter interface"""
        try:
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            import uuid
            old_combat_id = session.get('current_combat_id')
            if old_combat_id:
                old_session_key = f'combat_{old_combat_id}'
                session.pop(old_session_key, None)
                print(f"[Combat] Cleared old combat data: {old_combat_id}")
            
            # Generate fresh combat ID
            combat_id = str(uuid.uuid4())
            session['current_combat_id'] = combat_id
            print(f"[Combat] Generated new combat ID: {combat_id}")
            
            # Always initialize new combat (no loading from session)
            combat_state = None
            
            if True:
                # Get monster info from story_state
                monster_info = story_state.pending_monster
                
                if not monster_info:
                    return "No monster information found. Please restart from story state.", 400
                
                # Load characters
                manager = CampaignManager()
                characters = manager.get_characters(campaign_name)
                # Debug: Print character data
                print(f"[Combat Init] Loaded {len(characters)} characters")
                for char in characters:
                    print(f"[Combat Init] Character: {char.name}")
                    print(f"  - Type: {type(char)}")
                    print(f"  - Has char_class: {hasattr(char, 'char_class')}")
                    print(f"  - char_class value: {getattr(char, 'char_class', 'NOT FOUND')}")
                    print(f"  - Has class: {hasattr(char, 'class')}")
                    print(f"  - Has level: {hasattr(char, 'level')}")
                    print(f"  - level value: {getattr(char, 'level', 'NOT FOUND')}")
                    print(f"  - All attributes: {dir(char)}")

                # Get full monster data
                monster_data = monster_info.get('monster_data')
                if not monster_data:
                    return "Monster data not loaded properly.", 400
                
                # Create Monster instances
                from component.Class.monsters.monster import Monster
                monster = Monster.from_dict(monster_data)
                
                monsters = []
                for i in range(monster_info['count']):
                    monster_copy = Monster.from_dict(monster_data)
                    if monster_info['count'] > 1:
                        monster_copy.name = f"{monster_copy.name} #{i+1}"
                    monsters.append(monster_copy)
                
                # Create combat state
                from component.GameState.combat_state import CombatState
                combat_state = CombatState.from_monsters_and_characters(
                    monsters=monsters,
                    characters=characters,
                    encounter_name=f"Battle vs {monster.name}"
                )
                
                # Initialize combat
                combat_state.roll_initiative()
                combat_state.determine_turn_order()
                combat_state.init_combat()
                
                # Save using the proper serialization function
                try:
                    combat_str = serialize_combat(combat_state)
                    session_key = f'combat_{combat_id}'
                    session[session_key] = combat_str
                    session.modified = True
                    print(f"[Combat] Combat initialized and saved with ID: {combat_id}")
                except Exception as e:
                    print(f"[Combat] Error saving combat: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Get summary for template
            combat_data = combat_state.get_combat_summary()
            
            context_data = {
                'campaign_name': campaign_name,
                'combat_id': combat_id,  
                'tracker': tracker.to_dict(),
                'story_state': story_state.to_dict(),
                'combat_state': combat_data,
                'encounter_name': combat_data.get('encounter_name', 'Combat'),
                'monsters': combat_data.get('participants', []),
                'characters': combat_data.get('participants', []),
                'initiative_order': combat_data.get('initiative_order', [])
            }
            
            return render_template('HTML/combat_state.html', **context_data)
            
        except Exception as e:
            print(f"Error in combat_state_page: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", 500
        
    
    # ========================================================================
    # 10. COMBAT STATE INITIALIZE
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/combat-state/init', methods=['POST'])
    def combat_state_init(campaign_name):
        """Initialize combat encounter"""
        try:
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            # Get monster info from story_state
            monster_info = story_state.pending_monster
            
            if not monster_info:
                return jsonify({'error': 'No monster information found'}), 400
            
            # Load characters
            manager = CampaignManager()
            characters = manager.get_characters(campaign_name)
            
            # Get full monster data
            monster_data = monster_info.get('monster_data')
            if not monster_data:
                return jsonify({'error': 'Monster data not loaded properly'}), 400
            
            # Create Monster instance from data
            from component.Class.monsters.monster import Monster
            monster = Monster.from_dict(monster_data)
            
            # Create multiple monsters if count > 1
            monsters = []
            for i in range(monster_info['count']):
                # Create a copy with unique name
                monster_copy = Monster.from_dict(monster_data)
                if monster_info['count'] > 1:
                    monster_copy.name = f"{monster_copy.name} #{i+1}"
                monsters.append(monster_copy)
            
            # Create combat state
            combat_state = CombatState.from_monsters_and_characters(
                monsters=monsters,
                characters=characters,
                encounter_name=f"Battle vs {monster.name}"
            )
            
            # Roll initiative
            combat_state.roll_initiative()
            combat_state.determine_turn_order()
            combat_state.init_combat()
            
            # Get summary
            combat_summary = combat_state.get_combat_summary()
            
            # Store in session
            session['active_combat'] = combat_summary
            
            return jsonify({
                'success': True,
                'combat_summary': combat_summary
            })
            
        except Exception as e:
            print(f"Error in combat_state_init: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
        
    # ========================================================================
    # 11. COMBAT STATE ACTION
    # ========================================================================
    
    @app.route('/campaign/<campaign_name>/combat-state/action', methods=['POST'])
    def combat_state_action(campaign_name):
        """Process combat actions"""
        try:
            data = request.json
            action_type = data.get('action_type')
            
            # Get active combat from session
            combat_data = session.get('active_combat')
            
            if not combat_data:
                return jsonify({'error': 'No active combat'}), 400
            
            # For simplicity, track if combat is complete
            # In full implementation, you'd reconstruct CombatState and process actions
            
            # Simplified: just check if combat should end
            if action_type == 'end_combat':
                campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
                
                # Store combat result
                story_state.last_combat_result = {
                    'victory': True,
                    'rounds': combat_data.get('round', 1),
                    'summary': 'Combat completed successfully'
                }
                
                # Clear pending monster
                story_state.pending_monster = None
                
                # Clear session combat
                session.pop('active_combat', None)
                
                # Advance tracker
                tracker.advance_step()
                
                # Save
                save_story_package_data(campaign_name, tracker, story_state)
                
                return jsonify({
                    'success': True,
                    'combat_complete': True,
                    'redirect': url_for('story_package_hub', campaign_name=campaign_name)
                })
            
            # Otherwise return updated combat summary
            return jsonify({
                'success': True,
                'combat_summary': combat_data
            })
            
        except Exception as e:
            print(f"Error in combat_state_action: {e}")
            return jsonify({'error': str(e)}), 500
    
    
    print("✓ Story package routes registered")

    # Serilization
    import pickle
    import base64

    def serialize_combat(combat: CombatState) -> str:
        """Serialize combat state to string for session storage"""
        try:
            # Use pickle to serialize
            pickled = pickle.dumps(combat)
            # Encode to base64 string
            return base64.b64encode(pickled).decode('utf-8')
        except Exception as e:
            print(f"Error serializing combat: {e}")
            raise

    def deserialize_combat(combat_str: str) -> CombatState:
        """Deserialize combat state from session string"""
        try:
            # Decode from base64
            pickled = base64.b64decode(combat_str.encode('utf-8'))
            # Unpickle
            return pickle.loads(pickled)
        except Exception as e:
            print(f"Error deserializing combat: {e}")
            raise

    # Update the helper functions:


    def save_combat_to_session(combat_id: str, combat: CombatState):
        """Save combat to session with proper serialization"""
        session_key = f'combat_{combat_id}'
        
        try:
            combat_str = serialize_combat(combat)
            session[session_key] = combat_str
            session.modified = True
        except Exception as e:
            print(f"Error saving combat to session: {e}")
            raise

   
    
    
    @app.route('/api/campaign/<campaign_name>/characters', methods=['GET'])
    def get_campaign_characters(campaign_name):
        """Get full character data for a campaign"""
        try:
            manager = CampaignManager()
            characters = manager.get_characters(campaign_name)
            
            # Convert to dicts
            char_dicts = []
            for char in characters:
                if hasattr(char, '__dict__'):
                    char_dict = {
                        'name': char.name,
                        'char_class': getattr(char, 'char_class', 'Unknown'),
                        'class': getattr(char, 'char_class', 'Unknown'),
                        'level': getattr(char, 'level', 1),
                        'race': getattr(char, 'race', 'Unknown'),
                        'background': getattr(char, 'background', ''),
                        'stats': getattr(char, 'stats', {}),
                        'hp': getattr(char, 'hp', 0),
                        'max_hp': getattr(char, 'max_hp', 0)
                    }
                else:
                    char_dict = char
                
                char_dicts.append(char_dict)
            
            return jsonify({
                'success': True,
                'characters': char_dicts
            })
            
        except Exception as e:
            print(f"[API] Error getting characters: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    

    
        
    def get_combat_from_session(combat_id: str) -> Optional[CombatState]:
        """Load combat from session with proper deserialization"""
        session_key = f'combat_{combat_id}'
        
        if session_key not in session:
            return None
        
        try:
            combat_str = session[session_key]
            return deserialize_combat(combat_str)
        except Exception as e:
            print(f"Error loading combat from session: {e}")
            return None
        
    print("✓ Story package routes registered")
    
