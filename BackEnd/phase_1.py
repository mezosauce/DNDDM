#!/usr/bin/env python3
"""
Phase 1: Setup & Character Creation Routes
Handles character creation, updates, and phase advancement
"""

from flask import render_template, request, jsonify
from dataclasses import asdict

# These will be imported from main.py when we integrate
# from main import app, campaign_mgr, Character

from component.Class import create_character


def _get_json():
    """Safely get JSON body as a dict; raise ValueError if missing/invalid."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Request must contain a valid JSON body')
    return data

# ============================================================================
# PHASE 1: SETUP & CHARACTER CREATION
# ============================================================================

def register_phase1_routes(app, campaign_mgr, Character):
    """Register all Phase 1 routes with the Flask app"""
    
    @app.route('/campaign/<campaign_name>/setup')
    def setup_phase(campaign_name):
        """Setup and character creation phase"""
        try:
            campaign = campaign_mgr.load_campaign(campaign_name)
            characters = campaign_mgr.get_characters(campaign_name)
            
            return render_template('HTML/setup_phase.html', 
                                 campaign=campaign,
                                 characters=characters)
        except Exception as e:
            return f"Error: {e}", 404


    @app.route('/campaign/<campaign_name>/advance', methods=['POST'])
    def advance_phase(campaign_name):
        """Advance to next phase"""
        try:
            campaign = campaign_mgr.advance_phase(campaign_name)
            return jsonify({
                'success': True,
                'new_phase': campaign.current_phase
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    # ============================================================================
    # CHARACTER MANAGEMENT ENDPOINTS 
    # ============================================================================

    @app.route('/campaign/<campaign_name>/character/<character_name>/update', methods=['POST'])
    def update_character(campaign_name, character_name):
        """Update an existing character"""
        data = _get_json()
        
        try:
            # Load existing character
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            # Update fields 
            char.hp = int(data.get('hp', char.hp))
            char.max_hp = int(data.get('max_hp', char.max_hp))
            char.ac = int(data.get('ac', char.ac))
            char.level = int(data.get('level', char.level))
            
            if 'alignment' in data:
                char.alignment = data['alignment']
            if 'notes' in data:
                char.notes = data['notes']
            if 'has_inspiration' in data:
                char.has_inspiration = data['has_inspiration']
            
            # Update character in campaign
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/add', methods=['POST'])
    def add_character(campaign_name):
        """Add a new character"""
        data = _get_json()
        
        try:
            # Get class type from request (defaults to "Character" if not provided)
            class_type = data.get('class', 'Character')
            
            base_params = {
                'name': data['name'],
                'race': data['race'],
                'char_class': data['class'],
                'background': data['background'],
                'level': int(data.get('level', 1)), 
                'hp': int(data.get('hp', 10)),
                'max_hp': int(data.get('max_hp', 10)),
                'ac': int(data.get('ac', 10)),
                'stats': data.get('stats', {}),
                'alignment': data.get('alignment', 'True Neutral'), 
                
                'background_feature': data.get('background_feature', ''),
                'skill_proficiencies': data.get('skill_proficiencies', []),
                
                'languages_known': data.get('languages_known', []),
                'personality_traits': data.get('personality_traits', []),
                'ideal': data.get('ideal', ''),
                'bond': data.get('bond', ''),
                'flaw': data.get('flaw', ''),

            }
            

            additional_params = {}
            
            # Barbarian-specific fields
            if class_type == "Barbarian":
                additional_params.update({
                    """
                    primal_path: str = ""  # "Path of the Berserker" or "Path of the Totem Warrior"
                    rages_per_day: int = 2  # Based on level
                    rages_used: int = 0
                    rage_damage: int = 2  # Based on level
                    currently_raging: bool = False            
                    unarmored_defense_active: bool = True  # AC = 10 + DEX + CON when no armor
                    danger_sense_active: bool = False  # Level 2+
                    reckless_attack_available: bool = False  # Level 2+
                    fast_movement: int = 0  # Extra movement at level 5+
                    feral_instinct: bool = False  # Level 7+
                    brutal_critical_dice: int = 0  # Extra dice on crits (1 at 9th, 2 at 13th, 3 at 17th)
                    relentless_rage_active: bool = False  # Level 11+
                    relentless_rage_dc: int = 10  # DC for Constitution save
                    persistent_rage: bool = False  # Level 15+
                    indomitable_might: bool = False  # Level 18+
                    primal_champion: bool = False  # Level 20   
                    frenzy_active: bool = False
                    exhaustion_level: int = 0  # Track exhaustion (max 6)
                    mindless_rage: bool = False  # Level 6 Berserker
                    intimidating_presence_available: bool = False  # Level 10 Berserker
                    retaliation_available: bool = False  # Level 14 Berserker               
                    path_feature_3: bool = False
                    path_feature_6: bool = False
                    path_feature_10: bool = False
                    path_feature_14: bool = False
                    """


                    'primal_path': data.get('primal_path', ''),
                    'rages_per_day': int(data.get('rages_per_day', 2)),
                    'rages_used': int(data.get('rages_used', 0)),
                    'rage_damage': int(data.get('rage_damage', 2)),
                    'currently_raging': data.get('currently_raging', False),
                    'unarmored_defense_active': data.get('unarmored_defense_active', True),
                    'danger_sense_active': data.get('danger_sense_active', False),
                    'reckless_attack_available': data.get('reckless_attack_available', False),
                    'fast_movement': int(data.get('fast_movement', 0)),
                    'feral_instinct': data.get('feral_instinct', False),
                    'brutal_critical_dice': int(data.get('brutal_critical_dice', 0)),
                    'relentless_rage_active': data.get('relentless_rage_active', False),
                    'relentless_rage_dc': int(data.get('relentless_rage_dc', 10)),
                    'persistent_rage': data.get('persistent_rage', False),
                    'indomitable_might': data.get('indomitable_might', False),
                    'primal_champion': data.get('primal_champion', False),
                    'frenzy_active': data.get('frenzy_active', False),
                    'exhaustion_level': int(data.get('exhaustion_level', 0)),
                    'mindless_rage': data.get('mindless_rage', False),
                    'intimidating_presence_available': data.get('intimidating_presence_available', False),
                    'retaliation_available': data.get('retaliation_available', False),
                    'path_feature_3': data.get('path_feature_3', False),
                    'path_feature_6': data.get('path_feature_6', False),
                    'path_feature_10': data.get('path_feature_10', False),
                    'path_feature_14': data.get('path_feature_14', False)
                })
            if class_type == "Bard":
                additional_params.update({
                    """
                    bard_college: str = ""  # "College of Lore" or "College of Valor"
                    cantrips_known: List[str] = field(default_factory=list)
                    spells_known: List[str] = field(default_factory=list)
                    spell_slots: Dict[int, int] = field(default_factory=dict) 
                    spell_slots_used: Dict[int, int] = field(default_factory=dict)  
                    bardic_inspiration_die: str = "d6"  # d6, d8, d10, or d12
                    bardic_inspiration_uses: int = 0  # Max uses (based on Charisma modifier)
                    bardic_inspiration_remaining: int = 0  # Current remaining uses
                    musical_instruments: List[str] = field(default_factory=list)  # 3 instruments
                    jack_of_all_trades: bool = False  # Level 2+
                    song_of_rest_die: str = ""  # d6 at 2nd, d8 at 9th, d10 at 13th, d12 at 17th
                    font_of_inspiration: bool = False  # Level 5+
                    countercharm_available: bool = False  # Level 6+
                    superior_inspiration: bool = False  # Level 20
                    cutting_words_available: bool = False  # Level 3 Lore
                    additional_magical_secrets: bool = False  # Level 6 Lore
                    peerless_skill_available: bool = False  # Level 14 Lore
                    college_feature_3: bool = False
                    college_feature_6: bool = False
                    college_feature_14: bool = False
                    """


                    'bard_college': data.get('bard_college', ''),
                    'cantrips_known': data.get('cantrips_known', []),
                    'spells_known': data.get('spells_known', []),
                    'spell_slots': data.get('spell_slots', {}),
                    'spell_slots_used': data.get('spell_slots_used', {}),
                    'bardic_inspiration_die': data.get('bardic_inspiration_die', 'd6'),
                    'bardic_inspiration_uses': data.get('bardic_inspiration_uses'),
                    'bardic_inspiration_remaining': data.get('bardic_inspiration_remaining', 0),
                    'musical_instruments': data.get('musical_instruments', []),
                    'jack_of_all_trades': data.get('jack_of_all_trades', False),
                    'song_of_rest_die': data.get('song_of_rest_die', ''),
                    'font_of_inspiration': data.get('font_of_inspiration', False),
                    'countercharm_available': data.get('countercharm_available', False),
                    'superior_inspiration': data.get('superior_inspiration', False),
                    'cutting_words_available': data.get('cutting_words_available', False),
                    'additional_magical_secrets': data.get('additional_magical_secrets', False),
                    'peerless_skill_available': data.get('peerless_skill_available', False),
                    'college_feature_3': data.get('college_feature_3', False),
                    'college_feature_6': data.get('college_feature_6', False),
                    'college_feature_14': data.get('college_feature_14', False)
                    
                })

            if class_type == "Cleric":
                additional_params.update({
                """

                    divine_domain: str = ""  # "Life", "Knowledge", "Light", "Nature", "Tempest", "Trickery", "War"
                    deity: str = ""  # The deity the cleric serves
        
                    cantrips_known: int = 3
                    spell_slots: Dict[int, int] = field(default_factory=dict)  # {1: 2, 2: 0, ...}
                    spells_prepared: List[str] = field(default_factory=list)
                    domain_spells: List[str] = field(default_factory=list)  # Always prepared

                    channel_divinity_uses: int = 0  # Based on level (1 at 2nd, 2 at 6th, 3 at 18th)
                    channel_divinity_used: int = 0

                    destroy_undead_cr: float = 0  # CR threshold for destroying undead

                    divine_intervention_available: bool = False  # Level 10+
                    divine_intervention_used: bool = False  # Can't use for 7 days if successful
                    divine_intervention_auto_success: bool = False  # Level 20

                    bonus_proficiency_heavy_armor: bool = False  # Life domain gets heavy armor
                    disciple_of_life: bool = False  # Healing bonus (Life domain level 1)
                    preserve_life_available: bool = False  # Channel Divinity: Preserve Life (Life domain level 2)
                    blessed_healer: bool = False  # Heal self when healing others (Life domain level 6)
                    divine_strike_dice: int = 0  # Extra radiant damage (1d8 at 8th, 2d8 at 14th)
                    supreme_healing: bool = False  # Max healing dice (Life domain level 17)

                    domain_feature_1: bool = False
                    domain_feature_2: bool = False
                    domain_feature_6: bool = False
                    domain_feature_8: bool = False
                    domain_feature_17: bool = False
                    """

                    'divine_domain': data.get('divine_domain', ''),
                    'deity': data.get('deity', ''),
                    'cantrips_known': data.get('cantrips_known', 3),
                    'spell_slots': data.get('spell_slots', {}),
                    'spells_prepared': data.get('spells_prepared', []),
                    'domain_spells': data.get('domain_spells', []),
                    'channel_divinity_uses': int(data.get('channel_divinity_uses', 0)),
                    'channel_divinity_used': int(data.get('channel_divinity_used', 0)),
                    'destroy_undead_cr': float(data.get('destroy_undead_cr', 0)),
                    'divine_intervention_available': data.get('divine_intervention_available', False),
                    'divine_intervention_used': data.get('divine_intervention_used', False),
                    'divine_intervention_auto_success': data.get('divine_intervention_auto_success', False),
                    'bonus_proficiency_heavy_armor': data.get('bonus_proficiency_heavy_armor', False),
                    'disciple_of_life': data.get('disciple_of_life', False),
                    'preserve_life_available': data.get('preserve_life_available', False),
                    'blessed_healer': data.get('blessed_healer', False),
                    'divine_strike_dice': int(data.get('divine_strike_dice', 0)),
                    'supreme_healing': data.get('supreme_healing', False),
                    'domain_feature_1': data.get('domain_feature_1', False),
                    'domain_feature_2': data.get('domain_feature_2', False),
                    'domain_feature_6': data.get('domain_feature_6', False),
                    'domain_feature_8': data.get('domain_feature_8', False),
                    'domain_feature_17': data.get('domain_feature_17', False)

                   
                })

            if class_type == "Druid":
                additional_params.update({
                    """
                        druid_circle: str = ""  # "Circle of the Land" or "Circle of the Moon"
                        circle_land_type: str = ""  # arctic, coast, desert, forest, grassland, mountain, swamp
                        

                        cantrips_known: int = 2
                        known_cantrips: List[str] = field(default_factory=list)
                        prepared_spells: List[str] = field(default_factory=list)
                        spell_slots: Dict[int, int] = field(default_factory=dict)  # {level: max_slots}
                        spell_slots_used: Dict[int, int] = field(default_factory=dict)  # {level: used_slots}
                        spellcasting_ability: str = "wisdom"
                        
                        wild_shape_uses: int = 2
                        wild_shape_uses_remaining: int = 2
                        wild_shape_max_cr: float = 0.25
                        wild_shape_max_hours: int = 1
                        wild_shape_can_fly: bool = False
                        wild_shape_can_swim: bool = False
                        currently_wild_shaped: bool = False
                        wild_shape_beast: str = ""
                        wild_shape_hp: int = 0

                        druidic_language: bool = True  # Level 1
                        natural_recovery_available: bool = False  # Level 2 (Circle of the Land)
                        natural_recovery_used: bool = False
                        lands_stride: bool = False  # Level 6 (Circle of the Land)
                        natures_ward: bool = False  # Level 10 (Circle of the Land)
                        natures_sanctuary: bool = False  # Level 14 (Circle of the Land)

                        timeless_body: bool = False  # Level 18
                        beast_spells: bool = False  # Level 18
                        archdruid: bool = False  # Level 20

                        circle_spells: List[str] = field(default_factory=list)


                    """


                    'druid_circle': data.get('druid_circle', ''),
                    'circle_land_type': data.get('circle_land_type', ''),
                    'cantrips_known': int(data.get('cantrips_known', 2)),
                    'known_cantrips': data.get('known_cantrips', []),
                    'prepared_spells': data.get('prepared_spells', []),
                    'spell_slots': data.get('spell_slots', []),
                    'spell_slots_used': data.get('spell_slots_used', []),
                    'spellcasting_ability': data.get('spellcasting_ability', 'wisdom'),
                    'wild_shape_uses': int(data.get('wild_shape_uses', 2)),
                    'wild_shape_uses_remaining': int(data.get('wild_shape_uses_remaining', 2)),
                    'wild_shape_max_cr': float(data.get('wild_shape_max_cr', 0.25)),
                    'wild_shape_max_hours': int(data.get('wild_shape_max_hours', 1)),
                    'wild_shape_can_fly': data.get('wild_shape_can_fly', False),
                    'wild_shape_can_swim': data.get('wild_shape_can_swim', False),
                    'currently_wild_shaped': data.get('currently_wild_shaped', False),
                    'wild_shape_beast': data.get('wild_shape_beast', ''),
                    'wild_shape_hp': int(data.get('wild_shape_hp', 0)),
                    'druidic_language': data.get('druidic_language', True),
                    'natural_recovery_available': data.get('natural_recovery_available', False),
                    'natural_recovery_used': data.get('natural_recovery_used', False),
                    'lands_stride': data.get('lands_stride', False),
                    'natures_ward': data.get('natures_ward', False),
                    'natures_sanctuary': data.get('natures_sanctuary', False),
                    'timeless_body': data.get('timeless_body', False),
                    'beast_spells': data.get('beast_spells', False),
                    'archdruid': data.get('archdruid', False),
                    'circle_spells': data.get('circle_spells', [])
                })
            
            # Merge base and additional parameters
            all_params = {**base_params, **additional_params}
            
            # Use factory to create the correct class instance
            character = create_character(class_type=class_type, **all_params)
            
            campaign = campaign_mgr.add_character(campaign_name, character)
            
            return jsonify({
                'success': True,
                'setup_complete': campaign.setup_complete,
                'characters_count': len(campaign.characters),
                'party_size': campaign.party_size
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400



    @app.route('/campaign/<campaign_name>/character/<character_name>', methods=['GET'])
    def get_character_sheet(campaign_name, character_name):
        """Get full character sheet data"""
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            return jsonify({
                'success': True,
                'character': asdict(char)
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        
