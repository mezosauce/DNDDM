#!/usr/bin/env python3
"""
RPG Logic

Handles combat-specific logic, turn order, and action resolution.


"""

import sys
from pathlib import Path
from enum import Enum

project_root = Path(__file__).resolve().parents[1]  # Goes up 1 levels to DNDDM folder
sys.path.insert(0, str(project_root))


from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime
import random
import uuid

from Class.monsters.monster import Monster
from Class.Character import Character
from Class.barbarian import Barbarian

from GameState.dice_state import DiceRollState, DiceType, PlayerStats, RollType

class CombatPhase(Enum):
    """Combat phases"""
    SETUP = "setup"
    INITIATIVE = "initiative"
    ACTIVE = "active"
    ENDED = "ended"


class ParticipantType(Enum):
    """Type of combat participant"""
    CHARACTER = "character"
    MONSTER = "monster"


@dataclass
class CombatParticipant:
    """Wrapper for combat participants with combat-specific data"""
    participant_id: str
    name: str
    participant_type: ParticipantType
    entity: Union[Character, Monster]  # The actual character or monster object
    
    # Initiative
    initiative_roll: int = 0
    initiative_bonus: int = 0
    initiative_total: int = 0
    
    # Combat status
    is_active: bool = True
    is_surprised: bool = False
    has_acted_this_round: bool = False
    
    # Temporary combat modifiers
    temp_hp: int = 0
    conditions: List[str] = field(default_factory=list)
    
    def get_current_hp(self) -> int:
        """Get current HP from the entity"""
        return self.entity.hp
    
    def get_max_hp(self) -> int:
        """Get max HP from the entity"""
        if hasattr(self.entity, 'max_hp'):
            return self.entity.max_hp
        return self.entity.hp
    
    def get_ac(self) -> int:
        """Get AC from the entity"""
        return self.entity.ac
    
    def is_alive(self) -> bool:
        """Check if participant is alive"""
        return self.get_current_hp() > 0


