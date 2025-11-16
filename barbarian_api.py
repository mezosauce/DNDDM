#!/usr/bin/env python3
"""
Minimal Flask API to expose Barbarian actions for the frontend.

Run with: `python barbarian_api.py` and visit the frontend pages that use the JS.
This keeps state in-memory for simple integration/testing.
"""
from flask import Flask, jsonify, request
from Head.Class.barbarian import Barbarian
from typing import Dict

app = Flask(__name__)

# In-memory store of characters by name
_CHARACTERS: Dict[str, Barbarian] = {}


def serialize_barbarian(b: Barbarian):
    return b.get_character_sheet()


# Add simple CORS headers so browser pages served from other origins can call this API
@app.after_request
def _add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


@app.route('/api/barbarians', methods=['GET'])
def list_barbarians():
    print(f"[API] GET /api/barbarians -> {list(_CHARACTERS.keys())}")
    return jsonify({'barbarians': list(_CHARACTERS.keys())})


@app.route('/api/barbarian/<name>', methods=['GET'])
def get_barbarian(name):
    print(f"[API] GET /api/barbarian/{name}")
    b = _CHARACTERS.get(name)
    if not b:
        print(f"[API] -> 404 not found: {name}")
        return jsonify({'error': 'Not found'}), 404
    return jsonify(serialize_barbarian(b))


@app.route('/api/barbarian/<name>/create', methods=['POST'])
def create_barbarian(name):
    data = request.json or {}
    print(f"[API] POST /api/barbarian/{name}/create payload={data}")
    if name in _CHARACTERS:
        print(f"[API] -> already exists: {name}")
        return jsonify({'error': 'Already exists'}), 400

    stats = data.get('stats', {
        'strength': 15,
        'dexterity': 13,
        'constitution': 14,
        'intelligence': 10,
        'wisdom': 12,
        'charisma': 8
    })

    b = Barbarian(
        name=name,
        race=data.get('race', 'Human'),
        char_class='Barbarian',
        background=data.get('background', ''),
        level=int(data.get('level', 1)),
        stats=stats,
        alignment=data.get('alignment', 'True Neutral')
    )

    _CHARACTERS[name] = b
    return jsonify({'success': True, 'character': serialize_barbarian(b)})


@app.route('/api/barbarian/<name>/enter_rage', methods=['POST'])
def api_enter_rage(name):
    print(f"[API] POST /api/barbarian/{name}/enter_rage")
    b = _CHARACTERS.get(name)
    if not b:
        print(f"[API] -> 404 not found: {name}")
        return jsonify({'error': 'Not found'}), 404
    ok = b.enter_rage()
    return jsonify({'success': bool(ok), 'rages_used': b.rages_used, 'currently_raging': b.currently_raging})


@app.route('/api/barbarian/<name>/end_rage', methods=['POST'])
def api_end_rage(name):
    print(f"[API] POST /api/barbarian/{name}/end_rage")
    b = _CHARACTERS.get(name)
    if not b:
        print(f"[API] -> 404 not found: {name}")
        return jsonify({'error': 'Not found'}), 404
    b.end_rage()
    return jsonify({'success': True, 'currently_raging': b.currently_raging})


@app.route('/api/barbarian/<name>/long_rest', methods=['POST'])
def api_long_rest(name):
    print(f"[API] POST /api/barbarian/{name}/long_rest")
    b = _CHARACTERS.get(name)
    if not b:
        print(f"[API] -> 404 not found: {name}")
        return jsonify({'error': 'Not found'}), 404
    b.long_rest()
    return jsonify({'success': True, 'rages_used': b.rages_used, 'hp': b.hp})


@app.route('/api/barbarian/<name>/set_level', methods=['POST'])
def api_set_level(name):
    data = request.json or {}
    print(f"[API] POST /api/barbarian/{name}/set_level payload={data}")
    level = int(data.get('level', 1))
    b = _CHARACTERS.get(name)
    if not b:
        print(f"[API] -> 404 not found: {name}")
        return jsonify({'error': 'Not found'}), 404
    b.level = level
    b.apply_level_features()
    return jsonify({'success': True, 'level': b.level, 'rages_per_day': b.rages_per_day})


@app.route('/api/barbarian/<name>/update_stats', methods=['POST'])
def api_update_stats(name):
    data = request.json or {}
    stats = data.get('stats')
    print(f"[API] POST /api/barbarian/{name}/update_stats payload={data}")
    b = _CHARACTERS.get(name)
    if not b:
        print(f"[API] -> 404 not found: {name}")
        return jsonify({'error': 'Not found'}), 404
    if not isinstance(stats, dict):
        return jsonify({'error': 'Invalid stats payload'}), 400
    b.stats.update(stats)
    if b.unarmored_defense_active:
        b.calculate_unarmored_defense()
    return jsonify({'success': True, 'stats': b.stats, 'ac': b.ac})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=True)
