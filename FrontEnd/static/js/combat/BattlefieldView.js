/**
 * BattlefieldView.js
 * Renders and manages the combat battlefield display
 * Shows party members, enemies, HP bars, status effects, and turn indicators
 */

class BattlefieldView {
    constructor(combatController) {
        this.combatController = combatController;
        
        // DOM elements
        this.partyArea = document.getElementById('party-area');
        this.enemyArea = document.getElementById('enemy-area');
        this.roundDisplay = document.getElementById('round-number');
        this.encounterName = document.getElementById('encounter-name');
        
        // State
        this.combatantElements = new Map(); // participant_id -> DOM element
        this.selectedTargetId = null;
        this.targetingMode = false;
        this.validTargets = [];
        
        console.log('[BattlefieldView] Initialized');
    }
    
    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    /**
     * Render the initial battlefield state
     */
    render(combatState) {
        console.log('[BattlefieldView] Rendering battlefield', combatState);
        
        // Update header info
        this.updateHeader(combatState);
        
        // Clear existing content
        this.partyArea.innerHTML = '';
        this.enemyArea.innerHTML = '';
        this.combatantElements.clear();
        
        // Separate participants into party and enemies
        const party = combatState.participants.filter(p => p.type === 'character');
        const enemies = combatState.participants.filter(p => p.type === 'monster');
        
        // Render party members
        party.forEach(participant => {
            const card = this.createCombatantCard(participant, 'party');
            this.partyArea.appendChild(card);
            
            const participantId = participant.participant_id || participant.id
            this.combatantElements.set(participant.participant_id, card);
        });
        
        // Render enemies
        enemies.forEach(participant => {
            const card = this.createCombatantCard(participant, 'enemy');
            this.enemyArea.appendChild(card);
            this.combatantElements.set(participant.participant_id, card);
        });
        
        // Highlight current turn
        this.updateTurnIndicator(combatState.current_turn.participant_id);
    }
    
    /**
     * Update header information (encounter name, round)
     */
    updateHeader(combatState) {
        if (this.encounterName) {
            this.encounterName.textContent = combatState.encounter_name || 'Combat Encounter';
        }
        
        if (this.roundDisplay) {
            this.roundDisplay.textContent = combatState.round || 1;
        }
    }
    
    // ========================================================================
    // COMBATANT CARD CREATION
    // ========================================================================
    
    /**
     * Create a combatant card element
     */
    createCombatantCard(participant, side) {
        const card = document.createElement('div');
        card.className = `combatant-card ${side}`;

        const participantId = participant.participant_id || participant.id;
        card.dataset.participantId = participantId;
        card.dataset.participantType = participant.type;
        
        // Add defeated class if HP is 0
        if (participant.hp <= 0 || !participant.is_alive) {
            card.classList.add('defeated');
        }
        
        // Build card HTML
        card.innerHTML = `
            <div class="combatant-portrait">
                ${this.getPortraitContent(participant)}
            </div>
            
            <div class="combatant-info">
                <div class="combatant-header">
                    <span class="combatant-name">${participant.name}</span>
                    ${participant.type === 'character' ? `<span class="combatant-level">Lv ${participant.level}</span>` : ''}
                </div>
                
                <div class="combatant-stats">
                    <!-- HP Bar -->
                    <div class="stat-bar health-bar-container">
                        <label>HP</label>
                        <div class="health-bar">
                            <div class="health-bar-fill" style="width: ${this.getHPPercentage(participant)}%">
                                <span class="health-bar-text">${participant.hp} / ${participant.max_hp}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- MP/Resource Bar (if applicable) -->
                    ${this.createResourceBar(participant)}
                    
                    <!-- AC Badge -->
                    <div class="ac-badge" title="Armor Class">
                        <span class="ac-label">AC</span>
                        <span class="ac-value">${participant.ac || 10}</span>
                    </div>
                </div>
                
                <!-- Status Effects -->
                <div class="status-effects">
                    ${this.createStatusEffects(participant)}
                </div>
                
                <!-- Turn Indicator -->
                <div class="turn-indicator" style="display: none;">
                    <span class="turn-arrow">▶</span> YOUR TURN
                </div>
            </div>
        `;
        
        // Add click handler for targeting
        card.addEventListener('click', (e) => this.handleCardClick(participant.participant_id, e));
        
        return card;
    }
    
