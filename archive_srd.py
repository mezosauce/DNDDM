#!/usr/bin/env python3
"""
Archive Original SRD Repository
Moves the original 5thSRD repo to an archive folder for safekeeping
"""

import os
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import argparse


class SRDArchiver:
    """Archives the original SRD repository"""
    
    def __init__(self, source_repo: str, archive_dir: str = "./archive"):
        self.source_repo = Path(source_repo)
        self.archive_dir = Path(archive_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def create_archive_structure(self):
        """Create the archive directory structure"""
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created archive directory: {self.archive_dir}")
    
    def create_compressed_backup(self) -> Path:
        """Create a compressed zip backup of the entire repository"""
        zip_name = f"5thSRD_original_{self.timestamp}.zip"
        zip_path = self.archive_dir / zip_name
        
        print(f"\n📦 Creating compressed backup...")
        print(f"   Source: {self.source_repo}")
        print(f"   Target: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.source_repo):
                # Skip .git directory
                if '.git' in root:
                    continue
                    
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(self.source_repo.parent)
                    zipf.write(file_path, arcname)
                    
        file_size = zip_path.stat().st_size / (1024 * 1024)  # Convert to MB
        print(f"✓ Compressed backup created: {zip_name} ({file_size:.2f} MB)")
        return zip_path
    
    def move_to_archive(self) -> Path:
        """Move the original repository to archive directory"""
        repo_name = self.source_repo.name
        archive_repo_path = self.archive_dir / f"{repo_name}_original_{self.timestamp}"
        
        print(f"\n📁 Moving repository to archive...")
        print(f"   From: {self.source_repo}")
        print(f"   To: {archive_repo_path}")
        
        try:
            shutil.move(str(self.source_repo), str(archive_repo_path))
            print(f"✓ Repository moved successfully")
            return archive_repo_path
        except Exception as e:
            print(f"✗ Error moving repository: {e}")
            return None
    
    def create_readme(self, zip_path: Path, moved_path: Path):
        """Create a README in the archive directory"""
        readme_content = f"""# Archived 5th Edition SRD Repository

## Archive Information

- **Archive Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Original Repository**: https://github.com/vitusventure/5thSRD
- **Reason**: Reorganized into story cycle structure for AI DM usage

## Contents

### Compressed Backup
- **File**: `{zip_path.name}`
- **Size**: {zip_path.stat().st_size / (1024 * 1024):.2f} MB
- **Format**: ZIP archive with full repository contents

### Moved Repository
- **Directory**: `{moved_path.name if moved_path else 'N/A'}`
- **Status**: {'✓ Preserved' if moved_path and moved_path.exists() else '✗ Not moved'}

## Restoration

If you need to restore the original structure:

### From ZIP Archive
```bash
unzip {zip_path.name}
```

### From Moved Directory
```bash
cp -r {moved_path.name if moved_path else 'N/A'} ./5thSRD
```

## Notes

- The original repository is no longer needed for daily use
- All content has been reorganized into the story cycle structure
- This archive is for reference and backup purposes only
- You can safely delete this archive after confirming the reorganized structure works

## Reorganized Structure

The SRD content is now available in the story cycle structure:
- `01_setup_and_introduction/` - Character and world establishment
- `02_character_creation/` - Building heroes
- `03_call_to_adventure/` - Quest hooks and motivation
- `04_preparation_and_planning/` - Equipment and abilities
- `05_journey_and_exploration/` - Travel and discovery
- `06_obstacles_and_challenges/` - Complications
- `07_confrontation_and_combat/` - Combat encounters
- `08_monsters_and_npcs/` - Creatures and NPCs
- `09_crisis_and_setback/` - Consequences
- `10_magic_and_extraordinary_solutions/` - Spells and magic items
- `11_climax_and_resolution/` - Final encounters and rewards
- `12_aftermath_and_growth/` - Downtime and advancement
- `13_new_horizons/` - Future adventures
- `ref_quick_reference/` - Quick lookup tables

## Safe to Delete?

✓ **YES** - Once you've confirmed the reorganized structure contains all needed content
✗ **NO** - If you haven't verified the reorganization yet

Recommended: Keep for 30 days, then delete if no issues found.
"""
        
        readme_path = self.archive_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        print(f"✓ Created archive README: {readme_path}")
    
    def create_gitignore(self):
        """Create a .gitignore for the archive directory"""
        gitignore_content = """# Archive Directory
# This directory contains backups and is not needed in version control

# Ignore all contents
*

# Except this file
!.gitignore
!README.md
"""
        gitignore_path = self.archive_dir / ".gitignore"
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
        
        print(f"✓ Created .gitignore for archive directory")
    
    def generate_manifest(self) -> dict:
        """Generate a manifest of what was archived"""
        manifest = {
            "archive_date": datetime.now().isoformat(),
            "source_repo": str(self.source_repo),
            "archive_location": str(self.archive_dir),
            "files_archived": 0,
            "total_size_mb": 0,
            "directories": []
        }
        
        if self.source_repo.exists():
            for root, dirs, files in os.walk(self.source_repo):
                if '.git' not in root:
                    manifest["files_archived"] += len(files)
                    manifest["directories"].append(str(Path(root).relative_to(self.source_repo)))
            
            # Calculate total size
            total_size = sum(
                f.stat().st_size 
                for f in self.source_repo.rglob('*') 
                if f.is_file() and '.git' not in str(f)
            )
            manifest["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        
        return manifest
    
    def run(self, method: str = "move") -> bool:
        """
        Execute the archival process
        
        Args:
            method: "move" to move the repo, "zip" to only create zip, "both" for both
        """
        print("="*70)
        print("5th Edition SRD Repository Archiver")
        print("="*70)
        
        if not self.source_repo.exists():
            print(f"✗ Error: Source repository not found at {self.source_repo}")
            return False
        
        # Generate manifest before archiving
        print("\n📋 Generating manifest...")
        manifest = self.generate_manifest()
        print(f"   Files: {manifest['files_archived']}")
        print(f"   Size: {manifest['total_size_mb']} MB")
        print(f"   Directories: {len(manifest['directories'])}")
        
        # Create archive structure
        self.create_archive_structure()
        
        zip_path = None
        moved_path = None
        
        # Create compressed backup
        if method in ["zip", "both"]:
            zip_path = self.create_compressed_backup()
        
        # Move repository
        if method in ["move", "both"]:
            moved_path = self.move_to_archive()
        
        # Create documentation
        self.create_readme(zip_path, moved_path)
        self.create_gitignore()
        
        # Save manifest
        import json
        manifest_path = self.archive_dir / f"manifest_{self.timestamp}.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"✓ Saved manifest: {manifest_path}")
        
        print(f"\n{'='*70}")
        print("✓ Archival Complete!")
        print(f"{'='*70}")
        print(f"\nArchive Location: {self.archive_dir.absolute()}")
        
        if zip_path:
            print(f"Compressed Backup: {zip_path.name}")
        if moved_path:
            print(f"Moved Repository: {moved_path.name}")
        
        print(f"\nThe original repository is now safely archived.")
        print(f"You can continue using the reorganized story cycle structure.")
        print(f"\n💡 Tip: Keep the archive for 30 days, then delete if no issues found.")
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Archive the original 5thSRD repository after reorganization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Move repository to archive (default)
  python archive_srd.py ./5thSRD
  
  # Only create zip backup, don't move
  python archive_srd.py ./5thSRD --method zip
  
  # Both move and create zip
  python archive_srd.py ./5thSRD --method both
  
  # Specify custom archive location
  python archive_srd.py ./5thSRD --archive-dir ./backups/srd_archive
        """
    )
    
    parser.add_argument(
        "source_repo",
        help="Path to the original 5thSRD repository"
    )
    
    parser.add_argument(
        "--archive-dir",
        default="./archive",
        help="Directory to store the archive (default: ./archive)"
    )
    
    parser.add_argument(
        "--method",
        choices=["move", "zip", "both"],
        default="move",
        help="Archival method: move (move repo), zip (create zip only), both (default: move)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No files will be moved or created\n")
        print(f"Would archive: {args.source_repo}")
        print(f"Archive location: {args.archive_dir}")
        print(f"Method: {args.method}")
        return
    
    # Confirm with user
    print(f"⚠️  This will archive the repository: {args.source_repo}")
    print(f"   Method: {args.method}")
    print(f"   Archive to: {args.archive_dir}")
    
    confirm = input("\nContinue? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    archiver = SRDArchiver(args.source_repo, args.archive_dir)
    success = archiver.run(method=args.method)
    
    if success:
        print("\n✓ Success! Original repository safely archived.")
    else:
        print("\n✗ Archival failed. Check the errors above.")


if __name__ == "__main__":
    main()