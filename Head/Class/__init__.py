#!/usr/bin/env python3
"""
Class Registry and Factory System
Handles creation and serialization of class-specific Character objects
"""

from typing import Dict, Type, Any
from dataclasses import asdict

# Import all class implementations
from Head.Class.barbarian import Barbarian

# Try to import other classes (they may not exist yet)
try:
    from Head.Class.bard import Bard
except ImportError:
    Bard = None


# ============================================================================
# CLASS REGISTRY
# ============================================================================

# Registry mapping class names to class types
# Character base class added lazily to avoid circular import
CLASS_REGISTRY: Dict[str, Type] = {
    "Barbarian": Barbarian,
}

# Add other classes if they exist
if Bard:
    CLASS_REGISTRY["Bard"] = Bard


def _get_base_character_class():
    """Lazy import of base Character class to avoid circular dependency"""
    from Head.campaign_manager import Character
    return Character


def _ensure_character_in_registry():
    """Add Character to registry if not already present"""
    if "Character" not in CLASS_REGISTRY:
        CLASS_REGISTRY["Character"] = _get_base_character_class()


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_character(class_type: str, **kwargs):
    """
    Factory function to create a character of the specified class type.
    
    Args:
        class_type: Name of the class (e.g., "Barbarian", "Bard")
        **kwargs: Character attributes to pass to the constructor
    
    Returns:
        Character instance of the appropriate class
    
    Example:
        >>> barbarian = create_character("Barbarian", name="Grog", level=5)
        >>> isinstance(barbarian, Barbarian)
        True
    """
    # Ensure Character is in registry
    _ensure_character_in_registry()
    
    # Get the class from registry, default to base Character if not found
    character_class = CLASS_REGISTRY.get(class_type, CLASS_REGISTRY["Character"])
    
    # Remove class_type from kwargs if present (it's metadata, not a field)
    kwargs.pop('class_type', None)
    
    # Create and return the character
    return character_class(**kwargs)


def character_to_dict(character) -> Dict[str, Any]:
    """
    Convert a character to a dictionary for JSON serialization.
    Adds class_type metadata for proper deserialization.
    
    Args:
        character: Character instance to serialize
    
    Returns:
        Dictionary with character data plus class_type metadata
    
    Example:
        >>> barbarian = Barbarian(name="Grog")
        >>> data = character_to_dict(barbarian)
        >>> data['class_type']
        'Barbarian'
    """
    # Get character data as dict
    char_dict = asdict(character)
    
    # Add class_type metadata
    # Determine the actual class type
    class_name = type(character).__name__
    char_dict['class_type'] = class_name
    
    return char_dict


def character_from_dict(data: Dict[str, Any]):
    """
    Create a character from a dictionary (e.g., loaded from JSON).
    Uses class_type metadata to instantiate the correct class.
    
    Args:
        data: Dictionary containing character data
    
    Returns:
        Character instance of the appropriate class
    
    Example:
        >>> data = {'name': 'Grog', 'class_type': 'Barbarian', ...}
        >>> character = character_from_dict(data)
        >>> isinstance(character, Barbarian)
        True
    """
    # Extract class_type metadata (default to infer from char_class field)
    class_type = data.get('class_type')
    
    # Backward compatibility: If no class_type, try to infer from char_class
    if not class_type:
        class_type = data.get('char_class', 'Character')
    
    # Create character using factory
    return create_character(class_type, **data)


def get_available_classes() -> list:
    """
    Get list of all available character classes.
    
    Returns:
        List of class names that can be created
    
    Example:
        >>> classes = get_available_classes()
        >>> 'Barbarian' in classes
        True
    """
    _ensure_character_in_registry()
    return list(CLASS_REGISTRY.keys())


def is_class_available(class_name: str) -> bool:
    """
    Check if a class is available in the registry.
    
    Args:
        class_name: Name of the class to check
    
    Returns:
        True if class is available, False otherwise
    
    Example:
        >>> is_class_available('Barbarian')
        True
        >>> is_class_available('FakeClass')
        False
    """
    _ensure_character_in_registry()
    return class_name in CLASS_REGISTRY


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'CLASS_REGISTRY',
    'create_character',
    'character_to_dict',
    'character_from_dict',
    'get_available_classes',
    'is_class_available',
    'Barbarian',
]


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CLASS REGISTRY TEST")
    print("=" * 60)
    
    print(f"\nAvailable classes: {get_available_classes()}")
    
    # Test 1: Create a Barbarian
    print("\n" + "-" * 60)
    print("Test 1: Create Barbarian using factory")
    print("-" * 60)
    
    barbarian = create_character(
        class_type="Barbarian",
        name="Grog Strongjaw",
        race="Goliath",
        char_class="Barbarian",
        background="Outlander",
        level=5
    )
    
    print(f"Created: {barbarian}")
    print(f"Type: {type(barbarian).__name__}")
    print(f"Is Barbarian: {isinstance(barbarian, Barbarian)}")
    print(f"Rages per day: {barbarian.rages_per_day}")
    print(f"Rage damage: {barbarian.rage_damage}")
    
    # Test 2: Serialize to dict
    print("\n" + "-" * 60)
    print("Test 2: Serialize to dictionary")
    print("-" * 60)
    
    char_dict = character_to_dict(barbarian)
    print(f"class_type in dict: {char_dict.get('class_type')}")
    print(f"name in dict: {char_dict.get('name')}")
    print(f"rages_per_day in dict: {char_dict.get('rages_per_day')}")
    
    # Test 3: Deserialize from dict
    print("\n" + "-" * 60)
    print("Test 3: Deserialize from dictionary")
    print("-" * 60)
    
    restored_char = character_from_dict(char_dict)
    print(f"Restored: {restored_char}")
    print(f"Type: {type(restored_char).__name__}")
    print(f"Is Barbarian: {isinstance(restored_char, Barbarian)}")
    print(f"Name matches: {restored_char.name == barbarian.name}")
    print(f"Rages match: {restored_char.rages_per_day == barbarian.rages_per_day}")
    
    # Test 4: Backward compatibility
    print("\n" + "-" * 60)
    print("Test 4: Backward compatibility (no class_type field)")
    print("-" * 60)
    
    old_format_data = {
        'name': 'Old Character',
        'char_class': 'Barbarian',
        'race': 'Human',
        'background': 'Soldier',
        'level': 1
    }
    
    old_char = character_from_dict(old_format_data)
    print(f"Created from old format: {old_char}")
    print(f"Type: {type(old_char).__name__}")
    print(f"Is Barbarian: {isinstance(old_char, Barbarian)}")
    
    # Test 5: Unknown class defaults to Character
    print("\n" + "-" * 60)
    print("Test 5: Unknown class defaults to Character")
    print("-" * 60)
    
    unknown_data = {
        'name': 'Unknown Class',
        'class_type': 'FakeClass',
        'char_class': 'FakeClass',
        'race': 'Human',
        'background': 'Folk Hero',
        'level': 1
    }
    
    unknown_char = character_from_dict(unknown_data)
    print(f"Created: {unknown_char}")
    print(f"Type: {type(unknown_char).__name__}")
    
    # Import Character for final test
    Character = _get_base_character_class()
    print(f"Is base Character: {type(unknown_char) == Character}")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed")
    print("=" * 60)