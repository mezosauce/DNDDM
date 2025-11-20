#!/usr/bin/env python3
"""
Wizard Class - D&D 5e SRD Implementation
Derived from the base Character class with full Wizard features
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional


from Head.campaign_manager import Character


@dataclass
class Wizard(Character):
    """
    Wizard class implementation following D&D 5e SRD
    Inherits from Character and adds Wizard-specific features
    """
    
    # Wizard-specific attributes (all with defaults to avoid dataclass issues)
    arcane_tradition: str = ""  # Chosen at level 2 (e.g., "School of Evocation")
    
    # Spellcasting attributes
    cantrips_known: int = 3
    spellbook: List[str] = field(default_factory=list)  # List of known spells
    prepared_spells: List[str] = field(default_factory=list)  # Currently prepared spells
    
    # Spell slots by level (1st through 9th level slots)
    spell_slots: Dict[int, int] = field(default_factory=lambda: {
        1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0
    })
    spell_slots_used: Dict[int, int] = field(default_factory=lambda: {
        1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0
    })
    
    # Arcane Recovery
    arcane_recovery_available: bool = True  # Resets on long rest
    arcane_recovery_slots_max: int = 1  # Max spell slot levels recoverable
    
    # High level features
    spell_mastery_1st: str = ""  # 1st level spell for Spell Mastery (level 18)
    spell_mastery_2nd: str = ""  # 2nd level spell for Spell Mastery (level 18)
    signature_spell_1: str = ""  # First 3rd level signature spell (level 20)
    signature_spell_2: str = ""  # Second 3rd level signature spell (level 20)
    signature_spell_1_used: bool = False
    signature_spell_2_used: bool = False
    
    # School of Evocation features
    evocation_savant: bool = False  # Level 2 Evocation
    sculpt_spells: bool = False  # Level 2 Evocation
    potent_cantrip: bool = False  # Level 6 Evocation
    empowered_evocation: bool = False  # Level 10 Evocation
    overchannel_available: bool = False  # Level 14 Evocation
    overchannel_uses: int = 0  # Track uses for damage calculation
    
    # Tradition features unlocked at certain levels
    tradition_feature_2: bool = False
    tradition_feature_6: bool = False
    tradition_feature_10: bool = False
    tradition_feature_14: bool = False
    
    def __post_init__(self):
        """Initialize Wizard with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Wizard"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Wizards typically have high INT and decent DEX/CON
            self.stats = {
                "strength": 8,
                "dexterity": 14,
                "constitution": 13,
                "intelligence": 16,
                "wisdom": 12,
                "charisma": 10
            }
        
        # Set hit points based on level (1d6 per level)
        if self.level == 1:
            self.max_hp = 6 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Wizards choose two from: Arcana, History, Insight, 
            # Investigation, Medicine, and Religion
            self.skill_proficiencies = ["Arcana", "Investigation"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        # Apply level-based features
        self.apply_level_features()
        
        # Initialize spellbook with 6 1st-level spells if empty
        if not self.spellbook and self.level >= 1:
            self.spellbook = [
                "Magic Missile", "Shield", "Mage Armor",
                "Detect Magic", "Identify", "Sleep"
            ]
    
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
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Cantrips progression
        if self.level >= 1:
            self.cantrips_known = 3
        if self.level >= 4:
            self.cantrips_known = 4
        if self.level >= 10:
            self.cantrips_known = 5
        
        # Spell slots progression based on Wizard table
        self.spell_slots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        
        if self.level >= 1:
            self.spell_slots[1] = 2
        if self.level >= 2:
            self.spell_slots[1] = 3
        if self.level >= 3:
            self.spell_slots[1] = 4
            self.spell_slots[2] = 2
        if self.level >= 4:
            self.spell_slots[2] = 3
        if self.level >= 5:
            self.spell_slots[3] = 2
        if self.level >= 6:
            self.spell_slots[3] = 3
        if self.level >= 7:
            self.spell_slots[4] = 1
        if self.level >= 8:
            self.spell_slots[4] = 2
        if self.level >= 9:
            self.spell_slots[4] = 3
            self.spell_slots[5] = 1
        if self.level >= 10:
            self.spell_slots[5] = 2
        if self.level >= 11:
            self.spell_slots[6] = 1
        if self.level >= 12:
            self.spell_slots[6] = 1  # Still 1
        if self.level >= 13:
            self.spell_slots[7] = 1
        if self.level >= 14:
            self.spell_slots[7] = 1  # Still 1
        if self.level >= 15:
            self.spell_slots[8] = 1
        if self.level >= 17:
            self.spell_slots[9] = 1
        if self.level >= 18:
            self.spell_slots[6] = 1  # Still 1
        if self.level >= 19:
            self.spell_slots[6] = 2
        if self.level >= 20:
            self.spell_slots[7] = 2
        
        # Arcane Recovery - can recover up to half wizard level (rounded up)
        self.arcane_recovery_slots_max = (self.level + 1) // 2
        
        # Arcane Tradition features
        if self.level >= 2:
            self.tradition_feature_2 = True
        if self.level >= 6:
            self.tradition_feature_6 = True
        if self.level >= 10:
            self.tradition_feature_10 = True
        if self.level >= 14:
            self.tradition_feature_14 = True
        
        # School of Evocation specific
        if self.arcane_tradition == "School of Evocation":
            if self.level >= 2:
                self.evocation_savant = True
                self.sculpt_spells = True
            if self.level >= 6:
                self.potent_cantrip = True
            if self.level >= 10:
                self.empowered_evocation = True
            if self.level >= 14:
                self.overchannel_available = True
    
    def get_spell_save_dc(self) -> int:
        """Calculate spell save DC: 8 + proficiency + INT modifier"""
        return 8 + self.get_proficiency_bonus() + self._get_modifier("intelligence")
    
    def get_spell_attack_bonus(self) -> int:
        """Calculate spell attack modifier: proficiency + INT modifier"""
        return self.get_proficiency_bonus() + self._get_modifier("intelligence")
    
    def get_max_prepared_spells(self) -> int:
        """Calculate max number of prepared spells: INT modifier + wizard level (min 1)"""
        return max(1, self._get_modifier("intelligence") + self.level)
    
    def prepare_spell(self, spell: str) -> bool:
        """
        Prepare a spell from the spellbook.
        Returns True if successful, False otherwise.
        """
        if spell not in self.spellbook:
            return False
        
        if spell in self.prepared_spells:
            return False
        
        if len(self.prepared_spells) >= self.get_max_prepared_spells():
            return False
        
        self.prepared_spells.append(spell)
        return True
    
    def unprepare_spell(self, spell: str) -> bool:
        """Remove a spell from prepared spells list"""
        if spell in self.prepared_spells:
            self.prepared_spells.remove(spell)
            return True
        return False
    
    def cast_spell(self, spell_level: int) -> bool:
        """
        Cast a spell by expending a spell slot.
        Returns True if slot available, False otherwise.
        """
        if spell_level < 1 or spell_level > 9:
            return False
        
        available_slots = self.spell_slots.get(spell_level, 0)
        used_slots = self.spell_slots_used.get(spell_level, 0)
        
        if used_slots >= available_slots:
            return False
        
        self.spell_slots_used[spell_level] += 1
        return True
    
    def add_spell_to_spellbook(self, spell: str) -> bool:
        """Add a new spell to the spellbook"""
        if spell not in self.spellbook:
            self.spellbook.append(spell)
            return True
        return False
    
    def use_arcane_recovery(self, slot_levels: List[int]) -> bool:
        """
        Use Arcane Recovery to recover spell slots during short rest.
        slot_levels: list of spell slot levels to recover (e.g., [1, 1, 2] for two 1st and one 2nd)
        Can recover slots up to half wizard level (rounded up), none can be 6th or higher.
        """
        if not self.arcane_recovery_available:
            return False
        
        # Check total level doesn't exceed limit
        total_levels = sum(slot_levels)
        if total_levels > self.arcane_recovery_slots_max:
            return False
        
        # Check no slots are 6th level or higher
        if any(level >= 6 for level in slot_levels):
            return False
        
        # Recover the slots
        for level in slot_levels:
            if level >= 1 and level <= 9:
                self.spell_slots_used[level] = max(0, self.spell_slots_used[level] - 1)
        
        self.arcane_recovery_available = False
        return True
    
    def short_rest(self):
        """Reset resources on short rest"""
        # Arcane Recovery can be used once per day (resets on long rest, not short rest)
        # Signature spells reset on short rest (level 20)
        if self.level >= 20:
            self.signature_spell_1_used = False
            self.signature_spell_2_used = False
    
    def long_rest(self):
        """Reset resources on long rest"""
        # Reset all spell slots
        self.spell_slots_used = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        
        # Reset Arcane Recovery
        self.arcane_recovery_available = True
        
        # Reset Overchannel uses
        self.overchannel_uses = 0
        
        # Reset Signature Spells
        self.signature_spell_1_used = False
        self.signature_spell_2_used = False
        
        # Reset HP
        self.hp = self.max_hp
        
        # Can change prepared spells on long rest
        # (This would be done manually by calling prepare_spell/unprepare_spell)
    
    def use_overchannel(self, spell_level: int) -> int:
        """
        Use Overchannel (Evocation level 14) to maximize damage.
        Returns necrotic damage taken (0 for first use, then escalating).
        Spell must be 1st-5th level.
        """
        if not self.overchannel_available:
            return -1
        
        if spell_level < 1 or spell_level > 5:
            return -1
        
        self.overchannel_uses += 1
        
        # First use has no damage
        if self.overchannel_uses == 1:
            return 0
        
        # Subsequent uses deal necrotic damage
        # Base damage: 2d12 per spell level
        # Each additional use: +1d12 per spell level
        dice_per_level = 1 + self.overchannel_uses
        total_damage = dice_per_level * spell_level * 12  # Assume max roll for simplicity
        
        return total_damage
    
    def level_up(self):
        """Level up the wizard"""
        self.level += 1
        
        # Increase HP (1d6 + CON mod per level, or 4 + CON mod average)
        hp_gain = 4 + self._get_modifier("constitution")
        self.max_hp += hp_gain
        self.hp += hp_gain
        
        # Add 2 new spells to spellbook (free on level up)
        # Note: In actual implementation, these would be chosen by player
        
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
            "arcane_tradition": self.arcane_tradition if self.arcane_tradition else "Not chosen (Level 2+)",
            
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
                "cantrips_known": self.cantrips_known,
                "spells_prepared": f"{len(self.prepared_spells)}/{self.get_max_prepared_spells()}",
                "spellbook_size": len(self.spellbook)
            },
            
            "spell_slots": {
                level: f"{self.spell_slots[level] - self.spell_slots_used.get(level, 0)}/{self.spell_slots[level]}"
                for level in range(1, 10) if self.spell_slots.get(level, 0) > 0
            },
            
            "features": {
                "Spellcasting": True,
                "Arcane Recovery": f"Can recover up to {self.arcane_recovery_slots_max} levels (Available: {self.arcane_recovery_available})",
                "Arcane Tradition": self.arcane_tradition if self.level >= 2 else False,
                "Spell Mastery": f"{self.spell_mastery_1st}, {self.spell_mastery_2nd}" if self.level >= 18 and self.spell_mastery_1st else False,
                "Signature Spells": f"{self.signature_spell_1}, {self.signature_spell_2}" if self.level >= 20 and self.signature_spell_1 else False
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
        tradition_str = f" ({self.arcane_tradition})" if self.arcane_tradition else ""
        spell_slots_str = f"Slots: {self.spell_slots[1] - self.spell_slots_used[1]}/{self.spell_slots[1]} 1st"
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{tradition_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac} | {spell_slots_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Wizard
    wizard = Wizard(
        name="Elminster",
        race="Human",
        char_class="Wizard",
        background="Sage",
        level=1,
        stats={
            "strength": 8,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 17,
            "wisdom": 12,
            "charisma": 10
        },
        alignment="Neutral Good",
        personality_traits=["I use polysyllabic words to convey my erudition", "I'm convinced that people are always trying to steal my secrets"],
        ideal="Knowledge. The path to power and self-improvement is through knowledge",
        bond="I've been searching my whole life for the answer to a certain question",
        flaw="I am easily distracted by the promise of information"
    )
    
    # Set starting equipment
    wizard.inventory = ["Quarterstaff", "Spellbook", "Component Pouch", "Scholar's Pack", "Dagger"]
    
    print("=" * 60)
    print("WIZARD CHARACTER SHEET")
    print("=" * 60)
    print(wizard)
    print()
    
    # Display character sheet
    sheet = wizard.get_character_sheet()
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
    print(f"  Spell Attack Bonus: {sheet['spellcasting']['spell_attack_bonus']}")
    print(f"  Cantrips Known: {sheet['spellcasting']['cantrips_known']}")
    print(f"  Spells Prepared: {sheet['spellcasting']['spells_prepared']}")
    print(f"  Spellbook Size: {sheet['spellcasting']['spellbook_size']}")
    print()
    
    print("Spell Slots:")
    for level, slots in sheet['spell_slots'].items():
        print(f"  Level {level}: {slots}")
    print()
    
    print("Spellbook:")
    for spell in wizard.spellbook[:6]:
        print(f"  • {spell}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    print("Equipment:")
    for item in wizard.inventory:
        print(f"  • {item}")
    print()
    
    # Test spellcasting mechanics
    print("=" * 60)
    print("TESTING SPELLCASTING MECHANICS")
    print("=" * 60)
    
    # Prepare spells
    print("\nPreparing spells...")
    max_prepared = wizard.get_max_prepared_spells()
    print(f"Can prepare up to {max_prepared} spells")
    
    spells_to_prepare = ["Magic Missile", "Shield", "Mage Armor", "Detect Magic"]
    for spell in spells_to_prepare:
        if wizard.prepare_spell(spell):
            print(f"  ✓ Prepared: {spell}")
    
    print(f"\nPrepared spells: {wizard.prepared_spells}")
    
    # Cast a spell
    print("\nCasting Magic Missile (1st level spell)...")
    if wizard.cast_spell(1):
        print("✓ Spell cast successfully!")
        print(f"  Remaining 1st level slots: {wizard.spell_slots[1] - wizard.spell_slots_used[1]}/{wizard.spell_slots[1]}")
    
    # Test Arcane Recovery
    print("\nUsing Arcane Recovery during short rest...")
    print(f"Can recover up to {wizard.arcane_recovery_slots_max} spell slot levels")
    if wizard.use_arcane_recovery([1]):  # Recover one 1st level slot
        print("✓ Recovered 1st level spell slot")
        print(f"  1st level slots: {wizard.spell_slots[1] - wizard.spell_slots_used[1]}/{wizard.spell_slots[1]}")
        print(f"  Arcane Recovery available: {wizard.arcane_recovery_available}")
    
    # Test leveling up
    print("\n" + "=" * 60)
    print("TESTING LEVEL UP")
    print("=" * 60)
    
    print(f"\nCurrent level: {wizard.level}")
    print(f"Current HP: {wizard.hp}/{wizard.max_hp}")
    print(f"Current spell slots: {wizard.spell_slots}")
    
    wizard.level_up()
    print(f"\nAfter level up:")
    print(f"New level: {wizard.level}")
    print(f"New HP: {wizard.hp}/{wizard.max_hp}")
    print(f"Features unlocked: Arcane Tradition available")
    
    # Choose Arcane Tradition
    wizard.arcane_tradition = "School of Evocation"
    wizard.apply_level_features()
    
    print(f"\nArcane Tradition chosen: {wizard.arcane_tradition}")
    print(f"New features: Evocation Savant, Sculpt Spells")
    
    # Level up to 3 to get more spell slots
    wizard.level_up()
    print(f"\nLevel {wizard.level} spell slots:")
    for level in range(1, 10):
        if wizard.spell_slots[level] > 0:
            print(f"  Level {level}: {wizard.spell_slots[level]}")
    
    # Test long rest
    print("\n" + "=" * 60)
    print("LONG REST")
    print("=" * 60)
    wizard.long_rest()
    print("✓ Long rest completed")
    print(f"  Spell slots restored")
    print(f"  Arcane Recovery available: {wizard.arcane_recovery_available}")
    
    print("\n" + "=" * 60)
    print(wizard)
    print("=" * 60)