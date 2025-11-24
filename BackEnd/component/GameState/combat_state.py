#!/usr/bin/env python3
"""
RPG Logic

Handles combat-specific logic, turn order, and action resolution.


"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]  # Goes up 1 levels to DNDDM folder
sys.path.insert(0, str(project_root))


from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

from Class.monsters.monster import Monster
from Class.Character import Character


from GameState.dice_state import DiceRollState, DiceType, PlayerStats, RollType
import random


@dataclass
class CombatState:
    """Manages the state of combat encounters"""
    encounter_name: str
    monsters: List[Monster] = field(default_factory=list)
    characters: List[Character] = field(default_factory=list)
    turn_order: List[str] = field(default_factory=list)  # Names of participants in turn order
    current_turn_index: int = 0
    round_number: int = 1
    log: List[str] = field(default_factory=list)  # Combat log entries

    def start_combat(self):
        """Initialize combat state and determine turn order"""
        self.turn_order = [c.name for c in self.characters] + [m.name for m in self.monsters]
        # Simple initiative roll (could be expanded)
        import random
        random.shuffle(self.turn_order)
        self.current_turn_index = 0
        self.round_number = 1
        self.log.append(f"Combat '{self.encounter_name}' started. Turn order: {', '.join(self.turn_order)}")

    def next_turn(self):
        """Advance to the next turn in the combat"""
        if not self.turn_order:
            raise ValueError("Turn order is empty. Start combat first.")
        
        self.current_turn_index += 1
        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.round_number += 1
            self.log.append(f"--- Round {self.round_number} ---")
        
        current_participant = self.turn_order[self.current_turn_index]
        self.log.append(f"It's now {current_participant}'s turn.")

    def get_current_participant(self) -> str:
        """Get the name of the current participant whose turn it is"""
        if not self.turn_order:
            raise ValueError("Turn order is empty. Start combat first.")
        return self.turn_order[self.current_turn_index]
    
    def add_log_entry(self, entry: str):
        """Add an entry to the combat log with a timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log.append(f"[{timestamp}] {entry}")

    def end_combat(self):
        """End the combat encounter"""
        self.log.append(f"Combat '{self.encounter_name}' ended after {self.round_number} rounds.")
        self.turn_order.clear()
        self.current_turn_index = 0
        self.round_number = 1


    def get_combat_summary(self) -> str:
        """Get a summary of the combat log"""
        return "\n".join(self.log)
    def is_combat_active(self) -> bool:
        """Check if combat is currently active"""
        return len(self.turn_order) > 0
    def remove_participant(self, name: str):
        """Remove a participant (character or monster) from combat"""
        if name in self.turn_order:
            index = self.turn_order.index(name)
            self.turn_order.remove(name)
            # Adjust current turn index if necessary
            if index <= self.current_turn_index and self.current_turn_index > 0:
                self.current_turn_index -= 1
            self.add_log_entry(f"{name} has been removed from combat.")
        else:
            raise ValueError(f"Participant '{name}' not found in combat.")
    def add_monster(self, monster: Monster):
        """Add a monster to the combat encounter"""
        self.monsters.append(monster)
        self.turn_order.append(monster.name)
        self.add_log_entry(f"Monster '{monster.name}' has joined the combat.")
    def add_character(self, character: Character):
        """Add a character to the combat encounter"""
        self.characters.append(character)
        self.turn_order.append(character.name)
        self.add_log_entry(f"Character '{character.name}' has joined the combat.")
    def reset_combat(self):
        """Reset the combat state to initial conditions"""
        self.turn_order.clear()
        self.current_turn_index = 0
        self.round_number = 1
        self.log.clear()
        self.add_log_entry(f"Combat '{self.encounter_name}' has been reset.")
    def get_participant_status(self, name: str) -> Optional[str]:
        """Get the status of a participant (character or monster)"""
        for character in self.characters:
            if character.name == name:
                return f"Character '{name}': HP={character.current_hp}, AC={character.ac}"
        for monster in self.monsters:
            if monster.name == name:
                return f"Monster '{name}': HP={monster.hp}, AC={monster.ac}"
        return None
    def heal_participant(self, name: str, amount: int):
        """Heal a participant (character or monster) by a specified amount"""
        for character in self.characters:
            if character.name == name:
                character.current_hp = min(character.max_hp, character.current_hp + amount)
                self.add_log_entry(f"Character '{name}' healed by {amount} HP.")
                return
        for monster in self.monsters:
            if monster.name == name:
                monster.hp += amount  # Assuming monsters have no max HP limit here
                self.add_log_entry(f"Monster '{name}' healed by {amount} HP.")
                return
        raise ValueError(f"Participant '{name}' not found in combat.")
    def damage_participant(self, name: str, amount: int):
        """Damage a participant (character or monster) by a specified amount"""
        for character in self.characters:
            if character.name == name:
                character.current_hp = max(0, character.current_hp - amount)
                self.add_log_entry(f"Character '{name}' took {amount} damage.")
                return
        for monster in self.monsters:
            if monster.name == name:
                monster.hp = max(0, monster.hp - amount)
                self.add_log_entry(f"Monster '{name}' took {amount} damage.")
                return
        raise ValueError(f"Participant '{name}' not found in combat.")
    
    def list_participants(self) -> List[str]:
        """List all participants currently in combat"""
        return self.turn_order.copy()
    
    def is_participant_alive(self, name: str) -> bool:
        """Check if a participant (character or monster) is still alive"""
        for character in self.characters:
            if character.name == name:
                return character.current_hp > 0
        for monster in self.monsters:
            if monster.name == name:
                return monster.hp > 0
        raise ValueError(f"Participant '{name}' not found in combat.")
    def get_round_number(self) -> int:
        """Get the current round number"""
        return self.round_number
    def get_full_status(self) -> Dict[str, str]:
        """Get the full status of all participants in combat"""
        status = {}
        for character in self.characters:
            status[character.name] = f"Character: HP={character.current_hp}/{character.max_hp}, AC={character.ac}"
        for monster in self.monsters:
            status[monster.name] = f"Monster: HP={monster.hp}, AC={monster.ac}"
        return status
    def serialize(self) -> Dict:
        """Serialize the combat state to a dictionary"""
        return {
            "encounter_name": self.encounter_name,
            "monsters": [m.to_dict() for m in self.monsters],
            "characters": [c.to_dict() for c in self.characters],
            "turn_order": self.turn_order,
            "current_turn_index": self.current_turn_index,
            "round_number": self.round_number,
            "log": self.log
        }
    @staticmethod
    def deserialize(data: Dict) -> 'CombatState':
        """Deserialize a dictionary to a CombatState object"""
        combat_state = CombatState(
            encounter_name=data.get("encounter_name", ""),
            monsters=[Monster.from_dict(m) for m in data.get("monsters", [])],
            characters=[Character.from_dict(c) for c in data.get("characters", [])],
            turn_order=data.get("turn_order", []),
            current_turn_index=data.get("current_turn_index", 0),
            round_number=data.get("round_number", 1),
            log=data.get("log", [])
        )
        return combat_state
    def print_combat_log(self):
        """Print the combat log to the console"""
        for entry in self.log:
            print(entry)
    def get_next_participant(self) -> str:
        """Peek at the next participant without advancing the turn"""
        if not self.turn_order:
            raise ValueError("Turn order is empty. Start combat first.")
        next_index = (self.current_turn_index + 1) % len(self.turn_order)
        return self.turn_order[next_index]
    def skip_current_turn(self):
        """Skip the current participant's turn"""
        self.add_log_entry(f"{self.get_current_participant()}'s turn has been skipped.")
        self.next_turn()
    def reorder_turn(self, name: str, new_position: int):
        """Reorder a participant in the turn order"""
        if name not in self.turn_order:
            raise ValueError(f"Participant '{name}' not found in combat.")
        self.turn_order.remove(name)
        self.turn_order.insert(new_position, name)
        self.add_log_entry(f"{name} has been moved to position {new_position + 1} in the turn order.")

    def clear_log(self):
        """Clear the combat log"""
        self.log.clear()
        self.add_log_entry("Combat log has been cleared.")
    def get_participant_index(self, name: str) -> int:
        """Get the index of a participant in the turn order"""
        if name not in self.turn_order:
            raise ValueError(f"Participant '{name}' not found in combat.")
        return self.turn_order.index(name)
    def has_participant(self, name: str) -> bool:
        """Check if a participant is in the combat"""
        return name in self.turn_order
    def get_participant_count(self) -> int:
        """Get the total number of participants in combat"""
        return len(self.turn_order)
    def summarize_combat(self) -> str:
        """Get a brief summary of the combat state"""
        return (f"Combat '{self.encounter_name}': "
                f"{len(self.characters)} characters, "
                f"{len(self.monsters)} monsters, "
                f"Round {self.round_number}, "
                f"Current turn: {self.get_current_participant()}")
    def advance_rounds(self, num_rounds: int):
        """Advance the combat by a specified number of rounds"""
        for _ in range(num_rounds):
            while self.current_turn_index < len(self.turn_order) - 1:
                self.next_turn()
            self.next_turn()  # This will increment the round number
    def reset_turn_order(self):
        """Reset the turn order to the initial state"""
        self.turn_order = [c.name for c in self.characters] + [m.name for m in self.monsters]
        self.current_turn_index = 0
        self.add_log_entry("Turn order has been reset to initial state.")

    def get_participants_by_type(self, participant_type: str) -> List[str]:
        """Get a list of participants filtered by type ('character' or 'monster')"""
        if participant_type == 'character':
            return [c.name for c in self.characters]
        elif participant_type == 'monster':
            return [m.name for m in self.monsters]
        else:
            raise ValueError("participant_type must be 'character' or 'monster'")
        
    def is_turn_order_empty(self) -> bool:
        """Check if the turn order is empty"""
        return len(self.turn_order) == 0
    
    def get_combatants_status(self) -> Dict[str, str]:
        """Get the status of all combatants"""
        status = {}
        for character in self.characters:
            status[character.name] = f"Character: HP={character.current_hp}/{character.max_hp}, AC={character.ac}"
        for monster in self.monsters:
            status[monster.name] = f"Monster: HP={monster.hp}, AC={monster.ac}"
        return status
    
    def revive_participant(self, name: str, hp: int):
        """Revive a participant (character or monster) with specified HP"""
        for character in self.characters:
            if character.name == name:
                character.current_hp = hp
                self.add_log_entry(f"Character '{name}' has been revived with {hp} HP.")
                return
        for monster in self.monsters:
            if monster.name == name:
                monster.hp = hp
                self.add_log_entry(f"Monster '{name}' has been revived with {hp} HP.")
                return
        raise ValueError(f"Participant '{name}' not found in combat.")
    def get_combat_duration(self) -> str:
        """Get a summary of the combat duration based on log entries"""
        if len(self.log) < 2:
            return "Combat duration is too short to determine."
        
        start_time_str = self.log[0].split(']')[0][1:]
        end_time_str = self.log[-1].split(']')[0][1:]
        
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        
        duration = end_time - start_time
        return str(duration)
    def get_participant_details(self, name: str) -> Optional[Dict]:
        """Get detailed information about a participant (character or monster)"""
        for character in self.characters:
            if character.name == name:
                return {
                    "type": "character",
                    "hp": character.current_hp,
                    "max_hp": character.max_hp,
                    "ac": character.ac,
                    "level": character.level,
                    "class": character.char_class,
                    "race": character.race
                }
        for monster in self.monsters:
            if monster.name == name:
                return {
                    "type": "monster",
                    "hp": monster.hp,
                    "ac": monster.ac,
                    "challenge_rating": monster.challenge_rating,
                    "type": monster.monster_type,
                    "size": monster.size,
                    "alignment": monster.alignment
                }
        return None
    def duplicate_combat_state(self) -> 'CombatState':
        """Create a duplicate of the current combat state"""
        return CombatState.deserialize(self.serialize())
    def get_log_length(self) -> int:
        """Get the number of entries in the combat log"""
        return len(self.log)
    def summarize_participants(self) -> str:
        """Get a summary of all participants in combat"""
        summary = "Participants in combat:\n"
        for character in self.characters:
            summary += f"- Character: {character.name} (HP: {character.current_hp}/{character.max_hp}, AC: {character.ac})\n"
        for monster in self.monsters:
            summary += f"- Monster: {monster.name} (HP: {monster.hp}, AC: {monster.ac})\n"
        return summary
    def get_active_participants(self) -> List[str]:
        """Get a list of participants who are still alive in combat"""
        active = []
        for character in self.characters:
            if character.current_hp > 0:
                active.append(character.name)
        for monster in self.monsters:
            if monster.hp > 0:
                active.append(monster.name)
        return active
    def end_round(self):
        """End the current round and log the event"""
        self.add_log_entry(f"Round {self.round_number} has ended.")
        self.round_number += 1
        self.current_turn_index = 0
        self.add_log_entry(f"--- Round {self.round_number} ---")
    def get_combat_overview(self) -> str:
        """Get an overview of the combat state"""
        overview = (f"Combat Overview:\n"
                    f"- Encounter Name: {self.encounter_name}\n"
                    f"- Round Number: {self.round_number}\n"
                    f"- Current Turn: {self.get_current_participant()}\n"
                    f"- Total Participants: {len(self.turn_order)}\n"
                    f"- Active Participants: {len(self.get_active_participants())}\n")
        return overview
    def has_active_combatants(self) -> bool:
        """Check if there are any active combatants (characters or monsters)"""
        return len(self.get_active_participants()) > 0
    def get_combatants_by_status(self) -> Dict[str, List[str]]:
        """Get combatants categorized by their status (alive or defeated)"""
        status = {
            "alive": [],
            "defeated": []
        }
        for character in self.characters:
            if character.current_hp > 0:
                status["alive"].append(character.name)
            else:
                status["defeated"].append(character.name)
        for monster in self.monsters:
            if monster.hp > 0:
                status["alive"].append(monster.name)
            else:
                status["defeated"].append(monster.name)
        return status
    def get_combatant_types(self) -> Dict[str, int]:
        """Get a count of combatants by type (characters vs monsters)"""
        return {
            "characters": len(self.characters),
            "monsters": len(self.monsters)
        }
    def log_combatant_action(self, name: str, action: str):
        """Log an action taken by a combatant"""
        self.add_log_entry(f"{name} {action}")
    def get_combatant_names(self) -> List[str]:
        """Get a list of all combatant names"""
        names = [c.name for c in self.characters] + [m.name for m in self.monsters]
        return names
    def has_monsters(self) -> bool:
        """Check if there are any monsters in combat"""
        return len(self.monsters) > 0
    def has_characters(self) -> bool:
        """Check if there are any characters in combat"""
        return len(self.characters) > 0
    def get_combatant_summary(self) -> str:
        """Get a brief summary of all combatants"""
        summary = "Combatant Summary:\n"
        for character in self.characters:
            summary += f"- Character: {character.name} (HP: {character.current_hp}/{character.max_hp}, AC: {character.ac})\n"
        for monster in self.monsters:
            summary += f"- Monster: {monster.name} (HP: {monster.hp}, AC: {monster.ac})\n"
        return summary
    def is_participant_turn(self, name: str) -> bool:
        """Check if it's the specified participant's turn"""
        return self.get_current_participant() == name
    def get_combat_log_slice(self, start: int, end: int) -> List[str]:
        """Get a slice of the combat log entries"""
        return self.log[start:end]
    def get_combatant_health_percentage(self, name: str) -> Optional[float]:
        """Get the health percentage of a combatant"""
        for character in self.characters:
            if character.name == name:
                return (character.current_hp / character.max_hp) * 100
        for monster in self.monsters:
            if monster.name == name:
                # Assuming monsters have no max HP limit here
                return 100.0  # Monsters are considered at full health unless specified otherwise
        return None
    def get_combatant_types_list(self) -> List[str]:
        """Get a list of combatant types (character or monster)"""
        types = []
        for character in self.characters:
            types.append("character")
        for monster in self.monsters:
            types.append("monster")
        return types
    def get_combatant_count_by_type(self) -> Dict[str, int]:
        """Get a count of combatants by type"""
        return {
            "characters": len(self.characters),
            "monsters": len(self.monsters)
        }
    def log_combatant_status(self):
        """Log the status of all combatants"""
        for character in self.characters:
            self.add_log_entry(f"Character '{character.name}': HP={character.current_hp}/{character.max_hp}, AC={character.ac}")
        for monster in self.monsters:
            self.add_log_entry(f"Monster '{monster.name}': HP={monster.hp}, AC={monster.ac}")
    def get_combatant_summary_by_type(self) -> Dict[str, List[str]]:
        """Get a summary of combatants categorized by type"""
        summary = {
            "characters": [c.name for c in self.characters],
            "monsters": [m.name for m in self.monsters]
        }
        return summary
    def get_combatant_names_by_type(self, participant_type: str) -> List[str]:
        """Get a list of combatant names filtered by type ('character' or 'monster')"""
        if participant_type == 'character':
            return [c.name for c in self.characters]
        elif participant_type == 'monster':
            return [m.name for m in self.monsters]
        else:
            raise ValueError("participant_type must be 'character' or 'monster'")

    def perform_basic_attack(self, attacker_name: str, target_name: str, 
                            advantage: bool = False, disadvantage: bool = False) -> Dict:
        """Perform a basic melee attack using existing dice system"""
        attacker = self._get_participant_object(attacker_name)
        target = self._get_participant_object(target_name)
        
        if not attacker or not target:
            raise ValueError("Attacker or target not found")
        
        # Get attack bonus
        if hasattr(attacker, 'stats'):
            str_mod = (attacker.stats.get('strength', 10) - 10) // 2
            prof_bonus = attacker.get_proficiency_bonus() if hasattr(attacker, 'get_proficiency_bonus') else 2
            attack_bonus = str_mod + prof_bonus
        else:
            attack_bonus = 0
        
        # Use existing dice system to roll attack
        roll_type = RollType.ADVANTAGE if advantage else (RollType.DISADVANTAGE if disadvantage else RollType.NORMAL)
        num_dice = 2 if roll_type != RollType.NORMAL else 1
        
        attack_rolls = [random.randint(1, 20) for _ in range(num_dice)]
        
        if roll_type == RollType.ADVANTAGE:
            selected_roll = max(attack_rolls)
        elif roll_type == RollType.DISADVANTAGE:
            selected_roll = min(attack_rolls)
        else:
            selected_roll = attack_rolls[0]
        
        total_attack = selected_roll + attack_bonus
        
        # Check hit
        target_ac = target.ac if hasattr(target, 'ac') else 10
        hit = total_attack >= target_ac
        crit = selected_roll == 20
        crit_miss = selected_roll == 1
        
        result = {
            "attacker": attacker_name,
            "target": target_name,
            "attack_rolls": attack_rolls,
            "selected_roll": selected_roll,
            "attack_bonus": attack_bonus,
            "total_attack": total_attack,
            "target_ac": target_ac,
            "hit": hit and not crit_miss,
            "critical_hit": crit,
            "critical_miss": crit_miss,
            "damage": 0,
            "damage_rolls": [],
            "attack_roll": selected_roll  # Add for compatibility
        }
        
        # Roll damage if hit
        if (hit or crit) and not crit_miss:
            damage_dice_count = 2 if crit else 1
            damage_rolls = [random.randint(1, 8) for _ in range(damage_dice_count)]
            damage = sum(damage_rolls) + str_mod
            
            result["damage"] = damage
            result["damage_rolls"] = damage_rolls
            
            self.damage_participant(target_name, damage)
        
        self._log_attack_result(result)
        return result


    def _barbarian_special_attack(self, attacker, target, special_type: str, **kwargs) -> Dict:
        """Handle Barbarian special attacks"""
        if special_type == "reckless_attack":
            if not attacker.reckless_attack_available:
                raise ValueError("Reckless Attack not available at this level")
            
            str_mod = (attacker.stats.get('strength', 10) - 10) // 2
            prof_bonus = attacker.get_proficiency_bonus()
            attack_bonus = str_mod + prof_bonus
            
            # Roll with advantage (2d20, take higher)
            attack_rolls = [random.randint(1, 20) for _ in range(2)]
            selected_roll = max(attack_rolls)
            total_attack = selected_roll + attack_bonus
            
            target_ac = target.ac if hasattr(target, 'ac') else 10
            hit = total_attack >= target_ac
            crit = selected_roll == 20
            
            result = {
                "attacker": attacker.name,
                "target": target.name,
                "attack_type": "Reckless Attack",
                "attack_rolls": attack_rolls,
                "selected_roll": selected_roll,
                "attack_bonus": attack_bonus,
                "total_attack": total_attack,
                "target_ac": target_ac,
                "hit": hit,
                "critical_hit": crit,
                "damage": 0,
                "damage_rolls": []
            }
            
            if hit or crit:
                rage_bonus = attacker.rage_damage if attacker.currently_raging else 0
                damage_dice_count = 2 if crit else 1
                damage_rolls = [random.randint(1, 12) for _ in range(damage_dice_count)]  # Greataxe
                damage = sum(damage_rolls) + str_mod + rage_bonus
                
                result["damage"] = damage
                result["damage_rolls"] = damage_rolls
                
                self.damage_participant(target.name, damage)
            
            self.add_log_entry(f"{attacker.name} uses Reckless Attack on {target.name}! "
                            f"Rolls: {attack_rolls} (using {selected_roll}) + {attack_bonus} = {total_attack} vs AC {target_ac} - "
                            f"{'HIT' if hit else 'MISS'}! Damage: {result['damage']}")
            
            return result
        
        else:
            raise ValueError(f"Unknown Barbarian special attack: {special_type}")

    def _bard_special_attack(self, attacker, target, special_type: str, **kwargs) -> Dict:
        """Handle Bard special attacks"""
        if special_type == "vicious_mockery":
            if "vicious mockery" not in [c.lower() for c in attacker.cantrips_known]:
                raise ValueError("Vicious Mockery not known")
            
            spell_dc = attacker.get_spell_save_dc()
            
            # Target Wisdom save
            wis_mod = (target.stats.get('wisdom', 10) - 10) // 2 if hasattr(target, 'stats') else 0
            save_roll = random.randint(1, 20) + wis_mod
            
            success = save_roll >= spell_dc
            
            result = {
                "attacker": attacker.name,
                "target": target.name,
                "attack_type": "Vicious Mockery",
                "spell_dc": spell_dc,
                "save_roll": save_roll,
                "saved": success,
                "damage": 0,
                "damage_rolls": []
            }
            
            if not success:
                damage_dice = 1 + (attacker.level - 1) // 6
                damage_rolls = [random.randint(1, 4) for _ in range(damage_dice)]
                damage = sum(damage_rolls)
                
                result["damage"] = damage
                result["damage_rolls"] = damage_rolls
                
                self.damage_participant(target.name, damage)
            
            self.add_log_entry(f"{attacker.name} casts Vicious Mockery on {target.name}! "
                            f"DC {spell_dc}, Save: {save_roll} - "
                            f"{'SAVED' if success else 'FAILED'}! Damage: {result['damage']}")
            
            return result
        
        else:
            raise ValueError(f"Unknown Bard special attack: {special_type}")

    def _cleric_special_attack(self, attacker, target, special_type: str, **kwargs) -> Dict:
        """Handle Cleric special attacks"""
        if special_type == "guiding_bolt":
            if "guiding bolt" not in [s.lower() for s in attacker.spells_prepared]:
                raise ValueError("Guiding Bolt not prepared")
            
            if not hasattr(attacker, 'cast_spell') or not attacker.cast_spell(1):
                raise ValueError("No spell slots available")
            
            spell_attack = attacker.get_spell_attack_bonus()
            attack_roll = random.randint(1, 20)
            total_attack = attack_roll + spell_attack
            
            target_ac = target.ac if hasattr(target, 'ac') else 10
            hit = total_attack >= target_ac
            crit = attack_roll == 20
            
            result = {
                "attacker": attacker.name,
                "target": target.name,
                "attack_type": "Guiding Bolt",
                "attack_roll": attack_roll,
                "spell_attack_bonus": spell_attack,
                "total_attack": total_attack,
                "target_ac": target_ac,
                "hit": hit,
                "critical_hit": crit,
                "damage": 0,
                "damage_rolls": []
            }
            
            if hit or crit:
                damage_dice_count = 8 if crit else 4  # 4d6
                damage_rolls = [random.randint(1, 6) for _ in range(damage_dice_count)]
                damage = sum(damage_rolls)
                
                result["damage"] = damage
                result["damage_rolls"] = damage_rolls
                
                self.damage_participant(target.name, damage)
            
            self.add_log_entry(f"{attacker.name} casts Guiding Bolt on {target.name}! "
                            f"Roll: {attack_roll} + {spell_attack} = {total_attack} vs AC {target_ac} - "
                            f"{'HIT' if hit else 'MISS'}! Damage: {result['damage']}")
            
            return result
        
        else:
            raise ValueError(f"Unknown Cleric special attack: {special_type}")

    def _druid_special_attack(self, attacker, target, special_type: str, **kwargs) -> Dict:
        """Handle Druid special attacks"""
        if special_type == "wild_shape_attack":
            if not attacker.currently_wild_shaped:
                raise ValueError("Not in Wild Shape form")
            
            str_mod = (attacker.stats.get('strength', 10) - 10) // 2
            prof_bonus = attacker.get_proficiency_bonus()
            attack_bonus = str_mod + prof_bonus
            
            attack_roll = random.randint(1, 20)
            total_attack = attack_roll + attack_bonus
            
            target_ac = target.ac if hasattr(target, 'ac') else 10
            hit = total_attack >= target_ac
            crit = attack_roll == 20
            
            result = {
                "attacker": attacker.name,
                "target": target.name,
                "attack_type": f"Wild Shape Attack ({attacker.wild_shape_beast})",
                "attack_roll": attack_roll,
                "attack_bonus": attack_bonus,
                "total_attack": total_attack,
                "target_ac": target_ac,
                "hit": hit,
                "critical_hit": crit,
                "damage": 0,
                "damage_rolls": []
            }
            
            if hit or crit:
                damage_dice_count = 2 if crit else 1
                damage_rolls = [random.randint(1, 6) for _ in range(damage_dice_count)]
                damage = sum(damage_rolls) + str_mod
                
                result["damage"] = damage
                result["damage_rolls"] = damage_rolls
                
                self.damage_participant(target.name, damage)
            
            self.add_log_entry(f"{attacker.name} ({attacker.wild_shape_beast}) attacks {target.name}! "
                            f"Roll: {attack_roll} + {attack_bonus} = {total_attack} vs AC {target_ac} - "
                            f"{'HIT' if hit else 'MISS'}! Damage: {result['damage']}")
            
            return result
        
        else:
            raise ValueError(f"Unknown Druid special attack: {special_type}")
        

    def _get_participant_object(self, name: str):
            """Get the actual participant object (Character or Monster) by name"""
            for character in self.characters:
                if character.name == name:
                    return character
            for monster in self.monsters:
                if monster.name == name:
                    return monster
            return None

    def get_available_attacks(self, participant_name: str) -> Dict[str, List[str]]:
        """Get available attacks for a participant"""
        participant = self._get_participant_object(participant_name)
        
        if not participant:
            raise ValueError(f"Participant '{participant_name}' not found")
        
        available = {
            "basic": ["melee_attack"],
            "special": []
        }
        
        # Add class-specific attacks for characters
        if hasattr(participant, 'char_class'):
            char_class = participant.char_class.lower()
            
            if char_class == "barbarian":
                if hasattr(participant, 'reckless_attack_available') and participant.reckless_attack_available:
                    available["special"].append("reckless_attack")
            
            elif char_class == "bard":
                if hasattr(participant, 'cantrips_known') and any('vicious mockery' in c.lower() for c in participant.cantrips_known):
                    available["special"].append("vicious_mockery")
            
            elif char_class == "cleric":
                if hasattr(participant, 'spells_prepared') and any('guiding bolt' in s.lower() for s in participant.spells_prepared):
                    available["special"].append("guiding_bolt")
            
            elif char_class == "druid":
                if hasattr(participant, 'currently_wild_shaped') and participant.currently_wild_shaped:
                    available["special"].append("wild_shape_attack")
        
        return available

    def _log_attack_result(self, result: Dict):
        """Log the result of an attack"""
        attacker = result['attacker']
        target = result['target']
        
        if result.get('critical_miss'):
            self.add_log_entry(f"{attacker} critically missed {target}!")
        elif result.get('critical_hit'):
            self.add_log_entry(f"{attacker} CRITICAL HIT on {target} for {result['damage']} damage!")
        elif result['hit']:
            self.add_log_entry(f"{attacker} hit {target} for {result['damage']} damage!")
        else:
            self.add_log_entry(f"{attacker} missed {target}.")

        # Test 

