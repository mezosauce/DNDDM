#!/usr/bin/env python3
"""
Class Registry and Factory System
Provides dynamic character class instantiation and serialization
"""

from typing import Dict, Type, Any, Optional
from dataclasses import asdict
import json

# Import base Character class
from Head.campaign_manager import Character

# Import all class implementations
from Head.Class.barbarian import Barbarian

# ============================================================================
# CLASS REGISTRY
# ============================================================================

CLASS_REGISTRY: Dict[str, Type[Character]] = {
    "Character": Character,  # Base class
    "Barbarian": Barbarian,
}


def register_class(class_name: str, class_type: Type[Character]):
    """Register a new character class"""
    CLASS_REGISTRY[class_name] = class_type


def get_registered_classes():
    """Get all registered class names"""
    return list(CLASS_REGISTRY.keys())


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_character(class_type: str = "Character", **kwargs) -> Character:
    """
    Factory function to create character instances of the correct class type.
    
    Args:
        class_type: Name of the class to instantiate (e.g., "Barbarian")
        **kwargs: Character data fields
    
    Returns:
        Instance of the appropriate Character subclass
    
    Example:
        >>> char = create_character("Barbarian", name="Grog", level=3, ...)
        >>> isinstance(char, Barbarian)  # True
        >>> char.enter_rage()  # Barbarian-specific method works!
    """
    # Get class from registry, default to base Character
    CharClass = CLASS_REGISTRY.get(class_type, Character)
    
    # Remove class_type from kwargs if present (it's not a Character field)
    kwargs.pop('class_type', None)
    
    # Instantiate and return
    return CharClass(**kwargs)


def character_to_dict(character: Character) -> Dict[str, Any]:
    """
    Convert character to dictionary with class_type metadata.
    
    Args:
        character: Character instance
    
    Returns:
        Dictionary with all character data + class_type field
    """
    data = asdict(character)
    
    # Add class_type metadata
    data['class_type'] = character.__class__.__name__
    
    return data


def character_from_dict(data: Dict[str, Any]) -> Character:
    """
    Load character from dictionary, instantiating correct class type.
    
    Args:
        data: Character data dictionary (with optional class_type field)
    
    Returns:
        Instance of the appropriate Character subclass
    
    Note:
        Backward compatible - if no class_type field, infers from char_class
        or defaults to base Character class.
    """
    # Try to get class_type from data
    class_type = data.get('class_type')
    
    # Backward compatibility: infer from char_class if class_type missing
    if not class_type:
        char_class = data.get('char_class', 'Character')
        # Map common class names to registry keys
        class_type = char_class if char_class in CLASS_REGISTRY else 'Character'
    
    # Create instance using factory
    return create_character(class_type, **data)


# ============================================================================
# METADATA LOADER
# ============================================================================

def get_class_metadata(class_name: str) -> Optional[Dict[str, Any]]:
    """
    Load class metadata from class_metadata.json
    
    Args:
        class_name: Name of the class (e.g., "Barbarian")
    
    Returns:
        Dictionary of class metadata or None if not found
    """
    try:
        from pathlib import Path
        metadata_file = Path(__file__).parent / "class_metadata.json"
        
        with open(metadata_file, 'r') as f:
            all_metadata = json.load(f)
        
        return all_metadata.get(class_name)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def get_all_class_metadata() -> Dict[str, Dict[str, Any]]:
    """Load all class metadata"""
    try:
        from pathlib import Path
        metadata_file = Path(__file__).parent / "class_metadata.json"
        
        with open(metadata_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'CLASS_REGISTRY',
    'register_class',
    'get_registered_classes',
    'create_character',
    'character_to_dict',
    'character_from_dict',
    'get_class_metadata',
    'get_all_class_metadata',
]