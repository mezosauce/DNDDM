#!/usr/bin/env python3
"""
Rogue Class - D&D 5e SRD Implementation
Derived from the base Character class with full Rogue features
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from Head.campaign_manager import Character


@dataclass
class Rogue(Character):
    """
    Rogue class implementation following D&D 5e SRD
    Inherits from Character and adds Rogue-specific features
    """
    
    # Rogue-specific attributes
    roguish_archetype: str = ""  # "Thief", "Assassin", or "Arcane Trickster"
    
    # Sneak Attack mechanics
    sneak_attack_dice: int = 1  # Number of d6 dice for sneak attack
    sneak_attack_used_this_turn: bool = False
    
    # Expertise tracking
    expertise_skills: Set[str] = field(default_factory=set)
    expertise_thieves_tools: bool = False
    
    # Cunning Action
    cunning_action_available: bool = False
    
    # Class features by level
    uncanny_dodge_available: bool = False
    evasion_available: bool = False
    reliable_talent_available: bool = False
    blindsense_available: bool = False
    slippery_mind_available: bool = False
    elusive_available: bool = False
    stroke_of_luck_available: bool = False
    stroke_of_luck_used: bool = False
    
    # Thief archetype features
    fast_hands_available: bool = False
    second_story_work_available: bool = False
    supreme_sneak_available: bool = False
    use_magic_device_available: bool = False
    thiefs_reflexes_available: bool = False
    
    # Archetype features unlocked at certain levels
    archetype_feature_3: bool = False
    archetype_feature_9: bool = False
    archetype_feature_13: bool = False
    archetype_feature_17: bool = False
    
    def __post_init__(self):
        """Initialize Rogue with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Rogue"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Rogues typically have high DEX and INT/CHA
            self.stats = {
                "strength": 10,
                "dexterity": 16,
                "constitution": 14,
                "intelligence": 13,
                "wisdom": 12,
                "charisma": 10
            }
        
        # Set hit points based on level (1d8 per level)
        if self.level == 1:
            self.max_hp = 8 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Rogues choose four from: Acrobatics, Athletics, Deception, Insight, 
            # Intimidation, Investigation, Perception, Performance, Persuasion, 
            # Sleight of Hand, and Stealth
            self.skill_proficiencies = ["Stealth", "Acrobatics", "Perception", "Investigation"]
        
        if not self.languages_known:
            self.languages_known = ["Common", "Thieves' Cant"]
        
        # Set initial expertise (level 1)
        if self.level >= 1:
            # Default expertise choices - can be customized
            self.expertise_skills = {"Stealth", "Acrobatics"}
            self.expertise_thieves_tools = False  # Could be True if choosing thieves' tools
        
        # Calculate AC based on light armor (default leather armor = 11 + DEX)
        if self.ac == 10:
            self.ac = 11 + self._get_modifier("dexterity")
        
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
    
    def get_expertise_bonus(self, skill: str = None, tool: str = None) -> int:
        """
        Calculate expertise bonus for a skill or tool
        Returns double proficiency bonus if expertise applies
        """
        if skill and skill in self.expertise_skills:
            return self.get_proficiency_bonus() * 2
        if tool and tool == "thieves' tools" and self.expertise_thieves_tools:
            return self.get_proficiency_bonus() * 2
        return self.get_proficiency_bonus()
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Sneak Attack progression
        sneak_attack_levels = {
            1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 5, 10: 5,
            11: 6, 12: 6, 13: 7, 14: 7, 15: 8, 16: 8, 17: 9, 18: 9, 19: 10, 20: 10
        }
        self.sneak_attack_dice = sneak_attack_levels.get(self.level, 1)
        
        # Class features by level
        if self.level >= 1:
            # Expertise and Thieves' Cant already handled in __post_init__
            pass
        
        if self.level >= 2:
            self.cunning_action_available = True
        
        if self.level >= 3:
            self.archetype_feature_3 = True
        
        if self.level >= 5:
            self.uncanny_dodge_available = True
        
        if self.level >= 6:
            # Additional expertise (can be customized)
            self.expertise_skills.update({"Sleight of Hand", "Perception"})
        
        if self.level >= 7:
            self.evasion_available = True
        
        if self.level >= 9:
            self.archetype_feature_9 = True
        
        if self.level >= 11:
            self.reliable_talent_available = True
        
        if self.level >= 13:
            self.archetype_feature_13 = True
        
        if self.level >= 14:
            self.blindsense_available = True
        
        if self.level >= 15:
            self.slippery_mind_available = True
            # Gain proficiency in Wisdom saving throws
            # This would need to be integrated with the base saving throw system
        
        if self.level >= 17:
            self.archetype_feature_17 = True
        
        if self.level >= 18:
            self.elusive_available = True
        
        if self.level >= 20:
            self.stroke_of_luck_available = True
        
        # Thief archetype features
        if self.roguish_archetype == "Thief":
            if self.level >= 3:
                self.fast_hands_available = True
                self.second_story_work_available = True
            if self.level >= 9:
                self.supreme_sneak_available = True
            if self.level >= 13:
                self.use_magic_device_available = True
            if self.level >= 17:
                self.thiefs_reflexes_available = True
    
    def can_sneak_attack(self, has_advantage: bool, ally_near_target: bool = False, 
                        has_disadvantage: bool = False, weapon_type: str = "finesse") -> bool:
        """
        Check if sneak attack can be applied
        Conditions:
        - Must have advantage OR ally within 5ft of target (and no disadvantage)
        - Must use finesse or ranged weapon
        - Once per turn
        """
        if self.sneak_attack_used_this_turn:
            return False
        
        if weapon_type not in ["finesse", "ranged"]:
            return False
        
        if has_disadvantage:
            return False
        
        return has_advantage or ally_near_target
    
    def calculate_sneak_attack_damage(self) -> int:
        """Calculate sneak attack damage (returns total dice, not rolled value)"""
        return self.sneak_attack_dice * 3.5  # Average of d6 is 3.5
    
    def use_sneak_attack(self) -> bool:
        """
        Mark sneak attack as used this turn
        Returns True if successful, False if already used
        """
        if self.sneak_attack_used_this_turn:
            return False
        
        self.sneak_attack_used_this_turn = True
        return True
    
    def reset_turn(self):
        """Reset turn-based features"""
        self.sneak_attack_used_this_turn = False
    
    def use_cunning_action(self, action: str) -> bool:
        """
        Use Cunning Action to take Dash, Disengage, or Hide as bonus action
        Returns True if successful
        """
        if not self.cunning_action_available:
            return False
        
        if action.lower() not in ["dash", "disengage", "hide"]:
            return False
        
        # In actual implementation, this would trigger the action
        # For now, just return success
        return True
    
    def use_uncanny_dodge(self) -> bool:
        """Use Uncanny Dodge to halve damage from an attack"""
        if not self.uncanny_dodge_available:
            return False
        
        # In actual implementation, this would be called when taking damage
        # For now, just return availability
        return True
    
    def use_evasion(self, saving_throw_success: bool) -> int:
        """
        Use Evasion when subjected to effect requiring DEX save
        Returns damage taken (0 on success, half on failure)
        """
        if not self.evasion_available:
            return 1  # Normal rules apply
        
        if saving_throw_success:
            return 0  # No damage on successful save
        else:
            return 0.5  # Half damage on failed save
    
    def use_reliable_talent(self, ability_check_roll: int) -> int:
        """
        Apply Reliable Talent to ability check
        Treats rolls of 9 or lower as 10
        """
        if not self.reliable_talent_available:
            return ability_check_roll
        
        # Only applies to skills you're proficient in
        # This would need to be checked by the caller
        return max(ability_check_roll, 10)
    
    def use_stroke_of_luck(self, attack_missed: bool = False, ability_check_failed: bool = False) -> bool:
        """
        Use Stroke of Luck to turn miss into hit or failed check into 20
        Returns True if successful and resource consumed
        """
        if not self.stroke_of_luck_available:
            return False
        
        if self.stroke_of_luck_used:
            return False
        
        if attack_missed or ability_check_failed:
            self.stroke_of_luck_used = True
            return True
        
        return False
    
    def short_rest(self):
        """Reset short rest resources"""
        self.stroke_of_luck_used = False
    
    def long_rest(self):
        """Reset long rest resources"""
        self.stroke_of_luck_used = False
        self.hp = self.max_hp
        self.reset_turn()
    
    def level_up(self):
        """Level up the rogue"""
        self.level += 1
        
        # Increase HP (1d8 + CON mod per level, or 4.5 + CON mod average)
        hp_gain = 4 + self._get_modifier("constitution")  # Rounded down average
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
            "roguish_archetype": self.roguish_archetype if self.roguish_archetype else "Not chosen (Level 3+)",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": self.ac,
            "speed": 30,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "dexterity": self._get_modifier("dexterity") + self.get_proficiency_bonus(),
                "intelligence": self._get_modifier("intelligence") + self.get_proficiency_bonus(),
                "wisdom": self._get_modifier("wisdom") + (self.get_proficiency_bonus() if self.slippery_mind_available else 0)
            },
            
            "skills": self.skill_proficiencies,
            "expertise_skills": list(self.expertise_skills),
            "expertise_thieves_tools": self.expertise_thieves_tools,
            "languages": self.languages_known,
            
            "sneak_attack": {
                "dice": f"{self.sneak_attack_dice}d6",
                "average_damage": self.calculate_sneak_attack_damage(),
                "used_this_turn": self.sneak_attack_used_this_turn
            },
            
            "features": {
                "Expertise": True,
                "Sneak Attack": True,
                "Thieves' Cant": True,
                "Cunning Action": self.cunning_action_available,
                "Uncanny Dodge": self.uncanny_dodge_available,
                "Evasion": self.evasion_available,
                "Reliable Talent": self.reliable_talent_available,
                "Blindsense": self.blindsense_available,
                "Slippery Mind": self.slippery_mind_available,
                "Elusive": self.elusive_available,
                "Stroke of Luck": self.stroke_of_luck_available
            },
            
            "thief_features": {
                "Fast Hands": self.fast_hands_available,
                "Second-Story Work": self.second_story_work_available,
                "Supreme Sneak": self.supreme_sneak_available,
                "Use Magic Device": self.use_magic_device_available,
                "Thief's Reflexes": self.thiefs_reflexes_available
            } if self.roguish_archetype == "Thief" else {},
            
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
        archetype_str = f" ({self.roguish_archetype})" if self.roguish_archetype else ""
        sneak_str = f"Sneak Attack: {self.sneak_attack_dice}d6"
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{archetype_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac} | {sneak_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Rogue
    rogue = Rogue(
        name="Silas Shadowstep",
        race="Half-Elf",
        char_class="Rogue",
        background="Criminal",
        level=1,
        stats={
            "strength": 10,
            "dexterity": 16,
            "constitution": 14,
            "intelligence": 12,
            "wisdom": 13,
            "charisma": 14
        },
        alignment="Chaotic Good",
        personality_traits=["I always have a plan for when things go wrong", "I am incredibly slow to trust"],
        ideal="Freedom. Chains are meant to be broken, as are those who would forge them.",
        bond="I'm trying to pay off an old debt I owe to a generous benefactor.",
        flaw="I can't resist taking a risk if there's money involved."
    )
    
    # Set starting equipment
    rogue.inventory = ["Rapier", "Shortbow", "Arrows (20)", "Burglar's Pack", "Leather Armor", "Dagger x2", "Thieves' Tools"]
    
    print("=" * 60)
    print("ROGUE CHARACTER SHEET")
    print("=" * 60)
    print(rogue)
    print()
    
    # Display character sheet
    sheet = rogue.get_character_sheet()
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
    
    print("Sneak Attack:")
    print(f"  Dice: {sheet['sneak_attack']['dice']}")
    print(f"  Average Damage: {sheet['sneak_attack']['average_damage']:.1f}")
    print(f"  Used This Turn: {sheet['sneak_attack']['used_this_turn']}")
    print()
    
    print("Expertise Skills:")
    for skill in sheet['expertise_skills']:
        print(f"  • {skill}")
    print(f"  Thieves' Tools Expertise: {sheet['expertise_thieves_tools']}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    print("Equipment:")
    for item in rogue.inventory:
        print(f"  • {item}")
    print()
    
    # Test sneak attack mechanics
    print("=" * 60)
    print("TESTING SNEAK ATTACK MECHANICS")
    print("=" * 60)
    
    print("\nChecking sneak attack conditions...")
    can_sneak = rogue.can_sneak_attack(
        has_advantage=True,
        ally_near_target=False,
        has_disadvantage=False,
        weapon_type="finesse"
    )
    print(f"Can use sneak attack (with advantage): {can_sneak}")
    
    can_sneak_ally = rogue.can_sneak_attack(
        has_advantage=False,
        ally_near_target=True,
        has_disadvantage=False,
        weapon_type="finesse"
    )
    print(f"Can use sneak attack (with ally nearby): {can_sneak_ally}")
    
    print("\nUsing sneak attack...")
    if rogue.use_sneak_attack():
        print("✓ Sneak attack activated!")
        print(f"Sneak attack damage: {rogue.calculate_sneak_attack_damage():.1f} average")
    
    print("\nTrying to use sneak attack again this turn...")
    if not rogue.use_sneak_attack():
        print("✗ Cannot use sneak attack again this turn (already used)")
    
    print("\nResetting turn...")
    rogue.reset_turn()
    print("✓ Turn reset - sneak attack available again")
    
    # Test leveling up
    print("\n" + "=" * 60)
    print("TESTING LEVEL UP")
    print("=" * 60)
    
    print(f"\nCurrent level: {rogue.level}")
    print(f"Current HP: {rogue.hp}/{rogue.max_hp}")
    print(f"Current sneak attack: {rogue.sneak_attack_dice}d6")
    
    rogue.level_up()
    rogue.level_up()  # Level to 3
    rogue.roguish_archetype = "Thief"
    rogue.apply_level_features()
    
    print(f"\nAfter level up to level {rogue.level}:")
    print(f"New HP: {rogue.hp}/{rogue.max_hp}")
    print(f"New sneak attack: {rogue.sneak_attack_dice}d6")
    print(f"Features unlocked: Cunning Action, Thief Archetype")
    print(f"Thief features: Fast Hands, Second-Story Work")
    
    # Level up more to test higher level features
    for _ in range(4):  # Level to 7
        rogue.level_up()
    
    print(f"\nAt level {rogue.level}:")
    print(f"Sneak attack: {rogue.sneak_attack_dice}d6")
    print(f"Features: Uncanny Dodge, Evasion")
    
    print("\n" + "=" * 60)
    print(rogue)
    print("=" * 60)