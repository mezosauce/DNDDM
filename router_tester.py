#!/usr/bin/env python3
"""
Flask API Routes for Barbarian Class
Provides REST API endpoints for JavaScript frontend integration

Endpoints:
    GET    /api/barbarian/<name>              - Get character data
    POST   /api/barbarian/<name>/create       - Create new character
    POST   /api/barbarian/<name>/enter_rage   - Enter rage
    POST   /api/barbarian/<name>/end_rage     - End rage
    POST   /api/barbarian/<name>/long_rest    - Long rest
    POST   /api/barbarian/<name>/update_stats - Update ability scores
    POST   /api/barbarian/<name>/set_level    - Set character level
    DELETE /api/barbarian/<name>              - Delete character
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Head.Class import create_character, character_to_dict, character_from_dict
from Head.Class.barbarian import Barbarian

# Create Blueprint
barbarian_api = Blueprint('barbarian_api', __name__, url_prefix='/api/barbarian')

# In-memory storage (replace with database in production)
# Format: {character_name: Barbarian instance}
barbarian_characters: Dict[str, Barbarian] = {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_character_or_404(name: str) -> Barbarian:
    """Get character or return 404 error"""
    if name not in barbarian_characters:
        return None
    return barbarian_characters[name]


def success_response(message: str, data: Dict[str, Any] = None, status: int = 200):
    """Create standardized success response"""
    response = {"success": True, "message": message}
    if data:
        response.update(data)
    return jsonify(response), status


def error_response(message: str, status: int = 400):
    """Create standardized error response"""
    return jsonify({"success": False, "error": message}), status


# ============================================================================
# CHARACTER MANAGEMENT ENDPOINTS
# ============================================================================

@barbarian_api.route('/<string:name>', methods=['GET'])
def get_character(name: str):
    """
    Get character data
    
    GET /api/barbarian/<name>
    
    Returns:
        200: Character data as JSON
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    return jsonify(character_to_dict(character)), 200


@barbarian_api.route('/<string:name>/create', methods=['POST'])
def create_barbarian(name: str):
    """
    Create new barbarian character
    
    POST /api/barbarian/<name>/create
    Body: {
        "race": "Goliath",
        "background": "Outlander",
        "level": 1,
        "stats": {
            "strength": 17,
            "dexterity": 14,
            ...
        },
        "primal_path": "Path of the Berserker" (optional)
    }
    
    Returns:
        201: Character created successfully
        409: Character already exists
        400: Invalid data
    """
    if name in barbarian_characters:
        return error_response("Character already exists", 409)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided", 400)
    
    try:
        # Create character using factory
        character = create_character(
            "Barbarian",
            name=name,
            race=data.get('race', 'Human'),
            background=data.get('background', ''),
            level=data.get('level', 1),
            stats=data.get('stats', None),
            alignment=data.get('alignment', '')
        )
        
        # Set optional barbarian-specific fields
        if 'primal_path' in data:
            character.primal_path = data['primal_path']
            character.apply_level_features()
        
        barbarian_characters[name] = character
        
        return success_response(
            "Character created successfully",
            character_to_dict(character),
            201
        )
    
    except Exception as e:
        return error_response(f"Failed to create character: {str(e)}", 400)


@barbarian_api.route('/<string:name>', methods=['DELETE'])
def delete_character(name: str):
    """
    Delete character
    
    DELETE /api/barbarian/<name>
    
    Returns:
        200: Character deleted
        404: Character not found
    """
    if name not in barbarian_characters:
        return error_response("Character not found", 404)
    
    del barbarian_characters[name]
    return success_response(f"Character '{name}' deleted")


# ============================================================================
# RAGE MECHANICS ENDPOINTS
# ============================================================================

@barbarian_api.route('/<string:name>/enter_rage', methods=['POST'])
def enter_rage(name: str):
    """
    Enter rage
    
    POST /api/barbarian/<name>/enter_rage
    
    Returns:
        200: Rage activated successfully
        400: Cannot enter rage (already raging or no rages left)
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    success = character.enter_rage()
    
    if success:
        return success_response(
            "Rage activated!",
            {
                "rages_used": character.rages_used,
                "rages_per_day": character.rages_per_day,
                "currently_raging": character.currently_raging,
                "rage_damage": character.rage_damage,
                "rage_benefits": character.get_rage_benefits()
            }
        )
    else:
        return error_response(
            "Cannot enter rage (already raging or no rages left)",
            400
        )


@barbarian_api.route('/<string:name>/end_rage', methods=['POST'])
def end_rage(name: str):
    """
    End rage
    
    POST /api/barbarian/<name>/end_rage
    
    Returns:
        200: Rage ended successfully
        400: Not currently raging
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    if not character.currently_raging:
        return error_response("Not currently raging", 400)
    
    character.end_rage()
    
    return success_response(
        "Rage ended",
        {
            "currently_raging": character.currently_raging,
            "exhaustion_level": character.exhaustion_level,
            "rages_used": character.rages_used,
            "rages_per_day": character.rages_per_day
        }
    )


