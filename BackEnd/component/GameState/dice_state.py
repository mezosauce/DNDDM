#!/usr/bin/env python3

"""

•	Dice Roll State:
    o	Input:
    	    Situation
    	    Success Rate (For example the overall score they need to succeed)
    	    Player Base Status
    	    Type of Dice to Roll
    o	Output:
    	    Succeeded or not
    	    If the score is above +10 > expected result {Give message to LLM dialogue to cover how the player did it with ease}
    o	Explanation: The goal is to be able to provide actual proper story telling with the interactive feeling with the user to roll the 
        dice and see the calculations with their base params and then offer a clean output to the LLM to move on.


"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from enum import Enum
import random
import re


class DiceType(Enum):
    """Standard RPG dice types"""
    D4 = 4
    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12
    D20 = 20
    D100 = 100


class RollOutcome(Enum):
    """Possible roll outcomes"""
    CRITICAL_SUCCESS = "critical_success"  # +10 or more above target
    SUCCESS = "success"
    FAILURE = "failure"
    CRITICAL_FAILURE = "critical_failure"  # Natural 1 on d20
    PENDING = "pending"


class DifficultyLevel(Enum):
    """Standard D&D difficulty classes"""
    TRIVIAL = 5
    EASY = 10
    MEDIUM = 15
    HARD = 20
    VERY_HARD = 25
    NEARLY_IMPOSSIBLE = 30


class RollType(Enum):
    """Types of rolls"""
    NORMAL = "normal"
    ADVANTAGE = "advantage"  # Roll twice, take higher
    DISADVANTAGE = "disadvantage"  # Roll twice, take lower


@dataclass
class PlayerStats:
    """Player's base statistics and modifiers"""
    strength: int = 0
    dexterity: int = 0
    constitution: int = 0
    intelligence: int = 0
    wisdom: int = 0
    charisma: int = 0
    
    # Skill proficiencies (bonus added to relevant rolls)
    proficiency_bonus: int = 2
    proficient_skills: List[str] = field(default_factory=list)
    
    # Additional modifiers
    equipment_bonus: int = 0
    temporary_bonus: int = 0
    
    def get_modifier(self, stat_name: str) -> int:
        """Calculate D&D style modifier from stat (stat-10)//2"""
        stat_value = getattr(self, stat_name.lower(), 10)
        return (stat_value - 10) // 2
    
    def get_total_modifier(self, stat_name: str, skill: Optional[str] = None) -> int:
        """Get total modifier including proficiency and bonuses"""
        base_mod = self.get_modifier(stat_name)
        
        # Add proficiency if applicable
        proficiency = 0
        if skill and skill.lower() in [s.lower() for s in self.proficient_skills]:
            proficiency = self.proficiency_bonus
        
        return base_mod + proficiency + self.equipment_bonus + self.temporary_bonus


@dataclass
class RollContext:
    """Context for a dice roll scenario"""
    roll_id: str
    situation: str  # The scenario description
    dice_type: DiceType
    target_number: int  # DC (Difficulty Class)
    relevant_stat: str  # Which stat applies (strength, dexterity, etc.)
    skill: Optional[str] = None  # Specific skill (athletics, stealth, etc.)
    roll_type: RollType = RollType.NORMAL
    player_stats: Optional[PlayerStats] = None
    
    # Flavor text for outcomes
    success_text: Optional[str] = None
    failure_text: Optional[str] = None
    critical_success_text: Optional[str] = None
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)


