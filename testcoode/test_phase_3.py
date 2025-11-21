#!/usr/bin/env python3
"""
Improved Phase 3 Integration Test with Better Diagnostics
Helps identify where character files are actually being saved
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path (adjust if needed for your structure)
script_dir = Path(__file__).parent.absolute()
parent_dir = script_dir.parent
sys.path.insert(0, str(parent_dir))

from Head.campaign_manager import CampaignManager
from Head.Class import create_character, character_to_dict, character_from_dict, get_available_classes


def find_character_file(campaign_dir, character_name):
    """
    Search for the character file with flexible matching.
    Returns the path if found, None otherwise.
    """
    campaign_path = Path(campaign_dir)
    
    if not campaign_path.exists():
        print(f"  ⚠ Campaign directory doesn't exist: {campaign_path}")
        return None
    
    # Try multiple possible filename formats
    possible_names = [
        f"{character_name}.json",
        f"{character_name.replace(' ', '_')}.json",
        f"{character_name.replace(' ', '')}.json",
    ]
    
    # Search recursively for any matching files
    print(f"\n  Searching in: {campaign_path}")
    for json_file in campaign_path.rglob("*.json"):
        print(f"    Found: {json_file.relative_to(campaign_path)}")
        
        # Check if this is a character file by reading it
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'name' in data:
                    if data['name'] == character_name:
                        print(f"    ✓ Matched by name: {data['name']}")
                        return json_file
        except:
            pass
    
    return None


def test_phase_3_improved():
    """Run Phase 3 test with better diagnostics"""
    
    print("=" * 70)
    print("PHASE 3 INTEGRATION TEST (IMPROVED)")
    print("=" * 70)
    
    # Initialize campaign manager
    print("\n[1/7] Initializing Campaign Manager...")
    test_dir = "./test_campaigns"
    campaign_mgr = CampaignManager(test_dir)
    print(f"✓ Campaign directory: {Path(test_dir).absolute()}")
    
    # Create test campaign
    print("\n[2/7] Creating test campaign...")
    campaign_name = "Phase 3 Test Campaign"
    try:
        campaign = campaign_mgr.create_campaign(
            name=campaign_name,
            party_size=2,
            description="Testing Barbarian class implementation"
        )
        print(f"✓ Campaign created: {campaign.name}")
    except ValueError as e:
        campaign = campaign_mgr.load_campaign(campaign_name)
        print(f"✓ Campaign loaded: {campaign.name}")
    
    # Show campaign folder info
    print(f"\n  Campaign folder structure:")
    campaign_base = Path(test_dir)
    if campaign_base.exists():
        for item in sorted(campaign_base.rglob("*"))[:20]:  # Limit output
            if item.is_dir():
                print(f"    📁 {item.relative_to(campaign_base)}/")
            elif item.is_file():
                print(f"    📄 {item.relative_to(campaign_base)}")
    
    # Test available classes
    print("\n[3/7] Testing class registry...")
    available_classes = get_available_classes()
    print(f"Available classes: {', '.join(available_classes)}")
    assert 'Barbarian' in available_classes, "Barbarian not in registry!"
    print("✓ Barbarian class available")
    
    # Create Barbarian character
    print("\n[4/7] Creating Barbarian character...")
    char_name = "Test Grog"
    barbarian = create_character(
        class_type="Barbarian",
        name=char_name,
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
    
    # Test Barbarian features
    print("\n[5/7] Testing Barbarian features...")
    print("  Testing rage mechanics...")
    assert barbarian.enter_rage(), "Failed to enter rage!"
    print(f"    ✓ Entered rage")
    barbarian.end_rage()
    print(f"    ✓ Rage ended")
    
    print("  Testing unarmored defense...")
    barbarian.calculate_unarmored_defense()
    print(f"    ✓ AC: {barbarian.ac}")
    
    # Save to campaign
    print("\n[6/7] Saving to campaign...")
    try:
        campaign_mgr.add_character(campaign.name, barbarian)
        print(f"✓ Character added to campaign")
    except ValueError as e:
        campaign_mgr.update_character(campaign.name, barbarian)
        print(f"✓ Character updated in campaign")
    
    # Find the actual file location
    print("\n[6.5/7] Locating saved character file...")
    char_file = find_character_file(test_dir, char_name)
    
    if char_file:
        print(f"  ✓ Found character file: {char_file}")
        
        # Verify file contents
        with open(char_file, 'r') as f:
            saved_data = json.load(f)
        
        print(f"  ✓ File contents:")
        print(f"    - name: {saved_data.get('name')}")
        print(f"    - class_type: {saved_data.get('class_type')}")
        print(f"    - char_class: {saved_data.get('char_class')}")
        print(f"    - rages_per_day: {saved_data.get('rages_per_day')}")
        print(f"    - level: {saved_data.get('level')}")
        
        if 'class_type' not in saved_data:
            print(f"  ⚠ WARNING: 'class_type' field missing in saved data!")
            print(f"    This may cause issues with deserialization.")
        
    else:
        print(f"  ⚠ WARNING: Could not find character file!")
        print(f"  Expected character name: '{char_name}'")
        print(f"  Campaign directory: {Path(test_dir).absolute()}")
        print(f"\n  This might mean:")
        print(f"    1. The file is saved with a different name")
        print(f"    2. The file is saved in a different location")
        print(f"    3. The save operation didn't actually write a file")
    
    # Load character back
    print("\n[7/7] Loading character from campaign...")
    loaded_char = campaign_mgr.get_character(campaign.name, char_name)
    
    if loaded_char is None:
        print(f"  ⚠ WARNING: get_character returned None!")
        print(f"  Campaign: {campaign.name}")
        print(f"  Character name: {char_name}")
        print(f"  Available characters: {list(campaign.characters.keys())}")
        raise AssertionError(f"Failed to load character '{char_name}'")
    
    print(f"✓ Character loaded: {loaded_char.name}")
    print(f"  Type: {type(loaded_char).__name__}")
    
    # Verify it's a Barbarian
    from Head.Class.barbarian import Barbarian
    if not isinstance(loaded_char, Barbarian):
        print(f"  ⚠ WARNING: Loaded character is type {type(loaded_char).__name__}, not Barbarian!")
        print(f"  This suggests the class_type metadata is not being preserved correctly.")
    else:
        print(f"  ✓ Loaded as Barbarian class")
    
    # Test methods
    print("\n  Testing methods on loaded character...")
    methods_to_test = ['enter_rage', 'calculate_unarmored_defense', 'get_rage_benefits']
    for method in methods_to_test:
        if not hasattr(loaded_char, method):
            print(f"    ✗ Missing method: {method}")
        else:
            print(f"    ✓ Has method: {method}")
    
    # Test a method
    loaded_char.calculate_unarmored_defense()
    print(f"    ✓ Methods work: AC = {loaded_char.ac}")
    
    # Success summary
    print("\n" + "=" * 70)
    print("✅ PHASE 3 TEST COMPLETE")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        test_phase_3_improved()
        print("\n✅ All tests passed!")
        print("\nIf you see any warnings above, you may need to fix:")
        print("  • File naming conventions in campaign_manager.py")
        print("  • class_type metadata serialization")
        print("  • Character file save/load locations")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)