@barbarian_api.route('/<string:name>/activate_frenzy', methods=['POST'])
def activate_frenzy(name: str):
    """
    Activate Frenzy (Berserker Path only)
    
    POST /api/barbarian/<name>/activate_frenzy
    
    Returns:
        200: Frenzy activated
        400: Cannot activate frenzy
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    success = character.activate_frenzy()
    
    if success:
        return success_response(
            "Frenzy activated! Extra attack available, exhaustion after rage ends.",
            {"frenzy_active": character.frenzy_active}
        )
    else:
        return error_response(
            "Cannot activate frenzy (not raging, wrong path, or feature not unlocked)",
            400
        )


# ============================================================================
# REST & RECOVERY ENDPOINTS
# ============================================================================

@barbarian_api.route('/<string:name>/long_rest', methods=['POST'])
def long_rest(name: str):
    """
    Long rest (8 hours)
    
    POST /api/barbarian/<name>/long_rest
    
    Returns:
        200: Long rest completed
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    character.long_rest()
    
    return success_response(
        "Long rest completed. Rages and HP restored!",
        {
            "rages_used": character.rages_used,
            "rages_per_day": character.rages_per_day,
            "hp": character.hp,
            "max_hp": character.max_hp,
            "currently_raging": character.currently_raging,
            "relentless_rage_dc": character.relentless_rage_dc
        }
    )


# ============================================================================
# CHARACTER MODIFICATION ENDPOINTS
# ============================================================================

@barbarian_api.route('/<string:name>/update_stats', methods=['POST'])
def update_stats(name: str):
    """
    Update ability scores
    
    POST /api/barbarian/<name>/update_stats
    Body: {
        "stats": {
            "strength": 18,
            "dexterity": 14,
            ...
        }
    }
    
    Returns:
        200: Stats updated successfully
        400: Invalid data
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    data = request.get_json()
    if not data or 'stats' not in data:
        return error_response("No stats provided", 400)
    
    try:
        # Update stats
        character.stats.update(data['stats'])
        
        # Recalculate dependent values
        if character.unarmored_defense_active:
            character.calculate_unarmored_defense()
        
        return success_response(
            "Stats updated successfully",
            {
                "stats": character.stats,
                "ac": character.ac
            }
        )
    
    except Exception as e:
        return error_response(f"Failed to update stats: {str(e)}", 400)


@barbarian_api.route('/<string:name>/set_level', methods=['POST'])
def set_level(name: str):
    """
    Set character level
    
    POST /api/barbarian/<name>/set_level
    Body: {"level": 5}
    
    Returns:
        200: Level updated successfully
        400: Invalid level
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    data = request.get_json()
    if not data or 'level' not in data:
        return error_response("No level provided", 400)
    
    try:
        level = int(data['level'])
        if level < 1 or level > 20:
            return error_response("Level must be between 1 and 20", 400)
        
        old_level = character.level
        character.level = level
        character.apply_level_features()
        
        # Recalculate AC if using Unarmored Defense
        if character.unarmored_defense_active:
            character.calculate_unarmored_defense()
        
        return success_response(
            f"Level updated from {old_level} to {level}",
            {
                "old_level": old_level,
                "new_level": character.level,
                "rages_per_day": character.rages_per_day,
                "rage_damage": character.rage_damage,
                "fast_movement": character.fast_movement,
                "brutal_critical_dice": character.brutal_critical_dice,
                "features": {
                    "reckless_attack": character.reckless_attack_available,
                    "danger_sense": character.danger_sense_active,
                    "feral_instinct": character.feral_instinct,
                    "relentless_rage": character.relentless_rage_active,
                    "persistent_rage": character.persistent_rage,
                    "indomitable_might": character.indomitable_might,
                    "primal_champion": character.primal_champion
                }
            }
        )
    
    except ValueError:
        return error_response("Invalid level value", 400)
    except Exception as e:
        return error_response(f"Failed to set level: {str(e)}", 400)


