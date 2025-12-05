/**
 * CombatLog.js
 * Combat message logging and display system
 * 
 * Features:
 * - Chronological message display
 * - Color-coded message types
 * - Auto-scroll to latest messages
 * - Collapsible panel
 * - Message filtering (optional)
 * - Damage rolls and bonuses display
 */

class CombatLog {
    constructor() {
        // DOM Elements
        this.logContainer = document.getElementById('combat-log');
        this.logHeader = document.getElementById('log-toggle');
        this.logWrapper = document.getElementById('combat-log-container');
        
        // State
        this.messages = [];
        this.maxMessages = 100; // Keep last 100 messages
        this.isCollapsed = true;
        this.autoScroll = true;
        
        // Message type colors
        this.messageColors = {
            'damage': '#ff6b6b',      // Red - damage dealt
            'healing': '#51cf66',     // Green - healing
            'buff': '#4dabf7',        // Blue - buffs/positive effects
            'debuff': '#ffa94d',      // Orange - debuffs/negative effects
            'miss': '#adb5bd',        // Gray - misses
            'system': '#ffd93d',      // Yellow - system messages
            'turn': '#a78bfa',        // Purple - turn changes
            'round': '#f59f00',       // Amber - round changes
            'info': '#e9ecef'         // Light gray - general info
        };
        
        console.log('[CombatLog] Initialized');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Initial collapsed state
        if (this.logWrapper) {
            this.logWrapper.classList.add('collapsed');
        }
    }
    
    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    setupEventListeners() {
        // Toggle log visibility
        if (this.logHeader) {
            this.logHeader.addEventListener('click', () => this.toggle());
        }
        
        console.log('[CombatLog] Event listeners attached');
    }
    
    // ========================================================================
    // MESSAGE MANAGEMENT
    // ========================================================================
    
    /**
     * Add a message to the combat log
     * 
     * @param {string} type - Message type (damage, healing, system, etc.)
     * @param {string} message - Message text
     * @param {object} data - Optional additional data (rolls, bonuses, etc.)
     */
    addEntry(type, message, data = {}) {
        console.log('[CombatLog] Adding entry:', type, message);
        
        const timestamp = this.getTimestamp();
        
        const entry = {
            type: type,
            message: message,
            data: data,
            timestamp: timestamp
        };
        
        this.messages.push(entry);
        
        // Limit message history
        if (this.messages.length > this.maxMessages) {
            this.messages.shift();
        }
        
        // Render the new message
        this.renderMessage(entry);
        
        // Auto-scroll to bottom
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }
    
    /**
     * Add multiple entries at once
     */
    addEntries(entries) {
        entries.forEach(entry => {
            this.addEntry(entry.type, entry.message, entry.data);
        });
    }
    
    /**
     * Clear all messages
     */
    clear() {
        console.log('[CombatLog] Clearing log');
        this.messages = [];
        if (this.logContainer) {
            this.logContainer.innerHTML = '';
        }
    }
    
    // ========================================================================
    // SPECIALIZED MESSAGE METHODS
    // ========================================================================
    
    /**
     * Log an attack
     */
    logAttack(attacker, target, result) {
        const { hit, damage, critical, attackRoll, attackBonus, ac } = result;
        
        if (hit) {
            const critText = critical ? ' CRITICAL HIT!' : '';
            const message = `${attacker} attacks ${target}${critText}`;
            
            this.addEntry(critical ? 'damage' : 'damage', message, {
                attackRoll: attackRoll,
                attackBonus: attackBonus,
                totalAttack: attackRoll + attackBonus,
                targetAC: ac,
                damage: damage
            });
            
            if (damage > 0) {
                this.addEntry('damage', `  → ${damage} damage!`);
            }
        } else {
            const message = `${attacker} attacks ${target}... MISS!`;
            this.addEntry('miss', message, {
                attackRoll: attackRoll,
                attackBonus: attackBonus,
                totalAttack: attackRoll + attackBonus,
                targetAC: ac
            });
        }
    }
    
    /**
     * Log healing
     */
    logHealing(healer, target, amount, spell = null) {
        const spellText = spell ? ` using ${spell}` : '';
        const message = `${healer} heals ${target}${spellText} for ${amount} HP`;
        this.addEntry('healing', message, { healing: amount });
    }
    
    /**
     * Log a buff/debuff application
     */
    logEffect(caster, target, effect, isBuff = true) {
        const type = isBuff ? 'buff' : 'debuff';
        const message = `${caster} applies ${effect} to ${target}`;
        this.addEntry(type, message, { effect: effect });
    }
    
    /**
     * Log a skill use
     */
    logSkill(user, skillName, target = null) {
        const targetText = target ? ` on ${target}` : '';
        const message = `${user} uses ${skillName}${targetText}`;
        this.addEntry('system', message, { skill: skillName });
    }
    
    /**
     * Log a spell cast
     */
    logSpell(caster, spellName, level, target = null) {
        const targetText = target ? ` targeting ${target}` : '';
        const message = `${caster} casts ${spellName} (Level ${level})${targetText}`;
        this.addEntry('system', message, { spell: spellName, level: level });
    }
    