@dataclass
class RollResult:
    """Result of a dice roll"""
    roll_id: str
    
    # Roll details
    dice_type: DiceType
    raw_rolls: List[int]  # All dice rolled (2 if advantage/disadvantage)
    selected_roll: int  # The roll that counts
    modifiers: Dict[str, int]  # Breakdown of all modifiers
    total_score: int  # Final score after modifiers
    
    # Outcome
    target_number: int
    outcome: RollOutcome
    margin: int  # How much above/below target
    
    # Context
    situation: str
    relevant_stat: str
    skill: Optional[str] = None
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get_narrative_result(self) -> str:
        """Get a narrative description of the result"""
        if self.outcome == RollOutcome.CRITICAL_SUCCESS:
            return f"🎯 **CRITICAL SUCCESS!** (Rolled {self.total_score}, needed {self.target_number}. +{self.margin} over target!)"
        elif self.outcome == RollOutcome.SUCCESS:
            return f"✅ **Success!** (Rolled {self.total_score}, needed {self.target_number})"
        elif self.outcome == RollOutcome.CRITICAL_FAILURE:
            return f"💥 **CRITICAL FAILURE!** (Natural 1!)"
        else:
            return f"❌ **Failure.** (Rolled {self.total_score}, needed {self.target_number})"
    
    def get_roll_breakdown(self) -> str:
        """Get detailed breakdown of the roll"""
        breakdown = f" **Roll Breakdown:**\n"
        breakdown += f"  • Dice: {self.dice_type.name}\n"
        
        if len(self.raw_rolls) > 1:
            breakdown += f"  • Rolls: {', '.join(map(str, self.raw_rolls))} (using {self.selected_roll})\n"
        else:
            breakdown += f"  • Roll: {self.selected_roll}\n"
        
        if self.modifiers:
            breakdown += f"  • Modifiers:\n"
            for mod_name, mod_value in self.modifiers.items():
                if mod_value != 0:
                    breakdown += f"    - {mod_name}: {mod_value:+d}\n"
        
        breakdown += f"  • **Total: {self.total_score}** vs DC {self.target_number}"
        
        return breakdown


