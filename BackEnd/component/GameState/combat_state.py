#!/usr/bin/env python3
"""
RPG Logic

Handles combat-specific logic, turn order, and action resolution.


"""

import sys
from pathlib import Path
from enum import Enum
import re
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


    @classmethod
    def from_dm_description(
        cls,
        dm_text: str,
        characters: List[Character],
        dice_state: Optional[DiceRollState] = None,
        index_path: str = "../../../srd_story_cycle/08_monsters_and_npcs/INDEX.md"
    ) -> 'CombatState':
        """Parse DM combat Setup using INDEX.md for monster lookup
        
        Args:
            dm_text: DM's description of the encounter
            characters: List of player characters
            dice_state: Optional DiceRollState
            index_path: Path to the monster INDEX.md file
            
        Returns:
            Initialized CombatState
            
        Example:
            dm_text = "You encounter 3 goblins and 1 ogre in the cave"
        """
        
        lines = dm_text.split('.')
        encounter_name = lines[0].strip() if lines else "Unknown Encounter"
        
        # Parse monster counts from description
        monster_pattern = r'(\d+)\s+([a-zA-Z\s]+?)(?:s|es)?\s*(?:and|in|at|,|\.|\n|$)'
        matches = re.findall(monster_pattern, dm_text.lower())
        
        monsters = []
        monster_summary = []
        
        # Load monster index
        monster_index = cls._load_monster_index(index_path)
        
        for count_str, monster_name in matches:
            count = int(count_str)
            monster_name = monster_name.strip()
            
            # Find matching monster in index
            monster_file_path = cls._find_monster_in_index(monster_name, monster_index)
            
            if monster_file_path:
                # Load monster from markdown file
                base_path = Path(index_path).parent
                full_path = base_path / monster_file_path
                
                monster_template = cls._load_monster_from_markdown(full_path)
                
                if monster_template:
                    # Create copies of the monster
                    for _ in range(count):
                        monster_copy = Monster(
                            name=monster_template.name,
                            monster_type=monster_template.monster_type,
                            size=monster_template.size,
                            alignment=monster_template.alignment,
                            challenge_rating=monster_template.challenge_rating,
                            hp=monster_template.hp,
                            ac=monster_template.ac,
                            stats=monster_template.stats.copy(),
                            abilities=monster_template.abilities.copy(),
                            actions=monster_template.actions.copy(),
                            legendary_actions=monster_template.legendary_actions.copy(),
                            lair_actions=monster_template.lair_actions.copy(),
                            description=monster_template.description
                        )
                        monsters.append(monster_copy)
                    
                    monster_summary.append(f"{count} {monster_template.name}{'s' if count > 1 else ''}")
        
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


    @staticmethod
    def _load_monster_index(index_path: str) -> Dict[str, str]:
        """Load monster names and file paths from INDEX.md
        
        Returns:
            Dict mapping lowercase monster names to file paths
        """
        monster_index = {}
        
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Pattern to match: * [Monster Name](path/to/monster.md)
            pattern = r'\*\s*\[([^\]]+)\]\(([^\)]+)\)'
            matches = re.findall(pattern, content)
            
            for name, path in matches:
                # Store with lowercase name for easier matching
                monster_index[name.lower()] = path
                
        except FileNotFoundError:
            print(f"Warning: Monster index not found at {index_path}")
        
        return monster_index


    @staticmethod
    def _find_monster_in_index(search_name: str, monster_index: Dict[str, str]) -> Optional[str]:
        """Find monster file path by name
        
        Args:
            search_name: Name to search for (from DM description)
            monster_index: Dict of monster names to file paths
            
        Returns:
            File path if found, None otherwise
        """
        search_name = search_name.lower().strip()
        
        # Try exact match first
        if search_name in monster_index:
            return monster_index[search_name]
        
        # Try singular form (remove trailing 's')
        if search_name.endswith('s'):
            singular = search_name[:-1]
            if singular in monster_index:
                return monster_index[singular]
        
        # Try partial match
        for name, path in monster_index.items():
            if search_name in name or name in search_name:
                return path
        
        print(f"Warning: Monster '{search_name}' not found in index")
        return None


    @staticmethod
    def _load_monster_from_markdown(file_path: Path) -> Optional[Monster]:
        """Parse monster markdown file and create Monster object
        
        Args:
            file_path: Path to monster markdown file
            
        Returns:
            Monster object or None if parsing fails
        """
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse YAML frontmatter
            name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
            cr_match = re.search(r'^cr:\s*(\d+(?:\.\d+)?)$', content, re.MULTILINE)
            type_match = re.search(r'^type:\s*(.+)$', content, re.MULTILINE)
            
            # Parse main content
            size_align_match = re.search(r'_([^,]+),\s*([^_]+)_', content)
            ac_match = re.search(r'\*\*Armor Class\*\*\s*(\d+)', content)
            hp_match = re.search(r'\*\*Hit Points\*\*\s*(\d+)', content)
            
            # Parse stat block
            stats = {}
            stat_pattern = r'\|\s*(\d+)\s*\(([+-]?\d+)\)\s*\|'
            stat_matches = re.findall(stat_pattern, content)
            if len(stat_matches) >= 6:
                stat_names = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
                for i, (score, modifier) in enumerate(stat_matches[:6]):
                    stats[stat_names[i]] = int(score)
            
            # Parse actions
            actions = []
            actions_section = re.search(r'### Actions\s*(.+?)(?:###|$)', content, re.DOTALL)
            if actions_section:
                action_pattern = r'\*\*([^*]+?)\.\*\*\s*(.+?)(?=\*\*[^*]+?\.\*\*|\Z)'
                action_matches = re.findall(action_pattern, actions_section.group(1), re.DOTALL)
                for action_name, action_desc in action_matches:
                    actions.append({
                        'name': action_name.strip(),
                        'description': action_desc.strip()
                    })
            
            # Parse abilities
            abilities = []
            abilities_section = re.search(r'\*\*Challenge\*\*.*?\n\n(.+?)(?:### Actions)', content, re.DOTALL)
            if abilities_section:
                ability_pattern = r'\*\*([^*]+?)\.\*\*\s*(.+?)(?=\*\*[^*]+?\.\*\*|\n\n|\Z)'
                ability_matches = re.findall(ability_pattern, abilities_section.group(1), re.DOTALL)
                for ability_name, ability_desc in ability_matches:
                    abilities.append({
                        'name': ability_name.strip(),
                        'description': ability_desc.strip()
                    })
            
            # Parse legendary actions
            legendary_actions = []
            legendary_section = re.search(r'### Legendary Actions\s*(.+?)$', content, re.DOTALL)
            if legendary_section:
                leg_pattern = r'\*\*([^*]+?)\.*\*\*\s*(.+?)(?=\*\*[^*]+?\.|\Z)'
                leg_matches = re.findall(leg_pattern, legendary_section.group(1), re.DOTALL)
                for leg_name, leg_desc in leg_matches:
                    legendary_actions.append({
                        'name': leg_name.strip(),
                        'description': leg_desc.strip()
                    })
            
            # Create Monster object
            if name_match and ac_match and hp_match:
                size_category = size_align_match.group(1).split()[0] if size_align_match else "Medium"
                alignment = size_align_match.group(2).strip() if size_align_match else "unaligned"
                
                return Monster(
                    name=name_match.group(1),
                    monster_type=type_match.group(1) if type_match else "unknown",
                    size=size_category,
                    alignment=alignment,
                    challenge_rating=float(cr_match.group(1)) if cr_match else 1,
                    hp=int(hp_match.group(1)),
                    ac=int(ac_match.group(1)),
                    stats=stats,
                    abilities=abilities,
                    actions=actions,
                    legendary_actions=legendary_actions,
                    lair_actions=[],
                    description=f"A {size_category.lower()} {type_match.group(1) if type_match else 'creature'}"
                )
                
        except Exception as e:
            print(f"Error loading monster from {file_path}: {e}")
        
        return None
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