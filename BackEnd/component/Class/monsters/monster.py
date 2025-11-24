"""
Monster Class Module

"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class Monster:
    """Monster data class for D&D 5e monsters"""
    name: str
    monster_type: str
    size: str
    alignment: str
    challenge_rating: float
    hp: int
    ac: int
    stats: Dict[str, int] = field(default_factory=dict)
    abilities: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    legendary_actions: List[str] = field(default_factory=list)
    lair_actions: List[str] = field(default_factory=list)
    description: Optional[str] = None


    def to_dict(self) -> Dict:
        """Convert Monster dataclass to dictionary"""
        return {
            "name": self.name,
            "monster_type": self.monster_type,
            "size": self.size,
            "alignment": self.alignment,
            "challenge_rating": self.challenge_rating,
            "hp": self.hp,
            "ac": self.ac,
            "stats": self.stats,
            "abilities": self.abilities,
            "actions": self.actions,
            "legendary_actions": self.legendary_actions,
            "lair_actions": self.lair_actions,
            "description": self.description
        }
    @staticmethod
    def from_dict(data: Dict) -> 'Monster':
        """Create Monster dataclass from dictionary"""
        return Monster(
            name=data.get("name", ""),
            monster_type=data.get("monster_type", ""),
            size=data.get("size", ""),
            alignment=data.get("alignment", ""),
            challenge_rating=data.get("challenge_rating", 0.0),
            hp=data.get("hp", 0),
            ac=data.get("ac", 0),
            stats=data.get("stats", {}),
            abilities=data.get("abilities", []),
            actions=data.get("actions", []),
            legendary_actions=data.get("legendary_actions", []),
            lair_actions=data.get("lair_actions", []),
            description=data.get("description")
        )
    def __str__(self) -> str:
        return f"{self.name} (CR {self.challenge_rating}) - {self.size} {self.monster_type}, {self.alignment}"
    def display_stats(self) -> str:
        stats_str = ", ".join([f"{key}: {value}" for key, value in self.stats.items()])
        return f"Stats for {self.name}: {stats_str}"
    def display_actions(self) -> str:
        actions_str = "\n".join(self.actions)
        return f"Actions for {self.name}:\n{actions_str}"
    def display_abilities(self) -> str:
        abilities_str = "\n".join(self.abilities)
        return f"Abilities for {self.name}:\n{abilities_str}"
    def display_legendary_actions(self) -> str:
        legendary_str = "\n".join(self.legendary_actions)
        return f"Legendary Actions for {self.name}:\n{legendary_str}"
    def display_lair_actions(self) -> str:
        lair_str = "\n".join(self.lair_actions)
        return f"Lair Actions for {self.name}:\n{lair_str}"
    def full_description(self) -> str:
        desc = f"{self}\nHP: {self.hp}, AC: {self.ac}\n"
        desc += self.display_stats() + "\n"
        if self.abilities:
            desc += self.display_abilities() + "\n"
        if self.actions:
            desc += self.display_actions() + "\n"
        if self.legendary_actions:
            desc += self.display_legendary_actions() + "\n"
        if self.lair_actions:
            desc += self.display_lair_actions() + "\n"
        if self.description:
            desc += f"Description:\n{self.description}\n"
        return desc
# Example usage:
if __name__ == "__main__":
    goblin_data = {
        "name": "Goblin",
        "monster_type": "Humanoid",
        "size": "Small",
        "alignment": "Neutral Evil",
        "challenge_rating": 0.25,
        "hp": 7,
        "ac": 15,
        "stats": {
            "strength": 8,
            "dexterity": 14,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 8,
            "charisma": 8
        },
        "abilities": ["Nimble Escape"],
        "actions": ["Scimitar Attack", "Shortbow Attack"],
        "description": "Goblins are small, green-skinned humanoids known for their cunning and malice."
    }

    goblin = Monster.from_dict(goblin_data)
    print(goblin.full_description())
