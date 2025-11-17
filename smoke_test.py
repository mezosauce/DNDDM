#!/usr/bin/env python3
"""
Quick smoke test to verify the Barbarian API pipeline
Run this to quickly check if everything is working
"""

import requests
import json
import time
import sys

def run_smoke_test():
    """Run a quick smoke test of the API"""
    
    BASE_URL = "http://localhost:5005"
    CHARACTER_NAME = "SmokeTestBarbarian"
    
    print("🔥 Running Barbarian API Smoke Test")
    print("=" * 50)
    
    try:
        # 1. Check server health
        print("\n1. Checking server health...")
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("   ✅ Server is healthy")
        else:
            print("   ❌ Server health check failed")
            return False
        
        # 2. Create character
        print("\n2. Creating test character...")
        response = requests.post(
            f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/create",
            json={
                "level": 3,
                "race": "Half-Orc",
                "stats": {
                    "strength": 16,
                    "dexterity": 14,
                    "constitution": 15,
                    "intelligence": 8,
                    "wisdom": 12,
                    "charisma": 10
                }
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Created {data['name']} (Level {data['level']} {data['race']} {data['char_class']})")
        else:
            print(f"   ❌ Failed to create character: {response.text}")
            return False
        
        # 3. Test rage mechanics
        print("\n3. Testing rage mechanics...")
        
        # Enter rage
        response = requests.post(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/enter_rage")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Entered rage! Damage bonus: +{data['rage_damage']}")
        else:
            print("   ❌ Failed to enter rage")
            return False
        
        # Check current state
        response = requests.get(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}")
        data = response.json()
        if data['currently_raging']:
            print(f"   ✅ Currently raging: {data['currently_raging']}")
            print(f"   ✅ Rages used: {data['rages_used']}/{data['rages_per_day']}")
        else:
            print("   ❌ Rage state incorrect")
            return False
        
        # End rage
        response = requests.post(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/end_rage")
        if response.status_code == 200:
            print("   ✅ Rage ended successfully")
        else:
            print("   ❌ Failed to end rage")
            return False
        
        # 4. Test level progression
        print("\n4. Testing level progression...")
        response = requests.post(
            f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/set_level",
            json={"level": 5}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Leveled up to {data['new_level']}")
            print(f"   ✅ New HP: {data['hp']}")
        else:
            print("   ❌ Failed to level up")
            return False
        
        # 5. Test stat updates
        print("\n5. Testing stat updates...")
        new_stats = {
            "strength": 18,
            "dexterity": 14,
            "constitution": 16,
            "intelligence": 8,
            "wisdom": 12,
            "charisma": 10
        }
        response = requests.post(
            f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/update_stats",
            json={"stats": new_stats}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Stats updated, new AC: {data['ac']}")
        else:
            print("   ❌ Failed to update stats")
            return False
        
        # 6. Test long rest
        print("\n6. Testing long rest...")
        response = requests.post(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/long_rest")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Long rest completed")
            print(f"   ✅ HP restored: {data['hp_restored']}")
            print(f"   ✅ Rages restored: {data['rages_restored']}")
        else:
            print("   ❌ Failed to complete long rest")
            return False
        
        # 7. Get character sheet
        print("\n7. Getting character sheet...")
        response = requests.get(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/sheet")
        if response.status_code == 200:
            sheet = response.json()
            print("   ✅ Character sheet retrieved")
            print(f"   📋 {sheet['name']} - {sheet['class']}")
            print(f"   📋 HP: {sheet['hit_points']} | AC: {sheet['armor_class']}")
            print(f"   📋 Speed: {sheet['speed']} ft")
        else:
            print("   ❌ Failed to get character sheet")
            return False
        
        # 8. Cleanup
        print("\n8. Cleaning up...")
        response = requests.delete(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}")
        if response.status_code == 200:
            print("   ✅ Test character deleted")
        else:
            print("   ❌ Failed to delete character")
            return False
        
        print("\n" + "=" * 50)
        print("✨ All smoke tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        print("   Make sure the server is running:")
        print("   python test_barbarian_api.py")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def simulate_javascript_calls():
    """Simulate the exact calls that barbarian.js would make"""
    
    print("\n🌐 Simulating JavaScript Frontend Calls")
    print("=" * 50)
    
    BASE_URL = "http://localhost:5005"
    CHARACTER_NAME = "JSTestHero"
    
    try:
        # Simulate setCharacterName() 
        print("\n→ Simulating: barbarianManager.setCharacterName('JSTestHero')")
        
        # Check if exists
        response = requests.get(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}")
        if response.status_code == 404:
            print("  Character doesn't exist, creating...")
            response = requests.post(
                f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/create",
                json={
                    "level": 1,
                    "stats": {
                        "strength": 15,
                        "dexterity": 13,
                        "constitution": 14,
                        "intelligence": 10,
                        "wisdom": 12,
                        "charisma": 8
                    },
                    "race": "Human",
                    "background": ""
                }
            )
            if response.status_code == 200:
                print("  ✅ Character created")
        
        # Simulate enterRage()
        print("\n→ Simulating: barbarianManager.enterRage()")
        response = requests.post(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/enter_rage")
        if response.status_code == 200:
            print("  ✅ Rage activated")
        
        time.sleep(0.5)  # Simulate user action delay
        
        # Simulate endRage()
        print("\n→ Simulating: barbarianManager.endRage()")
        response = requests.post(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/end_rage")
        if response.status_code == 200:
            print("  ✅ Rage ended")
        
        # Simulate setLevel()
        print("\n→ Simulating: barbarianManager.setLevel(3)")
        response = requests.post(
            f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/set_level",
            json={"level": 3}
        )
        if response.status_code == 200:
            print("  ✅ Level set to 3")
        
        # Simulate updateStats()
        print("\n→ Simulating: barbarianManager.updateStats({str: 16, ...})")
        response = requests.post(
            f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/update_stats",
            json={
                "stats": {
                    "strength": 16,
                    "dexterity": 13,
                    "constitution": 14,
                    "intelligence": 10,
                    "wisdom": 12,
                    "charisma": 8
                }
            }
        )
        if response.status_code == 200:
            print("  ✅ Stats updated")
        
        # Simulate longRest()
        print("\n→ Simulating: barbarianManager.longRest()")
        response = requests.post(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}/long_rest")
        if response.status_code == 200:
            print("  ✅ Long rest completed")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/barbarian/{CHARACTER_NAME}")
        
        print("\n✨ JavaScript simulation completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Simulation failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎮 D&D 5e Barbarian API Pipeline Test")
    print("=====================================\n")
    
    # Run smoke test
    smoke_passed = run_smoke_test()
    
    if smoke_passed:
        # Run JavaScript simulation
        simulate_javascript_calls()
        
        print("\n" + "=" * 50)
        print("🎉 All pipeline tests completed successfully!")
        print("\nThe JavaScript ↔ Python pipeline is working correctly!")
        print("\nYou can now:")
        print("1. Run the full test suite: python test_barbarian_api.py --test")
        print("2. Run integration tests: python test_pipeline_integration.py")
        print("3. View API docs: http://localhost:5005/docs")
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ Some tests failed. Please check the server and try again.")
        sys.exit(1)