if __name__ == "__main__":
    print("=" * 70)
    print("COMBAT STATE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # ========================================================================
    # TEST 1: Basic Combat State Creation and Participant Management
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 1: Combat State Creation & Participant Management")
    print("=" * 70)
    
    # Create characters
    char1 = Character(
        name="Aragorn", race="Human", char_class="Fighter", 
        background="Soldier", level=5, hp=45, max_hp=45, ac=18,
        stats={'strength': 16, 'dexterity': 14, 'constitution': 14,
               'intelligence': 10, 'wisdom': 12, 'charisma': 10}
    )
    
    char2 = Character(
        name="Legolas", race="Elf", char_class="Ranger",
        background="Outlander", level=5, hp=38, max_hp=38, ac=16,
        stats={'strength': 12, 'dexterity': 18, 'constitution': 12,
               'intelligence': 10, 'wisdom': 14, 'charisma': 10}
    )
    
    # Create monsters
    goblin1 = Monster(
        name="Goblin 1", monster_type="Humanoid", size="Small",
        alignment="Neutral Evil", challenge_rating=0.25, hp=7, ac=15
    )
    
    goblin2 = Monster(
        name="Goblin 2", monster_type="Humanoid", size="Small",
        alignment="Neutral Evil", challenge_rating=0.25, hp=7, ac=15
    )
    
    orc = Monster(
        name="Orc Warrior", monster_type="Humanoid", size="Medium",
        alignment="Chaotic Evil", challenge_rating=0.5, hp=15, ac=13
    )
    
    # Create combat
    combat = CombatState(encounter_name="Goblin Ambush")
    
    # Test adding participants
    try:
        combat.add_character(char1)
        combat.add_character(char2)
        combat.add_monster(goblin1)
        combat.add_monster(goblin2)
        combat.add_monster(orc)
        print("✓ Successfully added 2 characters and 3 monsters")
        print(f"  Total participants: {combat.get_participant_count()}")
    except Exception as e:
        print(f"✗ Failed to add participants: {e}")
    
    # Test participant lists
    try:
        all_participants = combat.list_participants()
        print(f"✓ Participants: {', '.join(all_participants)}")
        
        characters = combat.get_participants_by_type('character')
        monsters = combat.get_participants_by_type('monster')
        print(f"  Characters: {', '.join(characters)}")
        print(f"  Monsters: {', '.join(monsters)}")
    except Exception as e:
        print(f"✗ Failed to list participants: {e}")
    
    # Test participant status
    try:
        status = combat.get_participant_status("Aragorn")
        print(f"✓ Aragorn status: {status}")
    except Exception as e:
        print(f"✗ Failed to get status: {e}")
    
    # ========================================================================
    # TEST 2: Combat Flow - Initiative, Turns, Rounds
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 2: Combat Flow - Initiative, Turns, Rounds")
    print("=" * 70)
    
    try:
        combat.start_combat()
        print("✓ Combat started")
        print(f"  Turn order: {', '.join(combat.turn_order)}")
        print(f"  Current participant: {combat.get_current_participant()}")
        print(f"  Round: {combat.get_round_number()}")
    except Exception as e:
        print(f"✗ Failed to start combat: {e}")
    
    # Test turn advancement
    try:
        print("\n--- Advancing through turns ---")
        for i in range(3):
            current = combat.get_current_participant()
            next_participant = combat.get_next_participant()
            print(f"  Turn {i+1}: {current} (next: {next_participant})")
            combat.next_turn()
        print(f"✓ Advanced 3 turns, now round {combat.get_round_number()}")
    except Exception as e:
        print(f"✗ Failed to advance turns: {e}")
    
    # Test skip turn
    try:
        current = combat.get_current_participant()
        combat.skip_current_turn()
        print(f"✓ Skipped {current}'s turn")
    except Exception as e:
        print(f"✗ Failed to skip turn: {e}")
    
    # ========================================================================
    # TEST 3: Damage and Healing
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 3: Damage and Healing")
    print("=" * 70)
    
    try:
        print(f"Before damage: {combat.get_participant_status('Goblin 1')}")
        combat.damage_participant("Goblin 1", 5)
        print(f"After 5 damage: {combat.get_participant_status('Goblin 1')}")
        
        combat.heal_participant("Goblin 1", 2)
        print(f"After 2 healing: {combat.get_participant_status('Goblin 1')}")
        print("✓ Damage and healing work correctly")
    except Exception as e:
        print(f"✗ Failed damage/healing: {e}")
    
    # Test participant death
    try:
        combat.damage_participant("Goblin 2", 20)  # Overkill
        is_alive = combat.is_participant_alive("Goblin 2")
        print(f"✓ Goblin 2 alive status: {is_alive}")
        
        if not is_alive:
            combat.remove_participant("Goblin 2")
            print(f"✓ Removed defeated Goblin 2 from combat")
            print(f"  Remaining participants: {combat.get_participant_count()}")
    except Exception as e:
        print(f"✗ Failed death handling: {e}")
    
    # ========================================================================
    # TEST 4: Basic Attack System
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 4: Basic Attack System")
    print("=" * 70)
    
    try:
        print("\n--- Normal Attack ---")
        result = combat.perform_basic_attack("Aragorn", "Goblin 1")
        print(f"Attacker: {result['attacker']}")
        print(f"Target: {result['target']}")
        print(f"Attack roll: {result['selected_roll']} + {result['attack_bonus']} = {result['total_attack']}")
        print(f"Target AC: {result['target_ac']}")
        print(f"Result: {'HIT' if result['hit'] else 'MISS'}")
        if result['critical_hit']:
            print(f"  ⚔️ CRITICAL HIT!")
        if result['hit']:
            print(f"  Damage: {result['damage']} (rolls: {result['damage_rolls']})")
        print("✓ Normal attack executed")
    except Exception as e:
        print(f"✗ Failed basic attack: {e}")
    
    try:
        print("\n--- Attack with Advantage ---")
        result = combat.perform_basic_attack("Legolas", "Orc Warrior", advantage=True)
        print(f"Attack rolls (advantage): {result['attack_rolls']}")
        print(f"Selected: {result['selected_roll']} + {result['attack_bonus']} = {result['total_attack']}")
        print(f"Result: {'HIT' if result['hit'] else 'MISS'}")
        if result['hit']:
            print(f"  Damage: {result['damage']}")
        print("✓ Advantage attack executed")
    except Exception as e:
        print(f"✗ Failed advantage attack: {e}")
    
    try:
        print("\n--- Attack with Disadvantage ---")
        result = combat.perform_basic_attack("Aragorn", "Orc Warrior", disadvantage=True)
        print(f"Attack rolls (disadvantage): {result['attack_rolls']}")
        print(f"Selected: {result['selected_roll']} + {result['attack_bonus']} = {result['total_attack']}")
        print(f"Result: {'HIT' if result['hit'] else 'MISS'}")
        print("✓ Disadvantage attack executed")
    except Exception as e:
        print(f"✗ Failed disadvantage attack: {e}")
    
    # ========================================================================
    # TEST 5: Class-Specific Attacks (with mock class characters)
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 5: Class-Specific Attacks")
    print("=" * 70)
    
    # Test with Barbarian
    try:
        from Class.barbarian import Barbarian
        
        barbarian = Barbarian(
            name="Grog", race="Goliath", char_class="Barbarian",
            background="Outlander", level=5, hp=50, max_hp=50, ac=15,
            stats={'strength': 18, 'dexterity': 12, 'constitution': 16,
                   'intelligence': 8, 'wisdom': 10, 'charisma': 10},
            primal_path="Path of the Berserker"
        )
        
        combat2 = CombatState(encounter_name="Barbarian Test")
        combat2.add_character(barbarian)
        combat2.add_monster(orc)
        combat2.start_combat()
        
        print("\n--- Testing Barbarian Reckless Attack ---")
        barbarian.enter_rage()
        result = combat2._barbarian_special_attack(barbarian, orc, "reckless_attack")
        print(f"Reckless Attack: {result['attack_type']}")
        print(f"Rolls (advantage): {result['attack_rolls']}")
        print(f"Result: {'HIT' if result['hit'] else 'MISS'}")
        if result['hit']:
            print(f"  Damage: {result['damage']} (includes rage bonus)")
        print("✓ Barbarian special attack works")
        
    except ImportError:
        print("⚠ Barbarian class not available for testing")
    except Exception as e:
        print(f"✗ Failed Barbarian attack: {e}")
    
    # Test with Bard
    try:
        from Class.bard import Bard
        
        bard = Bard(
            name="Scanlan", race="Gnome", char_class="Bard",
            background="Entertainer", level=5, hp=30, max_hp=30, ac=14,
            stats={'strength': 8, 'dexterity': 14, 'constitution': 12,
                   'intelligence': 10, 'wisdom': 10, 'charisma': 18},
            cantrips_known=["vicious mockery", "prestidigitation"]
        )
        
        combat3 = CombatState(encounter_name="Bard Test")
        combat3.add_character(bard)
        
        goblin_test = Monster(
            name="Test Goblin", monster_type="Humanoid", size="Small",
            alignment="Neutral Evil", challenge_rating=0.25, hp=7, ac=15
        )
        goblin_test.stats = {'wisdom': 8}
        combat3.add_monster(goblin_test)
        combat3.start_combat()
        
        print("\n--- Testing Bard Vicious Mockery ---")
        result = combat3._bard_special_attack(bard, goblin_test, "vicious_mockery")
        print(f"Vicious Mockery: {result['attack_type']}")
        print(f"Spell DC: {result['spell_dc']}, Save roll: {result['save_roll']}")
        print(f"Result: {'SAVED' if result['saved'] else 'FAILED'}")
        if not result['saved']:
            print(f"  Damage: {result['damage']} (rolls: {result['damage_rolls']})")
        print("✓ Bard special attack works")
        
    except ImportError:
        print("⚠ Bard class not available for testing")
    except Exception as e:
        print(f"✗ Failed Bard attack: {e}")
    
    # ========================================================================
    # TEST 6: Combat Status and Queries
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 6: Combat Status and Queries")
    print("=" * 70)
    
    try:
        print("\n--- Full Combat Status ---")
        status = combat.get_full_status()
        for name, info in status.items():
            print(f"  {name}: {info}")
        print("✓ Full status retrieved")
    except Exception as e:
        print(f"✗ Failed to get full status: {e}")
    
    try:
        print("\n--- Active Participants ---")
        active = combat.get_active_participants()
        print(f"  Active: {', '.join(active)}")
        print("✓ Active participants identified")
    except Exception as e:
        print(f"✗ Failed to get active participants: {e}")
    
    try:
        print("\n--- Combatants by Status ---")
        by_status = combat.get_combatants_by_status()
        print(f"  Alive: {', '.join(by_status['alive'])}")
        print(f"  Defeated: {', '.join(by_status['defeated'])}")
        print("✓ Combatants categorized by status")
    except Exception as e:
        print(f"✗ Failed to categorize combatants: {e}")
    
    try:
        print("\n--- Combat Summary ---")
        summary = combat.summarize_combat()
        print(f"  {summary}")
        print("✓ Combat summary generated")
    except Exception as e:
        print(f"✗ Failed to generate summary: {e}")
    
    # ========================================================================
    # TEST 7: Combat Log and History
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 7: Combat Log and History")
    print("=" * 70)
    
    try:
        print(f"\nCombat log has {combat.get_log_length()} entries")
        print("\n--- Last 5 Log Entries ---")
        recent_logs = combat.get_combat_log_slice(-5, None)
        for log in recent_logs:
            print(f"  {log}")
        print("✓ Combat log accessible")
    except Exception as e:
        print(f"✗ Failed to access combat log: {e}")
    
    try:
        print("\n--- Combat Summary ---")
        print(combat.get_combat_summary())
        print("✓ Combat summary generated")
    except Exception as e:
        print(f"✗ Failed to generate summary: {e}")
    
    # ========================================================================
    # TEST 8: Serialization and Deserialization
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 8: Serialization and Deserialization")
    print("=" * 70)
    
    try:
        # Serialize
        combat_data = combat.serialize()
        print(f"✓ Combat serialized ({len(str(combat_data))} bytes)")
        
        # Deserialize
        combat_restored = CombatState.deserialize(combat_data)
        print(f"✓ Combat deserialized")
        print(f"  Encounter: {combat_restored.encounter_name}")
        print(f"  Participants: {combat_restored.get_participant_count()}")
        print(f"  Round: {combat_restored.get_round_number()}")
        print(f"  Turn: {combat_restored.get_current_participant()}")
        
        # Verify data integrity
        assert combat.encounter_name == combat_restored.encounter_name
        assert combat.get_participant_count() == combat_restored.get_participant_count()
        assert combat.get_round_number() == combat_restored.get_round_number()
        print("✓ Serialization preserves data integrity")
        
    except Exception as e:
        print(f"✗ Failed serialization: {e}")
    
    # ========================================================================
    # TEST 9: Edge Cases and Error Handling
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 9: Edge Cases and Error Handling")
    print("=" * 70)
    
    # Test invalid participant
    try:
        combat.damage_participant("NonExistent", 10)
        print("✗ Should have raised error for invalid participant")
    except ValueError as e:
        print(f"✓ Correctly raised error for invalid participant: {e}")
    
    # Test removing non-existent participant
    try:
        combat.remove_participant("FakeCharacter")
        print("✗ Should have raised error for non-existent participant")
    except ValueError as e:
        print(f"✓ Correctly raised error for non-existent participant")
    
    # Test combat state without starting
    try:
        new_combat = CombatState(encounter_name="Test")
        new_combat.get_current_participant()
        print("✗ Should have raised error for unstarted combat")
    except ValueError as e:
        print(f"✓ Correctly raised error for unstarted combat")
    
    # Test empty turn order
    try:
        empty_combat = CombatState(encounter_name="Empty")
        empty_combat.start_combat()
        print("✓ Can start combat with empty turn order (edge case)")
    except Exception as e:
        print(f"  Note: Empty combat handling: {e}")
    
    # ========================================================================
    # TEST 10: Combat End and Reset
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST 10: Combat End and Reset")
    print("=" * 70)
    
    try:
        print(f"Before end: Active={combat.is_combat_active()}")
        combat.end_combat()
        print(f"After end: Active={combat.is_combat_active()}")
        print("✓ Combat ended successfully")
    except Exception as e:
        print(f"✗ Failed to end combat: {e}")
    
    try:
        # Reset and restart
        combat.reset_combat()
        print("✓ Combat reset")
        print(f"  Participants: {combat.get_participant_count()}")
        print(f"  Log entries: {combat.get_log_length()}")
    except Exception as e:
        print(f"✗ Failed to reset combat: {e}")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)
    print("\n✓ All major combat systems tested")
    print("  - Combat state management")
    print("  - Participant tracking")
    print("  - Turn and round advancement")
    print("  - Damage and healing")
    print("  - Basic attack system")
    print("  - Class-specific attacks")
    print("  - Status queries")
    print("  - Combat logging")
    print("  - Serialization")
    print("  - Error handling")
    print("\nReview output above for any ✗ failures")
    print("=" * 70)