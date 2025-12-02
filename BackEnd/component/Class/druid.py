#!/usr/bin/env python3
"""
Druid Class - D&D 5e SRD Implementation
Derived from the base Character class with full Druid features
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional


from Class.Character import Character


@dataclass
class Druid(Character):
    """
    Druid class implementation following D&D 5e SRD
    Inherits from Character and adds Druid-specific features
    """
    
    # Druid Circle
    druid_circle: str = ""  # "Circle of the Land" or "Circle of the Moon"
    circle_land_type: str = ""  # arctic, coast, desert, forest, grassland, mountain, swamp
    
    # Spellcasting attributes
    cantrips_known: int = 2
    known_cantrips: List[str] = field(default_factory=list)
    prepared_spells: List[str] = field(default_factory=list)
    spell_slots: Dict[int, int] = field(default_factory=dict)  # {level: max_slots}
    spell_slots_used: Dict[int, int] = field(default_factory=dict)  # {level: used_slots}
    spellcasting_ability: str = "wisdom"
    
    # Wild Shape attributes
    wild_shape_uses: int = 2
    wild_shape_uses_remaining: int = 2
    wild_shape_max_cr: float = 0.25
    wild_shape_max_hours: int = 1
    wild_shape_can_fly: bool = False
    wild_shape_can_swim: bool = False
    currently_wild_shaped: bool = False
    wild_shape_beast: str = ""
    wild_shape_hp: int = 0
    
    # Druid features
    druidic_language: bool = True  # Level 1
    natural_recovery_available: bool = False  # Level 2 (Circle of the Land)
    natural_recovery_used: bool = False
    lands_stride: bool = False  # Level 6 (Circle of the Land)
    natures_ward: bool = False  # Level 10 (Circle of the Land)
    natures_sanctuary: bool = False  # Level 14 (Circle of the Land)
    
    # High-level features
    timeless_body: bool = False  # Level 18
    beast_spells: bool = False  # Level 18
    archdruid: bool = False  # Level 20
    
    # Circle of the Land bonus spells
    circle_spells: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize Druid with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Druid"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Druids typically have high WIS, good CON and DEX
            self.stats = {
                "strength": 10,
                "dexterity": 13,
                "constitution": 14,
                "intelligence": 12,
                "wisdom": 15,
                "charisma": 8
            }
        
        # Set hit points based on level (1d8 per level)
        if self.level == 1:
            self.max_hp = 90
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Druids choose two from: Arcana, Animal Handling, Insight, 
            # Medicine, Nature, Perception, Religion, Survival
            self.skill_proficiencies = ["Nature", "Perception"]
        
        if not self.languages_known:
            self.languages_known = ["Common", "Druidic"]
        elif "Druidic" not in self.languages_known:
            self.languages_known.append("Druidic")
        
        # Initialize spell slots if not set
        if not self.spell_slots:
            self.initialize_spell_slots()
        
        if not self.spell_slots_used:
            self.spell_slots_used = {i: 0 for i in range(1, 10)}
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
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
    
    def initialize_spell_slots(self):
        """Initialize spell slots based on level"""
        # Spell slot progression table from SRD
        slots_by_level = {
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
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
        }
        
        self.spell_slots = slots_by_level.get(self.level, {1: 2})
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Cantrips known progression
        if self.level >= 1:
            self.cantrips_known = 2
        if self.level >= 4:
            self.cantrips_known = 3
        if self.level >= 10:
            self.cantrips_known = 4
        
        # Wild Shape progression
        if self.level >= 2:
            self.wild_shape_max_cr = 0.25
            self.wild_shape_max_hours = self.level // 2
            self.wild_shape_can_fly = False
            self.wild_shape_can_swim = False
        
        if self.level >= 4:
            self.wild_shape_max_cr = 0.5
            self.wild_shape_can_swim = True
        
        if self.level >= 8:
            self.wild_shape_max_cr = 1.0
            self.wild_shape_can_fly = True
        
        # High-level features
        if self.level >= 18:
            self.timeless_body = True
            self.beast_spells = True
        
        if self.level >= 20:
            self.archdruid = True
            self.wild_shape_uses = 999  # Unlimited
        
        # Circle of the Land features
        if self.druid_circle == "Circle of the Land":
            if self.level >= 2:
                self.natural_recovery_available = True
            if self.level >= 6:
                self.lands_stride = True
            if self.level >= 10:
                self.natures_ward = True
            if self.level >= 14:
                self.natures_sanctuary = True
            
            # Add circle spells based on land type and level
            self.update_circle_spells()
        
        # Initialize spell slots
        self.initialize_spell_slots()
    
    def update_circle_spells(self):
        """Update circle spells based on land type and level"""
        if self.druid_circle != "Circle of the Land" or not self.circle_land_type:
            return
        
        circle_spell_lists = {
            "arctic": {
                3: ["hold person", "spike growth"],
                5: ["sleet storm", "slow"],
                7: ["freedom of movement", "ice storm"],
                9: ["commune with nature", "cone of cold"]
            },
            "coast": {
                3: ["mirror image", "misty step"],
                5: ["water breathing", "water walk"],
                7: ["control water", "freedom of movement"],
                9: ["conjure elemental", "scrying"]
            },
            "desert": {
                3: ["blur", "silence"],
                5: ["create food and water", "protection from energy"],
                7: ["blight", "hallucinatory terrain"],
                9: ["insect plague", "wall of stone"]
            },
            "forest": {
                3: ["barkskin", "spider climb"],
                5: ["call lightning", "plant growth"],
                7: ["divination", "freedom of movement"],
                9: ["commune with nature", "tree stride"]
            },
            "grassland": {
                3: ["invisibility", "pass without trace"],
                5: ["daylight", "haste"],
                7: ["divination", "freedom of movement"],
                9: ["dream", "insect plague"]
            },
            "mountain": {
                3: ["spider climb", "spike growth"],
                5: ["lightning bolt", "meld into stone"],
                7: ["stone shape", "stoneskin"],
                9: ["passwall", "wall of stone"]
            },
            "swamp": {
                3: ["acid arrow", "darkness"],
                5: ["water walk", "stinking cloud"],
                7: ["freedom of movement", "locate creature"],
                9: ["insect plague", "scrying"]
            }
        }
        
        land_spells = circle_spell_lists.get(self.circle_land_type.lower(), {})
        self.circle_spells = []
        
        for spell_level, spells in land_spells.items():
            if self.level >= spell_level:
                self.circle_spells.extend(spells)
    
    def get_spell_save_dc(self) -> int:
        """Calculate spell save DC: 8 + proficiency bonus + WIS modifier"""
        return 8 + self.get_proficiency_bonus() + self._get_modifier("wisdom")
    
    def get_spell_attack_bonus(self) -> int:
        """Calculate spell attack bonus: proficiency bonus + WIS modifier"""
        return self.get_proficiency_bonus() + self._get_modifier("wisdom")
    
    def get_max_prepared_spells(self) -> int:
        """Calculate max prepared spells: WIS modifier + druid level (min 1)"""
        return max(1, self._get_modifier("wisdom") + self.level)
    
    def prepare_spell(self, spell: str) -> bool:
        """Prepare a spell (can be done on long rest)"""
        if len(self.prepared_spells) >= self.get_max_prepared_spells():
            return False
        
        if spell not in self.prepared_spells:
            self.prepared_spells.append(spell)
            return True
        return False
    
    def unprepare_spell(self, spell: str) -> bool:
        """Unprepare a spell"""
        if spell in self.prepared_spells:
            self.prepared_spells.remove(spell)
            return True
        return False
    
    def cast_spell(self, spell_level: int) -> bool:
        """Cast a spell using a spell slot"""
        if spell_level < 1 or spell_level > 9:
            return False
        
        # Check if slot is available
        max_slots = self.spell_slots.get(spell_level, 0)
        used_slots = self.spell_slots_used.get(spell_level, 0)
        
        if used_slots >= max_slots:
            return False
        
        # Can't cast spells while wild shaped (unless level 18+)
        if self.currently_wild_shaped and not self.beast_spells:
            return False
        
        self.spell_slots_used[spell_level] = used_slots + 1
        return True
    
    def enter_wild_shape(self, beast_name: str, beast_hp: int) -> bool:
        """
        Enter Wild Shape form
        Returns True if successful, False otherwise
        """
        if self.level < 2:
            return False
        
        if self.wild_shape_uses_remaining <= 0:
            return False
        
        if self.currently_wild_shaped:
            return False
        
        self.currently_wild_shaped = True
        self.wild_shape_beast = beast_name
        self.wild_shape_hp = beast_hp
        self.wild_shape_uses_remaining -= 1
        return True
    
    def exit_wild_shape(self, damage_taken: int = 0) -> int:
        """
        Exit Wild Shape form
        Returns overflow damage to apply to normal form
        """
        if not self.currently_wild_shaped:
            return 0
        
        overflow_damage = 0
        if damage_taken > self.wild_shape_hp:
            overflow_damage = damage_taken - self.wild_shape_hp
        
        self.currently_wild_shaped = False
        self.wild_shape_beast = ""
        self.wild_shape_hp = 0
        
        return overflow_damage
    
    def natural_recovery(self, spell_levels_to_recover: List[int]) -> bool:
        """
        Use Natural Recovery (Circle of the Land, Level 2)
        Recover spell slots during short rest
        Total spell levels recovered <= druid level / 2 (rounded up)
        No slot can be 6th level or higher
        """
        if not self.natural_recovery_available:
            return False
        
        if self.natural_recovery_used:
            return False
        
        # Check if any slot is 6th level or higher
        if any(level >= 6 for level in spell_levels_to_recover):
            return False
        
        # Check total levels don't exceed limit
        max_recovery = (self.level + 1) // 2  # Round up
        if sum(spell_levels_to_recover) > max_recovery:
            return False
        
        # Recover the slots
        for level in spell_levels_to_recover:
            if level in self.spell_slots_used:
                self.spell_slots_used[level] = max(0, self.spell_slots_used[level] - 1)
        
        self.natural_recovery_used = True
        return True
    
    def short_rest(self):
        """Restore Wild Shape uses on short rest"""
        self.wild_shape_uses_remaining = self.wild_shape_uses
        # Natural Recovery can be used during short rest
        # (but tracking whether it's used is handled separately)
    
    def long_rest(self):
        """Reset resources on long rest"""
        self.wild_shape_uses_remaining = self.wild_shape_uses
        self.currently_wild_shaped = False
        self.wild_shape_beast = ""
        self.wild_shape_hp = 0
        self.hp = self.max_hp
        self.natural_recovery_used = False
        
        # Restore all spell slots
        for level in self.spell_slots_used:
            self.spell_slots_used[level] = 0
        
        # Can change prepared spells on long rest
        # (handled by player choosing new spells)
    
    def level_up(self):
        """Level up the druid"""
        self.level += 1
        
        # Increase HP (1d8 + CON mod per level, or 5 + CON mod average)
        hp_gain = 5 + self._get_modifier("constitution")
        self.max_hp += hp_gain
        self.hp += hp_gain
        
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
            "druid_circle": self.druid_circle if self.druid_circle else "Not chosen (Level 2+)",
            "circle_land": self.circle_land_type if self.circle_land_type else "N/A",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": self.ac,
            "speed": 30,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "intelligence": self._get_modifier("intelligence") + self.get_proficiency_bonus(),
                "wisdom": self._get_modifier("wisdom") + self.get_proficiency_bonus()
            },
            
            "skills": self.skill_proficiencies,
            "languages": self.languages_known,
            
            "spellcasting": {
                "spell_save_dc": self.get_spell_save_dc(),
                "spell_attack_bonus": f"+{self.get_spell_attack_bonus()}",
                "cantrips_known": f"{len(self.known_cantrips)}/{self.cantrips_known}",
                "spells_prepared": f"{len(self.prepared_spells)}/{self.get_max_prepared_spells()}",
                "spell_slots": {
                    level: f"{self.spell_slots_used.get(level, 0)}/{slots}"
                    for level, slots in self.spell_slots.items()
                }
            },
            
            "wild_shape": {
                "uses": f"{self.wild_shape_uses - self.wild_shape_uses_remaining}/{self.wild_shape_uses}",
                "max_cr": self.wild_shape_max_cr,
                "max_duration": f"{self.wild_shape_max_hours} hours",
                "can_fly": self.wild_shape_can_fly,
                "can_swim": self.wild_shape_can_swim,
                "currently_active": self.currently_wild_shaped,
                "current_beast": self.wild_shape_beast if self.currently_wild_shaped else "N/A"
            },
            
            "features": {
                "Druidic": self.druidic_language,
                "Natural Recovery": self.natural_recovery_available,
                "Land's Stride": self.lands_stride,
                "Nature's Ward": self.natures_ward,
                "Nature's Sanctuary": self.natures_sanctuary,
                "Timeless Body": self.timeless_body,
                "Beast Spells": self.beast_spells,
                "Archdruid": self.archdruid
            },
            
            "circle_spells": self.circle_spells,
            "known_cantrips": self.known_cantrips,
            "prepared_spells": self.prepared_spells,
            
            
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
        circle_str = f" ({self.druid_circle})" if self.druid_circle else ""
        wild_shape_str = f"Wild Shape: {self.wild_shape_uses_remaining}/{self.wild_shape_uses}"
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{circle_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac} | {wild_shape_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Druid
    druid = Druid(
        name="Keyleth",
        race="Half-Elf",
        char_class="Druid",
        background="Acolyte",
        level=1,
        stats={
            "strength": 10,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 12,
            "wisdom": 16,
            "charisma": 10
        },
        alignment="Neutral Good",
        personality_traits=["I see omens in every event", "I am tolerant of other faiths"],
        ideal="Nature. The natural world is more important than constructs of civilization",
        bond="I seek to preserve a sacred grove",
        flaw="I put too much trust in those who wield power within my temple's hierarchy"
    )
    
    
    # Add some starting cantrips
    druid.known_cantrips = ["Druidcraft", "Produce Flame"]
    
    print("=" * 60)
    print("DRUID CHARACTER SHEET")
    print("=" * 60)
    print(druid)
    print()
    
    # Display character sheet
    sheet = druid.get_character_sheet()
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
    print(f"  Spell Attack: {sheet['spellcasting']['spell_attack_bonus']}")
    print(f"  Cantrips Known: {sheet['spellcasting']['cantrips_known']}")
    print(f"  Spells Prepared: {sheet['spellcasting']['spells_prepared']}")
    print(f"  Spell Slots:")
    for level, slots in sheet['spellcasting']['spell_slots'].items():
        print(f"    Level {level}: {slots}")
    print()
    
    print("Known Cantrips:")
    for cantrip in druid.known_cantrips:
        print(f"  • {cantrip}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    # Test leveling up to 2 and choosing Circle
    print("=" * 60)
    print("TESTING LEVEL UP TO 2")
    print("=" * 60)
    
    print(f"\nCurrent level: {druid.level}")
    print(f"Wild Shape uses: {druid.wild_shape_uses}")
    
    druid.level_up()
    druid.druid_circle = "Circle of the Land"
    druid.circle_land_type = "Forest"
    druid.apply_level_features()
    
    print(f"\nAfter level up:")
    print(f"New level: {druid.level}")
    print(f"Druid Circle: {druid.druid_circle}")
    print(f"Land Type: {druid.circle_land_type}")
    print(f"Wild Shape uses: {druid.wild_shape_uses}")
    print(f"Wild Shape max CR: {druid.wild_shape_max_cr}")
    print(f"Wild Shape duration: {druid.wild_shape_max_hours} hours")
    print(f"Natural Recovery available: {druid.natural_recovery_available}")
    
    # Test Wild Shape
    print("\n" + "=" * 60)
    print("TESTING WILD SHAPE")
    print("=" * 60)
    
    print(f"\nWild Shape uses remaining: {druid.wild_shape_uses_remaining}")
    print("\nEntering Wild Shape (Wolf form, 11 HP)...")
    if druid.enter_wild_shape("Wolf", 11):
        print("✓ Wild Shape activated!")
        print(f"  Current form: {druid.wild_shape_beast}")
        print(f"  Wild Shape HP: {druid.wild_shape_hp}")
        print(f"  Uses remaining: {druid.wild_shape_uses_remaining}")
    
    print("\nExiting Wild Shape...")
    overflow = druid.exit_wild_shape(0)
    print(f"✓ Wild Shape ended (overflow damage: {overflow})")
    
    # Test spell casting
    print("\n" + "=" * 60)
    print("TESTING SPELLCASTING")
    print("=" * 60)
    
    druid.prepared_spells = ["Cure Wounds", "Entangle", "Goodberry"]
    print(f"\nPrepared spells: {', '.join(druid.prepared_spells)}")
    print(f"Max prepared: {druid.get_max_prepared_spells()}")
    print(f"\nLevel 1 spell slots: {druid.spell_slots[1]}")
    
    print("\nCasting Cure Wounds (Level 1)...")
    if druid.cast_spell(1):
        print("✓ Spell cast successfully!")
        print(f"  Slots remaining: {druid.spell_slots[1] - druid.spell_slots_used[1]}/{druid.spell_slots[1]}")
    
    # Level up to 3 to get circle spells
    print("\n" + "=" * 60)
    print("TESTING LEVEL 3 - CIRCLE SPELLS")
    print("=" * 60)
    
    druid.level_up()
    druid.apply_level_features()
    
    print(f"\nLevel: {druid.level}")
    print(f"Circle Spells (automatically prepared):")
    for spell in druid.circle_spells:
        print(f"  • {spell}")
    
    print("\n" + "=" * 60)
    print(druid)
    print("=" * 60)