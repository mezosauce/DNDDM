/**
 * Wizard Class Features UI
 * Handles Wizard-specific displays: Spell Slots, Spellcasting, Arcane Recovery, Feature Tree
 */

class WizardFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Wizard');
        this.cantripsKnown = 3;
        this.spellbook = [];
        this.preparedSpells = [];
        this.stats = { strength: 10, dexterity: 10, constitution: 10, intelligence: 16, wisdom: 12, charisma: 10 };
        
        // Spell slots by level (max available)
        this.spellSlots = {
            1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0
        };
        
        // Spell slots used
        this.spellSlotsUsed = {
            1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0
        };
        
        this.arcaneRecoveryAvailable = true;
        this.arcaneRecoveryMax = 1; // Max spell slot levels recoverable
    }

    initialize(level, stats, subclass = '') {
        this.level = level;
        this.stats = stats || this.stats;
        this.subclass = subclass;
        this.updateSpellProgression();
        this.initializeSpellbook();
        this.render();
    }

    updateSpellProgression() {
        // Cantrips progression
        if (this.level >= 10) this.cantripsKnown = 5;
        else if (this.level >= 4) this.cantripsKnown = 4;
        else this.cantripsKnown = 3;

        // Spell slots progression based on Wizard table
        this.spellSlots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0};
        
        if (this.level >= 1) this.spellSlots[1] = 2;
        if (this.level >= 2) this.spellSlots[1] = 3;
        if (this.level >= 3) {
            this.spellSlots[1] = 4;
            this.spellSlots[2] = 2;
        }
        if (this.level >= 4) this.spellSlots[2] = 3;
        if (this.level >= 5) this.spellSlots[3] = 2;
        if (this.level >= 6) this.spellSlots[3] = 3;
        if (this.level >= 7) this.spellSlots[4] = 1;
        if (this.level >= 8) this.spellSlots[4] = 2;
        if (this.level >= 9) {
            this.spellSlots[4] = 3;
            this.spellSlots[5] = 1;
        }
        if (this.level >= 10) this.spellSlots[5] = 2;
        if (this.level >= 11) this.spellSlots[6] = 1;
        if (this.level >= 13) this.spellSlots[7] = 1;
        if (this.level >= 15) this.spellSlots[8] = 1;
        if (this.level >= 17) this.spellSlots[9] = 1;
        if (this.level >= 19) this.spellSlots[7] = 2;
        if (this.level >= 20) this.spellSlots[7] = 2;

        // Arcane Recovery - can recover up to half wizard level (rounded up)
        this.arcaneRecoveryMax = Math.ceil(this.level / 2);
    }

    initializeSpellbook() {
        // Initialize with 6 starting spells if empty
        if (this.spellbook.length === 0) {
            this.spellbook = [
                'Magic Missile', 'Shield', 'Mage Armor',
                'Detect Magic', 'Identify', 'Sleep'
            ];
        }
    }

    calculateSpellSaveDC() {
        const profBonus = this.getProficiencyBonus();
        const intMod = calculateModifier(this.stats.intelligence);
        return 8 + profBonus + intMod;
    }

    calculateSpellAttackBonus() {
        const profBonus = this.getProficiencyBonus();
        const intMod = calculateModifier(this.stats.intelligence);
        return profBonus + intMod;
    }

    getMaxPreparedSpells() {
        const intMod = calculateModifier(this.stats.intelligence);
        return Math.max(1, intMod + this.level);
    }

    render() {
        const container = document.getElementById('wizard-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    📚 Wizard Features
                </div>
                
                ${this.renderSpellcastingInfo()}
                ${this.renderSpellSlots()}
                ${this.renderArcaneRecovery()}
                ${this.renderSpellManagement()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderSpellcastingInfo() {
        const spellSaveDC = this.calculateSpellSaveDC();
        const spellAttack = this.calculateSpellAttackBonus();
        const maxPrepared = this.getMaxPreparedSpells();
        const intMod = calculateModifier(this.stats.intelligence);
        const profBonus = this.getProficiencyBonus();

        return `
            <div class="calculation-display">
                <div class="ability-card-name">✨ Spellcasting</div>
                <div class="calculation-formula">
                    <strong>Spell Save DC:</strong> 8 + Prof (${profBonus}) + INT (${formatModifier(intMod)}) = <strong>${spellSaveDC}</strong><br>
                    <strong>Spell Attack:</strong> Prof (${profBonus}) + INT (${formatModifier(intMod)}) = <strong>${formatModifier(spellAttack)}</strong><br>
                    <strong>Cantrips Known:</strong> ${this.cantripsKnown}<br>
                    <strong>Spells Prepared:</strong> ${this.preparedSpells.length}/${maxPrepared}
                </div>
            </div>
        `;
    }

    renderSpellSlots() {
        let html = `
            <div class="resource-tracker">
                <div class="resource-name">
                    🔮 Spell Slots
                </div>
        `;

        // Render each spell level with available slots
        for (let level = 1; level <= 9; level++) {
            const max = this.spellSlots[level];
            if (max > 0) {
                const used = this.spellSlotsUsed[level] || 0;
                const remaining = max - used;
                const percentage = (remaining / max) * 100;
                
                html += `
                    <div class="spell-slot-row">
                        <div class="spell-level-label">Level ${level}</div>
                        <div class="resource-bar spell-slot-bar">
                            <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);">
                                ${remaining}/${max}
                            </div>
                        </div>
                        <div class="spell-slot-buttons">
                            <button class="spell-slot-use-btn" data-level="${level}" ${remaining <= 0 ? 'disabled' : ''}>
                                Cast
                            </button>
                            <button class="spell-slot-restore-btn" data-level="${level}" ${used <= 0 ? 'disabled' : ''}>
                                Restore
                            </button>
                        </div>
                    </div>
                `;
            }
        }

        html += `
                <div class="resource-buttons" style="margin-top: 10px;">
                    <button id="long-rest-btn">
                        Long Rest (Restore All)
                    </button>
                </div>
            </div>
        `;

        return html;
    }

    renderArcaneRecovery() {
        const canUse = this.arcaneRecoveryAvailable;
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    ⚡ Arcane Recovery ${canUse ? '' : '(Used)'}
                </div>
                <div class="calculation-formula" style="margin: 10px 0;">
                    Once per day during a short rest, recover spell slots up to <strong>${this.arcaneRecoveryMax}</strong> combined levels.
                    <br><small style="color: #888;">No slot can be 6th level or higher.</small>
                </div>
                <div class="resource-buttons">
                    <button id="arcane-recovery-btn" ${!canUse ? 'disabled' : ''}>
                        Use Arcane Recovery
                    </button>
                </div>
            </div>
        `;
    }

    renderSpellManagement() {
        return `
            <div class="calculation-display">
                <div class="ability-card-name">📖 Spellbook</div>
                <div class="calculation-formula">
                    <strong>Spells in Spellbook:</strong> ${this.spellbook.length}<br>
                    <strong>Can Prepare:</strong> ${this.getMaxPreparedSpells()} spells<br>
                    <strong>Currently Prepared:</strong> ${this.preparedSpells.length}
                </div>
                <div style="margin-top: 10px;">
                    <button id="manage-spells-btn" style="width: 100%;">
                        Manage Spellbook & Prepared Spells
                    </button>
                </div>
            </div>
        `;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Spellcasting', desc: `${this.cantripsKnown} cantrips, spell save DC ${this.calculateSpellSaveDC()}` },
            { level: 1, name: 'Arcane Recovery', desc: `Recover up to ${this.arcaneRecoveryMax} spell slot levels during short rest` },
            { level: 2, name: 'Arcane Tradition', desc: this.subclass || 'Choose your school of magic' },
            { level: 4, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 8, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 12, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 16, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 18, name: 'Spell Mastery', desc: 'Cast one 1st & one 2nd level spell at will' },
            { level: 19, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 20, name: 'Signature Spells', desc: 'Cast two 3rd level spells once per short rest without slots' }
        ];

        // Add School of Evocation features if selected
        if (this.subclass === 'School of Evocation') {
            features.push(
                { level: 2, name: 'Evocation Savant', desc: 'Copy evocation spells at half cost' },
                { level: 2, name: 'Sculpt Spells', desc: 'Protect allies from your evocation spells' },
                { level: 6, name: 'Potent Cantrip', desc: 'Cantrips deal half damage on successful save' },
                { level: 10, name: 'Empowered Evocation', desc: 'Add INT modifier to evocation spell damage' },
                { level: 14, name: 'Overchannel', desc: 'Maximize damage of 1st-5th level spells' }
            );
        }

        // Sort by level
        features.sort((a, b) => a.level - b.level);

        let html = '<div class="feature-tree">';
        
        features.forEach(feature => {
            const unlocked = this.isFeatureUnlocked(feature.level);
            html += `
                <div class="feature-node ${unlocked ? 'unlocked' : 'locked'}">
                    <div class="feature-level">Lv ${feature.level}</div>
                    <div style="flex: 1;">
                        <div class="feature-name">${feature.name}</div>
                        <div class="feature-desc">${feature.desc}</div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    attachEventListeners() {
        // Spell slot use buttons
        document.querySelectorAll('.spell-slot-use-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = parseInt(e.target.dataset.level);
                this.castSpell(level);
            });
        });

        // Spell slot restore buttons
        document.querySelectorAll('.spell-slot-restore-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = parseInt(e.target.dataset.level);
                this.restoreSpellSlot(level);
            });
        });

        // Long rest button
        const longRestBtn = document.getElementById('long-rest-btn');
        if (longRestBtn) {
            longRestBtn.addEventListener('click', () => this.longRest());
        }

        // Arcane Recovery button
        const arcaneRecoveryBtn = document.getElementById('arcane-recovery-btn');
        if (arcaneRecoveryBtn) {
            arcaneRecoveryBtn.addEventListener('click', () => this.showArcaneRecoveryDialog());
        }

        // Manage spells button
        const manageSpellsBtn = document.getElementById('manage-spells-btn');
        if (manageSpellsBtn) {
            manageSpellsBtn.addEventListener('click', () => this.showSpellManagementDialog());
        }
    }

    castSpell(level) {
        const max = this.spellSlots[level];
        const used = this.spellSlotsUsed[level] || 0;

        if (used >= max) {
            this.showNotification(`❌ No ${this.getOrdinal(level)} level spell slots remaining!`);
            return;
        }

        this.spellSlotsUsed[level] = (this.spellSlotsUsed[level] || 0) + 1;
        this.render();
        
        this.showNotification(`✨ Cast ${this.getOrdinal(level)} level spell!`);
    }

    restoreSpellSlot(level) {
        const used = this.spellSlotsUsed[level] || 0;
        
        if (used <= 0) return;

        this.spellSlotsUsed[level] = Math.max(0, used - 1);
        this.render();
        
        this.showNotification(`⚡ Restored one ${this.getOrdinal(level)} level spell slot.`);
    }

    showArcaneRecoveryDialog() {
        if (!this.arcaneRecoveryAvailable) {
            this.showNotification('❌ Arcane Recovery already used. Requires long rest.');
            return;
        }

        // Simple implementation - ask user which slots to recover
        const message = `Arcane Recovery: Choose spell slots to recover (up to ${this.arcaneRecoveryMax} combined levels)\n\n` +
            `Available slots to recover:\n` +
            Object.entries(this.spellSlotsUsed)
                .filter(([level, used]) => used > 0 && parseInt(level) < 6)
                .map(([level, used]) => `Level ${level}: ${used} used`)
                .join('\n');

        const input = prompt(message + '\n\nEnter slot levels to recover (e.g., "1,1,2" to recover two 1st and one 2nd):');
        
        if (!input) return;

        const slots = input.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
        
        if (this.useArcaneRecovery(slots)) {
            this.showNotification('⚡ Arcane Recovery used! Spell slots restored.');
        } else {
            this.showNotification('❌ Invalid slot selection. Check levels and total.');
        }
    }

    useArcaneRecovery(slotLevels) {
        if (!this.arcaneRecoveryAvailable) return false;

        // Check total level doesn't exceed limit
        const totalLevels = slotLevels.reduce((sum, level) => sum + level, 0);
        if (totalLevels > this.arcaneRecoveryMax) return false;

        // Check no slots are 6th level or higher
        if (slotLevels.some(level => level >= 6)) return false;

        // Restore the slots
        slotLevels.forEach(level => {
            if (level >= 1 && level <= 9) {
                this.spellSlotsUsed[level] = Math.max(0, (this.spellSlotsUsed[level] || 0) - 1);
            }
        });

        this.arcaneRecoveryAvailable = false;
        this.render();
        return true;
    }

    showSpellManagementDialog() {
        const spellbookList = this.spellbook.join('\n');
        const preparedList = this.preparedSpells.join('\n') || 'None';
        
        alert(`📖 SPELLBOOK (${this.spellbook.length} spells):\n${spellbookList}\n\n` +
              `✓ PREPARED (${this.preparedSpells.length}/${this.getMaxPreparedSpells()}):\n${preparedList}\n\n` +
              `Note: Full spell management would require a more detailed interface.`);
    }

    longRest() {
        // Reset all spell slots
        this.spellSlotsUsed = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0};
        
        // Reset Arcane Recovery
        this.arcaneRecoveryAvailable = true;
        
        this.render();
        this.showNotification('✨ Long rest completed! All spell slots and Arcane Recovery restored.');
    }

    shortRest() {
        // At level 20, signature spells would reset here
        this.render();
        this.showNotification('Short rest completed.');
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'feature-unlock-notice';
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '1000';
        notification.style.padding = '15px 20px';
        notification.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        notification.style.color = 'white';
        notification.style.borderRadius = '8px';
        notification.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
        notification.style.animation = 'slideIn 0.3s ease-out';
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    getOrdinal(n) {
        const suffixes = ['th', 'st', 'nd', 'rd'];
        const v = n % 100;
        return n + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
    }

    updateStats(stats) {
        this.stats = stats;
        this.render();
    }

    setLevel(level) {
        this.level = parseInt(level) || 1;
        this.updateSpellProgression();
        this.render();
    }

    setSubclass(subclass) {
        this.subclass = subclass;
        this.render();
    }

    prepareSpell(spellName) {
        if (!this.spellbook.includes(spellName)) return false;
        if (this.preparedSpells.includes(spellName)) return false;
        if (this.preparedSpells.length >= this.getMaxPreparedSpells()) return false;

        this.preparedSpells.push(spellName);
        return true;
    }

    unprepareSpell(spellName) {
        const index = this.preparedSpells.indexOf(spellName);
        if (index > -1) {
            this.preparedSpells.splice(index, 1);
            return true;
        }
        return false;
    }

    addSpellToSpellbook(spellName) {
        if (!this.spellbook.includes(spellName)) {
            this.spellbook.push(spellName);
            return true;
        }
        return false;
    }
}

// Export for global use
window.WizardFeatureManager = WizardFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Wizard') {
        window.wizardManager = new WizardFeatureManager();
    }
});