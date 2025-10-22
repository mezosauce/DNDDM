#!/usr/bin/env python3
"""
Enhanced AI DM Integration for Phase 3 (Active Campaign)
Properly routes queries to relevant SRD content for active gameplay
"""

from pathlib import Path
from typing import Dict, List, Optional
import re


class Phase3QueryRouter:
    """
    Smart query router for Phase 3 (Active Campaign)
    Maps player queries to relevant SRD files from packages 5-13
    """
    
    # Story phases 5-13 (Active Campaign)
    ACTIVE_PHASES = [
        "05_journey_and_exploration",
        "06_obstacles_and_challenges", 
        "07_confrontation_and_combat",
        "08_monsters_and_npcs",
        "09_crisis_and_setback",
        "10_magic_and_extraordinary_solutions",
        "11_climax_and_resolution",
        "12_aftermath_and_growth",
        "13_new_horizons"
    ]
    
    # Keyword mapping for active gameplay
    QUERY_PATTERNS = {
        # Combat queries (Phase 7)
        'combat': {
            'keywords': ['attack', 'fight', 'combat', 'hit', 'damage', 'weapon', 'strike', 
                        'battle', 'initiative', 'turn', 'action', 'bonus action'],
            'files': [
                '10_combat_basics/initiative.md',
                '10_combat_basics/actions_in_combat.md',
                '10_combat_basics/attack_rolls.md',
                '10_combat_basics/damage_and_healing.md',
                '10_combat_basics/movement_combat.md',
                '11_tactical_combat/conditions.md',
                '11_tactical_combat/special_attacks.md'
            ],
            'priority': 10
        },
        
        # Movement and exploration (Phase 5)
        'exploration': {
            'keywords': ['move', 'travel', 'explore', 'walk', 'run', 'climb', 'jump',
                        'search', 'look', 'investigate', 'perception', 'examine'],
            'files': [
                '06_travel/movement.md',
                '06_travel/environment_rules.md',
                '07_discovery/ability_checks.md',
                '07_discovery/investigation.md',
                '07_discovery/perception.md'
            ],
            'priority': 8
        },
        
        # Spellcasting (Phase 10)
        'magic': {
            'keywords': ['cast', 'spell', 'magic', 'cantrip', 'ritual', 'concentration',
                        'magic missile', 'fireball', 'heal', 'cure', 'enchant'],
            'files': [
                '14_spellcasting/magic_basics.md',
                '14_spellcasting/spell_slots.md',
                '14_spellcasting/concentration.md',
                '14_spellcasting/spell_lists/combat_spells.md',
                '14_spellcasting/spell_lists/utility_spells.md',
                '14_spellcasting/spell_lists/healing_spells.md'
            ],
            'priority': 9
        },
        
        # Monsters and NPCs (Phase 8)
        'monsters': {
            'keywords': ['monster', 'creature', 'enemy', 'foe', 'goblin', 'orc', 'dragon',
                        'undead', 'beast', 'npc', 'character', 'guard', 'merchant'],
            'files': [
                '12_monsters/monsters_by_cr.md',
                '12_monsters/monster_abilities.md',
                '12_monsters/legendary_creatures.md'
            ],
            'priority': 7
        },
        
        # Environmental hazards (Phase 6)
        'hazards': {
            'keywords': ['trap', 'hazard', 'poison', 'disease', 'fall', 'fire', 'lava',
                        'drowning', 'suffocate', 'exhaustion', 'tired', 'rest'],
            'files': [
                '08_environmental_hazards/traps.md',
                '08_environmental_hazards/hazards.md',
                '08_environmental_hazards/diseases_and_poisons.md',
                '08_environmental_hazards/exhaustion.md'
            ],
            'priority': 6
        },
        
        # Social interaction (Phase 6)
        'social': {
            'keywords': ['persuade', 'convince', 'talk', 'negotiate', 'intimidate', 
                        'deceive', 'lie', 'bluff', 'charm', 'diplomacy', 'conversation'],
            'files': [
                '07_discovery/social_interaction.md',
                '09_social_conflict/persuasion_deception.md',
                '09_social_conflict/npc_attitudes.md',
                '09_social_conflict/intimidation.md'
            ],
            'priority': 7
        },
        
        # Death and dying (Phase 9)
        'death': {
            'keywords': ['death', 'dying', 'unconscious', 'death save', 'stabilize',
                        'revive', 'resurrection', 'dead', 'killed'],
            'files': [
                '10_combat_basics/damage_and_healing.md',
                '13_consequences/death_and_dying.md',
                '13_consequences/exhaustion_stress.md'
            ],
            'priority': 10
        },
        
        # Magic items (Phase 10)
        'magic_items': {
            'keywords': ['magic item', 'artifact', 'enchanted', 'cursed', 'potion',
                        'scroll', 'wand', 'ring', 'sword', 'armor', 'treasure'],
            'files': [
                '15_magic_items/magic_items_by_rarity.md',
                '15_magic_items/artifacts.md',
                '15_magic_items/cursed_items.md'
            ],
            'priority': 5
        },
        
        # Boss encounters (Phase 11)
        'boss': {
            'keywords': ['boss', 'legendary', 'lair', 'lair action', 'legendary action',
                        'mythic', 'epic', 'final battle', 'climax'],
            'files': [
                '16_boss_encounters/legendary_actions.md',
                '16_boss_encounters/lair_actions.md',
                '16_boss_encounters/high_level_threats.md'
            ],
            'priority': 9
        },
        
        # Character advancement (Phase 12)
        'advancement': {
            'keywords': ['level up', 'experience', 'xp', 'advancement', 'grow stronger',
                        'learn', 'improve', 'feat', 'ability score'],
            'files': [
                '19_advancement/leveling_up.md',
                '19_advancement/experience_points.md',
                '05_learning_abilities/feats.md',
                '05_learning_abilities/class_features.md'
            ],
            'priority': 4
        },
        
        # Equipment and gear
        'equipment': {
            'keywords': ['equipment', 'gear', 'buy', 'sell', 'weapon', 'armor', 'tool',
                        'supplies', 'rations', 'rope', 'torch'],
            'files': [
                '04_equipping/equipment_full.md',
                '04_equipping/weapons.md',
                '04_equipping/armor.md',
                '04_equipping/adventuring_gear.md'
            ],
            'priority': 5
        },
        
        # Mounted combat
        'mounted': {
            'keywords': ['mount', 'horse', 'riding', 'mounted', 'vehicle', 'cart', 'wagon'],
            'files': [
                '06_travel/mounts_and_vehicles.md',
                '11_tactical_combat/mounted_combat.md'
            ],
            'priority': 6
        },
        
        # Tactical positioning
        'tactics': {
            'keywords': ['cover', 'hide', 'stealth', 'flank', 'position', 'advantage',
                        'disadvantage', 'obscured', 'concealed'],
            'files': [
                '11_tactical_combat/cover_and_concealment.md',
                '11_tactical_combat/conditions.md',
                '07_discovery/ability_checks.md'
            ],
            'priority': 7
        }
    }
    
    def __init__(self, srd_path: str = "./srd_story_cycle"):
        self.srd_path = Path(srd_path)
    
    def route_query(self, query: str, context: Dict = None) -> Dict:
        """
        Route a player query to relevant SRD files
        
        Args:
            query: Player's action or question
            context: Additional context (combat active, etc.)
            
        Returns:
            Dict with matched categories and files to load
        """
        query_lower = query.lower()
        matches = []
        
        # Check each pattern category
        for category, pattern_data in self.QUERY_PATTERNS.items():
            match_count = 0
            for keyword in pattern_data['keywords']:
                if keyword in query_lower:
                    match_count += 1
            
            if match_count > 0:
                matches.append({
                    'category': category,
                    'priority': pattern_data['priority'],
                    'match_count': match_count,
                    'files': pattern_data['files']
                })
        
        # Sort by priority and match count
        matches.sort(key=lambda x: (x['priority'], x['match_count']), reverse=True)
        
        # Context-based adjustments
        if context:
            if context.get('active_combat'):
                # Boost combat-related files during combat
                combat_files = self.QUERY_PATTERNS['combat']['files']
                matches.insert(0, {
                    'category': 'combat',
                    'priority': 10,
                    'match_count': 5,
                    'files': combat_files
                })
        
        # Collect unique files (preserve order)
        files_to_load = []
        seen = set()
        for match in matches[:3]:  # Top 3 categories
            for file in match['files']:
                if file not in seen:
                    files_to_load.append(file)
                    seen.add(file)
        
        # Always include reference files for quick lookup
        reference_files = [
            'ref_conditions_quick.md',
            'ref_actions_quick.md',
            'ref_common_dcs.md'
        ]
        
        for ref_file in reference_files:
            if ref_file not in seen:
                files_to_load.append(ref_file)
                seen.add(ref_file)
        
        return {
            'query': query,
            'matched_categories': [m['category'] for m in matches[:3]],
            'files_to_load': files_to_load[:8],  # Limit to 8 files max
            'context_used': context or {}
        }
    
    def get_context_description(self, routing_result: Dict) -> str:
        """Generate a human-readable description of what SRD content is being used"""
        categories = routing_result['matched_categories']
        if not categories:
            return "General gameplay"
        
        category_names = {
            'combat': 'Combat Rules',
            'exploration': 'Exploration & Movement',
            'magic': 'Spellcasting',
            'monsters': 'Creatures & NPCs',
            'hazards': 'Environmental Hazards',
            'social': 'Social Interaction',
            'death': 'Death & Dying',
            'magic_items': 'Magic Items',
            'boss': 'Legendary Encounters',
            'advancement': 'Character Growth',
            'equipment': 'Equipment & Gear',
            'mounted': 'Mounted Combat',
            'tactics': 'Tactical Combat'
        }
        
        used = [category_names.get(cat, cat) for cat in categories[:2]]
        return " & ".join(used)


