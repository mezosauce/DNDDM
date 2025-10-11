#!/usr/bin/env python3
"""
Flask Web UI for AI Dungeon Master
Run this on your Raspberry Pi 5 and access from any device on your network
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import secrets
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Import your AI DM components
try:
    from ai_dm_query_router import QueryRouter
    from ai_dm_free import OllamaDM, GameState, SRDContentLoader
except ImportError as e:
    print(f"Warning: AI DM modules not found. Error: {e}")
    print("Make sure ai_dm_free.py and ai_dm_query_router.py are in the same directory.")
    OllamaDM = None
    GameState = None
    SRDContentLoader = None

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global game state
if GameState:
    game_state = GameState(
        current_phase="01_setup_and_introduction",
        party_level=1,
        location="Starting Tavern",
        active_combat=False,
        recent_events=[]
    )
else:
    # Fallback if imports failed
    class FakeGameState:
        def __init__(self):
            self.current_phase = "01_setup_and_introduction"
            self.party_level = 1
            self.location = "Starting Tavern"
            self.active_combat = False
            self.recent_events = []
    game_state = FakeGameState()

# Initialize AI DM
SRD_PATH = "./srd_story_cycle"
dm = None
if os.path.exists(SRD_PATH):
    dm = OllamaDM(SRD_PATH, default_model="llama3.2:3b")

# Session history
session_history = []
max_history = 100


# ============================================================================
# Web Routes
# ============================================================================

@app.route('/')
def index():
    """Main DM interface"""
    return render_template('index.html')

@app.route('/player')
def player_view():
    """Simplified player view"""
    return render_template('player.html')

@app.route('/api/status')
def status():
    """Get current game status"""
    return jsonify({
        'ollama_available': dm.ollama_available if dm else False,
        'model': dm.default_model if dm else None,
        'game_state': {
            'phase': game_state.current_phase,
            'level': game_state.party_level,
            'location': game_state.location,
            'combat': game_state.active_combat
        }
    })

@app.route('/api/ask', methods=['POST'])
def ask_dm():
    """Ask the DM a question"""
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    if not dm or not dm.ollama_available:
        return jsonify({'error': 'AI DM not available. Is Ollama running?'}), 503
    
    # Get response from AI DM
    result = dm.get_response(query, game_state)
    
    if 'error' in result:
        return jsonify(result), 500
    
    # Add to history
    session_history.append({
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'response': result['response'],
        'phase': game_state.current_phase
    })
    
    # Trim history
    if len(session_history) > max_history:
        session_history.pop(0)
    
    # Update game state
    game_state.recent_events.append(query[:50])
    if len(game_state.recent_events) > 5:
        game_state.recent_events.pop(0)
    
    # Auto-detect phase changes
    query_lower = query.lower()
    if any(word in query_lower for word in ['attack', 'fight', 'combat', 'roll initiative']):
        game_state.active_combat = True
        game_state.current_phase = "07_confrontation_and_combat"
    elif any(word in query_lower for word in ['rest', 'sleep', 'camp', 'long rest']):
        game_state.active_combat = False
    
    # Broadcast to all connected clients
    socketio.emit('dm_response', {
        'query': query,
        'response': result['response'],
        'game_state': {
            'phase': game_state.current_phase,
            'combat': game_state.active_combat
        }
    })
    
    return jsonify(result)

@app.route('/api/dice/roll', methods=['POST'])
def roll_dice():
    """Roll dice"""
    import random
    
    data = request.json
    dice_notation = data.get('dice', 'd20').lower()
    modifier = data.get('modifier', 0)
    
    try:
        # Parse dice notation (e.g., "2d6", "d20", "3d8+5")
        if '+' in dice_notation:
            dice_part, mod_part = dice_notation.split('+')
            modifier += int(mod_part)
            dice_notation = dice_part
        elif '-' in dice_notation:
            dice_part, mod_part = dice_notation.split('-')
            modifier -= int(mod_part)
            dice_notation = dice_part
        
        if 'd' in dice_notation:
            parts = dice_notation.split('d')
            num_dice = int(parts[0]) if parts[0] else 1
            die_size = int(parts[1])
        else:
            num_dice = 1
            die_size = int(dice_notation)
        
        # Roll the dice
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        result = {
            'dice': f"{num_dice}d{die_size}",
            'rolls': rolls,
            'modifier': modifier,
            'total': total,
            'natural_20': die_size == 20 and 20 in rolls,
            'natural_1': die_size == 20 and 1 in rolls
        }
        
        # Broadcast roll to all clients
        socketio.emit('dice_rolled', result)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/state', methods=['GET', 'POST'])
def manage_state():
    """Get or update game state"""
    if request.method == 'GET':
        return jsonify({
            'phase': game_state.current_phase,
            'level': game_state.party_level,
            'location': game_state.location,
            'combat': game_state.active_combat,
            'recent_events': game_state.recent_events
        })
    
    elif request.method == 'POST':
        data = request.json
        
        if 'phase' in data:
            game_state.current_phase = data['phase']
        if 'level' in data:
            game_state.party_level = int(data['level'])
        if 'location' in data:
            game_state.location = data['location']
        if 'combat' in data:
            game_state.active_combat = bool(data['combat'])
        
        # Broadcast state change
        socketio.emit('state_updated', {
            'phase': game_state.current_phase,
            'level': game_state.party_level,
            'location': game_state.location,
            'combat': game_state.active_combat
        })
        
        return jsonify({'success': True})

@app.route('/api/history')
def get_history():
    """Get session history"""
    return jsonify({
        'history': session_history[-20:],  # Last 20 interactions
        'total': len(session_history)
    })

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear session history"""
    session_history.clear()
    game_state.recent_events.clear()
    return jsonify({'success': True})