    /**
     * Get portrait content (icon or image)
     */
    getPortraitContent(participant) {
        // For now, use emoji/text icons
        // Later you can replace with actual images
        
        if (participant.type === 'character') {
            const classIcons = {
                'Barbarian': '⚔️',
                'Bard': '🎵',
                'Cleric': '✨',
                'Druid': '🌿',
                'Fighter': '🛡️',
                'Wizard': '🔮'
            };
            
            const icon = classIcons[participant.class] || '👤';
            return `<span class="portrait-icon">${icon}</span>`;
        } else {
            // Enemy icons
            const monsterIcons = {
                'goblin': '👹',
                'orc': '👺',
                'dragon': '🐉',
                'skeleton': '💀',
                'wolf': '🐺',
                'spider': '🕷️'
            };
            
            // Try to match monster type
            const monsterType = Object.keys(monsterIcons).find(key => 
                participant.name.toLowerCase().includes(key)
            );
            
            const icon = monsterIcons[monsterType] || '👿';
            return `<span class="portrait-icon enemy-icon">${icon}</span>`;
        }
    }
    
    /**
     * Create resource bar (spell slots, rage, etc.)
     */
    createResourceBar(participant) {
        if (participant.type !== 'character') {
            return ''; // Enemies don't have resource bars
        }
        
        // Check for spell slots
        if (participant.spell_slots) {
            const totalSlots = Object.values(participant.spell_slots.max || {}).reduce((a, b) => a + b, 0);
            const usedSlots = Object.values(participant.spell_slots.used || {}).reduce((a, b) => a + b, 0);
            const remainingSlots = totalSlots - usedSlots;
            const percentage = totalSlots > 0 ? (remainingSlots / totalSlots * 100) : 0;
            
            return `
                <div class="stat-bar mp-bar-container">
                    <label>Spell Slots</label>
                    <div class="mp-bar">
                        <div class="mp-bar-fill" style="width: ${percentage}%">
                            <span class="mp-bar-text">${remainingSlots} / ${totalSlots}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Check for rage (Barbarian)
        if (participant.rage) {
            const percentage = participant.rage.uses_remaining > 0 ? 100 : 0;
            return `
                <div class="stat-bar mp-bar-container">
                    <label>Rage</label>
                    <div class="mp-bar rage-bar">
                        <div class="mp-bar-fill" style="width: ${percentage}%">
                            <span class="mp-bar-text">${participant.rage.uses_remaining} uses</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        return '';
    }
    
    /**
     * Create status effect badges
     */
    createStatusEffects(participant) {
        const effects = [];
        
        // Rage
        if (participant.rage && participant.rage.active) {
            effects.push('<span class="status-badge rage" title="Raging">🔥 RAGE</span>');
        }
        
        // Wild Shape
        if (participant.wild_shape && participant.wild_shape.active) {
            effects.push(`<span class="status-badge wild-shape" title="Wild Shape: ${participant.wild_shape.beast}">🐾 ${participant.wild_shape.beast}</span>`);
        }
        
        // Bardic Inspiration (if we track who has it)
        if (participant.conditions && participant.conditions.includes('inspired')) {
            effects.push('<span class="status-badge inspiration" title="Inspired">🎵</span>');
        }
        
        // Defending
        if (participant.conditions && participant.conditions.includes('defending')) {
            effects.push('<span class="status-badge defending" title="Defending (+2 AC)">🛡️</span>');
        }
        
        // Defeated
        if (participant.hp <= 0 || !participant.is_alive) {
            effects.push('<span class="status-badge defeated-badge" title="Defeated">💀 DEFEATED</span>');
        }
        
        return effects.join('');
    }
    
    // ========================================================================
    // UPDATE METHODS
    // ========================================================================
    
    /**
     * Update a specific combatant's display
     */
    updateCombatant(participantId, data) {
        const card = this.combatantElements.get(participantId);
        if (!card) {
            console.warn(`[BattlefieldView] Card not found for ${participantId}`);
            return;
        }
        
        // Update HP if provided
        if (data.hp !== undefined || data.max_hp !== undefined) {
            this.updateHealthBar(participantId, data.hp, data.max_hp);
        }
        
        // Update status effects
        if (data.conditions !== undefined || data.rage !== undefined || data.wild_shape !== undefined) {
            const statusContainer = card.querySelector('.status-effects');
            if (statusContainer) {
                // Get current participant data and merge updates
                const combatState = this.combatController.combatState;
                const participant = combatState.participants.find(p => p.participant_id === participantId);
                if (participant) {
                    const updatedParticipant = { ...participant, ...data };
                    statusContainer.innerHTML = this.createStatusEffects(updatedParticipant);
                }
            }
        }
        
        // Update resource bars
        if (data.spell_slots !== undefined || data.rage !== undefined) {
            const combatState = this.combatController.combatState;
            const participant = combatState.participants.find(p => p.participant_id === participantId);
            if (participant) {
                const updatedParticipant = { ...participant, ...data };
                const resourceContainer = card.querySelector('.mp-bar-container');
                if (resourceContainer) {
                    const newResourceBar = this.createResourceBar(updatedParticipant);
                    if (newResourceBar) {
                        resourceContainer.outerHTML = newResourceBar;
                    }
                }
            }
        }
        
        // Mark as defeated if HP is 0
        if (data.hp === 0 || data.is_alive === false) {
            card.classList.add('defeated');
        }
    }
    
    /**
     * Update health bar for a combatant
     */
    updateHealthBar(participantId, newHp, maxHp) {
        const card = this.combatantElements.get(participantId);
        if (!card) return;
        
        const healthBarFill = card.querySelector('.health-bar-fill');
        const healthBarText = card.querySelector('.health-bar-text');
        
        if (healthBarFill && healthBarText) {
            const percentage = maxHp > 0 ? (newHp / maxHp * 100) : 0;
            
            // Animate the change
            healthBarFill.style.transition = 'width 0.5s ease-out';
            healthBarFill.style.width = `${percentage}%`;
            healthBarText.textContent = `${newHp} / ${maxHp}`;
            
            // Change color based on HP percentage
            healthBarFill.classList.remove('low', 'critical');
            if (percentage <= 25) {
                healthBarFill.classList.add('critical');
            } else if (percentage <= 50) {
                healthBarFill.classList.add('low');
            }
        }
    }
    
    /**
     * Update turn indicator
     */
    updateTurnIndicator(currentTurnParticipantId) {
        // Hide all turn indicators
        document.querySelectorAll('.turn-indicator').forEach(indicator => {
            indicator.style.display = 'none';
        });
        
        // Remove active class from all cards
        document.querySelectorAll('.combatant-card').forEach(card => {
            card.classList.remove('active-turn');
        });
        
        // Show indicator for current turn
        const card = this.combatantElements.get(currentTurnParticipantId);
        if (card) {
            const indicator = card.querySelector('.turn-indicator');
            if (indicator) {
                indicator.style.display = 'flex';
            }
            card.classList.add('active-turn');
            
            // Scroll into view if needed
            card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    /**
     * Update round number
     */
    updateRound(roundNumber) {
        if (this.roundDisplay) {
            this.roundDisplay.textContent = roundNumber;
            
            // Add a pulse animation
            this.roundDisplay.style.animation = 'none';
            setTimeout(() => {
                this.roundDisplay.style.animation = 'pulse 0.5s ease-out';
            }, 10);
        }
    }
    
    // ========================================================================
    // TARGETING SYSTEM
    // ========================================================================
    
    /**
     * Enter targeting mode
     */
    enterTargetingMode(validTargetIds, targetType = 'enemy') {
        console.log('[BattlefieldView] Entering targeting mode', validTargetIds);
        
        this.targetingMode = true;
        this.validTargets = validTargetIds;
        this.selectedTargetId = null;
        
        // Highlight valid targets
        this.combatantElements.forEach((card, participantId) => {
            if (validTargetIds.includes(participantId)) {
                card.classList.add('targetable');
                card.style.cursor = 'pointer';
            } else {
                card.classList.add('not-targetable');
                card.style.cursor = 'not-allowed';
            }
        });
        
        // Show targeting hint
        this.showTargetingHint(targetType);
    }
    
    /**
     * Exit targeting mode
     */
    exitTargetingMode() {
        console.log('[BattlefieldView] Exiting targeting mode');
        
        this.targetingMode = false;
        this.validTargets = [];
        this.selectedTargetId = null;
        
        // Remove targeting classes
        this.combatantElements.forEach(card => {
            card.classList.remove('targetable', 'not-targetable', 'target-selected');
            card.style.cursor = '';
        });
        
        // Hide targeting hint
        this.hideTargetingHint();
    }
    
    /**
     * Handle card click (for targeting)
     */
    handleCardClick(participantId, event) {
        if (!this.targetingMode) return;
        
        // Check if this is a valid target
        if (!this.validTargets.includes(participantId)) {
            console.log('[BattlefieldView] Invalid target clicked');
            return;
        }
        
        // Select this target
        this.selectedTargetId = participantId;
        
        // Update visual feedback
        this.combatantElements.forEach(card => {
            card.classList.remove('target-selected');
        });
        
        const card = this.combatantElements.get(participantId);
        if (card) {
            card.classList.add('target-selected');
        }
        
        console.log('[BattlefieldView] Target selected:', participantId);
        
        // Notify controller
        if (this.combatController.onTargetSelected) {
            this.combatController.onTargetSelected(participantId);
        }
    }
    
    /**
     * Show targeting hint message
     */
    showTargetingHint(targetType) {
        const hint = document.createElement('div');
        hint.id = 'targeting-hint';
        hint.className = 'targeting-hint';
        hint.innerHTML = `
            <span class="hint-icon">🎯</span>
            <span class="hint-text">Select a ${targetType === 'ally' ? 'party member' : 'target'}</span>
        `;
        
        const container = document.querySelector('#combat-container');
        if (container) {
            container.appendChild(hint);
        } else {
            console.warn('[BattlefieldView] Combat container not found for targeting hint');
            document.body.appendChild(hint);
        }    
    }
    
    /**
     * Hide targeting hint
     */
    hideTargetingHint() {
        const hint = document.getElementById('targeting-hint');
        if (hint) {
            hint.remove();
        }
    }
    
    // ========================================================================
    // ANIMATIONS
    // ========================================================================
    
    /**
     * Show damage number animation
     */
    showDamage(participantId, amount, isCritical = false) {
        const card = this.combatantElements.get(participantId);
        if (!card) return;
        
        const damageNumber = document.createElement('div');
        damageNumber.className = `damage-number ${isCritical ? 'critical' : ''}`;
        damageNumber.textContent = `-${amount}`;
        
        // Position at center of card
        const rect = card.getBoundingClientRect();
        damageNumber.style.left = `${rect.left + rect.width / 2}px`;
        damageNumber.style.top = `${rect.top + rect.height / 2}px`;
        
        document.body.appendChild(damageNumber);
        
        // Remove after animation
        setTimeout(() => {
            damageNumber.remove();
        }, 1000);
    }
    
    /**
     * Show healing number animation
     */
    showHealing(participantId, amount) {
        const card = this.combatantElements.get(participantId);
        if (!card) return;
        
        const healingNumber = document.createElement('div');
        healingNumber.className = 'healing-number';
        healingNumber.textContent = `+${amount}`;
        
        // Position at center of card
        const rect = card.getBoundingClientRect();
        healingNumber.style.left = `${rect.left + rect.width / 2}px`;
        healingNumber.style.top = `${rect.top + rect.height / 2}px`;
        
        document.body.appendChild(healingNumber);
        
        // Remove after animation
        setTimeout(() => {
            healingNumber.remove();
        }, 1000);
    }
    
    /**
     * Show miss animation
     */
    showMiss(participantId) {
        const card = this.combatantElements.get(participantId);
        if (!card) return;
        
        const missText = document.createElement('div');
        missText.className = 'miss-text';
        missText.textContent = 'MISS!';
        
        // Position at center of card
        const rect = card.getBoundingClientRect();
        missText.style.left = `${rect.left + rect.width / 2}px`;
        missText.style.top = `${rect.top + rect.height / 2}px`;
        
        document.body.appendChild(missText);
        
        // Remove after animation
        setTimeout(() => {
            missText.remove();
        }, 1000);
    }
    
    /**
     * Play buff/debuff animation
     */
    showEffect(participantId, effectType) {
        const card = this.combatantElements.get(participantId);
        if (!card) return;
        
        const effectIcons = {
            'rage': '🔥',
            'inspiration': '🎵',
            'heal': '✨',
            'buff': '⬆️',
            'debuff': '⬇️',
            'wild_shape': '🐾'
        };
        
        const icon = effectIcons[effectType] || '✨';
        
        const effectElement = document.createElement('div');
        effectElement.className = `effect-animation ${effectType}`;
        effectElement.textContent = icon;
        
        // Position at center of card
        const rect = card.getBoundingClientRect();
        effectElement.style.left = `${rect.left + rect.width / 2}px`;
        effectElement.style.top = `${rect.top + rect.height / 2}px`;
        
        document.body.appendChild(effectElement);
        
        // Remove after animation
        setTimeout(() => {
            effectElement.remove();
        }, 1500);
    }
    
    /**
     * Shake card (for taking damage)
     */
    shakeCard(participantId) {
        const card = this.combatantElements.get(participantId);
        if (!card) return;
        
        card.classList.add('shake');
        setTimeout(() => {
            card.classList.remove('shake');
        }, 500);
    }
    
    // ========================================================================
    // HELPER METHODS
    // ========================================================================
    
    /**
     * Get HP percentage
     */
    getHPPercentage(participant) {
        if (!participant.max_hp || participant.max_hp === 0) return 0;
        return Math.max(0, Math.min(100, (participant.hp / participant.max_hp) * 100));
    }
    
    /**
     * Get combatant card element
     */
    getCombatantCard(participantId) {
        return this.combatantElements.get(participantId);
    }
    
    /**
     * Check if participant is defeated
     */
    isDefeated(participantId) {
        const card = this.combatantElements.get(participantId);
        return card ? card.classList.contains('defeated') : false;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BattlefieldView;
}