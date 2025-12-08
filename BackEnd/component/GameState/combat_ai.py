#!/usr/bin/env python3
"""
Combat AI System
Handles enemy decision-making and action selection
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AIAction:
    """Represents an AI-chosen action"""
    action_type: str  # 'attack', 'spell', 'ability'
    action_name: str
    target_id: str
    description: str
    data: Dict = None


class CombatAI:
    """
    AI controller for enemy actions in combat
    Makes intelligent decisions based on combat state
    """
    
    def __init__(self, combat_state):
        self.combat_state = combat_state
    
    def choose_action(self, enemy_participant_id: str) -> AIAction:
        """
        Choose the best action for an enemy
        
        Args:
            enemy_participant_id: The enemy making the decision
            
        Returns:
            AIAction with chosen action and target
        """
        enemy = self.combat_state.get_participant_by_id(enemy_participant_id)
        
        if not enemy:
            raise ValueError(f"Enemy {enemy_participant_id} not found")
        
        # Get available targets (living player characters)
        available_targets = [
            p for p in self.combat_state.participants
            if p.participant_type.value == 'character' and p.is_alive()
        ]
        
        if not available_targets:
            raise ValueError("No valid targets available")
        
        # Choose target based on strategy
        target = self.choose_target(enemy, available_targets)
        
        # Choose action based on monster abilities
        action = self.choose_action_type(enemy, target)
        
        return action
    
    def choose_target(self, enemy, available_targets) -> str:
        """
        Choose which player character to target
        
        Strategies:
        - Attack lowest HP (finishing blow)
        - Attack highest threat (damage dealers)
        - Random (chaos)
        """
        # Simple strategy: Target lowest HP percentage
        target = min(
            available_targets,
            key=lambda p: p.get_current_hp() / max(p.get_max_hp(), 1)
        )
        
        return target
    
    def choose_action_type(self, enemy, target) -> AIAction:
        """
        Choose what action to take
        
        For now: Simple melee attack
        Future: Consider monster abilities, spells, etc.
        """
        # Get monster's actions from entity
        monster = enemy.entity
        
        if hasattr(monster, 'actions') and monster.actions:
            # Use first available action (could be improved)
            action_name = monster.actions[0] if isinstance(monster.actions[0], str) else monster.actions[0].get('name', 'Attack')
        else:
            action_name = "Attack"
        
        return AIAction(
            action_type='attack',
            action_name=action_name,
            target_id=target.participant_id,
            description=f"{enemy.name} attacks {target.name}!",
            data={}
        )


class CombatActionResolver:
    """
    Resolves combat actions and calculates results
    """
    
    @staticmethod
    def resolve_attack(attacker, target, action_data: Dict = None) -> Dict:
        """
        Resolve a basic attack action
        
        Returns:
            Dict with result data for frontend
        """
        # Calculate attack roll (1d20 + modifiers)
        attack_roll = random.randint(1, 20)
        
        # Get attacker's attack bonus (simplified)
        attack_bonus = CombatActionResolver._get_attack_bonus(attacker)
        total_attack = attack_roll + attack_bonus
        
        # Get target's AC
        target_ac = target.get_ac()
        
        # Check for hit
        is_critical = attack_roll == 20
        is_miss = attack_roll == 1 or (total_attack < target_ac and not is_critical)
        
        if is_miss:
            return {
                'success': True,
                'hit': False,
                'message': f"{attacker.name} attacks {target.name} but misses! (Rolled {attack_roll})",
                'type': 'system',
                'attacker': attacker.name,
                'target': target.participant_id,
                'damage': 0,
                'new_hp': target.get_current_hp(),
                'max_hp': target.get_max_hp(),
                'target_defeated': False
            }
        
        # Calculate damage
        damage = CombatActionResolver._calculate_damage(attacker, is_critical)
        
        # Apply damage
        new_hp = max(0, target.entity.hp - damage)
        target.entity.hp = new_hp
        
        target_defeated = new_hp <= 0
        
        crit_text = " CRITICAL HIT!" if is_critical else ""
        
        return {
            'success': True,
            'hit': True,
            'critical': is_critical,
            'message': f"{attacker.name} attacks {target.name} for {damage} damage!{crit_text}",
            'type': 'damage',
            'attacker': attacker.name,
            'target': target.participant_id,
            'damage': damage,
            'new_hp': new_hp,
            'max_hp': target.get_max_hp(),
            'target_defeated': target_defeated,
            'attack_roll': attack_roll,
            'attack_bonus': attack_bonus,
            'total_attack': total_attack,
            'target_ac': target_ac
        }
    
    @staticmethod
    def resolve_defend(character) -> Dict:
        """
        Resolve a defend action (+2 AC until next turn)
        """
        # In a full implementation, you'd track this as a condition
        return {
            'success': True,
            'message': f"{character.name} takes a defensive stance!",
            'type': 'system',
            'character': character.name,
            'effect': 'defending'
        }
    
    @staticmethod
    def resolve_skill(character, skill_name: str, target, skill_data: Dict) -> Dict:
        """
        Resolve a character skill/ability
        
        Examples: Rage, Bardic Inspiration, Wild Shape, etc.
        """
        # Get character's class
        char_class = getattr(character.entity, 'char_class', 'Character')
        
        # Route to appropriate skill handler
        if char_class == 'Barbarian':
            return CombatActionResolver._resolve_barbarian_skill(character, skill_name, target, skill_data)
        elif char_class == 'Bard':
            return CombatActionResolver._resolve_bard_skill(character, skill_name, target, skill_data)
        elif char_class == 'Cleric':
            return CombatActionResolver._resolve_cleric_skill(character, skill_name, target, skill_data)
        elif char_class == 'Druid':
            return CombatActionResolver._resolve_druid_skill(character, skill_name, target, skill_data)
        else:
            return {
                'success': False,
                'error': f'Unknown skill: {skill_name} for class {char_class}'
            }
    
    # ========================================================================
    # CLASS-SPECIFIC SKILL HANDLERS
    # ========================================================================
    
    @staticmethod
    def _resolve_barbarian_skill(character, skill_name, target, skill_data):
        """Resolve Barbarian abilities"""
        barbarian = character.entity
        
        if skill_name == 'Rage':
            if barbarian.enter_rage():
                return {
                    'success': True,
                    'message': f"{character.name} enters a RAGE! 🔥",
                    'type': 'buff',
                    'character': character.name,
                    'effect': 'rage',
                    'resource_changes': {
                        'rage_used': barbarian.rages_used,
                        'currently_raging': barbarian.currently_raging
                    }
                }
            else:
                return {
                    'success': False,
                    'error': 'No rage uses remaining!'
                }
        
        elif skill_name == 'Reckless Attack':
            # Would set a flag for advantage on next attack
            return {
                'success': True,
                'message': f"{character.name} attacks recklessly!",
                'type': 'buff',
                'character': character.name,
                'effect': 'reckless_attack'
            }
        
        return {'success': False, 'error': f'Unknown Barbarian skill: {skill_name}'}
    
    @staticmethod
    def _resolve_bard_skill(character, skill_name, target, skill_data):
        """Resolve Bard abilities"""
        bard = character.entity
        
        if skill_name == 'Bardic Inspiration':
            if bard.use_bardic_inspiration():
                return {
                    'success': True,
                    'message': f"{character.name} grants Bardic Inspiration to {target.name}! ({bard.bardic_inspiration_die})",
                    'type': 'buff',
                    'character': character.name,
                    'target': target.participant_id,
                    'effect': 'bardic_inspiration',
                    'resource_changes': {
                        'bardic_inspiration_remaining': bard.bardic_inspiration_remaining
                    }
                }
            else:
                return {'success': False, 'error': 'No Bardic Inspiration uses remaining!'}
        
        elif skill_name.startswith('Spell:'):
            spell_name = skill_name.replace('Spell:', '').strip()
            spell_level = skill_data.get('level', 1)
            
            if bard.cast_spell(spell_level):
                # Simple healing spell example
                if 'heal' in spell_name.lower():
                    healing = random.randint(1, 8) + 3  # 1d8+3
                    target.entity.hp = min(target.entity.hp + healing, target.get_max_hp())
                    
                    return {
                        'success': True,
                        'message': f"{character.name} casts {spell_name} on {target.name}!",
                        'type': 'healing',
                        'character': character.name,
                        'target': target.participant_id,
                        'healing': healing,
                        'new_hp': target.entity.hp,
                        'max_hp': target.get_max_hp(),
                        'resource_changes': {
                            'spell_slots_used': bard.spell_slots_used
                        }
                    }
                
                # Damage spell
                else:
                    damage = random.randint(2, 8) * spell_level
                    target.entity.hp = max(0, target.entity.hp - damage)
                    
                    return {
                        'success': True,
                        'message': f"{character.name} casts {spell_name} on {target.name} for {damage} damage!",
                        'type': 'damage',
                        'character': character.name,
                        'target': target.participant_id,
                        'damage': damage,
                        'new_hp': target.entity.hp,
                        'max_hp': target.get_max_hp(),
                        'target_defeated': target.entity.hp <= 0,
                        'resource_changes': {
                            'spell_slots_used': bard.spell_slots_used
                        }
                    }
            else:
                return {'success': False, 'error': 'No spell slots remaining!'}
        
        return {'success': False, 'error': f'Unknown Bard skill: {skill_name}'}
    
    @staticmethod
    def _resolve_cleric_skill(character, skill_name, target, skill_data):
        """Resolve Cleric abilities"""
        cleric = character.entity
        
        # Ensure spell tracking attributes exist
        if not hasattr(cleric, 'spell_slots_used'):
            cleric.spell_slots_used = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        
        if not hasattr(cleric, 'spell_slots'):
            # Default spell slots for level 1 cleric
            cleric.spell_slots = {1: 2, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        
        if not hasattr(cleric, 'channel_divinity_used'):
            cleric.channel_divinity_used = 0
        
        if skill_name == 'Channel Divinity: Turn Undead':
            # Calculate max uses based on level
            level = getattr(cleric, 'level', 1)
            max_uses = 1 if level < 6 else (2 if level < 18 else 3)
            
            if cleric.channel_divinity_used < max_uses:
                cleric.channel_divinity_used += 1
                return {
                    'success': True,
                    'message': f"{character.name} channels divinity to turn undead!",
                    'type': 'effect',
                    'character': character.name,
                    'effect': 'turn_undead',
                    'resource_changes': {
                        'channel_divinity_used': cleric.channel_divinity_used
                    }
                }
            else:
                return {'success': False, 'error': 'No Channel Divinity uses remaining!'}
        
        elif skill_name.startswith('Spell:'):
            spell_name = skill_name.replace('Spell:', '').strip()
            spell_level = skill_data.get('spell_level', skill_data.get('level', 1))
            
            # Check if spell slot available
            used = cleric.spell_slots_used.get(spell_level, 0)
            max_slots = cleric.spell_slots.get(spell_level, 0)
            
            if used >= max_slots:
                return {'success': False, 'error': f'No level {spell_level} spell slots remaining!'}
            
            # Use spell slot
            cleric.spell_slots_used[spell_level] = used + 1
            
            # Get spell modifier (Wisdom for Clerics)
            wis_mod = 0
            if hasattr(cleric, 'stats') and isinstance(cleric.stats, dict):
                wis_score = cleric.stats.get('wisdom', 10)
                wis_mod = (wis_score - 10) // 2
            
            # Determine if healing or damage spell
            spell_type = skill_data.get('spell_type', 'damage')
            is_healing = spell_type == 'healing' or any(word in spell_name.lower() for word in ['heal', 'cure', 'restore'])
            
            if is_healing:
                # Healing spell
                import random
                healing = random.randint(1, 8) * spell_level + wis_mod
                
                # Disciple of Life bonus (Life domain feature)
                if hasattr(cleric, 'disciple_of_life') and cleric.disciple_of_life:
                    healing += 2 + spell_level
                
                old_hp = target.entity.hp
                target.entity.hp = min(target.entity.hp + healing, target.get_max_hp())
                actual_healing = target.entity.hp - old_hp
                
                return {
                    'success': True,
                    'message': f"{character.name} casts {spell_name} (Level {spell_level}) on {target.name}, healing {actual_healing} HP!",
                    'type': 'healing',
                    'character': character.name,
                    'target': target.participant_id or target.id,
                    'healing': actual_healing,
                    'new_hp': target.entity.hp,
                    'max_hp': target.get_max_hp(),
                    'spell_level': spell_level,
                    'resource_changes': {
                        'spell_slots_used': cleric.spell_slots_used
                    }
                }
            else:
                # Damage spell
                import random
                damage = sum(random.randint(1, 8) for _ in range(spell_level)) + wis_mod
                
                old_hp = target.entity.hp
                target.entity.hp = max(0, target.entity.hp - damage)
                actual_damage = old_hp - target.entity.hp
                
                return {
                    'success': True,
                    'message': f"{character.name} casts {spell_name} (Level {spell_level}) on {target.name} for {actual_damage} damage!",
                    'type': 'damage',
                    'character': character.name,
                    'target': target.participant_id or target.id,
                    'damage': actual_damage,
                    'new_hp': target.entity.hp,
                    'max_hp': target.get_max_hp(),
                    'target_defeated': target.entity.hp <= 0,
                    'spell_level': spell_level,
                    'resource_changes': {
                        'spell_slots_used': cleric.spell_slots_used
                    }
                }
        
        return {'success': False, 'error': f'Unknown Cleric skill: {skill_name}'}

    @staticmethod
    def _resolve_druid_skill(character, skill_name, target, skill_data):
        """Resolve Druid abilities"""
        druid = character.entity
        

        if not hasattr(druid, 'spell_slots_used'):
            druid.spell_slots_used = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        
        if not hasattr(druid, 'spell_slots'):
            druid.spell_slots = {1: 2, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        
        if not hasattr(druid, 'wild_shape_uses_remaining'):
            druid.wild_shape_uses_remaining = 2
        
        if not hasattr(druid, 'currently_wild_shaped'):
            druid.currently_wild_shaped = False

        if skill_name == 'Wild Shape':
            beast_name = skill_data.get('beast_name', 'Wolf')
            beast_hp = skill_data.get('beast_hp', 15)
            
            if druid.enter_wild_shape(beast_name, beast_hp):
                return {
                    'success': True,
                    'message': f"{character.name} transforms into a {beast_name}!",
                    'type': 'buff',
                    'character': character.name,
                    'effect': 'wild_shape',
                    'resource_changes': {
                        'wild_shape_uses_remaining': druid.wild_shape_uses_remaining,
                        'currently_wild_shaped': druid.currently_wild_shaped,
                        'wild_shape_beast': druid.wild_shape_beast
                    }
                }
            else:
                return {'success': False, 'error': 'No Wild Shape uses remaining!'}
        
        elif skill_name.startswith('Spell:'):
            spell_name = skill_name.replace('Spell:', '').strip()
            spell_level = skill_data.get('level', 1)
            
            # Similar to Cleric spell handling
            used = druid.spell_slots_used.get(spell_level, 0)
            max_slots = druid.spell_slots.get(spell_level, 0)
            
            if used < max_slots:
                druid.spell_slots_used[spell_level] = used + 1
                
                # Example: Cure Wounds
                if 'heal' in spell_name.lower() or 'cure' in spell_name.lower():
                    healing = random.randint(1, 8) + druid._get_modifier('wisdom')
                    target.entity.hp = min(target.entity.hp + healing, target.get_max_hp())
                    
                    return {
                        'success': True,
                        'message': f"{character.name} casts {spell_name} on {target.name} for {healing} HP!",
                        'type': 'healing',
                        'character': character.name,
                        'target': target.participant_id,
                        'healing': healing,
                        'new_hp': target.entity.hp,
                        'max_hp': target.get_max_hp(),
                        'resource_changes': {
                            'spell_slots_used': druid.spell_slots_used
                        }
                    }
                
                # Damage spell
                else:
                    damage = random.randint(2, 8) * spell_level
                    target.entity.hp = max(0, target.entity.hp - damage)
                    
                    return {
                        'success': True,
                        'message': f"{character.name} casts {spell_name} on {target.name} for {damage} damage!",
                        'type': 'damage',
                        'character': character.name,
                        'target': target.participant_id,
                        'damage': damage,
                        'new_hp': target.entity.hp,
                        'max_hp': target.get_max_hp(),
                        'target_defeated': target.entity.hp <= 0,
                        'resource_changes': {
                            'spell_slots_used': druid.spell_slots_used
                        }
                    }
            else:
                return {'success': False, 'error': f'No level {spell_level} spell slots remaining!'}
        
        return {'success': False, 'error': f'Unknown Druid skill: {skill_name}'}
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    @staticmethod
    def _get_attack_bonus(participant) -> int:
        """Calculate attack bonus for a participant"""
        entity = participant.entity
        
        if hasattr(entity, 'stats') and isinstance(entity.stats, dict):
            # Use STR modifier + proficiency bonus (simplified)
            str_score = entity.stats.get('strength', 10)
            str_mod = (str_score - 10) // 2
            
            # Get proficiency bonus
            if hasattr(entity, 'level'):
                prof_bonus = CombatActionResolver._get_proficiency_bonus(entity.level)
            else:
                prof_bonus = 2
            
            return str_mod + prof_bonus
        
        return 2  # Default
    
    @staticmethod
    def _get_proficiency_bonus(level: int) -> int:
        """Get proficiency bonus by level"""
        if level < 5:
            return 2
        elif level < 9:
            return 3
        elif level < 13:
            return 4
        elif level < 17:
            return 5
        else:
            return 6
    
    @staticmethod
    def _calculate_damage(attacker, is_critical: bool = False) -> int:
        """Calculate damage for an attack"""
        entity = attacker.entity
        
        # Base damage (1d8 for most weapons)
        base_dice = 1 if not is_critical else 2
        damage = sum(random.randint(1, 8) for _ in range(base_dice))
        
        # Add STR modifier
        if hasattr(entity, 'stats') and isinstance(entity.stats, dict):
            str_score = entity.stats.get('strength', 10)
            str_mod = (str_score - 10) // 2
            damage += str_mod
        
        # Add rage damage if Barbarian is raging
        if hasattr(entity, 'currently_raging') and entity.currently_raging:
            damage += entity.rage_damage
        
        return max(1, damage)