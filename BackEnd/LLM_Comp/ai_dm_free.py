#!/usr/bin/env python3
"""
AI DM with Ollama (FREE Local LLM Integration)
No API keys required - runs completely free on your computer!
"""

import os
import json
import requests 
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

# Import the query router (assumes it's in the same directory)
try:
    from LLM_Comp.ai_dm_query_router import QueryRouter, QueryType
except ImportError:
    print("Warning: Query router not found. Install ai_dm_query_router.py in the same directory.")


@dataclass
class GameState:
    """Represents current game state"""
    current_phase: str
    party_level: int
    location: str
    active_combat: bool
    recent_events: List[str]


class SRDContentLoader:
    """Loads and manages SRD content for AI context"""
    
    def __init__(self, srd_path: str):
        self.srd_path = Path(srd_path)
    
    def load_files(self, file_paths: List[str], max_chars: int = 15000) -> str:
        """Load content from multiple files with character limit"""
        content_parts = []
        total_chars = 0
        
        for file_path in file_paths:
            full_path = Path(file_path)
            if not full_path.is_absolute():
                full_path = self.srd_path / file_path
            
            if full_path.exists() and full_path.suffix == '.md':
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        
                    # Add file header
                    header = f"\n--- {full_path.name} ---\n"
                    
                    remaining_chars = max_chars - total_chars
                    if remaining_chars <= 0:
                        break
                    
                    # Truncate if necessary
                    if len(file_content) > remaining_chars:
                        file_content = file_content[:remaining_chars] + "\n[Content truncated...]"
                    
                    content_parts.append(header + file_content)
                    total_chars += len(header) + len(file_content)
                    
                except Exception as e:
                    print(f"Error loading {full_path}: {e}")
        
        return "\n".join(content_parts)
    
    def get_phase_summary(self, phase: str) -> str:
        """Get a summary of what a phase contains"""
        index_path = self.srd_path / phase / "INDEX.md"
        if index_path.exists():
            with open(index_path, 'r') as f:
                return f.read(500)
        return f"Phase: {phase}"


