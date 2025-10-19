"""
Phase 1: Setup & Character Creation Routes
This module should NOT create its own Flask app - it only defines routes
"""

from flask import render_template, request, jsonify
from campaign_manager import Character


# ============================================================================
# Phase 1: Setup & Character Creation
# ============================================================================

def register_phase1_routes(app, campaign_mgr):
    """
    Register all Phase 1 routes to the main Flask app
    
    Args:
        app: The Flask application instance
        campaign_mgr: The campaign manager instance
    """
    
    @app.route('/campaign/<campaign_name>/setup')
    def setup_phase(campaign_name):
        """Setup and character creation phase"""
        try:
            campaign = campaign_mgr.load_campaign(campaign_name)
            characters = campaign_mgr.get_characters(campaign_name)
            
            return render_template('setup_phase.html', 
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
    
    print("✓ Phase 1 routes registered")