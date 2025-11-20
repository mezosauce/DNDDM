#!/usr/bin/env python3
"""
Phase 3: Active Campaign Routes
Handles active gameplay, AI assistance, sessions, and SRD search
"""

from flask import render_template, request, jsonify
from pathlib import Path
import requests

# These will be imported from main.py when we integrate
# from main import app, campaign_mgr, dm, SRD_PATH, prompt_templates
# from main import Phase3QueryRouter, Phase3SRDLoader, create_phase3_prompt
# from main import QueryRouter, SRDContentLoader, create_full_prompt


# ============================================================================
# PHASE 3: ACTIVE CAMPAIGN (ENHANCED)
# ============================================================================

def register_phase3_routes(app, campaign_mgr, dm, SRD_PATH, prompt_templates,
                          Phase3QueryRouter, Phase3SRDLoader, create_phase3_prompt,
                          QueryRouter, SRDContentLoader, create_full_prompt):
    """Register all Phase 3 routes with the Flask app"""
    
    @app.route('/campaign/<campaign_name>/play')
    def active_campaign(campaign_name):
        """Active campaign gameplay"""
        try:
            context = campaign_mgr.get_campaign_context(campaign_name)
            return render_template('HTML/active_campaign.html', context=context)
        except Exception as e:
            return f"Error: {e}", 404


    @app.route('/campaign/<campaign_name>/session/new', methods=['POST'])
    def new_session(campaign_name):
        """Start a new session"""
        try:
            session_num = campaign_mgr.start_new_session(campaign_name)
            return jsonify({'success': True, 'session_number': session_num})
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/ai-assist', methods=['POST'])
    def ai_assist(campaign_name):
        """Get AI assistance in current phase - ENHANCED for Phase 3"""
        data = request.json
        query = data.get('query', '').strip()
        
        # Check if AI is available
        if not query:
            return jsonify({'error': 'No query provided'}), 400
        
        if not dm:
            return jsonify({'error': 'AI not available - Ollama not running or ai_dm_free.py not found'}), 503
        
        if not hasattr(dm, 'ollama_available') or not dm.ollama_available:
            return jsonify({'error': 'Ollama service not running. Start it with: ollama serve'}), 503
        
        try:
            # Load campaign
            campaign = campaign_mgr.load_campaign(campaign_name)
            characters = campaign_mgr.get_characters(campaign_name)
            
            # Determine phase (prep or active)
            if campaign.current_phase == "call_to_adventure":
                phase = 'prep'
            else:
                phase = 'active'
            
            # Build campaign context
            campaign_context = {
                'name': campaign.name,
                'description': campaign.description,
                'party_size': campaign.party_size,
                'characters': [
                    {
                        'name': char.name,
                        'race': char.race,
                        'char_class': char.char_class,
                        'level': char.level,
                        'hp': char.hp,
                        'max_hp': char.max_hp,
                        'ac': char.ac,
                        'stats': char.stats
                    }
                    for char in characters
                ],
                'session_number': campaign.session_number,
                'current_location': getattr(campaign, 'current_location', 'Unknown'),
                'active_combat': getattr(campaign, 'active_combat', False),
                'recent_events': getattr(campaign, 'recent_events', [])
            }
            
            # ENHANCED: Use Phase 3 router for active campaign
            srd_content = ""
            routing_info = None
            
            if phase == 'active' and Phase3QueryRouter and Phase3SRDLoader:
                try:
                    # Use enhanced Phase 3 router
                    router = Phase3QueryRouter(SRD_PATH)
                    
                    # Route the query with context
                    routing_info = router.route_query(
                        query, 
                        context={
                            'active_combat': campaign_context['active_combat'],
                            'session_number': campaign_context['session_number']
                        }
                    )
                    
                    # Load SRD content
                    loader = Phase3SRDLoader(SRD_PATH)
                    srd_content = loader.load_files(
                        routing_info['files_to_load'],
                        max_chars=15000
                    )
                    
                    # Log what we're using
                    print(f"[Phase 3 Router] Categories: {routing_info['matched_categories']}")
                    print(f"[Phase 3 Router] Files: {len(routing_info['files_to_load'])}")
                    
                except Exception as e:
                    print(f"Phase 3 routing warning: {e}")
                    # Fall back to basic routing if needed
                    
            elif phase == 'prep' and QueryRouter and SRDContentLoader:
                # Use Phase 2 router for prep
                try:
                    router = QueryRouter(SRD_PATH)
                    story_phase = '03_call_to_adventure'
                    routing = router.route_query(query, current_phase=story_phase)
                    
                    if routing['files_to_load']:
                        loader = SRDContentLoader(SRD_PATH)
                        srd_content = loader.load_files(
                            routing['files_to_load'][:3], 
                            max_chars=10000
                        )
                except Exception as e:
                    print(f"Phase 2 routing warning: {e}")
            
            # Create full prompt using appropriate system
            if phase == 'active' and create_phase3_prompt:
                # Use enhanced Phase 3 prompt
                base_prompt = prompt_templates.get_prompt('active')
                full_prompt = create_phase3_prompt(
                    campaign_context=campaign_context,
                    query=query,
                    srd_content=srd_content,
                    base_prompt=base_prompt
                )
            else:
                # Use standard prompt template
                full_prompt = create_full_prompt(
                    phase=phase,
                    campaign_context=campaign_context,
                    query=query,
                    srd_content=srd_content
                )
            
            # Get AI response using Ollama
            ollama_url = "http://localhost:11434/api/generate"
            payload = {
                "model": dm.default_model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500 if phase == 'active' else 400,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(ollama_url, json=payload, timeout=60)
            response.raise_for_status()
            
            ai_response = response.json().get('response', '').strip()
            
            # Update recent events if in active phase
            if phase == 'active':
                if not hasattr(campaign, 'recent_events'):
                    campaign.recent_events = []
                campaign.recent_events.append(f"Player: {query[:100]}")
                campaign.recent_events.append(f"DM: {ai_response[:100]}")
                # Keep only last 10 events
                campaign.recent_events = campaign.recent_events[-10:]
                campaign_mgr._save_campaign(campaign)
            
            # Include routing info in response for debugging
            response_data = {
                'response': ai_response,
                'query': query,
                'phase': phase
            }
            
            if routing_info:
                response_data['routing_info'] = {
                    'categories': routing_info['matched_categories'],
                    'files_loaded': len(routing_info['files_to_load'])
                }
            
            return jsonify(response_data)
            
        except Exception as e:
            print(f"Error in ai_assist: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500


    @app.route('/campaign/<campaign_name>/search-panel')
    def search_panel(campaign_name):
        """Render search panel for active campaign"""
        try:
            campaign = campaign_mgr.load_campaign(campaign_name)
            # Import search_engine here to avoid circular dependency
            from main import search_engine
            stats = search_engine.get_stats() if search_engine else {'status': 'not_available'}
            return render_template('HTML/search_panel.html', campaign=campaign, stats=stats)
        except Exception as e:
            return f"Error: {e}", 404


    @app.route('/srd-search')
    def srd_search_page():
        """Standalone SRD search page"""
        return render_template('HTML/srd_search.html')


    @app.route('/api/srd/file', methods=['POST'])
    def get_srd_file():
        """Serve SRD markdown file content"""
        data = request.json
        file_path = data.get('file_path', '')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        # Security: ensure path doesn't escape SRD directory
        if '..' in file_path or file_path.startswith('/'):
            return jsonify({'error': 'Invalid file path'}), 400
        
        try:
            full_path = Path(SRD_PATH) / file_path
            
            if not full_path.exists():
                return jsonify({'error': 'File not found'}), 404
            
            if not full_path.is_file():
                return jsonify({'error': 'Not a file'}), 400
            
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return jsonify({
                'success': True,
                'content': content,
                'file_path': file_path
            })
            
        except Exception as e:
            print(f"Error serving SRD file: {e}")
            return jsonify({'error': str(e)}), 500