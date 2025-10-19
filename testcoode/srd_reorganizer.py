#!/usr/bin/env python3
"""
SRD Story Cycle Reorganizer
Reorganizes the 5th Edition SRD from vitusventure/5thSRD into story cycle structure
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, List

# Define the story cycle structure and file mappings
STORY_CYCLE_STRUCTURE = {
    "01_setup_and_introduction": {
        "description": "Establishing the world and characters",
        "subdirs": {
            "world_building": [
                "races.md",
                "beyond_1st_level.md",
                "alignment.md",
                "languages.md",
                "inspiration.md"
            ],
            "backgrounds": [
                "backgrounds.md",
                "personality_and_background.md"
            ],
            "cosmology": [
                "planes_of_existence.md",
                "the_planes.md"
            ]
        }
    },
    
    "02_character_creation": {
        "description": "Building heroes",
        "subdirs": {
            "classes": [
                "classes.md",
                "barbarian.md",
                "bard.md",
                "cleric.md",
                "druid.md",
                "fighter.md",
                "monk.md",
                "paladin.md",
                "ranger.md",
                "rogue.md",
                "sorcerer.md",
                "warlock.md",
                "wizard.md"
            ],
            "abilities": [
                "ability_scores.md",
                "using_ability_scores.md",
                "advantage_and_disadvantage.md",
                "proficiency_bonus.md"
            ],
            "starting_equipment": [
                "equipment.md",
                "equipment_packs.md",
                "starting_wealth.md"
            ]
        }
    },
    
    "03_call_to_adventure": {
        "description": "Inciting incidents and motivation",
        "subdirs": {
            "motivation": [
                "backgrounds.md",
                "personality_and_background.md",
                "bonds.md",
                "ideals.md",
                "flaws.md"
            ],
            "divine_calling": [
                "gods.md",
                "fantasy-historical_pantheons.md"
            ]
        }
    },
    
    "04_preparation_and_planning": {
        "description": "Getting ready for the adventure",
        "subdirs": {
            "equipment": [
                "armor.md",
                "weapons.md",
                "adventuring_gear.md",
                "tools.md",
                "mounts_and_vehicles.md",
                "trade_goods.md",
                "expenses.md"
            ],
            "abilities": [
                "feats.md",
                "multiclassing.md"
            ],
            "magic_preparation": [
                "spellcasting.md",
                "spells_by_level.md",
                "spell_lists.md"
            ]
        }
    },
    
    "05_journey_and_exploration": {
        "description": "The adventure unfolds",
        "subdirs": {
            "travel": [
                "movement.md",
                "the_environment.md",
                "between_adventures.md",
                "resting.md"
            ],
            "exploration": [
                "time.md",
                "vision_and_light.md",
                "food_and_water.md",
                "interacting_with_objects.md"
            ],
            "skills": [
                "ability_checks.md",
                "skills.md",
                "using_ability_scores.md",
                "contests.md"
            ],
            "social": [
                "social_interaction.md",
                "charisma.md"
            ]
        }
    },
    
    "06_obstacles_and_challenges": {
        "description": "Complications arise",
        "subdirs": {
            "hazards": [
                "traps.md",
                "diseases.md",
                "madness.md",
                "poisons.md",
                "objects.md"
            ],
            "environmental": [
                "the_environment.md",
                "wilderness_survival.md",
                "falling.md",
                "suffocating.md",
                "underwater_combat.md"
            ],
            "resource_depletion": [
                "exhaustion.md",
                "food_and_water.md"
            ]
        }
    },
    
    "07_confrontation_and_combat": {
        "description": "Major conflicts and battles",
        "subdirs": {
            "combat_basics": [
                "combat.md",
                "the_order_of_combat.md",
                "making_an_attack.md",
                "attack_rolls.md",
                "damage_and_healing.md",
                "initiative.md"
            ],
            "combat_actions": [
                "actions_in_combat.md",
                "bonus_actions.md",
                "reactions.md",
                "movement_and_position.md",
                "opportunity_attacks.md"
            ],
            "tactical": [
                "cover.md",
                "conditions.md",
                "grappling.md",
                "mounted_combat.md",
                "melee_attacks.md",
                "ranged_attacks.md",
                "two-weapon_fighting.md"
            ],
            "special_combat": [
                "underwater_combat.md",
                "combat_modifiers.md"
            ]
        }
    },
    
    "08_monsters_and_npcs": {
        "description": "Adversaries and allies",
        "subdirs": {
            "monster_basics": [
                "monsters.md",
                "monster_manual.md",
                "statistics.md"
            ],
            "by_type": [
                "aberrations.md",
                "beasts.md",
                "celestials.md",
                "constructs.md",
                "dragons.md",
                "elementals.md",
                "fey.md",
                "fiends.md",
                "giants.md",
                "humanoids.md",
                "monstrosities.md",
                "oozes.md",
                "plants.md",
                "undead.md"
            ],
            "legendary": [
                "legendary_creatures.md",
                "lair_actions.md"
            ]
        }
    },
    
    "09_crisis_and_setback": {
        "description": "Things get worse before they get better",
        "subdirs": {
            "consequences": [
                "damage_and_healing.md",
                "death_and_dying.md",
                "hit_points.md",
                "dropping_to_0_hit_points.md",
                "death_saving_throws.md"
            ],
            "afflictions": [
                "exhaustion.md",
                "diseases.md",
                "madness.md",
                "poisons.md",
                "conditions.md"
            ]
        }
    },
    
    "10_magic_and_extraordinary_solutions": {
        "description": "Special powers and supernatural elements",
        "subdirs": {
            "spellcasting": [
                "spellcasting.md",
                "casting_a_spell.md",
                "spell_slots.md",
                "concentration.md",
                "spell_level.md",
                "spell_components.md",
                "spell_duration.md",
                "spell_range.md",
                "spell_attack_rolls.md",
                "spell_saving_throws.md"
            ],
            "spell_lists": [
                "spells.md",
                "spell_lists.md",
                "spells_by_level.md",
                "bard_spells.md",
                "cleric_spells.md",
                "druid_spells.md",
                "paladin_spells.md",
                "ranger_spells.md",
                "sorcerer_spells.md",
                "warlock_spells.md",
                "wizard_spells.md"
            ],
            "magic_items": [
                "magic_items.md",
                "attunement.md",
                "cursed_items.md",
                "sentient_magic_items.md",
                "artifacts.md"
            ]
        }
    },
    
    "11_climax_and_resolution": {
        "description": "The final challenge",
        "subdirs": {
            "epic_encounters": [
                "legendary_creatures.md",
                "legendary_actions.md",
                "lair_actions.md",
                "mythic_encounters.md"
            ],
            "rewards": [
                "treasure.md",
                "individual_treasure.md",
                "treasure_hoard.md",
                "experience_points.md"
            ]
        }
    },
    
    "12_aftermath_and_growth": {
        "description": "Consequences and character development",
        "subdirs": {
            "downtime": [
                "between_adventures.md",
                "downtime_activities.md",
                "resting.md",
                "lifestyle_expenses.md"
            ],
            "advancement": [
                "beyond_1st_level.md",
                "leveling_up.md",
                "experience_points.md",
                "milestones.md",
                "multiclassing.md"
            ],
            "crafting": [
                "crafting.md",
                "magic_item_creation.md"
            ]
        }
    },
    
    "13_new_horizons": {
        "description": "Setup for the next adventure",
        "subdirs": {
            "reputation": [
                "renown.md",
                "fame.md"
            ],
            "world_impact": [
                "running_a_business.md",
                "building_a_stronghold.md"
            ]
        }
    },
    
    "ref_quick_reference": {
        "description": "Quick lookup during any story phase",
        "subdirs": {
            "tables": [
                "conditions.md",
                "actions_in_combat.md",
                "cover.md",
                "ability_checks.md",
                "skills.md"
            ],
            "rules_summary": [
                "README.md",
                "index.md",
                "introduction.md"
            ]
        }
    }
}


class SRDReorganizer:
    """Reorganizes SRD files into story cycle structure"""
    
    def __init__(self, source_dir: str, target_dir: str):
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.file_mapping = {}
        self.missing_files = []
        self.copied_files = []
        
    def scan_source_files(self) -> List[str]:
        """Scan source directory for all markdown files"""
        md_files = []
        for root, dirs, files in os.walk(self.source_dir):
            for file in files:
                if file.endswith('.md'):
                    rel_path = os.path.relpath(os.path.join(root, file), self.source_dir)
                    md_files.append(rel_path)
        return md_files
    
    def find_source_file(self, filename: str, available_files: List[str]) -> str:
        """Find a source file by name, trying different paths"""
        # Try exact match
        if filename in available_files:
            return filename
        
        # Try basename match
        basename = os.path.basename(filename)
        for file in available_files:
            if os.path.basename(file) == basename:
                return file
        
        # Try case-insensitive match
        basename_lower = basename.lower()
        for file in available_files:
            if os.path.basename(file).lower() == basename_lower:
                return file
        
        return None
    
    def create_structure(self):
        """Create the story cycle directory structure"""
        print(f"Creating story cycle structure in: {self.target_dir}")
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # Create README for the reorganized structure
        readme_content = """# D&D 5th Edition SRD - Story Cycle Organization

