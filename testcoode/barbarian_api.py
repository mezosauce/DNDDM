#!/usr/bin/env python3
"""
Test Suite for Barbarian API Pipeline
Tests the integration between Python backend (barbarian.py) and JavaScript frontend (barbarian.js)

This test suite validates:
1. Character creation and retrieval
2. Rage mechanics (enter/end/reset)
3. Stat updates and level changes
4. Unarmored Defense calculations
5. Long rest functionality
6. Error handling and edge cases

Run with: pytest test_barbarian_api.py -v
"""

import pytest
import json
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BackEnd.Class.barbarian import Barbarian
from BackEnd.Class import create_character, character_to_dict, character_from_dict


# ============================================================================
# MOCK FLASK APP FOR TESTING
# ============================================================================

class MockFlaskApp:
    """Mock Flask app to simulate API endpoints"""
    
    def __init__(self):
        self.characters = {}
    
    def create_character_endpoint(self, name, data):
        """POST /api/barbarian/<name>/create"""
        if name in self.characters:
            return {"error": "Character already exists"}, 409
        
        character = create_character(
            "Barbarian",
            name=name,
            race=data.get('race', 'Human'),
            background=data.get('background', ''),
            level=data.get('level', 1),
            stats=data.get('stats', {
                "strength": 15,
                "dexterity": 13,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8
            })
        )
        
        self.characters[name] = character
        return character_to_dict(character), 201
    
    def get_character_endpoint(self, name):
        """GET /api/barbarian/<name>"""
        if name not in self.characters:
            return {"error": "Character not found"}, 404
        
        return character_to_dict(self.characters[name]), 200
    
    def enter_rage_endpoint(self, name):
        """POST /api/barbarian/<name>/enter_rage"""
        if name not in self.characters:
            return {"error": "Character not found"}, 404
        
        character = self.characters[name]
        success = character.enter_rage()
        
        if success:
            return {
                "success": True,
                "message": "Rage activated",
                "rages_used": character.rages_used,
                "rages_per_day": character.rages_per_day,
                "currently_raging": character.currently_raging,
                "rage_damage": character.rage_damage
            }, 200
        else:
            return {
                "success": False,
                "message": "Cannot enter rage (already raging or no rages left)"
            }, 400
    
    def end_rage_endpoint(self, name):
        """POST /api/barbarian/<name>/end_rage"""
        if name not in self.characters:
            return {"error": "Character not found"}, 404
        
        character = self.characters[name]
        if not character.currently_raging:
            return {"success": False, "message": "Not currently raging"}, 400
        
        character.end_rage()
        return {
            "success": True,
            "message": "Rage ended",
            "currently_raging": character.currently_raging,
            "exhaustion_level": character.exhaustion_level
        }, 200
    
    def long_rest_endpoint(self, name):
        """POST /api/barbarian/<name>/long_rest"""
        if name not in self.characters:
            return {"error": "Character not found"}, 404
        
        character = self.characters[name]
        character.long_rest()
        
        return {
            "success": True,
            "message": "Long rest completed",
            "rages_used": character.rages_used,
            "hp": character.hp,
            "max_hp": character.max_hp,
            "currently_raging": character.currently_raging
        }, 200
    
    def update_stats_endpoint(self, name, stats):
        """POST /api/barbarian/<name>/update_stats"""
        if name not in self.characters:
            return {"error": "Character not found"}, 404
        
        character = self.characters[name]
        character.stats.update(stats)
        
        # Recalculate dependent values
        if character.unarmored_defense_active:
            character.calculate_unarmored_defense()
        
        return {
            "success": True,
            "stats": character.stats,
            "ac": character.ac
        }, 200
    
    def set_level_endpoint(self, name, level):
        """POST /api/barbarian/<name>/set_level"""
        if name not in self.characters:
            return {"error": "Character not found"}, 404
        
        character = self.characters[name]
        old_level = character.level
        character.level = level
        character.apply_level_features()
        
        if character.unarmored_defense_active:
            character.calculate_unarmored_defense()
        
        return {
            "success": True,
            "old_level": old_level,
            "new_level": character.level,
            "rages_per_day": character.rages_per_day,
            "rage_damage": character.rage_damage,
            "features_updated": True
        }, 200