@barbarian_api.route('/<string:name>/set_primal_path', methods=['POST'])
def set_primal_path(name: str):
    """
    Set Primal Path (subclass)
    
    POST /api/barbarian/<name>/set_primal_path
    Body: {"primal_path": "Path of the Berserker"}
    
    Returns:
        200: Primal path set successfully
        400: Invalid path or character not level 3+
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    if character.level < 3:
        return error_response("Must be level 3 or higher to choose Primal Path", 400)
    
    data = request.get_json()
    if not data or 'primal_path' not in data:
        return error_response("No primal path provided", 400)
    
    valid_paths = [
        "Path of the Berserker",
        "Path of the Totem Warrior"
    ]
    
    path = data['primal_path']
    if path not in valid_paths:
        return error_response(
            f"Invalid primal path. Valid options: {', '.join(valid_paths)}",
            400
        )
    
    character.primal_path = path
    character.apply_level_features()
    
    return success_response(
        f"Primal Path set to {path}",
        {
            "primal_path": character.primal_path,
            "path_features": {
                "level_3": character.path_feature_3,
                "level_6": character.path_feature_6,
                "level_10": character.path_feature_10,
                "level_14": character.path_feature_14
            }
        }
    )


# ============================================================================
# QUERY ENDPOINTS
# ============================================================================

@barbarian_api.route('/<string:name>/character_sheet', methods=['GET'])
def get_character_sheet(name: str):
    """
    Get formatted character sheet
    
    GET /api/barbarian/<name>/character_sheet
    
    Returns:
        200: Complete character sheet
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    return jsonify(character.get_character_sheet()), 200


@barbarian_api.route('/<string:name>/rage_benefits', methods=['GET'])
def get_rage_benefits(name: str):
    """
    Get current rage benefits
    
    GET /api/barbarian/<name>/rage_benefits
    
    Returns:
        200: Rage benefits (or inactive status)
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    return jsonify(character.get_rage_benefits()), 200


@barbarian_api.route('/<string:name>/proficiency_bonus', methods=['GET'])
def get_proficiency_bonus(name: str):
    """
    Get proficiency bonus
    
    GET /api/barbarian/<name>/proficiency_bonus
    
    Returns:
        200: Proficiency bonus
        404: Character not found
    """
    character = get_character_or_404(name)
    if not character:
        return error_response("Character not found", 404)
    
    return jsonify({
        "proficiency_bonus": character.get_proficiency_bonus()
    }), 200


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

@barbarian_api.route('/list', methods=['GET'])
def list_characters():
    """
    List all barbarian characters
    
    GET /api/barbarian/list
    
    Returns:
        200: List of character names and basic info
    """
    characters_list = []
    for name, char in barbarian_characters.items():
        characters_list.append({
            "name": name,
            "level": char.level,
            "race": char.race,
            "primal_path": char.primal_path,
            "hp": f"{char.hp}/{char.max_hp}",
            "currently_raging": char.currently_raging
        })
    
    return jsonify({
        "count": len(characters_list),
        "characters": characters_list
    }), 200


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@barbarian_api.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return error_response("Resource not found", 404)


@barbarian_api.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return error_response("Internal server error", 500)


# ============================================================================
# FLASK APP REGISTRATION
# ============================================================================

def register_barbarian_api(app):
    """
    Register the barbarian API blueprint with a Flask app
    
    Usage:
        from flask import Flask
        from barbarian_api_routes import register_barbarian_api
        
        app = Flask(__name__)
        register_barbarian_api(app)
        app.run()
    """
    app.register_blueprint(barbarian_api)


# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    from flask import Flask
    from flask_cors import CORS
    
    # Create Flask app
    app = Flask(__name__)
    CORS(app)  # Enable CORS for frontend testing
    
    # Register blueprint
    register_barbarian_api(app)
    
    # Add a root endpoint for testing
    @app.route('/')
    def index():
        return jsonify({
            "message": "Barbarian API Server",
            "version": "1.0",
            "endpoints": {
                "GET /api/barbarian/<name>": "Get character",
                "POST /api/barbarian/<name>/create": "Create character",
                "POST /api/barbarian/<name>/enter_rage": "Enter rage",
                "POST /api/barbarian/<name>/end_rage": "End rage",
                "POST /api/barbarian/<name>/long_rest": "Long rest",
                "POST /api/barbarian/<name>/update_stats": "Update stats",
                "POST /api/barbarian/<name>/set_level": "Set level",
                "POST /api/barbarian/<name>/set_primal_path": "Set subclass",
                "GET /api/barbarian/<name>/character_sheet": "Get character sheet",
                "GET /api/barbarian/list": "List all characters"
            }
        })
    
    print("=" * 80)
    print("BARBARIAN API SERVER")
    print("=" * 80)
    print("\nStarting Flask development server...")
    print("API available at: http://localhost:5000")
    print("\nTest with curl:")
    print('  curl -X POST http://localhost:5000/api/barbarian/Grog/create \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"race":"Goliath","level":1}\'')
    print("\nPress Ctrl+C to stop")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)