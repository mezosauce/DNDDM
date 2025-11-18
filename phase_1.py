#!/usr/bin/env python3
"""
Phase 1: Setup & Character Creation Routes
Handles character creation, updates, and phase advancement
"""

from flask import render_template, request, jsonify
from dataclasses import asdict

# These will be imported from main.py when we integrate
# from main import app, campaign_mgr, Character

from Head.Class import create_character


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
            
            # Prepare base parameters that all characters need
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
                'inventory': data.get('inventory', []),
                'notes': data.get('notes', ''),
                'alignment': data.get('alignment', 'True Neutral'),
                'has_inspiration': data.get('has_inspiration', False),
                'armor_worn': data.get('armor_worn', ''),
                'background_feature': data.get('background_feature', ''),
                'skill_proficiencies': data.get('skill_proficiencies', []),
                'tool_proficiencies': data.get('tool_proficiencies', []),
                'languages_known': data.get('languages_known', []),
                'personality_traits': data.get('personality_traits', []),
                'ideal': data.get('ideal', ''),
                'bond': data.get('bond', ''),
                'flaw': data.get('flaw', ''),
                'saving_throw_proficiencies': data.get('saving_throw_proficiencies', []),
                'background_equipment': data.get('background_equipment', [])
            }
            
            # Handle currency separately
            base_params['currency'] = data.get('currency', {'cp': 0, 'sp': 0, 'ep': 0, 'gp': 0, 'pp': 0})
            
            # For class-specific parameters, pass them directly and let the factory handle them
            # The factory will ignore unknown parameters for each class
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
            

            if class_type =="Fighter":
                additional_params.update({
                    """

                    martial_archetype: str = ""  # "Champion", "Battle Master", "Eldritch Knight"

                    fighting_styles: List[str] = field(default_factory=list)
                    second_wind_used: bool = False
                    action_surge_uses: int = 0
                    action_surge_max_uses: int = 1
                    indomitable_uses: int = 0
                    indomitable_max_uses: int = 1

                    extra_attacks: int = 1  # Base is 1 attack, increases at levels 5, 11, 20

                    improved_critical: bool = False  # Crit on 19-20
                    remarkable_athlete: bool = False  # Level 7 Champion
                    additional_fighting_style: bool = False  # Level 10 Champion
                    superior_critical: bool = False  # Crit on 18-20
                    survivor_active: bool = False  # Level 18 Champion
                    

                    archetype_feature_3: bool = False
                    archetype_feature_7: bool = False
                    archetype_feature_10: bool = False
                    archetype_feature_15: bool = False
                    archetype_feature_18: bool = False
                    



                    """


                    'martial_archetype': data.get('martial_archetype', ''),
                    'fighting_styles': data.get('fighting_styles', []),
                    'second_wind_used': data.get('second_wind_used', False),
                    'action_surge_uses': int(data.get('action_surge_uses', 0)),
                    'action_surge_max_uses': int(data.get('action_surge_max_uses', 1)),
                    'indomitable_uses': int(data.get('indomitable_uses', 0)),
                    'indomitable_max_uses': int(data.get('indomitable_max_uses', 1)),
                    'extra_attacks': int(data.get('extra_attacks', 1)),
                    'improved_critical': data.get('improved_critical', False),
                    'remarkable_athlete': data.get('remarkable_athlete', False),
                    'additional_fighting_style': data.get('additional_fighting_style', False),
                    'superior_critical': data.get('superior_critical', False),
                    'survivor_active': data.get('survivor_active', False),
                    'archetype_feature_3': data.get('archetype_feature_3', False),
                    'archetype_feature_7': data.get('archetype_feature_7', False),
                    'archetype_feature_10': data.get('archetype_feature_10', False),
                    'archetype_feature_15': data.get('archetype_feature_15', False),
                    'archetype_feature_18': data.get('archetype_feature_18', False)

                })

                if class_type == "Monk":
                    additional_params.update({
                        """
                        monastic_tradition: str = ""  # "Way of the Open Hand", "Way of Shadow", "Way of the Four Elements"

                        ki_points: int = 0
                        ki_points_max: int = 0
                        ki_save_dc: int = 0

                        martial_arts_die: int = 4  # d4 at level 1, progresses per table
                        martial_arts_active: bool = True

                        unarmored_movement: int = 0  # Bonus movement speed
                        unarmored_defense_active: bool = True  # AC = 10 + DEX + WIS when no armor

                        deflect_missiles_available: bool = False  # Level 3+
                        slow_fall_available: bool = False  # Level 4+
                        extra_attack: bool = False  # Level 5+
                        stunning_strike_available: bool = False  # Level 5+
                        ki_empowered_strikes: bool = False  # Level 6+
                        evasion_available: bool = False  # Level 7+
                        stillness_of_mind_available: bool = False  # Level 7+
                        purity_of_body: bool = False  # Level 10+
                        tongue_of_sun_moon: bool = False  # Level 13+
                        diamond_soul: bool = False  # Level 14+
                        timeless_body: bool = False  # Level 15+
                        empty_body_available: bool = False  # Level 18+
                        perfect_self: bool = False  # Level 20

                        can_move_vertically: bool = False  # Level 9+ unarmored movement
                        can_move_on_liquid: bool = False  # Level 9+ unarmored movement

                        tradition_feature_3: bool = False
                        tradition_feature_6: bool = False
                        tradition_feature_11: bool = False
                        tradition_feature_17: bool = False

                        open_hand_technique: bool = False
                        wholeness_of_body_available: bool = False
                        tranquility_active: bool = False
                        quivering_palm_active: bool = False
                        quivering_palm_target: str = ""  # Name of creature affected by quivering palm
                        """
                        
                        'monastic_tradition': data.get('monastic_tradition', ''),
                        'ki_points': int(data.get('ki_points', 0)),
                        'ki_points_max': int(data.get('ki_points_max', 0)),
                        'ki_save_dc': int(data.get('ki_save_dc', 0)),
                        'martial_arts_die': int(data.get('martial_arts_die', 4)),
                        'martial_arts_active': data.get('martial_arts_active', True),
                        'unarmored_movement': int(data.get('unarmored_movement', 0)),
                        'unarmored_defense_active': data.get('unarmored_defense_active', True),
                        'deflect_missiles_available': data.get('deflect_missiles_available', False),
                        'slow_fall_available': data.get('slow_fall_available', False),
                        'extra_attack': data.get('extra_attack', False),
                        'stunning_strike_available': data.get('stunning_strike_available', False),
                        'ki_empowered_strikes': data.get('ki_empowered_strikes', False),
                        'evasion_available': data.get('evasion_available', False),
                        'stillness_of_mind_available': data.get('stillness_of_mind_available', False),
                        'purity_of_body': data.get('purity_of_body', False),
                        'tongue_of_sun_moon': data.get('tongue_of_sun_moon', False),
                        'diamond_soul': data.get('diamond_soul', False),
                        'timeless_body': data.get('timeless_body', False),
                        'empty_body_available': data.get('empty_body_available', False),
                        'perfect_self': data.get('perfect_self', False),
                        'can_move_vertically': data.get('can_move_vertically', False),
                        'can_move_on_liquid': data.get('can_move_on_liquid', False),
                        'tradition_feature_3': data.get('tradition_feature_3', False),
                        'tradition_feature_6': data.get('tradition_feature_6', False),
                        'tradition_feature_11': data.get('tradition_feature_11', False),
                        'tradition_feature_17': data.get('tradition_feature_17', False),
                        'open_hand_technique': data.get('open_hand_technique', False),
                        'wholeness_of_body_available': data.get('wholeness_of_body_available', False),
                        'tranquility_active': data.get('tranquility_active', False),
                        'quivering_palm_active': data.get('quivering_palm_active', False),
                        'quivering_palm_target': data.get('quivering_palm_target', '')
                    })
                    
                    if class_type == "Paladin":
                        additional_params.update({
                            """
                            sacred_oath: str = ""  # "Oath of Devotion", etc.

                            divine_sense_uses: int = 1  # 1 + CHA mod
                            divine_sense_used: int = 0

                            lay_on_hands_pool: int = 5  # level × 5
                            lay_on_hands_remaining: int = 5

                            prepared_spells: List[str] = field(default_factory=list)
                            spell_slots: Dict[int, int] = field(default_factory=dict)  # {level: remaining}
                            max_spell_slots: Dict[int, int] = field(default_factory=dict)  # {level: max}

                            fighting_style: str = ""  # "Defense", "Dueling", "Great Weapon Fighting", "Protection"

                            divine_smite_available: bool = False

                            aura_of_protection_range: int = 0  # 10ft at 6th, 30ft at 18th
                            aura_of_courage_range: int = 0  # 10ft at 10th, 30ft at 18th
                            aura_of_devotion_range: int = 0  # 10ft at 7th, 30ft at 18th (Oath of Devotion)

                            divine_health: bool = False
                            extra_attack: bool = False
                            improved_divine_smite: bool = False
                            cleansing_touch_uses: int = 0
                            cleansing_touch_remaining: int = 0

                            sacred_weapon_available: bool = False
                            turn_the_unholy_available: bool = False
                            purity_of_spirit: bool = False
                            holy_nimbus_available: bool = False

                            channel_divinity_uses: int = 1
                            channel_divinity_used: int = 0
                            """
                            
                            'sacred_oath': data.get('sacred_oath', ''),
                            'divine_sense_uses': int(data.get('divine_sense_uses', 1)),
                            'divine_sense_used': int(data.get('divine_sense_used', 0)),
                            'lay_on_hands_pool': int(data.get('lay_on_hands_pool', 5)),
                            'lay_on_hands_remaining': int(data.get('lay_on_hands_remaining', 5)),
                            'prepared_spells': data.get('prepared_spells', []),
                            'spell_slots': data.get('spell_slots', {}),
                            'max_spell_slots': data.get('max_spell_slots', {}),
                            'fighting_style': data.get('fighting_style', ''),
                            'divine_smite_available': data.get('divine_smite_available', False),
                            'aura_of_protection_range': int(data.get('aura_of_protection_range', 0)),
                            'aura_of_courage_range': int(data.get('aura_of_courage_range', 0)),
                            'aura_of_devotion_range': int(data.get('aura_of_devotion_range', 0)),
                            'divine_health': data.get('divine_health', False),
                            'extra_attack': data.get('extra_attack', False),
                            'improved_divine_smite': data.get('improved_divine_smite', False),
                            'cleansing_touch_uses': int(data.get('cleansing_touch_uses', 0)),
                            'cleansing_touch_remaining': int(data.get('cleansing_touch_remaining', 0)),
                            'sacred_weapon_available': data.get('sacred_weapon_available', False),
                            'turn_the_unholy_available': data.get('turn_the_unholy_available', False),
                            'purity_of_spirit': data.get('purity_of_spirit', False),
                            'holy_nimbus_available': data.get('holy_nimbus_available', False),
                            'channel_divinity_uses': int(data.get('channel_divinity_uses', 1)),
                            'channel_divinity_used': int(data.get('channel_divinity_used', 0))
                        })

                        if class_type == "Ranger":
                            additional_params.update({
                                """
                                ranger_archetype: str = ""  # "Hunter" or "Beast Master"

                                favored_enemies: List[str] = field(default_factory=list)  # List of enemy types
                                favored_enemy_languages: List[str] = field(default_factory=list)  # Languages learned

                                favored_terrains: List[str] = field(default_factory=list)  # List of terrain types

                                fighting_style: str = ""  # "Archery", "Defense", "Dueling", or "Two-Weapon Fighting"

                                spells_known: List[str] = field(default_factory=list)  # Known spells
                                spell_slots: Dict[int, int] = field(default_factory=dict)  # Available slots by level
                                spells_prepared: List[str] = field(default_factory=list)  # Prepared spells

                                primeval_awareness_active: bool = False
                                lands_stride_active: bool = False
                                hide_in_plain_sight_active: bool = False
                                vanish_active: bool = False
                                feral_senses_active: bool = False
                                foe_slayer_active: bool = False

                                hunters_prey: str = ""  # "Colossus Slayer", "Giant Killer", or "Horde Breaker"
                                defensive_tactics: str = ""  # "Escape the Horde", "Multiattack Defense", or "Steel Will"
                                multiattack: str = ""  # "Volley" or "Whirlwind Attack"
                                superior_hunters_defense: str = ""  # "Evasion", "Stand Against the Tide", or "Uncanny Dodge"
                                """
                                
                                'ranger_archetype': data.get('ranger_archetype', ''),
                                'favored_enemies': data.get('favored_enemies', []),
                                'favored_enemy_languages': data.get('favored_enemy_languages', []),
                                'favored_terrains': data.get('favored_terrains', []),
                                'fighting_style': data.get('fighting_style', ''),
                                'spells_known': data.get('spells_known', []),
                                'spell_slots': data.get('spell_slots', {}),
                                'spells_prepared': data.get('spells_prepared', []),
                                'primeval_awareness_active': data.get('primeval_awareness_active', False),
                                'lands_stride_active': data.get('lands_stride_active', False),
                                'hide_in_plain_sight_active': data.get('hide_in_plain_sight_active', False),
                                'vanish_active': data.get('vanish_active', False),
                                'feral_senses_active': data.get('feral_senses_active', False),
                                'foe_slayer_active': data.get('foe_slayer_active', False),
                                'hunters_prey': data.get('hunters_prey', ''),
                                'defensive_tactics': data.get('defensive_tactics', ''),
                                'multiattack': data.get('multiattack', ''),
                                'superior_hunters_defense': data.get('superior_hunters_defense', '')
                            })

                            if class_type == "Rogue":
                                additional_params.update({
                                    """
                                    roguish_archetype: str = ""  # "Thief", "Assassin", or "Arcane Trickster"

                                    sneak_attack_dice: int = 1  # Number of d6 dice for sneak attack
                                    sneak_attack_used_this_turn: bool = False

                                    expertise_skills: Set[str] = field(default_factory=set)
                                    expertise_thieves_tools: bool = False

                                    cunning_action_available: bool = False

                                    uncanny_dodge_available: bool = False
                                    evasion_available: bool = False
                                    reliable_talent_available: bool = False
                                    blindsense_available: bool = False
                                    slippery_mind_available: bool = False
                                    elusive_available: bool = False
                                    stroke_of_luck_available: bool = False
                                    stroke_of_luck_used: bool = False

                                    fast_hands_available: bool = False
                                    second_story_work_available: bool = False
                                    supreme_sneak_available: bool = False
                                    use_magic_device_available: bool = False
                                    thiefs_reflexes_available: bool = False

                                    archetype_feature_3: bool = False
                                    archetype_feature_9: bool = False
                                    archetype_feature_13: bool = False
                                    archetype_feature_17: bool = False
                                    """

                                    'roguish_archetype': data.get('roguish_archetype', ''),
                                    'sneak_attack_dice': int(data.get('sneak_attack_dice', 1)),
                                    'sneak_attack_used_this_turn': data.get('sneak_attack_used_this_turn', False),
                                    'expertise_skills': set(data.get('expertise_skills', [])),
                                    'expertise_thieves_tools': data.get('expertise_thieves_tools', False),
                                    'cunning_action_available': data.get('cunning_action_available', False),
                                    'uncanny_dodge_available': data.get('uncanny_dodge_available', False),
                                    'evasion_available': data.get('evasion_available', False),
                                    'reliable_talent_available': data.get('reliable_talent_available', False),
                                    'blindsense_available': data.get('blindsense_available', False),
                                    'slippery_mind_available': data.get('slippery_mind_available', False),
                                    'elusive_available': data.get('elusive_available', False),
                                    'stroke_of_luck_available': data.get('stroke_of_luck_available', False),
                                    'stroke_of_luck_used': data.get('stroke_of_luck_used', False),
                                    'fast_hands_available': data.get('fast_hands_available', False),
                                    'second_story_work_available': data.get('second_story_work_available', False),
                                    'supreme_sneak_available': data.get('supreme_sneak_available', False),
                                    'use_magic_device_available': data.get('use_magic_device_available', False),
                                    'thiefs_reflexes_available': data.get('thiefs_reflexes_available', False),
                                    'archetype_feature_3': data.get('archetype_feature_3', False),
                                    'archetype_feature_9': data.get('archetype_feature_9', False),
                                    'archetype_feature_13': data.get('archetype_feature_13', False),
                                    'archetype_feature_17': data.get('archetype_feature_17', False)
                                })

                                if class_type == "Sorcerer":
                                    additional_params.update({
                                        """
                                        sorcerous_origin: str = ""  # "Draconic Bloodline", "Wild Magic", etc.

                                        cantrips_known: int = 4
                                        spells_known: List[str] = field(default_factory=list)
                                        spell_slots: Dict[int, int] = field(default_factory=dict)  # {level: max_slots}
                                        spell_slots_used: Dict[int, int] = field(default_factory=dict)  # {level: used_slots}

                                        sorcery_points: int = 0
                                        sorcery_points_max: int = 0

                                        metamagic_options: List[str] = field(default_factory=list)

                                        wild_magic_surge_available: bool = False
                                        tides_of_chaos_available: bool = False

                                        origin_feature_1: bool = False
                                        origin_feature_6: bool = False
                                        origin_feature_14: bool = False
                                        origin_feature_18: bool = False
                                        """

                                        'sorcerous_origin': data.get('sorcerous_origin', ''),
                                        'cantrips_known': int(data.get('cantrips_known', 4)),
                                        'spells_known': data.get('spells_known', []),
                                        'spell_slots': data.get('spell_slots', {}),
                                        'spell_slots_used': data.get('spell_slots_used', {}),
                                        'sorcery_points': int(data.get('sorcery_points', 0)),
                                        'sorcery_points_max': int(data.get('sorcery_points_max', 0)),
                                        'metamagic_options': data.get('metamagic_options', []),
                                        'wild_magic_surge_available': data.get('wild_magic_surge_available', False),
                                        'tides_of_chaos_available': data.get('tides_of_chaos_available', False),
                                        'origin_feature_1': data.get('origin_feature_1', False),
                                        'origin_feature_6': data.get('origin_feature_6', False),
                                        'origin_feature_14': data.get('origin_feature_14', False),
                                        'origin_feature_18': data.get('origin_feature_18', False)
                                    })

                                if class_type == "Warlock":
                                    additional_params.update({
                                        """
                                        otherworldly_patron: str = ""  # "The Fiend", "The Archfey", "The Great Old One"
                                        pact_boon: str = ""  # "Pact of the Chain", "Pact of the Blade", "Pact of the Tome"
                                        cantrips_known: int = 2
                                        spells_known: int = 2
                                        spell_slots: int = 1
                                        spell_slot_level: int = 1
                                        spell_slots_used: int = 0
                                        eldritch_invocations_known: int = 0
                                        eldritch_invocations: Set[str] = field(default_factory=set)
                                        mystic_arcanum_6: str = ""
                                        mystic_arcanum_7: str = ""
                                        mystic_arcanum_8: str = ""
                                        mystic_arcanum_9: str = ""
                                        mystic_arcanum_used: Dict[str, bool] = field(default_factory=dict)
                                        
                                        spellcasting_ability: str = "charisma"
                                        has_familiar: bool = False
                                        familiar_form: str = ""
                                        pact_weapon: str = ""
                                        book_of_shadows: bool = False
                                        book_of_shadows_cantrips: Set[str] = field(default_factory=set)

                                        dark_ones_blessing_thp: int = 0
                                        dark_ones_own_luck_used: bool = False
                                        fiendish_resistance_type: str = ""
                                        hurl_through_hell_used: bool = False
                                        """

                                        'otherworldly_patron': data.get('otherworldly_patron', ''),
                                        'pact_boon': data.get('pact_boon', ''),
                                        'cantrips_known': int(data.get('cantrips_known', 2)),
                                        'spells_known': int(data.get('spells_known', 2)),
                                        'spell_slots': int(data.get('spell_slots', 1)),
                                        'spell_slot_level': int(data.get('spell_slot_level', 1)),
                                        'spell_slots_used': int(data.get('spell_slots_used', 0)),
                                        'eldritch_invocations_known': int(data.get('eldritch_invocations_known', 0)),
                                        'eldritch_invocations': set(data.get('eldritch_invocations', [])),
                                        'mystic_arcanum_6': data.get('mystic_arcanum_6', ''),
                                        'mystic_arcanum_7': data.get('mystic_arcanum_7', ''),
                                        'mystic_arcanum_8': data.get('mystic_arcanum_8', ''),
                                        'mystic_arcanum_9': data.get('mystic_arcanum_9', ''),
                                        'mystic_arcanum_used': data.get('mystic_arcanum_used', {
                                            '6': False,
                                            '7': False,
                                            '8': False,
                                            '9': False}),
                                        'spellcasting_ability': data.get('spellcasting_ability', 'charisma'),
                                        'has_familiar': data.get('has_familiar', False),
                                        'familiar_form': data.get('familiar_form', ''),
                                        'pact_weapon': data.get('pact_weapon', ''),
                                        'book_of_shadows': data.get('book_of_shadows', False),
                                        'book_of_shadows_cantrips': set(data.get('book_of_shadows_cantrips', [])),
                                        'dark_ones_blessing_thp': int(data.get('dark_ones_blessing_thp', 0)),
                                        'dark_ones_own_luck_used': data.get('dark_ones_own_luck_used', False),
                                        'fiendish_resistance_type': data.get('fiendish_resistance_type', ''),
                                        'hurl_through_hell_used': data.get('hurl_through_hell_used', False)

                                    })

                                    if class_type == "Wizard":
                                        additional_params.update({
                                            """
                                            arcane_tradition: str = ""  # Chosen at level 2 (e.g., "School of Evocation")

                                            cantrips_known: int = 3
                                            spellbook: List[str] = field(default_factory=list)  # List of known spells
                                            prepared_spells: List[str] = field(default_factory=list)  # Currently prepared spells

                                            spell_slots: Dict[int, int] = field(default_factory=lambda: {
                                                1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0
                                            })
                                            spell_slots_used: Dict[int, int] = field(default_factory=lambda: {
                                                1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0
                                            })

                                            arcane_recovery_available: bool = True  # Resets on long rest
                                            arcane_recovery_slots_max: int = 1  # Max spell slot levels recoverable
s
                                            spell_mastery_1st: str = ""  # 1st level spell for Spell Mastery (level 18)
                                            spell_mastery_2nd: str = ""  # 2nd level spell for Spell Mastery (level 18)
                                            signature_spell_1: str = ""  # First 3rd level signature spell (level 20)
                                            signature_spell_2: str = ""  # Second 3rd level signature spell (level 20)
                                            signature_spell_1_used: bool = False
                                            signature_spell_2_used: bool = False

                                            evocation_savant: bool = False  # Level 2 Evocation
                                            sculpt_spells: bool = False  # Level 2 Evocation
                                            potent_cantrip: bool = False  # Level 6 Evocation
                                            empowered_evocation: bool = False  # Level 10 Evocation
                                            overchannel_available: bool = False  # Level 14 Evocation
                                            overchannel_uses: int = 0  # Track uses for damage calculation

                                            tradition_feature_2: bool = False
                                            tradition_feature_6: bool = False
                                            tradition_feature_10: bool = False
                                            tradition_feature_14: bool = False
                                            """

                                            'arcane_tradition': data.get('arcane_tradition', ''),
                                            'cantrips_known': int(data.get('cantrips_known', 3)),
                                            'spellbook': data.get('spellbook', []),
                                            'prepared_spells': data.get('prepared_spells', []),
                                            'spell_slots': data.get('spell_slots', {
                                                1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0
                                            }),
                                            'spell_slots_used': data.get('spell_slots_used', {
                                                1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0
                                            }),
                                            'arcane_recovery_available': data.get('arcane_recovery_available', True),
                                            'arcane_recovery_slots_max': int(data.get('arcane_recovery_slots_max', 1)),
                                            'spell_mastery_1st': data.get('spell_mastery_1st', ''),
                                            'spell_mastery_2nd': data.get('spell_mastery_2nd', ''),
                                            'signature_spell_1': data.get('signature_spell_1', ''),
                                            'signature_spell_2': data.get('signature_spell_2', ''),
                                            'signature_spell_1_used': data.get('signature_spell_1_used', False),
                                            'signature_spell_2_used': data.get('signature_spell_2_used', False),
                                            'evocation_savant': data.get('evocation_savant', False),
                                            'sculpt_spells': data.get('sculpt_spells', False),
                                            'potent_cantrip': data.get('potent_cantrip', False),
                                            'empowered_evocation': data.get('empowered_evocation', False),
                                            'overchannel_available': data.get('overchannel_available', False),
                                            'overchannel_uses': int(data.get('overchannel_uses', 0)),
                                            'tradition_feature_2': data.get('tradition_feature_2', False),
                                            'tradition_feature_6': data.get('tradition_feature_6', False),
                                            'tradition_feature_10': data.get('tradition_feature_10', False),
                                            'tradition_feature_14': data.get('tradition_feature_14', False)
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







    @app.route('/campaign/<campaign_name>/character/<character_name>/currency/remove', methods=['POST'])
    def remove_character_currency(campaign_name, character_name):
        """Remove currency from a character"""
        data = _get_json()
        coin_type = data.get('coin_type')
        amount = int(data.get('amount', 0))
        
        if not coin_type or amount <= 0:
            return jsonify({'error': 'Invalid coin_type or amount'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            success = char.remove_currency(coin_type, amount)
            
            if not success:
                return jsonify({'error': 'Insufficient funds'}), 400
            
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'currency': char.currency,
                'total_gp': char.get_total_gold_value()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/currency/pay', methods=['POST'])
    def pay_cost(campaign_name, character_name):
        """Pay a cost in gold (auto-converts currency)"""
        data = _get_json()
        cost_gp = float(data.get('cost', 0))
        
        if cost_gp <= 0:
            return jsonify({'error': 'Invalid cost'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            success = char.pay_cost(cost_gp)
            
            if not success:
                return jsonify({
                    'error': 'Insufficient funds',
                    'required': cost_gp,
                    'available': char.get_total_gold_value()
                }), 400
            
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'paid': cost_gp,
                'remaining_currency': char.currency,
                'remaining_gp': char.get_total_gold_value()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/currency/convert', methods=['POST'])
    def convert_currency(campaign_name, character_name):
        """Convert currency between denominations"""
        data = _get_json()
        from_type = data.get('from_type')
        to_type = data.get('to_type')
        amount = int(data.get('amount', 0))
        
        if not from_type or not to_type or amount <= 0:
            return jsonify({'error': 'Invalid parameters'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            success = char.convert_currency(from_type, to_type, amount)
            
            if not success:
                return jsonify({'error': 'Conversion failed (insufficient funds or invalid amount)'}), 400
            
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'currency': char.currency,
                'total_gp': char.get_total_gold_value()
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/inventory/add', methods=['POST'])
    def add_inventory_item(campaign_name, character_name):
        """Add item to character inventory"""
        data = _get_json()
        item = data.get('item', '').strip()
        
        if not item:
            return jsonify({'error': 'No item provided'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            char.inventory.append(item)
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'inventory': char.inventory
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/inventory/remove', methods=['POST'])
    def remove_inventory_item(campaign_name, character_name):
        """Remove item from character inventory"""
        data = _get_json()
        item = data.get('item', '').strip()
        
        if not item:
            return jsonify({'error': 'No item provided'}), 400
        
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            if item in char.inventory:
                char.inventory.remove(item)
                campaign_mgr.update_character(campaign_name, char)
                
                return jsonify({
                    'success': True,
                    'inventory': char.inventory
                })
            else:
                return jsonify({'error': 'Item not found in inventory'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 400


    @app.route('/campaign/<campaign_name>/character/<character_name>/inspiration/toggle', methods=['POST'])
    def toggle_inspiration(campaign_name, character_name):
        """Toggle inspiration for a character"""
        try:
            char = campaign_mgr.get_character(campaign_name, character_name)
            if not char:
                return jsonify({'error': 'Character not found'}), 404
            
            char.has_inspiration = not char.has_inspiration
            campaign_mgr.update_character(campaign_name, char)
            
            return jsonify({
                'success': True,
                'has_inspiration': char.has_inspiration
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
        
