/**
 * Combat View Controller
 * Main orchestrator for JRPG-style combat system
 * 
 * Responsibilities:
 * - Initialize combat from backend state
 * - Manage combat flow (turns, rounds, phases)
 * - Coordinate between view components
 * - Handle player input and AI turns
 * - Process combat actions via API
 * - Detect victory/defeat conditions
 */

class CombatViewController {
    constructor(campaignName, combatId) {
        this.campaignName = campaignName;
        this.combatId = combatId;
        
        // State
        this.combatState = null;
        this.currentTurnParticipant = null;
        this.selectedAction = null;
        this.selectedTarget = null;
        this.isProcessingAction = false;
        this.combatEnded = false;

        // Components (will be initialized)
        this.battlefieldView = null;
        this.actionMenu = null;
        this.combatLog = null;
        this.animator = null;
        
        // Class Feature Managers (for player characters)
        this.featureManagers = {};
        
        // Configuration
        this.API_BASE = window.API_BASE || '';
        this.AUTO_ENEMY_TURNS = true;
        this.ANIMATION_SPEED = 1; // 1 = normal, 2 = fast, 0.5 = slow
    }

    // ========================================================================
    // INITIALIZATION
    // ========================================================================

    async initialize() {
        console.log('[Combat] Initializing combat controller...');
        
        try {
            // Initialize components
            this.initializeComponents();
            
            // Load combat state from backend
            await this.loadCombatState();
            
            await this.loadFullCharacterData();

            /// Setup event listeners
            this.setupEventListeners();

            // Render initial state
            this.render();
            
            // Start combat flow
            this.startCombatFlow();
            
            console.log('[Combat] ✓ Initialization complete');
        } catch (error) {
            console.error('[Combat] ✗ Initialization failed:', error);
            this.showError('Failed to initialize combat: ' + error.message);
        }
    }

    initializeComponents() {
        // Initialize view components
        this.battlefieldView = new BattlefieldView(this);
        this.actionMenu = new ActionMenu(this);
        this.combatLog = new CombatLog();
        this.animator = new CombatAnimations();
        
        console.log('[Combat] Components initialized');
    }

    async loadCombatState() {
        console.log('[Combat] Loading combat state from backend...');
        
        const response = await fetch(
            `${this.API_BASE}/api/combat/${this.combatId}/summary`,
            { method: 'GET' }
        );
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load combat state');
        }
        
        this.combatState = data.summary;
        console.log('[Combat] ✓ State loaded:', this.combatState);
        
        console.log('[Combat] Participants:', this.combatState.participants.map(p => ({
            id: p.id,
            participant_id: p.participant_id,
            name: p.name,
            type: p.type,
            class: p.class,
            level: p.level
        })));
        
