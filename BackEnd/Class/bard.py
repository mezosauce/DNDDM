#!/usr/bin/env python3
"""
Bard Class - D&D 5e SRD Implementation
Derived from the base Character class with full Bard features
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from BackEnd.campaign_manager import Character


@dataclass
class Bard(Character):
    """
    Bard class implementation following D&D 5e SRD
    Inherits from Character and adds Bard-specific features
    """
    
    # Bard-specific attributes (all with defaults to avoid dataclass issues)
    bard_college: str = ""  # "College of Lore" or "College of Valor"
    
    # Spellcasting
    cantrips_known: List[str] = field(default_factory=list)
    spells_known: List[str] = field(default_factory=list)
    spell_slots: Dict[int, int] = field(default_factory=dict)  # {spell_level: slots}
    spell_slots_used: Dict[int, int] = field(default_factory=dict)  # {spell_level: used}
    
    # Bardic Inspiration
    bardic_inspiration_die: str = "d6"  # d6, d8, d10, or d12
    bardic_inspiration_uses: int = 0  # Max uses (based on Charisma modifier)
    bardic_inspiration_remaining: int = 0  # Current remaining uses
    
    # Musical Instruments (tool proficiencies)
    musical_instruments: List[str] = field(default_factory=list)  # 3 instruments
    
    # Expertise (choose at 3rd and 10th level)
    expertise_skills: List[str] = field(default_factory=list)  # Skills with doubled proficiency
    
    # Magical Secrets (spells from other classes)
    magical_secrets: List[str] = field(default_factory=list)
    
    # Feature flags
    jack_of_all_trades: bool = False  # Level 2+
    song_of_rest_die: str = ""  # d6 at 2nd, d8 at 9th, d10 at 13th, d12 at 17th
    font_of_inspiration: bool = False  # Level 5+
    countercharm_available: bool = False  # Level 6+
    superior_inspiration: bool = False  # Level 20
    
    # College of Lore features
    cutting_words_available: bool = False  # Level 3 Lore
    additional_magical_secrets: bool = False  # Level 6 Lore
    peerless_skill_available: bool = False  # Level 14 Lore
    
    # College features unlocked at certain levels
    college_feature_3: bool = False
    college_feature_6: bool = False
    college_feature_14: bool = False
    
    def __post_init__(self):
        """Initialize Bard with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Bard"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Bards typically have high CHA, decent DEX and CON
            self.stats = {
                "strength": 8,
                "dexterity": 14,
                "constitution": 12,
                "intelligence": 10,
                "wisdom": 13,
                "charisma": 15
            }
        
        # Set hit points based on level (1d8 per level)
        if self.level == 1:
            self.max_hp = 8 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Bards can choose any three skills
            self.skill_proficiencies = ["Performance", "Persuasion", "Deception"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        if not self.musical_instruments:
            # Bards get three musical instruments
            self.musical_instruments = ["Lute", "Flute", "Drum"]
        
        # Initialize spell slots based on level
        if not self.spell_slots:
            self.spell_slots = self._get_spell_slots_for_level(self.level)
        
        # Initialize used spell slots
        if not self.spell_slots_used:
            self.spell_slots_used = {level: 0 for level in self.spell_slots.keys()}
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
    def _get_spell_slots_for_level(self, level: int) -> Dict[int, int]:
        """Get spell slots based on bard level"""
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
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
        }
        return spell_slot_table.get(level, {1: 2})
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Calculate bardic inspiration uses based on Charisma modifier
        cha_mod = self._get_modifier("charisma")
        self.bardic_inspiration_uses = max(1, cha_mod)
        if self.bardic_inspiration_remaining == 0:
            self.bardic_inspiration_remaining = self.bardic_inspiration_uses
        
        # Bardic Inspiration die progression
        if self.level >= 15:
            self.bardic_inspiration_die = "d12"
        elif self.level >= 10:
            self.bardic_inspiration_die = "d10"
        elif self.level >= 5:
            self.bardic_inspiration_die = "d8"
        else:
            self.bardic_inspiration_die = "d6"
        
        # Class features by level
        if self.level >= 2:
            self.jack_of_all_trades = True
            self.song_of_rest_die = "d6"
        
        if self.level >= 5:
            self.font_of_inspiration = True
        
        if self.level >= 6:
            self.countercharm_available = True
        
        # Song of Rest progression
        if self.level >= 17:
            self.song_of_rest_die = "d12"
        elif self.level >= 13:
            self.song_of_rest_die = "d10"
        elif self.level >= 9:
            self.song_of_rest_die = "d8"
        
        if self.level >= 20:
            self.superior_inspiration = True
        
        # College features
        if self.level >= 3:
            self.college_feature_3 = True
        if self.level >= 6:
            self.college_feature_6 = True
        if self.level >= 14:
            self.college_feature_14 = True
        
        # College of Lore specific
        if self.bard_college == "College of Lore":
            if self.level >= 3:
                self.cutting_words_available = True
            if self.level >= 6:
                self.additional_magical_secrets = True
            if self.level >= 14:
                self.peerless_skill_available = True
        
        # Update spell slots
        self.spell_slots = self._get_spell_slots_for_level(self.level)
        self.spell_slots_used = {level: 0 for level in self.spell_slots.keys()}
    
    def get_max_cantrips(self) -> int:
        """Get maximum cantrips known based on level"""
        if self.level >= 10:
            return 4
        elif self.level >= 4:
            return 3
        else:
            return 2
    
    def get_max_spells_known(self) -> int:
        """Get maximum spells known based on level"""
        spells_known_table = {
            1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14,
            11: 15, 12: 15, 13: 16, 14: 18, 15: 19, 16: 19, 17: 20, 18: 22,
            19: 22, 20: 22
        }
        return spells_known_table.get(self.level, 4)
    
    def use_bardic_inspiration(self) -> bool:
        """
        Use a bardic inspiration charge.
        Returns True if successful, False if no uses remaining.
        """
        if self.bardic_inspiration_remaining > 0:
            self.bardic_inspiration_remaining -= 1
            return True
        return False
    
    def cast_spell(self, spell_level: int) -> bool:
        """
        Cast a spell of the given level.
        Returns True if successful, False if no slots available.
        """
        if spell_level not in self.spell_slots:
            return False
        
        if self.spell_slots_used[spell_level] < self.spell_slots[spell_level]:
            self.spell_slots_used[spell_level] += 1
            return True
        
        # Try to use a higher level slot
        for level in range(spell_level + 1, 10):
            if level in self.spell_slots and self.spell_slots_used[level] < self.spell_slots[level]:
                self.spell_slots_used[level] += 1
                return True
        
        return False
    
    def long_rest(self):
        """Reset resources on long rest"""
        self.spell_slots_used = {level: 0 for level in self.spell_slots.keys()}
        self.bardic_inspiration_remaining = self.bardic_inspiration_uses
        self.hp = self.max_hp
    
    def short_rest(self):
        """
        Short rest - restore bardic inspiration if 5th level or higher (Font of Inspiration).
        Players can also spend hit dice to recover HP.
        """
        if self.font_of_inspiration:
            self.bardic_inspiration_remaining = self.bardic_inspiration_uses
    
    def learn_cantrip(self, cantrip: str) -> bool:
        """Learn a new cantrip"""
        if len(self.cantrips_known) >= self.get_max_cantrips():
            return False
        if cantrip not in self.cantrips_known:
            self.cantrips_known.append(cantrip)
            return True
        return False
    
    def learn_spell(self, spell: str) -> bool:
        """Learn a new spell"""
        if len(self.spells_known) >= self.get_max_spells_known():
            return False
        if spell not in self.spells_known:
            self.spells_known.append(spell)
            return True
        return False
    
    def forget_spell(self, spell: str) -> bool:
        """Forget a spell (can swap when leveling up)"""
        if spell in self.spells_known:
            self.spells_known.remove(spell)
            return True
        return False
    
    def add_expertise(self, skill: str) -> bool:
        """Add expertise to a skill (must be proficient)"""
        if skill not in self.skill_proficiencies:
            return False
        
        max_expertise = 2 if self.level < 10 else 4
        if len(self.expertise_skills) >= max_expertise:
            return False
        
        if skill not in self.expertise_skills:
            self.expertise_skills.append(skill)
            return True
        return False
    
    def add_magical_secret(self, spell: str) -> bool:
        """Add a spell from Magical Secrets feature"""
        max_secrets = 0
        if self.level >= 18:
            max_secrets = 6
        elif self.level >= 14:
            max_secrets = 4
        elif self.level >= 10:
            max_secrets = 2
        
        if len(self.magical_secrets) >= max_secrets:
            return False
        
        if spell not in self.magical_secrets:
            self.magical_secrets.append(spell)
            return True
        return False
    
    def choose_college(self, college: str) -> bool:
        """Choose a bard college at 3rd level"""
        if self.level < 3:
            return False
        
        valid_colleges = ["College of Lore", "College of Valor"]
        if college not in valid_colleges:
            return False
        
        self.bard_college = college
        self.apply_level_features()
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
    
    def get_spell_save_dc(self) -> int:
        """Calculate spell save DC: 8 + proficiency bonus + Charisma modifier"""
        return 8 + self.get_proficiency_bonus() + self._get_modifier("charisma")
    
    def get_spell_attack_modifier(self) -> int:
        """Calculate spell attack modifier: proficiency bonus + Charisma modifier"""
        return self.get_proficiency_bonus() + self._get_modifier("charisma")
    
    def level_up(self):
        """Level up the bard"""
        self.level += 1
        
        # Increase HP (1d8 + CON mod per level, or 5 + CON mod average)
        hp_gain = 5 + self._get_modifier("constitution")
        self.max_hp += hp_gain
        self.hp += hp_gain
        
        # Reapply level-based features
        self.apply_level_features()
    
    def get_available_spell_slots(self) -> Dict[int, str]:
        """Get a formatted display of available spell slots"""
        slots = {}
        for level, total in self.spell_slots.items():
            used = self.spell_slots_used.get(level, 0)
            slots[level] = f"{total - used}/{total}"
        return slots
    
    def get_character_sheet(self) -> Dict:
        """Generate a complete character sheet"""
        return {
            "name": self.name,
            "race": self.race,
            "class": f"{self.char_class} {self.level}",
            "background": self.background,
            "alignment": self.alignment,
            "bard_college": self.bard_college if self.bard_college else "Not chosen (Level 3+)",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": self.ac,
            "speed": 30,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "dexterity": self._get_modifier("dexterity") + self.get_proficiency_bonus(),
                "charisma": self._get_modifier("charisma") + self.get_proficiency_bonus()
            },
            
            "skills": self.skill_proficiencies,
            "expertise": self.expertise_skills,
            "languages": self.languages_known,
            "tools": self.musical_instruments,
            
            "spellcasting": {
                "spell_save_dc": self.get_spell_save_dc(),
                "spell_attack_bonus": self.get_spell_attack_modifier(),
                "cantrips_known": f"{len(self.cantrips_known)}/{self.get_max_cantrips()}",
                "spells_known": f"{len(self.spells_known)}/{self.get_max_spells_known()}",
                "spell_slots": self.get_available_spell_slots()
            },
            
            "bardic_inspiration": {
                "die": self.bardic_inspiration_die,
                "uses": f"{self.bardic_inspiration_remaining}/{self.bardic_inspiration_uses}"
            },
            
            "features": {
                "Spellcasting": True,
                "Bardic Inspiration": f"{self.bardic_inspiration_die}",
                "Jack of All Trades": self.jack_of_all_trades,
                "Song of Rest": self.song_of_rest_die if self.song_of_rest_die else False,
                "Expertise": f"{len(self.expertise_skills)} skills" if self.expertise_skills else False,
                "Font of Inspiration": self.font_of_inspiration,
                "Countercharm": self.countercharm_available,
                "Magical Secrets": f"{len(self.magical_secrets)} spells" if self.magical_secrets else False,
                "Superior Inspiration": self.superior_inspiration
            },
            
            "college_features": self._get_college_features(),
            
            "cantrips": self.cantrips_known,
            "spells": self.spells_known,
            "magical_secrets_spells": self.magical_secrets,
            
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
    
    def _get_college_features(self) -> Dict[str, bool]:
        """Get college-specific features"""
        features = {}
        
        if self.bard_college == "College of Lore":
            if self.college_feature_3:
                features["Bonus Proficiencies"] = "3 additional skills"
                features["Cutting Words"] = self.cutting_words_available
            if self.college_feature_6:
                features["Additional Magical Secrets"] = self.additional_magical_secrets
            if self.college_feature_14:
                features["Peerless Skill"] = self.peerless_skill_available
        
        return features
    
    def __str__(self) -> str:
        """String representation"""
        college_str = f" ({self.bard_college})" if self.bard_college else ""
        inspiration_str = f"Inspiration: {self.bardic_inspiration_remaining}/{self.bardic_inspiration_uses} ({self.bardic_inspiration_die})"
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{college_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac} | {inspiration_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Bard
    bard = Bard(
        name="Lyra Songweaver",
        race="Half-Elf",
        char_class="Bard",
        background="Entertainer",
        level=1,
        stats={
            "strength": 8,
            "dexterity": 14,
            "constitution": 13,
            "intelligence": 12,
            "wisdom": 10,
            "charisma": 16
        },
        alignment="Chaotic Good",
        personality_traits=["I love a good insult, even one directed at me", "I always have a joke ready"],
        ideal="Creativity. The world is in need of new ideas and bold action",
        bond="I want to be famous, whatever it takes",
        flaw="I'll do anything to win fame and renown"
    )
    
    # Set starting equipment
    bard.inventory = ["Rapier", "Lute", "Leather Armor", "Dagger", "Entertainer's Pack"]
    bard.currency['gp'] = 15
    
    print("=" * 60)
    print("BARD CHARACTER SHEET")
    print("=" * 60)
    print(bard)
    print()
    
    # Display character sheet
    sheet = bard.get_character_sheet()
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
    print(f"  Cantrips Known: {sheet['spellcasting']['cantrips_known']}")
    print(f"  Spells Known: {sheet['spellcasting']['spells_known']}")
    print("  Spell Slots:")
    for level, slots in sheet['spellcasting']['spell_slots'].items():
        print(f"    Level {level}: {slots}")
    print()
    
    print("Bardic Inspiration:")
    print(f"  Die: {sheet['bardic_inspiration']['die']}")
    print(f"  Uses: {sheet['bardic_inspiration']['uses']}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    print("Skills:")
    for skill in sheet['skills']:
        expertise_marker = " (Expertise)" if skill in sheet['expertise'] else ""
        print(f"  • {skill}{expertise_marker}")
    print()
    
    print("Musical Instruments:")
    for instrument in sheet['tools']:
        print(f"  • {instrument}")
    print()
    
    print("Equipment:")
    for item in bard.inventory:
        print(f"  • {item}")
    print()
    
    # Learn some spells
    print("=" * 60)
    print("LEARNING SPELLS")
    print("=" * 60)
    
    print("\nLearning cantrips...")
    bard.learn_cantrip("Vicious Mockery")
    bard.learn_cantrip("Prestidigitation")
    print(f"✓ Cantrips learned: {', '.join(bard.cantrips_known)}")
    
    print("\nLearning spells...")
    bard.learn_spell("Cure Wounds")
    bard.learn_spell("Healing Word")
    bard.learn_spell("Thunderwave")
    bard.learn_spell("Charm Person")
    print(f"✓ Spells learned: {', '.join(bard.spells_known)}")
    
    # Test bardic inspiration
    print("\n" + "=" * 60)
    print("TESTING BARDIC INSPIRATION")
    print("=" * 60)
    
    print(f"\nInspiration available: {bard.bardic_inspiration_remaining}/{bard.bardic_inspiration_uses}")
    print("Using bardic inspiration...")
    if bard.use_bardic_inspiration():
        print(f"✓ Inspiration granted! ({bard.bardic_inspiration_die})")
        print(f"Remaining: {bard.bardic_inspiration_remaining}/{bard.bardic_inspiration_uses}")
    
    # Test spellcasting
    print("\n" + "=" * 60)
    print("TESTING SPELLCASTING")
    print("=" * 60)
    
    print(f"\nAvailable spell slots: {bard.get_available_spell_slots()}")
    print("Casting Cure Wounds (1st level)...")
    if bard.cast_spell(1):
        print("✓ Spell cast successfully!")
        print(f"Remaining slots: {bard.get_available_spell_slots()}")
    
    # Test rest mechanics
    print("\n" + "=" * 60)
    print("TESTING REST MECHANICS")
    print("=" * 60)
    
    print(f"\nBefore rest:")
    print(f"  HP: {bard.hp}/{bard.max_hp}")
    print(f"  Inspiration: {bard.bardic_inspiration_remaining}/{bard.bardic_inspiration_uses}")
    print(f"  Spell slots: {bard.get_available_spell_slots()}")
    
    bard.hp -= 5  # Simulate damage
    
    print("\nTaking a short rest...")
    bard.short_rest()
    print(f"After short rest (Level 1, no Font of Inspiration yet):")
    print(f"  Inspiration: {bard.bardic_inspiration_remaining}/{bard.bardic_inspiration_uses}")
    
    print("\nTaking a long rest...")
    bard.long_rest()
    print(f"After long rest:")
    print(f"  HP: {bard.hp}/{bard.max_hp}")
    print(f"  Inspiration: {bard.bardic_inspiration_remaining}/{bard.bardic_inspiration_uses}")
    print(f"  Spell slots: {bard.get_available_spell_slots()}")
    
    # Test leveling up
    print("\n" + "=" * 60)
    print("TESTING LEVEL UP")
    print("=" * 60)
    
    print(f"\nCurrent level: {bard.level}")
    print(f"Current HP: {bard.hp}/{bard.max_hp}")
    print(f"Current Bardic Inspiration: {bard.bardic_inspiration_die}")
    
    bard.level_up()
    print(f"\nAfter level up to {bard.level}:")
    print(f"New HP: {bard.hp}/{bard.max_hp}")
    print(f"Features unlocked: Jack of All Trades, Song of Rest (d6)")
    
    # Level up to 3 to choose college
    bard.level_up()
    print(f"\nLevel {bard.level} - Can now choose Bard College!")
    bard.choose_college("College of Lore")
    print(f"✓ Chosen: {bard.bard_college}")
    print(f"New features: Cutting Words, Expertise (2 skills)")
    
    # Add expertise
    bard.add_expertise("Performance")
    bard.add_expertise("Persuasion")
    print(f"Expertise in: {', '.join(bard.expertise_skills)}")
    
    # Learn more spells
    bard.learn_spell("Detect Magic")
    bard.learn_spell("Disguise Self")
    print(f"\nSpells known ({len(bard.spells_known)}/{bard.get_max_spells_known()}): {', '.join(bard.spells_known)}")
    
    # Continue leveling to test more features
    print("\n" + "=" * 60)
    print("ADVANCING TO HIGHER LEVELS")
    print("=" * 60)
    
    # Level to 5
    bard.level_up()
    bard.level_up()
    print(f"\nLevel {bard.level}:")
    print(f"  Bardic Inspiration: {bard.bardic_inspiration_die}")
    print(f"  Font of Inspiration: {bard.font_of_inspiration}")
    print(f"  Max cantrips: {bard.get_max_cantrips()}")
    
    # Level to 10
    for _ in range(5):
        bard.level_up()
    
    print(f"\nLevel {bard.level}:")
    print(f"  Bardic Inspiration: {bard.bardic_inspiration_die}")
    print(f"  Can choose 2 more expertise skills")
    print(f"  Magical Secrets: Can learn 2 spells from any class")
    print(f"  Max cantrips: {bard.get_max_cantrips()}")
    print(f"  Max spells known: {bard.get_max_spells_known()}")
    
    print("\n" + "=" * 60)
    print(bard)
    print("=" * 60)