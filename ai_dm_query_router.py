#!/usr/bin/env python3
"""
AI DM Query Router
Routes player queries and actions to appropriate story cycle phases and files
"""

import re
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class QueryType(Enum):
    """Types of queries the AI DM might receive"""
    RULE_LOOKUP = "rule_lookup"
    CHARACTER_ACTION = "character_action"
    COMBAT = "combat"
    SPELL_LOOKUP = "spell_lookup"
    MONSTER_INFO = "monster_info"
    ITEM_LOOKUP = "item_lookup"
    SKILL_CHECK = "skill_check"
    WORLD_INFO = "world_info"
    STORY_PROGRESSION = "story_progression"
    CHARACTER_DEVELOPMENT = "character_development"
    UNDEFINED = "undefined"


@dataclass
class RoutingResult:
    """Result of routing a query"""
    primary_phase: str
    secondary_phases: List[str]
    relevant_files: List[str]
    query_type: QueryType
    confidence: float
    suggested_context: str
    keywords_matched: List[str]


class QueryRouter:
    """Routes queries to appropriate story cycle phases"""
    
    def __init__(self, srd_path: str):
        self.srd_path = Path(srd_path)
        
        # Define keyword patterns for each phase and file type
        self.phase_patterns = {
            "01_setup_and_introduction": {
                "keywords": [
                    "race", "ancestry", "background", "alignment", "language",
                    "character creation", "who am i", "where am i from",
                    "culture", "heritage", "homeland", "cosmology", "planes"
                ],
                "action_verbs": [],
                "questions": ["who", "what race", "what background", "where from"]
            },
            
            "02_character_creation": {
                "keywords": [
                    "class", "level", "ability score", "stats", "strength",
                    "dexterity", "constitution", "intelligence", "wisdom", "charisma",
                    "proficiency", "starting equipment", "hit points", "hp"
                ],
                "action_verbs": ["create", "build", "choose", "select"],
                "questions": ["what class", "how much health", "what stats"]
            },
            
            "03_call_to_adventure": {
                "keywords": [
                    "quest", "mission", "goal", "motivation", "hook",
                    "patron", "deity", "god", "calling", "purpose", "bond",
                    "ideal", "flaw", "faction"
                ],
                "action_verbs": ["accept", "begin", "start", "embark"],
                "questions": ["why", "what's my motivation", "who sent me"]
            },
            
            "04_preparation_and_planning": {
                "keywords": [
                    "equipment", "gear", "weapon", "armor", "tool",
                    "buy", "purchase", "shop", "prepare", "plan",
                    "spell preparation", "feat", "multiclass"
                ],
                "action_verbs": ["buy", "equip", "prepare", "learn", "train"],
                "questions": ["what can i buy", "how much does", "what weapons"]
            },
            
            "05_journey_and_exploration": {
                "keywords": [
                    "travel", "journey", "explore", "investigate", "search",
                    "perception", "insight", "nature", "survival",
                    "track", "navigate", "rest", "camp", "weather"
                ],
                "action_verbs": [
                    "travel", "walk", "explore", "investigate", "search",
                    "look", "examine", "track", "follow", "rest", "camp"
                ],
                "questions": ["how far", "how long", "what do i see", "can i find"]
            },
            
            "06_obstacles_and_challenges": {
                "keywords": [
                    "trap", "hazard", "obstacle", "poison", "disease",
                    "exhaustion", "difficult terrain", "problem", "complication",
                    "persuade", "deceive", "intimidate", "negotiate"
                ],
                "action_verbs": [
                    "avoid", "overcome", "negotiate", "persuade", "deceive",
                    "intimidate", "bypass", "disable"
                ],
                "questions": ["is there a trap", "how do i avoid", "can i persuade"]
            },
            
            "07_confrontation_and_combat": {
                "keywords": [
                    "attack", "combat", "fight", "initiative", "damage",
                    "hit", "miss", "ac", "armor class", "cover", "condition",
                    "grapple", "shove", "opportunity attack", "reaction",
                    "bonus action", "movement", "range"
                ],
                "action_verbs": [
                    "attack", "fight", "shoot", "cast", "hit", "strike",
                    "charge", "defend", "dodge", "dash", "disengage",
                    "grapple", "shove", "help", "hide"
                ],
                "questions": ["can i attack", "how much damage", "what's my ac"]
            },
            
            "08_monsters_and_npcs": {
                "keywords": [
                    "monster", "creature", "enemy", "npc", "stat block",
                    "legendary", "lair", "dragon", "goblin", "orc",
                    "undead", "beast", "aberration", "fiend", "celestial"
                ],
                "action_verbs": ["encounter", "face", "meet"],
                "questions": [
                    "what monster", "how strong", "what are the stats",
                    "what can it do", "legendary actions"
                ]
            },
            
            "09_crisis_and_setback": {
                "keywords": [
                    "dying", "death", "unconscious", "dead", "death save",
                    "death saving throw", "stabilize", "revive",
                    "exhausted", "cursed", "afflicted", "0 hp", "knocked out"
                ],
                "action_verbs": ["die", "fall", "succumb", "stabilize", "revive"],
                "questions": ["am i dying", "what happens at 0 hp", "death saves"]
            },
            
            "10_magic_and_extraordinary_solutions": {
                "keywords": [
                    "spell", "magic", "cast", "cantrip", "ritual",
                    "spell slot", "concentration", "component", "material",
                    "verbal", "somatic", "magic item", "artifact",
                    "enchanted", "cursed item", "attunement"
                ],
                "action_verbs": [
                    "cast", "conjure", "summon", "enchant", "dispel",
                    "attune", "activate"
                ],
                "questions": [
                    "can i cast", "what does the spell", "spell slot",
                    "what's this magic item"
                ]
            },
            
            "11_climax_and_resolution": {
                "keywords": [
                    "boss", "final battle", "climax", "legendary action",
                    "lair action", "mythic", "reward", "treasure", "loot",
                    "experience", "xp", "quest complete"
                ],
                "action_verbs": ["defeat", "conquer", "triumph", "complete", "finish"],
                "questions": ["is this the boss", "what do we get", "how much xp"]
            },
            
            "12_aftermath_and_growth": {
                "keywords": [
                    "downtime", "level up", "advancement", "training",
                    "crafting", "business", "rest", "recover",
                    "between adventures", "milestone"
                ],
                "action_verbs": [
                    "level up", "train", "craft", "rest", "recover",
                    "build", "establish"
                ],
                "questions": ["can i level up", "how do i advance", "what's next"]
            },
            
            "13_new_horizons": {
                "keywords": [
                    "renown", "fame", "reputation", "next adventure",
                    "stronghold", "business", "influence", "legacy"
                ],
                "action_verbs": ["establish", "build", "expand", "influence"],
                "questions": ["what's next", "what changed", "what's my reputation"]
            },
            
            "ref_quick_reference": {
                "keywords": [
                    "condition", "action list", "what can i do",
                    "quick reference", "summary", "rules summary"
                ],
                "action_verbs": [],
                "questions": ["what actions", "what conditions", "quick rule"]
            }
        }
        
        # File-specific patterns for more precise routing
        self.file_patterns = {
            # Spells
            "spell": {
                "phases": ["10_magic_and_extraordinary_solutions"],
                "subdirs": ["spellcasting", "spell_lists"],
                "keywords": ["spell", "cast", "magic", "cantrip"]
            },
            
            # Combat
            "combat": {
                "phases": ["07_confrontation_and_combat"],
                "subdirs": ["combat_basics", "combat_actions", "tactical"],
                "keywords": ["attack", "damage", "initiative", "combat"]
            },
            
            # Monsters
            "monster": {
                "phases": ["08_monsters_and_npcs"],
                "subdirs": ["monster_basics", "by_type", "legendary"],
                "keywords": ["monster", "creature", "stat block"]
            },
            
            # Skills
            "skill": {
                "phases": ["05_journey_and_exploration"],
                "subdirs": ["skills"],
                "keywords": [
                    "acrobatics", "animal handling", "arcana", "athletics",
                    "deception", "history", "insight", "intimidation",
                    "investigation", "medicine", "nature", "perception",
                    "performance", "persuasion", "religion", "sleight of hand",
                    "stealth", "survival"
                ]
            },
            
            # Conditions
            "condition": {
                "phases": ["07_confrontation_and_combat", "ref_quick_reference"],
                "subdirs": ["tactical", "tables"],
                "keywords": [
                    "blinded", "charmed", "deafened", "frightened",
                    "grappled", "incapacitated", "invisible", "paralyzed",
                    "petrified", "poisoned", "prone", "restrained",
                    "stunned", "unconscious", "exhaustion"
                ]
            }
        }
    
    def analyze_query(self, query: str) -> Dict:
        """Analyze a query to extract key information"""
        query_lower = query.lower()
        
        analysis = {
            "has_question_word": any(q in query_lower for q in ["what", "how", "why", "when", "where", "who", "can"]),
            "has_action_verb": False,
            "matched_keywords": [],
            "matched_phases": {},
            "query_type": QueryType.UNDEFINED,
            "is_combat": any(word in query_lower for word in ["attack", "damage", "combat", "fight", "initiative"]),
            "is_spell": any(word in query_lower for word in ["spell", "cast", "magic"]),
            "is_skill_check": any(word in query_lower for word in ["check", "roll", "perception", "investigation"])
        }
        
        # Check for question words and action verbs in each phase
        for phase, patterns in self.phase_patterns.items():
            matches = 0
            matched_words = []
            
            # Check keywords
            for keyword in patterns["keywords"]:
                if keyword in query_lower:
                    matches += 1
                    matched_words.append(keyword)
            
            # Check action verbs
            for verb in patterns["action_verbs"]:
                if verb in query_lower:
                    matches += 2  # Weight action verbs higher
                    matched_words.append(verb)
                    analysis["has_action_verb"] = True
            
            # Check question patterns
            for question in patterns["questions"]:
                if question in query_lower:
                    matches += 1.5
                    matched_words.append(question)
            
            if matches > 0:
                analysis["matched_phases"][phase] = {
                    "score": matches,
                    "keywords": matched_words
                }
        
        # Determine query type
        if analysis["is_combat"]:
            analysis["query_type"] = QueryType.COMBAT
        elif analysis["is_spell"]:
            analysis["query_type"] = QueryType.SPELL_LOOKUP
        elif analysis["is_skill_check"]:
            analysis["query_type"] = QueryType.SKILL_CHECK
        elif "monster" in query_lower or "creature" in query_lower:
            analysis["query_type"] = QueryType.MONSTER_INFO
        elif "magic item" in query_lower or "artifact" in query_lower:
            analysis["query_type"] = QueryType.ITEM_LOOKUP
        elif analysis["has_action_verb"]:
            analysis["query_type"] = QueryType.CHARACTER_ACTION
        else:
            analysis["query_type"] = QueryType.RULE_LOOKUP
        
        return analysis
    
    def route_query(self, query: str, current_story_phase: Optional[str] = None) -> RoutingResult:
        """Route a query to appropriate phases and files"""
        analysis = self.analyze_query(query)
        
        # Sort phases by relevance
        sorted_phases = sorted(
            analysis["matched_phases"].items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )
        
        if not sorted_phases:
            # Default to current phase or quick reference
            primary_phase = current_story_phase or "ref_quick_reference"
            secondary_phases = []
            confidence = 0.3
        else:
            primary_phase = sorted_phases[0][0]
            secondary_phases = [phase for phase, _ in sorted_phases[1:3]]
            
            # Calculate confidence based on match strength
            top_score = sorted_phases[0][1]["score"]
            confidence = min(top_score / 5.0, 1.0)  # Normalize to 0-1
        
        # If current phase is provided and has moderate confidence, boost it
        if current_story_phase and confidence < 0.7:
            if current_story_phase not in [primary_phase] + secondary_phases:
                secondary_phases.insert(0, current_story_phase)
        
        # Get relevant files based on query type and phases
        relevant_files = self._get_relevant_files(
            primary_phase,
            secondary_phases,
            analysis["query_type"],
            query.lower()
        )
        
        # Generate suggested context
        suggested_context = self._generate_context_suggestion(
            primary_phase,
            analysis["query_type"],
            query
        )
        
        # Collect all matched keywords
        all_keywords = []
        for phase_data in analysis["matched_phases"].values():
            all_keywords.extend(phase_data["keywords"])
        
        return RoutingResult(
            primary_phase=primary_phase,
            secondary_phases=secondary_phases,
            relevant_files=relevant_files,
            query_type=analysis["query_type"],
            confidence=confidence,
            suggested_context=suggested_context,
            keywords_matched=list(set(all_keywords))
        )
    
    def _get_relevant_files(
        self,
        primary_phase: str,
        secondary_phases: List[str],
        query_type: QueryType,
        query_lower: str
    ) -> List[str]:
        """Get list of relevant files for the query"""
        files = []
        
        # Get files from primary phase
        phase_path = self.srd_path / primary_phase
        if phase_path.exists():
            # Add files based on query type
            if query_type == QueryType.COMBAT:
                files.extend(self._get_files_from_subdirs(
                    phase_path,
                    ["combat_basics", "combat_actions", "tactical"]
                ))
            elif query_type == QueryType.SPELL_LOOKUP:
                files.extend(self._get_files_from_subdirs(
                    phase_path,
                    ["spellcasting", "spell_lists"]
                ))
            elif query_type == QueryType.MONSTER_INFO:
                files.extend(self._get_files_from_subdirs(
                    phase_path,
                    ["monster_basics", "by_type", "legendary"]
                ))
            else:
                # Get all files from phase
                files.extend(self._get_all_files_from_phase(phase_path))
        
        # Add index file
        index_file = phase_path / "INDEX.md"
        if index_file.exists():
            files.insert(0, str(index_file))
        
        # Limit to most relevant files
        return files[:10]
    
    def _get_files_from_subdirs(
        self,
        phase_path: Path,
        subdirs: List[str]
    ) -> List[str]:
        """Get all markdown files from specific subdirectories"""
        files = []
        for subdir in subdirs:
            subdir_path = phase_path / subdir
            if subdir_path.exists():
                files.extend([
                    str(f) for f in subdir_path.glob("*.md")
                ])
        return files
    
    def _get_all_files_from_phase(self, phase_path: Path) -> List[str]:
        """Get all markdown files from a phase"""
        files = []
        for subdir in phase_path.iterdir():
            if subdir.is_dir():
                files.extend([
                    str(f) for f in subdir.glob("*.md")
                ])
        return files
    
    def _generate_context_suggestion(
        self,
        primary_phase: str,
        query_type: QueryType,
        query: str
    ) -> str:
        """Generate a context suggestion for the AI DM"""
        phase_descriptions = {
            "01_setup_and_introduction": "You're helping establish character background and world context.",
            "02_character_creation": "You're assisting with character creation and mechanics.",
            "03_call_to_adventure": "You're setting up the adventure hook and motivation.",
            "04_preparation_and_planning": "You're helping the party prepare for their journey.",
            "05_journey_and_exploration": "You're narrating travel and exploration.",
            "06_obstacles_and_challenges": "You're presenting obstacles and complications.",
            "07_confrontation_and_combat": "You're running a combat encounter.",
            "08_monsters_and_npcs": "You're providing information about creatures or NPCs.",
            "09_crisis_and_setback": "You're dealing with serious consequences or setbacks.",
            "10_magic_and_extraordinary_solutions": "You're handling magic, spells, or magical items.",
            "11_climax_and_resolution": "You're running the climactic encounter or resolution.",
            "12_aftermath_and_growth": "You're handling downtime and character advancement.",
            "13_new_horizons": "You're setting up future adventures.",
            "ref_quick_reference": "You're providing quick rules reference."
        }
        
        base_context = phase_descriptions.get(
            primary_phase,
            "You're assisting the DM with game mechanics."
        )
        
        type_context = {
            QueryType.COMBAT: " Focus on clear combat mechanics and tactical options.",
            QueryType.SPELL_LOOKUP: " Provide accurate spell details and limitations.",
            QueryType.MONSTER_INFO: " Give comprehensive creature information.",
            QueryType.SKILL_CHECK: " Explain skill check mechanics and DCs.",
            QueryType.CHARACTER_ACTION: " Describe action outcomes and consequences."
        }
        
        return base_context + type_context.get(query_type, "")
    
    def get_context_files_for_ai(
        self,
        query: str,
        current_phase: Optional[str] = None,
        max_files: int = 5
    ) -> Dict:
        """
        Get a formatted context package for an AI DM system
        Returns files to load and context instructions
        """
        result = self.route_query(query, current_phase)
        
        return {
            "query": query,
            "routing": {
                "primary_phase": result.primary_phase,
                "secondary_phases": result.secondary_phases,
                "confidence": result.confidence,
                "query_type": result.query_type.value
            },
            "files_to_load": result.relevant_files[:max_files],
            "ai_instructions": {
                "context": result.suggested_context,
                "keywords": result.keywords_matched,
                "response_style": self._get_response_style(result.query_type)
            }
        }
    
    def _get_response_style(self, query_type: QueryType) -> str:
        """Get recommended response style for query type"""
        styles = {
            QueryType.COMBAT: "Be precise and clear. Provide step-by-step combat mechanics.",
            QueryType.SPELL_LOOKUP: "Be exact with spell details. Include all components and limitations.",
            QueryType.MONSTER_INFO: "Provide full stat blocks and special abilities.",
            QueryType.SKILL_CHECK: "Explain the skill, typical DCs, and consequences.",
            QueryType.CHARACTER_ACTION: "Narrate outcomes dramatically while explaining mechanics.",
            QueryType.RULE_LOOKUP: "Be clear and cite specific rules.",
            QueryType.WORLD_INFO: "Be descriptive and immersive.",
            QueryType.STORY_PROGRESSION: "Focus on narrative flow and player choice."
        }
        return styles.get(query_type, "Be helpful and accurate.")