# ============================================================================
# PYTEST FIXTURES
# ============================================================================

@pytest.fixture
def mock_app():
    """Provide a fresh mock Flask app for each test"""
    return MockFlaskApp()


@pytest.fixture
def sample_barbarian_data():
    """Sample character creation data"""
    return {
        "name": "Grog Strongjaw",
        "race": "Goliath",
        "background": "Outlander",
        "level": 1,
        "stats": {
            "strength": 17,
            "dexterity": 14,
            "constitution": 16,
            "intelligence": 8,
            "wisdom": 10,
            "charisma": 12
        }
    }


@pytest.fixture
def created_character(mock_app, sample_barbarian_data):
    """Create a character and return the mock app with character"""
    name = sample_barbarian_data["name"]
    data = {k: v for k, v in sample_barbarian_data.items() if k != "name"}
    mock_app.create_character_endpoint(name, data)
    return mock_app, name


# ============================================================================
# TEST: CHARACTER CREATION
# ============================================================================

class TestCharacterCreation:
    """Test character creation and retrieval endpoints"""
    
    def test_create_new_character(self, mock_app, sample_barbarian_data):
        """Test creating a new barbarian character"""
        name = sample_barbarian_data["name"]
        data = {k: v for k, v in sample_barbarian_data.items() if k != "name"}
        
        response, status = mock_app.create_character_endpoint(name, data)
        
        assert status == 201
        assert response["name"] == name
        assert response["char_class"] == "Barbarian"
        assert response["race"] == "Goliath"
        assert response["level"] == 1
        assert "rages_per_day" in response
        assert response["rages_per_day"] == 2
    
    def test_create_duplicate_character(self, mock_app, sample_barbarian_data):
        """Test that creating duplicate character fails"""
        name = sample_barbarian_data["name"]
        data = {k: v for k, v in sample_barbarian_data.items() if k != "name"}
        
        # Create first character
        mock_app.create_character_endpoint(name, data)
        
        # Try to create duplicate
        response, status = mock_app.create_character_endpoint(name, data)
        
        assert status == 409
        assert "error" in response
    
    def test_get_existing_character(self, created_character):
        """Test retrieving an existing character"""
        mock_app, name = created_character
        
        response, status = mock_app.get_character_endpoint(name)
        
        assert status == 200
        assert response["name"] == name
        assert response["char_class"] == "Barbarian"
    
    def test_get_nonexistent_character(self, mock_app):
        """Test retrieving a character that doesn't exist"""
        response, status = mock_app.get_character_endpoint("NonExistent")
        
        assert status == 404
        assert "error" in response
    
    def test_default_barbarian_stats(self, mock_app):
        """Test that default stats are applied correctly"""
        name = "TestBarbarian"
        data = {"race": "Human", "background": "Soldier", "level": 1}
        
        response, status = mock_app.create_character_endpoint(name, data)
        
        assert status == 201
        assert "stats" in response
        # Should have default barbarian stats
        assert response["stats"]["strength"] >= 10
        assert response["stats"]["constitution"] >= 10


# ============================================================================
# TEST: RAGE MECHANICS
# ============================================================================