class SRDContentLoader:
    """Load and combine SRD content files"""
    
    def __init__(self, srd_path: str = "./srd_story_cycle"):
        self.srd_path = Path(srd_path)
    
    def load_files(self, file_list: List[str], max_chars: int = 15000) -> str:
        """
        Load multiple SRD files and combine them
        
        Args:
            file_list: List of relative file paths
            max_chars: Maximum total characters to return
            
        Returns:
            Combined content string
        """
        content_parts = []
        total_chars = 0
        
        for file_path in file_list:
            full_path = self.srd_path / file_path
            
            if not full_path.exists():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Add file header
                header = f"\n### {file_path}\n"
                content_part = header + file_content
                
                # Check if we'd exceed limit
                if total_chars + len(content_part) > max_chars:
                    remaining = max_chars - total_chars
                    if remaining > 500:  # Only add if we have substantial space
                        content_part = content_part[:remaining] + "\n[Content truncated...]"
                        content_parts.append(content_part)
                    break
                
                content_parts.append(content_part)
                total_chars += len(content_part)
                
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")
                continue
        
        return "\n".join(content_parts)
    
    def load_file(self, file_path: str) -> Optional[str]:
        """Load a single SRD file"""
        full_path = self.srd_path / file_path
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None


def create_phase3_prompt(
    campaign_context: Dict,
    query: str,
    srd_content: str,
    base_prompt: str
) -> str:
    """
    Create a complete prompt for Phase 3 (Active Campaign)
    
    Args:
        campaign_context: Dict with campaign/party info
        query: Player's action/query
        srd_content: Relevant SRD rules
        base_prompt: Base DM prompt from template
        
    Returns:
        Complete formatted prompt
    """
    prompt = f"{base_prompt}\n\n"
    
    # Campaign context
    prompt += "=== CAMPAIGN CONTEXT ===\n"
    prompt += f"Campaign: {campaign_context.get('name', 'Unknown')}\n"
    prompt += f"Session: {campaign_context.get('session_number', 1)}\n"
    
    if campaign_context.get('current_location'):
        prompt += f"Location: {campaign_context['current_location']}\n"
    
    if campaign_context.get('active_combat'):
        prompt += "⚔️ COMBAT IS ACTIVE\n"
    
    # Party info
    if campaign_context.get('characters'):
        prompt += "\n=== PARTY ===\n"
        for char in campaign_context['characters']:
            prompt += f"• {char.get('name')}: {char.get('race')} {char.get('char_class')} "
            prompt += f"(Lvl {char.get('level', 1)}, HP: {char.get('hp')}/{char.get('max_hp')}, "
            prompt += f"AC: {char.get('ac')})\n"
    
    # Recent events
    if campaign_context.get('recent_events'):
        prompt += "\n=== RECENT EVENTS ===\n"
        for event in campaign_context['recent_events'][-5:]:
            prompt += f"- {event}\n"
    
    # SRD rules
    if srd_content and len(srd_content) > 100:
        prompt += f"\n=== D&D 5E RULES REFERENCE ===\n{srd_content}\n"
    
    # Player query
    prompt += f"\n=== PLAYER ACTION ===\n{query}\n"
    
    # Response instruction
    prompt += "\n=== YOUR RESPONSE ===\n"
    prompt += "As Dungeon Master, respond to the player's action with vivid narration "
    prompt += "and clear mechanics. Call for rolls when needed, describe outcomes dramatically.\n\n"
    prompt += "DM: "
    
    return prompt


# Testing and examples
if __name__ == "__main__":
    router = Phase3QueryRouter()
    
    print("=" * 70)
    print("PHASE 3 QUERY ROUTER - TESTING")
    print("=" * 70)
    
    test_queries = [
        "I attack the goblin with my sword",
        "I cast fireball at the enemies",
        "I want to search the room for traps",
        "I try to persuade the guard to let us pass",
        "I'm dying! Someone help!",
        "Can I climb up the wall?",
        "I want to use my legendary action"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = router.route_query(query)
        print(f"   Categories: {', '.join(result['matched_categories'])}")
        print(f"   Files ({len(result['files_to_load'])}):")
        for file in result['files_to_load'][:3]:
            print(f"     • {file}")
        if len(result['files_to_load']) > 3:
            print(f"     ... and {len(result['files_to_load']) - 3} more")
    
    print("\n" + "=" * 70)