#!/usr/bin/env python3
"""
•	Story State:
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

"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable, Any
from datetime import datetime

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[3]  # Goes up 1 levels to DNDDM folder
sys.path.insert(0, str(project_root))

from BackEnd.prompts import campaign_init_prompt, pre_combat_prompt, post_combat_prompt, pre_diceroll_prompt, post_diceroll_prompt, pre_question_prompt, post_question_prompt, wrapup_prompt
from GameState.combat_state import CombatState
from GameState.dice_state import DiceRollState
from GameState.question_state import QuestioningState

@dataclass
class StoryState:
    """
    Manages narrative state and story progression for D&D campaign.
    
    This class is responsible for tracking WHERE the story is,
    WHAT is happening narratively, and HOW the story is progressing.
    It does NOT generate content - that's handled by the Story package.
    """
    
    # Story Progression
    story_package_number: int = 1  # 1-5 for main campaign
    is_side_quest: bool = False
    main_campaign_complete: bool = False
    package_phase: int = 1  # Which step in the 15-step flow
    
    # Current Narrative Context
    current_location: str = ""
    current_scene: str = ""
    narrative_context: str = ""  # What's happening right now
    
    # Active Elements
    active_npcs: List[str] = field(default_factory=list)
    plot_points: List[str] = field(default_factory=list)
    
    # State Transition Tracking
    last_game_state: Optional[str] = None  # "init", "combat", "dice", "question"
    next_game_state: Optional[str] = None  # "combat", "dice", "question", "end"
    
    # Story History
    story_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Session Context
    session_notes_reference: Optional[str] = None
    key_session_events: List[str] = field(default_factory=list)
    player_decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Combat-related context (for pre/post combat story generation)
    pending_monster: Optional[Dict[str, Any]] = None  # Monster being prepared for combat
    last_combat_result: Optional[Dict[str, Any]] = None  # Result of last combat
    
    # Dice-related context (for pre/post dice roll story generation)
    pending_dice_situation: Optional[Dict[str, Any]] = None  # What dice roll is about
    last_dice_result: Optional[Dict[str, Any]] = None  # Result of last dice roll
    
    # Question-related context (for pre/post questioning)
    pending_question: Optional[Dict[str, Any]] = None  # Question being asked
    last_question_answer: Optional[Dict[str, Any]] = None  # Player's answer



    # State Transitions
    def set_transition_to_combat(self, monster_data: Dict[str, Any]):
        """Prepare for transition to combat state"""
        
    def set_transition_to_dice(self, dice_situation: Dict[str, Any]):
        """Prepare for transition to dice roll state"""
        
    def set_transition_to_question(self, question_data: Dict[str, Any]):
        """Prepare for transition to questioning state"""
        
    def set_transition_to_end(self):
        """Mark that we're ending the campaign/package"""
        
    def complete_transition(self, from_state: str):
        """Called when we've completed a transition and are back in story state"""

    # Story History

    def add_story_event(self, event_type: str, narrative_text: str, metadata: Optional[Dict] = None):
        """Add a narrative event to story history"""
    
    def get_recent_events(self, count: int = 5) -> List[Dict]:
        """Get the most recent N story events"""
    
    def get_events_by_type(self, event_type: str) -> List[Dict]:
        """Get all events of a specific type"""


    # Context Manangment

    def update_location(self, location: str, description: str = ""):
        """Update current location"""
        
    def add_npc(self, npc_name: str):
        """Add an NPC to the current scene"""
        
    def remove_npc(self, npc_name: str):
        """Remove an NPC from the scene"""
        
    def add_plot_point(self, plot_point: str):
        """Add a new active plot point"""
        
    def resolve_plot_point(self, plot_point: str):
        """Mark a plot point as resolved"""
        
    def add_item_to_scene(self, item: str):
        """Add an item/object to the current scene"""

    # Serilization:


    # Utility: 

    # Example Usage:

    