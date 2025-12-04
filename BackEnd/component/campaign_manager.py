#!/usr/bin/env python3
"""
Campaign Manager - Phased Session System
Manages campaigns with structured phases and persistent storage
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict, field
import shutil


from component.Class.Character import Character, character_to_dict, character_from_dict


@dataclass
class Campaign:
    """Campaign data"""
    name: str
    created_date: str
    current_phase: str
    party_size: int
    characters: List[Dict] = field(default_factory=list) 
    setup_complete: bool = False
    adventure_complete: bool = False
    preparation_complete: bool = False
    session_number: int = 0
    description: str = ""
    story_package_tracker: Optional[Dict] = None    
    story_state: Optional[Dict] = None
    
    def __post_init__(self):
        if self.characters is None:
            self.characters = []


class CampaignManager:
    """Manages campaigns with phased workflow"""
    
    PHASES = {
        "setup": {
            "name": "Setup & Character Creation",
            "description": "Create characters and establish the party",
            "story_phases": ["01_setup_and_introduction", "02_character_creation"]
        },
        "call_to_adventure": {
            "name": "Call to Adventure & Preparation",
            "description": "Set up the quest and prepare for the journey",
            "story_phases": ["03_call_to_adventure", "04_preparation_and_planning"]
        },
        "active_campaign": {
            "name": "Active Campaign",
            "description": "The adventure begins!",
            "story_phases": [
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
        }
    }
    
    def __init__(self, campaigns_dir: str = "./campaigns"):
        self.campaigns_dir = Path(campaigns_dir)
        self.campaigns_dir.mkdir(exist_ok=True)
    
    def create_campaign(self, name: str, party_size: int, description: str = "") -> Campaign:
        """Create a new campaign"""
        if party_size < 1 or party_size > 8:
            raise ValueError("Party size must be between 1 and 8")
        
        # Create campaign folder
        campaign_folder = self.campaigns_dir / self._sanitize_name(name)
        if campaign_folder.exists():
            raise ValueError(f"Campaign '{name}' already exists")
        
        campaign_folder.mkdir(parents=True)
        
        # Create subfolders
        (campaign_folder / "characters").mkdir()
        (campaign_folder / "sessions").mkdir()
        (campaign_folder / "notes").mkdir()
        
        # Create campaign object
        campaign = Campaign(
            name=name,
            created_date=datetime.now().isoformat(),
            current_phase="setup",
            party_size=party_size,
            description=description
        )
        
        # Save campaign metadata
        self._save_campaign(campaign)
        
        # Create campaign setup markdown
        self._create_campaign_setup_file(campaign)
        
        return campaign
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize campaign name for folder name"""
        return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name).strip()
    
    def _get_campaign_folder(self, campaign_name: str) -> Path:
        """Get campaign folder path"""
        return self.campaigns_dir / self._sanitize_name(campaign_name)
    
    def _save_campaign(self, campaign: Campaign):
        """Save campaign metadata"""
        folder = self._get_campaign_folder(campaign.name)
        metadata_file = folder / "campaign.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(campaign), f, indent=2)

    def _save_campaign_dict(self, campaign_name: str, campaign_dict: dict):
        """Save campaign metadata from dict"""
        folder = self._get_campaign_folder(campaign_name)
        metadata_file = folder / "campaign.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(campaign_dict, f, indent=2)

    def load_campaign(self, campaign_name: str) -> Campaign:
        """Load campaign from disk"""
        folder = self._get_campaign_folder(campaign_name)
        metadata_file = folder / "campaign.json"
        
        if not metadata_file.exists():
            raise ValueError(f"Campaign '{campaign_name}' not found")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Campaign(**data)
    
    def list_campaigns(self) -> List[Dict]:
        """List all campaigns"""
        campaigns = []
        for folder in self.campaigns_dir.iterdir():
            if folder.is_dir():
                metadata_file = folder / "campaign.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        campaigns.append({
                            "name": data["name"],
                            "created_date": data["created_date"],
                            "current_phase": data["current_phase"],
                            "party_size": data["party_size"],
                            "session_number": data["session_number"]
                        })
        return campaigns
    
    def add_character(self, campaign_name: str, character: Character):
        """Add a character to the campaign"""
        campaign = self.load_campaign(campaign_name)
        
        if len(campaign.characters) >= campaign.party_size:
            raise ValueError(f"Campaign already has {campaign.party_size} characters (max)")
        
        # Save character as individual file using new serialization
        folder = self._get_campaign_folder(campaign_name)
        char_file = folder / "characters" / f"{self._sanitize_name(character.name)}.json"
        
        # Use character_to_dict to include class_type metadata
        char_dict = character_to_dict(character)
        
        with open(str(char_file), 'w', encoding='utf-8') as f:
            json.dump(char_dict, f, indent=2)
        
        # Add to campaign
        campaign.characters.append(char_dict)
        
        # Update campaign setup markdown
        self._update_campaign_setup_file(campaign)
        
        # Check if setup is complete
        if len(campaign.characters) == campaign.party_size:
            campaign.setup_complete = True
        
        self._save_campaign(campaign)
        
        return campaign
    
    def update_character(self, campaign_name: str, character: Character):
            """Update an existing character"""
            campaign = self.load_campaign(campaign_name)
            
            # Use character_to_dict for proper serialization
            char_dict = character_to_dict(character)
            
            # Find and update character in campaign
            for i, char_data in enumerate(campaign.characters):
                if char_data['name'] == character.name:
                    campaign.characters[i] = char_dict
                    break
            else:
                raise ValueError(f"Character '{character.name}' not found in campaign")
            
            # Save character file
            folder = self._get_campaign_folder(campaign_name)
            char_file = folder / "characters" / f"{self._sanitize_name(character.name)}.json"
            
            with open(char_file, 'w', encoding='utf-8') as f:
                json.dump(char_dict, f, indent=2)
            
            # Update campaign setup markdown
            self._update_campaign_setup_file(campaign)
            
            self._save_campaign(campaign)
            
            return campaign
    
    def get_characters(self, campaign_name: str) -> List[Character]:
        """Get all characters in campaign"""
        campaign = self.load_campaign(campaign_name)
        # Use character_from_dict to instantiate correct class types
        return [character_from_dict(char_data) for char_data in campaign.characters]
    
    def get_character(self, campaign_name: str, character_name: str) -> Optional[Character]:
        """Get a specific character by name"""
        characters = self.get_characters(campaign_name)
        for char in characters:
            if char.name == character_name:
                return char
        return None
    
    def advance_phase(self, campaign_name: str) -> Campaign:
        """Advance campaign to next phase"""
        campaign = self.load_campaign(campaign_name)
        
        if campaign.current_phase == "setup":
            if not campaign.setup_complete:
                raise ValueError("Cannot advance: Setup not complete (add all characters first)")
            campaign.current_phase = "call_to_adventure"
            
        elif campaign.current_phase == "call_to_adventure":
            if not campaign.adventure_complete:
                raise ValueError("Cannot advance: Mark adventure phase as complete first")
            campaign.current_phase = "active_campaign"
            campaign.session_number = 1
            self._create_session_file(campaign, 1)
            
        else:
            raise ValueError("Campaign is already in active phase")
        
        self._save_campaign(campaign)
        return campaign
    
    def mark_phase_complete(self, campaign_name: str, phase: str):
        """Mark a phase as complete"""
        campaign = self.load_campaign(campaign_name)
        
        if phase == "setup":
            campaign.setup_complete = True
        elif phase == "call_to_adventure":
            campaign.adventure_complete = True
        elif phase == "preparation":
            campaign.preparation_complete = True
        
        self._save_campaign(campaign)
        return campaign
    
    def start_new_session(self, campaign_name: str) -> int:
        """Start a new session in active campaign"""
        campaign = self.load_campaign(campaign_name)
        
        if campaign.current_phase != "active_campaign":
            raise ValueError("Can only create sessions in active campaign phase")
        
        campaign.session_number += 1
        self._create_session_file(campaign, campaign.session_number)
        self._save_campaign(campaign)
        
        return campaign.session_number
    
    def _create_campaign_setup_file(self, campaign: Campaign):
        """Create the initial campaign setup markdown file"""
        folder = self._get_campaign_folder(campaign.name)
        setup_file = folder / "CAMPAIGN_SETUP.md"
        
        content = f"""# {campaign.name}

## Campaign Information
- **Created:** {datetime.fromisoformat(campaign.created_date).strftime('%B %d, %Y')}
- **Party Size:** {campaign.party_size}
- **Current Phase:** {self.PHASES[campaign.current_phase]['name']}
- **Description:** {campaign.description or 'No description provided'}

## Party Composition
*Characters will be added below as they are created*

---

## Campaign Notes
Add your campaign notes, world-building, and story hooks here.

### Setting

### Major NPCs

### Plot Hooks

### House Rules

---
*This file is automatically updated as characters are added.*
"""
        
        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _update_campaign_setup_file(self, campaign: Campaign):
        """Update campaign setup file with characters - ENHANCED with new fields"""
        folder = self._get_campaign_folder(campaign.name)
        setup_file = folder / "CAMPAIGN_SETUP.md"
        
        # Read existing content
        with open(setup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the party composition section
        party_section_start = content.find("## Party Composition")
        party_section_end = content.find("---", party_section_start)
        
        # Build new party section with ENHANCED details
        party_content = "\n## Party Composition\n\n"
        
        for char_data in campaign.characters:
            char = character_from_dict(char_data)
            
            party_content += f"""### {char.name}
- **Race:** {char.race}
- **Class:** {char.char_class}
- **Background:** {char.background}
- **Alignment:** {char.alignment}
- **Level:** {char.level}
- **HP:** {char.hp}/{char.max_hp}
- **AC:** {char.ac}

**Ability Scores:**
- STR: {char.stats['strength']} | DEX: {char.stats['dexterity']} | CON: {char.stats['constitution']}
- INT: {char.stats['intelligence']} | WIS: {char.stats['wisdom']} | CHA: {char.stats['charisma']}

**Proficiencies:**
- Skills: {', '.join(char.skill_proficiencies) if char.skill_proficiencies else 'None'}

**Languages:** {', '.join(char.languages_known) if char.languages_known else 'Common'}

**Personality:**
- Traits: {', '.join(char.personality_traits) if char.personality_traits else 'None'}
- Ideal: {char.ideal or 'None'}
- Bond: {char.bond or 'None'}
- Flaw: {char.flaw or 'None'}


**Background Feature:** {char.background_feature or 'None'}

**Notes:** {char.notes or 'None'}

---

"""
        
        # Replace party section
        new_content = content[:party_section_start] + party_content + content[party_section_end:]
        
        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
    
    def _create_session_file(self, campaign: Campaign, session_num: int):
        """Create a new session notes file"""
        folder = self._get_campaign_folder(campaign.name)
        session_file = folder / "sessions" / f"session_{session_num:03d}.md"
        
        content = f"""# Session {session_num} - {campaign.name}

**Date:** {datetime.now().strftime('%B %d, %Y')}

## Session Summary
*Add your session summary here*

## Events
- 

## NPCs Encountered
- 

## Locations Visited
- 

## Items Found
- 

## Currency Changes
- 

## Combat Encounters
- 

## Quests Updated
- 

## Notes for Next Session
- 

---
*Session started: {datetime.now().strftime('%I:%M %p')}*
"""
        
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_campaign_context(self, campaign_name: str) -> Dict:
        """Get full campaign context for AI DM - UPDATED with preparations support"""
        campaign = self.load_campaign(campaign_name)
        characters = self.get_characters(campaign_name)
        
        # Read campaign setup
        folder = self._get_campaign_folder(campaign_name)
        setup_file = folder / "CAMPAIGN_SETUP.md"
        
        setup_content = ""
        if setup_file.exists():
            with open(setup_file, 'r', encoding='utf-8') as f:
                setup_content = f.read()
        
        # Read quest preparations (Phase 2 output)
        preparations_content = ""
        preparations_file = folder / "preparations.md"
        if preparations_file.exists():
            with open(preparations_file, 'r', encoding='utf-8') as f:
                preparations_content = f.read()
        
        # Get latest session notes if in active campaign
        latest_session = ""
        if campaign.current_phase == "active_campaign" and campaign.session_number > 0:
            session_file = folder / "sessions" / f"session_{campaign.session_number:03d}.md"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    latest_session = f.read()
        
        return {
            "campaign": asdict(campaign),
            "characters": [asdict(char) for char in characters],
            "setup_content": setup_content,
            "preparations_content": preparations_content,
            "latest_session": latest_session,
            "phase_info": self.PHASES[campaign.current_phase],
            "available_story_phases": self.PHASES[campaign.current_phase]["story_phases"]
        }
    
    def delete_campaign(self, campaign_name: str):
        """Delete a campaign (moves to trash)"""
        folder = self._get_campaign_folder(campaign_name)
        if not folder.exists():
            raise ValueError(f"Campaign '{campaign_name}' not found")
        
        # Create trash folder
        trash_folder = self.campaigns_dir / "_trash"
        trash_folder.mkdir(exist_ok=True)
        
        # Move to trash with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        trash_dest = trash_folder / f"{folder.name}_{timestamp}"
        shutil.move(str(folder), str(trash_dest))
        
        return True


# ============================================================================
# Flask Integration Functions
# ============================================================================

def get_campaign_manager():
    """Get or create campaign manager instance"""
    if not hasattr(get_campaign_manager, 'instance'):
        get_campaign_manager.instance = CampaignManager()
    return get_campaign_manager.instance


# ============================================================================
# CLI for Testing
# ============================================================================

def main():
    """CLI for testing campaign manager"""
    import sys
    
    manager = CampaignManager()
    
    if len(sys.argv) < 2:
        print("Campaign Manager CLI")
        print("\nCommands:")
        print("  create <name> <party_size> - Create new campaign")
        print("  list                        - List all campaigns")
        print("  add-char <campaign> <name>  - Add character")
        print("  show <campaign>             - Show campaign info")
        print("  advance <campaign>          - Advance to next phase")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "create":
        name = sys.argv[2]
        party_size = int(sys.argv[3])
        desc = sys.argv[4] if len(sys.argv) > 4 else ""
        campaign = manager.create_campaign(name, party_size, desc)
        print(f"✓ Created campaign: {campaign.name}")
        print(f"  Party size: {party_size}")
        print(f"  Folder: campaigns/{manager._sanitize_name(name)}/")
    
    elif cmd == "list":
        campaigns = manager.list_campaigns()
        if not campaigns:
            print("No campaigns found")
        else:
            print(f"Found {len(campaigns)} campaign(s):\n")
            for c in campaigns:
                print(f"  • {c['name']}")
                print(f"    Phase: {c['current_phase']}")
                print(f"    Party: {c['party_size']} characters")
                print(f"    Sessions: {c['session_number']}")
                print()
    
    elif cmd == "add-char":
        campaign_name = sys.argv[2]
        char_name = sys.argv[3]
        
        # Interactive character creation
        print(f"\nCreating character: {char_name}")
        race = input("Race: ")
        char_class = input("Class: ")
        background = input("Background: ")
        
        char = Character(
            name=char_name,
            race=race,
            char_class=char_class,
            background=background
        )
        
        campaign = manager.add_character(campaign_name, char)
        print(f"✓ Added {char_name} to {campaign_name}")
        print(f"  Characters: {len(campaign.characters)}/{campaign.party_size}")
        
        if campaign.setup_complete:
            print("  ✓ Setup complete! Ready to advance to next phase.")
    
    elif cmd == "show":
        campaign_name = sys.argv[2]
        context = manager.get_campaign_context(campaign_name)
        
        print(f"\nCampaign: {context['campaign']['name']}")
        print(f"Phase: {context['phase_info']['name']}")
        print(f"Characters: {len(context['characters'])}/{context['campaign']['party_size']}")
        print(f"\nCharacters:")
        for char in context['characters']:
            print(f"  • {char['name']} - {char['race']} {char['char_class']}")
            print(f"    Wealth: {Character(**char).get_total_gold_value():.2f} gp")
    
    elif cmd == "advance":
        campaign_name = sys.argv[2]
        campaign = manager.advance_phase(campaign_name)
        print(f"✓ Advanced to: {manager.PHASES[campaign.current_phase]['name']}")


if __name__ == "__main__":
    main()