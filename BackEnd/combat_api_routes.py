#!/usr/bin/env python3
"""
Combat API Routes
Flask endpoints for JRPG combat system
"""

from flask import url_for, jsonify, request, session
from typing import Dict, Optional
import json
import random

from component.GameState.combat_state import CombatState, CombatParticipant
from component.GameState.combat_ai import CombatAI, CombatActionResolver
from component.campaign_manager import CampaignManager
from phase_3 import load_story_package_data, save_story_package_data


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
    
    @app.route('/api/combat/<combat_id>/summary', methods=['GET'])
    def get_combat_summary(combat_id):
        """Get current combat state"""

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
                'initiative_order': [{'id': pid, 'initiative': init} for pid, init in combat.initiative_order],
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
            data = request.json or {}
            
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

            print(f"[Combat API] Processing enemy action for: {enemy_id}")
            
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
            summary = combat.get_combat_summary()

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
                },
                'combat_state': summary
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
    # POST COMBAT
    # ========================================================================
    @app.route('/campaign/<campaign_name>/combat-state/complete', methods=['POST'])
    def combat_state_complete(campaign_name):
        """Complete combat and advance story package tracker"""
        try:
            data = request.json
            result = data.get('result', 'victory')  # 'victory', 'defeat', 'fled'
            
            campaign, tracker, story_state, flow = load_story_package_data(campaign_name)
            
            # Store combat result in story_state
            combat_summary = {
                'result': result,
                'rounds': data.get('rounds', 0),
                'xp_gained': data.get('xp_gained', 0) if result == 'victory' else 0
            }
            
            story_state.last_combat_result = combat_summary
            
            # Add story event
            story_state.add_story_event(
                event_type="combat_complete",
                narrative_text=f"Combat ended in {result}",
                metadata=combat_summary
            )
            
            # Clear pending monster
            story_state.pending_monster = None
            
            # Clear session combat
            combat_id = session.get('current_combat_id')
            if combat_id:
                session_key = f'combat_{combat_id}'
                session.pop(session_key, None)
                session.pop('current_combat_id', None)
            
            # Advance tracker to next step
            tracker.advance_step()
            
            # Save everything
            save_story_package_data(campaign_name, tracker, story_state)
            
            return jsonify({
                'success': True,
                'result': result,
                'next_step': tracker.current_step,
                'redirect': url_for('story_package_hub', campaign_name=campaign_name)
            })
            
        except Exception as e:
            print(f"Error completing combat: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================

    
    
    def resolve_attack(attacker, target) -> dict:
        """Resolve a basic attack action"""
        import random
        
        print(f"[Combat] Resolving attack: {attacker.name} -> {target.name}")
        
        # Calculate attack roll (1d20 + modifiers)
        attack_roll = random.randint(1, 20)
        attack_bonus = get_attack_bonus(attacker)
        total_attack = attack_roll + attack_bonus
        
        # Get target's AC
        target_ac = target.get_ac()
        
        # Check for critical hit/miss
        is_critical = attack_roll == 20
        is_miss = attack_roll == 1 or (total_attack < target_ac and not is_critical)
        
        print(f"[Combat] Attack roll: {attack_roll} + {attack_bonus} = {total_attack} vs AC {target_ac}")
        
        if is_miss:
            return {
                'success': True,
                'hit': False,
                'message': f"{attacker.name} attacks {target.name} but misses! (Rolled {attack_roll}+{attack_bonus}={total_attack} vs AC {target_ac})",
                'type': 'attack',
                'attacker': attacker.name,
                'target': target.participant_id,  # Use participant_id instead of name
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
        
        print(f"[Combat] Damage dealt: {damage}, new HP: {new_hp}/{target.get_max_hp()}")
        
        return {
            'success': True,
            'hit': True,
            'critical': is_critical,
            'message': f"{attacker.name} attacks {target.name} for {damage} damage!{crit_text}",
            'type': 'attack',
            'attacker': attacker.name,
            'target': target.participant_id, 
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
                    'target': target.participant_id,
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
                'target': target.participant_id,
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
                'target': target.participant_id,
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
        """Load combat from session with deserialization"""
        session_key = f'combat_{combat_id}'
        
        if session_key not in session:
            return None
        
        try:
            combat_str = session[session_key]
            return deserialize_combat(combat_str)
        except Exception as e:
            print(f"[Combat API] Error deserializing combat: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def save_combat_to_session(combat_id: str, combat):
        """Save combat to session with serialization"""
        session_key = f'combat_{combat_id}'
        
        try:
            combat_str = serialize_combat(combat)
            session[session_key] = combat_str
            session.modified = True
        except Exception as e:
            print(f"[Combat API] Error serializing combat: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    print("[Combat API] Routes registered successfully")


