#!/usr/bin/env python3
"""
Combat API Routes
Flask endpoints for JRPG combat system
"""

from flask import jsonify, request, session
from typing import Dict, Optional
import json

from component.GameState.combat_state import CombatState, CombatParticipant
from component.GameState.combat_ai import CombatAI, CombatActionResolver
from component.campaign_manager import CampaignManager

import pickle
import base64

def serialize_combat(combat) -> str:
    """Serialize combat state to string for session storage"""
    try:
        pickled = pickle.dumps(combat)
        return base64.b64encode(pickled).decode('utf-8')
    except Exception as e:
        print(f"Error serializing combat: {e}")
        raise

def deserialize_combat(combat_str: str):
    """Deserialize combat state from session string"""
    try:
        pickled = base64.b64decode(combat_str.encode('utf-8'))
        return pickle.loads(pickled)
    except Exception as e:
        print(f"Error deserializing combat: {e}")
        raise


def register_combat_routes(app):
    """Register all combat-related API routes"""
    
    # ========================================================================
    # COMBAT STATE MANAGEMENT
    # ========================================================================
    
    @app.route('/api/combat/<combat_id>/summary', methods=['GET'])
    def get_combat_summary(combat_id):
        """
        Get current combat state summary
        
        Returns:
            JSON with combat state including:
            - participants (characters and monsters)
            - initiative order
            - current turn
            - round number
            - combat log
        """
        try:
            # Get combat from session with deserialization
            session_key = f'combat_{combat_id}'
            
            if session_key not in session:
                return jsonify({
                    'success': False,
                    'error': 'Combat not found in session'
                }), 404
            
            # Deserialize combat state
            try:
                combat = deserialize_combat(session[session_key])
            except Exception as e:
                print(f"[API] Error deserializing combat: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': f'Combat deserialization failed: {str(e)}'
                }), 500
            
            # Get summary
            summary = combat.get_combat_summary()
            
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
    
    # ========================================================================
    # PLAYER ACTIONS
    # ========================================================================
    
    @app.route('/api/combat/<combat_id>/player-action', methods=['POST'])
    def process_player_action(combat_id):
        """
        Process a player's combat action
        
        Expected JSON:
        {
            "character_id": "char_fighter",
            "action_type": "attack" | "skill" | "defend" | "item",
            "action_name": "Attack" | "Rage" | etc.,
            "target_id": "mon_goblin_1" (optional),
            "action_data": {} (optional)
        }
        
        Returns:
            JSON with action result
        """
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
            action_type = data.get('action_type')
            action_name = data.get('action_name')
            target_id = data.get('target_id')
            action_data = data.get('action_data', {})
            
            # Get character and target
            character = combat.get_participant_by_id(character_id)
            target = combat.get_participant_by_id(target_id) if target_id else None
            
            if not character:
                return jsonify({
                    'success': False,
                    'error': f'Character {character_id} not found'
                }), 400
            
            # Resolve action
            result = resolve_action(
                combat,
                character,
                action_type,
                action_name,
                target,
                action_data
            )
            
            if not result.get('success'):
                return jsonify(result), 400
            
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
    
    # ========================================================================
    # ENEMY ACTIONS (AI)
    # ========================================================================
    
    @app.route('/api/combat/<combat_id>/enemy-action', methods=['POST'])
    def process_enemy_action(combat_id):
        """
        AI chooses and executes enemy action
        
        Expected JSON:
        {
            "enemy_id": "mon_goblin_1"
        }
        
        Returns:
            JSON with action result
        """
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
            
            enemy_id = data.get('enemy_id')
            
            # Get AI to choose action
            ai = CombatAI(combat)
            action = ai.choose_action(enemy_id)
            
            # Get enemy and target
            enemy = combat.get_participant_by_id(enemy_id)
            target = combat.get_participant_by_id(action.target_id)
            
            if not enemy or not target:
                return jsonify({
                    'success': False,
                    'error': 'Enemy or target not found'
                }), 400
            
            # Resolve action
            result = CombatActionResolver.resolve_attack(enemy, target, action.data)
            
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
    
    # ========================================================================
    # TURN MANAGEMENT
    # ========================================================================
    
    @app.route('/api/combat/<combat_id>/advance-turn', methods=['POST'])
    def advance_turn(combat_id):
        """
        Advance to next turn in initiative order
        
        Returns:
            JSON with updated combat state
        """
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
            
            # Advance turn
            combat.current_turn_index += 1
            
            # Check if new round
            if combat.current_turn_index >= len(combat.initiative_order):
                combat.current_turn_index = 0
                combat.current_round += 1
                combat.total_rounds = combat.current_round
                new_round = True
            else:
                new_round = False
            
            # Start new turn
            combat.start_turn()
            
            # Save combat state
            save_combat_to_session(combat_id, combat)
            
            # Get updated summary
            summary = combat.get_combat_summary()
            
            return jsonify({
                'success': True,
                'combat_state': summary,
                'new_round': new_round,
                'round': combat.current_round
            })
            
        except Exception as e:
            print(f"[API] Error advancing turn: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ========================================================================
    # COMBAT END
    # ========================================================================
    
    @app.route('/api/combat/<combat_id>/end', methods=['POST'])
    def end_combat(combat_id):
        """
        Mark combat as ended
        
        Expected JSON:
        {
            "result": "victory" | "defeat" | "flee"
        }
        """
        try:
            data = request.json
            result = data.get('result', 'unknown')
            
            # Get combat from session
            combat = get_combat_from_session(combat_id)
            
            if not combat:
                return jsonify({
                    'success': False,
                    'error': 'Combat not found'
                }), 404
            
            # Mark combat as ended
            combat.combat_phase = combat.combat_phase.__class__.ENDED
            combat.end_time = combat.start_time  # Would use datetime
            
            # Store result in metadata
            combat.metadata['result'] = result
            combat.metadata['total_rounds'] = combat.current_round
            
            # Save final state
            save_combat_to_session(combat_id, combat)
            
            # Log
            combat._log(f"Combat ended: {result}")
            
            return jsonify({
                'success': True,
                'result': result,
                'rounds': combat.current_round
            })
            
        except Exception as e:
            print(f"[API] Error ending combat: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ========================================================================
    # FLEE
    # ========================================================================
    
    @app.route('/api/combat/<combat_id>/flee', methods=['POST'])
    def flee_combat(combat_id):
        """
        Attempt to flee from combat
        
        Returns:
            JSON with flee result
        """
        try:
            # Get combat from session
            combat = get_combat_from_session(combat_id)
            
            if not combat:
                return jsonify({
                    'success': False,
                    'error': 'Combat not found'
                }), 404
            
            # Simple flee (always succeeds for now)
            # In full D&D rules, would require checks
            
            combat._log("Party fled from combat!")
            
            # End combat
            combat.combat_phase = combat.combat_phase.__class__.ENDED
            combat.metadata['result'] = 'fled'
            
            save_combat_to_session(combat_id, combat)
            
            return jsonify({
                'success': True,
                'message': 'Successfully fled from combat'
            })
            
        except Exception as e:
            print(f"[API] Error fleeing: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================
    
    def resolve_action(combat, character, action_type, action_name, target, action_data):
        """
        Route action to appropriate resolver
        """
        if action_type == 'attack':
            if not target:
                return {'success': False, 'error': 'No target selected'}
            return CombatActionResolver.resolve_attack(character, target, action_data)
        
        elif action_type == 'defend':
            return CombatActionResolver.resolve_defend(character)
        
        elif action_type == 'skill':
            if not target:
                # Some skills don't need a target (Rage, Wild Shape)
                target = character
            return CombatActionResolver.resolve_skill(character, action_name, target, action_data)
        
        elif action_type == 'item':
            # TODO: Implement item usage
            return {
                'success': False,
                'error': 'Item usage not yet implemented'
            }
        
        else:
            return {
                'success': False,
                'error': f'Unknown action type: {action_type}'
            }
    
    def get_combat_from_session(combat_id: str) -> Optional[CombatState]:
        """
        Load combat from session with deserialization
        """
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
        """
        Save combat to session with serialization
        """
        session_key = f'combat_{combat_id}'
        
        try:
            combat_str = serialize_combat(combat)
            session[session_key] = combat_str
            session.modified = True
        except Exception as e:
            print(f"Error saving combat to session: {e}")
            raise
    
    print("[Combat API] Routes registered")