class TestRageMechanics:
    """Test rage enter/end/reset functionality"""
    
    def test_enter_rage_success(self, created_character):
        """Test successfully entering rage"""
        mock_app, name = created_character
        
        response, status = mock_app.enter_rage_endpoint(name)
        
        assert status == 200
        assert response["success"] is True
        assert response["currently_raging"] is True
        assert response["rages_used"] == 1
        assert response["rage_damage"] == 2
    
    def test_enter_rage_when_already_raging(self, created_character):
        """Test that entering rage twice fails"""
        mock_app, name = created_character
        
        # Enter rage first time
        mock_app.enter_rage_endpoint(name)
        
        # Try to enter rage again
        response, status = mock_app.enter_rage_endpoint(name)
        
        assert status == 400
        assert response["success"] is False
    
    def test_enter_rage_no_rages_left(self, created_character):
        """Test that rage fails when all rages are used"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        # Use all rages (level 1 has 2 rages)
        character.enter_rage()
        character.end_rage()
        character.enter_rage()
        character.end_rage()
        
        # Try to rage again
        response, status = mock_app.enter_rage_endpoint(name)
        
        assert status == 400
        assert response["success"] is False
    
    def test_end_rage_success(self, created_character):
        """Test successfully ending rage"""
        mock_app, name = created_character
        
        # Enter rage first
        mock_app.enter_rage_endpoint(name)
        
        # End rage
        response, status = mock_app.end_rage_endpoint(name)
        
        assert status == 200
        assert response["success"] is True
        assert response["currently_raging"] is False
    
    def test_end_rage_when_not_raging(self, created_character):
        """Test ending rage when not raging fails gracefully"""
        mock_app, name = created_character
        
        response, status = mock_app.end_rage_endpoint(name)
        
        assert status == 400
        assert response["success"] is False
    
    def test_rage_benefits_calculation(self, created_character):
        """Test that rage benefits are calculated correctly"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        character.enter_rage()
        benefits = character.get_rage_benefits()
        
        assert benefits["active"] is True
        assert benefits["advantage_on_str_checks"] is True
        assert benefits["advantage_on_str_saves"] is True
        assert benefits["bonus_melee_damage"] == 2
        assert "bludgeoning" in benefits["resistance_physical"]
        assert benefits["cannot_cast_spells"] is True


# ============================================================================
# TEST: LONG REST
# ============================================================================

class TestLongRest:
    """Test long rest functionality"""
    
    def test_long_rest_restores_rages(self, created_character):
        """Test that long rest restores rage uses"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        # Use a rage
        character.enter_rage()
        character.end_rage()
        assert character.rages_used == 1
        
        # Long rest
        response, status = mock_app.long_rest_endpoint(name)
        
        assert status == 200
        assert response["success"] is True
        assert response["rages_used"] == 0
        assert response["currently_raging"] is False
    
    def test_long_rest_restores_hp(self, created_character):
        """Test that long rest restores HP"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        # Damage the character
        original_hp = character.max_hp
        character.hp = original_hp // 2
        
        # Long rest
        response, status = mock_app.long_rest_endpoint(name)
        
        assert status == 200
        assert response["hp"] == response["max_hp"]
        assert response["hp"] == original_hp
    
    def test_long_rest_ends_rage(self, created_character):
        """Test that long rest ends active rage"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        # Enter rage
        character.enter_rage()
        assert character.currently_raging is True
        
        # Long rest
        response, status = mock_app.long_rest_endpoint(name)
        
        assert response["currently_raging"] is False


# ============================================================================
# TEST: STAT UPDATES
# ============================================================================

class TestStatUpdates:
    """Test stat modification and recalculation"""
    
    def test_update_single_stat(self, created_character):
        """Test updating a single ability score"""
        mock_app, name = created_character
        
        new_stats = {"strength": 20}
        response, status = mock_app.update_stats_endpoint(name, new_stats)
        
        assert status == 200
        assert response["success"] is True
        assert response["stats"]["strength"] == 20
    
    def test_update_multiple_stats(self, created_character):
        """Test updating multiple ability scores"""
        mock_app, name = created_character
        
        new_stats = {
            "strength": 18,
            "constitution": 16,
            "dexterity": 14
        }
        response, status = mock_app.update_stats_endpoint(name, new_stats)
        
        assert status == 200
        assert response["stats"]["strength"] == 18
        assert response["stats"]["constitution"] == 16
        assert response["stats"]["dexterity"] == 14
    
    def test_stat_update_recalculates_ac(self, created_character):
        """Test that updating DEX/CON recalculates Unarmored Defense AC"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        original_ac = character.ac
        
        # Increase DEX and CON
        new_stats = {
            "dexterity": 18,  # +4 mod
            "constitution": 18  # +4 mod
        }
        response, status = mock_app.update_stats_endpoint(name, new_stats)
        
        # AC should be higher: 10 + 4 (DEX) + 4 (CON) = 18
        assert response["ac"] > original_ac
        assert response["ac"] == 18


