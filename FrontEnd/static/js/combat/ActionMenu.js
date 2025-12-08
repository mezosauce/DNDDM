/**
 * ActionMenu.js
 * Dynamic action menu system for JRPG combat
 * 
 * Features:
 * - Main menu (Attack, Skills, Items, Defend)
 * - Class-specific skill submenus
 * - Resource tracking and validation
 * - Target selection integration
 * - Back/cancel navigation
 */

class ActionMenu {
    constructor(combatController) {
        this.combatController = combatController;
        
        // DOM Elements
        this.menuContainer = document.getElementById('action-menu');
        this.mainMenu = document.getElementById('main-menu');
        this.skillsMenu = document.getElementById('skills-menu');
        this.targetMenu = document.getElementById('target-menu');
        
        // State
        this.currentMenu = 'main';
        this.selectedAction = null;
        this.activeCharacter = null;
        
        console.log('[ActionMenu] Initialized');
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    /**
     * Load character class metadata from JSON
     */
    async loadCharacterClassMetadata() {
        if (this._classMetadata) {
            return this._classMetadata;
        }
        
        try {
            const response = await fetch('/static/data/class_metadata.json');
            this._classMetadata = await response.json();
            console.log('[ActionMenu] Loaded class metadata:', Object.keys(this._classMetadata));
            return this._classMetadata;
        } catch (error) {
            console.error('[ActionMenu] Failed to load class metadata:', error);
            return {};
        }
    }
    
    setupEventListeners() {
        // Main menu buttons
        const mainMenuButtons = this.mainMenu.querySelectorAll('.action-btn');
        mainMenuButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleMainMenuClick(action);
            });
        });
        
        // Back buttons
        document.querySelectorAll('.back-btn').forEach(btn => {
            btn.addEventListener('click', () => this.showMainMenu());
        });
        
        console.log('[ActionMenu] Event listeners attached');
    }
    
    // ========================================================================
    // MENU DISPLAY MANAGEMENT
    // ========================================================================
    
    /**
     * Show action menu for current character's turn
     */
    show(character) {
        console.log('[ActionMenu] Showing menu for:', character.name);
        console.log('[ActionMenu] Character data:', {
            name: character.name,
            class: character.class,
            char_class: character.char_class,
            level: character.level,
            type: character.type,
            participant_id: character.participant_id,
            id: character.id
        });

        console.log('[ActionMenu] Showing menu for:', character.name);
        const participantId = character.participant_id || character.id;
            console.log('[ActionMenu] Looking for participant ID:', participantId);
            
            const allParticipants = this.combatController.getParticipants();
            console.log('[ActionMenu] All participants:', allParticipants.map(p => ({
                id: p.id,
                participant_id: p.participant_id,
                name: p.name,
                type: p.type
            })));
            
            const fullParticipant = allParticipants.find(
                p => {
                    const pId = p.participant_id || p.id;
                    console.log('[ActionMenu] Comparing:', pId, 'with', participantId);
                    return pId === participantId;
                }
            );
            
            console.log('[ActionMenu] Full participant found:', fullParticipant);
            
            this.activeCharacter = fullParticipant || character;
            console.log('[ActionMenu] Active character set to:', this.activeCharacter);
    
            this.menuContainer.style.display = 'block';
            
            // Make sure we're on the main menu
            this.showMainMenu();
            
            // Update button states based on character resources
            this.updateMainMenuStates();
        }
    
    /**
     * Hide action menu (enemy turn)
     */
    hide() {
        console.log('[ActionMenu] Hiding menu');
        this.menuContainer.style.display = 'none';
        this.currentMenu = 'main';
        this.selectedAction = null;
    }
    
    /**
     * Show main action menu
     */
    showMainMenu() {
        console.log('[ActionMenu] Showing main menu');
        
        // Hide all menus
        this.mainMenu.classList.remove('active');
        this.skillsMenu.classList.remove('active');
        this.targetMenu.classList.remove('active');
        
        // Show main menu
        this.mainMenu.classList.add('active');
        this.currentMenu = 'main';
        this.selectedAction = null;
        
        // Exit targeting mode if active
        this.combatController.battlefieldView.exitTargetingMode();
    }
    
    /**
     * Show skills submenu
     */
    showSkillsMenu() {
        console.log('[ActionMenu] Showing skills menu');
        
        // Hide all menus
        this.mainMenu.classList.remove('active');
        this.skillsMenu.classList.remove('active');
        this.targetMenu.classList.remove('active');
        
        // Populate and show skills menu
        this.populateSkillsMenu();
        this.skillsMenu.classList.add('active');
        this.currentMenu = 'skills';
    }
    
    /**
     * Show target selection menu
     */
    showTargetMenu(action) {
        console.log('[ActionMenu] Showing target menu for:', action);
        
        this.selectedAction = action;
        
        // Determine valid targets
        const validTargets = this.getValidTargets(action);
        
        if (validTargets.length === 0) {
            console.warn('[ActionMenu] No valid targets!');
            this.combatController.showError('No valid targets available');
            return;
        }
        
        // If only one valid target, auto-select it
        if (validTargets.length === 1 && action.auto_target_single) {
            console.log('[ActionMenu] Auto-targeting single target');
            this.handleTargetSelected(validTargets[0]);
            return;
        }
        
        // Enter targeting mode on battlefield
        const targetType = action.target_type || 'enemy';

        const validIds = validTargets.map(t => t.participant_id || t.id);
        
        this.combatController.battlefieldView.enterTargetingMode(validIds, targetType);
        
        // Hide menus - battlefield will handle target selection
        this.mainMenu.classList.remove('active');
        this.skillsMenu.classList.remove('active');
        this.targetMenu.classList.remove('active');
        
        this.currentMenu = 'targeting';
    }
    
    /**
     * Reset to main menu
     */
    resetToMainMenu() {
        console.log('[ActionMenu] Resetting to main menu');
        this.showMainMenu();
        this.selectedAction = null;
    }
    
    // ========================================================================
    // MAIN MENU ACTIONS
    // ========================================================================
    
    /**
     * Handle main menu button click
     */

    
    handleMainMenuClick(actionType) {
        console.log('[ActionMenu] Main menu action:', actionType);
        
        switch (actionType) {
            case 'attack':
                this.handleAttack();
                break;
            case 'skills':
                this.showSkillsMenu();
                break;
            case 'items':
                this.handleItems();
                break;
            case 'defend':
                this.handleDefend();
                break;
            default:
                console.warn('[ActionMenu] Unknown action:', actionType);
        }
    }
    
    /**
     * Handle Attack action
     */
    handleAttack() {
        const action = {
            type: 'attack',
            name: 'Attack',
            target_type: 'enemy',
            description: 'Make a basic melee or ranged attack',
            data: {}
        };
        
        this.showTargetMenu(action);
    }
    
    /**
     * Handle Defend action
     */
    handleDefend() {
        const action = {
            type: 'defend',
            name: 'Defend',
            target_type: 'self',
            description: 'Gain +2 AC until your next turn',
            data: {},
            auto_target_single: true
        };
        
        // Defend targets self
        this.selectedAction = action;
        const self = this.combatController.getParticipants().find(
            p => p.id === this.activeCharacter.id
        );
        
        if (self) {
            this.handleTargetSelected(self);
        }
    }
    
    /**
     * Handle Items action (placeholder)
     */
    handleItems() {
        // TODO: Implement item menu
        alert('Item system coming soon!\n\nPlanned features:\n- Healing potions\n- Buff scrolls\n- Thrown weapons\n- Equipment changes');
        this.showMainMenu();
    }
    
    // ========================================================================
    // SKILLS MENU
    // ========================================================================
    
    /**
     * Populate skills menu based on character class
     */
    populateSkillsMenu() {
        console.log('[ActionMenu] Populating skills for:', this.activeCharacter);
        
        const skillsList = document.getElementById('skills-list');
        if (!skillsList) {
            console.error('[ActionMenu] Skills list element not found');
            return;
        }
        
        skillsList.innerHTML = '';
        
        if (!this.activeCharacter) {
            console.error('[ActionMenu] No active character');
            skillsList.innerHTML = '<div class="no-skills">Character data not loaded</div>';
            return;
        }
        
        // Try to get class from multiple possible locations
        const charClass = this.activeCharacter.class || 
                        this.activeCharacter.char_class ||
                        this.activeCharacter.character_class;
        
        if (!charClass) {
            console.error('[ActionMenu] Active character missing class:', this.activeCharacter);
            skillsList.innerHTML = `
                <div class="no-skills">
                    <p>Unable to load class data for ${this.activeCharacter.name}</p>
                    <p style="font-size: 12px; color: #888;">Class information not available</p>
                </div>
            `;
            return;
        }
        
        console.log('[ActionMenu] Character class:', charClass, 'Level:', this.activeCharacter.level);
        
        // Get feature manager for this character
        const characterId = this.activeCharacter.participant_id || this.activeCharacter.id;
        const featureManager = this.combatController.getFeatureManager(characterId);
        
        if (!featureManager) {
            console.warn('[ActionMenu] No feature manager found, creating one...');
            // Create a temporary feature manager
            const manager = this.createFeatureManager(charClass);
            if (manager) {
                manager.initialize(this.activeCharacter.level || 1, this.activeCharacter.stats || {});
            }
        }
        
        // Get class-specific skills
        const skills = this.getClassSkills(charClass, featureManager);
        
        if (skills.length === 0) {
            skillsList.innerHTML = '<div class="no-skills">No skills available</div>';
            return;
        }
        
        // Create skill buttons
        skills.forEach(skill => {
            const skillBtn = this.createSkillButton(skill);
            skillsList.appendChild(skillBtn);
        });
    }
    
    /**
    * Create a feature manager for a class
    */
    createFeatureManager(charClass) {
        const managerClasses = {
            'Barbarian': window.BarbarianFeatureManager,
            'Bard': window.BardFeatureManager,
            'Cleric': window.ClericFeatureManager,
            'Druid': window.DruidFeatureManager
        };
        
        const ManagerClass = managerClasses[charClass];
        
        if (!ManagerClass) {
            console.warn('[ActionMenu] No feature manager class for:', charClass);
            return null;
        }
        
        console.log('[ActionMenu] Creating temporary feature manager for:', charClass);
        return new ManagerClass();
    }
    /**
     * Get available skills for character class
     */
    getClassSkills(charClass, featureManager) {
    console.log('[ActionMenu] Getting skills for class:', charClass, 'Manager:', !!featureManager);
    
    if (!charClass) {
        console.error('[ActionMenu] No class provided to getClassSkills');
        return [];
    }
    
    const skills = [];
    
    // If no feature manager, create a temporary one
    let manager = featureManager;
    if (!manager) {
        console.log('[ActionMenu] No feature manager, creating temporary one');
        manager = this.createTemporaryManager(charClass);
    }
    
    switch (charClass) {
        case 'Barbarian':
            skills.push(...this.getBarbarianSkills(manager));
            break;
        case 'Bard':
            skills.push(...this.getBardSkills(manager));
            break;
        case 'Cleric':
            skills.push(...this.getClericSkills(manager));
            break;
        case 'Druid':
            skills.push(...this.getDruidSkills(manager));
            break;
        default:
            console.warn('[ActionMenu] Unknown class:', charClass);
    }
    
    console.log('[ActionMenu] Found', skills.length, 'skills for', charClass);
    return skills;
}

    /**
     * Create a temporary feature manager for a class
     */
    createTemporaryManager(charClass) {
        console.log('[ActionMenu] Creating temporary manager for:', charClass);
        
        const managerClasses = {
            'Barbarian': window.BarbarianFeatureManager,
            'Bard': window.BardFeatureManager,
            'Cleric': window.ClericFeatureManager,
            'Druid': window.DruidFeatureManager
        };
        
        const ManagerClass = managerClasses[charClass];
        
        if (!ManagerClass) {
            console.error('[ActionMenu] No manager class found for:', charClass);
            return null;
        }
        
        const manager = new ManagerClass();
        
        // Initialize with character data
        const level = this.activeCharacter.level || 1;
        const stats = this.activeCharacter.stats || {
            strength: 10,
            dexterity: 10,
            constitution: 10,
            intelligence: 10,
            wisdom: 10,
            charisma: 10
        };
        
        console.log('[ActionMenu] Initializing manager with level:', level, 'stats:', stats);
        manager.initialize(level, stats);
        
        return manager;
    }
    
    /**
     * Get Barbarian skills
     */
    getBarbarianSkills(manager) {
        const skills = [];
        
        if (manager) {
            // Rage
            if (!manager.currentlyRaging) {
                skills.push({
                    name: 'Rage',
                    description: `+${manager.rageDamage} damage, advantage on STR checks, resistance to physical damage`,
                    cost: `${manager.ragesUsed}/${manager.ragesPerDay} uses`,
                    available: manager.ragesUsed < manager.ragesPerDay,
                    type: 'skill',
                    target_type: 'self',
                    data: { skill_name: 'Rage' },
                    auto_target_single: true
                });
            } else {
                skills.push({
                    name: 'End Rage',
                    description: 'End your current rage',
                    cost: 'Free',
                    available: true,
                    type: 'skill',
                    target_type: 'self',
                    data: { skill_name: 'End Rage' },
                    auto_target_single: true
                });
            }
            
            // Reckless Attack (Level 2+)
            if (manager.level >= 2) {
                skills.push({
                    name: 'Reckless Attack',
                    description: 'Gain advantage on attack rolls this turn, enemies have advantage on you',
                    cost: 'Free (once per turn)',
                    available: true,
                    type: 'skill',
                    target_type: 'enemy',
                    data: { skill_name: 'Reckless Attack' }
                });
            }
        }
        
        return skills;
    }
    
    /**
     * Get Bard skills
     */
    getBardSkills(manager) {
        const skills = [];
        
        if (manager) {
            // Bardic Inspiration
            skills.push({
                name: 'Bardic Inspiration',
                description: `Grant an ally ${manager.bardicInspirationDie} to add to their next check/attack/save`,
                cost: `${manager.bardicInspirationRemaining}/${manager.bardicInspirationUses} uses`,
                available: manager.bardicInspirationRemaining > 0,
                type: 'skill',
                target_type: 'ally',
                data: { skill_name: 'Bardic Inspiration' }
            });
            
            // Spellcasting by level
            this.addSpellSlotSkills(skills, manager);
        }
        
        return skills;
    }
    
    /**
     * Get Cleric skills
     */
    getClericSkills(manager) {
        const skills = [];
        
        if (manager) {
            // Channel Divinity: Turn Undead (Level 2+)
            if (manager.level >= 2) {
                const remaining = manager.channelDivinityUses - manager.channelDivinityUsed;
                skills.push({
                    name: 'Turn Undead',
                    description: `Channel Divinity to turn undead (DC ${manager.getSpellSaveDC()})`,
                    cost: `${remaining}/${manager.channelDivinityUses} uses`,
                    available: remaining > 0,
                    type: 'skill',
                    target_type: 'enemy',
                    data: { skill_name: 'Turn Undead', channel_divinity: true }
                });
            }
            
            // Spellcasting by level
            this.addSpellSlotSkills(skills, manager);
        }
        
        return skills;
    }
    
    /**
     * Get Druid skills
     */
    getDruidSkills(manager) {
        const skills = [];
        
        if (manager) {
            // Wild Shape (Level 2+)
            if (manager.level >= 2) {
                if (!manager.currentlyWildShaped) {
                    skills.push({
                        name: 'Wild Shape',
                        description: `Transform into a beast (CR ${manager.wildShapeMaxCR}, ${manager.wildShapeMaxHours}h)`,
                        cost: `${manager.wildShapeUsesRemaining}/${manager.wildShapeUses} uses`,
                        available: manager.wildShapeUsesRemaining > 0,
                        type: 'skill',
                        target_type: 'self',
                        data: { skill_name: 'Wild Shape' },
                        auto_target_single: true
                    });
                } else {
                    skills.push({
                        name: 'Revert Form',
                        description: `End Wild Shape (currently: ${manager.wildShapeBeast})`,
                        cost: 'Free',
                        available: true,
                        type: 'skill',
                        target_type: 'self',
                        data: { skill_name: 'Revert Form' },
                        auto_target_single: true
                    });
                }
            }
            
            // Spellcasting by level (if not in Wild Shape or has Beast Spells)
            if (!manager.currentlyWildShaped || manager.level >= 18) {
                this.addSpellSlotSkills(skills, manager);
            }
        }
        
        return skills;
    }
    
    /**
     * Add spell slot options as skills
     */
    addSpellSlotSkills(skills, manager) {
        if (!manager.spellSlots) return;
        
        for (let level = 1; level <= 9; level++) {
            const total = manager.spellSlots[level];
            if (!total || total === 0) continue;
            
            const used = manager.spellSlotsUsed[level] || 0;
            const remaining = total - used;
            skills.push({
            name: `Healing Spell (Lv ${level})`,
            description: `Cast a ${this.getSpellLevelName(level)} healing spell`,
            cost: `${remaining}/${total} slots`,
            available: remaining > 0,
            type: 'spell',
            target_type: 'ally', 
            data: { 
                spell_level: level,
                spell_type: 'healing',
                spell_name: `Cure Wounds` 
            }
        });
        
        skills.push({
            name: `Damage Spell (Lv ${level})`,
            description: `Cast a ${this.getSpellLevelName(level)} damage spell`,
            cost: `${remaining}/${total} slots`,
            available: remaining > 0,
            type: 'spell',
            target_type: 'enemy', 
            data: { 
                spell_level: level,
                spell_type: 'damage',
                spell_name: `Magic Missile`
            }
        });
        }
    }
    
    /**
     * Get spell level name
     */
    getSpellLevelName(level) {
        const names = {
            1: '1st-level',
            2: '2nd-level',
            3: '3rd-level',
            4: '4th-level',
            5: '5th-level',
            6: '6th-level',
            7: '7th-level',
            8: '8th-level',
            9: '9th-level'
        };
        return names[level] || `${level}th-level`;
    }
    
    /**
     * Create skill button element
     */
    createSkillButton(skill) {
        const btn = document.createElement('button');
        btn.className = 'skill-btn';
        btn.disabled = !skill.available;
        
        btn.innerHTML = `
            <div class="skill-name">${skill.name}</div>
            <div class="skill-description">${skill.description}</div>
            <div class="skill-cost ${skill.available ? '' : 'unavailable'}">${skill.cost}</div>
        `;
        
        if (skill.available) {
            btn.addEventListener('click', () => this.handleSkillSelected(skill));
        }
        
        return btn;
    }
    
    /**
     * Handle skill selection
     */
    handleSkillSelected(skill) {
        console.log('[ActionMenu] Skill selected:', skill.name);
        
        const action = {
            type: skill.type,
            name: skill.name,
            target_type: skill.target_type,
            description: skill.description,
            data: skill.data,
            auto_target_single: skill.auto_target_single
        };
        
        this.showTargetMenu(action);
    }
    
    // ========================================================================
    // TARGET HANDLING
    // ========================================================================
    
    /**
     * Get valid targets for an action
     */
    getValidTargets(action) {
        const targetType = action.target_type || 'enemy';
        
        switch (targetType) {
            case 'enemy':
                return this.combatController.getEnemies();
            case 'ally':
                return this.combatController.getAllies();
            case 'self':
                return [this.activeCharacter];
            case 'any':
                return this.combatController.getParticipants();
            default:
                console.warn('[ActionMenu] Unknown target type:', targetType);
                return [];
        }
    }

    
    /**
     * Handle target selection
     */
 
    /**
 * Handle target selection
 */
    handleTargetSelected(targetId) {
        console.log('[ActionMenu] Target selected:', targetId);
        console.log('[ActionMenu] Selected Action:', this.selectedAction);
        
        if (!this.selectedAction) {
            console.error('[ActionMenu] No action selected!');
            return;
        }
        
        // Get the full target participant object
        const target = this.combatController.getParticipants().find(
            p => (p.participant_id || p.id) === targetId
        );
        
        if (!target) {
            console.error('[ActionMenu] Target not found:', targetId);
            this.combatController.showError('Invalid target selected');
            return;
        }
        
        console.log('[ActionMenu] Found target:', target.name);
        console.log('[ActionMenu] Executing action:', this.selectedAction.name, 'on', target.name);
        
        // Execute the action through the combat controller
        this.combatController.processPlayerAction(this.selectedAction, target);
        
        // Reset menu
        this.selectedAction = null;

    }

    // ========================================================================
    // STATE UPDATES
    // ========================================================================
    
    /**
     * Update main menu button states
     */
    updateMainMenuStates() {

        if (!this.activeCharacter || !this.activeCharacter.class) {
            console.warn('[ActionMenu] Cannot update menu states - character data missing');
            return;
        }
        // Check if character has usable skills
        const characterId = this.activeCharacter.participant_id || this.activeCharacter.id;
        const featureManager = this.combatController.getFeatureManager(characterId);
        const skills = this.getClassSkills(this.activeCharacter.class, featureManager);
        const hasUsableSkills = skills.some(s => s.available);
        
        const skillsBtn = this.mainMenu.querySelector('[data-action="skills"]');
        if (skillsBtn) {
            skillsBtn.disabled = !hasUsableSkills;
        }
        
        // Items always available (placeholder)
        const itemsBtn = this.mainMenu.querySelector('[data-action="items"]');
        if (itemsBtn) {
            itemsBtn.disabled = false; // Will be true when items are implemented
        }
    }
    
    /**
     * Refresh menu (useful after resource changes)
     */
    refresh() {
        if (this.currentMenu === 'main') {
            this.updateMainMenuStates();
        } else if (this.currentMenu === 'skills') {
            this.populateSkillsMenu();
        }
    }
}

// Export for global use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ActionMenu;
}