    /**
     * Log turn change
     */
    logTurnChange(characterName) {
        const message = `─── ${characterName}'s Turn ───`;
        this.addEntry('turn', message);
    }
    
    /**
     * Log round change
     */
    logRoundChange(roundNumber) {
        const message = `═══ ROUND ${roundNumber} ═══`;
        this.addEntry('round', message);
    }
    
    /**
     * Log a character defeat
     */
    logDefeat(characterName) {
        const message = `💀 ${characterName} has been defeated!`;
        this.addEntry('system', message, { defeated: true });
    }
    
    /**
     * Log victory
     */
    logVictory() {
        const message = `🎉 VICTORY! All enemies defeated!`;
        this.addEntry('system', message, { victory: true });
    }
    
    /**
     * Log defeat
     */
    logPartyDefeat() {
        const message = `💀 DEFEAT... Your party has fallen.`;
        this.addEntry('system', message, { defeat: true });
    }
    
    /**
     * Log flee attempt
     */
    logFlee(success) {
        const message = success 
            ? `🏃 Your party fled from combat!`
            : `Failed to flee!`;
        this.addEntry('system', message, { fled: success });
    }
    
    // ========================================================================
    // RENDERING
    // ========================================================================
    
    /**
     * Render a message entry
     */
    renderMessage(entry) {
        if (!this.logContainer) {
            console.warn('[CombatLog] Log container not found');
            return;
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = `log-entry ${entry.type}`;
        
        // Build message content
        let content = `<span class="log-timestamp">[${entry.timestamp}]</span> `;
        content += `<span class="log-message">${this.escapeHtml(entry.message)}</span>`;
        
        // Add roll details if available
        if (entry.data.attackRoll !== undefined) {
            content += this.renderAttackDetails(entry.data);
        }
        
        messageElement.innerHTML = content;
        
        // Apply color
        const color = this.messageColors[entry.type] || this.messageColors['info'];
        messageElement.style.borderLeftColor = color;
        
        // Add to container
        this.logContainer.appendChild(messageElement);
        
        // Animate entry
        requestAnimationFrame(() => {
            messageElement.classList.add('visible');
        });
    }
    
    /**
     * Render attack roll details
     */
    renderAttackDetails(data) {
        const { attackRoll, attackBonus, totalAttack, targetAC, damage } = data;
        
        let details = '<div class="log-details">';
        
        if (attackRoll !== undefined) {
            details += `  d20: ${attackRoll}`;
            if (attackBonus) {
                details += ` + ${attackBonus}`;
            }
            details += ` = ${totalAttack}`;
            if (targetAC !== undefined) {
                details += ` vs AC ${targetAC}`;
            }
        }
        
        details += '</div>';
        return details;
    }
    
    /**
     * Render all messages (full refresh)
     */
    renderAll() {
        if (!this.logContainer) return;
        
        this.logContainer.innerHTML = '';
        
        this.messages.forEach(entry => {
            this.renderMessage(entry);
        });
        
        if (this.autoScroll) {
            this.scrollToBottom();
        }
    }
    
    // ========================================================================
    // UI CONTROLS
    // ========================================================================
    
    /**
     * Toggle log visibility
     */
    toggle() {
        this.isCollapsed = !this.isCollapsed;
        
        if (this.logWrapper) {
            if (this.isCollapsed) {
                this.logWrapper.classList.add('collapsed');
            } else {
                this.logWrapper.classList.remove('collapsed');
                this.scrollToBottom();
            }
        }
        
        // Update toggle icon
        const toggleIcon = this.logHeader.querySelector('.toggle-icon');
        if (toggleIcon) {
            toggleIcon.textContent = this.isCollapsed ? '▲' : '▼';
        }
        
        console.log('[CombatLog] Toggled:', this.isCollapsed ? 'collapsed' : 'expanded');
    }
    
    /**
     * Expand the log
     */
    expand() {
        if (this.isCollapsed) {
            this.toggle();
        }
    }
    
    /**
     * Collapse the log
     */
    collapse() {
        if (!this.isCollapsed) {
            this.toggle();
        }
    }
    
    /**
     * Scroll to bottom of log
     */
    scrollToBottom() {
        if (this.logContainer) {
            this.logContainer.scrollTop = this.logContainer.scrollHeight;
        }
    }
    
    /**
     * Enable/disable auto-scroll
     */
    setAutoScroll(enabled) {
        this.autoScroll = enabled;
        console.log('[CombatLog] Auto-scroll:', enabled);
    }
    
    // ========================================================================
    // UTILITIES
    // ========================================================================
    
    /**
     * Get current timestamp
     */
    getTimestamp() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Export log as text
     */
    exportLog() {
        let text = '=== COMBAT LOG ===\n\n';
        
        this.messages.forEach(entry => {
            text += `[${entry.timestamp}] ${entry.message}\n`;
        });
        
        return text;
    }
    
    /**
     * Download log as file
     */
    downloadLog(filename = 'combat_log.txt') {
        const text = this.exportLog();
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        
        URL.revokeObjectURL(url);
        
        console.log('[CombatLog] Downloaded log');
    }
}

// Export for global use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CombatLog;
}