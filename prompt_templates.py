#!/usr/bin/env python3
"""
AI Prompt Template System
Loads customizable prompts from text files for different campaign phases
"""

from pathlib import Path


class PromptTemplates:
    """Manages AI prompt templates for different campaign phases"""
    
    def __init__(self, prompts_dir="prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(exist_ok=True)
        
        # Create default templates if they don't exist
        self._create_default_templates()
    
    def _create_default_templates(self):
        """Create default prompt template files"""
        
        # Prep Phase Prompt
        prep_prompt_path = self.prompts_dir / "prep_phase_prompt.txt"
        if not prep_prompt_path.exists():
            prep_prompt_path.write_text("""You are an expert Dungeon Master helping to prepare a D&D 5th Edition campaign.

=== YOUR ROLE IN PREP PHASE ===
You are assisting the DM in planning the adventure BEFORE gameplay begins. Focus on:
- Creating compelling quest hooks that engage the party
- Establishing the setting, atmosphere, and tone
- Identifying key NPCs and their motivations
- Planning potential obstacles and encounters
- Suggesting equipment and resources needed
- Discussing party composition and roles
- Building anticipation for the adventure

=== RESPONSE STYLE ===
- Be creative and engaging with quest hooks
- Ask clarifying questions about the party and their interests
- Provide multiple options when suggesting ideas
- Keep responses focused on planning and preparation
- Include practical DM tips and considerations
- Reference relevant D&D lore when appropriate
- Help establish "why" the party would take this quest

=== TONE ===
Collaborative, helpful, and creative. You're brainstorming WITH the DM, not dictating to them.
Think of yourself as an experienced DM sharing ideas over coffee.

=== EXAMPLE INTERACTIONS ===
DM: "Create a quest hook for my party"
You: "I'd love to help! Tell me a bit about your party first - what motivates them? 
Are they heroic do-gooders, treasure seekers, or something else? Here are three quest 
hook ideas to start:

1. **The Missing Caravan** - A wealthy merchant offers gold to find his missing supply 
caravan. Unknown to him, goblins have taken the goods to their cave hideout.

2. **Ancient Ruins** - Strange lights have been seen at old ruins outside town. The 
local sage believes something ancient has awakened.

3. **Tavern Brawl Gone Wrong** - What starts as a bar fight reveals that mysterious 
cultists are kidnapping townsfolk.

Which direction appeals to your group?"
""", encoding='utf-8')
        
        # Active Campaign Prompt  
        active_prompt_path = self.prompts_dir / "active_phase_prompt.txt"
        if not active_prompt_path.exists():
            active_prompt_path.write_text("""You are an expert Dungeon Master running a D&D 5th Edition campaign.

=== YOUR ROLE IN ACTIVE PLAY ===
You are actively running the game session. Your responsibilities:
- Narrate events vividly and engagingly
- Adjudicate rules fairly and consistently
- Control NPCs and monsters with distinct personalities
- Describe environments using all five senses
- Call for ability checks and saving throws
- Manage combat encounters with clear descriptions
- Respond to player actions dynamically
- Keep the story moving forward

=== RESPONSE STYLE ===
1. **Start with vivid narration** - Set the scene before mechanics
2. **Call for specific rolls when needed** - "Roll a d20 and add your Dexterity modifier"
3. **Provide clear DC targets** - "You need to beat a DC 15 to succeed"
4. **Describe outcomes dramatically** - Both success and failure
5. **Keep combat flowing** - Clear turn-by-turn descriptions
6. **Balance story and mechanics** - Don't get bogged down in rules

=== COMBAT FORMAT ===
When combat occurs:
1. Describe the scene dramatically (set the stakes)
2. State required rolls (attack, damage, saves)
3. Describe results vividly (make it cinematic)
4. Track initiative and turn order
5. Describe enemy actions and motivations

Example: "The orc chieftain roars and charges! Roll initiative. He swings his greataxe 
at you with brutal force - roll a d20 and add your Armor Class. If it meets or exceeds 
your AC, you'll take damage."

=== NPC VOICES ===
Give NPCs distinct personalities:
- Use dialogue to show character
- Vary speech patterns (formal, casual, crude)
- Show emotions through actions
- Make them memorable

=== TONE ===
Immersive, dramatic, and fair. Make the players feel like heroes in an epic story.
Be the DM who makes them say "I can't wait for next session!"

=== KEY PRINCIPLES ===
- "Yes, and..." - Build on player ideas
- Failed rolls ≠ boring - Make failures interesting
- Players are the heroes - Let them shine
- Rules serve the story - Don't let rules slow the fun
""", encoding='utf-8')
    
    def get_prompt(self, phase):
        """
        Load the appropriate prompt template
        
        Args:
            phase: 'prep' or 'active'
            
        Returns:
            str: The prompt template content
        """
        if phase == 'prep':
            path = self.prompts_dir / "prep_phase_prompt.txt"
        elif phase == 'active':
            path = self.prompts_dir / "active_phase_prompt.txt"
        else:
            raise ValueError(f"Unknown phase: {phase}")
        
        if not path.exists():
            self._create_default_templates()
        
        return path.read_text(encoding='utf-8')
    
    def update_prompt(self, phase, new_content):
        """
        Update a prompt template
        
        Args:
            phase: 'prep' or 'active'
            new_content: New prompt content
        """
        if phase == 'prep':
            path = self.prompts_dir / "prep_phase_prompt.txt"
        elif phase == 'active':
            path = self.prompts_dir / "active_phase_prompt.txt"
        else:
            raise ValueError(f"Unknown phase: {phase}")
        
        path.write_text(new_content, encoding='utf-8')
    
    def get_all_prompts(self):
        """Get both prompts as a dictionary"""
        return {
            'prep': self.get_prompt('prep'),
            'active': self.get_prompt('active')
        }


def create_full_prompt(phase, campaign_context, query, srd_content=""):
    """
    Create complete AI prompt using templates
    
    Args:
        phase: 'prep' or 'active'
        campaign_context: Dict with campaign info
        query: User's question
        srd_content: Relevant D&D rules (optional)
        
    Returns:
        str: Complete prompt for AI
    """
    templates = PromptTemplates()
    base_prompt = templates.get_prompt(phase)
    
    # Build the complete prompt
    prompt = f"{base_prompt}\n\n"
    
    # Add campaign context
    prompt += "=== CAMPAIGN CONTEXT ===\n"
    prompt += f"Campaign: {campaign_context.get('name', 'Unknown')}\n"
    
    if campaign_context.get('description'):
        prompt += f"Campaign Description: {campaign_context['description']}\n"
    
    prompt += f"Party Size: {campaign_context.get('party_size', 0)}\n"
    
    if campaign_context.get('characters'):
        prompt += "\nParty Members:\n"
        for char in campaign_context['characters']:
            stats = char.get('stats', {})
            prompt += f"- {char.get('name', 'Unknown')}: "
            prompt += f"{char.get('race', 'Unknown')} {char.get('char_class', 'Unknown')} "
            prompt += f"(Level {char.get('level', 1)}, HP: {char.get('hp', 0)}/{char.get('max_hp', 0)}, "
            prompt += f"AC: {char.get('ac', 0)})\n"
            if stats:
                prompt += f"  Stats: STR {stats.get('strength', 10)}, "
                prompt += f"DEX {stats.get('dexterity', 10)}, "
                prompt += f"CON {stats.get('constitution', 10)}, "
                prompt += f"INT {stats.get('intelligence', 10)}, "
                prompt += f"WIS {stats.get('wisdom', 10)}, "
                prompt += f"CHA {stats.get('charisma', 10)}\n"
    
    # Phase-specific context
    if phase == 'prep':
        prompt += "\n=== PREPARATION PHASE ===\n"
        prompt += "You are helping plan the adventure before Session 1 begins.\n"
        if campaign_context.get('quest_objective'):
            prompt += f"Quest Objective: {campaign_context['quest_objective']}\n"
    
    elif phase == 'active':
        prompt += "\n=== ACTIVE SESSION ===\n"
        prompt += f"Session Number: {campaign_context.get('session_number', 1)}\n"
        
        if campaign_context.get('current_location'):
            prompt += f"Current Location: {campaign_context['current_location']}\n"
        
        if campaign_context.get('active_combat'):
            prompt += "⚔️ COMBAT IS ACTIVE\n"
        
        if campaign_context.get('recent_events'):
            prompt += "\nRecent Events:\n"
            for event in campaign_context['recent_events'][-5:]:
                prompt += f"- {event}\n"
    
    # Add SRD content if provided
    if srd_content and len(srd_content) > 100:
        prompt += f"\n=== D&D 5E RULES REFERENCE ===\n{srd_content}\n"
    
    # Add the user's query
    prompt += f"\n=== {'DM' if phase == 'prep' else 'PLAYER'} QUERY ===\n{query}\n"
    
    # Add response instruction
    if phase == 'prep':
        prompt += "\n=== YOUR RESPONSE ===\nHelp plan the adventure. Be creative and collaborative:\n\nDM: "
    else:
        prompt += "\n=== YOUR RESPONSE ===\nAs the Dungeon Master, respond to the player's action:\n\nDM: "
    
    return prompt


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Create template system
    templates = PromptTemplates()
    
    print("=" * 70)
    print("📜 AI PROMPT TEMPLATE SYSTEM")
    print("=" * 70)
    print("\n✓ Created prompt templates in 'prompts/' directory:")
    print("  - prep_phase_prompt.txt")
    print("  - active_phase_prompt.txt")
    print("\n💡 You can edit these files to customize AI behavior!")
    print("\n" + "=" * 70)
    
    # Test prompt creation
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("\n📋 TESTING PROMPT CREATION\n")
        
        campaign_context = {
            'name': 'The Lost Mines',
            'party_size': 3,
            'description': 'A classic adventure',
            'characters': [
                {'name': 'Aragorn', 'race': 'Human', 'char_class': 'Ranger', 
                 'level': 3, 'hp': 25, 'max_hp': 25, 'ac': 15},
                {'name': 'Legolas', 'race': 'Elf', 'char_class': 'Fighter', 
                 'level': 3, 'hp': 30, 'max_hp': 30, 'ac': 16}
            ]
        }
        
        print("PREP PHASE EXAMPLE:")
        print("-" * 70)
        prompt = create_full_prompt(
            phase='prep',
            campaign_context=campaign_context,
            query="Create a quest hook for my party"
        )
        print(prompt[:800] + "...\n")
        
        print("\nACTIVE PHASE EXAMPLE:")
        print("-" * 70)
        campaign_context['session_number'] = 1
        campaign_context['current_location'] = "Goblin Cave"
        campaign_context['recent_events'] = ["Entered cave", "Found tracks"]
        
        prompt = create_full_prompt(
            phase='active',
            campaign_context=campaign_context,
            query="I attack the goblin with my sword"
        )
        print(prompt[:800] + "...")