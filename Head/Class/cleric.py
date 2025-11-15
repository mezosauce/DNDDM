#!/usr/bin/env python3
"""
Cleric Class - D&D 5e SRD Implementation
Derived from the base Character class with full Cleric features
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from Head.campaign_manager import Character


@dataclass
class Cleric(Character):
    """
    Cleric class implementation following D&D 5e SRD
    Inherits from Character and adds Cleric-specific features
    """
    
    # Cleric-specific attributes (all with defaults to avoid dataclass issues)
    divine_domain: str = ""  # "Life", "Knowledge", "Light", "Nature", "Tempest", "Trickery", "War"
    deity: str = ""  # The deity the cleric serves
    
    # Spellcasting
    cantrips_known: int = 3
    spell_slots: Dict[int, int] = field(default_factory=dict)  # {1: 2, 2: 0, ...}
    spells_prepared: List[str] = field(default_factory=list)
    domain_spells: List[str] = field(default_factory=list)  # Always prepared
    
    # Channel Divinity
    channel_divinity_uses: int = 0  # Based on level (1 at 2nd, 2 at 6th, 3 at 18th)
    channel_divinity_used: int = 0
    
    # Destroy Undead
    destroy_undead_cr: float = 0  # CR threshold for destroying undead
    
    # Divine Intervention
    divine_intervention_available: bool = False  # Level 10+
    divine_intervention_used: bool = False  # Can't use for 7 days if successful
    divine_intervention_auto_success: bool = False  # Level 20
    
    # Life Domain specific features
    bonus_proficiency_heavy_armor: bool = False  # Life domain gets heavy armor
    disciple_of_life: bool = False  # Healing bonus (Life domain level 1)
    preserve_life_available: bool = False  # Channel Divinity: Preserve Life (Life domain level 2)
    blessed_healer: bool = False  # Heal self when healing others (Life domain level 6)
    divine_strike_dice: int = 0  # Extra radiant damage (1d8 at 8th, 2d8 at 14th)
    supreme_healing: bool = False  # Max healing dice (Life domain level 17)
    
    # Domain features unlocked at certain levels
    domain_feature_1: bool = False
    domain_feature_2: bool = False
    domain_feature_6: bool = False
    domain_feature_8: bool = False
    domain_feature_17: bool = False
    
    def __post_init__(self):
        """Initialize Cleric with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Cleric"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Clerics typically have high WIS and CON
            self.stats = {
                "strength": 10,
                "dexterity": 12,
                "constitution": 14,
                "intelligence": 11,
                "wisdom": 16,
                "charisma": 13
            }
        
        # Set hit points based on level (1d8 per level)
        if self.level == 1:
            self.max_hp = 8 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Clerics choose two from: History, Insight, Medicine, Persuasion, Religion
            self.skill_proficiencies = ["Insight", "Religion"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        # Initialize spell slots
        if not self.spell_slots:
            self.spell_slots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Cantrips known progression
        if self.level >= 1:
            self.cantrips_known = 3
        if self.level >= 4:
            self.cantrips_known = 4
        if self.level >= 10:
            self.cantrips_known = 5
        
        # Spell slots progression (from the table)
        spell_slot_progression = {
            1:  {1: 2, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            2:  {1: 3, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            3:  {1: 4, 2: 2, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            4:  {1: 4, 2: 3, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            5:  {1: 4, 2: 3, 3: 2, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            6:  {1: 4, 2: 3, 3: 3, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            7:  {1: 4, 2: 3, 3: 3, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            8:  {1: 4, 2: 3, 3: 3, 4: 2, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            9:  {1: 4, 2: 3, 3: 3, 4: 3, 5: 1, 6: 0, 7: 0, 8: 0, 9: 0},
            10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 0, 7: 0, 8: 0, 9: 0},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 0, 8: 0, 9: 0},
            12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 0, 8: 0, 9: 0},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 0, 9: 0},
            14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 0, 9: 0},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 0},
            16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 0},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
            18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
        }
        
        if self.level in spell_slot_progression:
            self.spell_slots = spell_slot_progression[self.level].copy()
        
        # Channel Divinity uses
        if self.level >= 2:
            self.channel_divinity_uses = 1
        if self.level >= 6:
            self.channel_divinity_uses = 2
        if self.level >= 18:
            self.channel_divinity_uses = 3
        
        # Destroy Undead progression
        if self.level >= 5:
            self.destroy_undead_cr = 0.5
        if self.level >= 8:
            self.destroy_undead_cr = 1
        if self.level >= 11:
            self.destroy_undead_cr = 2
        if self.level >= 14:
            self.destroy_undead_cr = 3
        if self.level >= 17:
            self.destroy_undead_cr = 4
        
        # Divine Intervention
        if self.level >= 10:
            self.divine_intervention_available = True
        if self.level >= 20:
            self.divine_intervention_auto_success = True
        
        # Apply Divine Domain features
        if self.divine_domain == "Life":
            self._apply_life_domain_features()
    
    def _apply_life_domain_features(self):
        """Apply Life Domain specific features"""
        # Level 1 features
        if self.level >= 1:
            self.domain_feature_1 = True
            self.bonus_proficiency_heavy_armor = True
            self.disciple_of_life = True
            
            # Add Life Domain spells for level 1
            if "bless" not in self.domain_spells:
                self.domain_spells.extend(["bless", "cure wounds"])
        
        # Level 2 features
        if self.level >= 2:
            self.domain_feature_2 = True
            self.preserve_life_available = True
        
        # Level 3 domain spells
        if self.level >= 3:
            if "lesser restoration" not in self.domain_spells:
                self.domain_spells.extend(["lesser restoration", "spiritual weapon"])
        
        # Level 5 domain spells
        if self.level >= 5:
            if "beacon of hope" not in self.domain_spells:
                self.domain_spells.extend(["beacon of hope", "revivify"])
        
        # Level 6 features
        if self.level >= 6:
            self.domain_feature_6 = True
            self.blessed_healer = True
        
        # Level 7 domain spells
        if self.level >= 7:
            if "death ward" not in self.domain_spells:
                self.domain_spells.extend(["death ward", "guardian of faith"])
        
        # Level 8 features
        if self.level >= 8:
            self.domain_feature_8 = True
            self.divine_strike_dice = 1  # 1d8 radiant damage
        
        # Level 9 domain spells
        if self.level >= 9:
            if "mass cure wounds" not in self.domain_spells:
                self.domain_spells.extend(["mass cure wounds", "raise dead"])
        
        # Level 14 - Divine Strike improvement
        if self.level >= 14:
            self.divine_strike_dice = 2  # 2d8 radiant damage
        
        # Level 17 features
        if self.level >= 17:
            self.domain_feature_17 = True
            self.supreme_healing = True
    
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
        """Calculate spell save DC: 8 + proficiency bonus + Wisdom modifier"""
        return 8 + self.get_proficiency_bonus() + self._get_modifier("wisdom")
    
    def get_spell_attack_bonus(self) -> int:
        """Calculate spell attack bonus: proficiency bonus + Wisdom modifier"""
        return self.get_proficiency_bonus() + self._get_modifier("wisdom")
    
    def get_max_prepared_spells(self) -> int:
        """Calculate maximum prepared spells: Wisdom modifier + cleric level (minimum 1)"""
        return max(1, self._get_modifier("wisdom") + self.level)
    
    def prepare_spell(self, spell_name: str) -> bool:
        """
        Prepare a spell from the cleric spell list.
        Returns True if successful, False if already at max prepared spells.
        """
        if spell_name in self.spells_prepared:
            return False  # Already prepared
        
        if len(self.spells_prepared) >= self.get_max_prepared_spells():
            return False  # At max capacity
        
        self.spells_prepared.append(spell_name)
        return True
    
    def unprepare_spell(self, spell_name: str) -> bool:
        """Unprepare a spell"""
        if spell_name in self.spells_prepared:
            self.spells_prepared.remove(spell_name)
            return True
        return False
    
    def use_channel_divinity(self) -> bool:
        """
        Use Channel Divinity if available.
        Returns True if successful, False if no uses remaining.
        """
        if self.channel_divinity_used >= self.channel_divinity_uses:
            return False
        
        self.channel_divinity_used += 1
        return True
    
    def turn_undead_dc(self) -> int:
        """Calculate DC for Turn Undead (same as spell save DC)"""
        return self.get_spell_save_dc()
    
    def preserve_life_hp_pool(self) -> int:
        """
        Calculate HP pool for Preserve Life (Life domain Channel Divinity).
        Returns 5 times cleric level.
        """
        if not self.preserve_life_available:
            return 0
        return 5 * self.level
    
    def disciple_of_life_bonus(self, spell_level: int) -> int:
        """
        Calculate bonus healing from Disciple of Life.
        Returns 2 + spell level.
        """
        if not self.disciple_of_life:
            return 0
        return 2 + spell_level
    
    def blessed_healer_heal(self, spell_level: int) -> int:
        """
        Calculate self-healing from Blessed Healer.
        Returns 2 + spell level.
        """
        if not self.blessed_healer:
            return 0
        return 2 + spell_level
    
    def attempt_divine_intervention(self) -> bool:
        """
        Attempt Divine Intervention.
        Returns True if successful (roll <= cleric level, or level 20).
        At level 20, automatically succeeds.
        """
        if not self.divine_intervention_available:
            return False
        
        if self.divine_intervention_used:
            return False
        
        # Level 20 auto-succeeds
        if self.divine_intervention_auto_success:
            return True
        
        # Would normally roll percentile dice (1d100)
        # Success if roll <= cleric level
        # For implementation purposes, we'll simulate this
        import random
        roll = random.randint(1, 100)
        
        if roll <= self.level:
            self.divine_intervention_used = True  # Can't use for 7 days
            return True
        
        return False
    
    def long_rest(self):
        """Reset resources on long rest"""
        self.channel_divinity_used = 0
        self.hp = self.max_hp
        # Spell slots are regained
        # Prepared spells can be changed
        # Divine Intervention: if failed, can be used again after long rest
        # Note: if Divine Intervention succeeded, can't use for 7 days (not auto-reset)
    
    def short_rest(self):
        """Reset resources on short rest"""
        self.channel_divinity_used = 0  # Channel Divinity resets on short or long rest
    
    def level_up(self):
        """Level up the cleric"""
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
            "deity": self.deity if self.deity else "Not chosen",
            "divine_domain": self.divine_domain if self.divine_domain else "Not chosen (Level 1)",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": self.ac,
            "speed": 30,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "wisdom": self._get_modifier("wisdom") + self.get_proficiency_bonus(),
                "charisma": self._get_modifier("charisma") + self.get_proficiency_bonus()
            },
            
            "skills": self.skill_proficiencies,
            "languages": self.languages_known,
            
            "spellcasting": {
                "cantrips_known": self.cantrips_known,
                "spell_slots": self.spell_slots,
                "spells_prepared": f"{len(self.spells_prepared)}/{self.get_max_prepared_spells()}",
                "prepared_spell_list": self.spells_prepared,
                "domain_spells": self.domain_spells,
                "spell_save_dc": self.get_spell_save_dc(),
                "spell_attack_bonus": f"+{self.get_spell_attack_bonus()}"
            },
            
            "channel_divinity": {
                "uses": f"{self.channel_divinity_used}/{self.channel_divinity_uses}",
                "turn_undead_dc": self.turn_undead_dc() if self.level >= 2 else "N/A"
            },
            
            "features": {
                "Spellcasting": True,
                "Divine Domain": self.divine_domain if self.divine_domain else False,
                "Channel Divinity": f"{self.channel_divinity_uses}/rest" if self.level >= 2 else False,
                "Destroy Undead": f"CR {self.destroy_undead_cr}" if self.destroy_undead_cr > 0 else False,
                "Divine Intervention": f"{self.level}% chance" if self.divine_intervention_available and not self.divine_intervention_auto_success else ("Auto-success" if self.divine_intervention_auto_success else False),
            },
            
            "life_domain_features": {
                "Heavy Armor Proficiency": self.bonus_proficiency_heavy_armor,
                "Disciple of Life": f"+{2 + 1} HP per 1st level healing spell" if self.disciple_of_life else False,
                "Preserve Life": f"{self.preserve_life_hp_pool()} HP pool" if self.preserve_life_available else False,
                "Blessed Healer": self.blessed_healer,
                "Divine Strike": f"+{self.divine_strike_dice}d8 radiant" if self.divine_strike_dice > 0 else False,
                "Supreme Healing": self.supreme_healing
            } if self.divine_domain == "Life" else {},
            
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
        domain_str = f" ({self.divine_domain})" if self.divine_domain else ""
        channel_str = f"Channel Divinity: {self.channel_divinity_used}/{self.channel_divinity_uses}" if self.level >= 2 else ""
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{domain_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac} | {channel_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Cleric
    cleric = Cleric(
        name="Jester Lavorre",
        race="Tiefling",
        char_class="Cleric",
        background="Acolyte",
        level=1,
        stats={
            "strength": 10,
            "dexterity": 12,
            "constitution": 14,
            "intelligence": 11,
            "wisdom": 16,
            "charisma": 13
        },
        alignment="Chaotic Good",
        deity="The Traveler",
        divine_domain="Life",
        personality_traits=["I idolize a particular hero of my faith", "I see omens in every event"],
        ideal="Charity. I always try to help those in need",
        bond="I would die to recover an ancient relic of my faith",
        flaw="I judge others harshly, and myself even more severely"
    )
    
    # Set starting equipment
    cleric.inventory = ["Mace", "Scale Mail", "Light Crossbow", "20 Bolts", "Priest's Pack", "Shield", "Holy Symbol"]
    cleric.currency = {'cp': 0, 'sp': 0, 'ep': 0, 'gp': 15, 'pp': 0}
    
    print("=" * 60)
    print("CLERIC CHARACTER SHEET")
    print("=" * 60)
    print(cleric)
    print()
    
    # Display character sheet
    sheet = cleric.get_character_sheet()
    print(f"Name: {sheet['name']}")
    print(f"Class: {sheet['class']}")
    print(f"Race: {sheet['race']}")
    print(f"Background: {sheet['background']}")
    print(f"Alignment: {sheet['alignment']}")
    print(f"Deity: {sheet['deity']}")
    print(f"Divine Domain: {sheet['divine_domain']}")
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
    print(f"  Cantrips Known: {sheet['spellcasting']['cantrips_known']}")
    print(f"  Spell Save DC: {sheet['spellcasting']['spell_save_dc']}")
    print(f"  Spell Attack: {sheet['spellcasting']['spell_attack_bonus']}")
    print(f"  Spells Prepared: {sheet['spellcasting']['spells_prepared']}")
    print(f"  Domain Spells: {', '.join(sheet['spellcasting']['domain_spells'])}")
    print(f"  Spell Slots:")
    for level, slots in sheet['spellcasting']['spell_slots'].items():
        if slots > 0:
            print(f"    Level {level}: {slots}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    if sheet['life_domain_features']:
        print("Life Domain Features:")
        for feature, value in sheet['life_domain_features'].items():
            if value and value is not False:
                print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
        print()
    
    print("Equipment:")
    for item in cleric.inventory:
        print(f"  • {item}")
    print()
    
    print(f"Currency: {sheet['total_wealth_gp']:.2f} gp total")
    print()
    
    # Test spellcasting mechanics
    print("=" * 60)
    print("TESTING SPELLCASTING MECHANICS")
    print("=" * 60)
    
    print(f"\nMax prepared spells: {cleric.get_max_prepared_spells()}")
    print(f"Spell Save DC: {cleric.get_spell_save_dc()}")
    print(f"Spell Attack Bonus: +{cleric.get_spell_attack_bonus()}")
    
    print("\nPreparing spells...")
    cleric.prepare_spell("healing word")
    cleric.prepare_spell("shield of faith")
    cleric.prepare_spell("guiding bolt")
    print(f"Prepared: {', '.join(cleric.spells_prepared)}")
    
    # Test Channel Divinity
    print("\n" + "=" * 60)
    print("TESTING LEVEL UP AND CHANNEL DIVINITY")
    print("=" * 60)
    
    cleric.level_up()
    print(f"\nLevel up to {cleric.level}!")
    print(f"New HP: {cleric.hp}/{cleric.max_hp}")
    print(f"Channel Divinity uses: {cleric.channel_divinity_uses}")
    print(f"Turn Undead DC: {cleric.turn_undead_dc()}")
    
    if cleric.preserve_life_available:
        print(f"Preserve Life HP pool: {cleric.preserve_life_hp_pool()}")
    
    print("\nUsing Channel Divinity: Turn Undead")
    if cleric.use_channel_divinity():
        print("✓ Channel Divinity used!")
        print(f"  Remaining uses: {cleric.channel_divinity_uses - cleric.channel_divinity_used}/{cleric.channel_divinity_uses}")
    
    # Level up to demonstrate more features
    print("\n" + "=" * 60)
    print("LEVELING TO 8 FOR MORE FEATURES")
    print("=" * 60)
    
    for _ in range(6):  # Level up to 8
        cleric.level_up()
    
    print(f"\nNow level {cleric.level}!")
    print(f"HP: {cleric.hp}/{cleric.max_hp}")
    print(f"Cantrips Known: {cleric.cantrips_known}")
    print(f"Channel Divinity: {cleric.channel_divinity_uses} uses per rest")
    print(f"Destroy Undead: CR {cleric.destroy_undead_cr} or lower")
    
    if cleric.divine_strike_dice > 0:
        print(f"Divine Strike: +{cleric.divine_strike_dice}d8 radiant damage")
    
    if cleric.blessed_healer:
        print("Blessed Healer: Heal self when healing others")
    
    # Show spell slots
    print("\nSpell Slots:")
    for level, slots in cleric.spell_slots.items():
        if slots > 0:
            print(f"  Level {level}: {slots} slots")
    
    print("\nDomain Spells (always prepared):")
    for spell in cleric.domain_spells:
        print(f"  • {spell}")
    
    print("\n" + "=" * 60)
    print(cleric)
    print("=" * 60)