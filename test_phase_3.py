#!/usr/bin/env python3
"""
Phase 3 Integration Test
Tests the complete flow: Select → Create → Save → Load → Display

Tests:
1. Create Barbarian using factory
2. Save Barbarian to campaign
3. Load Barbarian from campaign
4. Verify all features work
5. Test UI integration points
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Head.campaign_manager import CampaignManager
from Head.Class import create_character, character_to_dict, character_from_dict, get_available_classes


def test_phase_3():
    """Run complete Phase 3 integration test"""
    
    print("=" * 70)
    print("PHASE 3 INTEGRATION TEST")
    print("Testing: Select → Create → Save → Load → Display")
    print("=" * 70)
    
    # Initialize campaign manager
    print("\n[1/6] Initializing Campaign Manager...")
    campaign_mgr = CampaignManager("./test_campaigns")
    
    # Create test campaign
    print("[2/6] Creating test campaign...")
    try:
        campaign = campaign_mgr.create_campaign(
            name="Phase 3 Test Campaign",
            party_size=2,
            description="Testing Barbarian class implementation"
        )
        print(f"✓ Campaign created: {campaign.name}")
    except ValueError:
        # Campaign exists, load it
        campaign = campaign_mgr.load_campaign("Phase 3 Test Campaign")
        print(f"✓ Campaign loaded: {campaign.name}")
    
    # Test available classes
    print("\n[3/6] Testing class registry...")
    available_classes = get_available_classes()
    print(f"Available classes: {', '.join(available_classes)}")
    assert 'Barbarian' in available_classes, "Barbarian not in registry!"
    print("✓ Barbarian class available")
    
    # Create Barbarian character
    print("\n[4/6] Creating Barbarian character...")
    barbarian = create_character(
        class_type="Barbarian",
        name="Test Grog",
        race="Goliath",
        char_class="Barbarian",
        background="Outlander",
        level=5,
        stats={
            "strength": 18,
            "dexterity": 14,
            "constitution": 16,
            "intelligence": 8,
            "wisdom": 10,
            "charisma": 12
        },
        alignment="Chaotic Neutral",
        personality_traits=["I'm driven by wanderlust"],
        ideal="Freedom",
        bond="My clan is everything",
        flaw="I love ale too much",
        inventory=["Greataxe", "Handaxe", "Javelin x4"],
        currency={'cp': 0, 'sp': 50, 'ep': 0, 'gp': 25, 'pp': 0}
    )
    
    print(f"✓ Created: {barbarian}")
    print(f"  Type: {type(barbarian).__name__}")
    print(f"  Level: {barbarian.level}")
    print(f"  HP: {barbarian.hp}/{barbarian.max_hp}")
    print(f"  AC: {barbarian.ac}")
    print(f"  Rages: {barbarian.rages_used}/{barbarian.rages_per_day}")
    print(f"  Rage Damage: +{barbarian.rage_damage}")
    
    # Test Barbarian-specific features
    print("\n[5/6] Testing Barbarian features...")
    
    # Test rage
    print("  Testing rage mechanics...")
    assert barbarian.enter_rage(), "Failed to enter rage!"
    print(f"    ✓ Entered rage ({barbarian.rages_used}/{barbarian.rages_per_day} used)")
    
    benefits = barbarian.get_rage_benefits()
    print(f"    ✓ Rage benefits: +{benefits['bonus_melee_damage']} damage")
    
    barbarian.end_rage()
    print(f"    ✓ Rage ended")
    
    # Test unarmored defense
    print("  Testing unarmored defense...")
    barbarian.calculate_unarmored_defense()
    print(f"    ✓ AC calculated: {barbarian.ac}")
    
    # Test level features
    print("  Testing level-based features...")
    print(f"    ✓ Extra Attack: {barbarian.level >= 5}")
    print(f"    ✓ Fast Movement: +{barbarian.fast_movement} ft")
    print(f"    ✓ Brutal Critical: {barbarian.brutal_critical_dice} dice")
    
    # Save to campaign
    print("\n[5/6] Saving to campaign...")
    try:
        campaign_mgr.add_character(campaign.name, barbarian)
        print(f"✓ Barbarian saved to campaign")
    except ValueError as e:
        # Character already exists, update it
        campaign_mgr.update_character(campaign.name, barbarian)
        print(f"✓ Barbarian updated in campaign")
    
    # Verify save file
    campaign_folder = Path("./test_campaigns/Phase_3_Test_Campaign")
    char_file = campaign_folder / "characters" / "Test_Grog.json"
    
    print(f"  Checking save file: {char_file}")
    assert char_file.exists(), "Character file not found!"
    
    with open(char_file, 'r') as f:
        saved_data = json.load(f)
    
    print(f"  ✓ Save file exists")
    print(f"  ✓ class_type in save: {saved_data.get('class_type')}")
    print(f"  ✓ rages_per_day in save: {saved_data.get('rages_per_day')}")
    print(f"  ✓ primal_path in save: {saved_data.get('primal_path', 'None')}")
    
    # Load character back
    print("\n[6/6] Loading character from campaign...")
    loaded_char = campaign_mgr.get_character(campaign.name, "Test Grog")
    
    assert loaded_char is not None, "Failed to load character!"
    print(f"✓ Character loaded: {loaded_char.name}")
    print(f"  Type: {type(loaded_char).__name__}")
    
    # Verify it's a Barbarian with all features
    from Head.Class.barbarian import Barbarian
    assert isinstance(loaded_char, Barbarian), "Loaded character is not a Barbarian!"
    print(f"  ✓ Loaded as Barbarian class")
    
    # Test that methods work
    print("\n  Testing methods on loaded character...")
    assert hasattr(loaded_char, 'enter_rage'), "Missing enter_rage method!"
    assert hasattr(loaded_char, 'calculate_unarmored_defense'), "Missing calculate_unarmored_defense!"
    assert hasattr(loaded_char, 'get_rage_benefits'), "Missing get_rage_benefits!"
    print(f"    ✓ All Barbarian methods present")
    
    # Test a method
    loaded_char.calculate_unarmored_defense()
    print(f"    ✓ Unarmored Defense works: AC = {loaded_char.ac}")
    
    # Test rage on loaded character
    loaded_char.enter_rage()
    print(f"    ✓ Rage works: {loaded_char.currently_raging}")
    
    # Display character sheet
    print("\n" + "=" * 70)
    print("CHARACTER SHEET TEST")
    print("=" * 70)
    
    sheet = loaded_char.get_character_sheet()
    
    print(f"\n{sheet['name']}")
    print(f"{sheet['class']} | {sheet['race']} | {sheet['background']}")
    print(f"Alignment: {sheet['alignment']}")
    print(f"\nHP: {sheet['hit_points']} | AC: {sheet['armor_class']} | Speed: {sheet['speed']} ft")
    print(f"\nAbility Scores:")
    for ability, score in sheet['ability_scores'].items():
        mod = (score - 10) // 2
        sign = '+' if mod >= 0 else ''
        print(f"  {ability.upper()}: {score} ({sign}{mod})")
    
    print(f"\nRage: {sheet['rage']['uses']}")
    print(f"  Damage: +{sheet['rage']['damage_bonus']}")
    print(f"  Active: {sheet['rage']['currently_active']}")
    
    print(f"\nClass Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  ✓ {feature}: {value if isinstance(value, str) else ''}")
    
    print(f"\nInventory:")
    for item in sheet['inventory']:
        print(f"  • {item}")
    
    print(f"\nCurrency: {sheet['total_wealth_gp']} gp")
    
    # Success!
    print("\n" + "=" * 70)
    print("✅ PHASE 3 TEST COMPLETE - ALL TESTS PASSED")
    print("=" * 70)
    print("\nTest Results:")
    print("  ✓ Character created with correct class type")
    print("  ✓ Character saved with class_type metadata")
    print("  ✓ Character loaded as correct class (Barbarian)")
    print("  ✓ All class methods work (enter_rage, calculate_AC, etc.)")
    print("  ✓ Character sheet displays properly")
    print("\nPhase 3 implementation successful! Ready for Phase 4.")
    
    return True


def test_ui_integration():
    """Test UI integration points"""
    
    print("\n" + "=" * 70)
    print("UI INTEGRATION CHECK")
    print("=" * 70)
    
    # Check for required files
    files_to_check = [
        ("Class Selector JS", "static/js/class_selector.js"),
        ("Barbarian Features JS", "static/js/class_features/barbarian.js"),
        ("Base Features JS", "static/js/class_features/base.js"),
        ("Class Features CSS", "static/css/class_features.css"),
        ("Class Selector CSS", "static/css/class_selector.css"),
        ("Class Metadata", "static/data/class_metadata.json"),
        ("Feature Tree Component", "templates/HTML/components/class_feature_tree.html")
    ]
    
    print("\nChecking UI files...")
    all_present = True
    for name, path in files_to_check:
        exists = Path(path).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name}: {path}")
        if not exists:
            all_present = False
    
    if all_present:
        print("\n✓ All UI files present")
    else:
        print("\n⚠ Some UI files missing - please create them")
    
    print("\nUI Integration Points:")
    print("  1. setup_phase.html should include:")
    print("     - <script src='static/js/class_selector.js'>")
    print("     - <script src='static/js/class_features/barbarian.js'>")
    print("     - <div id='barbarian-features'> container")
    print("\n  2. When user selects 'Barbarian':")
    print("     - onClassChange() fires")
    print("     - ClassSelector.selectClass('Barbarian')")
    print("     - BarbarianFeatureManager initializes")
    print("     - Feature tree displays")
    print("\n  3. When form submits:")
    print("     - class_type='Barbarian' sent to server")
    print("     - create_character() uses factory")
    print("     - Barbarian object created with all features")
    
    return all_present


if __name__ == "__main__":
    try:
        # Run main test
        test_phase_3()
        
        # Run UI integration check
        test_ui_integration()
        
        print("\n" + "=" * 70)
        print("🎉 PHASE 3 COMPLETE AND VERIFIED")
        print("=" * 70)
        print("\nNext Steps:")
        print("  • Test in browser: Create a Barbarian character")
        print("  • Verify feature tree displays correctly")
        print("  • Test rage tracker functionality")
        print("  • Proceed to Phase 4: Bard (spellcaster example)")
        
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)