This directory contains the 5th Edition SRD reorganized into a narrative story cycle structure.

## Structure

The content is organized into phases that follow the natural flow of a D&D adventure:

"""
        
        for phase_dir, phase_data in STORY_CYCLE_STRUCTURE.items():
            phase_path = self.target_dir / phase_dir
            phase_path.mkdir(exist_ok=True)
            
            readme_content += f"\n### {phase_dir.replace('_', ' ').title()}\n"
            readme_content += f"{phase_data['description']}\n"
            
            # Create subdirectories
            for subdir in phase_data['subdirs'].keys():
                subdir_path = phase_path / subdir
                subdir_path.mkdir(exist_ok=True)
        
        readme_content += """
## Usage

Each phase contains relevant rules and content for that part of the story.
Files are organized by topic within each phase.

## Original Source

This is a reorganization of: https://github.com/vitusventure/5thSRD
"""
        
        with open(self.target_dir / "README.md", "w") as f:
            f.write(readme_content)
    
    def copy_files(self):
        """Copy files from source to target according to mapping"""
        print("\nScanning source files...")
        available_files = self.scan_source_files()
        print(f"Found {len(available_files)} markdown files in source")
        
        print("\nCopying files to story cycle structure...")
        
        for phase_dir, phase_data in STORY_CYCLE_STRUCTURE.items():
            phase_path = self.target_dir / phase_dir
            
            for subdir, files in phase_data['subdirs'].items():
                subdir_path = phase_path / subdir
                
                for filename in files:
                    source_file = self.find_source_file(filename, available_files)
                    
                    if source_file:
                        src = self.source_dir / source_file
                        dst = subdir_path / os.path.basename(filename)
                        
                        try:
                            shutil.copy2(src, dst)
                            self.copied_files.append(filename)
                            print(f"  ✓ Copied: {filename} -> {phase_dir}/{subdir}/")
                        except Exception as e:
                            print(f"  ✗ Error copying {filename}: {e}")
                            self.missing_files.append(filename)
                    else:
                        self.missing_files.append(filename)
                        print(f"  ⚠ Not found: {filename}")
    
    def create_phase_indexes(self):
        """Create index files for each phase"""
        print("\nCreating phase index files...")
        
        for phase_dir, phase_data in STORY_CYCLE_STRUCTURE.items():
            phase_path = self.target_dir / phase_dir
            
            index_content = f"# {phase_dir.replace('_', ' ').title()}\n\n"
            index_content += f"**Story Purpose:** {phase_data['description']}\n\n"
            index_content += "## Contents\n\n"
            
            for subdir, files in phase_data['subdirs'].items():
                index_content += f"### {subdir.replace('_', ' ').title()}\n\n"
                
                for filename in files:
                    file_path = phase_path / subdir / os.path.basename(filename)
                    if file_path.exists():
                        display_name = os.path.basename(filename).replace('.md', '').replace('_', ' ').title()
                        rel_path = f"{subdir}/{os.path.basename(filename)}"
                        index_content += f"- [{display_name}]({rel_path})\n"
                
                index_content += "\n"
            
            with open(phase_path / "INDEX.md", "w") as f:
                f.write(index_content)
            
            print(f"  ✓ Created index for {phase_dir}")
    
    def generate_report(self):
        """Generate a report of the reorganization"""
        report_content = f"""# SRD Reorganization Report