@app.route('/api/initiative', methods=['GET', 'POST', 'DELETE'])
def manage_initiative():
    """Manage initiative tracker"""
    if 'initiative_order' not in app.config:
        app.config['initiative_order'] = []
    
    if request.method == 'GET':
        return jsonify({'initiative': app.config['initiative_order']})
    
    elif request.method == 'POST':
        data = request.json
        entry = {
            'name': data.get('name'),
            'initiative': data.get('initiative'),
            'hp': data.get('hp', None),
            'max_hp': data.get('max_hp', None),
            'ac': data.get('ac', None)
        }
        app.config['initiative_order'].append(entry)
        # Sort by initiative (descending)
        app.config['initiative_order'].sort(key=lambda x: x['initiative'], reverse=True)
        
        socketio.emit('initiative_updated', {'initiative': app.config['initiative_order']})
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        app.config['initiative_order'].clear()
        socketio.emit('initiative_updated', {'initiative': []})
        return jsonify({'success': True})


# ============================================================================
# SocketIO Events (Real-time updates)
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    emit('connected', {
        'game_state': {
            'phase': game_state.current_phase,
            'level': game_state.party_level,
            'location': game_state.location,
            'combat': game_state.active_combat
        }
    })

@socketio.on('player_action')
def handle_player_action(data):
    """Broadcast player action to all clients"""
    emit('player_action', data, broadcast=True)


# ============================================================================
# Main
# ============================================================================