class OllamaDM:
    """FREE AI Dungeon Master using Ollama (local LLM)"""
    
    def __init__(
        self,
        srd_path: str,
        ollama_url: str = "http://localhost:11434",
        default_model: str = "llama3.2:3b"
    ):
        self.srd_path = srd_path
        self.router = QueryRouter(srd_path)
        self.loader = SRDContentLoader(srd_path)
        self.ollama_url = ollama_url
        self.default_model = default_model
        
        # Check if Ollama is running
        self.ollama_available = self._check_ollama()
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def list_available_models(self) -> List[str]:
        """List all available Ollama models"""
        if not self.ollama_available:
            return []
        
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
        except:
            pass
        return []
    
    def create_prompt(
        self,
        query: str,
        game_state: GameState,
        routing_context: str,
        srd_content: str
    ) -> str:
        """Create a comprehensive prompt for the local LLM"""
        
        # Build a clear, structured prompt
        prompt = f"""You are an expert Dungeon Master for Dungeons & Dragons 5th Edition.

=== CURRENT GAME ===
Story Phase: {game_state.current_phase.replace('_', ' ').title()}
Party Level: {game_state.party_level}
Location: {game_state.location}
Combat Active: {'Yes' if game_state.active_combat else 'No'}
"""
        
        if game_state.recent_events:
            prompt += f"Recent Events: {', '.join(game_state.recent_events[-3:])}\n"
        
        prompt += f"""
=== YOUR ROLE ===
{routing_context}

=== D&D 5E RULES (Use these for accuracy) ===
{srd_content}

=== PLAYER QUERY ===
{query}

=== YOUR RESPONSE ===
As the Dungeon Master, respond to the player's query. Be descriptive, engaging, and accurate with the rules. Keep your response focused and under 250 words.

DM:"""
        
        return prompt
    
    def get_response(
        self,
        query: str,
        game_state: GameState,
        model: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict:
        """
        Get a DM response from Ollama
        
        Args:
            query: Player's question or action
            game_state: Current game state
            model: Ollama model to use (default: self.default_model)
            temperature: Creativity level (0.0-1.0, default: 0.7)
            stream: Whether to stream the response
        
        Returns:
            Dict with 'response', 'routing', and 'model' keys
        """
        
        if not self.ollama_available:
            return {
                "error": "Ollama not running. Start it with: ollama serve",
                "help": "Visit https://ollama.ai for installation instructions"
            }
        
        model = model or self.default_model
        
        # Route the query to get appropriate SRD content
        routing = self.router.get_context_files_for_ai(
            query,
            game_state.current_phase
        )
        
        # Load relevant SRD content (optimized for llama3.2:3b)
        srd_content = self.loader.load_files(
            routing['files_to_load'],
            max_chars=15000  # Balanced context for 3B models
        )
        
        # Create the prompt
        prompt = self.create_prompt(
            query,
            game_state,
            routing['ai_instructions']['context'],
            srd_content
        )
        
        # Call Ollama API
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": stream,
                    "options": {
                        "temperature": temperature,
                        "num_predict": 500,  # Optimized for llama3.2:3b
                        "top_p": 0.9,
                        "top_k": 40,
                        "repeat_penalty": 1.1
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                
                return {
                    "response": result.get('response', '').strip(),
                    "routing": routing['routing'],
                    "model": model,
                    "context_loaded": len(srd_content),
                    "files_used": [Path(f).name for f in routing['files_to_load'][:3]]
                }
            else:
                return {
                    "error": f"Ollama request failed: {response.status_code}",
                    "details": response.text
                }
                
        except requests.exceptions.Timeout:
            return {"error": "Request timed out. Try a smaller model or reduce context."}
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to Ollama. Is it running? (ollama serve)"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def get_response_streaming(
        self,
        query: str,
        game_state: GameState,
        model: Optional[str] = None,
        temperature: float = 0.7
    ):
        """
        Get a streaming response from Ollama (yields chunks as they arrive)
        
        Usage:
            for chunk in dm.get_response_streaming(query, game_state):
                print(chunk, end='', flush=True)
        """
        
        if not self.ollama_available:
            yield "Error: Ollama not running"
            return
        
        model = model or self.default_model
        
        # Route and prepare
        routing = self.router.get_context_files_for_ai(query, game_state.current_phase)
        srd_content = self.loader.load_files(routing['files_to_load'], max_chars=15000)  # Optimized for 3B models
        prompt = self.create_prompt(query, game_state, routing['ai_instructions']['context'], srd_content)
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {"temperature": temperature, "num_predict": 500, "repeat_penalty": 1.1}
                },
                stream=True,
                timeout=120
            )
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if 'response' in chunk:
                        yield chunk['response']
                        
        except Exception as e:
            yield f"\nError: {str(e)}"


def setup_ollama():
    """Guide user through Ollama setup"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║          FREE AI DM - Ollama Setup Guide                     ║
╚══════════════════════════════════════════════════════════════╝

Ollama lets you run AI models completely FREE on your computer!

STEP 1: Install Ollama
----------------------
Visit: https://ollama.ai
Download for your OS (Windows/Mac/Linux)

STEP 2: Start Ollama
--------------------
Open terminal and run:
    ollama serve

STEP 3: Download a Model (one-time, ~4-8GB)
-------------------------------------------
Recommended models for D&D:

🌟 BEST FOR PI 5 (8GB): Llama 3.2 3B (optimal balance)
    ollama pull llama3.2:3b

⚡ FAST ALTERNATIVE: Phi 3 3.8B (quick responses)
    ollama pull phi3:3.8b

🧠 QUALITY OPTION: Mistral 7B (best quality, uses more RAM)
    ollama pull mistral:7b

🎯 D&D OPTIMIZED: Neural Chat
    ollama pull neural-chat:7b

STEP 4: Run Your AI DM!
-----------------------
    python ai_dm_free.py

That's it! 100% FREE, no API keys, no subscriptions! 
""")


