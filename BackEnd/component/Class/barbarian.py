#!/usr/bin/env python3
"""
Barbarian Class - D&D 5e SRD Implementation
Derived from the base Character class with full Barbarian features
"""
import os
import pathlib
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional


from campaign_manager import Character


@dataclass
class Barbarian(Character):
    """
    Barbarian class implementation following D&D 5e SRD
    Inherits from Character and adds Barbarian-specific features
    """
    
    # Barbarian-specific attributes (all with defaults to avoid dataclass issues)
    primal_path: str = ""  # "Path of the Berserker" or "Path of the Totem Warrior"
    
    # Rage mechanics
    rages_per_day: int = 2  # Based on level
    rages_used: int = 0
    rage_damage: int = 2  # Based on level
    currently_raging: bool = False
    
    # Barbarian features
    unarmored_defense_active: bool = True  # AC = 10 + DEX + CON when no armor
    danger_sense_active: bool = False  # Level 2+
    reckless_attack_available: bool = False  # Level 2+
    fast_movement: int = 0  # Extra movement at level 5+
    feral_instinct: bool = False  # Level 7+
    brutal_critical_dice: int = 0  # Extra dice on crits (1 at 9th, 2 at 13th, 3 at 17th)
    relentless_rage_active: bool = False  # Level 11+
    relentless_rage_dc: int = 10  # DC for Constitution save
    persistent_rage: bool = False  # Level 15+
    indomitable_might: bool = False  # Level 18+
    primal_champion: bool = False  # Level 20
    
    # Path of the Berserker features
    frenzy_active: bool = False
    exhaustion_level: int = 0  # Track exhaustion (max 6)
    mindless_rage: bool = False  # Level 6 Berserker
    intimidating_presence_available: bool = False  # Level 10 Berserker
    retaliation_available: bool = False  # Level 14 Berserker
    
    # Path features unlocked at certain levels
    path_feature_3: bool = False
    path_feature_6: bool = False
    path_feature_10: bool = False
    path_feature_14: bool = False
    
    def __post_init__(self):
        """Initialize Barbarian with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Barbarian"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Barbarians typically have high STR and CON
            self.stats = {
                "strength": 15,
                "dexterity": 13,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8
            }
        
        # Set hit points based on level (1d12 per level)
        if self.level == 1:
            self.max_hp = 12 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Barbarians choose two from: Animal Handling, Athletics, Intimidation, 
            # Nature, Perception, and Survival
            self.skill_proficiencies = ["Athletics", "Perception"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        # Calculate AC using Unarmored Defense if no armor
        if self.unarmored_defense_active and self.ac == 10:
            self.calculate_unarmored_defense()
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
    def calculate_unarmored_defense(self):
        """Calculate AC using Unarmored Defense: 10 + DEX mod + CON mod"""
        if self.unarmored_defense_active:
            dex_mod = self._get_modifier("dexterity")
            con_mod = self._get_modifier("constitution")
            self.ac = 10 + dex_mod + con_mod
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Rage progression
        if self.level >= 1:
            self.rages_per_day = 2
            self.rage_damage = 2
        if self.level >= 3:
            self.rages_per_day = 3
        if self.level >= 6:
            self.rages_per_day = 4
        if self.level >= 12:
            self.rages_per_day = 5
        if self.level >= 17:
            self.rages_per_day = 6
        if self.level >= 20:
            self.rages_per_day = 999  # Unlimited
        
        # Rage damage progression
        if self.level >= 9:
            self.rage_damage = 3
        if self.level >= 16:
            self.rage_damage = 4
        
        # Class features by level
        if self.level >= 2:
            self.reckless_attack_available = True
            self.danger_sense_active = True
        
        if self.level >= 5:
            self.fast_movement = 10
        
        if self.level >= 7:
            self.feral_instinct = True
        
        if self.level >= 9:
            self.brutal_critical_dice = 1
        
        if self.level >= 11:
            self.relentless_rage_active = True
        
        if self.level >= 13:
            self.brutal_critical_dice = 2
        
        if self.level >= 15:
            self.persistent_rage = True
        
        if self.level >= 17:
            self.brutal_critical_dice = 3
        
        if self.level >= 18:
            self.indomitable_might = True
        
        if self.level >= 20:
            self.primal_champion = True
            # Primal Champion: STR and CON increase by 4, max becomes 24
            self.stats["strength"] = min(self.stats["strength"] + 4, 24)
            self.stats["constitution"] = min(self.stats["constitution"] + 4, 24)
            self.calculate_unarmored_defense()  # Recalculate AC
        
        # Path features
        if self.level >= 3:
            self.path_feature_3 = True
        if self.level >= 6:
            self.path_feature_6 = True
        if self.level >= 10:
            self.path_feature_10 = True
        if self.level >= 14:
            self.path_feature_14 = True
        
        # Path of the Berserker specific
        if self.primal_path == "Path of the Berserker":
            if self.level >= 6:
                self.mindless_rage = True
            if self.level >= 10:
                self.intimidating_presence_available = True
            if self.level >= 14:
                self.retaliation_available = True
    
    def enter_rage(self) -> bool:
        """
        Enter a rage if rages are available.
        Returns True if successful, False otherwise.
        """
        if self.rages_used >= self.rages_per_day:
            return False
        
        if self.currently_raging:
            return False
        
        self.currently_raging = True
        self.rages_used += 1
        return True
    
    def end_rage(self):
        """End current rage"""
        self.currently_raging = False
        
        # If Frenzy was active, gain exhaustion level
        if self.frenzy_active:
            self.frenzy_active = False
            self.gain_exhaustion(1)
    
    def long_rest(self):
        """Reset resources on long rest"""
        self.rages_used = 0
        self.currently_raging = False
        self.frenzy_active = False
        self.relentless_rage_dc = 10
        self.hp = self.max_hp
        # Note: Exhaustion doesn't reset on long rest
    
    def activate_frenzy(self) -> bool:
        """
        Activate Frenzy (Berserker Path, requires rage active)
        Allows bonus action melee attack each turn, but causes exhaustion after rage
        """
        if not self.currently_raging:
            return False
        
        if self.primal_path != "Path of the Berserker":
            return False
        
        if not self.path_feature_3:
            return False
        
        self.frenzy_active = True
        return True
    
    def gain_exhaustion(self, levels: int = 1):
        """Gain exhaustion levels (max 6, level 6 = death)"""
        self.exhaustion_level = min(self.exhaustion_level + levels, 6)
    
    def remove_exhaustion(self, levels: int = 1):
        """Remove exhaustion levels"""
        self.exhaustion_level = max(self.exhaustion_level - levels, 0)
    
    def relentless_rage_save(self) -> bool:
        """
        Make a DC 10+ Constitution save when dropping to 0 HP while raging.
        On success, drop to 1 HP instead.
        DC increases by 5 for each use, resets on rest.
        """
        if not self.relentless_rage_active:
            return False
        
        if not self.currently_raging:
            return False
        
        # Simulate Constitution save (would need dice roll in actual game)
        # For now, just track the DC
        con_save_bonus = self._get_modifier("constitution") + self.get_proficiency_bonus()
        
        # In actual implementation, would roll 1d20 + con_save_bonus vs self.relentless_rage_dc
        # For this implementation, we'll return True if possible and increase DC
        
        success = True  # Placeholder - would be actual dice roll
        
        if success:
            self.hp = 1
            self.relentless_rage_dc += 5
        
        return success
    
    def get_proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on level"""
        if self.level < 5:
            return 2
        elif self.level < 9:
            return 3
        elif self.level < 13:
            return 4
        elif self.level < 17:
            return 5
        else:
            return 6
    
    def intimidating_presence_dc(self) -> int:
        """
        Calculate DC for Intimidating Presence (Berserker Level 10)
        DC = 8 + proficiency bonus + Charisma modifier
        """
        return 8 + self.get_proficiency_bonus() + self._get_modifier("charisma")
    
    def get_rage_benefits(self) -> Dict[str, any]:
        """Get current rage benefits"""
        if not self.currently_raging:
            return {"active": False}
        
        return {
            "active": True,
            "advantage_on_str_checks": True,
            "advantage_on_str_saves": True,
            "bonus_melee_damage": self.rage_damage,
            "resistance_physical": ["bludgeoning", "piercing", "slashing"],
            "frenzy_active": self.frenzy_active,
            "cannot_cast_spells": True,
            "cannot_concentrate": True
        }
    
    def level_up(self):
        """Level up the barbarian"""
        self.level += 1
        
        # Increase HP (1d12 + CON mod per level, or 7 + CON mod average)
        hp_gain = 7 + self._get_modifier("constitution")
        self.max_hp += hp_gain
        self.hp += hp_gain
        
        # Reapply level-based features
        self.apply_level_features()
        
        # Recalculate AC if using Unarmored Defense
        if self.unarmored_defense_active:
            self.calculate_unarmored_defense()
    
    def get_character_sheet(self) -> Dict:
        """Generate a complete character sheet"""
        return {
            "name": self.name,
            "race": self.race,
            "class": f"{self.char_class} {self.level}",
            "background": self.background,
            "alignment": self.alignment,
            "primal_path": self.primal_path if self.primal_path else "Not chosen (Level 3+)",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": self.ac,
            "speed": 30 + self.fast_movement,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "strength": self._get_modifier("strength") + self.get_proficiency_bonus(),
                "constitution": self._get_modifier("constitution") + self.get_proficiency_bonus()
            },
            
            "skills": self.skill_proficiencies,
            "languages": self.languages_known,
            
            "rage": {
                "uses": f"{self.rages_used}/{self.rages_per_day}",
                "damage_bonus": self.rage_damage,
                "currently_active": self.currently_raging
            },
            
            "features": {
                "Unarmored Defense": True,
                "Reckless Attack": self.reckless_attack_available,
                "Danger Sense": self.danger_sense_active,
                "Fast Movement": f"+{self.fast_movement} ft" if self.fast_movement > 0 else False,
                "Feral Instinct": self.feral_instinct,
                "Brutal Critical": f"+{self.brutal_critical_dice} dice" if self.brutal_critical_dice > 0 else False,
                "Relentless Rage": self.relentless_rage_active,
                "Persistent Rage": self.persistent_rage,
                "Indomitable Might": self.indomitable_might,
                "Primal Champion": self.primal_champion
            },
            
            "inventory": self.inventory,
            "currency": self.currency,
            "total_wealth_gp": self.get_total_gold_value(),
            
            "personality": {
                "traits": self.personality_traits,
                "ideal": self.ideal,
                "bond": self.bond,
                "flaw": self.flaw
            },
            
            "notes": self.notes
        }
    
    def __str__(self) -> str:
        """String representation"""
        path_str = f" ({self.primal_path})" if self.primal_path else ""
        rage_str = f"Rages: {self.rages_used}/{self.rages_per_day}"
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{path_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac} | {rage_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Barbarian
    barbarian = Barbarian(
        name="Grog Strongjaw",
        race="Goliath",
        char_class="Barbarian",
        background="Outlander",
        level=1,
        stats={
            "strength": 17,
            "dexterity": 14,
            "constitution": 16,
            "intelligence": 8,
            "wisdom": 10,
            "charisma": 12
        },
        alignment="Chaotic Neutral",
        personality_traits=["I'm driven by wanderlust", "I place no stock in wealthy or well-mannered folk"],
        ideal="Freedom. Chains are meant to be broken",
        bond="My clan is the most important thing in my life",
        flaw="I am too enamored of ale, wine, and other intoxicants"
    )
    
    # Set starting equipment
    barbarian.inventory = ["Greataxe", "Handaxe", "Handaxe", "Explorer's Pack", "Javelin x4"]
    
    print("=" * 60)
    print("BARBARIAN CHARACTER SHEET")
    print("=" * 60)
    print(barbarian)
    print()
    
    # Display character sheet
    sheet = barbarian.get_character_sheet()
    print(f"Name: {sheet['name']}")
    print(f"Class: {sheet['class']}")
    print(f"Race: {sheet['race']}")
    print(f"Background: {sheet['background']}")
    print(f"Alignment: {sheet['alignment']}")
    print()
    
    print(f"HP: {sheet['hit_points']} | AC: {sheet['armor_class']} | Speed: {sheet['speed']} ft")
    print()
    
    print("Ability Scores:")
    for ability, score in sheet['ability_scores'].items():
        modifier = (score - 10) // 2
        sign = '+' if modifier >= 0 else ''
        print(f"  {ability.capitalize()}: {score} ({sign}{modifier})")
    print()
    
    print(f"Proficiency Bonus: +{sheet['proficiency_bonus']}")
    print()
    
    print("Rage:")
    print(f"  Uses: {sheet['rage']['uses']}")
    print(f"  Damage Bonus: +{sheet['rage']['damage_bonus']}")
    print(f"  Currently Active: {sheet['rage']['currently_active']}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    print("Equipment:")
    for item in barbarian.inventory:
        print(f"  • {item}")
    print()
    
    # Test rage mechanics
    print("=" * 60)
    print("TESTING RAGE MECHANICS")
    print("=" * 60)
    
    print("\nEntering rage...")
    if barbarian.enter_rage():
        print("✓ Rage activated!")
        benefits = barbarian.get_rage_benefits()
        print(f"  - Advantage on Strength checks: {benefits['advantage_on_str_checks']}")
        print(f"  - Bonus damage: +{benefits['bonus_melee_damage']}")
        print(f"  - Resistances: {', '.join(benefits['resistance_physical'])}")
    
    print("\nEnding rage...")
    barbarian.end_rage()
    print("✓ Rage ended")
    
    print(f"\nRages remaining: {barbarian.rages_per_day - barbarian.rages_used}/{barbarian.rages_per_day}")
    
    # Test leveling up
    print("\n" + "=" * 60)
    print("TESTING LEVEL UP")
    print("=" * 60)
    
    print(f"\nCurrent level: {barbarian.level}")
    print(f"Current HP: {barbarian.hp}/{barbarian.max_hp}")
    print(f"Current rages per day: {barbarian.rages_per_day}")
    
    barbarian.level_up()
    print(f"\nAfter level up:")
    print(f"New level: {barbarian.level}")
    print(f"New HP: {barbarian.hp}/{barbarian.max_hp}")
    print(f"Features unlocked: Reckless Attack, Danger Sense")
    
    # Level up to 3 to choose path
    barbarian.level_up()
    barbarian.primal_path = "Path of the Berserker"
    barbarian.apply_level_features()
    
    print(f"\nLevel {barbarian.level} - Primal Path chosen: {barbarian.primal_path}")
    print(f"Rages per day: {barbarian.rages_per_day}")
    print(f"New feature: Frenzy")
    
    print("\n" + "=" * 60)
    print(barbarian)
    print("=" * 60)