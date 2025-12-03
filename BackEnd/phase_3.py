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
    if 'story_package_tracker' in campaign_dict:
        tracker = StoryPackageTracker.from_dict(campaign_dict['story_package_tracker'])
    else:
        # First time - initialize at package 1, step 1
        tracker = StoryPackageTracker(campaign_name=campaign_name)
        tracker.current_package = 1
        tracker.current_step = 1
        tracker.completed_steps[1] = []
    
    # Load or initialize story_state
    if 'story_state' in campaign_dict:
        story_state = StoryState.from_dict(campaign_dict['story_state'])
    else:
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


def build_story_context(campaign_name: str) -> Dict:
    """
    Build complete context for AI prompts.
    
    Returns:
        {
            'characters': list,
            'campaign': dict,
            'preparations': str,
            'session_notes': str
        }
    """
    manager = CampaignManager()
    context = manager.get_campaign_context(campaign_name)
    
    # Load preparations markdown if it exists
    prep_path = Path(__file__).parent.parent / "campaigns" / campaign_name / "preparations.md"
    preparations = ""
    if prep_path.exists():
        with open(prep_path, 'r') as f:
            preparations = f.read()
    
    # Build character summaries
    characters = []
    for char in context.get('characters', []):
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
            'name': context['campaign'].name,
            'description': context['campaign'].description,
            'session_number': context['campaign'].session_number
        },
        'preparations': preparations,
        'session_notes': context.get('session_notes', '')
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


def extract_monster_info_from_response(ai_response: str) -> Optional[Dict]:
    """
    Parse AI response for monster information.
    
    Returns monster data dict if found, None otherwise.
    """
    # Look for patterns like "3 goblins" or "1 dragon"
    import re
    pattern = r'(\d+)\s+([a-zA-Z\s]+?)(?:s|es)?\s*(?:appear|attack|emerge)'
    matches = re.findall(pattern, ai_response.lower())
    
    if matches:
        count, monster_name = matches[0]
        return {
            'count': int(count),
            'name': monster_name.strip(),
            'description': ai_response[:200]
        }
    
    return None


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
            
            # Route to appropriate page
            if state_type == 'story':
                return redirect(url_for('story_state_page', campaign_name=campaign_name))
            elif state_type == 'question':
                return redirect(url_for('question_state_page', campaign_name=campaign_name))
            elif state_type == 'dice':
                return redirect(url_for('dice_state_page', campaign_name=campaign_name))
            elif state_type == 'combat':
                return redirect(url_for('combat_state_page', campaign_name=campaign_name))
            else:
                return f"Invalid state type: {state_type}", 500
                
        except Exception as e:
            print(f"Error in story_package_hub: {e}")
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
                'step_definition': step_definition,
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
                    return jsonify({'error': 'No dice result found for conditional'}), 400
                
                # Route based on dice outcome
                success = last_dice_result.get('success', False)
                new_step = flow.evaluate_and_route_conditional(success)
                
                # Update tracker
                tracker.current_step = new_step
                
                # Clear cached content for new step
                session.pop(f"step_{current_step}_content", None)
                
            else:
                # Normal advancement
                tracker.advance_step()
                
                # Clear cached content
                session.pop(f"step_{current_step}_content", None)
            
            # Save everything
            save_story_package_data(campaign_name, tracker, story_state)
            
            # Redirect back to hub (which will route to next state)
            return redirect(url_for('story_package_hub', campaign_name=campaign_name))
            
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
                monster_info = extract_monster_info_from_response(ai_response)
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
            
            return render_template('HTML/questioning_state.html', **context_data)
            
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
                decision_type='question',
                decision=answer,
                context=story_state.pending_question
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
            
            context_data = {
                'campaign_name': campaign_name,
                'tracker': tracker.to_dict(),
                'story_state': story_state.to_dict(),
                'dice_situation': dice_situation,
                'character': asdict(character) if character else {},
                'roll_type': 'normal',
                'dc': dice_situation.get('dc', 15),
                'stat': dice_situation.get('stat', 'strength'),
                'skill': dice_situation.get('skill', None)
            }
            
            return render_template('HTML/dice_roll_state.html', **context_data)
            
        except Exception as e:
            print(f"Error in dice_state_page: {e}")
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
                'breakdown': result.get_roll_breakdown()
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
            
            # Get active combat from session
            combat_data = session.get('active_combat', None)
            
            if not combat_data:
                # Need to initialize combat first
                return redirect(url_for('combat_state_init', campaign_name=campaign_name))
            
            context_data = {
                'campaign_name': campaign_name,
                'tracker': tracker.to_dict(),
                'story_state': story_state.to_dict(),
                'combat_state': combat_data,
                'monsters': combat_data.get('monsters', []),
                'characters': combat_data.get('characters', []),
                'initiative_order': combat_data.get('initiative_order', [])
            }
            
            return render_template('HTML/combat_state.html', **context_data)
            
        except Exception as e:
            print(f"Error in combat_state_page: {e}")
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
            
            # Create combat using DM description method
            dm_description = f"You encounter {monster_info['count']} {monster_info['name']}"
            
            combat_state = CombatState.from_dm_description(
                dm_text=dm_description,
                characters=characters,
                dice_state=None
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