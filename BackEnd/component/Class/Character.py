"""
Base Class Character
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
import shutil

def default_stats() -> Dict[str, int]:
    return {
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10
    } # type: ignore

@dataclass
class Character:
    """Player character data - ENHANCED with full D&D 5e character sheet"""
    name: str
    race: str
    char_class: str
    background: str

    level: int = 1
    hp: int = 10
    max_hp: int = 10
    ac: int = 10
    stats: Dict[str, int] = field(default_factory=default_stats)

     
    notes: str = ""
     

    background_feature: str = ""  # Description of background feature
    
    skill_proficiencies: List[str] = field(default_factory=list)  # All skills (class + background)  # type: ignore

    languages_known: List[str] = field(default_factory=list)  # Combines racial + background languages  # type: ignore
    
    personality_traits: List[str] = field(default_factory=list)  # 2 traits  # type: ignore
    ideal: str = ""  # 1 ideal
    bond: str = ""  # 1 bond
    flaw: str = ""  # 1 flaw
    
    alignment: str = "True Neutral"      
    

    def __post_init__(self):
        # Ensure stats uses the expected key names (in case older data used different structure)
        if not isinstance(self.stats, dict):
            self.stats = {
                "strength": 10,
                "dexterity": 10,
                "constitution": 10,
                "intelligence": 10,
                "wisdom": 10,
                "charisma": 10
            }

def character_to_dict(character: Character) -> Dict:
    """Convert Character to dict with class type metadata for serialization"""
    char_dict = asdict(character)
    # Add class type metadata to support potential Character subclasses
    char_dict['_class_type'] = character.__class__.__name__
    return char_dict


def character_from_dict(char_data: Dict) -> Character:
    """Create Character from dict, handling class type metadata"""
    # Remove metadata that's not part of Character dataclass fields
    data = char_data.copy()
    class_type = data.pop('_class_type', 'Character')
    
    # Create appropriate character class instance
    # This supports future Character subclasses (e.g., Fighter, Wizard, etc.)
    if class_type == 'Character':
        return Character(**data)
    else:
        # Default to base Character if unknown type
        # Could be extended to handle subclasses in the future
        return Character(**data)