@dataclass
class CombatState:
    """Manages the state of combat encounters"""
    
    combat_id: str
    encounter_name: str
    combat_phase: CombatPhase.SETUP

    start_time: str = field(default_factory=lambda: datetime.now().isoformat)
    end_time: Optional[str] = None
    total_rounds: int = 0


    participants: List[CombatParticipant] = field(default_factory=list)
    defeated_participants: List[str] = field(default_factory=list)

    initiative_order: List[Tuple[str, int]] = field(default_factory=list)
    current_turn_index: int = 0
    current_round: int = 0

    actions_taken_this_turn: Dict[str, List[str]] = field(default_factory=dict)

    turn_history: List[Dict] = field(default_factory=list)
    log: List[str] = field(default_factory=list)

    dice_state: Optional[DiceRollState] = None
    
    
    metadata: Dict = field(default_factory=dict)


    # INIT

    def __init__(
        self,
        encounter_name: str,
        characters: List[Character],
        monsters: List[Monster],
        dice_state: Optional[DiceRollState] = None,
        combat_id: Optional[str] = None,
    ):
        """
        Initialize a combat encounter
        
        Args:
            encounter_name: Name of the encounter
            characters: List of player characters
            monsters: List of monsters
            dice_state: Optional DiceRollState for rolling
            combat_id: Optional custom combat ID
        """
        self.combat_id = combat_id or f"combat_{uuid.uuid4().hex[:8]}"
        self.encounter_name = encounter_name
        self.combat_phase = CombatPhase.SETUP
        self.start_time = datetime.now().isoformat()
        self.end_time = None
        self.total_rounds = 0
        self.current_round = 0
        
        # Initialize collections
        self.participants = []
        self.defeated_participants = []
        self.initiative_order = []
        self.current_turn_index = 0
        self.actions_taken_this_turn = {}
        self.turn_history = []
        self.log = []
        
        # Set dice state
        self.dice_state = dice_state
        
        
        self.metadata = {}
        
        # Add participants
        self._add_characters(characters)
        self._add_monsters(monsters)
        
        self._log(f"Combat '{encounter_name}' initialized")
        self._log(f"Participants: {len(self.participants)} ({len(characters)} characters, {len(monsters)} monsters)")



    def _add_characters(self, characters: List[Character]):
        """Add characters as combat participants"""
        for char in characters:
            participant = CombatParticipant(
                participant_id=f"char_{char.name.lower().replace(' ', '_')}",
                name=char.name,
                participant_type=ParticipantType.CHARACTER,
                entity=char,
                initiative_bonus=self._calculate_initiative_bonus(char)
            )
            self.participants.append(participant)
    
    def _add_monsters(self, monsters: List[Monster]):
        """Add monsters as combat participants"""
        # Track monster counts for duplicate names
        name_counts: Dict[str, int] = {}
        
        for monster in monsters:
            # Handle duplicate monster names
            base_name = monster.name
            if base_name in name_counts:
                name_counts[base_name] += 1
                display_name = f"{base_name} {name_counts[base_name]}"
                participant_id = f"mon_{base_name.lower().replace(' ', '_')}_{name_counts[base_name]}"
            else:
                name_counts[base_name] = 1
                display_name = base_name
                participant_id = f"mon_{base_name.lower().replace(' ', '_')}_1"
            
            participant = CombatParticipant(
                participant_id=participant_id,
                name=display_name,
                participant_type=ParticipantType.MONSTER,
                entity=monster,
                initiative_bonus=self._calculate_initiative_bonus(monster)
            )
            self.participants.append(participant)
    
    def _calculate_initiative_bonus(self, entity: Union[Character, Monster]) -> int:
        """Calculate initiative bonus (DEX modifier)"""
        if hasattr(entity, 'stats') and isinstance(entity.stats, dict):
            dex = entity.stats.get('dexterity', 10)
            return (dex - 10) // 2
        return 0
    
    def roll_initiative(self) -> Dict[str, Dict]:
        """
        Roll initiative for all participants
        
        Returns:
            Dict mapping participant_id to initiative data
        """
        if self.combat_phase != CombatPhase.SETUP:
            raise RuntimeError(f"Cannot roll initiative in phase: {self.combat_phase.value}")
        
        self.combat_phase = CombatPhase.INITIATIVE
        self._log("Rolling initiative...")
        
        initiative_results = {}
        
        for participant in self.participants:
            # Roll d20
            roll = random.randint(1, 20)
            
            # Calculate total
            total = roll + participant.initiative_bonus
            
            # Store in participant
            participant.initiative_roll = roll
            participant.initiative_total = total
            
            # Store in results
            initiative_results[participant.participant_id] = {
                'name': participant.name,
                'type': participant.participant_type.value,
                'roll': roll,
                'bonus': participant.initiative_bonus,
                'total': total
            }
            
            self._log(f"{participant.name}: {roll} + {participant.initiative_bonus} = {total}")
        
        return initiative_results
    

    def determine_turn_order(self):
        """ Sort by INIT"""
        if self.combat_phase != CombatPhase.INITIATIVE:
            raise RuntimeError(f"Cannot determine turn order in phase: {self.combat_phase.value}")
        
        # Sort participants by initiative (descending), then by initiative_bonus (descending)
        sorted_participants = sorted(
            self.participants,
            key=lambda p: (p.initiative_total, p.initiative_bonus),
            reverse=True
        )
        
        # Create initiative order list
        self.initiative_order = [
            (p.participant_id, p.initiative_total)
            for p in sorted_participants
        ]
        
        # Log the order
        self._log("\n=== Initiative Order ===")
        for i, (participant_id, init_total) in enumerate(self.initiative_order, 1):
            participant = self.get_participant_by_id(participant_id)
            self._log(f"{i}. {participant.name} (Initiative: {init_total})")
        self._log("=" * 40)

    def init_combat(self):
        """Start Combat Encounter"""
        if self.combat_phase != CombatPhase.INITIATIVE:
            raise RuntimeError(f"Cannot start combat in phase: {self.combat_phase.value}")
        
        if not self.initiative_order:
            raise RuntimeError("Cannot start combat: initiative order not determined")
        
        self.combat_phase = CombatPhase.ACTIVE
        self.current_round = 1
        self.current_turn_index = 0
        
        self._log("\n" + "=" * 60)
        self._log(f"COMBAT START: {self.encounter_name}")
        self._log("=" * 60)
        
        # Start first turn
        self.start_turn()
    
    def from_dm_description(cls,
        dm_text: str,
        characters: List[Character],
        available_monsters: Dict[str, Monster],
        dice_state: Optional[DiceRollState] = None
    ) -> 'CombatState':
        """Parse DM combat Setup
        Args:
            dm_text: DM's description of the encounter
            characters: List of player characters
            available_monsters: Dict mapping monster names to Monster objects
            dice_state: Optional DiceRollState
            
        Returns:
            Initialized CombatState
            
        Example:
            dm_text = "You encounter 3 goblins and 1 goblin boss in the cave"
            available_monsters = {"goblin": goblin_template, "goblin boss": boss_template}
        """

        import re

        lines = dm_text.split('.')
        encounter_name = lines[0].strip() if lines else "Unknown Encounter"


        monster_pattern = r'(\d+)\s+([a-zA-Z\s]+?)(?:s|es)?\s*(?:and|in|at|,|\.|\n|$)'
        matches = re.findall(monster_pattern, dm_text.lower())

        monsters = []
        monster_summary = []

        for count_str, monster_name in matches:
            count = int(count_str)
            monster_name = monster_name.strip()
            
            # Find matching monster template
            template = None
            for key, monster_template in available_monsters.items():
                if key.lower() in monster_name or monster_name in key.lower():
                    template = monster_template
                    break
            
            if template:
                # Create copies of the monster
                for _ in range(count):
                    # Create a copy of the monster
                    monster_copy = Monster(
                        name=template.name,
                        monster_type=template.monster_type,
                        size=template.size,
                        alignment=template.alignment,
                        challenge_rating=template.challenge_rating,
                        hp=template.hp,
                        ac=template.ac,
                        stats=template.stats.copy(),
                        abilities=template.abilities.copy(),
                        actions=template.actions.copy(),
                        legendary_actions=template.legendary_actions.copy(),
                        lair_actions=template.lair_actions.copy(),
                        description=template.description
                    )
                    monsters.append(monster_copy)
                
                monster_summary.append(f"{count} {template.name}{'s' if count > 1 else ''}")
        
        # Create combat state
        combat = cls(
            encounter_name=encounter_name,
            characters=characters,
            monsters=monsters,
            dice_state=dice_state
        )
        
        # Add metadata
        combat.metadata['dm_description'] = dm_text
        combat.metadata['monster_summary'] = ", ".join(monster_summary)
        
        return combat

# ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def get_participant_by_id(self, participant_id: str) -> Optional[CombatParticipant]:
        """Get participant by ID"""
        for participant in self.participants:
            if participant.participant_id == participant_id:
                return participant
        return None
    
    def get_current_participant(self) -> Optional[CombatParticipant]:
        """Get the participant whose turn it currently is"""
        if not self.initiative_order or self.current_turn_index >= len(self.initiative_order):
            return None
        
        participant_id = self.initiative_order[self.current_turn_index][0]
        return self.get_participant_by_id(participant_id)
    
    def _log(self, message: str):
        """Add entry to combat log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {message}")
    
    def start_turn(self):
        """Begin a participant's turn"""
        participant = self.get_current_participant()
        if not participant:
            return
        
        participant.has_acted_this_round = False
        self.actions_taken_this_turn[participant.participant_id] = []
        
        self._log(f"\n--- {participant.name}'s Turn (Initiative: {participant.initiative_total}) ---")
        
        # Record turn start in history
        self.turn_history.append({
            'round': self.current_round,
            'turn': self.current_turn_index + 1,
            'participant_id': participant.participant_id,
            'participant_name': participant.name,
            'hp': participant.get_current_hp(),
            'timestamp': datetime.now().isoformat()
        })
    
    def get_combat_summary(self) -> Dict:
        """Get current combat state summary for UI/LLM"""
        summary = {
            'combat_id': self.combat_id,
            'encounter_name': self.encounter_name,
            'phase': self.combat_phase.value,
            'round': self.current_round,
            'total_rounds': self.total_rounds,
            
            'participants': [],
            'initiative_order': [],
            
            'current_turn': None,
            'defeated_count': len(self.defeated_participants),
            
            'log': self.log[-10:] if len(self.log) > 10 else self.log
        }
        
        # Add participant data
        for participant in self.participants:
            summary['participants'].append({
                'id': participant.participant_id,
                'name': participant.name,
                'type': participant.participant_type.value,
                'hp': participant.get_current_hp(),
                'max_hp': participant.get_max_hp(),
                'ac': participant.get_ac(),
                'is_alive': participant.is_alive(),
                'conditions': participant.conditions,
                'initiative': participant.initiative_total
            })
        
        # Add initiative order
        for participant_id, init_total in self.initiative_order:
            participant = self.get_participant_by_id(participant_id)
            if participant:
                summary['initiative_order'].append({
                    'name': participant.name,
                    'initiative': init_total,
                    'is_current': self.initiative_order[self.current_turn_index][0] == participant_id
                })
        
        # Current turn info
        current = self.get_current_participant()
        if current:
            summary['current_turn'] = {
                'name': current.name,
                'type': current.participant_type.value,
                'hp': current.get_current_hp(),
                'max_hp': current.get_max_hp(),
                'ac': current.get_ac()
            }
        
        return summary