        console.log('[Combat] Current turn:', this.combatState.current_turn);
        // Initialize class feature managers for player characters
        this.initializeFeatureManagers();
    }

    async loadFullCharacterData() {
        console.log('[Combat] Loading full character data...');
        
        try {
            // Fetch full character data from the campaign
            const response = await fetch(
                `${this.API_BASE}/api/campaign/${this.campaignName}/characters`,
                { method: 'GET' }
            );
            
            if (!response.ok) {
                console.warn('[Combat] Could not load full character data');
                return;
            }
            
            const data = await response.json();
            
            if (data.success && data.characters) {
                // Merge full character data into combat participants
                this.combatState.participants.forEach(participant => {
                    if (participant.type === 'character') {
                        const fullChar = data.characters.find(c => c.name === participant.name);
                        if (fullChar) {
                            // Add missing fields
                            participant.class = fullChar.char_class || fullChar.class;
                            participant.level = fullChar.level || 1;
                            participant.stats = fullChar.stats || {};
                            participant.race = fullChar.race;
                            participant.background = fullChar.background;
                            
                            console.log(`[Combat] Loaded full data for ${participant.name}:`, {
                                class: participant.class,
                                level: participant.level
                            });
                        }
                    }
                });
            }
        } catch (error) {
            console.warn('[Combat] Error loading full character data:', error);
        }
    }

    initializeFeatureManagers() {
        console.log('[Combat] Initializing feature managers...');
        
        // Create feature managers for each player character
        this.combatState.participants.forEach(participant => {
            if (participant.type === 'character') {
                const charClass = participant.class || participant.char_class;
                
                if (!charClass) {
                    console.warn(`[Combat] Character ${participant.name} has no class, skipping feature manager`);
                    return;
                }
                
                console.log(`[Combat] Creating feature manager for ${participant.name} (${charClass})`);
                
                // Map to feature manager classes
                const managerClass = this.getFeatureManagerClass(charClass);
                
                if (managerClass) {
                    try {
                        const manager = new managerClass();
                        
                        // Initialize with level and stats
                        const level = participant.level || 1;
                        const stats = participant.stats || {
                            strength: 10,
                            dexterity: 10,
                            constitution: 10,
                            intelligence: 10,
                            wisdom: 10,
                            charisma: 10
                        };
                        
                        manager.initialize(level, stats);
                        
                        // Set character name if method exists (optional)
                        if (typeof manager.setCharacterName === 'function') {
                            manager.setCharacterName(participant.name);
                        } else {
                            // Manually set the name property
                            manager.characterName = participant.name;
                        }
                        
                        // Store manager
                        const participantId = participant.participant_id || participant.id;
                        this.featureManagers[participantId] = manager;
                        
                        console.log(`[Combat] ✓ Feature manager initialized: ${participant.name} (${charClass})`);
                    } catch (error) {
                        console.error(`[Combat] Failed to initialize feature manager for ${participant.name}:`, error);
                    }
                } else {
                    console.warn(`[Combat] No feature manager class found for: ${charClass}`);
                }
            }
        });
        
        console.log(`[Combat] Feature managers initialized: ${Object.keys(this.featureManagers).length}`);
    }

    getFeatureManagerClass(charClass) {
        const managerMap = {
            'Barbarian': window.BarbarianFeatureManager,
            'Bard': window.BardFeatureManager,
            'Cleric': window.ClericFeatureManager,
            'Druid': window.DruidFeatureManager,
        };
        
        return managerMap[charClass] || null;
    }

    // ========================================================================
    // EVENT LISTENERS
    // ========================================================================

    setupEventListeners() {
        // Combat log toggle
        const logToggle = document.getElementById('log-toggle');
        if (logToggle) {
            logToggle.addEventListener('click', () => this.toggleCombatLog());
        }
        
        // Flee button
        const fleeBtn = document.getElementById('btn-flee');
        if (fleeBtn) {
            fleeBtn.addEventListener('click', () => this.attemptFlee());
        }
        
        // Settings button
        const settingsBtn = document.getElementById('btn-settings');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.showSettings());
        }
        
        // Combat end modal
        const continueBtn = document.getElementById('btn-continue');
        if (continueBtn) {
            continueBtn.addEventListener('click', () => this.handleCombatEnd());
        }
        
        console.log('[Combat] Event listeners attached');
    }

    // ========================================================================
    // RENDERING
    // ========================================================================

    render() {
        console.log('[Combat] Rendering combat view...');
        
        // Update round counter
        this.updateRoundDisplay();
        
        // Render battlefield (characters and enemies)
        this.battlefieldView.render(this.combatState);
        
        // Update turn indicator
        this.updateTurnIndicator();
        
        // Render action menu (if it's player's turn)
        this.updateActionMenu();
        
        console.log('[Combat] ✓ Render complete');
    }

    updateRoundDisplay() {
        const roundElement = document.getElementById('current-round');
        if (roundElement && this.combatState) {
            roundElement.textContent = this.combatState.round || 1;
        }
    }

    updateTurnIndicator() {
        const turnNameElement = document.getElementById('current-turn-name');
        
        if (!this.combatState || !this.combatState.current_turn) {
            return;
        }
        
        const currentTurn = this.combatState.current_turn;
        
        if (turnNameElement) {
            turnNameElement.textContent = currentTurn.name;
            
            // Color code based on party/enemy
            if (currentTurn.type === 'character') {
                turnNameElement.style.color = 'var(--party-color)';
            } else {
                turnNameElement.style.color = 'var(--enemy-color)';
            }
        }
        
        // Update visual indicator on combatant cards
        this.battlefieldView.updateTurnIndicator(currentTurn.participant_id)
    }

    updateActionMenu() {
        if (!this.combatState || !this.combatState.current_turn) {
            return;
        }
        
        const currentTurn = this.combatState.current_turn;
        const isPlayerTurn = currentTurn.type === 'character';
        
        if (isPlayerTurn) {
            // Show action menu for player
            this.actionMenu.show(currentTurn);
        } else {
            // Hide action menu for enemy turn
            this.actionMenu.hide();
        }
    }

    // ========================================================================
    // COMBAT FLOW
    // ========================================================================

    async startCombatFlow() {
        console.log('[Combat] Starting combat flow...');
        
        // Add initial combat log entry
        this.combatLog.addEntry('system', `Combat begins! Round ${this.combatState.round}`);
        
        // Check if it's enemy turn and auto-process
        if (this.combatState.current_turn.type !== 'character' && this.AUTO_ENEMY_TURNS) {
            await this.processEnemyTurn();
        }
    }

    async processTurn() {
        if (this.isProcessingAction) {
            console.log('[Combat] Already processing action, ignoring...');
            return;
        }
        
        const currentTurn = this.combatState.current_turn;
        
        if (currentTurn.type === 'character') {
            // Wait for player input (handled by action menu)
            console.log(`[Combat] Waiting for player input (${currentTurn.name})`);
        } else {
            // Process enemy turn automatically
            if (this.AUTO_ENEMY_TURNS) {
                await this.processEnemyTurn();
            }
        }
    }

    async processEnemyTurn() {
        console.log('[Combat] Processing enemy turn...');
        
        this.isProcessingAction = true;
        
        try {
            const currentEnemy = this.combatState.current_turn;
            
            if (!currentEnemy || !currentEnemy.participant_id) {
                throw new Error('Invalid enemy turn data');
            }
            
            // Add to combat log
            this.combatLog.addEntry('turn', `${currentEnemy.name}'s turn...`);
            
            // Wait a moment for dramatic effect
            await this.delay(1000 / this.ANIMATION_SPEED);
            
            // Request AI action from backend
            console.log('[Combat] Requesting enemy action for:', currentEnemy.participant_id);
            
            const response = await fetch(
                `${this.API_BASE}/api/combat/${this.combatId}/enemy-action`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        enemy_id: currentEnemy.participant_id || currentEnemy.id
                    })
                }
            );
            
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Display action result
            await this.displayActionResult(data);
            
            // Reload combat state
            await this.loadCombatState();
            
            // Check for combat end
            await this.checkCombatEnd();
            
            // If combat didn't end, advance turn
            if (!this.combatEnded) {
                await this.advanceTurn();
            }
            
        } catch (error) {
            console.error('[Combat] Enemy turn error:', error);
            this.combatLog.addEntry('system', `Error: ${error.message}`);
            
            // Try to advance turn anyway to prevent getting stuck
            await this.advanceTurn();
        } finally {
            this.isProcessingAction = false;
        }
    }

    async processPlayerAction(action, target) {
        console.log('[Combat] Processing player action:', action, target);
        
        const actionMenu = document.getElementById('action-menu');
        if (actionMenu) {
            actionMenu.style.opacity = '0.5';
            actionMenu.style.pointerEvents = 'none';
        }
        this.isProcessingAction = true;
        
        try {
            const currentPlayer = this.combatState.current_turn;
            
            // Get the target participant ID (handle both formats)
            const targetId = target.participant_id || target.id;
            
            console.log('[Combat] Sending action to API:', {
                character_id: currentPlayer.participant_id || currentPlayer.id,
                action_type: action.type,
                action_name: action.name,
                target_id: targetId
            });
            
            // Send action to backend
            const response = await fetch(
                `${this.API_BASE}/api/combat/${this.combatId}/player-action`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        character_id: currentPlayer.participant_id || currentPlayer.id,
                        action_type: action.type,
                        action_name: action.name,
                        target_id: targetId,
                        action_data: action.data || {}
                    })
                }
            );
            
            const data = await response.json();
            
            if (!response.ok || !data.success) {
                console.error('[Combat] Action failed:', {
                    status: response.status,
                    statusText: response.statusText,
                    error: data.error,
                    action_type: action.type,
                    action_name: action.name
                });
                
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Display action result with animations
            await this.displayActionResult(data);
            
            // Reload combat state to get updated HP/resources
            await this.loadCombatState();
            
            // Check for combat end
            await this.checkCombatEnd();
            
            // If combat didn't end, advance to next turn
            if (!this.combatEnded) {
                await this.advanceTurn();
            }
            
        } catch (error) {
            console.error('[Combat] Player action error:', error);
            this.showError('Action failed: ' + error.message);
        } finally {
            this.isProcessingAction = false;
            const actionMenu = document.getElementById('action-menu');
            if (actionMenu) {
                actionMenu.style.opacity = '1';
                actionMenu.style.pointerEvents = 'auto';
            }

        }

        this.battlefieldView.exitTargetingMode();
        this.actionMenu.resetToMainMenu();
    }


    async displayActionResult(data) {
        console.log('[Combat] Displaying action result:', data);
        
        const result = data;
        
        // Add to combat log
        this.combatLog.addEntry(
            result.hit === false ? 'miss' : (result.critical ? 'damage' : result.type || 'system'),
            result.message || 'Action performed'
        );
        
        // Get target participant ID
        const targetId = result.target;
        
        // Show animations based on result type
        if (result.hit === false) {
            // Miss
            if (targetId) {
                await this.animator.showMiss(targetId);
            }
        } else if (result.damage && result.damage > 0) {
            // Damage
            if (targetId) {
                await this.animator.showDamage(
                    targetId,
                    result.damage,
                    result.critical || false
                );
                
                // Shake the target card
                this.battlefieldView.shakeCard(targetId);
            }
        }
        
        if (result.healing && result.healing > 0) {
            // Healing
            if (targetId) {
                await this.animator.showHealing(
                    targetId,
                    result.healing
                );
            }
        }

        if (result.type === 'spell' || result.message?.includes('casts')) {
            const casterId = this.combatState.current_turn.participant_id;
            const isHealing = result.healing && result.healing > 0;
            const spellLevel = result.spell_level || 1;
            
            if (casterId && targetId) {
                await this.animator.showSpellCast(casterId, targetId, spellLevel, isHealing);
            }
        }
        
        // Show buff/debuff effects
        if (result.effect) {
            const effectTargetId = result.character || result.attacker;
            if (effectTargetId) {
                await this.animator.showEffect(
                    effectTargetId,
                    result.effect
                );
            }
        }
        
        // Update HP bars if HP changed
        if (targetId && result.new_hp !== undefined) {
            this.battlefieldView.updateCombatant(targetId, {
                hp: result.new_hp,
                max_hp: result.max_hp
            });
        }
        
        // Update resource displays if resources changed
        if (result.resource_changes) {
            const characterId = result.character || this.combatState.current_turn.participant_id;
            this.updateCharacterResources(characterId, result.resource_changes);
            
            // Update the battlefield display
            this.battlefieldView.updateCombatant(characterId, result.resource_changes);
        }
        
        // Check if target was defeated
        if (result.target_defeated && targetId) {
            this.combatLog.addEntry('system', `${result.target} has been defeated!`);
            
            // Mark as defeated on battlefield
            this.battlefieldView.updateCombatant(targetId, { 
                hp: 0, 
                is_alive: false 
            });
        }
        
        // Add a delay for visual feedback
        await this.delay(800);
    }

    async advanceTurn() {
        console.log('[Combat] Advancing to next turn...');
        
        try {
            const response = await fetch(
                `${this.API_BASE}/api/combat/${this.combatId}/advance-turn`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                }
            );
            
            const data = await response.json();
            
            if (data.success) {
                // Update combat state
                this.combatState = data.combat_state;
                
                // Check if new round started
                if (data.new_round) {
                    this.combatLog.addEntry('system', `=== Round ${this.combatState.round} ===`);
                }
                
                // Re-render
                this.render();
                
                // Continue combat flow
                await this.processTurn();
            } else {
                throw new Error(data.error || 'Failed to advance turn');
            }
        } catch (error) {
            console.error('[Combat] Turn advance error:', error);
            this.showError('Failed to advance turn: ' + error.message);
        }
    }

    // ========================================================================
    // VICTORY / DEFEAT
    // ========================================================================

    async checkCombatEnd() {
        console.log('[Combat] Checking combat end conditions...');
        
        const allEnemiesDead = this.combatState.participants
            .filter(p => p.type === 'monster')
            .every(p => p.hp <= 0);
        
        const allPlayersDead = this.combatState.participants
            .filter(p => p.type === 'character')
            .every(p => p.hp <= 0);
        
        if (allEnemiesDead) {
            await this.handleVictory();
        } else if (allPlayersDead) {
            await this.handleDefeat();
        }
    }

    async handleVictory() {
        console.log('[Combat] VICTORY!');
        
        this.combatLog.addEntry('system', '=== VICTORY! ===');
        
        // Show victory modal
        const modal = document.getElementById('combat-end-modal');
        const title = document.getElementById('combat-result-title');
        const details = document.getElementById('combat-result-details');
        
        if (modal && title && details) {
            title.textContent = '🎉 Victory!';
            title.style.color = 'var(--accent-green)';
            
            details.innerHTML = `
                <p>All enemies have been defeated!</p>
                <p>Combat lasted ${this.combatState.round} rounds.</p>
                <div style="margin-top: 20px;">
                    <strong>Survivors:</strong>
                    ${this.getSurvivorsList()}
                </div>
            `;
            
            modal.classList.remove('hidden');
        }
        
        // Mark combat as ended in backend
        await this.endCombat('victory');
    }

    async handleDefeat() {
        console.log('[Combat] DEFEAT...');
        
        this.combatLog.addEntry('system', '=== DEFEAT ===');
        
        // Show defeat modal
        const modal = document.getElementById('combat-end-modal');
        const title = document.getElementById('combat-result-title');
        const details = document.getElementById('combat-result-details');
        
        if (modal && title && details) {
            title.textContent = '💀 Defeat...';
            title.style.color = 'var(--accent-red)';
            
            details.innerHTML = `
                <p>Your party has been defeated.</p>
                <p>Combat lasted ${this.combatState.round} rounds.</p>
            `;
            
            modal.classList.remove('hidden');
        }
        
        // Mark combat as ended in backend
        await this.endCombat('defeat');
    }

    getSurvivorsList() {
        const survivors = this.combatState.participants
            .filter(p => p.type === 'character' && p.hp > 0)
            .map(p => `${p.name} (${p.hp}/${p.max_hp} HP)`)
            .join('<br>');
        
        return survivors || 'None';
    }

    async endCombat(result) {
        try {
            await fetch(
                `${this.API_BASE}/api/combat/${this.combatId}/end`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ result: result })
                }
            );
        } catch (error) {
            console.error('[Combat] Error ending combat:', error);
        }
    }

    handleCombatEnd() {
        // Redirect back to story state
        window.location.href = `${this.API_BASE}/campaign/${this.campaignName}/story-package`;
    }

    // ========================================================================
    // CHARACTER RESOURCE MANAGEMENT
    // ========================================================================

    updateCharacterResources(characterId, resourceChanges) {
        if (!resourceChanges) return;
        
        const manager = this.featureManagers[characterId];
        if (!manager) return;
        
        console.log('[Combat] Updating resources:', characterId, resourceChanges);
        
        // Update based on resource type
        if (resourceChanges.rage_used !== undefined) {
            manager.ragesUsed = resourceChanges.rage_used;
        }
        
        if (resourceChanges.spell_slots_used) {
            manager.spellSlotsUsed = resourceChanges.spell_slots_used;
        }
        
        if (resourceChanges.bardic_inspiration_remaining !== undefined) {
            manager.bardicInspirationRemaining = resourceChanges.bardic_inspiration_remaining;
        }
        
        if (resourceChanges.wild_shape_uses_remaining !== undefined) {
            manager.wildShapeUsesRemaining = resourceChanges.wild_shape_uses_remaining;
        }
        
        // Re-render the feature manager if it's visible
        if (manager.render) {
            manager.render();
        }
    }

    // ========================================================================
    // UI HELPERS
    // ========================================================================

    toggleCombatLog() {
        const logContainer = document.getElementById('combat-log-container');
        if (logContainer) {
            logContainer.classList.toggle('collapsed');
            
            const icon = document.querySelector('.toggle-icon');
            if (icon) {
                icon.textContent = logContainer.classList.contains('collapsed') ? '▲' : '▼';
            }
        }
    }

    async attemptFlee() {
        if (!confirm('Are you sure you want to flee from combat?')) {
            return;
        }
        
        console.log('[Combat] Attempting to flee...');
        
        try {
            const response = await fetch(
                `${this.API_BASE}/api/combat/${this.combatId}/flee`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                }
            );
            
            const data = await response.json();
            
            if (data.success) {
                this.combatLog.addEntry('system', 'Fled from combat!');
                
                // Wait a moment then redirect
                await this.delay(1500);
                this.handleCombatEnd();
            } else {
                this.showError(data.error || 'Failed to flee!');
            }
        } catch (error) {
            console.error('[Combat] Flee error:', error);
            this.showError('Failed to flee: ' + error.message);
        }
    }

    showSettings() {
        
        alert('Settings coming soon!\n\n- Animation speed\n- Auto-enemy turns\n- Combat log settings');
    }

    showError(message) {
        // Simple error display - could be enhanced with a modal
        this.combatLog.addEntry('system', `ERROR: ${message}`);
        
        // Also show browser alert for critical errors
        if (message.includes('Failed')) {
            alert(message);
        }
    }

    // ========================================================================
    // UTILITIES
    // ========================================================================

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // ========================================================================
    // PUBLIC API (for action menu and battlefield view)
    // ========================================================================

    onActionSelected(action) {
        console.log('[Combat] Action selected:', action);
        this.selectedAction = action;
    }

    getCurrentTurnParticipant() {
        return this.combatState ? this.combatState.current_turn : null;
    }

    getParticipants() {
        return this.combatState ? this.combatState.participants : [];
    }

    getEnemies() {
        return this.getParticipants().filter(p => p.type === 'monster' && p.hp > 0);
    }

    getAllies() {
        return this.getParticipants().filter(p => p.type === 'character' && p.hp > 0);
    }

    getFeatureManager(characterId) {
        return this.featureManagers[characterId];
    }

    /**
     * Callback when target is selected on battlefield
     */
    onTargetSelected(targetId) {
        console.log('[Combat] Target selected callback:', targetId);
        
        // Pass to action menu to complete the action
        if (this.actionMenu) {
            this.actionMenu.handleTargetSelected(targetId);
        } else {
            console.error('[Combat] Action menu not available!');
        }
    }
}

// Export for global use
window.CombatViewController = CombatViewController;