class DiceRollState:
    """
    Manages dice roll mechanics in the game.
    
    Use Cases:
    - Skill checks: "Roll Athletics to climb the wall"
    - Combat: "Roll to hit the goblin"
    - Saving throws: "Roll Constitution to resist poison"
    - Ability checks: "Roll Intelligence to recall lore"
    """
    
    # Patterns that indicate a dice roll is needed
    ROLL_PATTERNS = [
        r"roll\s+(?:a\s+)?(?:d\d+|\w+\s+check)",
        r"make\s+(?:a\s+)?(?:\w+\s+)?(?:check|save|roll)",
        r"(?:attempt|try)\s+to",
        r"(?:strength|dexterity|constitution|intelligence|wisdom|charisma)\s+(?:check|save)",
        r"dc\s+\d+",
        r"difficulty\s+(?:class|check)",
    ]
    
    # Common skill to stat mapping
    SKILL_STAT_MAP = {
        'athletics': 'strength',
        'acrobatics': 'dexterity',
        'sleight of hand': 'dexterity',
        'stealth': 'dexterity',
        'arcana': 'intelligence',
        'history': 'intelligence',
        'investigation': 'intelligence',
        'nature': 'intelligence',
        'religion': 'intelligence',
        'animal handling': 'wisdom',
        'insight': 'wisdom',
        'medicine': 'wisdom',
        'perception': 'wisdom',
        'survival': 'wisdom',
        'deception': 'charisma',
        'intimidation': 'charisma',
        'performance': 'charisma',
        'persuasion': 'charisma',
    }
    
    def __init__(self, player_stats: Optional[PlayerStats] = None):
        self.player_stats = player_stats or PlayerStats()
        self.active_roll: Optional[RollContext] = None
        self.roll_history: List[RollContext] = []
        self.result_history: List[RollResult] = []
        self.is_active: bool = False
        self._roll_counter: int = 0
    
    def detect_roll_request(self, dm_response: str) -> bool:
        """
        Detect if the DM's response requires a dice roll.
        
        Args:
            dm_response: The DM's narration/response
            
        Returns:
            True if roll detected, False otherwise
        """
        dm_lower = dm_response.lower()
        
        for pattern in self.ROLL_PATTERNS:
            if re.search(pattern, dm_lower):
                return True
        
        return False
    
    def parse_roll_request(self, dm_response: str) -> Dict:
        """
        Parse DM response to extract roll parameters.
        
        Args:
            dm_response: The DM's narration
            
        Returns:
            Dictionary with parsed parameters
        """
        dm_lower = dm_response.lower()
        parsed = {
            'dice_type': DiceType.D20,  # Default
            'target_number': 15,  # Default medium difficulty
            'relevant_stat': 'strength',  # Default
            'skill': None,
            'roll_type': RollType.NORMAL
        }
        
        # Parse dice type
        dice_match = re.search(r'd(\d+)', dm_lower)
        if dice_match:
            dice_value = int(dice_match.group(1))
            try:
                parsed['dice_type'] = DiceType(dice_value)
            except ValueError:
                pass  # Keep default
        
        # Parse target number / DC
        dc_match = re.search(r'dc\s+(\d+)', dm_lower)
        if dc_match:
            parsed['target_number'] = int(dc_match.group(1))
        else:
            # Try to infer from difficulty words
            if 'easy' in dm_lower or 'simple' in dm_lower:
                parsed['target_number'] = DifficultyLevel.EASY.value
            elif 'hard' in dm_lower or 'difficult' in dm_lower:
                parsed['target_number'] = DifficultyLevel.HARD.value
            elif 'very hard' in dm_lower or 'nearly impossible' in dm_lower:
                parsed['target_number'] = DifficultyLevel.VERY_HARD.value
        
        # Parse stat and skill
        for skill, stat in self.SKILL_STAT_MAP.items():
            if skill in dm_lower:
                parsed['skill'] = skill
                parsed['relevant_stat'] = stat
                break
        
        # If no skill found, check for direct stat mentions
        if not parsed['skill']:
            for stat in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
                if stat in dm_lower:
                    parsed['relevant_stat'] = stat
                    break
        
        # Parse advantage/disadvantage
        if 'advantage' in dm_lower:
            parsed['roll_type'] = RollType.ADVANTAGE
        elif 'disadvantage' in dm_lower:
            parsed['roll_type'] = RollType.DISADVANTAGE
        
        return parsed
    
    def activate_roll(
        self,
        situation: str,
        dice_type: DiceType = DiceType.D20,
        target_number: int = 15,
        relevant_stat: str = 'strength',
        skill: Optional[str] = None,
        roll_type: RollType = RollType.NORMAL,
        success_text: Optional[str] = None,
        failure_text: Optional[str] = None,
        critical_success_text: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> RollContext:
        """
        Activate a dice roll state.
        
        Args:
            situation: Description of what's being attempted
            dice_type: Type of dice to roll
            target_number: DC to beat
            relevant_stat: Which stat applies
            skill: Specific skill if applicable
            roll_type: Normal/Advantage/Disadvantage
            success_text: Flavor text for success
            failure_text: Flavor text for failure
            critical_success_text: Flavor text for critical success
            metadata: Additional context
            
        Returns:
            RollContext object
        """
        self._roll_counter += 1
        roll_id = f"R{self._roll_counter:04d}"
        
        self.active_roll = RollContext(
            roll_id=roll_id,
            situation=situation,
            dice_type=dice_type,
            target_number=target_number,
            relevant_stat=relevant_stat,
            skill=skill,
            roll_type=roll_type,
            player_stats=self.player_stats,
            success_text=success_text,
            failure_text=failure_text,
            critical_success_text=critical_success_text,
            metadata=metadata or {}
        )
        
        self.is_active = True
        self.roll_history.append(self.active_roll)
        
        return self.active_roll
    
    def roll_dice(self, dice_type: DiceType, count: int = 1) -> List[int]:
        """
        Roll dice of specified type.
        
        Args:
            dice_type: Type of dice
            count: Number of dice to roll
            
        Returns:
            List of roll results
        """
        return [random.randint(1, dice_type.value) for _ in range(count)]
    
    def execute_roll(self, auto_roll: bool = True) -> RollResult:
        """
        Execute the active dice roll.
        
        Args:
            auto_roll: If False, waits for manual roll input
            
        Returns:
            RollResult object
        """
        if not self.is_active or not self.active_roll:
            raise ValueError("No active roll to execute")
        
        roll_ctx = self.active_roll
        
        # Determine number of dice to roll
        num_rolls = 1
        if roll_ctx.roll_type in [RollType.ADVANTAGE, RollType.DISADVANTAGE]:
            num_rolls = 2
        
        # Roll the dice
        raw_rolls = self.roll_dice(roll_ctx.dice_type, num_rolls)
        
        # Select which roll to use
        if roll_ctx.roll_type == RollType.ADVANTAGE:
            selected_roll = max(raw_rolls)
        elif roll_ctx.roll_type == RollType.DISADVANTAGE:
            selected_roll = min(raw_rolls)
        else:
            selected_roll = raw_rolls[0]
        
        # Calculate modifiers
        modifiers = {}
        
        if roll_ctx.player_stats:
            stat_mod = roll_ctx.player_stats.get_modifier(roll_ctx.relevant_stat)
            if stat_mod != 0:
                modifiers[f'{roll_ctx.relevant_stat.capitalize()} Modifier'] = stat_mod
            
            # Add proficiency if applicable
            if roll_ctx.skill and roll_ctx.skill.lower() in [s.lower() for s in roll_ctx.player_stats.proficient_skills]:
                modifiers['Proficiency'] = roll_ctx.player_stats.proficiency_bonus
            
            # Add other bonuses
            if roll_ctx.player_stats.equipment_bonus != 0:
                modifiers['Equipment'] = roll_ctx.player_stats.equipment_bonus
            
            if roll_ctx.player_stats.temporary_bonus != 0:
                modifiers['Temporary Bonus'] = roll_ctx.player_stats.temporary_bonus
        
        # Calculate total
        total_modifier = sum(modifiers.values())
        total_score = selected_roll + total_modifier
        
        # Determine outcome
        margin = total_score - roll_ctx.target_number
        
        # Critical failure on natural 1 (for d20 only)
        if roll_ctx.dice_type == DiceType.D20 and selected_roll == 1:
            outcome = RollOutcome.CRITICAL_FAILURE
        # Critical success if +10 or more over target
        elif margin >= 10:
            outcome = RollOutcome.CRITICAL_SUCCESS
        elif total_score >= roll_ctx.target_number:
            outcome = RollOutcome.SUCCESS
        else:
            outcome = RollOutcome.FAILURE
        
        # Create result
        result = RollResult(
            roll_id=roll_ctx.roll_id,
            dice_type=roll_ctx.dice_type,
            raw_rolls=raw_rolls,
            selected_roll=selected_roll,
            modifiers=modifiers,
            total_score=total_score,
            target_number=roll_ctx.target_number,
            outcome=outcome,
            margin=margin,
            situation=roll_ctx.situation,
            relevant_stat=roll_ctx.relevant_stat,
            skill=roll_ctx.skill
        )
        
        self.result_history.append(result)
        self.is_active = False
        
        return result
    
    def get_roll_prompt(self) -> str:
        """
        Generate a prompt for the player about the roll.
        
        Returns:
            Formatted roll prompt
        """
        if not self.is_active or not self.active_roll:
            return ""
        
        roll = self.active_roll
        
        # Calculate expected modifiers for preview
        preview_mod = 0
        if roll.player_stats:
            preview_mod = roll.player_stats.get_total_modifier(roll.relevant_stat, roll.skill)
        
        prompt = f" **Roll Required:** {roll.situation}\n"
        prompt += f"  • Dice: {roll.dice_type.name}\n"
        prompt += f"  • Target: {roll.target_number}\n"
        prompt += f"  • Stat: {roll.relevant_stat.capitalize()}"
        
        if roll.skill:
            prompt += f" ({roll.skill.title()})"
        
        prompt += f"\n  • Your Modifier: {preview_mod:+d}"
        
        if roll.roll_type != RollType.NORMAL:
            prompt += f"\n  • Roll Type: {roll.roll_type.value.title()}"
        
        prompt += "\n\n💬 **Type 'roll' to roll the dice!**"
        
        return prompt
    
    def format_result_for_dm(self, result: RollResult) -> str:
        """
        Format roll result for DM/LLM to continue story.
        
        Args:
            result: The roll result
            
        Returns:
            Formatted message for storytelling
        """
        roll_ctx = self.active_roll
        
        message = f"**ROLL RESULT:**\n"
        message += f"{result.get_narrative_result()}\n\n"
        message += f"{result.get_roll_breakdown()}\n\n"
        
        # Add storytelling guidance for LLM
        if result.outcome == RollOutcome.CRITICAL_SUCCESS:
            message += "**📝 DM Note:** This is a CRITICAL SUCCESS! "
            if roll_ctx and roll_ctx.critical_success_text:
                message += roll_ctx.critical_success_text
            else:
                message += "The player succeeded spectacularly with ease. Describe how they accomplished this with exceptional skill, grace, or power. Add beneficial side effects or bonuses."
        
        elif result.outcome == RollOutcome.SUCCESS:
            message += "**📝 DM Note:** The player succeeded. "
            if roll_ctx and roll_ctx.success_text:
                message += roll_ctx.success_text
            else:
                message += "Describe their successful action naturally."
        
        elif result.outcome == RollOutcome.CRITICAL_FAILURE:
            message += "**📝 DM Note:** CRITICAL FAILURE! "
            if roll_ctx and roll_ctx.failure_text:
                message += "Not only did they fail, but something went catastrophically wrong. " + roll_ctx.failure_text
            else:
                message += "Not only did they fail, but something went catastrophically wrong. Add complications or consequences."
        
        else:  # Regular failure
            message += "**📝 DM Note:** The player failed. "
            if roll_ctx and roll_ctx.failure_text:
                message += roll_ctx.failure_text
            else:
                message += "Describe the failure and its consequences."
        
        return message
    
    def clear_roll(self):
        """Clear the active roll state"""
        self.active_roll = None
        self.is_active = False
    
    def get_statistics(self) -> Dict:
        """Get statistics about rolls"""
        total_rolls = len(self.result_history)
        
        if total_rolls == 0:
            return {
                'total_rolls': 0,
                'critical_successes': 0,
                'successes': 0,
                'failures': 0,
                'critical_failures': 0,
                'success_rate': 0,
                'average_roll': 0,
                'current_active': self.is_active
            }
        
        crit_success = sum(1 for r in self.result_history if r.outcome == RollOutcome.CRITICAL_SUCCESS)
        success = sum(1 for r in self.result_history if r.outcome == RollOutcome.SUCCESS)
        failure = sum(1 for r in self.result_history if r.outcome == RollOutcome.FAILURE)
        crit_failure = sum(1 for r in self.result_history if r.outcome == RollOutcome.CRITICAL_FAILURE)
        
        successful_rolls = crit_success + success
        avg_roll = sum(r.selected_roll for r in self.result_history) / total_rolls
        
        return {
            'total_rolls': total_rolls,
            'critical_successes': crit_success,
            'successes': success,
            'failures': failure,
            'critical_failures': crit_failure,
            'success_rate': successful_rolls / total_rolls if total_rolls > 0 else 0,
            'average_roll': round(avg_roll, 2),
            'current_active': self.is_active
        }
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary for storage"""
        return {
            'is_active': self.is_active,
            'active_roll': {
                'roll_id': self.active_roll.roll_id,
                'situation': self.active_roll.situation,
                'dice_type': self.active_roll.dice_type.value,
                'target_number': self.active_roll.target_number,
                'relevant_stat': self.active_roll.relevant_stat,
                'skill': self.active_roll.skill,
                'roll_type': self.active_roll.roll_type.value,
                'success_text': self.active_roll.success_text,
                'failure_text': self.active_roll.failure_text,
                'critical_success_text': self.active_roll.critical_success_text,
                'timestamp': self.active_roll.timestamp,
                'metadata': self.active_roll.metadata
            } if self.active_roll else None,
            'player_stats': {
                'strength': self.player_stats.strength,
                'dexterity': self.player_stats.dexterity,
                'constitution': self.player_stats.constitution,
                'intelligence': self.player_stats.intelligence,
                'wisdom': self.player_stats.wisdom,
                'charisma': self.player_stats.charisma,
                'proficiency_bonus': self.player_stats.proficiency_bonus,
                'proficient_skills': self.player_stats.proficient_skills,
                'equipment_bonus': self.player_stats.equipment_bonus,
                'temporary_bonus': self.player_stats.temporary_bonus
            },
            'roll_counter': self._roll_counter,
            'statistics': self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DiceRollState':
        """Deserialize from dictionary"""
        # Reconstruct player stats
        stats_data = data.get('player_stats', {})
        player_stats = PlayerStats(
            strength=stats_data.get('strength', 0),
            dexterity=stats_data.get('dexterity', 0),
            constitution=stats_data.get('constitution', 0),
            intelligence=stats_data.get('intelligence', 0),
            wisdom=stats_data.get('wisdom', 0),
            charisma=stats_data.get('charisma', 0),
            proficiency_bonus=stats_data.get('proficiency_bonus', 2),
            proficient_skills=stats_data.get('proficient_skills', []),
            equipment_bonus=stats_data.get('equipment_bonus', 0),
            temporary_bonus=stats_data.get('temporary_bonus', 0)
        )
        
        state = cls(player_stats=player_stats)
        state.is_active = data.get('is_active', False)
        state._roll_counter = data.get('roll_counter', 0)
        
        if data.get('active_roll'):
            r_data = data['active_roll']
            state.active_roll = RollContext(
                roll_id=r_data['roll_id'],
                situation=r_data['situation'],
                dice_type=DiceType(r_data['dice_type']),
                target_number=r_data['target_number'],
                relevant_stat=r_data['relevant_stat'],
                skill=r_data.get('skill'),
                roll_type=RollType(r_data['roll_type']),
                player_stats=player_stats,
                success_text=r_data.get('success_text'),
                failure_text=r_data.get('failure_text'),
                critical_success_text=r_data.get('critical_success_text'),
                timestamp=r_data.get('timestamp', ''),
                metadata=r_data.get('metadata', {})
            )
        
        return state


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def integrate_with_dm_response(
    dm_response: str,
    dice_state: DiceRollState,
    auto_detect: bool = True,
    auto_parse: bool = True
) -> Tuple[str, bool]:
    """
    Integrate dice rolling with DM response.
    
    Args:
        dm_response: DM's narration
        dice_state: DiceRollState instance
        auto_detect: Automatically detect roll requests
        auto_parse: Automatically parse roll parameters
        
    Returns:
        (formatted_response, is_roll_active)
    """
    is_roll = False
    
    if auto_detect and dice_state.detect_roll_request(dm_response):
        if auto_parse:
            # Parse parameters from DM response
            params = dice_state.parse_roll_request(dm_response)
            dice_state.activate_roll(
                situation=dm_response,
                dice_type=params['dice_type'],
                target_number=params['target_number'],
                relevant_stat=params['relevant_stat'],
                skill=params['skill'],
                roll_type=params['roll_type']
            )
        is_roll = True
    
    # Format response with prompt if roll is active
    if dice_state.is_active:
        roll_prompt = dice_state.get_roll_prompt()
        formatted = f"{dm_response}\n\n---\n{roll_prompt}"
        return formatted, True
    
    return dm_response, False


def handle_player_roll(
    player_input: str,
    dice_state: DiceRollState
) -> Tuple[bool, Optional[RollResult], Optional[str]]:
    """
    Handle player input for dice rolling.
    
    Args:
        player_input: Player's raw input
        dice_state: DiceRollState instance
        
    Returns:
        (should_roll, result_object, formatted_result_message)
    """
    if not dice_state.is_active:
        return False, None, None  # Not in roll state
    
    # Check if player wants to roll
    player_lower = player_input.lower().strip()
    if player_lower in ['roll', 'r', 'roll dice', 'roll it', 'lets roll', "let's roll"]:
        result = dice_state.execute_roll()
        formatted_message = dice_state.format_result_for_dm(result)
        return True, result, formatted_message
    
    return False, None, None


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DICE ROLL STATE - TEST SUITE")
    print("=" * 70)
    
    # Setup player stats
    player_stats = PlayerStats(
        strength=16,  # +3 modifier
        dexterity=14,  # +2 modifier
        constitution=12,  # +1 modifier
        intelligence=10,  # +0 modifier
        wisdom=8,  # -1 modifier
        charisma=13,  # +1 modifier
        proficiency_bonus=2,
        proficient_skills=['Athletics', 'Stealth', 'Perception']
    )
    
    dice_state = DiceRollState(player_stats=player_stats)
    
    # Test 1: Detect roll requests
    print("\n TEST 1: Roll Detection")
    print("-" * 70)
    
    test_dm_responses = [
        "You approach the cliff. Roll Athletics to climb it.",
        "The guard looks suspicious. Make a Deception check, DC 15.",
        "The poison takes effect! Roll a Constitution saving throw.",
        "You search the room thoroughly.",  # Not a roll
        "Attempt to leap across the chasm (Strength check, hard difficulty)",
    ]
    
    for dm_resp in test_dm_responses:
        detected = dice_state.detect_roll_request(dm_resp)
        print(f"\nDM: {dm_resp}")
        print(f"Roll Detected: {detected}")
    
    # Test 2: Parse roll parameters
    print("\n\n TEST 2: Parse Roll Parameters")
    print("-" * 70)
    
    dm_response = "You try to sneak past the guards. Roll Stealth, DC 18."
    parsed = dice_state.parse_roll_request(dm_response)
    
    print(f"\nDM: {dm_response}")
    print(f"Parsed Parameters:")
    for key, value in parsed.items():
        print(f"  {key}: {value}")
    
    # Test 3: Activate roll
    print("\n\n TEST 3: Activate Roll")
    print("-" * 70)
    
    roll_ctx = dice_state.activate_roll(
        situation="Climb the steep cliff face",
        dice_type=DiceType.D20,
        target_number=15,
        relevant_stat='strength',
        skill='athletics',
        roll_type=RollType.NORMAL,
        success_text="You scale the cliff with determination.",
        failure_text="You slip and must try another path.",
        critical_success_text="You climb with such ease that you find a hidden shortcut!"
    )
    
    print(f"\n✓ Roll activated:")
    print(f"  ID: {roll_ctx.roll_id}")
    print(f"  Dice: {roll_ctx.dice_type.name}")
    print(f"  Target: {roll_ctx.target_number}")
    print(f"  Stat: {roll_ctx.relevant_stat}")
    print(f"  Skill: {roll_ctx.skill}")
    print(f"\n{dice_state.get_roll_prompt()}")
    
    # Test 4: Execute roll
    print("\n\n TEST 4: Execute Roll")
    print("-" * 70)
    
    print("\nExecuting roll...")
    result = dice_state.execute_roll()
    
    print(f"\n{result.get_narrative_result()}")
    print(f"\n{result.get_roll_breakdown()}")
    print(f"\n{dice_state.format_result_for_dm(result)}")
    
    # Test 5: Multiple rolls with different outcomes
    print("\n\n TEST 5: Multiple Rolls")
    print("-" * 70)
    
    test_scenarios = [
        {
            'situation': 'Dodge the falling rocks',
            'stat': 'dexterity',
            'skill': 'acrobatics',
            'target': 12
        },
        {
            'situation': 'Recall ancient lore',
            'stat': 'intelligence',
            'skill': 'history',
            'target': 20
        },
        {
            'situation': 'Intimidate the bandit',
            'stat': 'charisma',
            'skill': 'intimidation',
            'target': 14
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['situation']} ---")
        dice_state.activate_roll(
            situation=scenario['situation'],
            target_number=scenario['target'],
            relevant_stat=scenario['stat'],
            skill=scenario.get('skill')
        )
        result = dice_state.execute_roll()
        print(result.get_narrative_result())
    
    # Test 6: Advantage/Disadvantage
    print("\n\n TEST 6: Advantage & Disadvantage")
    print("-" * 70)
    
    print("\nRolling with ADVANTAGE:")
    dice_state.activate_roll(
        situation="Lucky shot at the target",
        target_number=15,
        relevant_stat='dexterity',
        roll_type=RollType.ADVANTAGE
    )
    result_adv = dice_state.execute_roll()
    print(result_adv.get_roll_breakdown())
    
    print("\nRolling with DISADVANTAGE:")
    dice_state.activate_roll(
        situation="Firing while wounded",
        target_number=15,
        relevant_stat='dexterity',
        roll_type=RollType.DISADVANTAGE
    )
    result_dis = dice_state.execute_roll()
    print(result_dis.get_roll_breakdown())
    
    # Test 7: Integration helper
    print("\n\n TEST 7: Integration Helper")
    print("-" * 70)
    
    dice_state2 = DiceRollState(player_stats)
    dm_resp = "The door is locked. Roll a Strength check to break it down, DC 18."
    
    formatted, is_roll = integrate_with_dm_response(dm_resp, dice_state2)
    
    print("\nDM Response:")
    print(formatted)
    
    # Simulate player rolling
    should_roll, result, message = handle_player_roll("roll", dice_state2)
    if should_roll:
        print("\n" + message)
    
    # Test 8: Statistics
    print("\n\n TEST 8: Statistics")
    print("-" * 70)
    
    stats = dice_state.get_statistics()
    print("\nRoll Statistics:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2%}" if 'rate' in key else f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # Test 9: Serialization
    print("\n\n TEST 9: Serialization")
    print("-" * 70)
    
    dice_dict = dice_state.to_dict()
    print("\n✓ Serialized to dictionary")
    print(f"Active: {dice_dict['is_active']}")
    print(f"Total rolls: {dice_dict['statistics']['total_rolls']}")
    
    restored = DiceRollState.from_dict(dice_dict)
    print(f"\n✓ Restored from dictionary")
    print(f"Player Strength: {restored.player_stats.strength}")
    print(f"Proficient Skills: {restored.player_stats.proficient_skills}")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS COMPLETED")
    print("=" * 70)