#!/usr/bin/env python3
"""
Warlock Class - D&D 5e SRD Implementation
Derived from the base Character class with full Warlock features
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from Head.campaign_manager import Character


@dataclass
class Warlock(Character):
    """
    Warlock class implementation following D&D 5e SRD
    Inherits from Character and adds Warlock-specific features
    """
    
    # Warlock-specific attributes
    otherworldly_patron: str = ""  # "The Fiend", "The Archfey", "The Great Old One"
    pact_boon: str = ""  # "Pact of the Chain", "Pact of the Blade", "Pact of the Tome"
    
    # Pact Magic mechanics
    cantrips_known: int = 2
    spells_known: int = 2
    spell_slots: int = 1
    spell_slot_level: int = 1
    spell_slots_used: int = 0
    
    # Eldritch Invocations
    eldritch_invocations_known: int = 0
    eldritch_invocations: Set[str] = field(default_factory=set)
    
    # Mystic Arcanum
    mystic_arcanum_6: str = ""
    mystic_arcanum_7: str = ""
    mystic_arcanum_8: str = ""
    mystic_arcanum_9: str = ""
    mystic_arcanum_used: Dict[str, bool] = field(default_factory=dict)
    
    # Spellcasting
    spellcasting_ability: str = "charisma"
    
    # Pact-specific features
    has_familiar: bool = False
    familiar_form: str = ""
    pact_weapon: str = ""
    book_of_shadows: bool = False
    book_of_shadows_cantrips: Set[str] = field(default_factory=set)
    
    # The Fiend patron features
    dark_ones_blessing_thp: int = 0
    dark_ones_own_luck_used: bool = False
    fiendish_resistance_type: str = ""
    hurl_through_hell_used: bool = False
    
    def __post_init__(self):
        """Initialize Warlock with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Warlock"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Warlocks typically have high CHA
            self.stats = {
                "strength": 8,
                "dexterity": 14,
                "constitution": 13,
                "intelligence": 12,
                "wisdom": 10,
                "charisma": 15
            }
        
        # Set hit points based on level (1d8 per level)
        if self.level == 1:
            self.max_hp = 8 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Warlocks choose two from: Arcana, Deception, History, Intimidation, 
            # Investigation, Nature, and Religion
            self.skill_proficiencies = ["Deception", "Intimidation"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Update spellcasting and invocation progression based on level
        level_features = {
            1: {"cantrips": 2, "spells_known": 2, "slots": 1, "slot_level": 1, "invocations": 0},
            2: {"cantrips": 2, "spells_known": 3, "slots": 2, "slot_level": 1, "invocations": 2},
            3: {"cantrips": 2, "spells_known": 4, "slots": 2, "slot_level": 2, "invocations": 2},
            4: {"cantrips": 3, "spells_known": 5, "slots": 2, "slot_level": 2, "invocations": 2},
            5: {"cantrips": 3, "spells_known": 6, "slots": 2, "slot_level": 3, "invocations": 3},
            6: {"cantrips": 3, "spells_known": 7, "slots": 2, "slot_level": 3, "invocations": 3},
            7: {"cantrips": 3, "spells_known": 8, "slots": 2, "slot_level": 4, "invocations": 4},
            8: {"cantrips": 3, "spells_known": 9, "slots": 2, "slot_level": 4, "invocations": 4},
            9: {"cantrips": 3, "spells_known": 10, "slots": 2, "slot_level": 5, "invocations": 5},
            10: {"cantrips": 4, "spells_known": 10, "slots": 2, "slot_level": 5, "invocations": 5},
            11: {"cantrips": 4, "spells_known": 11, "slots": 3, "slot_level": 5, "invocations": 5},
            12: {"cantrips": 4, "spells_known": 11, "slots": 3, "slot_level": 5, "invocations": 6},
            13: {"cantrips": 4, "spells_known": 12, "slots": 3, "slot_level": 5, "invocations": 6},
            14: {"cantrips": 4, "spells_known": 12, "slots": 3, "slot_level": 5, "invocations": 6},
            15: {"cantrips": 4, "spells_known": 13, "slots": 3, "slot_level": 5, "invocations": 7},
            16: {"cantrips": 4, "spells_known": 13, "slots": 3, "slot_level": 5, "invocations": 7},
            17: {"cantrips": 4, "spells_known": 14, "slots": 4, "slot_level": 5, "invocations": 7},
            18: {"cantrips": 4, "spells_known": 14, "slots": 4, "slot_level": 5, "invocations": 8},
            19: {"cantrips": 4, "spells_known": 15, "slots": 4, "slot_level": 5, "invocations": 8},
            20: {"cantrips": 4, "spells_known": 15, "slots": 4, "slot_level": 5, "invocations": 8}
        }
        
        # Apply current level features
        if self.level in level_features:
            features = level_features[self.level]
            self.cantrips_known = features["cantrips"]
            self.spells_known = features["spells_known"]
            self.spell_slots = features["slots"]
            self.spell_slot_level = features["slot_level"]
            self.eldritch_invocations_known = features["invocations"]
        
        # Apply Otherworldly Patron at level 1
        if self.level >= 1 and self.otherworldly_patron:
            # Apply Fiend patron features if chosen
            if self.otherworldly_patron == "The Fiend":
                pass  # Features applied when used
        
        # Apply Pact Boon at level 3
        if self.level >= 3 and self.pact_boon:
            if self.pact_boon == "Pact of the Chain":
                self.has_familiar = True
            elif self.pact_boon == "Pact of the Tome":
                self.book_of_shadows = True
        
        # Apply Mystic Arcanum at appropriate levels
        if self.level >= 11 and not self.mystic_arcanum_6:
            self.mystic_arcanum_6 = "Choose a 6th-level spell"
        if self.level >= 13 and not self.mystic_arcanum_7:
            self.mystic_arcanum_7 = "Choose a 7th-level spell"
        if self.level >= 15 and not self.mystic_arcanum_8:
            self.mystic_arcanum_8 = "Choose an 8th-level spell"
        if self.level >= 17 and not self.mystic_arcanum_9:
            self.mystic_arcanum_9 = "Choose a 9th-level spell"
    
    def get_spell_save_dc(self) -> int:
        """Calculate spell save DC: 8 + proficiency + CHA mod"""
        return 8 + self.get_proficiency_bonus() + self._get_modifier("charisma")
    
    def get_spell_attack_bonus(self) -> int:
        """Calculate spell attack bonus: proficiency + CHA mod"""
        return self.get_proficiency_bonus() + self._get_modifier("charisma")
    
    def use_spell_slot(self) -> bool:
        """
        Use a spell slot.
        Returns True if successful, False if no slots available.
        """
        if self.spell_slots_used >= self.spell_slots:
            return False
        
        self.spell_slots_used += 1
        return True
    
    def regain_spell_slots(self):
        """Regain all expended spell slots (short rest)"""
        self.spell_slots_used = 0
    
    def short_rest(self):
        """Reset short rest resources"""
        self.regain_spell_slots()
        self.dark_ones_own_luck_used = False
    
    def long_rest(self):
        """Reset resources on long rest"""
        self.regain_spell_slots()
        self.dark_ones_own_luck_used = False
        self.hurl_through_hell_used = False
        self.mystic_arcanum_used = {}  # Reset all Mystic Arcanum uses
        self.hp = self.max_hp
        self.dark_ones_blessing_thp = 0  # Temporary HP from Dark One's Blessing
    
    def add_eldritch_invocation(self, invocation: str) -> bool:
        """
        Add an eldritch invocation if slots are available.
        Returns True if successful, False otherwise.
        """
        if len(self.eldritch_invocations) >= self.eldritch_invocations_known:
            return False
        
        self.eldritch_invocations.add(invocation)
        return True
    
    def remove_eldritch_invocation(self, invocation: str) -> bool:
        """
        Remove an eldritch invocation.
        Returns True if successful, False if not found.
        """
        if invocation in self.eldritch_invocations:
            self.eldritch_invocations.remove(invocation)
            return True
        return False
    
    def use_mystic_arcanum(self, level: int) -> bool:
        """
        Use a Mystic Arcanum spell.
        Returns True if successful, False if already used.
        """
        arcanum_key = f"arcanum_{level}"
        
        if self.mystic_arcanum_used.get(arcanum_key, False):
            return False
        
        self.mystic_arcanum_used[arcanum_key] = True
        return True
    
    # The Fiend patron features
    def dark_ones_blessing(self, warlock_level: int):
        """
        Gain temporary HP when reducing hostile creature to 0 HP.
        THP = CHA mod + warlock level (minimum 1)
        """
        cha_mod = self._get_modifier("charisma")
        self.dark_ones_blessing_thp = max(cha_mod + warlock_level, 1)
    
    def dark_ones_own_luck(self) -> bool:
        """
        Add d10 to ability check or saving throw.
        Returns True if successful, False if already used.
        """
        if self.dark_ones_own_luck_used:
            return False
        
        self.dark_ones_own_luck_used = True
        return True
    
    def set_fiendish_resistance(self, damage_type: str):
        """Set damage type resistance for Fiendish Resilience"""
        self.fiendish_resistance_type = damage_type
    
    def hurl_through_hell(self) -> bool:
        """
        Use Hurl Through Hell feature.
        Returns True if successful, False if already used.
        """
        if self.hurl_through_hell_used:
            return False
        
        self.hurl_through_hell_used = True
        return True
    
    # Pact Boon features
    def create_pact_weapon(self, weapon_form: str = "Longsword"):
        """Create a pact weapon (Pact of the Blade)"""
        if self.pact_boon == "Pact of the Blade":
            self.pact_weapon = weapon_form
    
    def dismiss_pact_weapon(self):
        """Dismiss pact weapon"""
        self.pact_weapon = ""
    
    def add_tome_cantrip(self, cantrip: str) -> bool:
        """
        Add a cantrip to Book of Shadows (Pact of the Tome)
        Returns True if successful, False if at capacity.
        """
        if not self.book_of_shadows:
            return False
        
        if len(self.book_of_shadows_cantrips) >= 3:
            return False
        
        self.book_of_shadows_cantrips.add(cantrip)
        return True
    
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
    
    def eldritch_master(self) -> bool:
        """
        Use Eldritch Master feature (Level 20).
        Regain all expended spell slots.
        Returns True if successful, False if already used since long rest.
        """
        if self.level < 20:
            return False
        
        # In actual implementation, would track if used since long rest
        # For now, just regain slots
        self.regain_spell_slots()
        return True
    
    def level_up(self):
        """Level up the warlock"""
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
            "otherworldly_patron": self.otherworldly_patron if self.otherworldly_patron else "Not chosen",
            "pact_boon": self.pact_boon if self.pact_boon else "Not chosen (Level 3+)",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "temporary_hp": self.dark_ones_blessing_thp,
            "armor_class": self.ac,
            "speed": 30,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "spellcasting": {
                "spellcasting_ability": self.spellcasting_ability,
                "spell_save_dc": self.get_spell_save_dc(),
                "spell_attack_bonus": self.get_spell_attack_bonus(),
                "cantrips_known": self.cantrips_known,
                "spells_known": self.spells_known,
                "spell_slots": f"{self.spell_slots_used}/{self.spell_slots}",
                "spell_slot_level": self.spell_slot_level
            },
            
            "mystic_arcanum": {
                "6th_level": self.mystic_arcanum_6 if self.mystic_arcanum_6 else "Not available",
                "7th_level": self.mystic_arcanum_7 if self.mystic_arcanum_7 else "Not available",
                "8th_level": self.mystic_arcanum_8 if self.mystic_arcanum_8 else "Not available",
                "9th_level": self.mystic_arcanum_9 if self.mystic_arcanum_9 else "Not available"
            },
            
            "eldritch_invocations": {
                "known": self.eldritch_invocations_known,
                "current": list(self.eldritch_invocations)
            },
            
            "pact_features": {
                "has_familiar": self.has_familiar,
                "familiar_form": self.familiar_form if self.has_familiar else "None",
                "pact_weapon": self.pact_weapon if self.pact_weapon else "None",
                "book_of_shadows": self.book_of_shadows,
                "tome_cantrips": list(self.book_of_shadows_cantrips) if self.book_of_shadows else []
            },
            
            "saving_throws": {
                "wisdom": self._get_modifier("wisdom") + self.get_proficiency_bonus(),
                "charisma": self._get_modifier("charisma") + self.get_proficiency_bonus()
            },
            
            "skills": self.skill_proficiencies,
            "languages": self.languages_known,
            
            "patron_features": {
                "Dark One's Blessing THP": self.dark_ones_blessing_thp if self.otherworldly_patron == "The Fiend" else "N/A",
                "Dark One's Own Luck Used": self.dark_ones_own_luck_used if self.otherworldly_patron == "The Fiend" else "N/A",
                "Fiendish Resistance": self.fiendish_resistance_type if self.otherworldly_patron == "The Fiend" else "N/A",
                "Hurl Through Hell Used": self.hurl_through_hell_used if self.otherworldly_patron == "The Fiend" else "N/A"
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
        patron_str = f" ({self.otherworldly_patron})" if self.otherworldly_patron else ""
        pact_str = f" [{self.pact_boon}]" if self.pact_boon else ""
        slots_str = f"Spell Slots: {self.spell_slots_used}/{self.spell_slots} (Level {self.spell_slot_level})"
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{patron_str}{pact_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac} | {slots_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Warlock
    warlock = Warlock(
        name="Zariel Bloodweaver",
        race="Tiefling",
        char_class="Warlock",
        background="Acolyte",
        level=1,
        stats={
            "strength": 8,
            "dexterity": 14,
            "constitution": 13,
            "intelligence": 12,
            "wisdom": 10,
            "charisma": 17
        },
        alignment="Neutral Evil",
        personality_traits=["I see omens in every event and action", "I am haunted by memories of my past"],
        ideal="Power. I hope to one day rise to the top of my faith's religious hierarchy",
        bond="I would die to recover an ancient relic of my faith",
        flaw="I am suspicious of strangers and expect the worst of them"
    )
    
    # Set starting equipment
    warlock.inventory = ["Light crossbow", "20 bolts", "Component pouch", "Scholar's pack", 
                        "Leather armor", "Dagger", "Dagger"]
    
    print("=" * 60)
    print("WARLOCK CHARACTER SHEET")
    print("=" * 60)
    print(warlock)
    print()
    
    # Display character sheet
    sheet = warlock.get_character_sheet()
    print(f"Name: {sheet['name']}")
    print(f"Class: {sheet['class']}")
    print(f"Race: {sheet['race']}")
    print(f"Background: {sheet['background']}")
    print(f"Alignment: {sheet['alignment']}")
    print()
    
    print(f"HP: {sheet['hit_points']} | AC: {sheet['armor_class']} | Speed: {sheet['speed']} ft")
    if sheet['temporary_hp'] > 0:
        print(f"Temporary HP: {sheet['temporary_hp']}")
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
    spellcasting = sheet['spellcasting']
    print(f"  Spell Save DC: {spellcasting['spell_save_dc']}")
    print(f"  Spell Attack Bonus: +{spellcasting['spell_attack_bonus']}")
    print(f"  Cantrips Known: {spellcasting['cantrips_known']}")
    print(f"  Spells Known: {spellcasting['spells_known']}")
    print(f"  Spell Slots: {spellcasting['spell_slots']} (Level {spellcasting['spell_slot_level']})")
    print()
    
    print("Eldritch Invocations:")
    invocations = sheet['eldritch_invocations']
    print(f"  Known: {invocations['known']}")
    print(f"  Current: {', '.join(invocations['current']) if invocations['current'] else 'None'}")
    print()
    
    # Test spell slot mechanics
    print("=" * 60)
    print("TESTING SPELL SLOT MECHANICS")
    print("=" * 60)
    
    print("\nUsing spell slot...")
    if warlock.use_spell_slot():
        print("✓ Spell slot used!")
        print(f"  Slots remaining: {warlock.spell_slots - warlock.spell_slots_used}/{warlock.spell_slots}")
    
    print("\nTaking short rest...")
    warlock.short_rest()
    print("✓ Spell slots regained")
    print(f"  Slots available: {warlock.spell_slots - warlock.spell_slots_used}/{warlock.spell_slots}")
    
    # Test leveling up
    print("\n" + "=" * 60)
    print("TESTING LEVEL UP")
    print("=" * 60)
    
    print(f"\nCurrent level: {warlock.level}")
    print(f"Current HP: {warlock.hp}/{warlock.max_hp}")
    print(f"Current spell slots: {warlock.spell_slots} (Level {warlock.spell_slot_level})")
    
    warlock.level_up()
    print(f"\nAfter level up to 2:")
    print(f"New level: {warlock.level}")
    print(f"New HP: {warlock.hp}/{warlock.max_hp}")
    print(f"New spell slots: {warlock.spell_slots} (Level {warlock.spell_slot_level})")
    print(f"Eldritch Invocations available: {warlock.eldritch_invocations_known}")
    
    # Add some invocations
    warlock.add_eldritch_invocation("Agonizing Blast")
    warlock.add_eldritch_invocation("Devil's Sight")
    
    # Level up to 3 and choose patron and pact
    warlock.level_up()
    warlock.otherworldly_patron = "The Fiend"
    warlock.pact_boon = "Pact of the Chain"
    warlock.familiar_form = "Imp"
    warlock.apply_level_features()
    
    print(f"\nLevel {warlock.level}:")
    print(f"  Patron chosen: {warlock.otherworldly_patron}")
    print(f"  Pact Boon: {warlock.pact_boon}")
    print(f"  Familiar: {warlock.familiar_form}")
    print(f"  Spell slots: {warlock.spell_slots} (Level {warlock.spell_slot_level})")
    
    # Test Fiend patron features
    print("\n" + "=" * 60)
    print("TESTING FIEND PATRON FEATURES")
    print("=" * 60)
    
    print("\nUsing Dark One's Blessing...")
    warlock.dark_ones_blessing(warlock.level)
    print(f"✓ Gained {warlock.dark_ones_blessing_thp} temporary HP")
    
    print("\nUsing Dark One's Own Luck...")
    if warlock.dark_ones_own_luck():
        print("✓ Added d10 to ability check/saving throw")
    
    print("\nSetting Fiendish Resistance...")
    warlock.set_fiendish_resistance("fire")
    print(f"✓ Resistance to {warlock.fiendish_resistance_type} damage")
    
    print("\n" + "=" * 60)
    print(warlock)
    print("=" * 60)