#!/usr/bin/env python3
"""
Story State:
o	Input:
    	Characters.Json
    	Campaign.Json
    	Session Notes
    	If {Game_State_INIT}
        •	INIT Story Prompt
    	If {Next_Game_State == Combat State}: 
        •	SRD_Cycle/Monsters.Index.MD
        •	Combat Prep Prompt
    	If {Next_Game_State == Questoning State}:
        •	Questioning State Prompt
    	If {Next_Game_State == Dice Roll State}:
        •	Dice Roll Situation Prompt
    	If {Last_Game_State == Combat State}:
        •	Post Combat Prompt
    	If {Last_Game_State == Questioning State}:
        •	Post Questioning Prompt
    	If {Last_Game_State == Dice Roll State}:
        •	Post Dice Roll Prompt
    	If {Next_Game_State == END:
        •	Story Wrap up Prompt
o	Output:
    	If {Game_State_INIT} 
        •	INIT Story Dialogue
    	If {Next_Game_State == Combat State}:
        •	Give Chosen <Monster> Dialogue 
        •	Provide <Monster> Base Stats <Scaled>
    	If {Next_Game_State == Questoning State}:
        •	Provide <Situation> with only options to either Accept/ Decline
    	If {Next_Game_State == Dice Roll State}:
        •	Provide <Situation> Dialogue
        •	Provide type of Dice the Player has to roll
    	If {Last_Game_State == Combat State}:
        •	Post Combat Dialogue 
    	If {Last_Game_State == Questioning State}:
        •	Post Questioning Dialogue
    	If {Last_Game_State == Dice Roll State}:
        •	Post Dice Roll Dialogue
    	If {Next_Game_State == END:
        •	Story Wrap up Dialogue

Story State - Narrative State Management for D&D Campaign

Manages narrative state and story progression. Tracks WHERE the story is,
WHAT is happening narratively, and HOW the story is progressing.

This class does NOT generate content - that's handled by the Story Package.
It only tracks state and context for story generation.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
import sys
from pathlib import Path

# Import prompt templates
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from BackEnd.prompts import (
    init_story_prompt,
    pre_combat_prompt,
    pre_diceroll_prompt,
    pre_question_prompt,
    post_combat_prompt,
    post_diceroll_prompt,
    post_question_prompt,
    warpup_prompt
)


@dataclass
class StoryState:
    """
    Manages narrative state and story progression for D&D campaign.
    
    This class is responsible for tracking WHERE the story is,
    WHAT is happening narratively, and HOW the story is progressing.
    It does NOT generate content - that's handled by the Story package.
    """
    
    # ========================================================================
    # STORY PROGRESSION
    # ========================================================================
    story_package_number: int = 1  # 1-5 for main campaign
    is_side_quest: bool = False
    main_campaign_complete: bool = False
    package_phase: int = 1  # Which step in the 15-step flow (1-15)
    
    # ========================================================================
    # CURRENT NARRATIVE CONTEXT
    # ========================================================================
    current_location: str = ""
    current_scene: str = ""
    narrative_context: str = ""  # What's happening right now
    
    # ========================================================================
    # ACTIVE ELEMENTS
    # ========================================================================
    active_npcs: List[str] = field(default_factory=list)
    plot_points: List[str] = field(default_factory=list)
    resolved_plot_points: List[str] = field(default_factory=list)
    items_in_scene: List[str] = field(default_factory=list)
    
    # ========================================================================
    # STATE TRANSITION TRACKING
    # ========================================================================
    last_game_state: Optional[str] = None  # "init", "combat", "dice", "question"
    next_game_state: Optional[str] = None  # "combat", "dice", "question", "end", "story"
    
    # ========================================================================
    # STORY HISTORY
    # ========================================================================
    story_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # ========================================================================
    # SESSION CONTEXT
    # ========================================================================
    session_notes_reference: Optional[str] = None
    key_session_events: List[str] = field(default_factory=list)
    player_decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    # ========================================================================
    # METADATA
    # ========================================================================
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # ========================================================================
    # COMBAT-RELATED CONTEXT (for pre/post combat story generation)
    # ========================================================================
    pending_monster: Optional[Dict[str, Any]] = None  # Monster being prepared
    last_combat_result: Optional[Dict[str, Any]] = None  # Result of last combat
    
    # ========================================================================
    # DICE-RELATED CONTEXT (for pre/post dice roll story generation)
    # ========================================================================
    pending_dice_situation: Optional[Dict[str, Any]] = None  # Dice roll about
    last_dice_result: Optional[Dict[str, Any]] = None  # Result of last dice roll
    
    # ========================================================================
    # QUESTION-RELATED CONTEXT (for pre/post questioning)
    # ========================================================================
    pending_question: Optional[Dict[str, Any]] = None  # Question being asked
    last_question_answer: Optional[Dict[str, Any]] = None  # Player's answer
    
    
    # ========================================================================
    # STATE TRANSITION MANAGEMENT
    # ========================================================================
    
    def set_transition_to_combat(self, monster_data: Dict[str, Any]):
        """
        Prepare for transition to combat state.
        
        Args:
            monster_data: Information about the monster(s) for combat
                Expected keys: 'monster_name', 'count', 'description', etc.
        
        Example:
            story_state.set_transition_to_combat({
                'monster_name': 'Goblin',
                'count': 3,
                'description': 'Three goblins emerge from the shadows',
                'cr': 0.25
            })
        """
        self.pending_monster = monster_data
        self.next_game_state = "combat"
        self.last_updated = datetime.now().isoformat()
        
        # Add event to history
        self.add_story_event(
            event_type="transition_prep",
            narrative_text=f"Preparing for combat: {monster_data.get('description', 'Combat encounter')}",
            metadata={"target_state": "combat", "monster_data": monster_data}
        )
    
    def set_transition_to_dice(self, dice_situation: Dict[str, Any]):
        """
        Prepare for transition to dice roll state.
        
        Args:
            dice_situation: Information about the dice roll situation
                Expected keys: 'situation', 'stat', 'dc', 'dice_type', etc.
        
        Example:
            story_state.set_transition_to_dice({
                'situation': 'You must climb the steep cliff',
                'stat': 'strength',
                'skill': 'athletics',
                'dc': 15,
                'dice_type': 'd20'
            })
        """
        self.pending_dice_situation = dice_situation
        self.next_game_state = "dice"
        self.last_updated = datetime.now().isoformat()
        
        # Add event to history
        self.add_story_event(
            event_type="transition_prep",
            narrative_text=f"Dice roll required: {dice_situation.get('situation', 'Skill check')}",
            metadata={"target_state": "dice", "dice_situation": dice_situation}
        )
    
    def set_transition_to_question(self, question_data: Dict[str, Any]):
        """
        Prepare for transition to questioning state.
        
        Args:
            question_data: Information about the question
                Expected keys: 'question', 'context', 'consequences', etc.
        
        Example:
            story_state.set_transition_to_question({
                'question': 'Will you accept the mysterious stranger\'s offer?',
                'context': 'A hooded figure offers you a magical amulet',
                'consequences_accept': 'Gain a cursed amulet',
                'consequences_decline': 'The stranger vanishes'
            })
        """
        self.pending_question = question_data
        self.next_game_state = "question"
        self.last_updated = datetime.now().isoformat()
        
        # Add event to history
        self.add_story_event(
            event_type="transition_prep",
            narrative_text=f"Question posed: {question_data.get('question', 'Decision required')}",
            metadata={"target_state": "question", "question_data": question_data}
        )
    
    def set_transition_to_end(self):
        """
        Mark that we're ending the campaign/package.
        
        This should be called when the story package is complete
        and we're wrapping up the narrative.
        """
        self.next_game_state = "end"
        self.last_updated = datetime.now().isoformat()
        
        # Add event to history
        self.add_story_event(
            event_type="transition_prep",
            narrative_text=f"Ending story package {self.story_package_number}",
            metadata={"target_state": "end", "package_number": self.story_package_number}
        )
    
    def complete_transition(self, from_state: str):
        """
        Called when we've completed a transition and are back in story state.
        
        Args:
            from_state: The state we just came from ("combat", "dice", "question", "init")
        
        This method:
        1. Records the transition in history
        2. Clears pending state data
        3. Stores result data for narrative continuity
        """
        # Record the state we came from
        self.last_game_state = from_state
        self.next_game_state = "story"  # Back to story state
        self.last_updated = datetime.now().isoformat()
        
        # Process results based on state type
        if from_state == "combat":
            if self.pending_monster:
                # Store combat result if available
                self.last_combat_result = {
                    "monster": self.pending_monster,
                    "timestamp": datetime.now().isoformat()
                }
                self.pending_monster = None  # Clear pending
                
                self.add_story_event(
                    event_type="transition_complete",
                    narrative_text="Returned from combat encounter",
                    metadata={"from_state": "combat", "result": self.last_combat_result}
                )
        
        elif from_state == "dice":
            if self.pending_dice_situation:
                # Store dice result if available
                self.last_dice_result = {
                    "situation": self.pending_dice_situation,
                    "timestamp": datetime.now().isoformat()
                }
                self.pending_dice_situation = None  # Clear pending
                
                self.add_story_event(
                    event_type="transition_complete",
                    narrative_text="Returned from dice roll",
                    metadata={"from_state": "dice", "result": self.last_dice_result}
                )
        
        elif from_state == "question":
            if self.pending_question:
                # Store question result if available
                self.last_question_answer = {
                    "question": self.pending_question,
                    "timestamp": datetime.now().isoformat()
                }
                self.pending_question = None  # Clear pending
                
                self.add_story_event(
                    event_type="transition_complete",
                    narrative_text="Returned from questioning",
                    metadata={"from_state": "question", "result": self.last_question_answer}
                )
        
        elif from_state == "init":
            self.add_story_event(
                event_type="transition_complete",
                narrative_text="Campaign initialized",
                metadata={"from_state": "init"}
            )
    
    # ========================================================================
    # STORY HISTORY MANAGEMENT
    # ========================================================================
    
    def add_story_event(
        self, 
        event_type: str, 
        narrative_text: str, 
        metadata: Optional[Dict] = None
    ):
        """
        Add a narrative event to story history.
        
        Args:
            event_type: Type of event (e.g., "location_change", "npc_introduced", 
                       "combat", "dice_roll", "decision", "transition_prep", etc.)
            narrative_text: Human-readable description of what happened
            metadata: Additional structured data about the event
        
        Example:
            story_state.add_story_event(
                event_type="npc_introduced",
                narrative_text="The party meets Eldrin, a wise old wizard",
                metadata={"npc_name": "Eldrin", "location": "Tavern"}
            )
        """
        event = {
            "event_id": len(self.story_history) + 1,
            "event_type": event_type,
            "narrative_text": narrative_text,
            "timestamp": datetime.now().isoformat(),
            "package_number": self.story_package_number,
            "package_phase": self.package_phase,
            "location": self.current_location,
            "metadata": metadata or {}
        }
        
        self.story_history.append(event)
        self.last_updated = datetime.now().isoformat()
    
    def get_recent_events(self, count: int = 5) -> List[Dict]:
        """
        Get the most recent N story events.
        
        Args:
            count: Number of recent events to retrieve
        
        Returns:
            List of event dictionaries, most recent first
        
        Example:
            recent = story_state.get_recent_events(3)
            for event in recent:
                print(event['narrative_text'])
        """
        # Return most recent events (reversed so newest first)
        return list(reversed(self.story_history[-count:]))
    
    def get_events_by_type(self, event_type: str) -> List[Dict]:
        """
        Get all events of a specific type.
        
        Args:
            event_type: The type of events to retrieve
        
        Returns:
            List of matching event dictionaries
        
        Example:
            combats = story_state.get_events_by_type("combat")
            decisions = story_state.get_events_by_type("decision")
        """
        return [
            event for event in self.story_history 
            if event["event_type"] == event_type
        ]
    
    def get_events_by_location(self, location: str) -> List[Dict]:
        """
        Get all events that occurred at a specific location.
        
        Args:
            location: The location name
        
        Returns:
            List of matching event dictionaries
        """
        return [
            event for event in self.story_history 
            if event.get("location", "").lower() == location.lower()
        ]
    
    # ========================================================================
    # CONTEXT MANAGEMENT
    # ========================================================================
    
    def update_location(self, location: str, description: str = ""):
        """
        Update current location.
        
        Args:
            location: Name of the new location
            description: Optional description of the location
        
        Example:
            story_state.update_location(
                "Dark Forest",
                "A dense forest with twisted trees and eerie shadows"
            )
        """
        old_location = self.current_location
        self.current_location = location
        self.last_updated = datetime.now().isoformat()
        
        # Add to history
        self.add_story_event(
            event_type="location_change",
            narrative_text=f"Moved from {old_location or 'unknown'} to {location}",
            metadata={
                "old_location": old_location,
                "new_location": location,
                "description": description
            }
        )
    
    def add_npc(self, npc_name: str):
        """
        Add an NPC to the current scene.
        
        Args:
            npc_name: Name of the NPC
        
        Example:
            story_state.add_npc("Gandalf")
        """
        if npc_name not in self.active_npcs:
            self.active_npcs.append(npc_name)
            self.last_updated = datetime.now().isoformat()
            
            self.add_story_event(
                event_type="npc_introduced",
                narrative_text=f"{npc_name} appears in the scene",
                metadata={"npc_name": npc_name, "location": self.current_location}
            )
    
    def remove_npc(self, npc_name: str):
        """
        Remove an NPC from the scene.
        
        Args:
            npc_name: Name of the NPC to remove
        
        Example:
            story_state.remove_npc("Gandalf")
        """
        if npc_name in self.active_npcs:
            self.active_npcs.remove(npc_name)
            self.last_updated = datetime.now().isoformat()
            
            self.add_story_event(
                event_type="npc_departed",
                narrative_text=f"{npc_name} leaves the scene",
                metadata={"npc_name": npc_name, "location": self.current_location}
            )
    
    def add_plot_point(self, plot_point: str):
        """
        Add a new active plot point.
        
        Args:
            plot_point: Description of the plot point
        
        Example:
            story_state.add_plot_point("Find the ancient artifact")
        """
        if plot_point not in self.plot_points:
            self.plot_points.append(plot_point)
            self.last_updated = datetime.now().isoformat()
            
            self.add_story_event(
                event_type="plot_point_added",
                narrative_text=f"New plot point: {plot_point}",
                metadata={"plot_point": plot_point}
            )
    
    def resolve_plot_point(self, plot_point: str):
        """
        Mark a plot point as resolved.
        
        Args:
            plot_point: The plot point to resolve (exact match)
        
        Example:
            story_state.resolve_plot_point("Find the ancient artifact")
        """
        if plot_point in self.plot_points:
            self.plot_points.remove(plot_point)
            self.resolved_plot_points.append(plot_point)
            self.last_updated = datetime.now().isoformat()
            
            self.add_story_event(
                event_type="plot_point_resolved",
                narrative_text=f"Resolved: {plot_point}",
                metadata={"plot_point": plot_point}
            )
    
    def add_item_to_scene(self, item: str):
        """
        Add an item/object to the current scene.
        
        Args:
            item: Description of the item
        
        Example:
            story_state.add_item_to_scene("A dusty old book")
        """
        if item not in self.items_in_scene:
            self.items_in_scene.append(item)
            self.last_updated = datetime.now().isoformat()
            
            self.add_story_event(
                event_type="item_noticed",
                narrative_text=f"Item in scene: {item}",
                metadata={"item": item, "location": self.current_location}
            )
    
    def remove_item_from_scene(self, item: str):
        """
        Remove an item from the current scene.
        
        Args:
            item: Description of the item to remove
        """
        if item in self.items_in_scene:
            self.items_in_scene.remove(item)
            self.last_updated = datetime.now().isoformat()
            
            self.add_story_event(
                event_type="item_removed",
                narrative_text=f"Item removed: {item}",
                metadata={"item": item, "location": self.current_location}
            )
    
    def update_narrative_context(self, context: str):
        """
        Update the current narrative context.
        
        Args:
            context: Current narrative situation description
        
        Example:
            story_state.update_narrative_context(
                "The party stands at the entrance of a dark cave"
            )
        """
        self.narrative_context = context
        self.current_scene = context  # Also update scene
        self.last_updated = datetime.now().isoformat()
    
    def add_player_decision(self, decision: str, outcome: str):
        """
        Record a player decision and its outcome.
        
        Args:
            decision: What the player decided
            outcome: What happened as a result
        """
        decision_record = {
            "decision": decision,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat(),
            "package_number": self.story_package_number,
            "package_phase": self.package_phase
        }
        
        self.player_decisions.append(decision_record)
        
        self.add_story_event(
            event_type="player_decision",
            narrative_text=f"Decision: {decision}",
            metadata={"decision": decision, "outcome": outcome}
        )
    
    # ========================================================================
    # SERIALIZATION
    # ========================================================================
    
    def to_dict(self) -> Dict:
        """
        Convert StoryState to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the story state
        """
        return {
            # Story Progression
            "story_package_number": self.story_package_number,
            "is_side_quest": self.is_side_quest,
            "main_campaign_complete": self.main_campaign_complete,
            "package_phase": self.package_phase,
            
            # Current Narrative Context
            "current_location": self.current_location,
            "current_scene": self.current_scene,
            "narrative_context": self.narrative_context,
            
            # Active Elements
            "active_npcs": self.active_npcs,
            "plot_points": self.plot_points,
            "resolved_plot_points": self.resolved_plot_points,
            "items_in_scene": self.items_in_scene,
            
            # State Transition Tracking
            "last_game_state": self.last_game_state,
            "next_game_state": self.next_game_state,
            
            # Story History
            "story_history": self.story_history,
            
            # Session Context
            "session_notes_reference": self.session_notes_reference,
            "key_session_events": self.key_session_events,
            "player_decisions": self.player_decisions,
            
            # Metadata
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            
            # Pending State Data
            "pending_monster": self.pending_monster,
            "last_combat_result": self.last_combat_result,
            "pending_dice_situation": self.pending_dice_situation,
            "last_dice_result": self.last_dice_result,
            "pending_question": self.pending_question,
            "last_question_answer": self.last_question_answer
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StoryState':
        """
        Create StoryState from dictionary.
        
        Args:
            data: Dictionary with story state data
        
        Returns:
            StoryState instance
        """
        return cls(
            # Story Progression
            story_package_number=data.get("story_package_number", 1),
            is_side_quest=data.get("is_side_quest", False),
            main_campaign_complete=data.get("main_campaign_complete", False),
            package_phase=data.get("package_phase", 1),
            
            # Current Narrative Context
            current_location=data.get("current_location", ""),
            current_scene=data.get("current_scene", ""),
            narrative_context=data.get("narrative_context", ""),
            
            # Active Elements
            active_npcs=data.get("active_npcs", []),
            plot_points=data.get("plot_points", []),
            resolved_plot_points=data.get("resolved_plot_points", []),
            items_in_scene=data.get("items_in_scene", []),
            
            # State Transition Tracking
            last_game_state=data.get("last_game_state"),
            next_game_state=data.get("next_game_state"),
            
            # Story History
            story_history=data.get("story_history", []),
            
            # Session Context
            session_notes_reference=data.get("session_notes_reference"),
            key_session_events=data.get("key_session_events", []),
            player_decisions=data.get("player_decisions", []),
            
            # Metadata
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
            
            # Pending State Data
            pending_monster=data.get("pending_monster"),
            last_combat_result=data.get("last_combat_result"),
            pending_dice_situation=data.get("pending_dice_situation"),
            last_dice_result=data.get("last_dice_result"),
            pending_question=data.get("pending_question"),
            last_question_answer=data.get("last_question_answer")
        )
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current story state.
        
        Returns:
            Dictionary with key story state information
        """
        return {
            "package": f"{self.story_package_number}.{self.package_phase}",
            "location": self.current_location or "Unknown",
            "active_npcs": len(self.active_npcs),
            "active_plot_points": len(self.plot_points),
            "resolved_plot_points": len(self.resolved_plot_points),
            "total_events": len(self.story_history),
            "last_state": self.last_game_state or "init",
            "next_state": self.next_game_state or "story",
            "narrative_context": self.narrative_context[:100] + "..." if len(self.narrative_context) > 100 else self.narrative_context
        }
    
    def get_context_for_ai(self) -> str:
        """
        Generate a formatted context string for AI/LLM consumption.
        
        Returns:
            Formatted string with relevant story context
        """
        context_parts = [
            f"=== STORY CONTEXT ===",
            f"Package: {self.story_package_number}.{self.package_phase}",
            f"Location: {self.current_location or 'Unknown'}",
        ]
        
        if self.narrative_context:
            context_parts.append(f"Current Situation: {self.narrative_context}")
        
        if self.active_npcs:
            context_parts.append(f"NPCs Present: {', '.join(self.active_npcs)}")
        
        if self.plot_points:
            context_parts.append(f"Active Plot Points:")
            for pp in self.plot_points:
                context_parts.append(f"  - {pp}")
        
        if self.items_in_scene:
            context_parts.append(f"Items in Scene: {', '.join(self.items_in_scene)}")
        
        # Add recent events
        recent = self.get_recent_events(3)
        if recent:
            context_parts.append(f"\nRecent Events:")
            for event in recent:
                context_parts.append(f"  - {event['narrative_text']}")
        
        return "\n".join(context_parts)
    
    def clear_pending_states(self):
        """Clear all pending transition states."""
        self.pending_monster = None
        self.pending_dice_situation = None
        self.pending_question = None
        self.next_game_state = "story"
        self.last_updated = datetime.now().isoformat()
    
    def __str__(self) -> str:
        """String representation of story state."""
        return (
            f"StoryState(Package {self.story_package_number}.{self.package_phase}, "
            f"Location: {self.current_location or 'Unknown'}, "
            f"NPCs: {len(self.active_npcs)}, "
            f"Events: {len(self.story_history)})"
        )


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("STORY STATE - TEST SUITE")
    print("=" * 70)
    
    # Test 1: Create story state
    print("\n📖 TEST 1: Create Story State")
    print("-" * 70)
    
    story = StoryState(
        story_package_number=1,
        package_phase=1,
        current_location="Tavern",
        narrative_context="The party gathers in a bustling tavern"
    )
    
    print(f"✓ Created: {story}")
    print(f"Summary: {story.get_summary()}")
    
    # Test 2: Context Management
    print("\n\n📖 TEST 2: Context Management")
    print("-" * 70)
    
    story.update_location("Dark Forest", "A dense, mysterious forest")
    story.add_npc("Eldrin the Wizard")
    story.add_npc("Goblin Scout")
    story.add_plot_point("Find the ancient artifact")
    story.add_plot_point("Defeat the goblin tribe")
    story.add_item_to_scene("Mysterious amulet")
    
    print(f"Location: {story.current_location}")
    print(f"Active NPCs: {story.active_npcs}")
    print(f"Plot Points: {story.plot_points}")
    print(f"Items: {story.items_in_scene}")
    
    # Test 3: State Transitions
    print("\n\n📖 TEST 3: State Transitions")
    print("-" * 70)
    
    # Transition to combat
    story.set_transition_to_combat({
        'monster_name': 'Goblin',
        'count': 3,
        'description': 'Three goblins attack!',
        'cr': 0.25
    })
    print(f"✓ Set transition to combat")
    print(f"  Next state: {story.next_game_state}")
    print(f"  Pending monster: {story.pending_monster}")
    
    # Complete transition
    story.complete_transition("combat")
    print(f"✓ Completed transition from combat")
    print(f"  Last state: {story.last_game_state}")
    print(f"  Combat result stored: {story.last_combat_result is not None}")
    
    # Transition to dice
    story.set_transition_to_dice({
        'situation': 'Climb the cliff',
        'stat': 'strength',
        'skill': 'athletics',
        'dc': 15
    })
    print(f"✓ Set transition to dice roll")
    print(f"  Next state: {story.next_game_state}")
    
    story.complete_transition("dice")
    print(f"✓ Completed transition from dice roll")
    
    # Transition to question
    story.set_transition_to_question({
        'question': 'Do you trust the wizard?',
        'context': 'Eldrin offers a mysterious potion'
    })
    print(f"✓ Set transition to question")
    print(f"  Next state: {story.next_game_state}")
    
    story.complete_transition("question")
    print(f"✓ Completed transition from question")
    
    # Test 4: Story History
    print("\n\n📖 TEST 4: Story History")
    print("-" * 70)
    
    story.add_story_event(
        event_type="discovery",
        narrative_text="The party discovers a hidden cave",
        metadata={"item_found": "ancient map"}
    )
    
    story.add_player_decision(
        "Enter the cave",
        "The party ventures into darkness"
    )
    
    print(f"Total events: {len(story.story_history)}")
    print(f"\nRecent events:")
    for event in story.get_recent_events(5):
        print(f"  [{event['event_type']}] {event['narrative_text']}")
    
    # Test 5: Query Events
    print("\n\n📖 TEST 5: Query Events")
    print("-" * 70)
    
    transitions = story.get_events_by_type("transition_prep")
    print(f"Transition events: {len(transitions)}")
    
    location_events = story.get_events_by_location("Dark Forest")
    print(f"Events in Dark Forest: {len(location_events)}")
    
    # Test 6: AI Context
    print("\n\n📖 TEST 6: AI Context Generation")
    print("-" * 70)
    
    ai_context = story.get_context_for_ai()
    print(ai_context)
    
    # Test 7: Serialization
    print("\n\n📖 TEST 7: Serialization")
    print("-" * 70)
    
    # To dict
    story_dict = story.to_dict()
    print(f"✓ Serialized to dict")
    print(f"  Keys: {len(story_dict)}")
    print(f"  Package: {story_dict['story_package_number']}.{story_dict['package_phase']}")
    
    # From dict
    restored = StoryState.from_dict(story_dict)
    print(f"✓ Restored from dict")
    print(f"  Location: {restored.current_location}")
    print(f"  NPCs: {restored.active_npcs}")
    print(f"  Events: {len(restored.story_history)}")
    print(f"  Plot points: {restored.plot_points}")
    
    # Test 8: Resolve plot points
    print("\n\n📖 TEST 8: Resolve Plot Points")
    print("-" * 70)
    
    print(f"Active plot points: {story.plot_points}")
    story.resolve_plot_point("Defeat the goblin tribe")
    print(f"After resolution:")
    print(f"  Active: {story.plot_points}")
    print(f"  Resolved: {story.resolved_plot_points}")
    
    # Test 9: Remove items
    print("\n\n📖 TEST 9: Scene Management")
    print("-" * 70)
    
    print(f"Items before: {story.items_in_scene}")
    story.remove_item_from_scene("Mysterious amulet")
    print(f"Items after: {story.items_in_scene}")
    
    story.remove_npc("Goblin Scout")
    print(f"NPCs after removal: {story.active_npcs}")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS COMPLETED")
    print("=" * 70)