def main():
    """Demo of the query router"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Route D&D queries to story cycle phases")
    parser.add_argument("srd_path", help="Path to reorganized SRD directory")
    parser.add_argument("--query", "-q", help="Query to route")
    parser.add_argument("--phase", "-p", help="Current story phase")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    router = QueryRouter(args.srd_path)
    
    if args.interactive:
        print("=== AI DM Query Router - Interactive Mode ===")
        print("Enter queries to see routing suggestions (type 'quit' to exit)\n")
        
        current_phase = None
        while True:
            query = input("\n📝 Query: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if query.startswith("phase:"):
                current_phase = query.replace("phase:", "").strip()
                print(f"✓ Current phase set to: {current_phase}")
                continue
            
            result = router.get_context_files_for_ai(query, current_phase)
            
            print(f"\n{'='*60}")
            print(f"Query Type: {result['routing']['query_type']}")
            print(f"Confidence: {result['routing']['confidence']:.2f}")
            print(f"\n📍 Primary Phase: {result['routing']['primary_phase']}")
            
            if result['routing']['secondary_phases']:
                print(f"📎 Secondary Phases: {', '.join(result['routing']['secondary_phases'])}")
            
            print(f"\n📚 Files to Load ({len(result['files_to_load'])}):")
            for file in result['files_to_load']:
                print(f"  - {Path(file).name}")
            
            print(f"\n💡 AI Context: {result['ai_instructions']['context']}")
            print(f"🎯 Response Style: {result['ai_instructions']['response_style']}")
            
            if result['ai_instructions']['keywords']:
                print(f"🔑 Keywords: {', '.join(result['ai_instructions']['keywords'][:5])}")
    
    elif args.query:
        result = router.get_context_files_for_ai(args.query, args.phase)
        print(json.dumps(result, indent=2, default=str))
    
    else:
        # Run demo queries
        demo_queries = [
            "I want to attack the goblin with my longsword",
            "Can I cast fireball at 3rd level?",
            "What monster is in the cave?",
            "I want to make a perception check",
            "What happens when I reach 0 hit points?",
            "I want to level up my character",
            "Tell me about the dragonborn race",
            "How do I prepare spells?",
            "What's my movement speed?",
            "I want to persuade the guard"
        ]
        
        print("=== AI DM Query Router Demo ===\n")
        for query in demo_queries:
            result = router.get_context_files_for_ai(query)
            print(f"Query: {query}")
            print(f"→ Phase: {result['routing']['primary_phase']}")
            print(f"→ Type: {result['routing']['query_type']}")
            print(f"→ Confidence: {result['routing']['confidence']:.2f}")
            print()


if __name__ == "__main__":
    main()

    