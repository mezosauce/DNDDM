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

def initialize_character_resources(character):
    """Initialize resource tracking attributes for a character"""
    # Get character level
    level = getattr(character, 'level', 1)
    char_class = getattr(character, 'char_class', None)
    
    # Initialize spell slots based on class and level
    if char_class in ['Cleric', 'Druid', 'Bard']:
        if not hasattr(character, 'spell_slots_used'):
            character.spell_slots_used = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        
        if not hasattr(character, 'spell_slots'):
            # Basic spell slot table (simplified)
            spell_slots_by_level = {
                1: {1: 2},
                2: {1: 3},
                3: {1: 4, 2: 2},
                4: {1: 4, 2: 3},
                5: {1: 4, 2: 3, 3: 2}
                # Add more levels as needed
            }
            character.spell_slots = spell_slots_by_level.get(level, {1: 2})
    
    # Initialize class-specific resources
    if char_class == 'Barbarian':
        if not hasattr(character, 'rages_used'):
            character.rages_used = 0
        if not hasattr(character, 'currently_raging'):
            character.currently_raging = False
    
    elif char_class == 'Bard':
        if not hasattr(character, 'bardic_inspiration_remaining'):
            cha_mod = (character.stats.get('charisma', 10) - 10) // 2 if hasattr(character, 'stats') else 2
            character.bardic_inspiration_remaining = max(1, cha_mod)
        if not hasattr(character, 'bardic_inspiration_die'):
            character.bardic_inspiration_die = 'd6'
    
    elif char_class == 'Cleric':
        if not hasattr(character, 'channel_divinity_used'):
            character.channel_divinity_used = 0
    
    elif char_class == 'Druid':
        if not hasattr(character, 'wild_shape_uses_remaining'):
            character.wild_shape_uses_remaining = 2
        if not hasattr(character, 'currently_wild_shaped'):
            character.currently_wild_shaped = False
            
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


