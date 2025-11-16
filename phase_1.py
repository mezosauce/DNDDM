#!/usr/bin/env python3
"""
Phase 1: Setup & Character Creation Routes
Handles character creation, updates, and phase advancement
"""

from flask import render_template, request, jsonify
from dataclasses import asdict

# These will be imported from main.py when we integrate
# from main import app, campaign_mgr, Character

from Head.Class import create_character

# ============================================================================
# PHASE 1: SETUP & CHARACTER CREATION
# ============================================================================

def register_phase1_routes(app, campaign_mgr, Character):
    """Register all Phase 1 routes with the Flask app"""
    
    @app.route('/campaign/<campaign_name>/setup')
    def setup_phase(campaign_name):
        """Setup and character creation phase"""
        try:
            campaign = campaign_mgr.load_campaign(campaign_name)
            characters = campaign_mgr.get_characters(campaign_name)
            
            return render_template('HTML/setup_phase.html', 
                                 campaign=campaign,
                                 characters=characters)
        except Exception as e:
            return f"Error: {e}", 404


    @app.route('/campaign/<campaign_name>/character/add', methods=['POST'])
    def add_character(campaign_name):
        """Add a new character"""
        data = request.json
        
        try:
            character = Character(
                name=data['name'],
                race=data['race'],
                char_class=data['class'],
                background=data['background'],
                level=int(data.get('level', 1)),
                hp=int(data.get('hp', 10)),
                max_hp=int(data.get('max_hp', 10)),
                ac=int(data.get('ac', 10)),
                stats=data.get('stats', {}),
                inventory=data.get('inventory', []),
                notes=data.get('notes', '')
            )
            
            campaign = campaign_mgr.add_character(campaign_name, character)
            
            return jsonify({
                'success': True,
                'setup_complete': campaign.setup_complete,
                'characters_count': len(campaign.characters),
                'party_size': campaign.party_size
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/advance', methods=['POST'])
    def advance_phase(campaign_name):
        """Advance to next phase"""
        try:
            campaign = campaign_mgr.advance_phase(campaign_name)
            return jsonify({
                'success': True,
                'new_phase': campaign.current_phase
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    # ============================================================================
    # CHARACTER MANAGEMENT ENDPOINTS 
    # ============================================================================

    @app.route('/campaign/<campaign_name>/character/<character_name>/update', methods=['POST'])
    def update_character(campaign_name, character_name):
        """Update an existing character"""
        data = request.json
        
        try:
            # Load existing character
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            # Update fields 
            char.hp = int(data.get('hp', char.hp))
            char.max_hp = int(data.get('max_hp', char.max_hp))
            char.ac = int(data.get('ac', char.ac))
            char.level = int(data.get('level', char.level))
            
            if 'alignment' in data:
                char.alignment = data['alignment']
            if 'notes' in data:
                char.notes = data['notes']
            if 'has_inspiration' in data:
                char.has_inspiration = data['has_inspiration']
            
            # Update character in campaign
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/add', methods=['POST'])
    def add_character(campaign_name):
        """Add a new character"""
        data = request.json
        
        try:
            # Get class type from request (defaults to "Character" if not provided)
            class_type = data.get('class', 'Character')
            
            # Use factory to create the correct class instance
            character = create_character(
                class_type=data.get('class', 'Character'),
                name=data['name'],
                race=data['race'],
                char_class=data['class'],
                background=data['background'],
                level=int(data.get('level', 1)),
                hp=int(data.get('hp', 10)),
                max_hp=int(data.get('max_hp', 10)),
                ac=int(data.get('ac', 10)),
                stats=data.get('stats', {}),
                inventory=data.get('inventory', []),
                notes=data.get('notes', ''),
                alignment=data.get('alignment', 'True Neutral'),
                background_feature=data.get('background_feature', ''),
                skill_proficiencies=data.get('skill_proficiencies', []),
                tool_proficiencies=data.get('tool_proficiencies', []),
                languages_known=data.get('languages_known', []),
                personality_traits=data.get('personality_traits', []),
                ideal=data.get('ideal', ''),
                bond=data.get('bond', ''),
                flaw=data.get('flaw', ''),
                currency=data.get('currency', {'cp': 0, 'sp': 0, 'ep': 0, 'gp': 0, 'pp': 0})
            )
            
            campaign = campaign_mgr.add_character(campaign_name, character)
            
            return jsonify({
                'success': True,
                'setup_complete': campaign.setup_complete,
                'characters_count': len(campaign.characters),
                'party_size': campaign.party_size
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/campaign/<campaign_name>/character/<character_name>/currency/remove', methods=['POST'])
    def remove_character_currency(campaign_name, character_name):
        """Remove currency from a character"""
        data = request.json
        coin_type = data.get('coin_type')
        amount = int(data.get('amount', 0))
        
        if not coin_type or amount <= 0:
            return jsonify({'error': 'Invalid coin_type or amount'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            success = char.remove_currency(coin_type, amount)
            
            if not success:
                return jsonify({'error': 'Insufficient funds'}), 400
            
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'currency': char.currency,
                'total_gp': char.get_total_gold_value()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/currency/pay', methods=['POST'])
    def pay_cost(campaign_name, character_name):
        """Pay a cost in gold (auto-converts currency)"""
        data = request.json
        cost_gp = float(data.get('cost', 0))
        
        if cost_gp <= 0:
            return jsonify({'error': 'Invalid cost'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            success = char.pay_cost(cost_gp)
            
            if not success:
                return jsonify({
                    'error': 'Insufficient funds',
                    'required': cost_gp,
                    'available': char.get_total_gold_value()
                }), 400
            
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'paid': cost_gp,
                'remaining_currency': char.currency,
                'remaining_gp': char.get_total_gold_value()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/currency/convert', methods=['POST'])
    def convert_currency(campaign_name, character_name):
        """Convert currency between denominations"""
        data = request.json
        from_type = data.get('from_type')
        to_type = data.get('to_type')
        amount = int(data.get('amount', 0))
        
        if not from_type or not to_type or amount <= 0:
            return jsonify({'error': 'Invalid parameters'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            success = char.convert_currency(from_type, to_type, amount)
            
            if not success:
                return jsonify({'error': 'Conversion failed (insufficient funds or invalid amount)'}), 400
            
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'currency': char.currency,
                'total_gp': char.get_total_gold_value()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/inventory/add', methods=['POST'])
    def add_inventory_item(campaign_name, character_name):
        """Add item to character inventory"""
        data = request.json
        item = data.get('item', '').strip()
        
        if not item:
            return jsonify({'error': 'No item provided'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            char.inventory.append(item)
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'inventory': char.inventory
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/inventory/remove', methods=['POST'])
    def remove_inventory_item(campaign_name, character_name):
        """Remove item from character inventory"""
        data = request.json
        item = data.get('item', '').strip()
        
        if not item:
            return jsonify({'error': 'No item provided'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            if item in char.inventory:
                char.inventory.remove(item)
                campaign_mgr.update_character(campaign_name, char)
                
                return jsonify({
                    'success': True,
                    'inventory': char.inventory
                })
            else:
                return jsonify({'error': 'Item not found in inventory'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/inspiration/toggle', methods=['POST'])
    def toggle_inspiration(campaign_name, character_name):
        """Toggle inspiration for a character"""
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            char.has_inspiration = not char.has_inspiration
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'has_inspiration': char.has_inspiration
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>', methods=['GET'])
    def get_character_sheet(campaign_name, character_name):
        """Get full character sheet data"""
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            return jsonify({
                'success': True,
                'character': asdict(char)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
