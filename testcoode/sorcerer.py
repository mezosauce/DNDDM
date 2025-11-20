#!/usr/bin/env python3
"""
Sorcerer Class - D&D 5e SRD Implementation
Derived from the base Character class with full Sorcerer features
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from Head.campaign_manager import Character


@dataclass
class Sorcerer(Character):
    """
    Sorcerer class implementation following D&D 5e SRD
    Inherits from Character and adds Sorcerer-specific features
    """
    
    # Sorcerer-specific attributes
    sorcerous_origin: str = ""  # "Draconic Bloodline" or "Wild Magic"
    dragon_ancestor: str = ""  # For Draconic Bloodline
    dragon_damage_type: str = ""  # For Draconic Bloodline
    
    # Spellcasting
    cantrips_known: List[str] = field(default_factory=list)
    spells_known: List[str] = field(default_factory=list)
    spell_slots: Dict[int, int] = field(default_factory=dict)  # level -> slots available
    max_spell_slots: Dict[int, int] = field(default_factory=dict)  # level -> max slots
    
    # Sorcery Points mechanics
    sorcery_points: int = 0
    max_sorcery_points: int = 0
    
    # Metamagic options
    metamagic_options: Set[str] = field(default_factory=set)
    available_metamagic_count: int = 0
    
    # Draconic Bloodline features
    draconic_resilience_active: bool = False
    elemental_affinity_active: bool = False
    dragon_wings_active: bool = False
    draconic_presence_available: bool = False
    
    # Level progression tracking
    ability_score_improvements: int = 0
    
    def __post_init__(self):
        """Initialize Sorcerer with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Sorcerer"
        
        # Set initial stats if not provided (Sorcerers need high CHA)
        if not self.stats or all(v == 10 for v in self.stats.values()):
            self.stats = {
                "strength": 8,
                "dexterity": 14,
                "constitution": 13,
                "intelligence": 12,
                "wisdom": 10,
                "charisma": 15
            }
        
        # Set hit points based on level (1d6 per level)
        if self.level == 1:
            self.max_hp = 6 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Sorcerers choose two from: Arcana, Deception, Insight, Intimidation, Persuasion, Religion
            self.skill_proficiencies = ["Arcana", "Persuasion"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        # Initialize spell slots and sorcery points
        self.initialize_spellcasting()
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
    def initialize_spellcasting(self):
        """Initialize spell slots and sorcery points based on level"""
        # Define spell slot progression by level
        spell_slot_table = {
            1: {1: 2},
            2: {1: 3},
            3: {1: 4, 2: 2},
            4: {1: 4, 2: 3},
            5: {1: 4, 2: 3, 3: 2},
            6: {1: 4, 2: 3, 3: 3},
            7: {1: 4, 2: 3, 3: 3, 4: 1},
            8: {1: 4, 2: 3, 3: 3, 4: 2},
            9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
            18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        }
        
        # Set current level's spell slots
        if self.level in spell_slot_table:
            self.max_spell_slots = spell_slot_table[self.level].copy()
            self.spell_slots = spell_slot_table[self.level].copy()
        else:
            # Default to level 1 if level is out of range
            self.max_spell_slots = {1: 2}
            self.spell_slots = {1: 2}
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Sorcery Points progression
        sorcery_point_table = {
            2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
            11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 
            18: 18, 19: 19, 20: 20
        }
        
        if self.level >= 2:
            self.max_sorcery_points = sorcery_point_table.get(self.level, 0)
            self.sorcery_points = min(self.sorcery_points, self.max_sorcery_points)
        
        # Cantrips known progression
        cantrips_known_table = {
            1: 4, 4: 5, 10: 6
        }
        for level, cantrips in sorted(cantrips_known_table.items(), reverse=True):
            if self.level >= level:
                if len(self.cantrips_known) < cantrips:
                    # Add placeholder cantrips if needed
                    while len(self.cantrips_known) < cantrips:
                        self.cantrips_known.append(f"Cantrip {len(self.cantrips_known) + 1}")
                break
        
        # Spells known progression
        spells_known_table = {
            1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10,
            10: 11, 11: 12, 12: 12, 13: 13, 14: 13, 15: 14, 16: 14,
            17: 15, 18: 15, 19: 15, 20: 15
        }
        if self.level in spells_known_table:
            target_spells = spells_known_table[self.level]
            if len(self.spells_known) < target_spells:
                # Add placeholder spells if needed
                while len(self.spells_known) < target_spells:
                    self.spells_known.append(f"Spell {len(self.spells_known) + 1}")
        
        # Metamagic progression
        if self.level >= 3:
            self.available_metamagic_count = 2
        if self.level >= 10:
            self.available_metamagic_count = 3
        if self.level >= 17:
            self.available_metamagic_count = 4
        
        # Ensure we don't have more metamagic options than allowed
        while len(self.metamagic_options) > self.available_metamagic_count:
            self.metamagic_options.pop()
        
        # Ability Score Improvements
        self.ability_score_improvements = 0
        if self.level >= 4:
            self.ability_score_improvements += 1
        if self.level >= 8:
            self.ability_score_improvements += 1
        if self.level >= 12:
            self.ability_score_improvements += 1
        if self.level >= 16:
            self.ability_score_improvements += 1
        if self.level >= 19:
            self.ability_score_improvements += 1
        
        # Sorcerous Origin features
        if self.sorcerous_origin == "Draconic Bloodline":
            self.apply_draconic_features()
        
        # Level 20 feature
        if self.level >= 20:
            pass  # Sorcerous Restoration handled separately
    
    def apply_draconic_features(self):
        """Apply Draconic Bloodline specific features"""
        if self.level >= 1:
            self.draconic_resilience_active = True
            # Set AC to 13 + DEX when not wearing armor
            if not self.armor_worn:
                self.ac = 13 + self._get_modifier("dexterity")
        
        if self.level >= 6:
            self.elemental_affinity_active = True
        
        if self.level >= 14:
            self.dragon_wings_active = True
        
        if self.level >= 18:
            self.draconic_presence_available = True
    
    def get_spell_save_dc(self) -> int:
        """Calculate spell save DC: 8 + proficiency + CHA mod"""
        return 8 + self.get_proficiency_bonus() + self._get_modifier("charisma")
    
    def get_spell_attack_bonus(self) -> int:
        """Calculate spell attack bonus: proficiency + CHA mod"""
        return self.get_proficiency_bonus() + self._get_modifier("charisma")
    
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
    
    def add_metamagic_option(self, option: str) -> bool:
        """
        Add a metamagic option if slots are available
        Returns True if successful, False otherwise
        """
        if len(self.metamagic_options) >= self.available_metamagic_count:
            return False
        
        valid_options = {
            "Careful Spell", "Distant Spell", "Empowered Spell", "Extended Spell",
            "Heightened Spell", "Quickened Spell", "Subtle Spell", "Twinned Spell"
        }
        
        if option in valid_options:
            self.metamagic_options.add(option)
            return True
        
        return False
    
    def remove_metamagic_option(self, option: str) -> bool:
        """Remove a metamagic option"""
        if option in self.metamagic_options:
            self.metamagic_options.remove(option)
            return True
        return False
    
    def flexible_casting_create_slot(self, slot_level: int) -> bool:
        """
        Create a spell slot using sorcery points
        Returns True if successful, False otherwise
        """
        cost_table = {1: 2, 2: 3, 3: 5, 4: 6, 5: 7}
        
        if slot_level not in cost_table:
            return False
        
        cost = cost_table[slot_level]
        
        if self.sorcery_points < cost:
            return False
        
        self.sorcery_points -= cost
        
        # Add the spell slot
        if slot_level in self.spell_slots:
            self.spell_slots[slot_level] += 1
        else:
            self.spell_slots[slot_level] = 1
        
        return True
    
    def flexible_casting_convert_slot(self, slot_level: int) -> bool:
        """
        Convert a spell slot to sorcery points
        Returns True if successful, False otherwise
        """
        if slot_level not in self.spell_slots or self.spell_slots[slot_level] <= 0:
            return False
        
        if self.sorcery_points + slot_level > self.max_sorcery_points:
            return False
        
        self.spell_slots[slot_level] -= 1
        self.sorcery_points += slot_level
        return True
    
    def use_metamagic(self, metamagic: str, spell_level: int = 0) -> bool:
        """
        Use a metamagic option, spending sorcery points
        Returns True if successful, False otherwise
        """
        if metamagic not in self.metamagic_options:
            return False
        
        cost_table = {
            "Careful Spell": 1,
            "Distant Spell": 1,
            "Empowered Spell": 1,
            "Extended Spell": 1,
            "Heightened Spell": 3,
            "Quickened Spell": 2,
            "Subtle Spell": 1,
            "Twinned Spell": max(1, spell_level)  # 1 for cantrips, spell level for others
        }
        
        cost = cost_table.get(metamagic, 0)
        
        if self.sorcery_points < cost:
            return False
        
        self.sorcery_points -= cost
        return True
    
    def activate_dragon_wings(self) -> bool:
        """Activate dragon wings (Draconic Bloodline level 14)"""
        if not self.dragon_wings_active:
            return False
        
        if self.sorcerous_origin != "Draconic Bloodline":
            return False
        
        # In actual implementation, this would set fly speed
        # For now, just return success
        return True
    
    def use_draconic_presence(self) -> bool:
        """Use Draconic Presence (Draconic Bloodline level 18)"""
        if not self.draconic_presence_available:
            return False
        
        if self.sorcery_points < 5:
            return False
        
        self.sorcery_points -= 5
        return True
    
    def add_ability_score_improvement(self, ability1: str, ability2: str = None, increase: int = 1) -> bool:
        """
        Use an ability score improvement
        Can increase one ability by 2 or two abilities by 1 each
        """
        if self.ability_score_improvements <= 0:
            return False
        
        if ability2 is None:
            # Increase one ability by 2
            if ability1 in self.stats and self.stats[ability1] < 20:
                self.stats[ability1] = min(self.stats[ability1] + 2, 20)
                self.ability_score_improvements -= 1
                return True
        else:
            # Increase two abilities by 1 each
            if (ability1 in self.stats and ability2 in self.stats and
                self.stats[ability1] < 20 and self.stats[ability2] < 20):
                self.stats[ability1] = min(self.stats[ability1] + 1, 20)
                self.stats[ability2] = min(self.stats[ability2] + 1, 20)
                self.ability_score_improvements -= 1
                return True
        
        return False
    
    def long_rest(self):
        """Reset resources on long rest"""
        # Reset spell slots
        self.spell_slots = self.max_spell_slots.copy()
        
        # Reset sorcery points
        self.sorcery_points = self.max_sorcery_points
        
        # Reset HP
        self.hp = self.max_hp
    
    def short_rest(self):
        """Regain resources on short rest"""
        # Sorcerous Restoration at level 20
        if self.level >= 20:
            self.sorcery_points = min(self.sorcery_points + 4, self.max_sorcery_points)
    
    def level_up(self):
        """Level up the sorcerer"""
        self.level += 1
        
        # Increase HP (1d6 + CON mod per level, or 4 + CON mod average)
        hp_gain = 4 + self._get_modifier("constitution")
        
        # Draconic Bloodline gets +1 HP per level
        if self.sorcerous_origin == "Draconic Bloodline":
            hp_gain += 1
        
        self.max_hp += hp_gain
        self.hp += hp_gain
        
        # Reinitialize spellcasting for new level
        self.initialize_spellcasting()
        
        # Reapply level-based features
        self.apply_level_features()
    
    def get_character_sheet(self) -> Dict:
        """Generate a complete character sheet"""
        # Format spell slots for display
        spell_slots_display = {}
        for level, slots in sorted(self.spell_slots.items()):
            max_slots = self.max_spell_slots.get(level, 0)
            spell_slots_display[f"Level {level}"] = f"{slots}/{max_slots}"
        
        return {
            "name": self.name,
            "race": self.race,
            "class": f"{self.char_class} {self.level}",
            "background": self.background,
            "alignment": self.alignment,
            "sorcerous_origin": self.sorcerous_origin if self.sorcerous_origin else "Not chosen",
            "dragon_ancestor": self.dragon_ancestor if self.dragon_ancestor else "Not chosen",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": self.ac,
            "speed": 30,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "constitution": self._get_modifier("constitution") + self.get_proficiency_bonus(),
                "charisma": self._get_modifier("charisma") + self.get_proficiency_bonus()
            },
            
            "skills": self.skill_proficiencies,
            "languages": self.languages_known,
            
            "spellcasting": {
                "spell_save_dc": self.get_spell_save_dc(),
                "spell_attack_bonus": self.get_spell_attack_bonus(),
                "spell_slots": spell_slots_display,
                "sorcery_points": f"{self.sorcery_points}/{self.max_sorcery_points}",
                "cantrips_known": self.cantrips_known,
                "spells_known": self.spells_known
            },
            
            "metamagic_options": list(self.metamagic_options),
            
            "features": {
                "Spellcasting": True,
                "Sorcerous Origin": self.sorcerous_origin != "",
                "Font of Magic": self.level >= 2,
                "Metamagic": f"{len(self.metamagic_options)}/{self.available_metamagic_count} options",
                "Ability Score Improvements": f"{self.ability_score_improvements} available",
                "Sorcerous Restoration": self.level >= 20,
                "Draconic Resilience": self.draconic_resilience_active,
                "Elemental Affinity": self.elemental_affinity_active,
                "Dragon Wings": self.dragon_wings_active,
                "Draconic Presence": self.draconic_presence_available
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
        origin_str = f" ({self.sorcerous_origin})" if self.sorcerous_origin else ""
        spells_str = f" | Spells: {len(self.spells_known)} known"
        sorcery_str = f" | Sorcery Points: {self.sorcery_points}/{self.max_sorcery_points}" if self.level >= 2 else ""
        
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{origin_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac}{spells_str}{sorcery_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Sorcerer
    sorcerer = Sorcerer(
        name="Aelar the Arcane",
        race="Half-Elf",
        char_class="Sorcerer",
        background="Sage",
        level=1,
        stats={
            "strength": 8,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 12,
            "wisdom": 10,
            "charisma": 16
        },
        alignment="Chaotic Good",
        personality_traits=["I'm driven by a wanderlust that led me away from home", "I have learned to live with the voices in my head"],
        ideal="Freedom. Everyone should be free to pursue their own lives",
        bond="I owe my survival to another urchin who taught me to live on the streets",
        flaw="I am too enamored of ale, wine, and other intoxicants"
    )
    
    # Set starting equipment
    sorcerer.inventory = ["Light Crossbow", "20 Bolts", "Component Pouch", "Dagger", "Dagger", "Explorer's Pack"]
    
    print("=" * 60)
    print("SORCERER CHARACTER SHEET")
    print("=" * 60)
    print(sorcerer)
    print()
    
    # Display character sheet
    sheet = sorcerer.get_character_sheet()
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
    
    print("Spellcasting:")
    print(f"  Spell Save DC: {sheet['spellcasting']['spell_save_dc']}")
    print(f"  Spell Attack Bonus: +{sheet['spellcasting']['spell_attack_bonus']}")
    print(f"  Sorcery Points: {sheet['spellcasting']['sorcery_points']}")
    print()
    
    print("Spell Slots:")
    for level, slots in sheet['spellcasting']['spell_slots'].items():
        print(f"  {level}: {slots}")
    print()
    
    print(f"Cantrips Known: {', '.join(sheet['spellcasting']['cantrips_known'])}")
    print(f"Spells Known: {', '.join(sheet['spellcasting']['spells_known'])}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    print("Equipment:")
    for item in sorcerer.inventory:
        print(f"  • {item}")
    print()
    
    # Test leveling up and metamagic
    print("=" * 60)
    print("TESTING LEVEL UP AND METAMAGIC")
    print("=" * 60)
    
    print(f"\nCurrent level: {sorcerer.level}")
    print(f"Current HP: {sorcerer.hp}/{sorcerer.max_hp}")
    
    # Level up to 3 to get metamagic
    sorcerer.level_up()  # Level 2 - Font of Magic
    sorcerer.level_up()  # Level 3 - Metamagic
    
    # Choose Draconic Bloodline
    sorcerer.sorcerous_origin = "Draconic Bloodline"
    sorcerer.dragon_ancestor = "Gold"
    sorcerer.dragon_damage_type = "Fire"
    
    # Add some metamagic options
    sorcerer.add_metamagic_option("Quickened Spell")
    sorcerer.add_metamagic_option("Twinned Spell")
    
    sorcerer.apply_level_features()
    
    print(f"\nAfter level up to Level {sorcerer.level}:")
    print(f"New HP: {sorcerer.hp}/{sorcerer.max_hp}")
    print(f"Sorcerous Origin: {sorcerer.sorcerous_origin}")
    print(f"Dragon Ancestor: {sorcerer.dragon_ancestor}")
    print(f"Metamagic Options: {', '.join(sorcerer.metamagic_options)}")
    print(f"Sorcery Points: {sorcerer.sorcery_points}/{sorcerer.max_sorcery_points}")
    
    # Test spell slots
    print(f"\nSpell Slots:")
    for level, slots in sorted(sorcerer.spell_slots.items()):
        print(f"  Level {level}: {slots}")
    
    # Test flexible casting
    print("\n" + "=" * 60)
    print("TESTING FLEXIBLE CASTING")
    print("=" * 60)
    
    print(f"\nInitial sorcery points: {sorcerer.sorcery_points}")
    print("Converting Level 1 spell slot to sorcery points...")
    if sorcerer.flexible_casting_convert_slot(1):
        print("✓ Conversion successful!")
        print(f"Sorcery points: {sorcerer.sorcery_points}")
        print(f"Level 1 slots: {sorcerer.spell_slots.get(1, 0)}")
    
    print("\nCreating Level 2 spell slot from sorcery points...")
    if sorcerer.flexible_casting_create_slot(2):
        print("✓ Creation successful!")
        print(f"Sorcery points: {sorcerer.sorcery_points}")
        print(f"Level 2 slots: {sorcerer.spell_slots.get(2, 0)}")
    
    # Test metamagic
    print("\n" + "=" * 60)
    print("TESTING METAMAGIC")
    print("=" * 60)
    
    print(f"\nUsing Quickened Spell on a cantrip...")
    if sorcerer.use_metamagic("Quickened Spell"):
        print("✓ Metamagic applied!")
        print(f"Remaining sorcery points: {sorcerer.sorcery_points}")
    
    print(f"\nUsing Twinned Spell on a Level 1 spell...")
    if sorcerer.use_metamagic("Twinned Spell", 1):
        print("✓ Metamagic applied!")
        print(f"Remaining sorcery points: {sorcerer.sorcery_points}")
    
    print("\n" + "=" * 60)
    print(sorcerer)
    print("=" * 60)