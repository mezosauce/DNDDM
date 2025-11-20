#!/usr/bin/env python3
"""
Fighter Class - D&D 5e SRD Implementation
Derived from the base Character class with full Fighter features
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


from Head.campaign_manager import Character


@dataclass
class Fighter(Character):
    """
    Fighter class implementation following D&D 5e SRD
    Inherits from Character and adds Fighter-specific features
    """
    
    # Fighter-specific attributes
    martial_archetype: str = ""  # "Champion", "Battle Master", "Eldritch Knight"
    
    # Core Fighter mechanics
    fighting_styles: List[str] = field(default_factory=list)
    second_wind_used: bool = False
    action_surge_uses: int = 0
    action_surge_max_uses: int = 1
    indomitable_uses: int = 0
    indomitable_max_uses: int = 1
    
    # Extra Attack progression
    extra_attacks: int = 1  # Base is 1 attack, increases at levels 5, 11, 20
    
    # Champion archetype features
    improved_critical: bool = False  # Crit on 19-20
    remarkable_athlete: bool = False  # Level 7 Champion
    additional_fighting_style: bool = False  # Level 10 Champion
    superior_critical: bool = False  # Crit on 18-20
    survivor_active: bool = False  # Level 18 Champion
    
    # Archetype features unlocked at certain levels
    archetype_feature_3: bool = False
    archetype_feature_7: bool = False
    archetype_feature_10: bool = False
    archetype_feature_15: bool = False
    archetype_feature_18: bool = False
    
    def __post_init__(self):
        """Initialize Fighter with proper stats and proficiencies"""
        super().__post_init__()
        
        # Set class type
        self.char_class = "Fighter"
        
        # Set initial stats if not provided
        if not self.stats or all(v == 10 for v in self.stats.values()):
            # Fighters typically have high STR and CON
            self.stats = {
                "strength": 16,
                "dexterity": 14,
                "constitution": 15,
                "intelligence": 10,
                "wisdom": 12,
                "charisma": 8
            }
        
        # Set hit points based on level (1d10 per level)
        if self.level == 1:
            self.max_hp = 10 + self._get_modifier("constitution")
            self.hp = self.max_hp
        
        # Initialize proficiencies if empty
        if not self.skill_proficiencies:
            # Fighters choose two from: Acrobatics, Animal Handling, Athletics, 
            # History, Insight, Intimidation, Perception, Survival
            self.skill_proficiencies = ["Athletics", "Intimidation"]
        
        if not self.languages_known:
            self.languages_known = ["Common"]
        
        # Apply level-based features
        self.apply_level_features()
    
    def _get_modifier(self, ability: str) -> int:
        """Calculate ability modifier"""
        return (self.stats.get(ability, 10) - 10) // 2
    
    def apply_level_features(self):
        """Apply features based on current level according to SRD"""
        # Action Surge progression
        if self.level >= 2:
            self.action_surge_max_uses = 1
        if self.level >= 17:
            self.action_surge_max_uses = 2
        
        # Indomitable progression
        if self.level >= 9:
            self.indomitable_max_uses = 1
        if self.level >= 13:
            self.indomitable_max_uses = 2
        if self.level >= 17:
            self.indomitable_max_uses = 3
        
        # Extra Attack progression
        if self.level < 5:
            self.extra_attacks = 1
        elif self.level < 11:
            self.extra_attacks = 2
        elif self.level < 20:
            self.extra_attacks = 3
        else:
            self.extra_attacks = 4
        
        # Class features by level
        if self.level >= 1:
            # Starting fighting style
            if not self.fighting_styles:
                self.fighting_styles = ["Defense"]
        
        if self.level >= 3:
            self.archetype_feature_3 = True
        
        if self.level >= 7:
            self.archetype_feature_7 = True
        
        if self.level >= 10:
            self.archetype_feature_10 = True
        
        if self.level >= 15:
            self.archetype_feature_15 = True
        
        if self.level >= 18:
            self.archetype_feature_18 = True
        
        # Champion archetype features
        if self.martial_archetype == "Champion":
            if self.level >= 3:
                self.improved_critical = True
            if self.level >= 7:
                self.remarkable_athlete = True
            if self.level >= 10:
                self.additional_fighting_style = True
            if self.level >= 15:
                self.superior_critical = True
            if self.level >= 18:
                self.survivor_active = True
    
    def use_second_wind(self) -> Tuple[bool, int]:
        """
        Use Second Wind to regain hit points.
        Returns (success, hp_healed)
        """
        if self.second_wind_used:
            return False, 0
        
        hp_healed = max(1, self.roll_dice(1, 10)) + self.level
        self.hp = min(self.hp + hp_healed, self.max_hp)
        self.second_wind_used = True
        return True, hp_healed
    
    def use_action_surge(self) -> bool:
        """
        Use Action Surge to take an additional action.
        Returns True if successful, False otherwise.
        """
        if self.action_surge_uses >= self.action_surge_max_uses:
            return False
        
        self.action_surge_uses += 1
        return True
    
    def use_indomitable(self) -> bool:
        """
        Use Indomitable to reroll a failed saving throw.
        Returns True if successful, False otherwise.
        """
        if self.indomitable_uses >= self.indomitable_max_uses:
            return False
        
        self.indomitable_uses += 1
        return True
    
    def short_rest(self):
        """Reset short rest resources"""
        self.second_wind_used = False
        self.action_surge_uses = 0
    
    def long_rest(self):
        """Reset all resources on long rest"""
        self.second_wind_used = False
        self.action_surge_uses = 0
        self.indomitable_uses = 0
        self.hp = self.max_hp
    
    def add_fighting_style(self, style: str) -> bool:
        """
        Add a fighting style to the fighter.
        Returns True if successful, False if style already exists.
        """
        if style in self.fighting_styles:
            return False
        
        self.fighting_styles.append(style)
        return True
    
    def get_fighting_style_benefits(self, style: str) -> Dict[str, any]:
        """Get the benefits of a specific fighting style"""
        benefits = {
            "Archery": {
                "description": "+2 bonus to attack rolls with ranged weapons",
                "ranged_attack_bonus": 2
            },
            "Defense": {
                "description": "+1 bonus to AC while wearing armor",
                "ac_bonus": 1
            },
            "Dueling": {
                "description": "+2 bonus to damage rolls with one-handed melee weapons when wielding only one weapon",
                "damage_bonus": 2
            },
            "Great Weapon Fighting": {
                "description": "Reroll 1s and 2s on damage dice for two-handed weapons",
                "reroll_damage": [1, 2]
            },
            "Protection": {
                "description": "Use reaction to impose disadvantage on attack against ally within 5ft when wielding shield",
                "impose_disadvantage": True
            },
            "Two-Weapon Fighting": {
                "description": "Add ability modifier to damage of off-hand attack",
                "add_ability_modifier": True
            }
        }
        
        return benefits.get(style, {})
    
    def calculate_ac_with_fighting_styles(self, base_ac: int) -> int:
        """Calculate AC including fighting style bonuses"""
        ac = base_ac
        if "Defense" in self.fighting_styles:
            ac += 1
        return ac
    
    def get_critical_range(self) -> Tuple[int, int]:
        """Get the critical hit range based on Champion features"""
        if self.superior_critical and self.martial_archetype == "Champion":
            return 18, 20
        elif self.improved_critical and self.martial_archetype == "Champion":
            return 19, 20
        else:
            return 20, 20
    
    def get_remarkable_athlete_bonus(self) -> int:
        """Calculate the Remarkable Athlete bonus (half proficiency, round up)"""
        proficiency_bonus = self.get_proficiency_bonus()
        return (proficiency_bonus + 1) // 2  # Round up
    
    def check_survivor_healing(self) -> int:
        """
        Check if Survivor feature activates at start of turn.
        Returns HP regained (0 if not applicable)
        """
        if not self.survivor_active:
            return 0
        
        if self.hp <= self.max_hp // 2 and self.hp > 0:
            healing = 5 + self._get_modifier("constitution")
            self.hp = min(self.hp + healing, self.max_hp)
            return healing
        
        return 0
    
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
        """Level up the fighter"""
        self.level += 1
        
        # Increase HP (1d10 + CON mod per level, or 6 + CON mod average)
        hp_gain = 6 + self._get_modifier("constitution")
        self.max_hp += hp_gain
        self.hp += hp_gain
        
        # Reapply level-based features
        self.apply_level_features()
    
    def get_character_sheet(self) -> Dict:
        """Generate a complete character sheet"""
        # Calculate AC with fighting styles
        current_ac = self.calculate_ac_with_fighting_styles(self.ac)
        
        return {
            "name": self.name,
            "race": self.race,
            "class": f"{self.char_class} {self.level}",
            "background": self.background,
            "alignment": self.alignment,
            "martial_archetype": self.martial_archetype if self.martial_archetype else "Not chosen (Level 3+)",
            
            "hit_points": f"{self.hp}/{self.max_hp}",
            "armor_class": current_ac,
            "speed": self.speed,
            
            "ability_scores": self.stats,
            "proficiency_bonus": self.get_proficiency_bonus(),
            
            "saving_throws": {
                "strength": self._get_modifier("strength") + self.get_proficiency_bonus(),
                "constitution": self._get_modifier("constitution") + self.get_proficiency_bonus()
            },
            
            "skills": self.skill_proficiencies,
            "languages": self.languages_known,
            
            "combat_features": {
                "fighting_styles": self.fighting_styles,
                "second_wind_available": not self.second_wind_used,
                "action_surge": f"{self.action_surge_uses}/{self.action_surge_max_uses}",
                "indomitable": f"{self.indomitable_uses}/{self.indomitable_max_uses}",
                "extra_attacks": self.extra_attacks
            },
            
            "features": {
                "Fighting Style": ", ".join(self.fighting_styles) if self.fighting_styles else "None chosen",
                "Second Wind": True,
                "Action Surge": self.action_surge_max_uses > 0,
                "Martial Archetype": self.martial_archetype if self.martial_archetype else "Available at Level 3",
                "Extra Attack": f"{self.extra_attacks} attacks" if self.extra_attacks > 1 else False,
                "Indomitable": self.indomitable_max_uses > 0,
                
                # Champion features
                "Improved Critical": self.improved_critical,
                "Remarkable Athlete": self.remarkable_athlete,
                "Additional Fighting Style": self.additional_fighting_style,
                "Superior Critical": self.superior_critical,
                "Survivor": self.survivor_active
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
    
    def roll_dice(self, num_dice: int, dice_type: int) -> int:
        """
        Simulate rolling dice. In a real implementation, this would use random.
        For testing purposes, returns average roll.
        """
        return (num_dice * (dice_type + 1)) // 2
    
    def __str__(self) -> str:
        """String representation"""
        archetype_str = f" ({self.martial_archetype})" if self.martial_archetype else ""
        action_surge_str = f" | Action Surge: {self.action_surge_uses}/{self.action_surge_max_uses}"
        second_wind_str = " | Second Wind: Available" if not self.second_wind_used else " | Second Wind: Used"
        return f"{self.name} - Level {self.level} {self.race} {self.char_class}{archetype_str} | HP: {self.hp}/{self.max_hp} | AC: {self.ac}{action_surge_str}{second_wind_str}"


# Example usage and testing
if __name__ == "__main__":
    # Create a new Fighter
    fighter = Fighter(
        name="Sir Reginald Steelheart",
        race="Human",
        char_class="Fighter",
        background="Soldier",
        level=1,
        stats={
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8
        },
        alignment="Lawful Good",
        personality_traits=["I'm always polite and respectful", "I face problems head-on"],
        ideal="Greater Good. Our lot is to lay down our lives in defense of others",
        bond="I fight for those who cannot fight for themselves",
        flaw="I'd rather eat my armor than admit I'm wrong"
    )
    
    # Set starting equipment
    fighter.inventory = ["Longsword", "Shield", "Chain Mail", "Light Crossbow", "20 Bolts", "Dungeoneer's Pack"]
    
    print("=" * 60)
    print("FIGHTER CHARACTER SHEET")
    print("=" * 60)
    print(fighter)
    print()
    
    # Display character sheet
    sheet = fighter.get_character_sheet()
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
    
    print("Combat Features:")
    print(f"  Fighting Styles: {', '.join(sheet['combat_features']['fighting_styles'])}")
    print(f"  Second Wind: {'Available' if sheet['combat_features']['second_wind_available'] else 'Used'}")
    print(f"  Action Surge: {sheet['combat_features']['action_surge']}")
    print(f"  Indomitable: {sheet['combat_features']['indomitable']}")
    print(f"  Extra Attacks: {sheet['combat_features']['extra_attacks']}")
    print()
    
    print("Class Features:")
    for feature, value in sheet['features'].items():
        if value and value is not False:
            print(f"  • {feature}: {value if isinstance(value, str) else '✓'}")
    print()
    
    print("Equipment:")
    for item in fighter.inventory:
        print(f"  • {item}")
    print()
    
    # Test Second Wind
    print("=" * 60)
    print("TESTING SECOND WIND")
    print("=" * 60)
    
    # Take some damage first
    fighter.hp -= 8
    print(f"HP after taking damage: {fighter.hp}/{fighter.max_hp}")
    
    print("\nUsing Second Wind...")
    success, hp_healed = fighter.use_second_wind()
    if success:
        print(f"✓ Second Wind healed {hp_healed} HP!")
        print(f"Current HP: {fighter.hp}/{fighter.max_hp}")
    
    # Test Action Surge
    print("\n" + "=" * 60)
    print("TESTING ACTION SURGE")
    print("=" * 60)
    
    print("\nUsing Action Surge...")
    if fighter.use_action_surge():
        print("✓ Action Surge activated! You can take an additional action this turn.")
        print(f"Action Surge uses remaining: {fighter.action_surge_max_uses - fighter.action_surge_uses}")
    
    # Test leveling up
    print("\n" + "=" * 60)
    print("TESTING LEVEL UP")
    print("=" * 60)
    
    print(f"\nCurrent level: {fighter.level}")
    print(f"Current HP: {fighter.hp}/{fighter.max_hp}")
    print(f"Current extra attacks: {fighter.extra_attacks}")
    
    fighter.level_up()
    fighter.level_up()  # Level up to 3 to choose archetype
    fighter.martial_archetype = "Champion"
    fighter.apply_level_features()
    
    print(f"\nAfter level up to Level {fighter.level}:")
    print(f"New HP: {fighter.hp}/{fighter.max_hp}")
    print(f"Martial Archetype: {fighter.martial_archetype}")
    print(f"Features unlocked: Improved Critical (crit on 19-20)")
    print(f"Critical range: {fighter.get_critical_range()}")
    
    # Level up further to test more features
    for _ in range(7):  # Level up to 10
        fighter.level_up()
    fighter.apply_level_features()
    
    print(f"\nAt Level {fighter.level}:")
    print(f"Extra Attacks: {fighter.extra_attacks}")
    print(f"Action Surge uses: {fighter.action_surge_max_uses}")
    print(f"Features unlocked: Remarkable Athlete, Additional Fighting Style")
    
    # Test Remarkable Athlete
    if fighter.remarkable_athlete:
        bonus = fighter.get_remarkable_athlete_bonus()
        print(f"Remarkable Athlete bonus: +{bonus}")
    
    print("\n" + "=" * 60)
    print(fighter)
    print("=" * 60)