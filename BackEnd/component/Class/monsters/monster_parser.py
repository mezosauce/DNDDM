#!/usr/bin/env python3
"""
Monster Markdown Parser
Parses SRD monster markdown files and creates Monster instances
"""

import re
from pathlib import Path
from typing import Dict, Optional
from .monster import Monster


class MonsterParser:
    """Parse monster data from SRD markdown files"""
    
    def __init__(self, srd_base_path: str = "../../../../srd_story_cycle"):
        self.srd_base_path = Path(srd_base_path)
        self.monsters_path = self.srd_base_path / "08_monsters_and_npcs"
    
    def parse_monster_file(self, file_path: str) -> Optional[Monster]:
        """
        Parse a monster markdown file and return Monster instance
        
        Args:
            file_path: Relative path from SRD root (e.g., "08_monsters_and_npcs/tarrasque.md")
        
        Returns:
            Monster instance or None if parsing fails
        """
        full_path = self.srd_base_path / file_path
        
        if not full_path.exists():
            print(f"[MonsterParser] File not found: {full_path}")
            return None
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._parse_markdown_content(content)
            
        except Exception as e:
            print(f"[MonsterParser] Error parsing {file_path}: {e}")
            return None
    
    def _parse_markdown_content(self, content: str) -> Monster:
        """Parse markdown content into Monster data"""
        
        # Extract name (from # header)
        name_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else "Unknown Monster"
        
        # Extract monster type line (e.g., "*Large giant, chaotic evil*")
        type_line_match = re.search(r'\*([^,]+),\s+([^*]+)\*', content)
        if type_line_match:
            size_and_type = type_line_match.group(1).strip()
            alignment = type_line_match.group(2).strip()
            
            # Split size and type (e.g., "Large giant" -> "Large", "giant")
            parts = size_and_type.split(None, 1)
            size = parts[0] if len(parts) > 0 else "Medium"
            monster_type = parts[1] if len(parts) > 1 else "humanoid"
        else:
            size = "Medium"
            monster_type = "humanoid"
            alignment = "unaligned"
        
        # Extract AC
        ac_match = re.search(r'\*\*Armor Class\*\*\s+(\d+)', content)
        ac = int(ac_match.group(1)) if ac_match else 10
        
        # Extract HP
        hp_match = re.search(r'\*\*Hit Points\*\*\s+(\d+)', content)
        hp = int(hp_match.group(1)) if hp_match else 10
        
        # Extract CR
        cr_match = re.search(r'\*\*Challenge\*\*\s+([\d/]+)', content)
        if cr_match:
            cr_str = cr_match.group(1)
            if '/' in cr_str:
                # Handle fractions like "1/4"
                num, denom = cr_str.split('/')
                cr = float(num) / float(denom)
            else:
                cr = float(cr_str)
        else:
            cr = 1.0
        
        # Extract ability scores
        stats = self._extract_stats(content)
        
        # Extract special abilities
        abilities = self._extract_section_items(content, "### Special Abilities", "### Actions")
        
        # Extract actions
        actions = self._extract_section_items(content, "### Actions", "### Legendary Actions")
        if not actions:
            # Try alternate section name
            actions = self._extract_section_items(content, "### Actions", "### Reactions")
        if not actions:
            # No section delimiter, get everything after Actions
            actions = self._extract_section_items(content, "### Actions", None)
        
        # Extract legendary actions
        legendary_actions = self._extract_section_items(content, "### Legendary Actions", "### Lair Actions")
        if not legendary_actions:
            legendary_actions = self._extract_section_items(content, "### Legendary Actions", None)
        
        # Extract lair actions
        lair_actions = self._extract_section_items(content, "### Lair Actions", None)
        
        # Extract description (everything before the type line)
        description = self._extract_description(content)
        
        return Monster(
            name=name,
            monster_type=monster_type,
            size=size,
            alignment=alignment,
            challenge_rating=cr,
            hp=hp,
            ac=ac,
            stats=stats,
            abilities=abilities,
            actions=actions,
            legendary_actions=legendary_actions,
            lair_actions=lair_actions,
            description=description
        )
    
    def _extract_stats(self, content: str) -> Dict[str, int]:
        """Extract ability scores (STR, DEX, CON, INT, WIS, CHA)"""
        stats = {}
        
        stat_names = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
        
        # Look for stat block (format: |STR|DEX|CON|INT|WIS|CHA|)
        stat_pattern = r'\|STR\|DEX\|CON\|INT\|WIS\|CHA\|[^\|]*\n\|[-:]+\|[-:]+\|[-:]+\|[-:]+\|[-:]+\|[-:]+\|[^\|]*\n\|([^\|]+)\|([^\|]+)\|([^\|]+)\|([^\|]+)\|([^\|]+)\|([^\|]+)\|'
        match = re.search(stat_pattern, content)
        
        if match:
            for i, stat_name in enumerate(stat_names, 1):
                stat_value = match.group(i).strip()
                # Extract just the number (format might be "20 (+5)")
                num_match = re.search(r'(\d+)', stat_value)
                if num_match:
                    stats[stat_name.lower()] = int(num_match.group(1))
        
        # Default values if not found
        for stat in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            if stat not in stats:
                stats[stat] = 10
        
        return stats
    
    def _extract_section_items(self, content: str, start_marker: str, end_marker: Optional[str]) -> list:
        """Extract items from a markdown section"""
        items = []
        
        # Find section start
        start_match = re.search(re.escape(start_marker), content)
        if not start_match:
            return items
        
        start_pos = start_match.end()
        
        # Find section end
        if end_marker:
            end_match = re.search(re.escape(end_marker), content[start_pos:])
            end_pos = start_pos + end_match.start() if end_match else len(content)
        else:
            end_pos = len(content)
        
        section_content = content[start_pos:end_pos].strip()
        
        # Split by "***" or blank lines to separate items
        # Each item starts with ***Name***
        item_pattern = r'\*\*\*([^*]+)\*\*\*\.?\s*([^\*]+?)(?=\*\*\*|$)'
        matches = re.finditer(item_pattern, section_content, re.DOTALL)
        
        for match in matches:
            item_name = match.group(1).strip()
            item_desc = match.group(2).strip()
            # Remove extra whitespace
            item_desc = re.sub(r'\s+', ' ', item_desc)
            items.append(f"{item_name}. {item_desc}")
        
        return items
    
    def _extract_description(self, content: str) -> str:
        """Extract monster description (flavor text)"""
        # Get everything before the type line
        type_line_match = re.search(r'\*[^,]+,\s+[^*]+\*', content)
        if type_line_match:
            desc = content[:type_line_match.start()].strip()
            # Remove the title (first line starting with #)
            desc = re.sub(r'^#[^\n]+\n', '', desc).strip()
            return desc
        return ""
    
    def find_monster_by_name(self, monster_name: str) -> Optional[Monster]:
        """
        Search for a monster by name in the SRD
        
        Args:
            monster_name: Name of the monster to find
        
        Returns:
            Monster instance or None if not found
        """
        # Convert name to expected filename format
        filename = monster_name.lower().replace(' ', '_').replace('-', '_') + '.md'
        
        # Search in monsters directory
        monster_file = self.monsters_path / filename
        
        if monster_file.exists():
            return self.parse_monster_file(f"08_monsters_and_npcs/{filename}")
        
        # Try searching for partial matches
        for file in self.monsters_path.glob('*.md'):
            if monster_name.lower() in file.stem.lower():
                return self.parse_monster_file(f"08_monsters_and_npcs/{file.name}")
        
        print(f"[MonsterParser] Monster not found: {monster_name}")
        return None


# Example usage
if __name__ == "__main__":
    
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    
    from BackEnd.component.Class.monsters.monster import Monster
    from BackEnd.component.Class.monsters.monster_parser import MonsterParser
    
    parser = MonsterParser()
    tarrasque = parser.find_monster_by_name("Tarrasque")
    if tarrasque:
        print(tarrasque.full_description())