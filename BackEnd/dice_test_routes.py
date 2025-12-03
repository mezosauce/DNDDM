#!/usr/bin/env python3
"""
Dice Roll Test Route
Standalone test page for Phase 3 dice rolling system
"""

from flask import render_template, request, jsonify, session
from component.GameState.dice_state import (
    DiceRollState, 
    DiceType, 
    PlayerStats, 
    RollType,
    DifficultyLevel,
    RollOutcome
)
from dataclasses import asdict
import json


def register_dice_test_routes(app):
    """Register dice test routes with the Flask app"""
    
    @app.route('/test/dice')
    def dice_test_page():
        """Main dice testing page"""
        
        # Create default player stats for testing
        default_stats = PlayerStats(
            strength=16,  # +3 modifier
            dexterity=14,  # +2 modifier
            constitution=12,  # +1 modifier
            intelligence=10,  # +0 modifier
            wisdom=8,   # -1 modifier
            charisma=13,  # +1 modifier
            proficiency_bonus=2,
            proficient_skills=['Athletics', 'Stealth', 'Perception']
        )
        
        # Get or create dice state
        if 'dice_test_state' not in session:
            dice_state = DiceRollState(player_stats=default_stats)
            session['dice_test_state'] = dice_state.to_dict()
        else:
            dice_state_data = session['dice_test_state']
            dice_state = DiceRollState.from_dict(dice_state_data)
        
        # Get statistics
        stats = dice_state.get_statistics()
        
        context = {
            'player_stats': asdict(default_stats),
            'dice_types': [d.name for d in DiceType],
            'roll_types': [r.value for r in RollType],
            'difficulty_levels': {d.name: d.value for d in DifficultyLevel},
            'statistics': stats,
            'roll_history': dice_state.result_history[-10:] if dice_state.result_history else []
        }
        
        return render_template('dice_test.html', **context)
    
    
    @app.route('/test/dice/roll', methods=['POST'])
    def dice_test_roll():
        """Execute a test dice roll"""
        try:
            data = request.json
            
            # Get dice state from session
            if 'dice_test_state' not in session:
                return jsonify({'error': 'Dice state not initialized'}), 400
            
            dice_state_data = session['dice_test_state']
            dice_state = DiceRollState.from_dict(dice_state_data)
            
            # Parse parameters
            dice_type = DiceType[data.get('dice_type', 'D20')]
            target_number = int(data.get('target_number', 15))
            relevant_stat = data.get('relevant_stat', 'strength')
            skill = data.get('skill', None)
            roll_type = RollType(data.get('roll_type', 'normal'))
            situation = data.get('situation', 'Test roll')
            
            # Activate roll
            dice_state.activate_roll(
                situation=situation,
                dice_type=dice_type,
                target_number=target_number,
                relevant_stat=relevant_stat,
                skill=skill if skill else None,
                roll_type=roll_type
            )
            
            # Execute roll
            result = dice_state.execute_roll()
            
            # Save updated state
            session['dice_test_state'] = dice_state.to_dict()
            
            # Build response
            response = {
                'success': True,
                'result': {
                    'roll_id': result.roll_id,
                    'dice_type': result.dice_type.name,
                    'raw_rolls': result.raw_rolls,
                    'selected_roll': result.selected_roll,
                    'modifiers': result.modifiers,
                    'total_score': result.total_score,
                    'target_number': result.target_number,
                    'outcome': result.outcome.value,
                    'margin': result.margin,
                    'situation': result.situation,
                    'narrative': result.get_narrative_result(),
                    'breakdown': result.get_roll_breakdown()
                },
                'statistics': dice_state.get_statistics()
            }
            
            return jsonify(response)
            
        except Exception as e:
            print(f"Error in dice_test_roll: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/test/dice/update-stats', methods=['POST'])
    def dice_test_update_stats():
        """Update player stats for testing"""
        try:
            data = request.json
            
            # Create new player stats
            player_stats = PlayerStats(
                strength=int(data.get('strength', 10)),
                dexterity=int(data.get('dexterity', 10)),
                constitution=int(data.get('constitution', 10)),
                intelligence=int(data.get('intelligence', 10)),
                wisdom=int(data.get('wisdom', 10)),
                charisma=int(data.get('charisma', 10)),
                proficiency_bonus=int(data.get('proficiency_bonus', 2)),
                proficient_skills=data.get('proficient_skills', []),
                equipment_bonus=int(data.get('equipment_bonus', 0)),
                temporary_bonus=int(data.get('temporary_bonus', 0))
            )
            
            # Create new dice state with updated stats
            dice_state = DiceRollState(player_stats=player_stats)
            
            # Preserve roll history if requested
            if data.get('preserve_history', False) and 'dice_test_state' in session:
                old_state = DiceRollState.from_dict(session['dice_test_state'])
                dice_state.result_history = old_state.result_history
                dice_state._roll_counter = old_state._roll_counter
            
            # Save to session
            session['dice_test_state'] = dice_state.to_dict()
            
            return jsonify({
                'success': True,
                'player_stats': asdict(player_stats),
                'statistics': dice_state.get_statistics()
            })
            
        except Exception as e:
            print(f"Error in dice_test_update_stats: {e}")
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/test/dice/reset', methods=['POST'])
    def dice_test_reset():
        """Reset dice test state"""
        try:
            # Clear session
            if 'dice_test_state' in session:
                session.pop('dice_test_state')
            
            return jsonify({'success': True})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    
    @app.route('/test/dice/history')
    def dice_test_history():
        """Get full roll history"""
        try:
            if 'dice_test_state' not in session:
                return jsonify({'history': [], 'statistics': {}})
            
            dice_state_data = session['dice_test_state']
            dice_state = DiceRollState.from_dict(dice_state_data)
            
            # Convert results to JSON-serializable format
            history = []
            for result in dice_state.result_history:
                history.append({
                    'roll_id': result.roll_id,
                    'situation': result.situation,
                    'dice_type': result.dice_type.name,
                    'selected_roll': result.selected_roll,
                    'total_score': result.total_score,
                    'target_number': result.target_number,
                    'outcome': result.outcome.value,
                    'margin': result.margin,
                    'timestamp': result.timestamp
                })
            
            return jsonify({
                'history': history,
                'statistics': dice_state.get_statistics()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    
    print("✓ Dice test routes registered")