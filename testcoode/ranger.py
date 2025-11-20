#!/usr/bin/env python3
"""
Ranger Class - D&D 5e SRD Implementation
Derived from the base Character class with full Ranger features
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from Head.campaign_manager import Character


@dataclass
class Ranger(Character):
    """
    Ranger class implementation following D&D 5e SRD
    Inherits from Character and adds Ranger-specific features
    """
    
    # Ranger-specific attributes
    ranger_archetype: str = ""  # "Hunter" or "Beast Master"
    
    # Favored Enemy mechanics
    favored_enemies: List[str] = field(default_factory=list)  # List of enemy types
    favored_enemy_languages: List[str] = field(default_factory=list)  # Languages learned
    
    # Natural Explorer mechanics
    favored_terrains: List[str] = field(default_factory=list)  # List of terrain types
    
    # Fighting Style
    fighting_style: str = ""  # "Archery", "Defense", "Dueling", or "Two-Weapon Fighting"
    
    # Spellcasting
    spells_known: List[str] = field(default_factory=list)  # Known spells
    spell_slots: Dict[int, int] = field(default_factory=dict)  # Available slots by level
    spells_prepared: List[str] = field(default_factory=list)  # Prepared spells
    
    # Class features
    primeval_awareness_active: bool = False
    lands_stride_active: bool = False
    hide_in_plain_sight_active: bool = False
    vanish_active: bool = False
    feral_senses_active: bool = False
    foe_slayer_active: bool = False
    
    # Hunter archetype features
    hunters_prey: str = ""  # "Colossus Slayer", "Giant Killer", or "Horde Breaker"
    defensive_tactics: str = ""  # "Escape the Horde", "Multiattack Defense", or "Steel Will"
    multiattack: str = ""  # "Volley" or "Whirlwind Attack"
    superior_hunters_defense: str = ""  # "Evasion", "Stand Against the Tide", or "Uncanny Dodge"
    
    def __post_init__(self):
        """Initialize Ranger with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Ranger"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Rangers typically have high DEX and WIS
            self.stats = {
                "strength": 12,
                "dexterity": 15,
                "constitution": 14,
                "intelligence": 10,
                "wisdom": 13,
                "charisma": 8
            }
        
        # Set hit points based on level (1d10 per level)
        if self.level == 1:
            self.max_hp = 10 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Rangers choose three from: Animal Handling, Athletics, Insight, 
            # Investigation, Nature, Perception, Stealth, and Survival
            self.skill_proficiencies = ["Perception", "Stealth", "Survival"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        # Initialize spell slots
        self._initialize_spell_slots()
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
    def _initialize_spell_slots(self):
        """Initialize spell slots based on level"""
        self.spell_slots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        if self.level >= 2:
            self.spell_slots[1] = 2
        if self.level >= 3:
            self.spell_slots[1] = 3
        if self.level >= 5:
            self.spell_slots[1] = 4
            self.spell_slots[2] = 2
        if self.level >= 7:
            self.spell_slots[2] = 3
        if self.level >= 9:
            self.spell_slots[3] = 2
        if self.level >= 11:
            self.spell_slots[3] = 3
        if self.level >= 13:
            self.spell_slots[4] = 1
        if self.level >= 15:
            self.spell_slots[4] = 2
        if self.level >= 17:
            self.spell_slots[5] = 1
        if self.level >= 19:
            self.spell_slots[5] = 2
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Level 1 features
        if self.level >= 1:
            # These would typically be chosen during character creation
            # For now, we'll set defaults
            if not self.favored_enemies:
                self.favored_enemies = ["Beasts"]
                self.favored_enemy_languages = ["Sylvan"]  # Example language
            if not self.favored_terrains:
                self.favored_terrains = ["Forest"]
        
        # Level 2 features
        if self.level >= 2:
            if not self.fighting_style:
                self.fighting_style = "Archery"  # Default choice
            self._initialize_spell_slots()
        
        # Level 3 features
        if self.level >= 3:
            self.primeval_awareness_active = True
            if not self.ranger_archetype:
                self.ranger_archetype = "Hunter"  # Default archetype
            if self.ranger_archetype == "Hunter" and not self.hunters_prey:
                self.hunters_prey = "Colossus Slayer"  # Default Hunter feature
        
        # Level 5 features
        if self.level >= 5:
            pass  # Extra Attack handled in attack logic
        
        # Level 6 features
        if self.level >= 6:
            # Additional favored enemy and terrain
            if len(self.favored_enemies) < 2:
                self.favored_enemies.append("Humanoids (Gnolls, Orcs)")
                self.favored_enemy_languages.append("Orc")
            if len(self.favored_terrains) < 2:
                self.favored_terrains.append("Mountain")
        
        # Level 7 features
        if self.level >= 7 and self.ranger_archetype == "Hunter":
            if not self.defensive_tactics:
                self.defensive_tactics = "Escape the Horde"  # Default
        
        # Level 8 features
        if self.level >= 8:
            self.lands_stride_active = True
        
        # Level 10 features
        if self.level >= 10:
            self.hide_in_plain_sight_active = True
            if len(self.favored_terrains) < 3:
                self.favored_terrains.append("Swamp")
        
        # Level 11 features
        if self.level >= 11 and self.ranger_archetype == "Hunter":
            if not self.multiattack:
                self.multiattack = "Volley"  # Default
        
        # Level 14 features
        if self.level >= 14:
            self.vanish_active = True
            if len(self.favored_enemies) < 3:
                self.favored_enemies.append("Undead")
                self.favored_enemy_languages.append("Infernal")
        
        # Level 15 features
        if self.level >= 15 and self.ranger_archetype == "Hunter":
            if not self.superior_hunters_defense:
                self.superior_hunters_defense = "Evasion"  # Default
        
        # Level 18 features
        if self.level >= 18:
            self.feral_senses_active = True
        
        # Level 20 features
        if self.level >= 20:
            self.foe_slayer_active = True
    
    def get_spell_save_dc(self) -> int:
        """Calculate spell save DC: 8 + proficiency bonus + Wisdom modifier"""
        return 8 + self.get_proficiency_bonus() + self._get_modifier("wisdom")
    
    def get_spell_attack_bonus(self) -> int:
        """Calculate spell attack bonus: proficiency bonus + Wisdom modifier"""
        return self.get_proficiency_bonus() + self._get_modifier("wisdom")
    
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
    
    def get_favored_enemy_benefits(self, enemy_type: str) -> Dict[str, any]:
        """Get benefits against favored enemies"""
        is_favored = enemy_type in self.favored_enemies or any(
            enemy_type.lower() in enemy.lower() for enemy in self.favored_enemies
        )
        
        return {
            "is_favored": is_favored,
            "advantage_tracking": is_favored,
            "advantage_recall_information": is_favored,
            "wisdom_modifier_to_attack": is_favored and self.foe_slayer_active
        }
    
    def get_natural_explorer_benefits(self, terrain_type: str) -> Dict[str, any]:
        """Get benefits in favored terrain"""
        is_favored = terrain_type in self.favored_terrains
        
        return {
            "is_favored": is_favored,
            "double_proficiency": is_favored,
            "no_difficult_terrain": is_favored,
            "cannot_get_lost": is_favored,
            "remain_alert_while_traveling": is_favored,
            "stealth_at_normal_pace": is_favored,
            "double_foraging": is_favored,
            "enhanced_tracking": is_favored
        }
    
    def get_fighting_style_benefits(self) -> Dict[str, any]:
        """Get benefits from fighting style"""
        benefits = {
            "archery": {"ranged_attack_bonus": 2},
            "defense": {"ac_bonus": 1},
            "dueling": {"damage_bonus": 2, "conditions": ["one_handed_melee", "no_other_weapons"]},
            "two_weapon_fighting": {"add_ability_modifier_offhand": True}
        }
        return benefits.get(self.fighting_style, {})
    
    def use_primeval_awareness(self, spell_slot_level: int) -> Dict[str, any]:
        """
        Use Primeval Awareness feature
        Returns detection information for creature types
        """
        if spell_slot_level not in self.spell_slots or self.spell_slots[spell_slot_level] <= 0:
            return {"success": False, "message": "No spell slot available"}
        
        # Consume spell slot
        self.spell_slots[spell_slot_level] -= 1
        
        duration = spell_slot_level  # 1 minute per spell slot level
        
        return {
            "success": True,
            "duration": duration,
            "range": "1 mile (6 miles in favored terrain)",
            "creature_types": [
                "aberrations", "celestials", "dragons", "elementals", 
                "fey", "fiends", "undead"
            ],
            "detects_presence": True,
            "reveals_location": False,
            "reveals_number": False
        }
    
    def hide_in_plain_sight(self) -> Dict[str, any]:
        """Use Hide in Plain Sight feature"""
        if not self.hide_in_plain_sight_active:
            return {"success": False, "message": "Feature not available"}
        
        return {
            "success": True,
            "preparation_time": "1 minute",
            "materials_needed": ["natural materials"],
            "stealth_bonus": 10,
            "conditions": ["must remain still", "against solid surface"],
            "ends_on": ["movement", "action", "reaction"]
        }
    
    def get_hunter_features(self) -> Dict[str, any]:
        """Get Hunter archetype features"""
        if self.ranger_archetype != "Hunter":
            return {}
        
        features = {
            "hunters_prey": self.hunters_prey,
            "defensive_tactics": self.defensive_tactics,
            "multiattack": self.multiattack,
            "superior_hunters_defense": self.superior_hunters_defense
        }
        
        # Add descriptions
        descriptions = {
            "Colossus Slayer": "Extra 1d8 damage vs wounded creatures (once per turn)",
            "Giant Killer": "Reaction attack vs Large+ creatures that attack you",
            "Horde Breaker": "Extra attack vs different creature within 5ft of target",
            "Escape the Horde": "Disadvantage on opportunity attacks vs you",
            "Multiattack Defense": "+4 AC vs subsequent attacks from same creature",
            "Steel Will": "Advantage vs frightened saves",
            "Volley": "Ranged attack vs all creatures in 10ft radius",
            "Whirlwind Attack": "Melee attack vs all creatures within 5ft",
            "Evasion": "No damage on successful Dex saves, half on failed",
            "Stand Against the Tide": "Redirect missed melee attacks to other creatures",
            "Uncanny Dodge": "Use reaction to halve attack damage"
        }
        
        return {
            "features": features,
            "descriptions": descriptions
        }
    
    def calculate_attack_bonus(self, weapon_type: str, is_ranged: bool = False) -> int:
        """Calculate attack bonus with fighting style benefits"""
        base_bonus = self.get_proficiency_bonus() + self._get_modifier("dexterity")
        
        # Apply fighting style benefits
        style_benefits = self.get_fighting_style_benefits()
        
        if is_ranged and "ranged_attack_bonus" in style_benefits:
            base_bonus += style_benefits["ranged_attack_bonus"]
        
        return base_bonus
    
    def calculate_damage_bonus(self, weapon_type: str, is_main_hand: bool = True) -> int:
        """Calculate damage bonus with fighting style benefits"""
        base_bonus = self._get_modifier("dexterity")
        
        # Apply fighting style benefits
        style_benefits = self.get_fighting_style_benefits()
        
        if ("damage_bonus" in style_benefits and is_main_hand and
            self._meets_dueling_conditions()):
            base_bonus += style_benefits["damage_bonus"]
        
        return base_bonus
    
    def _meets_dueling_conditions(self) -> bool:
        """Check if conditions for Dueling fighting style are met"""
        if self.fighting_style != "dueling":
            return False
        
        # In a real implementation, this would check equipped weapons
        # For now, we'll assume the conditions can be met
        return True
    
    def get_extra_attack_count(self) -> int:
        """Get number of attacks (2 at level 5+)"""
        return 2 if self.level >= 5 else 1
    
    def long_rest(self):
        """Reset resources on long rest"""
        self._initialize_spell_slots()  # Reset spell slots
        self.hp = self.max_hp
    
    def level_up(self):
        """Level up the ranger"""
        self.level += 1
        
        # Increase HP (1d10 + CON mod per level, or 6 + CON mod average)
        hp_gain = 6 + self._get_modifier("constitution")
        self.max_hp += hp_gain
        self.hp += hp_gain
        
        # Reapply level-based features
        self.apply_level_features()
        
        # Update spell slots
        self._initialize_spell_slots()
    
    def get_character_sheet(self) -> Dict:
        """Generate a complete character sheet"""
        return {
            "name": self.name,
            "race": self.race,
            "class": f"{self.char_class} {self.level}",
            "background": self.background,
            "alignment": self.alignment,
            "ranger_archetype": self.ranger_archetype if self.ranger_archetype else "Not chosen (Level 3+)",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": self.ac,
            "speed": 30,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "strength": self._get_modifier("strength") + self.get_proficiency_bonus(),
                "dexterity": self._get_modifier("dexterity") + self.get_proficiency_bonus()
            },
            
            "skills": self.skill_proficiencies,
            "languages": self.languages_known + self.favored_enemy_languages,
            
            "ranger_features": {
                "Favored Enemies": self.favored_enemies,
                "Favored Terrains": self.favored_terrains,
                "Fighting Style": self.fighting_style,
                "Spellcasting": f"DC {self.get_spell_save_dc()}, +{self.get_spell_attack_bonus()} to hit",
                "Primeval Awareness": self.primeval_awareness_active,
                "Land's Stride": self.lands_stride_active,
                "Hide in Plain Sight": self.hide_in_plain_sight_active,
                "Vanish": self.vanish_active,
                "Feral Senses": self.feral_senses_active,
                "Foe Slayer": self.foe_slayer_active,
                "Extra Attack": self.level >= 5
            },
            
            "spell_slots": self.spell_slots,
            "spells_known": self.spells_known,
            
            "hunter_features": self.get_hunter_features() if self.ranger_archetype == "Hunter" else {},
            
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
        archetype_str = f" ({self.ranger_archetype})" if self.ranger_archetype else ""
        spells_str = f" | Spells: {sum(self.spell_slots.values())} slots" if self.level >= 2 else ""
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{archetype_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac}{spells_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Ranger
    ranger = Ranger(
        name="Aragorn",
        race="Human",
        char_class="Ranger",
        background="Outlander",
        level=1,
        stats={
            "strength": 14,
            "dexterity": 16,
            "constitution": 14,
            "intelligence": 12,
            "wisdom": 15,
            "charisma": 10
        },
        alignment="Neutral Good",
        personality_traits=["I feel far more comfortable around animals than people", "I'm always picking things up and fiddling with them"],
        ideal="Greater Good. It is each person's responsibility to make the most happiness for the whole tribe.",
        bond="I suffer awful visions of a coming disaster and will do anything to prevent it.",
        flaw="I am too enamored of ale, wine, and other intoxicants."
    )
    
    # Set starting equipment
    ranger.inventory = ["Longbow", "Arrows (20)", "Shortsword", "Shortsword", "Leather Armor", "Explorer's Pack"]
    
    print("=" * 60)
    print("RANGER CHARACTER SHEET")
    print("=" * 60)
    print(ranger)
    print()
    
    # Display character sheet
    sheet = ranger.get_character_sheet()
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
    
    print("Favored Enemies:")
    for enemy in sheet['ranger_features']['Favored Enemies']:
        print(f"  • {enemy}")
    print()
    
    print("Favored Terrains:")
    for terrain in sheet['ranger_features']['Favored Terrains']:
        print(f"  • {terrain}")
    print()
    
    print(f"Fighting Style: {sheet['ranger_features']['Fighting Style']}")
    print(f"Spellcasting: {sheet['ranger_features']['Spellcasting']}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['ranger_features'].items():
        if feature not in ["Favored Enemies", "Favored Terrains", "Fighting Style", "Spellcasting"]:
            if value and value is not False:
                print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    print("Spell Slots:")
    for level, slots in sheet['spell_slots'].items():
        if slots > 0:
            print(f"  Level {level}: {slots}")
    print()
    
    print("Equipment:")
    for item in ranger.inventory:
        print(f"  • {item}")
    print()
    
    # Test leveling up
    print("=" * 60)
    print("TESTING LEVEL UP")
    print("=" * 60)
    
    print(f"\nCurrent level: {ranger.level}")
    print(f"Current HP: {ranger.hp}/{ranger.max_hp}")
    
    ranger.level_up()  # Level 2
    ranger.level_up()  # Level 3
    ranger.ranger_archetype = "Hunter"
    ranger.apply_level_features()
    
    print(f"\nAfter leveling up to 3:")
    print(f"New level: {ranger.level}")
    print(f"New HP: {ranger.hp}/{ranger.max_hp}")
    print(f"Features unlocked: Fighting Style, Spellcasting, Primeval Awareness, Hunter Archetype")
    print(f"Hunter's Prey: {ranger.hunters_prey}")
    
    # Test favored enemy benefits
    print("\n" + "=" * 60)
    print("TESTING FAVORED ENEMY")
    print("=" * 60)
    
    benefits = ranger.get_favored_enemy_benefits("Beasts")
    print(f"Against Beasts (Favored Enemy):")
    print(f"  Advantage on tracking: {benefits['advantage_tracking']}")
    print(f"  Advantage on recall: {benefits['advantage_recall_information']}")
    
    # Test natural explorer benefits
    print("\n" + "=" * 60)
    print("TESTING NATURAL EXPLORER")
    print("=" * 60)
    
    benefits = ranger.get_natural_explorer_benefits("Forest")
    print(f"In Forest (Favored Terrain):")
    print(f"  Double proficiency: {benefits['double_proficiency']}")
    print(f"  No difficult terrain: {benefits['no_difficult_terrain']}")
    print(f"  Cannot get lost: {benefits['cannot_get_lost']}")
    
    print("\n" + "=" * 60)
    print(ranger)
    print("=" * 60)