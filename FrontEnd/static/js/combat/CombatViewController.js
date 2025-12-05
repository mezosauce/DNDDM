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
            
            // Setup event listeners
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
        
        // Initialize class feature managers for player characters
        this.initializeFeatureManagers();
    }

    initializeFeatureManagers() {
        // Create feature managers for each player character
        this.combatState.participants.forEach(participant => {
            if (participant.type === 'character') {
                const charClass = participant.class || 'Character';
                
                // Map to feature manager classes
                const managerClass = this.getFeatureManagerClass(charClass);
                
                if (managerClass) {
                    const manager = new managerClass();
                    manager.initialize(participant.level, participant.stats);
                    manager.setCharacterName(participant.name);
                    
                    this.featureManagers[participant.id] = manager;
                    
                    console.log(`[Combat] ✓ Feature manager initialized: ${participant.name} (${charClass})`);
                }
            }
        });
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
        this.battlefieldView.highlightCurrentTurn(currentTurn.name);
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
            
            // Add to combat log
            this.combatLog.addEntry('system', `${currentEnemy.name}'s turn...`);
            
            // Wait a moment for dramatic effect
            await this.delay(1000 / this.ANIMATION_SPEED);
            
            // Request AI action from backend
            const response = await fetch(
                `${this.API_BASE}/api/combat/${this.combatId}/enemy-action`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        enemy_id: currentEnemy.id
                    })
                }
            );
            
            const data = await response.json();
            
            if (data.success) {
                // Display action result
                await this.displayActionResult(data.result);
                
                // Advance to next turn
                await this.advanceTurn();
            } else {
                throw new Error(data.error || 'Enemy action failed');
            }
        } catch (error) {
            console.error('[Combat] Enemy turn error:', error);
            this.combatLog.addEntry('system', `Error: ${error.message}`);
            
            // Try to advance turn anyway
            await this.advanceTurn();
        } finally {
            this.isProcessingAction = false;
        }
    }

    async processPlayerAction(action, target = null) {
        console.log('[Combat] Processing player action:', action, target);
        
        this.isProcessingAction = true;
        
        try {
            const currentPlayer = this.combatState.current_turn;
            
            // Send action to backend
            const response = await fetch(
                `${this.API_BASE}/api/combat/${this.combatId}/player-action`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        character_id: currentPlayer.id,
                        action_type: action.type,
                        action_name: action.name,
                        target_id: target ? target.id : null,
                        action_data: action.data || {}
                    })
                }
            );
            
            const data = await response.json();
            
            if (data.success) {
                // Display action result with animations
                await this.displayActionResult(data.result);
                
                // Update character resources if needed
                this.updateCharacterResources(currentPlayer.id, data.resource_changes);
                
                // Advance to next turn
                await this.advanceTurn();
            } else {
                throw new Error(data.error || 'Action failed');
            }
        } catch (error) {
            console.error('[Combat] Player action error:', error);
            this.showError('Action failed: ' + error.message);
        } finally {
            this.isProcessingAction = false;
            this.actionMenu.resetToMainMenu();
        }
    }

    async displayActionResult(result) {
        console.log('[Combat] Displaying action result:', result);
        
        // Add to combat log
        this.combatLog.addEntry(result.type || 'damage', result.message);
        
        // Show animations
        if (result.damage) {
            await this.animator.showDamage(
                result.target,
                result.damage,
                result.critical || false
            );
        }
        
        if (result.healing) {
            await this.animator.showHealing(
                result.target,
                result.healing
            );
        }
        
        // Update HP bars
        if (result.target && result.new_hp !== undefined) {
            this.battlefieldView.updateParticipantHP(
                result.target,
                result.new_hp,
                result.max_hp
            );
        }
        
        // Check if target died
        if (result.target_defeated) {
            this.combatLog.addEntry('system', `${result.target} has been defeated!`);
            this.battlefieldView.markAsDead(result.target);
            
            // Check for combat end
            await this.checkCombatEnd();
        }
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
        // TODO: Implement settings modal
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

    onTargetSelected(target) {
        console.log('[Combat] Target selected:', target);
        this.selectedTarget = target;
        
        // Execute the action
        if (this.selectedAction && this.selectedTarget) {
            this.processPlayerAction(this.selectedAction, this.selectedTarget);
        }
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
}

// Export for global use
window.CombatViewController = CombatViewController;