def interactive_session(srd_path: str, model: str = "llama3.2:3b"):
    """Run an interactive AI DM session"""
    
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║              FREE AI DUNGEON MASTER                          ║")
    print("║              Powered by Ollama                               ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    # Initialize DM
    dm = OllamaDM(srd_path, default_model=model)
    
    # Check Ollama
    if not dm.ollama_available:
        print("❌ Ollama is not running!")
        print("\nTo fix this:")
        print("1. Open a terminal")
        print("2. Run: ollama serve")
        print("3. Run this script again\n")
        
        response = input("Would you like setup instructions? (y/n): ")
        if response.lower() == 'y':
            setup_ollama()
        return
    
    # Show available models
    models = dm.list_available_models()
    print(f"✓ Ollama is running!")
    print(f"✓ Using model: {model}")
    
    if models:
        print(f"✓ Available models: {', '.join(models[:5])}")
    
    # Initialize game state
    game_state = GameState(
        current_phase="01_setup_and_introduction",
        party_level=1,
        location="Tavern",
        active_combat=False,
        recent_events=[]
    )
    
    print("\n" + "="*60)
    print("Commands:")
    print("  - Type your actions naturally")
    print("  - 'state' - View game state")
    print("  - 'phase <name>' - Change story phase")
    print("  - 'level <num>' - Set party level")
    print("  - 'models' - List available models")
    print("  - 'quit' - Exit")
    print("="*60 + "\n")
    
    # Game loop
    while True:
        try:
            player_input = input("\n You: ").strip()
            
            if not player_input:
                continue
            
            # Handle commands
            if player_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thanks for playing! May your dice roll true!")
                break
            
            elif player_input.lower() == 'state':
                print(f"\n📊 Game State:")
                print(f"   Phase: {game_state.current_phase}")
                print(f"   Level: {game_state.party_level}")
                print(f"   Location: {game_state.location}")
                print(f"   Combat: {game_state.active_combat}")
                if game_state.recent_events:
                    print(f"   Recent: {', '.join(game_state.recent_events[-3:])}")
                continue
            
            elif player_input.lower().startswith('phase '):
                new_phase = player_input[6:].strip()
                game_state.current_phase = new_phase
                print(f"✓ Phase set to: {new_phase}")
                continue
            
            elif player_input.lower().startswith('level '):
                try:
                    new_level = int(player_input[6:].strip())
                    game_state.party_level = new_level
                    print(f"✓ Party level set to: {new_level}")
                except:
                    print("❌ Invalid level number")
                continue
            
            elif player_input.lower() == 'models':
                models = dm.list_available_models()
                print(f"\n📦 Available models:")
                for m in models:
                    print(f"   - {m}")
                continue
            
            # Get DM response
            print("\n🎭 DM: ", end='', flush=True)
            
            # Use streaming for better UX
            full_response = ""
            for chunk in dm.get_response_streaming(player_input, game_state, model=model):
                print(chunk, end='', flush=True)
                full_response += chunk
            
            print()  # New line after response
            
            # Update game state
            game_state.recent_events.append(player_input[:50])
            if len(game_state.recent_events) > 5:
                game_state.recent_events.pop(0)
            
            # Auto-detect phase changes
            if any(word in player_input.lower() for word in ['attack', 'fight', 'combat', 'initiative']):
                game_state.active_combat = True
                game_state.current_phase = "07_confrontation_and_combat"
            elif any(word in player_input.lower() for word in ['rest', 'sleep', 'camp']):
                game_state.active_combat = False
            
        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FREE AI Dungeon Master powered by Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--srd-path",
        default="./srd_story_cycle",
        help="Path to reorganized SRD directory"
    )
    
    parser.add_argument(
        "--model",
        default="llama3.2:3b",
        help="Ollama model to use (default: llama3.2:3b - optimized for Pi 5 8GB)"
    )
    
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Show Ollama setup instructions"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test connection to Ollama"
    )
    
    args = parser.parse_args()
    
    if args.setup:
        setup_ollama()
        return
    
    if args.test:
        dm = OllamaDM(args.srd_path)
        if dm.ollama_available:
            print("✓ Ollama is running!")
            models = dm.list_available_models()
            print(f"✓ Available models: {', '.join(models)}")
        else:
            print("❌ Ollama is not running")
            print("Run: ollama serve")
        return
    
    # Run interactive session
    interactive_session(args.srd_path, args.model)


if __name__ == "__main__":
    main()