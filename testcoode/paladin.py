#!/usr/bin/env python3
"""
Paladin Class - D&D 5e SRD Implementation
Derived from the base Character class with full Paladin features
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


from Head.campaign_manager import Character


@dataclass
class Paladin(Character):
    """
    Paladin class implementation following D&D 5e SRD
    Inherits from Character and adds Paladin-specific features
    """
    
    # Paladin-specific attributes
    sacred_oath: str = ""  # "Oath of Devotion", etc.
    
    # Divine Sense mechanics
    divine_sense_uses: int = 1  # 1 + CHA mod
    divine_sense_used: int = 0
    
    # Lay on Hands mechanics
    lay_on_hands_pool: int = 5  # level × 5
    lay_on_hands_remaining: int = 5
    
    # Spellcasting
    prepared_spells: List[str] = field(default_factory=list)
    spell_slots: Dict[int, int] = field(default_factory=dict)  # {level: remaining}
    max_spell_slots: Dict[int, int] = field(default_factory=dict)  # {level: max}
    
    # Fighting Style
    fighting_style: str = ""  # "Defense", "Dueling", "Great Weapon Fighting", "Protection"
    
    # Divine Smite
    divine_smite_available: bool = False
    
    # Auras
    aura_of_protection_range: int = 0  # 10ft at 6th, 30ft at 18th
    aura_of_courage_range: int = 0  # 10ft at 10th, 30ft at 18th
    aura_of_devotion_range: int = 0  # 10ft at 7th, 30ft at 18th (Oath of Devotion)
    
    # Class features
    divine_health: bool = False
    extra_attack: bool = False
    improved_divine_smite: bool = False
    cleansing_touch_uses: int = 0
    cleansing_touch_remaining: int = 0
    
    # Oath of Devotion features
    sacred_weapon_available: bool = False
    turn_the_unholy_available: bool = False
    purity_of_spirit: bool = False
    holy_nimbus_available: bool = False
    
    # Channel Divinity
    channel_divinity_uses: int = 1
    channel_divinity_used: int = 0
    
    def __post_init__(self):
        """Initialize Paladin with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Paladin"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Paladins typically have high STR and CHA
            self.stats = {
                "strength": 15,
                "dexterity": 12,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 13,
                "charisma": 16
            }
        
        # Set hit points based on level (1d10 per level)
        if self.level == 1:
            self.max_hp = 10 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Paladins choose two from: Athletics, Insight, Intimidation, 
            # Medicine, Persuasion, and Religion
            self.skill_proficiencies = ["Athletics", "Persuasion"]
        
        if not self.saving_throw_proficiencies:
            self.saving_throw_proficiencies = ["wisdom", "charisma"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        # Set starting equipment
        if not self.inventory:
            self.inventory = [
                "Chain mail", 
                "Holy symbol",
                "Martial weapon",
                "Shield",
                "Five javelins",
                "Priest's pack"
            ]
        
        # Initialize spell slots
        self.initialize_spell_slots()
        
        # Calculate Divine Sense uses
        self.calculate_divine_sense_uses()
        
        # Calculate Lay on Hands pool
        self.calculate_lay_on_hands_pool()
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
    def initialize_spell_slots(self):
        """Initialize spell slots based on level"""
        # Default: no spell slots at level 1
        self.max_spell_slots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.spell_slots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        # Update based on level
        self.update_spell_slots()
    
    def update_spell_slots(self):
        """Update spell slots based on current level"""
        # Spell slot progression from Paladin table
        slot_progression = {
            1: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            2: {1: 2, 2: 0, 3: 0, 4: 0, 5: 0},
            3: {1: 3, 2: 0, 3: 0, 4: 0, 5: 0},
            4: {1: 3, 2: 0, 3: 0, 4: 0, 5: 0},
            5: {1: 4, 2: 2, 3: 0, 4: 0, 5: 0},
            6: {1: 4, 2: 2, 3: 0, 4: 0, 5: 0},
            7: {1: 4, 2: 3, 3: 0, 4: 0, 5: 0},
            8: {1: 4, 2: 3, 3: 0, 4: 0, 5: 0},
            9: {1: 4, 2: 3, 3: 2, 4: 0, 5: 0},
            10: {1: 4, 2: 3, 3: 2, 4: 0, 5: 0},
            11: {1: 4, 2: 3, 3: 3, 4: 0, 5: 0},
            12: {1: 4, 2: 3, 3: 3, 4: 0, 5: 0},
            13: {1: 4, 2: 3, 3: 3, 4: 1, 5: 0},
            14: {1: 4, 2: 3, 3: 3, 4: 1, 5: 0},
            15: {1: 4, 2: 3, 3: 3, 4: 2, 5: 0},
            16: {1: 4, 2: 3, 3: 3, 4: 2, 5: 0},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}
        }
        
        if self.level in slot_progression:
            self.max_spell_slots = slot_progression[self.level].copy()
            # Only update spell slots if they haven't been set or are at default
            if all(v == 0 for v in self.spell_slots.values()):
                self.spell_slots = slot_progression[self.level].copy()
    
    def calculate_divine_sense_uses(self):
        """Calculate Divine Sense uses: 1 + CHA modifier"""
        self.divine_sense_uses = max(1, 1 + self._get_modifier("charisma"))
    
    def calculate_lay_on_hands_pool(self):
        """Calculate Lay on Hands pool: level × 5"""
        self.lay_on_hands_pool = self.level * 5
        if self.lay_on_hands_remaining > self.lay_on_hands_pool:
            self.lay_on_hands_remaining = self.lay_on_hands_pool
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Divine Sense (Level 1)
        if self.level >= 1:
            self.calculate_divine_sense_uses()
            self.calculate_lay_on_hands_pool()
        
        # Fighting Style, Spellcasting, Divine Smite (Level 2)
        if self.level >= 2:
            self.divine_smite_available = True
            self.update_spell_slots()
        
        # Divine Health, Sacred Oath (Level 3)
        if self.level >= 3:
            self.divine_health = True
            self.channel_divinity_uses = 1
        
        # Ability Score Improvement (Level 4, 8, 12, 16, 19)
        # Note: Actual ASI application would be handled separately
        
        # Extra Attack (Level 5)
        if self.level >= 5:
            self.extra_attack = True
        
        # Aura of Protection (Level 6)
        if self.level >= 6:
            self.aura_of_protection_range = 10
        
        # Sacred Oath feature (Level 7)
        if self.level >= 7 and self.sacred_oath == "Oath of Devotion":
            self.aura_of_devotion_range = 10
        
        # Aura of Courage (Level 10)
        if self.level >= 10:
            self.aura_of_courage_range = 10
        
        # Improved Divine Smite (Level 11)
        if self.level >= 11:
            self.improved_divine_smite = True
        
        # Cleansing Touch (Level 14)
        if self.level >= 14:
            self.cleansing_touch_uses = max(1, self._get_modifier("charisma"))
            self.cleansing_touch_remaining = self.cleansing_touch_uses
        
        # Sacred Oath feature (Level 15)
        if self.level >= 15 and self.sacred_oath == "Oath of Devotion":
            self.purity_of_spirit = True
        
        # Aura improvements (Level 18)
        if self.level >= 18:
            self.aura_of_protection_range = 30
            self.aura_of_courage_range = 30
            if self.sacred_oath == "Oath of Devotion":
                self.aura_of_devotion_range = 30
        
        # Sacred Oath feature (Level 20)
        if self.level >= 20 and self.sacred_oath == "Oath of Devotion":
            self.holy_nimbus_available = True
        
        # Channel Divinity uses increase
        if self.level >= 6:
            self.channel_divinity_uses = 2
        if self.level >= 18:
            self.channel_divinity_uses = 3
    
    def use_divine_sense(self) -> bool:
        """
        Use Divine Sense feature.
        Returns True if successful, False otherwise.
        """
        if self.divine_sense_used >= self.divine_sense_uses:
            return False
        
        self.divine_sense_used += 1
        return True
    
    def use_lay_on_hands(self, hp_to_heal: int = None, cure_disease: bool = False, cure_poison: bool = False) -> Dict[str, any]:
        """
        Use Lay on Hands to heal or cure conditions.
        Returns dict with result information.
        """
        result = {
            "success": False,
            "healed": 0,
            "diseases_cured": 0,
            "poisons_neutralized": 0,
            "message": ""
        }
        
        if self.lay_on_hands_remaining <= 0:
            result["message"] = "No healing power remaining in Lay on Hands pool"
            return result
        
        if hp_to_heal:
            if hp_to_heal > self.lay_on_hands_remaining:
                result["message"] = f"Not enough healing power. Available: {self.lay_on_hands_remaining}"
                return result
            
            self.lay_on_hands_remaining -= hp_to_heal
            result["healed"] = hp_to_heal
            result["success"] = True
            result["message"] = f"Healed {hp_to_heal} hit points"
        
        # Cure diseases (5 HP per disease)
        if cure_disease and self.lay_on_hands_remaining >= 5:
            self.lay_on_hands_remaining -= 5
            result["diseases_cured"] += 1
            result["success"] = True
            result["message"] += f"{', ' if result['message'] else ''}Cured 1 disease"
        
        # Neutralize poisons (5 HP per poison)
        if cure_poison and self.lay_on_hands_remaining >= 5:
            self.lay_on_hands_remaining -= 5
            result["poisons_neutralized"] += 1
            result["success"] = True
            result["message"] += f"{', ' if result['message'] else ''}Neutralized 1 poison"
        
        return result
    
    def divine_smite_damage(self, spell_slot_level: int, target_is_undead_or_fiend: bool = False) -> Tuple[int, str]:
        """
        Calculate Divine Smite damage for a given spell slot level.
        Returns (damage_dice, description)
        """
        if spell_slot_level < 1:
            return (0, "Invalid spell slot level")
        
        # Base damage: 2d8 for 1st level, +1d8 per level higher
        damage_dice = 2 + (spell_slot_level - 1)
        
        # Cap at 5d8
        damage_dice = min(damage_dice, 5)
        
        # Extra damage vs undead/fiends
        extra_dice = 1 if target_is_undead_or_fiend else 0
        
        total_dice = damage_dice + extra_dice
        
        description = f"{damage_dice}d8 radiant damage"
        if extra_dice > 0:
            description += f" + {extra_dice}d8 vs undead/fiend"
        
        return (total_dice, description)
    
    def use_channel_divinity(self, option: str = "sacred_weapon") -> bool:
        """
        Use Channel Divinity feature.
        Returns True if successful, False otherwise.
        """
        if self.channel_divinity_used >= self.channel_divinity_uses:
            return False
        
        if not self.sacred_oath:
            return False
        
        self.channel_divinity_used += 1
        return True
    
    def get_spell_save_dc(self) -> int:
        """Calculate spell save DC: 8 + proficiency + CHA mod"""
        return 8 + self.get_proficiency_bonus() + self._get_modifier("charisma")
    
    def get_spell_attack_bonus(self) -> int:
        """Calculate spell attack bonus: proficiency + CHA mod"""
        return self.get_proficiency_bonus() + self._get_modifier("charisma")
    
    def get_aura_of_protection_bonus(self) -> int:
        """Get Aura of Protection bonus: CHA modifier (min +1)"""
        return max(1, self._get_modifier("charisma"))
    
    def long_rest(self):
        """Reset resources on long rest"""
        self.divine_sense_used = 0
        self.lay_on_hands_remaining = self.lay_on_hands_pool
        self.channel_divinity_used = 0
        self.cleansing_touch_remaining = self.cleansing_touch_uses
        
        # Reset spell slots
        for level in self.spell_slots:
            self.spell_slots[level] = self.max_spell_slots.get(level, 0)
        
        self.hp = self.max_hp
    
    def short_rest(self):
        """Reset some resources on short rest"""
        self.channel_divinity_used = 0
    
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
    
    def level_up(self):
        """Level up the paladin"""
        self.level += 1
        
        # Increase HP (1d10 + CON mod per level, or 6 + CON mod average)
        hp_gain = 6 + self._get_modifier("constitution")
        self.max_hp += hp_gain
        self.hp += hp_gain
        
        # Recalculate Lay on Hands pool
        self.calculate_lay_on_hands_pool()
        
        # Update spell slots
        self.update_spell_slots()
        
        # Reapply level-based features
        self.apply_level_features()
    
    def get_character_sheet(self) -> Dict:
        """Generate a complete character sheet"""
        return {
            "name": self.name,
            "race": self.race,
            "class": f"{self.char_class} {self.level}",
            "background": self.background,
            "alignment": self.alignment,
            "sacred_oath": self.sacred_oath if self.sacred_oath else "Not chosen (Level 3+)",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": self.ac,
            "speed": 30,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "wisdom": self._get_modifier("wisdom") + (self.get_proficiency_bonus() if "wisdom" in self.saving_throw_proficiencies else 0),
                "charisma": self._get_modifier("charisma") + (self.get_proficiency_bonus() if "charisma" in self.saving_throw_proficiencies else 0)
            },
            
            "skills": self.skill_proficiencies,
            "languages": self.languages_known,
            
            "divine_sense": {
                "uses": f"{self.divine_sense_used}/{self.divine_sense_uses}",
            },
            
            "lay_on_hands": {
                "pool": f"{self.lay_on_hands_remaining}/{self.lay_on_hands_pool}",
            },
            
            "spellcasting": {
                "spell_save_dc": self.get_spell_save_dc(),
                "spell_attack_bonus": self.get_spell_attack_bonus(),
                "slots": dict(self.spell_slots),
                "prepared_spells": self.prepared_spells
            },
            
            "channel_divinity": {
                "uses": f"{self.channel_divinity_used}/{self.channel_divinity_uses}",
            },
            
            "fighting_style": self.fighting_style,
            
            "auras": {
                "Aura of Protection": f"{self.aura_of_protection_range} ft" if self.aura_of_protection_range > 0 else "Not available",
                "Aura of Courage": f"{self.aura_of_courage_range} ft" if self.aura_of_courage_range > 0 else "Not available",
                "Aura of Devotion": f"{self.aura_of_devotion_range} ft" if self.aura_of_devotion_range > 0 else "Not available"
            },
            
            "features": {
                "Divine Sense": True,
                "Lay on Hands": True,
                "Fighting Style": bool(self.fighting_style),
                "Spellcasting": self.level >= 2,
                "Divine Smite": self.divine_smite_available,
                "Divine Health": self.divine_health,
                "Sacred Oath": bool(self.sacred_oath),
                "Extra Attack": self.extra_attack,
                "Improved Divine Smite": self.improved_divine_smite,
                "Cleansing Touch": self.cleansing_touch_uses > 0,
                "Purity of Spirit": self.purity_of_spirit,
                "Holy Nimbus": self.holy_nimbus_available
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
        oath_str = f" ({self.sacred_oath})" if self.sacred_oath else ""
        lay_on_hands_str = f"LoH: {self.lay_on_hands_remaining}/{self.lay_on_hands_pool}"
        spells_str = f"Spells: {sum(self.spell_slots.values())}/{sum(self.max_spell_slots.values())}"
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{oath_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac} | {lay_on_hands_str} | {spells_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Paladin
    paladin = Paladin(
        name="Sir Galadon the Pure",
        race="Human",
        char_class="Paladin",
        background="Acolyte",
        level=1,
        stats={
            "strength": 16,
            "dexterity": 10,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 16
        },
        alignment="Lawful Good",
        personality_traits=["I see omens in every event and action", "I am tolerant of other faiths"],
        ideal="Charity. I always try to help those in need",
        bond="I would die to recover an ancient relic of my faith",
        flaw="I am suspicious of strangers and expect the worst of them"
    )
    
    print("=" * 60)
    print("PALADIN CHARACTER SHEET")
    print("=" * 60)
    print(paladin)
    print()
    
    # Display character sheet
    sheet = paladin.get_character_sheet()
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
    
    print("Divine Sense:")
    print(f"  Uses: {sheet['divine_sense']['uses']}")
    print()
    
    print("Lay on Hands:")
    print(f"  Pool: {sheet['lay_on_hands']['pool']} HP")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    print("Equipment:")
    for item in paladin.inventory:
        print(f"  • {item}")
    print()
    
    # Test Lay on Hands mechanics
    print("=" * 60)
    print("TESTING LAY ON HANDS MECHANICS")
    print("=" * 60)
    
    print(f"\nInitial Lay on Hands: {paladin.lay_on_hands_remaining}/{paladin.lay_on_hands_pool}")
    
    print("\nHealing 10 HP...")
    result = paladin.use_lay_on_hands(hp_to_heal=10)
    if result["success"]:
        print(f"✓ {result['message']}")
        print(f"Remaining pool: {paladin.lay_on_hands_remaining}/{paladin.lay_on_hands_pool}")
    
    print("\nCuring disease...")
    result = paladin.use_lay_on_hands(cure_disease=True)
    if result["success"]:
        print(f"✓ {result['message']}")
        print(f"Remaining pool: {paladin.lay_on_hands_remaining}/{paladin.lay_on_hands_pool}")
    
    # Test Divine Smite
    print("\n" + "=" * 60)
    print("TESTING DIVINE SMITE")
    print("=" * 60)
    
    print("\nDivine Smite damage calculations:")
    for slot_level in range(1, 6):
        damage, description = paladin.divine_smite_damage(slot_level)
        print(f"  Level {slot_level} slot: {description}")
    
    print("\nDivine Smite vs undead/fiend:")
    for slot_level in range(1, 6):
        damage, description = paladin.divine_smite_damage(slot_level, target_is_undead_or_fiend=True)
        print(f"  Level {slot_level} slot: {description}")
    
    # Test leveling up
    print("\n" + "=" * 60)
    print("TESTING LEVEL UP")
    print("=" * 60)
    
    print(f"\nCurrent level: {paladin.level}")
    print(f"Current HP: {paladin.hp}/{paladin.max_hp}")
    print(f"Current Lay on Hands: {paladin.lay_on_hands_pool}")
    print(f"Spell slots: {paladin.spell_slots}")
    
    # Level up to 2 for spellcasting and fighting style
    paladin.level_up()
    paladin.fighting_style = "Defense"
    
    print(f"\nAfter level up to 2:")
    print(f"New level: {paladin.level}")
    print(f"New HP: {paladin.hp}/{paladin.max_hp}")
    print(f"New Lay on Hands: {paladin.lay_on_hands_pool}")
    print(f"Spell slots: {paladin.spell_slots}")
    print(f"Fighting Style: {paladin.fighting_style}")
    print(f"Features unlocked: Spellcasting, Divine Smite")
    
    # Level up to 3 for Sacred Oath
    paladin.level_up()
    paladin.sacred_oath = "Oath of Devotion"
    paladin.apply_level_features()
    
    print(f"\nLevel {paladin.level} - Sacred Oath chosen: {paladin.sacred_oath}")
    print(f"Channel Divinity uses: {paladin.channel_divinity_uses}")
    print(f"New features: Divine Health, Sacred Oath")
    
    print("\n" + "=" * 60)
    print(paladin)
    print("=" * 60)