def get_spell_modifier(entity) -> int:
    """Get spellcasting modifier"""
    if hasattr(entity, 'stats') and isinstance(entity.stats, dict):
        # Use wisdom for clerics/druids, charisma for bards
        stat = 'wisdom' if getattr(entity, 'char_class') in ['Cleric', 'Druid'] else 'charisma'
        score = entity.stats.get(stat, 10)
        return (score - 10) // 2
    return 0


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
            
            
            # Build participant data
            
            participants = []
            for p in combat.participants:
                participant_data = {
                    'participant_id': p.participant_id,
                    'id': p.participant_id,
                    'name': p.name,
                    'type': p.participant_type.value,
                    'initiative': p.initiative_total,
                    'hp': p.get_current_hp(),
                    'max_hp': p.get_max_hp(),
                    'ac': p.get_ac(),
                    'is_alive': p.is_alive(),
                    'conditions': list(p.conditions) if hasattr(p, 'conditions') else []
                }
                
                # Add character-specific data
                if p.participant_type.value == 'character':
                    entity = p.entity
                    
                    # Extract class - try multiple attribute names
                    char_class = (getattr(entity, 'char_class', None) or 
                                getattr(entity, 'class', None) or 
                                getattr(entity, 'character_class', None))
                    
                    # Extract level
                    level = getattr(entity, 'level', 1)
                    
                    # Extract stats
                    stats = getattr(entity, 'stats', {})
                    if not isinstance(stats, dict):
                        # If stats is an object, try to convert it
                        stats = {
                            'strength': getattr(stats, 'strength', 10),
                            'dexterity': getattr(stats, 'dexterity', 10),
                            'constitution': getattr(stats, 'constitution', 10),
                            'intelligence': getattr(stats, 'intelligence', 10),
                            'wisdom': getattr(stats, 'wisdom', 10),
                            'charisma': getattr(stats, 'charisma', 10)
                        }
                    
                    participant_data['class'] = char_class
                    participant_data['char_class'] = char_class  # Compatibility
                    participant_data['level'] = level
                    participant_data['stats'] = stats
                    participant_data['race'] = getattr(entity, 'race', 'Unknown')
                    participant_data['background'] = getattr(entity, 'background', '')
                    
                    # Debug logging
                    print(f"[Combat API] Character {p.name}: class={char_class}, level={level}, stats={stats}")
                    
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
            
            initialize_character_resources(character.entity)
            
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
   
        elif action_type == 'skill' or action_type == 'spell':     
            if not target:
                # Some skills don't need a target (Rage, Wild Shape)
                target = character

            if action_type == 'spell':
                spell_level = action_data.get('spell_level', 1)
                # Generate spell name if not provided
                if not action_name or action_name.startswith('Cast Level'):
                    action_name = f'Spell:Level {spell_level}'
                elif not action_name.startswith('Spell:'):
                    action_name = f'Spell:{action_name}'
            
            return CombatActionResolver.resolve_skill(character, action_name, target, action_data) 
 
        else:
            return {
                'success': False,
                'error': f'Unknown action type: {action_type}'
            }
        
    def resolve_spell(caster_entity, character, skill_name, target, skill_data):
        """Resolve spell casting"""
        import random
        
        # Extract spell name and level
        spell_name = skill_name.replace('Spell:', '').strip()
        spell_level = skill_data.get('spell_level', 1)
        
        # Check spell slots
        if not hasattr(caster_entity, 'spell_slots_used'):
            caster_entity.spell_slots_used = {}
        if not hasattr(caster_entity, 'spell_slots'):
            caster_entity.spell_slots = {1: 2, 2: 0, 3: 0, 4: 0, 5: 0}
        
        used = caster_entity.spell_slots_used.get(spell_level, 0)
        max_slots = caster_entity.spell_slots.get(spell_level, 0)
        
        if used >= max_slots:
            return {'success': False, 'error': f'No level {spell_level} spell slots remaining!'}
        
        # Use spell slot
        caster_entity.spell_slots_used[spell_level] = used + 1
        
        # Determine spell type from skill_data or spell_name
        spell_type = skill_data.get('spell_type', 'damage')
        is_healing = spell_type == 'healing' or any(word in spell_name.lower() for word in ['heal', 'cure', 'restore'])
        
        if is_healing:
            # Healing spell
            healing = random.randint(1, 8) * spell_level + get_spell_modifier(caster_entity)
            
            # Cleric life domain bonus
            if hasattr(caster_entity, 'disciple_of_life') and caster_entity.disciple_of_life:
                healing += 2 + spell_level
            
            # Apply healing
            old_hp = target.entity.hp
            target.entity.hp = min(target.entity.hp + healing, target.get_max_hp())
            actual_healing = target.entity.hp - old_hp
            
            return {
                'success': True,
                'message': f"{character.name} casts {spell_name} (Level {spell_level}) on {target.name}, healing {actual_healing} HP!",
                'type': 'healing',
                'character': character.name,
                'target': target.participant_id or target.id,
                'healing': actual_healing,
                'new_hp': target.entity.hp,
                'max_hp': target.get_max_hp(),
                'resource_changes': {
                    'spell_slots_used': caster_entity.spell_slots_used
                }
            }
        else:
            # Damage spell
            # Base damage scales with spell level
            num_dice = spell_level
            damage = sum(random.randint(1, 8) for _ in range(num_dice))
            damage += get_spell_modifier(caster_entity)
            
            # Apply damage
            old_hp = target.entity.hp
            target.entity.hp = max(0, target.entity.hp - damage)
            actual_damage = old_hp - target.entity.hp
            
            return {
                'success': True,
                'message': f"{character.name} casts {spell_name} (Level {spell_level}) on {target.name} for {actual_damage} damage!",
                'type': 'damage',
                'character': character.name,
                'target': target.participant_id or target.id,
                'damage': actual_damage,
                'new_hp': target.entity.hp,
                'max_hp': target.get_max_hp(),
                'target_defeated': target.entity.hp <= 0,
                'resource_changes': {
                    'spell_slots_used': caster_entity.spell_slots_used
                }
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