"""
AI Prompts Loader
Loads prompt templates from the BackEnd/prompts/ directory text files.
"""

from pathlib import Path

# Get the prompts directory
PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(filename: str) -> str:
    """Load a prompt from a text file."""
    filepath = PROMPTS_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        return f"[Prompt file not found: {filename}]"

# Load all prompts with their exact names matching the .txt files
init_story_prompt = load_prompt("init_story_prompt.txt")
pre_combat_prompt = load_prompt("pre_combat_prompt.txt")
post_combat_prompt = load_prompt("post_combat_prompt.txt")
pre_diceroll_prompt = load_prompt("pre_diceroll_prompt.txt")
post_diceroll_prompt = load_prompt("post_diceroll_prompt.txt")
pre_question_prompt = load_prompt("pre_question_prompt.txt")
post_question_prompt = load_prompt("post_question_prompt.txt")
wrapup_prompt = load_prompt("wrapup_prompt.txt")
prep_phase_prompt = load_prompt("prep_phase_prompt.txt")
active_phase_prompt = load_prompt("active_phase_prompt.txt")

# Aliases for compatibility with different naming conventions
campaign_init_prompt = init_story_prompt

# For conditional evaluation (if needed later)
conditional_evaluation_prompt = """
Based on the previous dice roll outcome, determine the story's path forward.

If the roll succeeded:
- The party avoids additional danger
- Narrate how their success helps them progress
- Skip to the conclusion of this chapter

If the roll failed:
- Additional challenges arise
- Set up the circumstances for a second combat encounter
- Make the failure feel consequential

Evaluate the situation and guide the narrative appropriately.
"""