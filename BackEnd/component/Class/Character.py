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

    # inventory: List[str] = field(default_factory=list)  # type: ignore 
    notes: str = ""
    # armor_worn: str = "" 

    background_feature: str = ""  # Description of background feature
    # background_equipment: List[str] = field(default_factory=list)  # Equipment from background  # type: ignore
    
    skill_proficiencies: List[str] = field(default_factory=list)  # All skills (class + background)  # type: ignore
    # tool_proficiencies: List[str] = field(default_factory=list)  # Tools from background  # type: ignore

    languages_known: List[str] = field(default_factory=list)  # Combines racial + background languages  # type: ignore
    
    # Personality (from background tables)
    personality_traits: List[str] = field(default_factory=list)  # 2 traits  # type: ignore
    ideal: str = ""  # 1 ideal
    bond: str = ""  # 1 bond
    flaw: str = ""  # 1 flaw
    
    alignment: str = "True Neutral"  # Default alignment
    
    has_inspiration: bool = False

    
    
    # saving_throw_proficiencies: List[str] = field(default_factory=list)  # type: ignore
    # currency: full denominations, default to zero for each type
    currency: Dict[str, int] = field(default_factory=lambda: {
        'cp': 0,
        'sp': 0,
        'ep': 0,
        'gp': 0,
        'pp': 0
    })
    # type: ignore
    
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
    
    # Currency Helper Methods
    def get_total_gold_value(self) -> float:
        """Calculate total wealth in gold pieces"""
        return (
            self.currency['cp'] * 0.01 +
            self.currency['sp'] * 0.1 +
            self.currency['ep'] * 0.5 +
            self.currency['gp'] * 1.0 +
            self.currency['pp'] * 10.0
        )
    
    def add_currency(self, coin_type: str, amount: int):
        """Add currency to character"""
        if coin_type in self.currency:
            self.currency[coin_type] += amount
        else:
            raise ValueError(f"Invalid coin type: {coin_type}")
    
    def remove_currency(self, coin_type: str, amount: int) -> bool:
        """Remove currency from character. Returns False if insufficient funds."""
        if coin_type not in self.currency:
            raise ValueError(f"Invalid coin type: {coin_type}")
        
        if self.currency[coin_type] >= amount:
            self.currency[coin_type] -= amount
            return True
        return False
    
    def can_afford(self, cost_in_gp: float) -> bool:
        """Check if character can afford something (cost in gold pieces)"""
        return self.get_total_gold_value() >= cost_in_gp
    
    def pay_cost(self, cost_in_gp: float) -> bool:
        """
        Pay a cost in gold pieces by automatically converting currency.
        Returns True if successful, False if insufficient funds.
        """
        if not self.can_afford(cost_in_gp):
            return False
        
        # Try to pay with exact denominations first (largest to smallest)
        remaining = cost_in_gp
        
        # Pay with platinum
        pp_to_use = min(int(remaining / 10), self.currency['pp'])
        remaining -= pp_to_use * 10
        self.currency['pp'] -= pp_to_use
        
        # Pay with gold
        gp_to_use = min(int(remaining), self.currency['gp'])
        remaining -= gp_to_use
        self.currency['gp'] -= gp_to_use
        
        # Pay with electrum
        ep_to_use = min(int(remaining / 0.5), self.currency['ep'])
        remaining -= ep_to_use * 0.5
        self.currency['ep'] -= ep_to_use
        
        # Pay with silver
        sp_to_use = min(int(remaining / 0.1), self.currency['sp'])
        remaining -= sp_to_use * 0.1
        self.currency['sp'] -= sp_to_use
        
        # Pay remaining with copper
        cp_to_use = min(int(remaining / 0.01), self.currency['cp'])
        remaining -= cp_to_use * 0.01
        self.currency['cp'] -= cp_to_use
        
        # If still remaining, we need to make change (convert larger coins)
        if remaining > 0.001:  # Small float tolerance
            return False
        
        return True
    
    def convert_currency(self, from_type: str, to_type: str, amount: int) -> bool:
        """
        Convert currency from one denomination to another.
        Returns True if successful, False if insufficient funds.
        """
        conversion_rates = {
            'cp': 1, 'sp': 10, 'ep': 50, 'gp': 100, 'pp': 1000
        }
        
        if from_type not in conversion_rates or to_type not in conversion_rates:
            raise ValueError("Invalid coin type")
        
        if self.currency[from_type] < amount:
            return False
        
        # Calculate conversion
        from_value_in_cp = amount * conversion_rates[from_type]
        to_amount = from_value_in_cp // conversion_rates[to_type]
        
        if to_amount < 1:
            return False  # Can't convert (not enough value)
        
        # Perform conversion
        self.currency[from_type] -= amount
        self.currency[to_type] += to_amount
        
        return True