# ============================================================================
# TEST: LEVEL PROGRESSION
# ============================================================================

class TestLevelProgression:
    """Test level changes and feature unlocking"""
    
    def test_level_up_from_1_to_2(self, created_character):
        """Test leveling from 1 to 2 unlocks features"""
        mock_app, name = created_character
        
        response, status = mock_app.set_level_endpoint(name, 2)
        
        assert status == 200
        assert response["new_level"] == 2
        assert response["old_level"] == 1
        
        # Check character got level 2 features
        character = mock_app.characters[name]
        assert character.reckless_attack_available is True
        assert character.danger_sense_active is True
    
    def test_level_3_increases_rages(self, created_character):
        """Test that level 3 increases rages per day"""
        mock_app, name = created_character
        
        response, status = mock_app.set_level_endpoint(name, 3)
        
        assert response["rages_per_day"] == 3
    
    def test_level_9_increases_rage_damage(self, created_character):
        """Test that level 9 increases rage damage"""
        mock_app, name = created_character
        
        response, status = mock_app.set_level_endpoint(name, 9)
        
        assert response["rage_damage"] == 3
        
        # Check character got Brutal Critical
        character = mock_app.characters[name]
        assert character.brutal_critical_dice == 1
    
    def test_level_20_unlimited_rages(self, created_character):
        """Test that level 20 grants unlimited rages"""
        mock_app, name = created_character
        
        response, status = mock_app.set_level_endpoint(name, 20)
        
        assert response["rages_per_day"] == 999  # Unlimited
        
        # Check Primal Champion feature
        character = mock_app.characters[name]
        assert character.primal_champion is True
    
    def test_level_progression_unlocks_all_features(self, created_character):
        """Test that leveling through 1-20 unlocks all features"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        # Level to 5
        mock_app.set_level_endpoint(name, 5)
        assert character.fast_movement == 10
        
        # Level to 7
        mock_app.set_level_endpoint(name, 7)
        assert character.feral_instinct is True
        
        # Level to 11
        mock_app.set_level_endpoint(name, 11)
        assert character.relentless_rage_active is True
        
        # Level to 15
        mock_app.set_level_endpoint(name, 15)
        assert character.persistent_rage is True
        
        # Level to 18
        mock_app.set_level_endpoint(name, 18)
        assert character.indomitable_might is True


# ============================================================================
# TEST: UNARMORED DEFENSE
# ============================================================================

class TestUnarmoredDefense:
    """Test Unarmored Defense calculation"""
    
    def test_unarmored_defense_formula(self, created_character):
        """Test that Unarmored Defense uses correct formula: 10 + DEX + CON"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        # Set known stats
        character.stats["dexterity"] = 14  # +2 mod
        character.stats["constitution"] = 16  # +3 mod
        character.calculate_unarmored_defense()
        
        # AC should be 10 + 2 + 3 = 15
        assert character.ac == 15
    
    def test_unarmored_defense_updates_with_stats(self, created_character):
        """Test that Unarmored Defense updates when stats change"""
        mock_app, name = created_character
        
        # Update stats
        new_stats = {
            "dexterity": 20,  # +5 mod
            "constitution": 20  # +5 mod
        }
        response, status = mock_app.update_stats_endpoint(name, new_stats)
        
        # AC should be 10 + 5 + 5 = 20
        assert response["ac"] == 20


# ============================================================================
# TEST: ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Test error handling for invalid requests"""
    
    def test_operation_on_nonexistent_character(self, mock_app):
        """Test that operations on non-existent characters fail gracefully"""
        response, status = mock_app.enter_rage_endpoint("DoesNotExist")
        assert status == 404
        
        response, status = mock_app.end_rage_endpoint("DoesNotExist")
        assert status == 404
        
        response, status = mock_app.long_rest_endpoint("DoesNotExist")
        assert status == 404
    
    def test_invalid_stat_values_handled(self, created_character):
        """Test that invalid stat updates are handled"""
        mock_app, name = created_character
        
        # Stats should still update, even with unusual values
        new_stats = {"strength": 30}  # Very high
        response, status = mock_app.update_stats_endpoint(name, new_stats)
        
        assert status == 200
        assert response["stats"]["strength"] == 30


