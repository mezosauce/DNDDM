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
    
    print(f"[DEBUG] Extracting monster from response: {ai_response[:100]}...")
    print(f"[DEBUG] Monster index provided: {monster_index is not None}")
    
    # First, try to extract monster name from **Monster Name**: format
    bold_pattern = r'\*\*(?:(\d+)\s+)?([a-zA-Z\s]+)\*\*:'
    bold_match = re.search(bold_pattern, ai_response)

    monster_name = None
    count = 1  # Default to 1 monster

    if bold_match:
        count_str = bold_match.group(1)  # Might be None
        monster_name = bold_match.group(2).strip()
        
        # Get count if it was in the bold text
        if count_str:
            count = int(count_str)
        
        # Remove plural 's' or 'es' from monster name if count > 1
        if count > 1:
            if monster_name.endswith('ies'):
                # e.g., "Harpies" -> "Harpy"
                monster_name = monster_name[:-3] + 'y'
            elif monster_name.endswith('es'):
                # e.g., "Wolves" -> "Wolf" (but watch for "Horses" -> "Horse")
                if monster_name.endswith('ves'):
                    # e.g., "Wolves" -> "Wolf"
                    monster_name = monster_name[:-3] + 'f'
                elif not monster_name.endswith(('shes', 'ches', 'xes', 'ses', 'zes')):
                    # Not a natural 'es' ending, remove it
                    monster_name = monster_name[:-2]
                else:
                    # Natural 'es' ending like "Horses"
                    monster_name = monster_name[:-2]
            elif monster_name.endswith('s') and not monster_name.endswith('ss'):
                # e.g., "Rats" -> "Rat", but "Brass" stays "Brass"
                monster_name = monster_name[:-1]
        
        print(f"[DEBUG] Found monster in bold: {monster_name} (count: {count})")
        
    else:
        # Fallback: Look for patterns like "3 goblins attack" or "1 dragon appears"
        pattern = r'(\d+)\s+([a-zA-Z\s]+?)(?:s|es)?\s*(?:appear|attack|emerge|step|block|rise)'
        matches = re.findall(pattern, ai_response.lower())
        
        if matches:
            count, monster_name = matches[0]
            monster_name = monster_name.strip()
            count = int(count)
    
    if not monster_name:
        print("[WARNING] No monster name found in response")
        return None
    
    from component.Class.monsters.monster_parser import MonsterParser

    parser = MonsterParser()
    print(f"[DEBUG] Searching for monster: '{monster_name}'")
    monster = parser.find_monster_by_name(monster_name)

    if monster:
        return {
            'count': count,
            'name': monster.name,
            'description': ai_response[:200],
            
            'monster_data': monster.to_dict()  # Full monster stats
        }
    else:
        # Fallback if monster not found in SRD
        print(f"[WARNING] Monster {monster_name} not found in SRD, using defaults")
        return {
            'count': count,
            'name': monster_name,
            'description': ai_response[:200],
            
            'monster_data': {
                'name': monster_name,
                'monster_type': 'unknown',
                'size': 'Medium',
                'alignment': 'unaligned',
                'challenge_rating': 1.0,
                'hp': 20,
                'ac': 12,
                'stats': {
                    'strength': 10,
                    'dexterity': 10,
                    'constitution': 10,
                    'intelligence': 10,
                    'wisdom': 10,
                    'charisma': 10
                },
                'abilities': [],
                'actions': ['Slam. Melee Weapon Attack: +2 to hit, reach 5 ft. Hit: 1d6+0 damage.'],
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
    Parse AI response for binary question.
    
    Returns question data dict if found, None otherwise.
    """
    # Look for question marks
    sentences = ai_response.split('.')
    for sentence in sentences:
        if '?' in sentence:
            return {
                'question_text': sentence.strip(),
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
            return jsonify({'error': str(e)}), 500
    
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
            combat_id = session.get('current_combat_id')
            if not combat_id:
                combat_id = str(uuid.uuid4())
                session['current_combat_id'] = combat_id
            
            # Try to get existing combat using the correct key format
            session_key = f'combat_{combat_id}'
            combat_state = None
            
            if session_key in session:
                try:
                    combat_state = deserialize_combat(session[session_key])
                    print(f"[Combat] Loaded existing combat from session")
                except Exception as e:
                    print(f"[Combat] Error deserializing combat: {e}")
                    combat_state = None
            
            if not combat_state:
                # Initialize new combat
                print(f"[Combat] Initializing new combat with ID: {combat_id}")
                
                # Get monster info from story_state
                monster_info = story_state.pending_monster
                
                if not monster_info:
                    return "No monster information found. Please restart from story state.", 400
                
                # Load characters
                manager = CampaignManager()
                characters = manager.get_characters(campaign_name)
                
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
                save_combat_to_session(combat_id, combat_state)
                print(f"[Combat] Combat initialized and saved with ID: {combat_id}")
            
            # Get summary for template
            combat_data = combat_state.get_combat_summary()
            
            context_data = {
                'campaign_name': campaign_name,
                'combat_id': combat_id,  # Use persistent combat_id
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

    # ========================================================================
    # GAME LOGIC
    # ========================================================================
    from flask import jsonify, request, session
    from typing import Optional
    import random

    def register_combat_routes(app):
        """Register all combat-related API routes"""
        
        @app.route('/api/combat/<combat_id>/summary', methods=['GET'])
        def get_combat_summary(combat_id):
            """Get current combat state"""
            try:
                # Get combat from session
                combat = get_combat_from_session(combat_id)
                
                if not combat:
                    return jsonify({
                        'success': False,
                        'error': 'Combat not found'
                    }), 404
                
                # Build participant data
                participants = []
                for p in combat.participants:
                    participant_data = {
                        'participant_id': p.participant_id,
                        'name': p.name,
                        'type': p.participant_type.value,
                        'initiative': p.initiative,
                        'hp': p.get_current_hp(),
                        'max_hp': p.get_max_hp(),
                        'ac': p.get_ac(),
                        'is_alive': p.is_alive(),
                        'conditions': list(p.conditions) if hasattr(p, 'conditions') else []
                    }
                    
                    # Add character-specific data
                    if p.participant_type.value == 'character':
                        entity = p.entity
                        participant_data['class'] = getattr(entity, 'char_class', 'Unknown')
                        participant_data['level'] = getattr(entity, 'level', 1)
                        
                        # Add resources based on class
                        if hasattr(entity, 'currently_raging'):
                            participant_data['rage'] = {
                                'active': entity.currently_raging,
                                'uses_remaining': entity.rages_per_day - entity.rages_used
                            }
                        
                        if hasattr(entity, 'bardic_inspiration_remaining'):
                            participant_data['bardic_inspiration'] = {
                                'remaining': entity.bardic_inspiration_remaining,
                                'die': entity.bardic_inspiration_die
                            }
                        
                        if hasattr(entity, 'spell_slots_used'):
                            participant_data['spell_slots'] = {
                                'used': entity.spell_slots_used,
                                'max': entity.spell_slots
                            }
                        
                        if hasattr(entity, 'wild_shape_uses_remaining'):
                            participant_data['wild_shape'] = {
                                'remaining': entity.wild_shape_uses_remaining,
                                'active': entity.currently_wild_shaped,
                                'beast': entity.wild_shape_beast if entity.currently_wild_shaped else None
                            }
                        
                        if hasattr(entity, 'channel_divinity_used'):
                            max_uses = 1 if entity.level < 6 else (2 if entity.level < 18 else 3)
                            participant_data['channel_divinity'] = {
                                'remaining': max_uses - entity.channel_divinity_used
                            }
                    
                    participants.append(participant_data)
                
                # Get current turn info
                current_participant = combat.get_current_participant()
                current_turn = {
                    'participant_id': current_participant.participant_id if current_participant else None,
                    'name': current_participant.name if current_participant else None,
                    'type': current_participant.participant_type.value if current_participant else None
                }
                
                # Build response
                summary = {
                    'combat_id': combat_id,
                    'encounter_name': combat.encounter_name,
                    'participants': participants,
                    'initiative_order': [p.participant_id for p in combat.initiative_order],
                    'current_turn': current_turn,
                    'current_turn_index': combat.current_turn_index,
                    'round': combat.current_round,
                    'phase': combat.combat_phase.value,
                    'combat_log': combat.combat_log[-20:] if hasattr(combat, 'combat_log') else []
                }
                
                return jsonify({
                    'success': True,
                    'summary': summary
                })
                
            except Exception as e:
                print(f"[API] Error getting combat summary: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @app.route('/api/combat/<combat_id>/player-action', methods=['POST'])
        def process_player_action(combat_id):
            """Process player's combat action"""
            try:
                data = request.json
                
                # Get combat from session
                combat = get_combat_from_session(combat_id)
                
                if not combat:
                    return jsonify({
                        'success': False,
                        'error': 'Combat not found'
                    }), 404
                
                # Validate it's player's turn
                current_turn = combat.get_current_participant()
                if not current_turn or current_turn.participant_type.value != 'character':
                    return jsonify({
                        'success': False,
                        'error': 'Not a player turn'
                    }), 400
                
                # Get action parameters
                character_id = data.get('character_id')
                action_type = data.get('action_type')  # 'attack', 'skill', 'defend', 'item'
                action_name = data.get('action_name')
                target_id = data.get('target_id')
                action_data = data.get('action_data', {})
                
                # Validate character matches current turn
                if character_id != current_turn.participant_id:
                    return jsonify({
                        'success': False,
                        'error': 'Action character does not match current turn'
                    }), 400
                
                # Get character and target
                character = combat.get_participant_by_id(character_id)
                target = combat.get_participant_by_id(target_id) if target_id else None
                
                if not character:
                    return jsonify({
                        'success': False,
                        'error': f'Character {character_id} not found'
                    }), 400
                
                # Resolve action based on type
                result = None
                
                if action_type == 'attack':
                    if not target:
                        return jsonify({
                            'success': False,
                            'error': 'No target specified for attack'
                        }), 400
                    
                    result = resolve_attack(character, target)
                
                elif action_type == 'defend':
                    result = resolve_defend(character)
                
                elif action_type == 'skill':
                    # Some skills don't need targets (Rage, Wild Shape)
                    if not target and action_name not in ['Rage', 'Wild Shape', 'Reckless Attack']:
                        return jsonify({
                            'success': False,
                            'error': 'No target specified for skill'
                        }), 400
                    
                    result = resolve_skill(character, action_name, target, action_data)
                
                elif action_type == 'item':
                    return jsonify({
                        'success': False,
                        'error': 'Item usage not yet implemented'
                    }), 400
                
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Unknown action type: {action_type}'
                    }), 400
                
                # Check if action failed
                if not result.get('success'):
                    return jsonify(result), 400
                
                # Log the action
                combat._log(result.get('message', 'Action performed'))
                
                # Save combat state back to session
                save_combat_to_session(combat_id, combat)
                
                return jsonify(result)
                
            except Exception as e:
                print(f"[API] Error processing player action: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @app.route('/api/combat/<combat_id>/enemy-action', methods=['POST'])
        def process_enemy_action(combat_id):
            """AI decides and executes enemy action"""
            try:
                data = request.json
                
                # Get combat from session
                combat = get_combat_from_session(combat_id)
                
                if not combat:
                    return jsonify({
                        'success': False,
                        'error': 'Combat not found'
                    }), 404
                
                # Validate it's enemy turn
                current_turn = combat.get_current_participant()
                if not current_turn or current_turn.participant_type.value != 'monster':
                    return jsonify({
                        'success': False,
                        'error': 'Not an enemy turn'
                    }), 400
                
                enemy_id = data.get('enemy_id', current_turn.participant_id)
                
                # Get enemy
                enemy = combat.get_participant_by_id(enemy_id)
                
                if not enemy:
                    return jsonify({
                        'success': False,
                        'error': f'Enemy {enemy_id} not found'
                    }), 400
                
                # Choose target - attack lowest HP player
                available_targets = [
                    p for p in combat.participants
                    if p.participant_type.value == 'character' and p.is_alive()
                ]
                
                if not available_targets:
                    return jsonify({
                        'success': False,
                        'error': 'No valid targets available'
                    }), 400
                
                # Target lowest HP percentage
                target = min(
                    available_targets,
                    key=lambda p: p.get_current_hp() / max(p.get_max_hp(), 1)
                )
                
                # Resolve attack
                result = resolve_attack(enemy, target)
                
                # Log the action
                combat._log(result.get('message', 'Enemy action performed'))
                
                # Save combat state
                save_combat_to_session(combat_id, combat)
                
                return jsonify(result)
                
            except Exception as e:
                print(f"[API] Error processing enemy action: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @app.route('/api/combat/<combat_id>/advance-turn', methods=['POST'])
        def advance_turn(combat_id):
            """Move to next turn in initiative order"""
            try:
                # Get combat from session
                combat = get_combat_from_session(combat_id)
                
                if not combat:
                    return jsonify({
                        'success': False,
                        'error': 'Combat not found'
                    }), 404
                
                # Store current round
                old_round = combat.current_round
                
                # Advance turn index
                combat.current_turn_index += 1
                
                # Check if we need to start a new round
                new_round = False
                if combat.current_turn_index >= len(combat.initiative_order):
                    combat.current_turn_index = 0
                    combat.current_round += 1
                    combat.total_rounds = combat.current_round
                    new_round = True
                    combat._log(f"--- Round {combat.current_round} ---")
                
                # Skip dead participants
                max_attempts = len(combat.initiative_order)
                attempts = 0
                while attempts < max_attempts:
                    current = combat.get_current_participant()
                    if current and current.is_alive():
                        break
                    
                    # Skip this dead participant
                    combat.current_turn_index += 1
                    if combat.current_turn_index >= len(combat.initiative_order):
                        combat.current_turn_index = 0
                        combat.current_round += 1
                        new_round = True
                    
                    attempts += 1
                
                # Start the new turn
                current_participant = combat.get_current_participant()
                
                if current_participant:
                    # Handle start-of-turn effects
                    if hasattr(current_participant.entity, 'on_turn_start'):
                        current_participant.entity.on_turn_start()
                    
                    combat._log(f"{current_participant.name}'s turn")
                
                # Save combat state
                save_combat_to_session(combat_id, combat)
                
                # Build response
                return jsonify({
                    'success': True,
                    'new_round': new_round,
                    'round': combat.current_round,
                    'current_turn': {
                        'participant_id': current_participant.participant_id if current_participant else None,
                        'name': current_participant.name if current_participant else None,
                        'type': current_participant.participant_type.value if current_participant else None
                    }
                })
                
            except Exception as e:
                print(f"[API] Error advancing turn: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @app.route('/api/combat/<combat_id>/end', methods=['POST'])
        def end_combat(combat_id):
            """Mark combat as complete"""
            try:
                data = request.json
                result = data.get('result', 'unknown')  # 'victory', 'defeat', 'flee'
                
                # Get combat from session
                combat = get_combat_from_session(combat_id)
                
                if not combat:
                    return jsonify({
                        'success': False,
                        'error': 'Combat not found'
                    }), 404
                
                # Mark combat as ended
                from component.GameState.combat_state import CombatPhase
                combat.combat_phase = CombatPhase.ENDED
                
                # Store result in metadata
                if not hasattr(combat, 'metadata'):
                    combat.metadata = {}
                
                combat.metadata['result'] = result
                combat.metadata['total_rounds'] = combat.current_round
                
                # Calculate rewards for victory
                if result == 'victory':
                    xp_gained = sum(
                        getattr(p.entity, 'xp', 0)
                        for p in combat.participants
                        if p.participant_type.value == 'monster' and not p.is_alive()
                    )
                    combat.metadata['xp_gained'] = xp_gained
                    
                    # Log victory
                    combat._log(f"Combat ended in VICTORY! XP gained: {xp_gained}")
                elif result == 'defeat':
                    combat._log("Combat ended in DEFEAT!")
                elif result == 'flee':
                    combat._log("Party fled from combat!")
                
                # Save final state
                save_combat_to_session(combat_id, combat)
                
                return jsonify({
                    'success': True,
                    'result': result,
                    'rounds': combat.current_round,
                    'xp_gained': combat.metadata.get('xp_gained', 0) if result == 'victory' else 0
                })
                
            except Exception as e:
                print(f"[API] Error ending combat: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @app.route('/api/combat/<combat_id>/flee', methods=['POST'])
        def flee_combat(combat_id):
            """Attempt to flee (optional)"""
            try:
                # Get combat from session
                combat = get_combat_from_session(combat_id)
                
                if not combat:
                    return jsonify({
                        'success': False,
                        'error': 'Combat not found'
                    }), 404
                
                # In D&D 5e, fleeing requires a successful Dash action
                # For simplicity, we'll make it automatic for now
                # You could add a check here (e.g., party must succeed on group check)
                
                # Calculate flee chance (80% base for now)
                flee_roll = random.randint(1, 100)
                flee_success = flee_roll <= 80
                
                if flee_success:
                    combat._log("Party successfully fled from combat!")
                    
                    # Mark combat as ended via flee
                    from component.GameState.combat_state import CombatPhase
                    combat.combat_phase = CombatPhase.ENDED
                    
                    if not hasattr(combat, 'metadata'):
                        combat.metadata = {}
                    combat.metadata['result'] = 'fled'
                    
                    save_combat_to_session(combat_id, combat)
                    
                    return jsonify({
                        'success': True,
                        'fled': True,
                        'message': 'Successfully fled from combat!'
                    })
                else:
                    combat._log("Party failed to flee!")
                    
                    save_combat_to_session(combat_id, combat)
                    
                    return jsonify({
                        'success': True,
                        'fled': False,
                        'message': 'Failed to flee! Enemies get attacks of opportunity.'
                    })
                
            except Exception as e:
                print(f"[API] Error fleeing: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        # ========================================================================
        # HELPER FUNCTIONS
        # ========================================================================

        
        
        def resolve_attack(attacker, target) -> dict:
            """Resolve a basic attack action"""
            # Calculate attack roll (1d20 + modifiers)
            attack_roll = random.randint(1, 20)
            attack_bonus = get_attack_bonus(attacker)
            total_attack = attack_roll + attack_bonus
            
            # Get target's AC
            target_ac = target.get_ac()
            
            # Check for critical hit/miss
            is_critical = attack_roll == 20
            is_miss = attack_roll == 1 or (total_attack < target_ac and not is_critical)
            
            if is_miss:
                return {
                    'success': True,
                    'hit': False,
                    'message': f"{attacker.name} attacks {target.name} but misses! (Rolled {attack_roll}+{attack_bonus}={total_attack} vs AC {target_ac})",
                    'type': 'attack',
                    'attacker': attacker.name,
                    'target': target.name,
                    'damage': 0,
                    'new_hp': target.get_current_hp(),
                    'max_hp': target.get_max_hp(),
                    'target_defeated': False,
                    'attack_roll': attack_roll,
                    'attack_bonus': attack_bonus,
                    'total_attack': total_attack,
                    'target_ac': target_ac
                }
            
            # Calculate damage
            damage = calculate_damage(attacker, is_critical)
            
            # Apply damage
            new_hp = max(0, target.entity.hp - damage)
            target.entity.hp = new_hp
            
            target_defeated = new_hp <= 0
            crit_text = " CRITICAL HIT!" if is_critical else ""
            
            return {
                'success': True,
                'hit': True,
                'critical': is_critical,
                'message': f"{attacker.name} attacks {target.name} for {damage} damage!{crit_text}",
                'type': 'attack',
                'attacker': attacker.name,
                'target': target.name,
                'damage': damage,
                'new_hp': new_hp,
                'max_hp': target.get_max_hp(),
                'target_defeated': target_defeated,
                'attack_roll': attack_roll,
                'attack_bonus': attack_bonus,
                'total_attack': total_attack,
                'target_ac': target_ac
            }
        
        def resolve_defend(character) -> dict:
            """Resolve a defend action"""
            return {
                'success': True,
                'message': f"{character.name} takes a defensive stance! (+2 AC until next turn)",
                'type': 'defend',
                'character': character.name,
                'effect': 'defending'
            }
        
        def resolve_skill(character, skill_name, target, skill_data) -> dict:
            """Resolve a character skill/ability"""
            entity = character.entity
            char_class = getattr(entity, 'char_class', None)
            
            # Route to class-specific handlers
            if char_class == 'Barbarian':
                return resolve_barbarian_skill(character, skill_name, target, skill_data)
            elif char_class == 'Bard':
                return resolve_bard_skill(character, skill_name, target, skill_data)
            elif char_class == 'Cleric':
                return resolve_cleric_skill(character, skill_name, target, skill_data)
            elif char_class == 'Druid':
                return resolve_druid_skill(character, skill_name, target, skill_data)
            else:
                return {
                    'success': False,
                    'error': f'Unknown character class: {char_class}'
                }
        
        def resolve_barbarian_skill(character, skill_name, target, skill_data):
            """Resolve Barbarian abilities"""
            barbarian = character.entity
            
            if skill_name == 'Rage':
                if barbarian.enter_rage():
                    return {
                        'success': True,
                        'message': f"{character.name} enters a RAGE! 🔥 (+{barbarian.rage_damage} damage, resistance)",
                        'type': 'buff',
                        'character': character.name,
                        'effect': 'rage',
                        'resource_changes': {
                            'rages_remaining': barbarian.rages_per_day - barbarian.rages_used,
                            'currently_raging': True
                        }
                    }
                else:
                    return {'success': False, 'error': 'No rage uses remaining!'}
            
            elif skill_name == 'Reckless Attack':
                return {
                    'success': True,
                    'message': f"{character.name} attacks recklessly! (Advantage on attacks, enemies have advantage)",
                    'type': 'buff',
                    'character': character.name,
                    'effect': 'reckless'
                }
            
            return {'success': False, 'error': f'Unknown Barbarian skill: {skill_name}'}
        
        def resolve_bard_skill(character, skill_name, target, skill_data):
            """Resolve Bard abilities"""
            bard = character.entity
            
            if skill_name == 'Bardic Inspiration':
                if bard.use_bardic_inspiration():
                    return {
                        'success': True,
                        'message': f"{character.name} grants Bardic Inspiration to {target.name}! ({bard.bardic_inspiration_die})",
                        'type': 'buff',
                        'character': character.name,
                        'target': target.name,
                        'effect': 'inspiration',
                        'resource_changes': {
                            'bardic_inspiration_remaining': bard.bardic_inspiration_remaining
                        }
                    }
                else:
                    return {'success': False, 'error': 'No Bardic Inspiration uses remaining!'}
            
            elif skill_name.startswith('Spell:'):
                return resolve_spell(bard, character, skill_name, target, skill_data)
            
            return {'success': False, 'error': f'Unknown Bard skill: {skill_name}'}
        
        def resolve_cleric_skill(character, skill_name, target, skill_data):
            """Resolve Cleric abilities"""
            cleric = character.entity
            
            if skill_name == 'Channel Divinity: Turn Undead':
                max_uses = 1 if cleric.level < 6 else (2 if cleric.level < 18 else 3)
                if cleric.channel_divinity_used < max_uses:
                    cleric.channel_divinity_used += 1
                    return {
                        'success': True,
                        'message': f"{character.name} channels divinity to turn undead!",
                        'type': 'effect',
                        'character': character.name,
                        'effect': 'turn_undead',
                        'resource_changes': {
                            'channel_divinity_remaining': max_uses - cleric.channel_divinity_used
                        }
                    }
                else:
                    return {'success': False, 'error': 'No Channel Divinity uses remaining!'}
            
            elif skill_name.startswith('Spell:'):
                return resolve_spell(cleric, character, skill_name, target, skill_data)
            
            return {'success': False, 'error': f'Unknown Cleric skill: {skill_name}'}
        
        def resolve_druid_skill(character, skill_name, target, skill_data):
            """Resolve Druid abilities"""
            druid = character.entity
            
            if skill_name == 'Wild Shape':
                beast_name = skill_data.get('beast_name', 'Wolf')
                beast_hp = skill_data.get('beast_hp', 15)
                
                if druid.enter_wild_shape(beast_name, beast_hp):
                    return {
                        'success': True,
                        'message': f"{character.name} transforms into a {beast_name}!",
                        'type': 'transform',
                        'character': character.name,
                        'effect': 'wild_shape',
                        'resource_changes': {
                            'wild_shape_remaining': druid.wild_shape_uses_remaining,
                            'beast_name': beast_name,
                            'beast_hp': beast_hp
                        }
                    }
                else:
                    return {'success': False, 'error': 'No Wild Shape uses remaining!'}
            
            elif skill_name.startswith('Spell:'):
                return resolve_spell(druid, character, skill_name, target, skill_data)
            
            return {'success': False, 'error': f'Unknown Druid skill: {skill_name}'}
        
        def resolve_spell(caster_entity, character, skill_name, target, skill_data):
            """Resolve spell casting"""
            spell_name = skill_name.replace('Spell:', '').strip()
            spell_level = skill_data.get('level', 1)
            
            # Check spell slots
            used = caster_entity.spell_slots_used.get(spell_level, 0)
            max_slots = caster_entity.spell_slots.get(spell_level, 0)
            
            if used >= max_slots:
                return {'success': False, 'error': f'No level {spell_level} spell slots remaining!'}
            
            # Use spell slot
            caster_entity.spell_slots_used[spell_level] = used + 1
            
            # Determine spell type
            is_healing = any(word in spell_name.lower() for word in ['heal', 'cure', 'restore'])
            
            if is_healing:
                # Healing spell
                healing = random.randint(1, 8) * spell_level + get_spell_modifier(caster_entity)
                
                # Cleric life domain bonus
                if hasattr(caster_entity, 'disciple_of_life') and caster_entity.disciple_of_life:
                    healing += 2 + spell_level
                
                target.entity.hp = min(target.entity.hp + healing, target.get_max_hp())
                
                return {
                    'success': True,
                    'message': f"{character.name} casts {spell_name} on {target.name}, healing {healing} HP!",
                    'type': 'healing',
                    'character': character.name,
                    'target': target.name,
                    'healing': healing,
                    'new_hp': target.entity.hp,
                    'max_hp': target.get_max_hp(),
                    'resource_changes': {
                        'spell_slots_used': caster_entity.spell_slots_used
                    }
                }
            else:
                # Damage spell
                damage = random.randint(2, 8) * spell_level
                target.entity.hp = max(0, target.entity.hp - damage)
                
                return {
                    'success': True,
                    'message': f"{character.name} casts {spell_name} on {target.name} for {damage} damage!",
                    'type': 'damage',
                    'character': character.name,
                    'target': target.name,
                    'damage': damage,
                    'new_hp': target.entity.hp,
                    'max_hp': target.get_max_hp(),
                    'target_defeated': target.entity.hp <= 0,
                    'resource_changes': {
                        'spell_slots_used': caster_entity.spell_slots_used
                    }
                }
        
        def get_attack_bonus(participant) -> int:
            """Calculate attack bonus"""
            entity = participant.entity
            
            if hasattr(entity, 'stats') and isinstance(entity.stats, dict):
                str_score = entity.stats.get('strength', 10)
                str_mod = (str_score - 10) // 2
                prof_bonus = get_proficiency_bonus(getattr(entity, 'level', 1))
                return str_mod + prof_bonus
            
            return 2  # Default
        
        def get_proficiency_bonus(level: int) -> int:
            """Get proficiency bonus by level"""
            if level < 5:
                return 2
            elif level < 9:
                return 3
            elif level < 13:
                return 4
            elif level < 17:
                return 5
            else:
                return 6
        
        def get_spell_modifier(entity) -> int:
            """Get spellcasting modifier"""
            if hasattr(entity, 'stats') and isinstance(entity.stats, dict):
                # Use wisdom for clerics/druids, charisma for bards
                stat = 'wisdom' if getattr(entity, 'char_class') in ['Cleric', 'Druid'] else 'charisma'
                score = entity.stats.get(stat, 10)
                return (score - 10) // 2
            return 0
        
        def calculate_damage(attacker, is_critical: bool = False) -> int:
            """Calculate attack damage"""
            entity = attacker.entity
            
            # Base damage (1d8 weapon)
            base_dice = 1 if not is_critical else 2
            damage = sum(random.randint(1, 8) for _ in range(base_dice))
            
            # Add STR modifier
            if hasattr(entity, 'stats') and isinstance(entity.stats, dict):
                str_score = entity.stats.get('strength', 10)
                str_mod = (str_score - 10) // 2
                damage += str_mod
            
            # Add rage damage if raging
            if hasattr(entity, 'currently_raging') and entity.currently_raging:
                damage += entity.rage_damage
            
            return max(1, damage)
        
        def get_combat_from_session(combat_id: str):
            """Load combat from session"""
            session_key = f'combat_{combat_id}'
            
            if session_key not in session:
                return None
            
            return session[session_key]
        
        def save_combat_to_session(combat_id: str, combat):
            """Save combat to session"""
            session_key = f'combat_{combat_id}'
            session[session_key] = combat
            session.modified = True
        
        print("[Combat API] Routes registered successfully")

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