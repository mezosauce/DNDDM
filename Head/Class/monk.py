#!/usr/bin/env python3
"""
Monk Class - D&D 5e SRD Implementation
Derived from the base Character class with full Monk features
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional


from Head.campaign_manager import Character


@dataclass
class Monk(Character):
    """
    Monk class implementation following D&D 5e SRD
    Inherits from Character and adds Monk-specific features
    """
    
    # Monk-specific attributes
    monastic_tradition: str = ""  # "Way of the Open Hand", "Way of Shadow", "Way of the Four Elements"
    
    # Ki mechanics
    ki_points: int = 0
    ki_points_max: int = 0
    ki_save_dc: int = 0
    
    # Martial Arts
    martial_arts_die: int = 4  # d4 at level 1, progresses per table
    martial_arts_active: bool = True
    
    # Movement and defense
    unarmored_movement: int = 0  # Bonus movement speed
    unarmored_defense_active: bool = True  # AC = 10 + DEX + WIS when no armor
    
    # Class features by level
    deflect_missiles_available: bool = False  # Level 3+
    slow_fall_available: bool = False  # Level 4+
    extra_attack: bool = False  # Level 5+
    stunning_strike_available: bool = False  # Level 5+
    ki_empowered_strikes: bool = False  # Level 6+
    evasion_available: bool = False  # Level 7+
    stillness_of_mind_available: bool = False  # Level 7+
    purity_of_body: bool = False  # Level 10+
    tongue_of_sun_moon: bool = False  # Level 13+
    diamond_soul: bool = False  # Level 14+
    timeless_body: bool = False  # Level 15+
    empty_body_available: bool = False  # Level 18+
    perfect_self: bool = False  # Level 20
    
    # Movement improvements
    can_move_vertically: bool = False  # Level 9+ unarmored movement
    can_move_on_liquid: bool = False  # Level 9+ unarmored movement
    
    # Tradition features unlocked at certain levels
    tradition_feature_3: bool = False
    tradition_feature_6: bool = False
    tradition_feature_11: bool = False
    tradition_feature_17: bool = False
    
    # Way of the Open Hand features
    open_hand_technique: bool = False
    wholeness_of_body_available: bool = False
    tranquility_active: bool = False
    quivering_palm_active: bool = False
    quivering_palm_target: str = ""  # Name of creature affected by quivering palm
    
    def __post_init__(self):
        """Initialize Monk with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Monk"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Monks typically have high DEX and WIS
            self.stats = {
                "strength": 10,
                "dexterity": 16,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 15,
                "charisma": 8
            }
        
        # Set hit points based on level (1d8 per level)
        if self.level == 1:
            self.max_hp = 8 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Monks choose two from: Acrobatics, Athletics, History, Insight, Religion, Stealth
            self.skill_proficiencies = ["Acrobatics", "Insight"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        # Set initial equipment if empty
        if not self.inventory:
            self.inventory = ["Shortsword", "Explorer's Pack", "Dart x10"]
        
        # Calculate AC using Unarmored Defense if no armor
        if self.unarmored_defense_active and self.ac == 10:
            self.calculate_unarmored_defense()
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
    def calculate_unarmored_defense(self):
        """Calculate AC using Unarmored Defense: 10 + DEX mod + WIS mod"""
        if self.unarmored_defense_active:
            dex_mod = self._get_modifier("dexterity")
            wis_mod = self._get_modifier("wisdom")
            self.ac = 10 + dex_mod + wis_mod
    
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
    
    def calculate_ki_save_dc(self):
        """Calculate Ki save DC: 8 + proficiency bonus + Wisdom modifier"""
        self.ki_save_dc = 8 + self.get_proficiency_bonus() + self._get_modifier("wisdom")
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Ki points progression
        if self.level >= 1:
            self.ki_points_max = 0
        if self.level >= 2:
            self.ki_points_max = 2
        if self.level >= 3:
            self.ki_points_max = 3
        if self.level >= 4:
            self.ki_points_max = 4
        if self.level >= 5:
            self.ki_points_max = 5
        if self.level >= 6:
            self.ki_points_max = 6
        if self.level >= 7:
            self.ki_points_max = 7
        if self.level >= 8:
            self.ki_points_max = 8
        if self.level >= 9:
            self.ki_points_max = 9
        if self.level >= 10:
            self.ki_points_max = 10
        if self.level >= 11:
            self.ki_points_max = 11
        if self.level >= 12:
            self.ki_points_max = 12
        if self.level >= 13:
            self.ki_points_max = 13
        if self.level >= 14:
            self.ki_points_max = 14
        if self.level >= 15:
            self.ki_points_max = 15
        if self.level >= 16:
            self.ki_points_max = 16
        if self.level >= 17:
            self.ki_points_max = 17
        if self.level >= 18:
            self.ki_points_max = 18
        if self.level >= 19:
            self.ki_points_max = 19
        if self.level >= 20:
            self.ki_points_max = 20
        
        # Martial Arts die progression
        if self.level >= 1:
            self.martial_arts_die = 4
        if self.level >= 5:
            self.martial_arts_die = 6
        if self.level >= 11:
            self.martial_arts_die = 8
        if self.level >= 17:
            self.martial_arts_die = 10
        
        # Unarmored Movement progression
        if self.level >= 2:
            self.unarmored_movement = 10
        if self.level >= 6:
            self.unarmored_movement = 15
        if self.level >= 10:
            self.unarmored_movement = 20
        if self.level >= 14:
            self.unarmored_movement = 25
        if self.level >= 18:
            self.unarmored_movement = 30
        
        # Class features by level
        if self.level >= 2:
            self.calculate_ki_save_dc()
        
        if self.level >= 3:
            self.deflect_missiles_available = True
        
        if self.level >= 4:
            self.slow_fall_available = True
        
        if self.level >= 5:
            self.extra_attack = True
            self.stunning_strike_available = True
        
        if self.level >= 6:
            self.ki_empowered_strikes = True
        
        if self.level >= 7:
            self.evasion_available = True
            self.stillness_of_mind_available = True
        
        if self.level >= 9:
            self.can_move_vertically = True
            self.can_move_on_liquid = True
        
        if self.level >= 10:
            self.purity_of_body = True
        
        if self.level >= 13:
            self.tongue_of_sun_moon = True
        
        if self.level >= 14:
            self.diamond_soul = True
        
        if self.level >= 15:
            self.timeless_body = True
        
        if self.level >= 18:
            self.empty_body_available = True
        
        if self.level >= 20:
            self.perfect_self = True
        
        # Tradition features
        if self.level >= 3:
            self.tradition_feature_3 = True
        if self.level >= 6:
            self.tradition_feature_6 = True
        if self.level >= 11:
            self.tradition_feature_11 = True
        if self.level >= 17:
            self.tradition_feature_17 = True
        
        # Way of the Open Hand specific
        if self.monastic_tradition == "Way of the Open Hand":
            if self.level >= 3:
                self.open_hand_technique = True
            if self.level >= 6:
                self.wholeness_of_body_available = True
            if self.level >= 11:
                self.tranquility_active = True
            if self.level >= 17:
                self.quivering_palm_active = True
    
    def short_rest(self):
        """Regain Ki points on short rest (30+ minutes meditating)"""
        self.ki_points = self.ki_points_max
    
    def long_rest(self):
        """Reset resources on long rest"""
        self.ki_points = self.ki_points_max
        self.hp = self.max_hp
        # Reset Wholeness of Body and other daily abilities
        if self.wholeness_of_body_available:
            # This would be tracked separately in a full implementation
            pass
    
    def use_ki_point(self, cost: int = 1) -> bool:
        """
        Spend ki points if available.
        Returns True if successful, False otherwise.
        """
        if self.ki_points >= cost:
            self.ki_points -= cost
            return True
        return False
    
    def flurry_of_blows(self) -> bool:
        """
        Use Flurry of Blows (1 ki point)
        Make two unarmed strikes as a bonus action after Attack action
        Returns True if successful, False otherwise
        """
        if self.use_ki_point(1):
            return True
        return False
    
    def patient_defense(self) -> bool:
        """
        Use Patient Defense (1 ki point)
        Take Dodge action as a bonus action
        Returns True if successful, False otherwise
        """
        if self.use_ki_point(1):
            return True
        return False
    
    def step_of_the_wind(self) -> bool:
        """
        Use Step of the Wind (1 ki point)
        Take Disengage or Dash as bonus action, double jump distance
        Returns True if successful, False otherwise
        """
        if self.use_ki_point(1):
            return True
        return False
    
    def stunning_strike(self) -> bool:
        """
        Use Stunning Strike (1 ki point)
        When hitting with melee weapon attack, target must make CON save or be stunned
        Returns True if ki point spent, False otherwise
        """
        if self.use_ki_point(1):
            return True
        return False
    
    def deflect_missiles(self, damage: int) -> int:
        """
        Deflect Missiles reaction
        Reduce ranged weapon attack damage by 1d10 + DEX mod + monk level
        Return remaining damage after reduction
        """
        if not self.deflect_missiles_available:
            return damage
        
        # Calculate reduction (1d10 + DEX + monk level)
        # For simulation, we'll use average of 5.5 for d10
        reduction = 5 + self._get_modifier("dexterity") + self.level
        remaining_damage = max(0, damage - reduction)
        
        return remaining_damage
    
    def catch_missile(self, damage: int) -> bool:
        """
        If Deflect Missiles reduces damage to 0, can catch missile
        Returns True if missile can be caught, False otherwise
        """
        if not self.deflect_missiles_available:
            return False
        
        reduction = 5 + self._get_modifier("dexterity") + self.level
        return damage <= reduction
    
    def slow_fall(self, fall_distance: int) -> int:
        """
        Reduce falling damage using Slow Fall reaction
        Reduce damage by 5 x monk level
        Return remaining damage after reduction
        """
        if not self.slow_fall_available:
            return min(fall_distance, 20) * 10  # Normal falling damage: 1d6 per 10ft, max 20d6
        
        reduction = 5 * self.level
        normal_damage = min(fall_distance, 20) * 10  # Using average of 3.5 per d6 ≈ 3.5*20=70 max
        remaining_damage = max(0, normal_damage - reduction)
        
        return remaining_damage
    
    def wholeness_of_body(self) -> int:
        """
        Use Wholeness of Body (Open Hand Level 6)
        Heal for 3 x monk level
        Returns amount healed
        """
        if not self.wholeness_of_body_available:
            return 0
        
        if self.monastic_tradition != "Way of the Open Hand":
            return 0
        
        # Can only use once per long rest
        # For simplicity, we'll assume it's available
        healing = 3 * self.level
        self.hp = min(self.max_hp, self.hp + healing)
        
        return healing
    
    def apply_open_hand_technique(self, effect: str) -> Dict:
        """
        Apply Open Hand Technique effects after Flurry of Blows
        effect: "prone", "push", or "no_reactions"
        Returns effect details
        """
        if not self.open_hand_technique:
            return {}
        
        effects = {
            "prone": {
                "save": "Dexterity",
                "effect": "knocked prone"
            },
            "push": {
                "save": "Strength", 
                "effect": "pushed 15 feet away"
            },
            "no_reactions": {
                "save": None,
                "effect": "cannot take reactions until end of your next turn"
            }
        }
        
        return effects.get(effect, {})
    
    def activate_empty_body(self) -> bool:
        """
        Activate Empty Body (Level 18)
        Spend 4 ki points to become invisible and gain resistance to all damage except force
        Returns True if successful, False otherwise
        """
        if not self.empty_body_available:
            return False
        
        if self.ki_points < 4:
            return False
        
        self.use_ki_point(4)
        return True
    
    def activate_quivering_palm(self) -> bool:
        """
        Activate Quivering Palm (Open Hand Level 17)
        Spend 3 ki points on hit to set up vibrations
        Returns True if successful, False otherwise
        """
        if not self.quivering_palm_active:
            return False
        
        if self.ki_points < 3:
            return False
        
        self.use_ki_point(3)
        return True
    
    def trigger_quivering_palm(self, target_name: str) -> Dict:
        """
        Trigger Quivering Palm vibrations
        Target makes CON save or drops to 0 HP, or takes 10d10 necrotic on success
        Returns damage and effect information
        """
        if not self.quivering_palm_active:
            return {"success": False, "message": "Quivering Palm not available"}
        
        self.quivering_palm_target = target_name
        
        # Simulate the effect (would need actual dice rolls in game)
        # For simulation, return the possible outcomes
        return {
            "success": True,
            "target": target_name,
            "save_dc": self.ki_save_dc,
            "save_type": "Constitution",
            "on_fail": "dropped to 0 HP",
            "on_success": "10d10 necrotic damage",
            "duration_days": self.level
        }
    
    def level_up(self):
        """Level up the monk"""
        self.level += 1
        
        # Increase HP (1d8 + CON mod per level, or 5 + CON mod average)
        hp_gain = 5 + self._get_modifier("constitution")
        self.max_hp += hp_gain
        self.hp += hp_gain
        
        # Reapply level-based features
        self.apply_level_features()
        
        # Recalculate AC if using Unarmored Defense
        if self.unarmored_defense_active:
            self.calculate_unarmored_defense()
        
        # Recalculate Ki save DC
        self.calculate_ki_save_dc()
        
        # Refill ki points on level up
        self.ki_points = self.ki_points_max
    
    def get_character_sheet(self) -> Dict:
        """Generate a complete character sheet"""
        return {
            "name": self.name,
            "race": self.race,
            "class": f"{self.char_class} {self.level}",
            "background": self.background,
            "alignment": self.alignment,
            "monastic_tradition": self.monastic_tradition if self.monastic_tradition else "Not chosen (Level 3+)",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": self.ac,
            "speed": 30 + self.unarmored_movement,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "strength": self._get_modifier("strength") + self.get_proficiency_bonus(),
                "dexterity": self._get_modifier("dexterity") + self.get_proficiency_bonus()
            },
            
            "skills": self.skill_proficiencies,
            "languages": self.languages_known,
            
            "ki": {
                "points": f"{self.ki_points}/{self.ki_points_max}",
                "save_dc": self.ki_save_dc,
                "martial_arts_die": f"d{self.martial_arts_die}"
            },
            
            "features": {
                "Unarmored Defense": True,
                "Martial Arts": f"d{self.martial_arts_die}",
                "Ki": self.ki_points_max > 0,
                "Unarmored Movement": f"+{self.unarmored_movement} ft",
                "Deflect Missiles": self.deflect_missiles_available,
                "Slow Fall": self.slow_fall_available,
                "Extra Attack": self.extra_attack,
                "Stunning Strike": self.stunning_strike_available,
                "Ki-Empowered Strikes": self.ki_empowered_strikes,
                "Evasion": self.evasion_available,
                "Stillness of Mind": self.stillness_of_mind_available,
                "Purity of Body": self.purity_of_body,
                "Tongue of the Sun and Moon": self.tongue_of_sun_moon,
                "Diamond Soul": self.diamond_soul,
                "Timeless Body": self.timeless_body,
                "Empty Body": self.empty_body_available,
                "Perfect Self": self.perfect_self
            },
            
            "movement_abilities": {
                "vertical_surfaces": self.can_move_vertically,
                "liquid_surfaces": self.can_move_on_liquid
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
        tradition_str = f" ({self.monastic_tradition})" if self.monastic_tradition else ""
        ki_str = f"Ki: {self.ki_points}/{self.ki_points_max}"
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{tradition_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac} | {ki_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Monk
    monk = Monk(
        name="Li Mei",
        race="Human",
        char_class="Monk",
        background="Hermit",
        level=1,
        stats={
            "strength": 10,
            "dexterity": 16,
            "constitution": 14,
            "intelligence": 12,
            "wisdom": 16,
            "charisma": 8
        },
        alignment="Lawful Neutral",
        personality_traits=["I feel tremendous empathy for all who suffer", "I'm slow to trust those who follow other gods"],
        ideal="Greater Good. It is each person's responsibility to make the most happiness for the whole tribe.",
        bond="I entered seclusion to hide from the ones who might still be hunting me. I must someday confront them.",
        flaw="I am dogmatic in my thoughts and philosophy."
    )
    
    print("=" * 60)
    print("MONK CHARACTER SHEET")
    print("=" * 60)
    print(monk)
    print()
    
    # Display character sheet
    sheet = monk.get_character_sheet()
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
    
    print("Ki:")
    print(f"  Points: {sheet['ki']['points']}")
    print(f"  Save DC: {sheet['ki']['save_dc']}")
    print(f"  Martial Arts Die: d{sheet['ki']['martial_arts_die']}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    print("Equipment:")
    for item in monk.inventory:
        print(f"  • {item}")
    print()
    
    # Test Ki mechanics
    print("=" * 60)
    print("TESTING KI MECHANICS")
    print("=" * 60)
    
    # Level up to get Ki points
    monk.level_up()  # Level 2
    monk.level_up()  # Level 3
    monk.monastic_tradition = "Way of the Open Hand"
    monk.apply_level_features()
    
    print(f"\nLevel {monk.level} - Monastic Tradition chosen: {monk.monastic_tradition}")
    print(f"Ki points: {monk.ki_points}/{monk.ki_points_max}")
    print(f"Martial Arts die: d{monk.martial_arts_die}")
    print(f"Unarmored Movement: +{monk.unarmored_movement} ft")
    print()
    
    print("Testing Flurry of Blows...")
    if monk.flurry_of_blows():
        print("✓ Flurry of Blows activated! (Two unarmed strikes as bonus action)")
    print(f"Ki points remaining: {monk.ki_points}")
    print()
    
    print("Testing Patient Defense...")
    if monk.patient_defense():
        print("✓ Patient Defense activated! (Dodge as bonus action)")
    print(f"Ki points remaining: {monk.ki_points}")
    print()
    
    print("Testing Stunning Strike...")
    if monk.stunning_strike():
        print("✓ Stunning Strike activated! (Target must make CON save or be stunned)")
    print(f"Ki points remaining: {monk.ki_points}")
    print()
    
    # Test defensive abilities
    print("=" * 60)
    print("TESTING DEFENSIVE ABILITIES")
    print("=" * 60)
    
    print(f"\nTesting Deflect Missiles on 15 damage attack...")
    remaining_damage = monk.deflect_missiles(15)
    print(f"Damage reduced to: {remaining_damage}")
    
    if monk.catch_missile(15):
        print("✓ Missile can be caught! (Spend 1 ki point to throw it back)")
    print()
    
    print(f"Testing Slow Fall from 50ft fall...")
    fall_damage = monk.slow_fall(50)
    print(f"Falling damage reduced to: {fall_damage}")
    print()
    
    # Test healing ability
    print("=" * 60)
    print("TESTING HEALING ABILITIES")
    print("=" * 60)
    
    # Level up to get Wholeness of Body
    for _ in range(3):  # Level up to 6
        monk.level_up()
    
    print(f"\nLevel {monk.level} - Testing Wholeness of Body...")
    original_hp = monk.hp
    monk.hp = original_hp - 20  # Simulate taking damage
    print(f"HP before healing: {monk.hp}/{monk.max_hp}")
    
    healing = monk.wholeness_of_body()
    print(f"Wholeness of Body healed for: {healing} HP")
    print(f"HP after healing: {monk.hp}/{monk.max_hp}")
    print()
    
    # Test high-level features
    print("=" * 60)
    print("TESTING HIGH-LEVEL FEATURES")
    print("=" * 60)
    
    # Level up to get high-level features
    for _ in range(14):  # Level up to 20
        monk.level_up()
    
    print(f"\nLevel {monk.level} - High-level features:")
    print(f"Perfect Self: {monk.perfect_self}")
    print(f"Empty Body: {monk.empty_body_available}")
    print(f"Diamond Soul: {monk.diamond_soul}")
    print(f"Tongue of Sun and Moon: {monk.tongue_of_sun_moon}")
    print()
    
    print("Testing Empty Body...")
    if monk.activate_empty_body():
        print("✓ Empty Body activated! (Invisible and resistant to all damage except force)")
    print(f"Ki points remaining: {monk.ki_points}")
    print()
    
    print("Testing Quivering Palm...")
    if monk.activate_quivering_palm():
        print("✓ Quivering Palm activated! (Vibrations set in target)")
        palm_effect = monk.trigger_quivering_palm("Evil Villain")
        print(f"Target: {palm_effect['target']}")
        print(f"Save DC: {palm_effect['save_dc']} {palm_effect['save_type']}")
        print(f"On fail: {palm_effect['on_fail']}")
        print(f"On success: {palm_effect['on_success']}")
    print()
    
    print("\n" + "=" * 60)
    print(monk)
    print("=" * 60)