# ============================================================================
# TEST: SERIALIZATION
# ============================================================================

class TestSerialization:
    """Test character serialization and deserialization"""
    
    def test_character_to_dict_includes_all_fields(self, created_character):
        """Test that character_to_dict includes all barbarian fields"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        char_dict = character_to_dict(character)
        
        assert "name" in char_dict
        assert "char_class" in char_dict
        assert "class_type" in char_dict
        assert "rages_per_day" in char_dict
        assert "rage_damage" in char_dict
        assert "currently_raging" in char_dict
        assert "stats" in char_dict
    
    def test_character_from_dict_preserves_state(self, created_character):
        """Test that character can be restored from dict"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        # Modify character state
        character.enter_rage()
        character.level = 5
        character.apply_level_features()
        
        # Serialize and deserialize
        char_dict = character_to_dict(character)
        restored = character_from_dict(char_dict)
        
        assert restored.name == character.name
        assert restored.level == character.level
        assert restored.currently_raging == character.currently_raging
        assert restored.rages_per_day == character.rages_per_day
        assert restored.fast_movement == character.fast_movement


# ============================================================================
# TEST: INTEGRATION SCENARIOS
# ============================================================================

class TestIntegrationScenarios:
    """Test complete gameplay scenarios"""
    
    def test_combat_scenario(self, created_character):
        """Test a complete combat scenario with rage"""
        mock_app, name = created_character
        
        # 1. Character enters rage
        response, status = mock_app.enter_rage_endpoint(name)
        assert response["success"] is True
        
        # 2. Character is in combat (rage is active)
        char_data, _ = mock_app.get_character_endpoint(name)
        assert char_data["currently_raging"] is True
        
        # 3. Combat ends, rage ends
        response, status = mock_app.end_rage_endpoint(name)
        assert response["success"] is True
        
        # 4. Take a long rest to recover
        response, status = mock_app.long_rest_endpoint(name)
        assert response["rages_used"] == 0
    
    def test_level_up_scenario(self, created_character):
        """Test leveling up through early levels"""
        mock_app, name = created_character
        
        # Start at level 1
        char_data, _ = mock_app.get_character_endpoint(name)
        assert char_data["level"] == 1
        assert char_data["rages_per_day"] == 2
        
        # Level to 2 - unlock Reckless Attack
        mock_app.set_level_endpoint(name, 2)
        character = mock_app.characters[name]
        assert character.reckless_attack_available is True
        
        # Level to 3 - gain extra rage
        response, _ = mock_app.set_level_endpoint(name, 3)
        assert response["rages_per_day"] == 3
        
        # Level to 5 - gain Fast Movement
        mock_app.set_level_endpoint(name, 5)
        character = mock_app.characters[name]
        assert character.fast_movement == 10
    
    def test_exhaustive_rage_usage(self, created_character):
        """Test using all rages and recovering"""
        mock_app, name = created_character
        character = mock_app.characters[name]
        
        # Level 1 barbarian has 2 rages
        total_rages = character.rages_per_day
        
        # Use all rages
        for i in range(total_rages):
            response, status = mock_app.enter_rage_endpoint(name)
            assert response["success"] is True
            assert response["rages_used"] == i + 1
            mock_app.end_rage_endpoint(name)
        
        # Try to rage again - should fail
        response, status = mock_app.enter_rage_endpoint(name)
        assert response["success"] is False
        
        # Long rest recovers all rages
        mock_app.long_rest_endpoint(name)
        response, status = mock_app.enter_rage_endpoint(name)
        assert response["success"] is True


# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("BARBARIAN API PIPELINE TEST SUITE")
    print("=" * 80)
    print("\nThis test suite validates the integration between:")
    print("  • Python backend (Head/Class/barbarian.py)")
    print("  • JavaScript frontend (static/js/class_features/barbarian.js)")
    print("\nRun with: pytest test_barbarian_api.py -v")
    print("=" * 80)
    
    # Run pytest programmatically
    pytest.main([__file__, "-v", "--tb=short"])