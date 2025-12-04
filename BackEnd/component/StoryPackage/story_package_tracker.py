#!/usr/bin/env python3
"""
Story Package Tracker - Progress Management for Phase 3

Manages progression through story packages (3.1 - 3.5) and the 15-step flow.
Each package follows the same structured pattern:
  1. Story State: Setup scenery
  2. Questioning State: Accept/Decline
  3. Story State: Outcome dialogue
  4. Story State: Introduce dice roll
  5. Dice Roll State: Execute roll
  6. Story State: Setup combat
  7. Combat State: Execute combat
  8. Story State: Post-combat analysis
  9. Story State: Setup another dice roll
  10. Dice Roll State: Execute roll
  11. Story State: Conditional evaluation
  12. Story State: Setup second combat (conditional)
  13. Combat State: Execute second combat (conditional)
  14. Story State: Post-combat analysis (conditional)
  15. Story State: Wrap up package
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json


@dataclass
class StoryPackageTracker:
    """
    Tracks progress through story packages and their 15-step flow.
    
    Manages 5 story packages (3.1, 3.2, 3.3, 3.4, 3.5), each with
    a standardized 15-step structure cycling through game states.
    """
    
    campaign_name: str
    
    # Current position
    current_package: int = 1  # 1-5 (represents packages 3.1 - 3.5)
    current_step: int = 1      # 1-15
    
    # Completion tracking
    completed_steps: Dict[int, List[int]] = field(default_factory=dict)
    # Format: {package_number: [completed_step_numbers]}
    # Example: {1: [1,2,3,4,5], 2: [1,2,3], ...}
    
    completed_packages: List[int] = field(default_factory=list)
    # List of fully completed package numbers
    
    # Step to GameState mapping (consistent across all packages)
    step_state_map: Dict[int, str] = field(default_factory=lambda: {
        1: 'story',      # Setup scenery and surroundings
        2: 'question',   # Accept/Decline choice
        3: 'story',      # Outcome dialogue
        4: 'story',      # Introduce dice roll situation
        5: 'dice',       # Execute dice roll
        6: 'story',      # Setup combat encounter
        7: 'combat',     # Execute combat
        8: 'story',      # Post-combat analysis
        9: 'story',      # Setup another dice roll
        10: 'dice',      # Execute second dice roll
        11: 'story',     # Conditional evaluation
        12: 'story',     # Setup second combat (conditional)
        13: 'combat',    # Execute second combat (conditional)
        14: 'story',     # Post-combat analysis (conditional)
        15: 'story'      # Wrap up story package
    })
    
    # Conditional combat tracking
    conditional_combat_triggered: Dict[int, bool] = field(default_factory=dict)
    # Format: {package_number: True/False}
    # Tracks whether steps 12-14 were executed in each package
    
    # Metadata
    campaign_complete: bool = False
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Step history (for analytics/debugging)
    step_history: List[Dict] = field(default_factory=list)
    # Logs every step transition with timestamp
    
    def __post_init__(self):
        """Initialize completed_steps dict for all packages"""
        if not self.completed_steps:
            self.completed_steps = {i: [] for i in range(1, 6)}
        
        if not self.conditional_combat_triggered:
            self.conditional_combat_triggered = {i: False for i in range(1, 6)}
    
    # ========================================================================
    # STATE TYPE QUERIES
    # ========================================================================
    
    def get_current_state_type(self) -> str:
        """
        Get the game state type for the current step.
        
        Returns:
            State type: 'story', 'question', 'dice', or 'combat'
        
        Example:
            >>> tracker.current_step = 5
            >>> tracker.get_current_state_type()
            'dice'
        """
        return self.step_state_map.get(self.current_step, 'story')
    
    def get_state_type_for_step(self, step: int) -> str:
        """
        Get the game state type for a specific step number.
        
        Args:
            step: Step number (1-15)
        
        Returns:
            State type for that step
        """
        return self.step_state_map.get(step, 'story')
    
    def is_conditional_step(self, step: int) -> bool:
        """
        Check if a step is part of the conditional combat sequence.
        
        Args:
            step: Step number to check
        
        Returns:
            True if step is 12, 13, or 14 (conditional combat sequence)
        """
        return step in [12, 13, 14]
    
    


    # ========================================================================
    # STEP PROGRESSION
    # ========================================================================
    
    def advance_step(self) -> bool:
        """
        Advance to the next step in the current package.
        
        Returns:
            True if the package is now complete, False otherwise
        
        Example:
            >>> tracker.current_step = 10
            >>> package_complete = tracker.advance_step()
            >>> print(tracker.current_step)
            11
        """
         # Defensive: Ensure completed_steps has entry for current package
        if self.current_package not in self.completed_steps:
            self.completed_steps[self.current_package] = []
        
        # Defensive: Ensure conditional_combat_triggered has entry
        if self.current_package not in self.conditional_combat_triggered:
            self.conditional_combat_triggered[self.current_package] = False
        
        # Mark current step as completed
        if self.current_step not in self.completed_steps[self.current_package]:
            self.completed_steps[self.current_package].append(self.current_step)
        # Log step completion
        self._log_step_transition(
            from_step=self.current_step,
            to_step=self.current_step + 1,
            action="advance"
        )
        
        # Advance to next step
        self.current_step += 1
        self.last_updated = datetime.now().isoformat()
        
        # Check if package is complete
        if self.current_step > 15:
            return self._complete_current_package()
        
        return False
    
    def skip_conditional_combat(self):
        """
        Skip the conditional combat sequence (steps 12-14).
        
        Called from step 11 when the dice roll succeeds and
        conditional combat is not triggered.
        
        Jumps directly from step 11 to step 15.
        
        Example:
            >>> tracker.current_step = 11
            >>> tracker.skip_conditional_combat()
            >>> print(tracker.current_step)
            15
        """
        if self.current_step != 11:
            raise ValueError(
                f"Can only skip conditional combat from step 11. "
                f"Current step: {self.current_step}"
            )
        
        # Mark step 11 as completed
        if 11 not in self.completed_steps[self.current_package]:
            self.completed_steps[self.current_package].append(11)
        
        # Log the skip
        self._log_step_transition(
            from_step=11,
            to_step=15,
            action="skip_conditional_combat"
        )
        
        # Mark that conditional combat was NOT triggered
        self.conditional_combat_triggered[self.current_package] = False
        
        # Jump to step 15
        self.current_step = 15
        self.last_updated = datetime.now().isoformat()
    
    def trigger_conditional_combat(self):
        """
        Trigger the conditional combat sequence (steps 12-14).
        
        Called from step 11 when the dice roll fails and
        conditional combat IS triggered.
        
        Advances normally from step 11 to step 12.
        
        Example:
            >>> tracker.current_step = 11
            >>> tracker.trigger_conditional_combat()
            >>> print(tracker.current_step)
            12
        """
        if self.current_step != 11:
            raise ValueError(
                f"Can only trigger conditional combat from step 11. "
                f"Current step: {self.current_step}"
            )
        
        # Mark that conditional combat WAS triggered
        self.conditional_combat_triggered[self.current_package] = True
        
        # Log the trigger
        self._log_step_transition(
            from_step=11,
            to_step=12,
            action="trigger_conditional_combat"
        )
        
        # Advance normally to step 12
        self.advance_step()
    
    def _complete_current_package(self) -> bool:
        """
        Mark the current package as complete and prepare for next package.
        
        Returns:
            True (always, to indicate package completion)
        """
        # Mark package as complete
        if self.current_package not in self.completed_packages:
            self.completed_packages.append(self.current_package)
        
        # Log package completion
        self._log_step_transition(
            from_step=15,
            to_step=None,
            action="complete_package"
        )
        
        # Check if entire campaign is complete
        if self.current_package >= 5:
            self.campaign_complete = True
        
        self.last_updated = datetime.now().isoformat()
        
        return True
    
    def start_package(self, package_number: int):
        """
        Start a specific package.
        
        Args:
            package_number: Package number (1-5) to start
        """
        if package_number < 1 or package_number > 5:
            raise ValueError(f"Package number must be between 1 and 5, got {package_number}")
        
        self.current_package = package_number
        self.current_step = 1
        
        # Ensure completed_steps entry exists for this package
        if package_number not in self.completed_steps:
            self.completed_steps[package_number] = []
        
        # Ensure conditional combat tracking exists
        if package_number not in self.conditional_combat_triggered:
            self.conditional_combat_triggered[package_number] = False
        
        self.last_updated = datetime.now().isoformat()

        
    def start_next_package(self):
        """
        Start the next story package.
        
        Increments package number and resets to step 1.
        Should be called after completing a package.
        
        Example:
            >>> tracker.current_package = 1
            >>> tracker.start_next_package()
            >>> print(tracker.current_package, tracker.current_step)
            2 1
        
        Raises:
            ValueError: If campaign is already complete
        """
        if self.campaign_complete:
            raise ValueError("Campaign is already complete")
        
        if self.current_package >= 5:
            raise ValueError("Already on final package (3.5)")
        
        # Advance to next package
        old_package = self.current_package
        self.current_package += 1
        self.current_step = 1
        
        # Log package start
        self._log_step_transition(
            from_step=None,
            to_step=1,
            action=f"start_package_{self.current_package}"
        )
        
        self.last_updated = datetime.now().isoformat()
    
    # ========================================================================
    # COMPLETION STATUS QUERIES
    # ========================================================================
    
    def is_package_complete(self, package_number: Optional[int] = None) -> bool:
        """
        Check if a package is complete.
        
        Args:
            package_number: Package to check (1-5). If None, checks current package.
        
        Returns:
            True if the package is complete
        """
        pkg = package_number or self.current_package
        return pkg in self.completed_packages
    
    def is_step_complete(self, step: int, package_number: Optional[int] = None) -> bool:
        """
        Check if a specific step is complete.
        
        Args:
            step: Step number (1-15)
            package_number: Package to check. If None, checks current package.
        
        Returns:
            True if the step is complete
        """
        pkg = package_number or self.current_package
        return step in self.completed_steps.get(pkg, [])
    
    def is_campaign_complete(self) -> bool:
        """
        Check if the entire campaign (all 5 packages) is complete.
        
        Returns:
            True if all 5 packages are complete
        """
        return self.campaign_complete and len(self.completed_packages) >= 5
    
    def get_completed_step_count(self, package_number: Optional[int] = None) -> int:
        """
        Get the number of completed steps in a package.
        
        Args:
            package_number: Package to check. If None, checks current package.
        
        Returns:
            Number of completed steps
        """
        pkg = package_number or self.current_package
        return len(self.completed_steps.get(pkg, []))
    
    # ========================================================================
    # PROGRESS METRICS
    # ========================================================================
    
    def get_progress_percentage(self) -> float:
        """
        Calculate overall campaign progress as a percentage.
        
        Total possible steps: 5 packages × 15 steps = 75 steps
        (Note: Conditional combat may reduce actual steps)
        
        Returns:
            Progress percentage (0.0 to 100.0)
        
        Example:
            >>> tracker.current_package = 2
            >>> # Package 1 complete (15 steps), Package 2 at step 5
            >>> tracker.get_progress_percentage()
            26.67  # (15 + 5) / 75 * 100
        """
        total_completed_steps = sum(
            len(steps) for steps in self.completed_steps.values()
        )
        
        # Total possible steps: 5 packages × 15 steps
        total_steps = 5 * 15
        
        return (total_completed_steps / total_steps) * 100.0
    
    def get_package_progress_percentage(self, package_number: Optional[int] = None) -> float:
        """
        Calculate progress percentage for a specific package.
        
        Args:
            package_number: Package to check. If None, checks current package.
        
        Returns:
            Progress percentage for that package (0.0 to 100.0)
        """
        pkg = package_number or self.current_package
        completed = len(self.completed_steps.get(pkg, []))
        
        # Each package has 15 steps max
        return (completed / 15) * 100.0
    
    def get_remaining_steps_in_package(self) -> int:
        """
        Get the number of remaining steps in the current package.
        
        Returns:
            Number of steps remaining (including current step)
        """
        return 16 - self.current_step  # 16 because current_step is 1-indexed
    
    def get_remaining_packages(self) -> int:
        """
        Get the number of remaining packages (including current).
        
        Returns:
            Number of packages remaining
        """
        return 6 - self.current_package  # 6 because we count the current one
    
    # ========================================================================
    # DISPLAY HELPERS
    # ========================================================================
    
    def get_package_display_name(self, package_number: Optional[int] = None) -> str:
        """
        Get the display name for a package (e.g., "3.1", "3.2").
        
        Args:
            package_number: Package number (1-5). If None, uses current package.
        
        Returns:
            Display name like "3.1", "3.2", etc.
        """
        pkg = package_number or self.current_package
        return f"3.{pkg}"
    
    def get_current_position_string(self) -> str:
        """
        Get a human-readable string of current position.
        
        Returns:
            String like "Package 3.2, Step 7/15"
        
        Example:
            >>> tracker.current_package = 2
            >>> tracker.current_step = 7
            >>> tracker.get_current_position_string()
            'Package 3.2, Step 7/15'
        """
        return (
            f"Package {self.get_package_display_name()}, "
            f"Step {self.current_step}/15"
        )
    
    def get_summary(self) -> Dict:
        """
        Get a comprehensive summary of tracker state.
        
        Returns:
            Dictionary with progress information
        """
        return {
            "campaign_name": self.campaign_name,
            "current_position": self.get_current_position_string(),
            "current_package": self.current_package,
            "current_step": self.current_step,
            "current_state_type": self.get_current_state_type(),
            "package_progress": f"{self.get_package_progress_percentage():.1f}%",
            "overall_progress": f"{self.get_progress_percentage():.1f}%",
            "completed_packages": len(self.completed_packages),
            "remaining_packages": self.get_remaining_packages(),
            "remaining_steps_in_package": self.get_remaining_steps_in_package(),
            "campaign_complete": self.campaign_complete,
            "conditional_combat_this_package": self.conditional_combat_triggered.get(
                self.current_package, False
            )
        }
    
    # ========================================================================
    # STEP HISTORY LOGGING
    # ========================================================================
    
    def _log_step_transition(
        self, 
        from_step: Optional[int], 
        to_step: Optional[int],
        action: str
    ):
        """
        Log a step transition to history.
        
        Args:
            from_step: Step we're leaving (None if starting)
            to_step: Step we're entering (None if completing)
            action: Description of the action taken
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "package": self.current_package,
            "from_step": from_step,
            "to_step": to_step,
            "action": action
        }
        
        self.step_history.append(entry)
    
    def get_step_history(self, package_number: Optional[int] = None) -> List[Dict]:
        """
        Get step history for a specific package.
        
        Args:
            package_number: Package to get history for. If None, returns all history.
        
        Returns:
            List of history entries
        """
        if package_number is None:
            return self.step_history
        
        return [
            entry for entry in self.step_history
            if entry["package"] == package_number
        ]
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self) -> Dict:
        """
        Convert tracker to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "campaign_name": self.campaign_name,
            "current_package": self.current_package,
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "completed_packages": self.completed_packages,
            "step_state_map": self.step_state_map,
            "conditional_combat_triggered": self.conditional_combat_triggered,
            "campaign_complete": self.campaign_complete,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
            "step_history": self.step_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StoryPackageTracker':
        """
        Create tracker from dictionary.
        
        Args:
            data: Dictionary with tracker data
        
        Returns:
            StoryPackageTracker instance
        """
        completed_steps_raw = data.get("completed_steps", {})
        completed_steps = {}
        for key, value in completed_steps_raw.items():
            completed_steps[int(key)] = value
        # Fill in missing keys
        for i in range(1, 6):
            if i not in completed_steps:
                completed_steps[i] = []
        
        # Ensure conditional_combat_triggered has all package keys (1-5) as integers
        conditional_raw = data.get("conditional_combat_triggered", {})
        conditional_combat_triggered = {}
        for key, value in conditional_raw.items():
            conditional_combat_triggered[int(key)] = value
        # Fill in missing keys
        for i in range(1, 6):
            if i not in conditional_combat_triggered:
                conditional_combat_triggered[i] = False
        
        # Ensure step_state_map has integer keys
        step_state_map_raw = data.get("step_state_map", {})
        step_state_map = {}
        
        if step_state_map_raw:
            # Convert string keys to integers
            for key, value in step_state_map_raw.items():
                step_state_map[int(key)] = value
        
        # If empty or incomplete, use default mapping
        if not step_state_map or len(step_state_map) < 15:
            step_state_map = {
                1: 'story', 2: 'question', 3: 'story', 4: 'story', 5: 'dice',
                6: 'story', 7: 'combat', 8: 'story', 9: 'story', 10: 'dice',
                11: 'story', 12: 'story', 13: 'combat', 14: 'story', 15: 'story'
            }

        return cls(
            campaign_name=data["campaign_name"],
            current_package=data.get("current_package", 1),
            current_step=data.get("current_step", 1),
            completed_steps=completed_steps,  
            completed_packages=data.get("completed_packages", []),
            step_state_map=step_state_map,  
            conditional_combat_triggered=conditional_combat_triggered,  
            campaign_complete=data.get("campaign_complete", False),
            started_at=data.get("started_at", datetime.now().isoformat()),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
            step_history=data.get("step_history", [])
        )
    
    def save_to_file(self, filepath: str):
        """
        Save tracker to JSON file.
        
        Args:
            filepath: Path to save file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'StoryPackageTracker':
        """
        Load tracker from JSON file.
        
        Args:
            filepath: Path to load from
        
        Returns:
            StoryPackageTracker instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    # ========================================================================
    # UTILITY
    # ========================================================================
    
    def __str__(self) -> str:
        """String representation of tracker."""
        return (
            f"StoryPackageTracker({self.campaign_name}: "
            f"Package {self.get_package_display_name()}, "
            f"Step {self.current_step}/15, "
            f"{self.get_progress_percentage():.1f}% complete)"
        )


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("STORY PACKAGE TRACKER - TEST SUITE")
    print("=" * 70)
    
    # Test 1: Create tracker
    print("\n📦 TEST 1: Create Tracker")
    print("-" * 70)
    
    tracker = StoryPackageTracker(campaign_name="Test Campaign")
    
    print(f"✓ Created: {tracker}")
    print(f"Display name: {tracker.get_package_display_name()}")
    print(f"Position: {tracker.get_current_position_string()}")
    
    summary = tracker.get_summary()
    print(f"\nSummary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Test 2: State type queries
    print("\n\n📦 TEST 2: State Type Queries")
    print("-" * 70)
    
    for step in [1, 2, 5, 7, 10, 11, 13, 15]:
        state_type = tracker.get_state_type_for_step(step)
        is_conditional = tracker.is_conditional_step(step)
        print(f"Step {step:2d}: {state_type:8s} | Conditional: {is_conditional}")
    
    # Test 3: Normal progression
    print("\n\n📦 TEST 3: Normal Step Progression")
    print("-" * 70)
    
    print(f"Starting at: {tracker.get_current_position_string()}")
    
    # Advance through first few steps
    for i in range(5):
        print(f"\nStep {tracker.current_step} ({tracker.get_current_state_type()})")
        package_complete = tracker.advance_step()
        print(f"  → Advanced to step {tracker.current_step}")
        print(f"  Completed steps: {tracker.completed_steps[1]}")
        if package_complete:
            print("  ✓ Package complete!")
    
    print(f"\nProgress: {tracker.get_package_progress_percentage():.1f}%")
    
    # Test 4: Conditional combat - Skip
    print("\n\n📦 TEST 4: Conditional Combat - Skip Path")
    print("-" * 70)
    
    tracker2 = StoryPackageTracker(campaign_name="Skip Test")
    
    # Fast forward to step 11
    tracker2.current_step = 11
    for i in range(1, 11):
        tracker2.completed_steps[1].append(i)
    
    print(f"At step {tracker2.current_step}")
    print(f"Current state: {tracker2.get_current_state_type()}")
    
    # Skip conditional combat
    tracker2.skip_conditional_combat()
    
    print(f"After skip:")
    print(f"  Current step: {tracker2.current_step}")
    print(f"  Conditional combat triggered: {tracker2.conditional_combat_triggered[1]}")
    print(f"  Completed steps: {sorted(tracker2.completed_steps[1])}")
    
    # Test 5: Conditional combat - Trigger
    print("\n\n📦 TEST 5: Conditional Combat - Trigger Path")
    print("-" * 70)
    
    tracker3 = StoryPackageTracker(campaign_name="Trigger Test")
    
    # Fast forward to step 11
    tracker3.current_step = 11
    for i in range(1, 11):
        tracker3.completed_steps[1].append(i)
    
    print(f"At step {tracker3.current_step}")
    
    # Trigger conditional combat
    tracker3.trigger_conditional_combat()
    
    print(f"After trigger:")
    print(f"  Current step: {tracker3.current_step}")
    print(f"  Conditional combat triggered: {tracker3.conditional_combat_triggered[1]}")
    
    # Continue through conditional steps
    print(f"\nProgressing through conditional combat:")
    for _ in range(4):  # Steps 12, 13, 14, 15
        print(f"  Step {tracker3.current_step} ({tracker3.get_current_state_type()})")
        package_complete = tracker3.advance_step()
        if package_complete:
            print(f"  ✓ Package complete!")
            break
    
    # Test 6: Complete package and start next
    print("\n\n📦 TEST 6: Complete Package and Start Next")
    print("-" * 70)
    
    tracker4 = StoryPackageTracker(campaign_name="Package Test")
    
    # Fast forward to step 15
    tracker4.current_step = 15
    for i in range(1, 15):
        tracker4.completed_steps[1].append(i)
    
    print(f"At: {tracker4.get_current_position_string()}")
    print(f"Package complete: {tracker4.is_package_complete(1)}")
    
    # Complete the package
    package_complete = tracker4.advance_step()
    print(f"\nAfter advancing from step 15:")
    print(f"  Package complete: {package_complete}")
    print(f"  Completed packages: {tracker4.completed_packages}")
    print(f"  Current step: {tracker4.current_step}")
    
    # Start next package
    tracker4.start_next_package()
    print(f"\nAfter starting next package:")
    print(f"  Position: {tracker4.get_current_position_string()}")
    print(f"  Package progress: {tracker4.get_package_progress_percentage(2):.1f}%")
    
    # Test 7: Progress metrics
    print("\n\n📦 TEST 7: Progress Metrics")
    print("-" * 70)
    
    # Simulate progress
    test_tracker = StoryPackageTracker(campaign_name="Progress Test")
    
    # Complete package 1
    test_tracker.completed_steps[1] = list(range(1, 16))
    test_tracker.completed_packages.append(1)
    
    # Partially complete package 2
    test_tracker.current_package = 2
    test_tracker.current_step = 8
    test_tracker.completed_steps[2] = list(range(1, 8))
    
    print(f"Position: {test_tracker.get_current_position_string()}")
    print(f"Overall progress: {test_tracker.get_progress_percentage():.1f}%")
    print(f"Package 1 progress: {test_tracker.get_package_progress_percentage(1):.1f}%")
    print(f"Package 2 progress: {test_tracker.get_package_progress_percentage(2):.1f}%")
    print(f"Remaining packages: {test_tracker.get_remaining_packages()}")
    print(f"Remaining steps in package: {test_tracker.get_remaining_steps_in_package()}")
    
    # Test 8: Campaign completion
    print("\n\n📦 TEST 8: Campaign Completion")
    print("-" * 70)
    
    final_tracker = StoryPackageTracker(campaign_name="Final Test")
    
    # Complete all 5 packages
    for pkg in range(1, 6):
        final_tracker.completed_steps[pkg] = list(range(1, 16))
        final_tracker.completed_packages.append(pkg)
    
    final_tracker.current_package = 5
    final_tracker.current_step = 15
    
    print(f"Before final step:")
    print(f"  Campaign complete: {final_tracker.is_campaign_complete()}")
    
    # Advance past final step
    final_tracker.advance_step()
    
    print(f"\nAfter final step:")
    print(f"  Campaign complete: {final_tracker.is_campaign_complete()}")
    print(f"  Overall progress: {final_tracker.get_progress_percentage():.1f}%")
    print(f"  Completed packages: {final_tracker.completed_packages}")
    
    # Test 9: Serialization
    print("\n\n📦 TEST 9: Serialization")
    print("-" * 70)
    
    # Create tracker with some progress
    save_tracker = StoryPackageTracker(campaign_name="Save Test")
    save_tracker.current_package = 2
    save_tracker.current_step = 5
    save_tracker.completed_steps[1] = list(range(1, 16))
    save_tracker.completed_packages.append(1)
    save_tracker.completed_steps[2] = list(range(1, 5))
    save_tracker.conditional_combat_triggered[1] = True
    
    # To dict
    tracker_dict = save_tracker.to_dict()
    print(f"✓ Serialized to dict")
    print(f"  Keys: {list(tracker_dict.keys())}")
    
    # From dict
    restored = StoryPackageTracker.from_dict(tracker_dict)
    print(f"✓ Restored from dict")
    print(f"  Campaign: {restored.campaign_name}")
    print(f"  Position: {restored.get_current_position_string()}")
    print(f"  Completed packages: {restored.completed_packages}")
    print(f"  Progress: {restored.get_progress_percentage():.1f}%")
    
    # Test file save/load
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "tracker.json")
        
        save_tracker.save_to_file(filepath)
        print(f"✓ Saved to file: {filepath}")
        
        loaded = StoryPackageTracker.load_from_file(filepath)
        print(f"✓ Loaded from file")
        print(f"  Position: {loaded.get_current_position_string()}")
    
    # Test 10: Step history
    print("\n\n📦 TEST 10: Step History")
    print("-" * 70)
    
    history_tracker = StoryPackageTracker(campaign_name="History Test")
    
    # Make some moves
    history_tracker.advance_step()  # 1 → 2
    history_tracker.advance_step()  # 2 → 3
    history_tracker.advance_step()  # 3 → 4
    
    # Jump to 11 and skip
    history_tracker.current_step = 11
    history_tracker.skip_conditional_combat()  # 11 → 15
    
    print(f"Step history:")
    for entry in history_tracker.step_history:
        print(f"  {entry['action']:25s} | "
              f"Package {entry['package']} | "
              f"Step {entry.get('from_step', '?')} → {entry.get('to_step', '?')}")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS COMPLETED")
    print("=" * 70)