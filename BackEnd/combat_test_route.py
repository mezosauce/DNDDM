#!/usr/bin/env python3
"""
Combat Testing Routes
Provides endpoints for testing combat initialization
"""

from flask import render_template, request, jsonify, session
from datetime import datetime
from pathlib import Path
import json
import uuid

# These will be imported when integrated
# from main import app
from component.GameState.combat_state import CombatState, CombatPhase
from component.Class.Character import Character
from component.Class.barbarian import Barbarian
from component.Class.bard import Bard
from component.Class.cleric import Cleric
from component.Class.druid import Druid
from component.Class.monsters.monster import Monster
from component.GameState.dice_state import DiceRollState


def register_combat_test_routes(app):
    """Register combat testing routes"""
    
    # Store active combat sessions in memory (use Redis/DB for production)
    active_combats = {}
    
    @app.route('/combat-test')
    def combat_test_page():
        """Combat testing interface"""
        return render_template('HTML/combat_test.html')
    
    
    @app.route('/api/combat/create', methods=['POST'])
    def create_combat():
        """Create a new combat encounter"""
        try:
            data = request.json
            
            encounter_name = data.get('encounter_name', 'Test Encounter')
            characters_data = data.get('characters', [])
            monsters_data = data.get('monsters', [])
            
            # Create characters
            characters = []
            for char_data in characters_data:
                # Determine class type
                class_type = char_data.get('char_class', 'Character')
                
                # Create appropriate character class
                if class_type == 'Barbarian':
                    char = Barbarian(
                        name=char_data['name'],
                        race=char_data.get('race', 'Human'),
                        char_class=class_type,
                        background=char_data.get('background', 'Soldier'),
                        level=char_data.get('level', 1),
                        stats=char_data.get('stats', {
                            'strength': 15, 'dexterity': 14, 'constitution': 14,
                            'intelligence': 10, 'wisdom': 12, 'charisma': 8
                        })
                    )
                elif class_type == 'Bard':
                    char = Bard(
                        name=char_data['name'],
                        race=char_data.get('race', 'Human'),
                        char_class=class_type,
                        background=char_data.get('background', 'Entertainer'),
                        level=char_data.get('level', 1),
                        stats=char_data.get('stats', {
                            'strength': 8, 'dexterity': 14, 'constitution': 12,
                            'intelligence': 10, 'wisdom': 13, 'charisma': 15
                        })
                    )
                elif class_type == 'Cleric':
                    char = Cleric(
                        name=char_data['name'],
                        race=char_data.get('race', 'Human'),
                        char_class=class_type,
                        background=char_data.get('background', 'Acolyte'),
                        level=char_data.get('level', 1),
                        stats=char_data.get('stats', {
                            'strength': 10, 'dexterity': 12, 'constitution': 14,
                            'intelligence': 11, 'wisdom': 16, 'charisma': 13
                        })
                    )
                elif class_type == 'Druid':
                    char = Druid(
                        name=char_data['name'],
                        race=char_data.get('race', 'Human'),
                        char_class=class_type,
                        background=char_data.get('background', 'Outlander'),
                        level=char_data.get('level', 1),
                        stats=char_data.get('stats', {
                            'strength': 10, 'dexterity': 13, 'constitution': 14,
                            'intelligence': 12, 'wisdom': 15, 'charisma': 8
                        })
                    )
                else:
                    char = Character(
                        name=char_data['name'],
                        race=char_data.get('race', 'Human'),
                        char_class=class_type,
                        background=char_data.get('background', 'Folk Hero'),
                        level=char_data.get('level', 1),
                        stats=char_data.get('stats', {
                            'strength': 12, 'dexterity': 12, 'constitution': 12,
                            'intelligence': 12, 'wisdom': 12, 'charisma': 12
                        })
                    )
                
                char.hp = char_data.get('hp', char.max_hp)
                char.ac = char_data.get('ac', 10)
                characters.append(char)
            
            # Create monsters
            monsters = []
            for monster_data in monsters_data:
                monster = Monster(
                    name=monster_data.get('name', 'Unknown'),
                    monster_type=monster_data.get('monster_type', 'Humanoid'),
                    size=monster_data.get('size', 'Medium'),
                    alignment=monster_data.get('alignment', 'Neutral'),
                    challenge_rating=monster_data.get('challenge_rating', 0.5),
                    hp=monster_data.get('hp', 10),
                    ac=monster_data.get('ac', 12),
                    stats=monster_data.get('stats', {
                        'strength': 10, 'dexterity': 10, 'constitution': 10,
                        'intelligence': 10, 'wisdom': 10, 'charisma': 10
                    }),
                    abilities=monster_data.get('abilities', []),
                    actions=monster_data.get('actions', [])
                )
                monsters.append(monster)
            
            # Create combat
            combat = CombatState(
                encounter_name=encounter_name,
                characters=characters,
                monsters=monsters
            )
            
            # Store in active combats
            active_combats[combat.combat_id] = combat
            
            return jsonify({
                'success': True,
                'combat_id': combat.combat_id,
                'encounter_name': combat.encounter_name,
                'phase': combat.combat_phase.value,
                'participants': len(combat.participants)
            })
            
        except Exception as e:
            print(f"Error creating combat: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 400
    
    
    @app.route('/api/combat/<combat_id>/roll-initiative', methods=['POST'])
    def roll_initiative(combat_id):
        """Roll initiative for all participants"""
        try:
            combat = active_combats.get(combat_id)
            if not combat:
                return jsonify({'error': 'Combat not found'}), 404
            
            results = combat.roll_initiative()
            
            return jsonify({
                'success': True,
                'phase': combat.combat_phase.value,
                'results': results
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    
    @app.route('/api/combat/<combat_id>/determine-order', methods=['POST'])
    def determine_order(combat_id):
        """Determine turn order"""
        try:
            combat = active_combats.get(combat_id)
            if not combat:
                return jsonify({'error': 'Combat not found'}), 404
            
            combat.determine_turn_order()
            
            # Build order data
            order = []
            for i, (participant_id, init_total) in enumerate(combat.initiative_order, 1):
                participant = combat.get_participant_by_id(participant_id)
                order.append({
                    'position': i,
                    'participant_id': participant_id,
                    'name': participant.name,
                    'type': participant.participant_type.value,
                    'initiative': init_total
                })
            
            return jsonify({
                'success': True,
                'phase': combat.combat_phase.value,
                'order': order
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    
    @app.route('/api/combat/<combat_id>/start', methods=['POST'])
    def start_combat(combat_id):
        """Start the combat"""
        try:
            combat = active_combats.get(combat_id)
            if not combat:
                return jsonify({'error': 'Combat not found'}), 404
            
            combat.init_combat()
            
            current = combat.get_current_participant()
            
            return jsonify({
                'success': True,
                'phase': combat.combat_phase.value,
                'round': combat.current_round,
                'current_turn': {
                    'name': current.name,
                    'type': current.participant_type.value
                } if current else None
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    
    @app.route('/api/combat/<combat_id>/summary', methods=['GET'])
    def get_combat_summary(combat_id):
        """Get combat summary"""
        try:
            combat = active_combats.get(combat_id)
            if not combat:
                return jsonify({'error': 'Combat not found'}), 404
            
            summary = combat.get_combat_summary()
            
            return jsonify({
                'success': True,
                'summary': summary
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    
    @app.route('/api/combat/<combat_id>', methods=['DELETE'])
    def delete_combat(combat_id):
        """Delete a combat"""
        try:
            if combat_id in active_combats:
                del active_combats[combat_id]
                return jsonify({'success': True})
            return jsonify({'error': 'Combat not found'}), 404
            
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    
    @app.route('/api/monsters/presets', methods=['GET'])
    def get_monster_presets():
        """Get preset monster templates"""
        presets = {
            'goblin': {
                'name': 'Goblin',
                'monster_type': 'Humanoid',
                'size': 'Small',
                'alignment': 'Neutral Evil',
                'challenge_rating': 0.25,
                'hp': 7,
                'ac': 15,
                'stats': {
                    'strength': 8,
                    'dexterity': 14,
                    'constitution': 10,
                    'intelligence': 10,
                    'wisdom': 8,
                    'charisma': 8
                },
                'abilities': ['Nimble Escape'],
                'actions': ['Scimitar (1d6+2)', 'Shortbow (1d6+2)']
            },
            'goblin_boss': {
                'name': 'Goblin Boss',
                'monster_type': 'Humanoid',
                'size': 'Small',
                'alignment': 'Neutral Evil',
                'challenge_rating': 1,
                'hp': 21,
                'ac': 17,
                'stats': {
                    'strength': 10,
                    'dexterity': 14,
                    'constitution': 10,
                    'intelligence': 10,
                    'wisdom': 8,
                    'charisma': 10
                },
                'abilities': ['Redirect Attack'],
                'actions': ['Multiattack', 'Scimitar (1d6+2)', 'Javelin (1d6+2)']
            },
            'orc': {
                'name': 'Orc',
                'monster_type': 'Humanoid',
                'size': 'Medium',
                'alignment': 'Chaotic Evil',
                'challenge_rating': 0.5,
                'hp': 15,
                'ac': 13,
                'stats': {
                    'strength': 16,
                    'dexterity': 12,
                    'constitution': 16,
                    'intelligence': 7,
                    'wisdom': 11,
                    'charisma': 10
                },
                'abilities': ['Aggressive'],
                'actions': ['Greataxe (1d12+3)', 'Javelin (1d6+3)']
            },
            'wolf': {
                'name': 'Wolf',
                'monster_type': 'Beast',
                'size': 'Medium',
                'alignment': 'Unaligned',
                'challenge_rating': 0.25,
                'hp': 11,
                'ac': 13,
                'stats': {
                    'strength': 12,
                    'dexterity': 15,
                    'constitution': 12,
                    'intelligence': 3,
                    'wisdom': 12,
                    'charisma': 6
                },
                'abilities': ['Keen Hearing and Smell', 'Pack Tactics'],
                'actions': ['Bite (2d4+2)']
            },
            'skeleton': {
                'name': 'Skeleton',
                'monster_type': 'Undead',
                'size': 'Medium',
                'alignment': 'Lawful Evil',
                'challenge_rating': 0.25,
                'hp': 13,
                'ac': 13,
                'stats': {
                    'strength': 10,
                    'dexterity': 14,
                    'constitution': 15,
                    'intelligence': 6,
                    'wisdom': 8,
                    'charisma': 5
                },
                'abilities': ['Damage Vulnerabilities: Bludgeoning'],
                'actions': ['Shortsword (1d6+2)', 'Shortbow (1d6+2)']
            }
        }
        
        return jsonify({'presets': presets})