def create_templates():
    """Create HTML templates if they don't exist"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Create index.html (DM view)
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Dungeon Master</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d1b3d 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
        }
        .panel {
            background: rgba(30, 30, 46, 0.8);
            border: 2px solid #4a4a6a;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        h1, h2 {
            color: #ff6b6b;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online { background: #51cf66; }
        .status-offline { background: #ff6b6b; }
        .game-state {
            background: rgba(74, 74, 106, 0.3);
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .game-state-item {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            padding: 8px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }
        .chat-container {
            height: 400px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
            animation: fadeIn 0.3s;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message-player {
            background: rgba(81, 207, 102, 0.2);
            border-left: 3px solid #51cf66;
        }
        .message-dm {
            background: rgba(255, 107, 107, 0.2);
            border-left: 3px solid #ff6b6b;
        }
        .message-label {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        input, select, button {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 2px solid #4a4a6a;
            border-radius: 6px;
            background: rgba(30, 30, 46, 0.8);
            color: #e0e0e0;
            font-size: 16px;
        }
        button {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(255, 107, 107, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        .dice-roller {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin: 15px 0;
        }
        .dice-btn {
            padding: 15px;
            background: linear-gradient(135deg, #4a4a6a 0%, #3a3a5a 100%);
            border: 2px solid #6a6a8a;
        }
        .dice-result {
            text-align: center;
            padding: 20px;
            background: rgba(81, 207, 102, 0.2);
            border-radius: 8px;
            margin: 15px 0;
            font-size: 24px;
            font-weight: bold;
        }
        .natural-20 { background: rgba(255, 215, 0, 0.3); color: #ffd700; }
        .natural-1 { background: rgba(255, 0, 0, 0.3); color: #ff6b6b; }
        .loading {
            text-align: center;
            padding: 20px;
            color: #ff6b6b;
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 107, 107, 0.3);
            border-radius: 50%;
            border-top-color: #ff6b6b;
            animation: spin 1s ease-in-out infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Left Panel: Controls -->
        <div>
            <div class="panel">
                <h1>🎲 AI Dungeon Master</h1>
                <div>
                    <span class="status-indicator" id="status-indicator"></span>
                    <span id="status-text">Checking...</span>
                </div>
            </div>

            <div class="panel">
                <h2>Game State</h2>
                <div class="game-state">
                    <div class="game-state-item">
                        <span>Phase:</span>
                        <span id="current-phase">Loading...</span>
                    </div>
                    <div class="game-state-item">
                        <span>Level:</span>
                        <span id="party-level">1</span>
                    </div>
                    <div class="game-state-item">
                        <span>Location:</span>
                        <span id="location">Unknown</span>
                    </div>
                    <div class="game-state-item">
                        <span>Combat:</span>
                        <span id="combat-status">No</span>
                    </div>
                </div>
                <button onclick="updateState()">Update State</button>
            </div>

            <div class="panel">
                <h2>Dice Roller</h2>
                <div class="dice-roller">
                    <button class="dice-btn" onclick="rollDice('d4')">d4</button>
                    <button class="dice-btn" onclick="rollDice('d6')">d6</button>
                    <button class="dice-btn" onclick="rollDice('d8')">d8</button>
                    <button class="dice-btn" onclick="rollDice('d10')">d10</button>
                    <button class="dice-btn" onclick="rollDice('d12')">d12</button>
                    <button class="dice-btn" onclick="rollDice('d20')">d20</button>
                </div>
                <input type="text" id="custom-dice" placeholder="Custom (e.g., 2d6+3)">
                <button onclick="rollCustom()">Roll Custom</button>
                <div id="dice-result"></div>
            </div>
        </div>

        <!-- Right Panel: Chat -->
        <div class="panel">
            <h2>Ask the DM</h2>
            <div class="chat-container" id="chat-container"></div>
            <input type="text" id="query-input" placeholder="What do you want to do?" 
                   onkeypress="if(event.key==='Enter') askDM()">
            <button onclick="askDM()">Ask DM</button>
            <button onclick="clearHistory()" style="background: #666; margin-top: 10px;">Clear History</button>
        </div>
    </div>

    <script>
        const socket = io();
        let isLoading = false;

        // Check status on load
        fetch('/api/status')
            .then(r => r.json())
            .then(data => {
                updateStatusIndicator(data.ollama_available);
                if (data.game_state) {
                    updateGameStateDisplay(data.game_state);
                }
            });

        function updateStatusIndicator(online) {
            const indicator = document.getElementById('status-indicator');
            const text = document.getElementById('status-text');
            if (online) {
                indicator.className = 'status-indicator status-online';
                text.textContent = 'AI Online';
            } else {
                indicator.className = 'status-indicator status-offline';
                text.textContent = 'AI Offline';
            }
        }

        function updateGameStateDisplay(state) {
            document.getElementById('current-phase').textContent = 
                state.phase.replace(/_/g, ' ').replace(/^\d+\s*/, '');
            document.getElementById('party-level').textContent = state.level;
            document.getElementById('location').textContent = state.location;
            document.getElementById('combat-status').textContent = state.combat ? 'Yes' : 'No';
        }

        async function askDM() {
            if (isLoading) return;
            
            const input = document.getElementById('query-input');
            const query = input.value.trim();
            if (!query) return;

            // Add player message
            addMessage(query, 'player');
            input.value = '';
            isLoading = true;

            // Show loading
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.innerHTML = '<div class="spinner"></div> DM is thinking...';
            document.getElementById('chat-container').appendChild(loadingDiv);

            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query})
                });

                const data = await response.json();
                loadingDiv.remove();

                if (data.error) {
                    addMessage(`Error: ${data.error}`, 'dm');
                } else {
                    addMessage(data.response, 'dm');
                    if (data.routing) {
                        updateGameStateDisplay({
                            phase: data.routing.primary_phase,
                            level: document.getElementById('party-level').textContent,
                            location: document.getElementById('location').textContent,
                            combat: data.routing.query_type === 'combat'
                        });
                    }
                }
            } catch (error) {
                loadingDiv.remove();
                addMessage(`Error: ${error.message}`, 'dm');
            }

            isLoading = false;
        }

        function addMessage(text, type) {
            const container = document.getElementById('chat-container');
            const div = document.createElement('div');
            div.className = `message message-${type}`;
            div.innerHTML = `
                <div class="message-label">${type === 'player' ? '🎲 Player' : '🎭 DM'}</div>
                <div>${text}</div>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        async function rollDice(dice) {
            const response = await fetch('/api/dice/roll', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dice})
            });
            const data = await response.json();
            displayDiceResult(data);
        }

        async function rollCustom() {
            const dice = document.getElementById('custom-dice').value;
            const response = await fetch('/api/dice/roll', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dice})
            });
            const data = await response.json();
            displayDiceResult(data);
        }

        function displayDiceResult(data) {
            const resultDiv = document.getElementById('dice-result');
            let className = 'dice-result';
            if (data.natural_20) className += ' natural-20';
            if (data.natural_1) className += ' natural-1';
            
            resultDiv.className = className;
            resultDiv.innerHTML = `
                ${data.dice}: [${data.rolls.join(', ')}]
                ${data.modifier !== 0 ? ` ${data.modifier > 0 ? '+' : ''}${data.modifier}` : ''}
                = <strong>${data.total}</strong>
                ${data.natural_20 ? ' 🌟 NAT 20!' : ''}
                ${data.natural_1 ? ' 💀 NAT 1!' : ''}
            `;
        }

        function clearHistory() {
            if (confirm('Clear all chat history?')) {
                fetch('/api/history/clear', {method: 'POST'})
                    .then(() => {
                        document.getElementById('chat-container').innerHTML = '';
                    });
            }
        }

        // Socket.IO events
        socket.on('dm_response', (data) => {
            // Real-time updates from other clients
        });

        socket.on('dice_rolled', (data) => {
            displayDiceResult(data);
        });

        socket.on('state_updated', (data) => {
            updateGameStateDisplay(data);
        });
    </script>
</body>
</html>"""
    
    with open(templates_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # Create player.html (simplified view)
    player_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Player View</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1e1e2e;
            color: #e0e0e0;
            padding: 15px;
        }
        h1 { color: #ff6b6b; margin-bottom: 20px; text-align: center; }
        .dice-roller {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin: 20px 0;
        }
        button {
            padding: 20px;
            background: linear-gradient(135deg, #4a4a6a 0%, #3a3a5a 100%);
            border: 2px solid #6a6a8a;
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
        }
        .dice-result {
            text-align: center;
            padding: 30px;
            background: rgba(81, 207, 102, 0.2);
            border-radius: 8px;
            margin: 20px 0;
            font-size: 36px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h1>🎲 Dice Roller</h1>
    <div class="dice-roller">
        <button onclick="roll('d4')">d4</button>
        <button onclick="roll('d6')">d6</button>
        <button onclick="roll('d8')">d8</button>
        <button onclick="roll('d10')">d10</button>
        <button onclick="roll('d12')">d12</button>
        <button onclick="roll('d20')">d20</button>
    </div>
    <div id="result" class="dice-result">Roll a die!</div>
    
    <script>
        async function roll(dice) {
            const response = await fetch('/api/dice/roll', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dice})
            });
            const data = await response.json();
            document.getElementById('result').innerHTML = `
                ${data.dice}: ${data.total}
                ${data.natural_20 ? '<br>🌟 CRITICAL!' : ''}
                ${data.natural_1 ? '<br>💀 FUMBLE!' : ''}
            `;
        }
    </script>
</body>
</html>"""
    
    with open(templates_dir / 'player.html', 'w', encoding='utf-8') as f:
        f.write(player_html)
    
    print("✓ HTML templates created in ./templates/")


if __name__ == '__main__':
    # Create templates if they don't exist
    if not Path('templates/index.html').exists():
        print("Creating HTML templates...")
        create_templates()
    
    print("\n" + "="*60)
    print("🎲 AI Dungeon Master Web Interface")
    print("="*60)
    
    if dm and dm.ollama_available:
        print("✓ Ollama is running")
        print(f"✓ Model: {dm.default_model}")
    else:
        print("⚠ Ollama not detected. Start it with: ollama serve")
    
    print(f"\n📡 Server starting...")
    print(f"   DM Interface: http://localhost:5000")
    print(f"   Player View:  http://localhost:5000/player")
    print(f"\n💡 On your network:")
    print(f"   Find your Pi's IP with: hostname -I")
    print(f"   Then access: http://YOUR_PI_IP:5000")
    print("="*60 + "\n")
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)