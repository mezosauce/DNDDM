#!/usr/bin/env python3
"""
Story Package Flow - Step Definitions and Orchestration

Defines the 15-step flow pattern and orchestrates execution of each step.
Each story package (3.1 - 3.5) follows this same structured pattern.

The 15-step pattern cycles through 4 game states:
- Story State: DM narration, scene-setting, dialogue
- Questioning State: Binary Accept/Decline choices
- Dice Roll State: Skill checks, saving throws
- Combat State: Turn-based combat encounters
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any, Tuple, List
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from BackEnd.prompts import (
    init_story_prompt,
    pre_combat_prompt,
    post_combat_prompt,
    pre_diceroll_prompt,
    post_diceroll_prompt,
    pre_question_prompt,
    post_question_prompt,
    wrapup_prompt,

    active_phase_prompt
)

from BackEnd.component.GameState.story_state import StoryState
from .story_package_tracker import StoryPackageTracker
from BackEnd.component.GameState.dice_state import RollResult, RollOutcome


# ============================================================================
# STEP DEFINITIONS
# ============================================================================

STEP_DEFINITIONS = {
    1: {
        'state': 'story',
        'prompt_template': 'campaign_init',  # Uses campaign_init_prompt for first package, continuation for others
        'description': 'Setup scenery and surroundings',
        'requires_ai': True,
        'purpose': 'Establish the scene, location, and initial atmosphere',
        'expected_output': 'Rich narrative description of setting and situation',
        'next_state_trigger': None  # Auto-advance after narration
    },
    
    2: {
        'state': 'question',
        'prompt_template': 'pre_question',
        'description': 'Present Accept/Decline choice to player',
        'requires_ai': True,
        'purpose': 'Offer player a binary choice that branches the story',
        'expected_output': 'A clear question requiring Accept or Decline',
        'next_state_trigger': 'player_response'  # Wait for player to answer
    },
    
    3: {
        'state': 'story',
        'prompt_template': 'post_question',
        'description': 'Outcome dialogue based on player choice',
        'requires_ai': True,
        'purpose': 'Narrate consequences of player\'s Accept/Decline decision',
        'expected_output': 'Dialogue showing immediate results of choice',
        'next_state_trigger': None
    },
    
    4: {
        'state': 'story',
        'prompt_template': 'pre_diceroll',
        'description': 'Introduce dice roll situation',
        'requires_ai': True,
        'purpose': 'Set up a skill check or saving throw scenario',
        'expected_output': 'Narrative leading to a dice roll requirement',
        'next_state_trigger': 'dice_roll_setup'
    },
    
    5: {
        'state': 'dice',
        'prompt_template': None,  # Backend dice logic, no AI prompt
        'description': 'Execute dice roll with backend logic',
        'requires_ai': False,
        'purpose': 'Player rolls dice, calculate success/failure',
        'expected_output': 'Dice roll result with modifiers',
        'next_state_trigger': 'dice_roll_complete'
    },
    
    6: {
        'state': 'story',
        'prompt_template': 'pre_combat',
        'description': 'Pick balanced monster from INDEX.md, setup combat plot',
        'requires_ai': True,
        'purpose': 'Introduce combat encounter with narrative context',
        'expected_output': 'Combat setup with monster description',
        'next_state_trigger': 'combat_prep'
    },
    
    7: {
        'state': 'combat',
        'prompt_template': None,  # Backend combat logic, no AI prompt
        'description': 'Execute combat with backend logic',
        'requires_ai': False,
        'purpose': 'Run turn-based combat encounter',
        'expected_output': 'Combat results (victory/defeat)',
        'next_state_trigger': 'combat_complete'
    },
    
    8: {
        'state': 'story',
        'prompt_template': 'post_combat',
        'description': 'Analyze upgrades/equipment, dialogue about changes',
        'requires_ai': True,
        'purpose': 'Process combat aftermath, loot, experience',
        'expected_output': 'Post-combat narration with rewards/consequences',
        'next_state_trigger': None
    },
    
    9: {
        'state': 'story',
        'prompt_template': 'pre_diceroll',
        'description': 'Setup another dice roll situation',
        'requires_ai': True,
        'purpose': 'Introduce second skill check/saving throw',
        'expected_output': 'Narrative leading to dice roll',
        'next_state_trigger': 'dice_roll_setup'
    },
    
    10: {
        'state': 'dice',
        'prompt_template': None,  # Backend dice logic
        'description': 'Execute dice roll',
        'requires_ai': False,
        'purpose': 'Player rolls dice, calculate success/failure',
        'expected_output': 'Dice roll result with modifiers',
        'next_state_trigger': 'dice_roll_complete'
    },
    
    11: {
        'state': 'story',
        'prompt_template': 'conditional_evaluation',
        'description': 'Conditional evaluation: determine if second combat triggers',
        'requires_ai': True,
        'purpose': 'Evaluate dice roll result and decide story branch',
        'expected_output': 'Narrative that sets up conditional combat or resolution',
        'next_state_trigger': 'conditional_decision'  # Special trigger
    },
    
    12: {
        'state': 'story',
        'prompt_template': 'pre_combat',
        'description': 'Setup second combat encounter (conditional)',
        'requires_ai': True,
        'purpose': 'Introduce second combat if dice roll failed',
        'expected_output': 'Combat setup with monster description',
        'next_state_trigger': 'combat_prep',
        'conditional': True  # This step may be skipped
    },
    
    13: {
        'state': 'combat',
        'prompt_template': None,  # Backend combat logic
        'description': 'Execute second combat (conditional)',
        'requires_ai': False,
        'purpose': 'Run second combat encounter',
        'expected_output': 'Combat results',
        'next_state_trigger': 'combat_complete',
        'conditional': True
    },
    
    14: {
        'state': 'story',
        'prompt_template': 'post_combat',
        'description': 'Post-combat analysis (conditional)',
        'requires_ai': True,
        'purpose': 'Process second combat aftermath',
        'expected_output': 'Post-combat narration',
        'next_state_trigger': None,
        'conditional': True
    },
    
    15: {
        'state': 'story',
        'prompt_template': 'wrapup',
        'description': 'Wrap up story package',
        'requires_ai': True,
        'purpose': 'Conclude current package, transition to next',
        'expected_output': 'Closing narration, package conclusion',
        'next_state_trigger': 'package_complete'
    }
}


# ============================================================================
# STORY PACKAGE FLOW ORCHESTRATOR
# ============================================================================

class StoryPackageFlow:
    """
    Orchestrates the 15-step flow for story packages.
    
    This class coordinates between:
    - StoryPackageTracker (which step we're on)
    - StoryState (narrative context)
    - Step definitions (what to do at each step)
    - AI prompts (how to generate content)
    """
    
    def __init__(
        self, 
        tracker: StoryPackageTracker, 
        story_state: StoryState
    ):
        """
        Initialize flow orchestrator.
        
        Args:
            tracker: StoryPackageTracker managing progression
            story_state: StoryState managing narrative context
        """
        self.tracker = tracker
        self.story_state = story_state
    
    # ========================================================================
    # STEP QUERIES
    # ========================================================================
    
    def get_current_step_definition(self) -> Dict:
        """
        Get the definition for the current step.
        
        Returns:
            Dictionary with step configuration
        
        Example:
            >>> flow.tracker.current_step = 5
            >>> definition = flow.get_current_step_definition()
            >>> print(definition['state'])
            'dice'
        """
        return STEP_DEFINITIONS.get(
            self.tracker.current_step, 
            STEP_DEFINITIONS[1]  # Default to step 1 if invalid
        )
    
    def get_step_definition(self, step_number: int) -> Dict:
        """
        Get definition for a specific step.
        
        Args:
            step_number: Step number (1-15)
        
        Returns:
            Dictionary with step configuration
        """
        return STEP_DEFINITIONS.get(step_number, {})
    
    def is_current_step_conditional(self) -> bool:
        """
        Check if current step is part of conditional sequence.
        
        Returns:
            True if current step is 12, 13, or 14
        """
        definition = self.get_current_step_definition()
        return definition.get('conditional', False)
    
    # ========================================================================
    # AI PROMPT GENERATION
    # ========================================================================\

    def _format_character_combat_stats(self, characters: List[Dict]) -> str:
        """
        Format character stats for combat encounter balancing.
        
        Args:
            characters: List of character dictionaries
        
        Returns:
            Formatted string with character combat statistics
        """
        if not characters:
            return "No characters in party."
        
        lines = ["=== PARTY COMPOSITION & COMBAT STATS ==="]
        lines.append(f"Party Size: {len(characters)} character(s)\n")
        
        for char in characters:
            stats = char.get('stats', {})
            
            # Calculate derived stats
            level = char.get('level', 1)
            proficiency = 2 if level < 5 else (3 if level < 9 else (4 if level < 13 else (5 if level < 17 else 6)))
            
            # Calculate modifiers
            str_mod = (stats.get('strength', 10) - 10) // 2
            dex_mod = (stats.get('dexterity', 10) - 10) // 2
            con_mod = (stats.get('constitution', 10) - 10) // 2
            
            lines.append(f"Character: {char.get('name', 'Unknown')}")
            lines.append(f"  Class: {char.get('class', 'Unknown')} (Level {level})")
            lines.append(f"  HP: {char.get('hp', 0)}/{char.get('max_hp', 0)}")
            lines.append(f"  AC: {char.get('ac', 10)}")
            lines.append(f"  Proficiency Bonus: +{proficiency}")
            lines.append(f"  Stats:")
            lines.append(f"    STR: {stats.get('strength', 10)} (mod: {str_mod:+d})")
            lines.append(f"    DEX: {stats.get('dexterity', 10)} (mod: {dex_mod:+d})")
            lines.append(f"    CON: {stats.get('constitution', 10)} (mod: {con_mod:+d})")
            lines.append(f"    INT: {stats.get('intelligence', 10)} (mod: {(stats.get('intelligence', 10) - 10) // 2:+d})")
            lines.append(f"    WIS: {stats.get('wisdom', 10)} (mod: {(stats.get('wisdom', 10) - 10) // 2:+d})")
            lines.append(f"    CHA: {stats.get('charisma', 10)} (mod: {(stats.get('charisma', 10) - 10) // 2:+d})")
            
            # Estimate attack bonus (STR + proficiency for melee)
            attack_bonus = str_mod + proficiency
            lines.append(f"  Estimated Attack Bonus: +{attack_bonus}")
            
            # Estimate average damage per round (rough estimate)
            avg_weapon_damage = 4.5  # Average of 1d8
            avg_damage = avg_weapon_damage + str_mod
            lines.append(f"  Estimated Avg Damage/Round: {avg_damage:.1f}")
            lines.append("")
        
        # Calculate party averages
        avg_level = sum(c.get('level', 1) for c in characters) / len(characters)
        avg_hp = sum(c.get('hp', 0) for c in characters) / len(characters)
        avg_ac = sum(c.get('ac', 10) for c in characters) / len(characters)
        
        lines.append("=== PARTY AVERAGES ===")
        lines.append(f"Average Level: {avg_level:.1f}")
        lines.append(f"Average HP: {avg_hp:.1f}")
        lines.append(f"Average AC: {avg_ac:.1f}")
        lines.append("")
        
        # Add CR recommendations
        lines.append("=== MONSTER CR RECOMMENDATIONS ===")
        if avg_level <= 1:
            lines.append("Recommended CR Range: 0.125 - 0.5 (Deadly: 1)")
        elif avg_level <= 2:
            lines.append("Recommended CR Range: 0.25 - 1 (Deadly: 2)")
        elif avg_level <= 3:
            lines.append("Recommended CR Range: 0.5 - 2 (Deadly: 3)")
        elif avg_level <= 4:
            lines.append("Recommended CR Range: 1 - 3 (Deadly: 4)")
        else:
            lines.append(f"Recommended CR Range: {int(avg_level - 2)} - {int(avg_level + 1)} (Deadly: {int(avg_level + 2)})")
        
        lines.append("\nMultiple monsters: Divide party level by number of monsters for individual CR.")
        lines.append("Example: Level 3 party vs 3 monsters → Use CR 1 monsters")
        
        return "\n".join(lines)


    def generate_ai_prompt_for_step(
        self, 
        step: Optional[int] = None,
        context_data: Optional[Dict] = None
    ) -> str:
        """
        Generate the AI prompt for a specific step.
        
        Args:
            step: Step number (defaults to current step)
            context_data: Additional context (character data, campaign data, etc.)
        
        Returns:
            Formatted prompt string for AI/LLM
        
        Example:
            >>> prompt = flow.generate_ai_prompt_for_step(
            ...     step=1,
            ...     context_data={
            ...         'characters': character_list,
            ...         'campaign': campaign_data
            ...     }
            ... )
        """
        step_num = step or self.tracker.current_step
        definition = self.get_step_definition(step_num)
        
        if not definition.get('requires_ai'):
            return ""  # No AI prompt needed for backend-only steps
        
        # Get base prompt template
        prompt_template = definition.get('prompt_template')
        
        # Build context string
        context_parts = [
            f"=== STORY PACKAGE FLOW ===",
            f"Package: {self.tracker.get_package_display_name()}",
            f"Step: {step_num}/15 - {definition['description']}",
            f"State Type: {definition['state']}",
            f"",
            f"=== NARRATIVE CONTEXT ===",
            self.story_state.get_context_for_ai(),
            f""
        ]
        
        # Add context data if provided
        if context_data:
            context_parts.append(f"=== ADDITIONAL CONTEXT ===")
            
            if 'characters' in context_data:
                context_parts.append(f"Characters: {len(context_data['characters'])} in party")
            
            if 'campaign' in context_data:
                campaign = context_data['campaign']
                context_parts.append(f"Campaign: {campaign.get('name', 'Unknown')}")
                        
            if 'preparations' in context_data:
                context_parts.append(f"Quest Preparations Available: Yes")
                context_parts.append(f"\n=== QUEST PREPARATIONS ===")
                preparations = context_data['preparations']
                
                context_parts.append(str(preparations))  
                context_parts.append(f"")
            
            context_parts.append(f"")
        
        # Select appropriate prompt based on step
        prompt_parts = ["\n".join(context_parts)]
        
        if prompt_template == 'campaign_init':
            # First package or continuation
            if self.tracker.current_package == 1 and step_num == 1:
                prompt_parts.append(init_story_prompt)
                prompt_parts.append("\nThis is the beginning of the campaign. "
                                  "Establish the initial scene dramatically.")
            else:
                prompt_parts.append(init_story_prompt)
                prompt_parts.append(f"\nThis is package {self.tracker.get_package_display_name()}. "
                                  f"Continue the ongoing adventure with a new chapter.")
        
        elif prompt_template == 'pre_question':
            prompt_parts.append(pre_question_prompt)
            prompt_parts.append("\nPresent a meaningful binary choice (Accept/Decline) "
                              "that will affect the story direction.")
        
        elif prompt_template == 'post_question':
            prompt_parts.append(post_question_prompt)
            if self.story_state.last_question_answer:
                answer = self.story_state.last_question_answer
                prompt_parts.append(f"\nPlayer's decision: {answer.get('answer', 'Unknown')}")
                prompt_parts.append("Narrate the immediate consequences of this choice.")
        
        elif prompt_template == 'pre_diceroll':
            prompt_parts.append(pre_diceroll_prompt)
            if step_num == 4:
                prompt_parts.append("\nThis is the first dice roll of the package. "
                                  "Set up a meaningful skill check or saving throw.")
            else:  # step 9
                prompt_parts.append("\nThis is the second dice roll. "
                                  "It should be more challenging and consequential.")
        
        elif prompt_template == 'pre_combat':

            # Add detailed character combat stats
            if context_data.get('characters'):
                prompt_parts.append("\n" + self._format_character_combat_stats(context_data['characters']))
                prompt_parts.append("")
            
            # Add monster index for combat steps
            if context_data.get('monster_index'):
                prompt_parts.append("\n=== AVAILABLE MONSTERS ===")
                prompt_parts.append("\n" + context_data['monster_index'])
                prompt_parts.append("\n")

                prompt_parts.append("For level 1-2 parties, use CR 0.25 - 1 monsters.")
                prompt_parts.append("For level 3-4 parties, use CR 1 - 3 monsters.")
                prompt_parts.append("For level 5+ parties, use CR 3+ monsters.")
                prompt_parts.append("")
                prompt_parts.append(pre_combat_prompt)


            if step_num == 6:
                prompt_parts.append("\nThis is the first combat encounter. "
                                  "Choose an appropriate monster from INDEX.md "
                                  "and create engaging combat setup.")
            else:  # step 12
                prompt_parts.append("\nThis is the CONDITIONAL second combat. "
                                  "It triggers because the previous dice roll failed. "
                                  "This should be more difficult than the first combat.")
        
        elif prompt_template == 'post_combat':
            prompt_parts.append(post_combat_prompt)
            if self.story_state.last_combat_result:
                combat = self.story_state.last_combat_result
                prompt_parts.append(f"\nCombat completed. Narrate aftermath, "
                                  f"rewards, and character development.")
        
        elif prompt_template == 'conditional_evaluation':
            # Special prompt for step 11
            prompt_parts.append("\n=== CONDITIONAL EVALUATION ===")
            
            if self.story_state.last_dice_result:
                dice_result = self.story_state.last_dice_result
                prompt_parts.append(f"Previous dice roll result available.")
                prompt_parts.append("\nBased on the dice roll outcome, narrate what happens next.")
                prompt_parts.append("If the roll succeeded significantly, the party avoids further danger.")
                prompt_parts.append("If the roll failed, they face additional challenges (second combat).")
            else:
                prompt_parts.append("Evaluate the situation and determine if additional "
                                  "challenges (second combat) are warranted.")
        
        elif prompt_template == 'wrapup':
            prompt_parts.append(wrapup_prompt)
            prompt_parts.append(f"\nThis concludes Package {self.tracker.get_package_display_name()}.")
            
            if self.tracker.current_package < 5:
                prompt_parts.append("Provide a satisfying conclusion while setting up "
                                  "anticipation for the next chapter.")
            else:
                prompt_parts.append("This is the FINAL package. Provide an epic, "
                                  "satisfying conclusion to the entire campaign.")
        
        return "\n".join(prompt_parts)
    
    # ========================================================================
    # CONDITIONAL COMBAT LOGIC
    # ========================================================================
    
    def should_trigger_conditional_combat(
        self, 
        dice_result: Optional[RollResult] = None
    ) -> bool:
        """
        Determine if conditional combat (steps 12-14) should trigger.
        
        This is called at step 11 to decide the branch:
        - If dice roll succeeded: Skip to step 15
        - If dice roll failed: Continue to step 12 (combat)
        
        Args:
            dice_result: The result of the step 10 dice roll
        
        Returns:
            True if conditional combat should trigger, False to skip
        
        Logic:
            - Natural 1: Always trigger combat (critical failure)
            - Roll failed: Trigger combat
            - Roll succeeded: Skip combat
            - Roll succeeded by 10+: Definitely skip combat
        """
        if dice_result is None:
            # If no dice result available, check story_state
            if self.story_state.last_dice_result:
                # Try to infer from stored result
                # Default to not triggering if unclear
                return False
            # Default: don't trigger if no data
            return False
        
        # Check dice roll outcome
        if dice_result.outcome == RollOutcome.CRITICAL_FAILURE:
            # Natural 1: Always trigger combat
            return True
        
        elif dice_result.outcome in [RollOutcome.SUCCESS, RollOutcome.CRITICAL_SUCCESS]:
            # Roll succeeded: Skip combat
            return False
        
        else:  # RollOutcome.FAILURE
            # Roll failed: Trigger combat
            return True
    
    def evaluate_and_route_conditional(
        self, 
        dice_result: Optional[RollResult] = None
    ) -> Tuple[bool, str]:
        """
        Evaluate conditional at step 11 and route to correct next step.
        
        Args:
            dice_result: The dice roll result from step 10
        
        Returns:
            Tuple of (triggered_combat, routing_message)
        
        Example:
            >>> triggered, message = flow.evaluate_and_route_conditional(dice_result)
            >>> if triggered:
            ...     # Go to step 12
            >>> else:
            ...     # Jump to step 15
        """
        if self.tracker.current_step != 11:
            return False, "Not at conditional evaluation step"
        
        should_trigger = self.should_trigger_conditional_combat(dice_result)
        
        if should_trigger:
            # Trigger conditional combat
            self.tracker.trigger_conditional_combat()
            message = (
                "Dice roll failed - triggering conditional combat sequence. "
                f"Advancing to step {self.tracker.current_step} (second combat setup)."
            )
            return True, message
        
        else:
            # Skip conditional combat
            self.tracker.skip_conditional_combat()
            message = (
                "Dice roll succeeded - skipping conditional combat. "
                f"Jumping to step {self.tracker.current_step} (package wrap-up)."
            )
            return False, message
    
    # ========================================================================
    # EXECUTION FLOW
    # ========================================================================
    
    def execute_step(
        self, 
        player_input: Optional[str] = None,
        context_data: Optional[Dict] = None
    ) -> Dict:
        """
        Execute the current step in the flow.
        
        This is the main orchestration method. It:
        1. Gets current step definition
        2. Determines what action to take
        3. Updates story state appropriately
        4. Returns instructions for the route handler
        
        Args:
            player_input: Optional player input (for questions, dice rolls)
            context_data: Additional context (characters, campaign, etc.)
        
        Returns:
            Dictionary with execution results and routing instructions
        
        Example:
            >>> result = flow.execute_step(context_data={'characters': chars})
            >>> if result['requires_ai']:
            ...     prompt = result['ai_prompt']
            ...     # Call AI with prompt
            >>> if result['advance_step']:
            ...     flow.tracker.advance_step()
        """
        definition = self.get_current_step_definition()
        step_num = self.tracker.current_step
        state_type = definition['state']
        
        result = {
            'step': step_num,
            'state_type': state_type,
            'description': definition['description'],
            'requires_ai': definition.get('requires_ai', False),
            'requires_player_input': False,
            'advance_step': False,
            'route_to': None,
            'ai_prompt': None,
            'message': None,
            'conditional_decision': None
        }
        
        # Handle based on state type
        if state_type == 'story':
            # Story state: Generate AI prompt
            if definition.get('requires_ai'):
                result['ai_prompt'] = self.generate_ai_prompt_for_step(
                    step=step_num,
                    context_data=context_data
                )
                result['message'] = f"Generating narrative for step {step_num}"
            
            # Check if this is step 11 (conditional evaluation)
            if step_num == 11:
                result['requires_player_input'] = False
                result['conditional_decision'] = True
                result['message'] = "Conditional evaluation - check dice roll result"
            else:
                result['advance_step'] = True
        
        elif state_type == 'question':
            # Question state: Need player input
            result['requires_player_input'] = True
            result['route_to'] = 'question_state'
            result['ai_prompt'] = self.generate_ai_prompt_for_step(
                step=step_num,
                context_data=context_data
            )
            result['message'] = "Waiting for player Accept/Decline response"
        
        elif state_type == 'dice':
            # Dice state: Need player to roll
            result['requires_player_input'] = True
            result['route_to'] = 'dice_state'
            result['message'] = "Waiting for player dice roll"
        
        elif state_type == 'combat':
            # Combat state: Execute combat
            result['requires_player_input'] = True  # Combat is interactive
            result['route_to'] = 'combat_state'
            result['message'] = "Entering combat encounter"
        
        return result
    
    def get_next_action(self) -> Dict:
        """
        Get the next action required without executing.
        
        Useful for determining what page to show or what to expect next.
        
        Returns:
            Dictionary describing the next required action
        """
        definition = self.get_current_step_definition()
        
        return {
            'current_step': self.tracker.current_step,
            'state_type': definition['state'],
            'description': definition['description'],
            'requires_ai': definition.get('requires_ai', False),
            'requires_player_input': definition.get('state') in ['question', 'dice', 'combat'],
            'is_conditional': self.is_current_step_conditional(),
            'package': self.tracker.get_package_display_name(),
            'progress': self.tracker.get_package_progress_percentage()
        }
    
    # ========================================================================
    # UTILITY
    # ========================================================================
    
    def reset_to_step(self, step: int):
        """
        Reset tracker to a specific step (for testing/debugging).
        
        Args:
            step: Step number to reset to (1-15)
        """
        if step < 1 or step > 15:
            raise ValueError(f"Step must be between 1 and 15, got {step}")
        
        self.tracker.current_step = step
    
    def get_flow_summary(self) -> Dict:
        """
        Get a summary of the entire flow state.
        
        Returns:
            Dictionary with comprehensive flow information
        """
        return {
            'tracker': self.tracker.get_summary(),
            'story': self.story_state.get_summary(),
            'current_step': self.get_current_step_definition(),
            'next_action': self.get_next_action()
        }
    
    def __str__(self) -> str:
        """String representation."""
        return (
            f"StoryPackageFlow({self.tracker.get_current_position_string()}, "
            f"State: {self.get_current_step_definition()['state']})"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_all_story_steps() -> list:
    """Get list of all story state steps (non-interactive)."""
    return [
        step for step, definition in STEP_DEFINITIONS.items()
        if definition['state'] == 'story'
    ]


def get_all_interactive_steps() -> list:
    """Get list of all interactive steps (require player input)."""
    return [
        step for step, definition in STEP_DEFINITIONS.items()
        if definition['state'] in ['question', 'dice', 'combat']
    ]


def get_step_summary() -> Dict[int, str]:
    """Get a quick summary of all 15 steps."""
    return {
        step: f"{definition['state']:8s} - {definition['description']}"
        for step, definition in STEP_DEFINITIONS.items()
    }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("STORY PACKAGE FLOW - TEST SUITE")
    print("=" * 70)
    
    # Test 1: Step Definitions
    print("\n📚 TEST 1: Step Definitions")
    print("-" * 70)
    
    print("All 15 steps:")
    for step, desc in get_step_summary().items():
        conditional = " [CONDITIONAL]" if STEP_DEFINITIONS[step].get('conditional') else ""
        print(f"  {step:2d}. {desc}{conditional}")
    
    print(f"\nStory steps: {get_all_story_steps()}")
    print(f"Interactive steps: {get_all_interactive_steps()}")
    
    # Test 2: Create Flow
    print("\n\n📚 TEST 2: Create Flow Orchestrator")
    print("-" * 70)
    
    tracker = StoryPackageTracker(campaign_name="Test Campaign")
    story_state = StoryState(
        story_package_number=1,
        package_phase=1,
        current_location="Starting Village"
    )
    
    flow = StoryPackageFlow(tracker, story_state)
    
    print(f"✓ Created: {flow}")
    print(f"Current step definition:")
    definition = flow.get_current_step_definition()
    for key, value in definition.items():
        print(f"  {key}: {value}")
    
    # Test 3: AI Prompt Generation
    print("\n\n📚 TEST 3: AI Prompt Generation")
    print("-" * 70)
    
    # Test prompt for step 1
    print("Generating prompt for Step 1 (Campaign Init)...")
    prompt = flow.generate_ai_prompt_for_step(
        step=1,
        context_data={
            'characters': [{'name': 'Test Hero'}],
            'campaign': {'name': 'Test Campaign'}
        }
    )
    print(f"Prompt length: {len(prompt)} characters")
    print(f"First 200 chars:\n{prompt[:200]}...")
    
    # Test prompt for step 2
    print("\nGenerating prompt for Step 2 (Question)...")
    prompt = flow.generate_ai_prompt_for_step(step=2)
    print(f"Prompt length: {len(prompt)} characters")
    
    # Test 4: Execute Step
    print("\n\n📚 TEST 4: Execute Step")
    print("-" * 70)
    
    print(f"Current: {tracker.get_current_position_string()}")
    
    result = flow.execute_step(context_data={'characters': []})
    
    print(f"Execution result:")
    for key, value in result.items():
        if key != 'ai_prompt':  # Skip printing full prompt
            print(f"  {key}: {value}")
    
    # Test 5: Step Progression
    print("\n\n📚 TEST 5: Step Progression")
    print("-" * 70)
    
    # Progress through several steps
    for i in range(5):
        print(f"\nStep {tracker.current_step}:")
        definition = flow.get_current_step_definition()
        print(f"  State: {definition['state']}")
        print(f"  Description: {definition['description']}")
        
        next_action = flow.get_next_action()
        print(f"  Requires AI: {next_action['requires_ai']}")
        print(f"  Requires Input: {next_action['requires_player_input']}")
        
        tracker.advance_step()
    
    print(f"\nNow at: {tracker.get_current_position_string()}")
    
    # Test 6: Conditional Combat Logic
    print("\n\n📚 TEST 6: Conditional Combat Logic")
    print("-" * 70)
    
    # Create mock dice result
    from BackEnd.component.GameState.dice_state import (
        RollResult, DiceType, RollOutcome
    )
    
    # Test 6a: Success - Should skip combat
    print("Test 6a: Dice roll SUCCESS")
    success_result = RollResult(
        roll_id="TEST1",
        dice_type=DiceType.D20,
        raw_rolls=[15],
        selected_roll=15,
        modifiers={'Strength': 3},
        total_score=18,
        target_number=15,
        outcome=RollOutcome.SUCCESS,
        margin=3,
        situation="Test roll",
        relevant_stat="strength"
    )
    
    should_trigger = flow.should_trigger_conditional_combat(success_result)
    print(f"  Should trigger combat: {should_trigger}")
    print(f"  Expected: False")
    
    # Test 6b: Failure - Should trigger combat
    print("\nTest 6b: Dice roll FAILURE")
    failure_result = RollResult(
        roll_id="TEST2",
        dice_type=DiceType.D20,
        raw_rolls=[8],
        selected_roll=8,
        modifiers={'Strength': 2},
        total_score=10,
        target_number=15,
        outcome=RollOutcome.FAILURE,
        margin=-5,
        situation="Test roll",
        relevant_stat="strength"
    )
    
    should_trigger = flow.should_trigger_conditional_combat(failure_result)
    print(f"  Should trigger combat: {should_trigger}")
    print(f"  Expected: True")
    
    # Test 6c: Critical Failure - Always trigger
    print("\nTest 6c: Dice roll CRITICAL FAILURE")
    crit_fail_result = RollResult(
        roll_id="TEST3",
        dice_type=DiceType.D20,
        raw_rolls=[1],
        selected_roll=1,
        modifiers={'Strength': 5},
        total_score=6,
        target_number=15,
        outcome=RollOutcome.CRITICAL_FAILURE,
        margin=-9,
        situation="Test roll",
        relevant_stat="strength"
    )
    
    should_trigger = flow.should_trigger_conditional_combat(crit_fail_result)
    print(f"  Should trigger combat: {should_trigger}")
    print(f"  Expected: True")
    
    # Test 7: Evaluate and Route
    print("\n\n📚 TEST 7: Evaluate and Route Conditional")
    print("-" * 70)
    
    # Create fresh flow at step 11
    tracker2 = StoryPackageTracker(campaign_name="Conditional Test")
    tracker2.current_step = 11
    for i in range(1, 11):
        tracker2.completed_steps[1].append(i)
    
    story_state2 = StoryState(story_package_number=1, package_phase=11)
    flow2 = StoryPackageFlow(tracker2, story_state2)
    
    print(f"Starting at: {tracker2.get_current_position_string()}")
    
    # Route with success (skip)
    triggered, message = flow2.evaluate_and_route_conditional(success_result)
    print(f"\nWith SUCCESS result:")
    print(f"  Triggered combat: {triggered}")
    print(f"  Message: {message}")
    print(f"  New position: {tracker2.get_current_position_string()}")
    
    # Reset and test with failure (trigger)
    tracker2.current_step = 11
    triggered, message = flow2.evaluate_and_route_conditional(failure_result)
    print(f"\nWith FAILURE result:")
    print(f"  Triggered combat: {triggered}")
    print(f"  Message: {message}")
    print(f"  New position: {tracker2.get_current_position_string()}")
    
    # Test 8: Flow Summary
    print("\n\n📚 TEST 8: Flow Summary")
    print("-" * 70)
    
    summary = flow.get_flow_summary()
    print("Complete flow summary:")
    print(f"  Tracker: {summary['tracker']['current_position']}")
    print(f"  Story location: {summary['story']['location']}")
    print(f"  Current step state: {summary['current_step']['state']}")
    print(f"  Next action: {summary['next_action']['description']}")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS COMPLETED")
    print("=" * 70)