## Summary

- **Files copied successfully:** {len(self.copied_files)}
- **Files not found:** {len(self.missing_files)}
- **Total phases created:** {len(STORY_CYCLE_STRUCTURE)}

## Missing Files

The following files were referenced but not found in the source:

"""
        
        for filename in sorted(self.missing_files):
            report_content += f"- {filename}\n"
        
        report_content += """
## Notes

Some files may not exist in the source repository or may have different names.
This is normal - the SRD doesn't cover every possible rule variant.

You may want to:
1. Check if these files exist under different names
2. Create placeholder files for missing content
3. Adjust the story cycle structure to match available content

## Next Steps

1. Review the missing files list
2. Manually add any critical missing content
3. Update the structure mapping as needed
4. Create the query router for AI DM integration
"""
        
        with open(self.target_dir / "REORGANIZATION_REPORT.md", "w") as f:
            f.write(report_content)
        
        print(f"\n{'='*60}")
        print(f"Reorganization complete!")
        print(f"{'='*60}")
        print(f"✓ Files copied: {len(self.copied_files)}")
        print(f"⚠ Files not found: {len(self.missing_files)}")
        print(f"\nSee {self.target_dir}/REORGANIZATION_REPORT.md for details")
    
    def run(self):
        """Execute the full reorganization process"""
        print("="*60)
        print("SRD Story Cycle Reorganizer")
        print("="*60)
        
        self.create_structure()
        self.copy_files()
        self.create_phase_indexes()
        self.generate_report()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Reorganize D&D 5e SRD into story cycle structure"
    )
    parser.add_argument(
        "source",
        help="Path to the source SRD docs directory (e.g., 5thSRD/docs)"
    )
    parser.add_argument(
        "target",
        help="Path to create the reorganized structure"
    )
    
    args = parser.parse_args()
    
    reorganizer = SRDReorganizer(args.source, args.target)
    reorganizer.run()


if __name__ == "__main__":
    main()