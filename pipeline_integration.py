#!/usr/bin/env python3
"""
Integration tests simulating JavaScript frontend behavior
Tests the complete pipeline between barbarian.js and barbarian.py
"""

import json
import asyncio
import aiohttp
import pytest
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Simulate JavaScript frontend behavior
@dataclass
class JavaScriptSimulator:
    """Simulates the JavaScript BarbarianFeatureManager behavior"""
    
    api_base: str = "http://localhost:5005"
    character_name: Optional[str] = None
    level: int = 1
    stats: Dict[str, int] = None
    rages_used: int = 0
    rages_per_day: int = 2
    rage_damage: int = 2
    currently_raging: bool = False
    
    def __post_init__(self):
        if self.stats is None:
            self.stats = {
                "strength": 15,
                "dexterity": 13,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8
            }
    
    async def make_request(self, session: aiohttp.ClientSession, method: str, endpoint: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request simulating JavaScript fetch()"""
        url = f"{self.api_base}{endpoint}"
        async with session.request(method, url, json=json_data) as response:
            return await response.json(), response.status
    
    async def set_character_name(self, session: aiohttp.ClientSession, name: str) -> bool:
        """Simulate setCharacterName() from JavaScript"""
        self.character_name = name
        
        # Check if character exists
        result, status = await self.make_request(
            session, "GET", f"/api/barbarian/{name}"
        )
        
        if status == 404:
            # Create character if not found (like JS does)
            result, status = await self.make_request(
                session, "POST", f"/api/barbarian/{name}/create",
                {
                    "level": self.level,
                    "stats": self.stats,
                    "race": "Human",
                    "background": ""
                }
            )
            return status == 200
        
        return True
    
    async def enter_rage(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Simulate enterRage() from JavaScript"""
        if not self.character_name:
            return {"error": "No character set"}
        
        # Optimistically update UI state (like JS does)
        if self.rages_used < self.rages_per_day and not self.currently_raging:
            self.currently_raging = True
            self.rages_used += 1
        
        # Send to backend
        result, status = await self.make_request(
            session, "POST", f"/api/barbarian/{self.character_name}/enter_rage"
        )
        
        if status != 200:
            # Rollback optimistic update
            self.currently_raging = False
            self.rages_used -= 1
        
        return result
    
    async def end_rage(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Simulate endRage() from JavaScript"""
        if not self.character_name:
            return {"error": "No character set"}
        
        self.currently_raging = False
        
        result, status = await self.make_request(
            session, "POST", f"/api/barbarian/{self.character_name}/end_rage"
        )
        
        return result
    
    async def long_rest(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Simulate longRest() from JavaScript"""
        if not self.character_name:
            return {"error": "No character set"}
        
        # Optimistic update
        self.rages_used = 0
        self.currently_raging = False
        
        result, status = await self.make_request(
            session, "POST", f"/api/barbarian/{self.character_name}/long_rest"
        )
        
        return result
    
    async def update_stats(self, session: aiohttp.ClientSession, stats: Dict[str, int]) -> Dict[str, Any]:
        """Simulate updateStats() from JavaScript"""
        if not self.character_name:
            return {"error": "No character set"}
        
        self.stats = stats
        
        result, status = await self.make_request(
            session, "POST", f"/api/barbarian/{self.character_name}/update_stats",
            {"stats": stats}
        )
        
        return result
    
    async def set_level(self, session: aiohttp.ClientSession, level: int) -> Dict[str, Any]:
        """Simulate setLevel() from JavaScript"""
        if not self.character_name:
            return {"error": "No character set"}
        
        self.level = level
        self.update_rage_progression()
        
        result, status = await self.make_request(
            session, "POST", f"/api/barbarian/{self.character_name}/set_level",
            {"level": level}
        )
        
        return result
    
    def update_rage_progression(self):
        """Simulate updateRageProgression() from JavaScript"""
        if self.level >= 20:
            self.rages_per_day = 999
        elif self.level >= 17:
            self.rages_per_day = 6
        elif self.level >= 12:
            self.rages_per_day = 5
        elif self.level >= 6:
            self.rages_per_day = 4
        elif self.level >= 3:
            self.rages_per_day = 3
        else:
            self.rages_per_day = 2
        
        if self.level >= 16:
            self.rage_damage = 4
        elif self.level >= 9:
            self.rage_damage = 3
        else:
            self.rage_damage = 2
    
    def calculate_unarmored_defense(self) -> int:
        """Simulate calculateUnarmoredDefense() from JavaScript"""
        dex_mod = (self.stats["dexterity"] - 10) // 2
        con_mod = (self.stats["constitution"] - 10) // 2
        return 10 + dex_mod + con_mod


# Integration test cases
class TestJavaScriptPythonIntegration:
    """Test the complete pipeline between JavaScript and Python"""
    
    @pytest.fixture
    async def session(self):
        """Create aiohttp session for tests"""
        async with aiohttp.ClientSession() as session:
            yield session
    
    @pytest.fixture
    def js_simulator(self):
        """Create JavaScript simulator"""
        return JavaScriptSimulator()
    
    @pytest.mark.asyncio
    async def test_initial_character_creation_flow(self, session, js_simulator):
        """Test the initial character creation flow from JavaScript"""
        # Simulate user entering character name in UI
        success = await js_simulator.set_character_name(session, "IntegrationTestHero")
        assert success == True
        assert js_simulator.character_name == "IntegrationTestHero"
    
    @pytest.mark.asyncio
    async def test_combat_rage_flow(self, session, js_simulator):
        """Test a combat scenario with rage mechanics"""
        # Setup character
        await js_simulator.set_character_name(session, "CombatTestHero")
        
        # Enter combat - activate rage
        rage_result = await js_simulator.enter_rage(session)
        assert rage_result.get("success") == True
        assert js_simulator.currently_raging == True
        assert js_simulator.rages_used == 1
        
        # Combat ends - end rage
        end_result = await js_simulator.end_rage(session)
        assert end_result.get("success") == True
        assert js_simulator.currently_raging == False
        
        # Second combat
        rage_result = await js_simulator.enter_rage(session)
        assert rage_result.get("success") == True
        
        # Try to rage again while already raging (should fail)
        rage_result = await js_simulator.enter_rage(session)
        # JS simulator prevents this optimistically
        assert js_simulator.rages_used == 2  # Should not increase
    
    @pytest.mark.asyncio
    async def test_level_progression_flow(self, session, js_simulator):
        """Test character leveling up through JavaScript"""
        await js_simulator.set_character_name(session, "LevelTestHero")
        
        # Start at level 1
        assert js_simulator.level == 1
        assert js_simulator.rages_per_day == 2
        assert js_simulator.rage_damage == 2
        
        # Level up to 3 (gain subclass)
        result = await js_simulator.set_level(session, 3)
        assert result.get("success") == True
        assert js_simulator.level == 3
        assert js_simulator.rages_per_day == 3
        
        # Level up to 9 (brutal critical)
        result = await js_simulator.set_level(session, 9)
        assert js_simulator.level == 9
        assert js_simulator.rage_damage == 3
        
        # Level up to 20 (unlimited rages)
        result = await js_simulator.set_level(session, 20)
        assert js_simulator.level == 20
        assert js_simulator.rages_per_day == 999
    
    @pytest.mark.asyncio
    async def test_stat_update_ac_calculation(self, session, js_simulator):
        """Test stat updates and AC recalculation"""
        await js_simulator.set_character_name(session, "StatTestHero")
        
        # Calculate initial AC
        initial_ac = js_simulator.calculate_unarmored_defense()
        assert initial_ac == 12  # 10 + 1 (DEX 13) + 1 (CON 14)
        
        # Update stats
        new_stats = {
            "strength": 18,
            "dexterity": 16,
            "constitution": 16,
            "intelligence": 8,
            "wisdom": 12,
            "charisma": 10
        }
        
        result = await js_simulator.update_stats(session, new_stats)
        assert result.get("success") == True
        
        # Check new AC calculation
        new_ac = js_simulator.calculate_unarmored_defense()
        assert new_ac == 16  # 10 + 3 (DEX 16) + 3 (CON 16)
    
    @pytest.mark.asyncio
    async def test_rest_mechanics(self, session, js_simulator):
        """Test long rest resource restoration"""
        await js_simulator.set_character_name(session, "RestTestHero")
        
        # Use all rages
        await js_simulator.enter_rage(session)
        await js_simulator.end_rage(session)
        await js_simulator.enter_rage(session)
        await js_simulator.end_rage(session)
        
        assert js_simulator.rages_used == 2
        
        # Long rest
        result = await js_simulator.long_rest(session)
        assert result.get("success") == True
        assert js_simulator.rages_used == 0
        assert js_simulator.currently_raging == False
    
    @pytest.mark.asyncio
    async def test_error_handling_flow(self, session, js_simulator):
        """Test error handling between JavaScript and Python"""
        # Try to perform actions without setting character
        result = await js_simulator.enter_rage(session)
        assert result.get("error") == "No character set"
        
        # Set character
        await js_simulator.set_character_name(session, "ErrorTestHero")
        
        # Use all rages
        await js_simulator.enter_rage(session)
        await js_simulator.end_rage(session)
        await js_simulator.enter_rage(session)
        await js_simulator.end_rage(session)
        
        # Try to rage with no rages left
        # JS prevents this optimistically
        initial_rages = js_simulator.rages_used
        result = await js_simulator.enter_rage(session)
        # Should not increase due to optimistic prevention
        assert js_simulator.rages_used == initial_rages
    
    @pytest.mark.asyncio
    async def test_concurrent_updates(self, session):
        """Test handling concurrent updates from multiple 'tabs'"""
        # Simulate two browser tabs with same character
        tab1 = JavaScriptSimulator()
        tab2 = JavaScriptSimulator()
        
        # Both tabs load the same character
        await tab1.set_character_name(session, "ConcurrentTestHero")
        await tab2.set_character_name(session, "ConcurrentTestHero")
        
        # Tab 1 enters rage
        result1 = await tab1.enter_rage(session)
        assert result1.get("success") == True
        
        # Tab 2 tries to enter rage (should fail - already raging)
        result2 = await tab2.enter_rage(session)
        # Backend should reject this
        assert result2.get("detail") is not None
    
    @pytest.mark.asyncio  
    async def test_full_gameplay_session(self, session, js_simulator):
        """Test a complete gameplay session flow"""
        # Player creates character
        await js_simulator.set_character_name(session, "GameplayHero")
        
        # First combat encounter
        await js_simulator.enter_rage(session)
        # Combat ends
        await js_simulator.end_rage(session)
        
        # Level up after combat
        await js_simulator.set_level(session, 2)
        
        # Update stats (ability score improvement simulation)
        new_stats = js_simulator.stats.copy()
        new_stats["strength"] += 2
        await js_simulator.update_stats(session, new_stats)
        
        # Second combat
        await js_simulator.enter_rage(session)
        await js_simulator.end_rage(session)
        
        # Out of rages - need rest
        assert js_simulator.rages_used == 2
        
        # Long rest before next adventuring day
        await js_simulator.long_rest(session)
        assert js_simulator.rages_used == 0
        
        # Ready for next day
        await js_simulator.enter_rage(session)
        assert js_simulator.currently_raging == True


class TestMetadataIntegration:
    """Test integration with class_metadata.json"""
    
    def test_metadata_loading(self):
        """Test loading and parsing class metadata"""
        # In real scenario, this would load from the JSON file
        metadata = {
            "Barbarian": {
                "hit_die": "d12",
                "primary_abilities": ["Strength", "Constitution"],
                "features_by_level": {
                    "1": ["Rage", "Unarmored Defense"],
                    "2": ["Reckless Attack", "Danger Sense"],
                    "3": ["Primal Path"]
                }
            }
        }
        
        barbarian_meta = metadata["Barbarian"]
        assert barbarian_meta["hit_die"] == "d12"
        assert "Strength" in barbarian_meta["primary_abilities"]
        assert "Rage" in barbarian_meta["features_by_level"]["1"]
    
    def test_feature_unlock_by_level(self):
        """Test that features unlock at correct levels per metadata"""
        features_by_level = {
            1: ["Rage", "Unarmored Defense"],
            2: ["Reckless Attack", "Danger Sense"],
            3: ["Primal Path"],
            5: ["Extra Attack", "Fast Movement"],
            7: ["Feral Instinct"],
            9: ["Brutal Critical (1 die)"],
            11: ["Relentless Rage"],
            15: ["Persistent Rage"],
            20: ["Primal Champion"]
        }
        
        # Test feature availability at different levels
        def get_features_at_level(level):
            available = []
            for req_level, features in features_by_level.items():
                if level >= req_level:
                    available.extend(features)
            return available
        
        # Level 1 barbarian
        lvl1_features = get_features_at_level(1)
        assert "Rage" in lvl1_features
        assert "Unarmored Defense" in lvl1_features
        assert "Reckless Attack" not in lvl1_features
        
        # Level 5 barbarian
        lvl5_features = get_features_at_level(5)
        assert "Extra Attack" in lvl5_features
        assert "Fast Movement" in lvl5_features
        assert "Relentless Rage" not in lvl5_features
        
        # Level 20 barbarian
        lvl20_features = get_features_at_level(20)
        assert "Primal Champion" in lvl20_features
        assert len(lvl20_features) == sum(len(f) for f in features_by_level.values())


# Performance test for pipeline
class TestPerformance:
    """Test performance of the JavaScript-Python pipeline"""
    
    @pytest.mark.asyncio
    async def test_rapid_state_changes(self, session):
        """Test rapid state changes like in actual gameplay"""
        import time
        
        js = JavaScriptSimulator()
        await js.set_character_name(session, "PerformanceHero")
        
        start_time = time.time()
        
        # Simulate rapid combat actions
        for _ in range(5):
            await js.enter_rage(session)
            await js.end_rage(session)
            await js.long_rest(session)  # Reset for next iteration
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time (< 2 seconds for 15 requests)
        assert elapsed < 2.0, f"Pipeline too slow: {elapsed:.2f}s"
        
        # Verify state consistency
        assert js.rages_used == 0  # Should be reset after last rest
        assert js.currently_raging == False


if __name__ == "__main__":
    import sys
    
    if "--integration" in sys.argv:
        # Run integration tests
        print("Running JavaScript-Python integration tests...")
        print("Make sure the FastAPI server is running on http://localhost:5005")
        print("Run: python test_barbarian_api.py")
        pytest.main([__file__, "-v", "--tb=short", "-k", "Integration"])
    elif "--performance" in sys.argv:
        # Run performance tests
        print("Running performance tests...")
        pytest.main([__file__, "-v", "--tb=short", "-k", "Performance"])
    else:
        # Run all tests
        print("Running all pipeline tests...")
        print("Make sure the FastAPI server is running on http://localhost:5005")
        pytest.main([__file__, "-v", "--tb=short"])