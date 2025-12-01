/**
 * Druid Class Features UI
 * Handles Druid-specific displays: Wild Shape, Spellcasting, Feature Tree
 */

class DruidFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Druid');
        this.wildShapeUses = 2;
        this.wildShapeUsesRemaining = 2;
        this.currentlyWildShaped = false;
        this.wildShapeBeast = '';
        this.wildShapeMaxCR = 0.25;
        this.wildShapeMaxHours = 1;
        this.canFly = false;
        this.canSwim = false;
        
        // Spellcasting
        this.cantripsKnown = 2;
        this.knownCantrips = [];
        this.preparedSpells = [];
        this.spellSlots = {};
        this.spellSlotsUsed = {};
        
        // Circle features
        this.druidCircle = '';
        this.circleLandType = '';
        this.naturalRecoveryUsed = false;
        
        this.stats = { wisdom: 10, constitution: 10, dexterity: 10 };
    }

    initialize(level, stats, circleLandType = '') {
        this.level = level;
        this.stats = stats || this.stats;
        this.circleLandType = circleLandType;
        this.updateWildShapeProgression();
        this.updateSpellSlots();
        this.updateCantripsKnown();
        this.render();
    }

    updateWildShapeProgression() {
        if (this.level >= 20) {
            this.wildShapeUses = 999; // Unlimited
        } else if (this.level >= 2) {
            this.wildShapeUses = 2;
        }
        
        // Reset uses remaining if max changed
        if (this.wildShapeUsesRemaining > this.wildShapeUses) {
            this.wildShapeUsesRemaining = this.wildShapeUses;
        }
        
        // CR and duration progression
        if (this.level >= 8) {
            this.wildShapeMaxCR = 1;
            this.canFly = true;
            this.canSwim = true;
        } else if (this.level >= 4) {
            this.wildShapeMaxCR = 0.5;
            this.canFly = false;
            this.canSwim = true;
        } else if (this.level >= 2) {
            this.wildShapeMaxCR = 0.25;
            this.canFly = false;
            this.canSwim = false;
        }
        
        this.wildShapeMaxHours = Math.floor(this.level / 2);
    }

    updateCantripsKnown() {
        if (this.level >= 10) this.cantripsKnown = 4;
        else if (this.level >= 4) this.cantripsKnown = 3;
        else this.cantripsKnown = 2;
    }

    updateSpellSlots() {
        const slotsByLevel = {
            1: { 1: 2 },
            2: { 1: 3 },
            3: { 1: 4, 2: 2 },
            4: { 1: 4, 2: 3 },
            5: { 1: 4, 2: 3, 3: 2 },
            6: { 1: 4, 2: 3, 3: 3 },
            7: { 1: 4, 2: 3, 3: 3, 4: 1 },
            8: { 1: 4, 2: 3, 3: 3, 4: 2 },
            9: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 1 },
            10: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2 },
            11: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1 },
            12: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1 },
            13: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1 },
            14: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1 },
            15: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1 },
            16: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1 },
            17: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1 },
            18: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1 },
            19: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1 },
            20: { 1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1 }
        };

        this.spellSlots = slotsByLevel[this.level] || { 1: 2 };
        
        // Initialize used slots if not exists
        for (let level in this.spellSlots) {
            if (!(level in this.spellSlotsUsed)) {
                this.spellSlotsUsed[level] = 0;
            }
        }
    }

    getSpellSaveDC() {
        const wisMod = calculateModifier(this.stats.wisdom);
        const profBonus = this.getProficiencyBonus();
        return 8 + profBonus + wisMod;
    }

    getSpellAttackBonus() {
        const wisMod = calculateModifier(this.stats.wisdom);
        const profBonus = this.getProficiencyBonus();
        return profBonus + wisMod;
    }

    getMaxPreparedSpells() {
        const wisMod = calculateModifier(this.stats.wisdom);
        return Math.max(1, wisMod + this.level);
    }

    getProficiencyBonus() {
        if (this.level < 5) return 2;
        if (this.level < 9) return 3;
        if (this.level < 13) return 4;
        if (this.level < 17) return 5;
        return 6;
    }

    render() {
        const container = document.getElementById('druid-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    🌿 Druid Features
                </div>
                
                ${this.renderSpellcastingInfo()}
                ${this.level >= 2 ? this.renderWildShapeTracker() : ''}
                ${this.druidCircle === 'Circle of the Land' && this.level >= 2 ? this.renderNaturalRecovery() : ''}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderSpellcastingInfo() {
        const spellDC = this.getSpellSaveDC();
        const spellAttack = this.getSpellAttackBonus();
        const maxPrepared = this.getMaxPreparedSpells();
        const wisMod = calculateModifier(this.stats.wisdom);

        return `
            <div class="calculation-display">
                <div class="ability-card-name">✨ Spellcasting</div>
                <div class="calculation-formula" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div>
                        <strong>Spell Save DC:</strong> ${spellDC}<br>
                        <small>8 + Prof (${this.getProficiencyBonus()}) + WIS (${formatModifier(wisMod)})</small>
                    </div>
                    <div>
                        <strong>Spell Attack:</strong> ${formatModifier(spellAttack)}<br>
                        <small>Prof (${this.getProficiencyBonus()}) + WIS (${formatModifier(wisMod)})</small>
                    </div>
                </div>
                <div style="margin-top: 10px;">
                    <strong>Cantrips Known:</strong> ${this.knownCantrips.length}/${this.cantripsKnown}<br>
                    <strong>Spells Prepared:</strong> ${this.preparedSpells.length}/${maxPrepared}
                </div>
                ${this.renderSpellSlots()}
            </div>
        `;
    }

    renderSpellSlots() {
        let html = '<div style="margin-top: 15px;"><strong>Spell Slots:</strong></div>';
        html += '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 8px;">';

        for (let level = 1; level <= 9; level++) {
            if (this.spellSlots[level]) {
                const total = this.spellSlots[level];
                const used = this.spellSlotsUsed[level] || 0;
                const remaining = total - used;
                const percentage = (remaining / total) * 100;

                html += `
                    <div class="spell-slot-tracker" data-level="${level}">
                        <div style="font-size: 12px; font-weight: bold; margin-bottom: 4px;">
                            Level ${level}
                        </div>
                        <div class="resource-bar" style="height: 20px;">
                            <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #4caf50 0%, #45a049 100%); font-size: 11px; line-height: 20px;">
                                ${remaining}/${total}
                            </div>
                        </div>
                        <div style="margin-top: 4px; display: flex; gap: 4px;">
                            <button class="spell-use-btn" data-level="${level}" style="flex: 1; font-size: 11px; padding: 2px 4px;" ${remaining <= 0 ? 'disabled' : ''}>
                                Use
                            </button>
                            <button class="spell-restore-btn" data-level="${level}" style="flex: 1; font-size: 11px; padding: 2px 4px;" ${used <= 0 ? 'disabled' : ''}>
                                +1
                            </button>
                        </div>
                    </div>
                `;
            }
        }

        html += '</div>';
        html += `
            <div style="margin-top: 10px;">
                <button id="spell-long-rest-btn" style="width: 100%;">
                    Long Rest (Restore All Slots)
                </button>
            </div>
        `;

        return html;
    }

    renderWildShapeTracker() {
        const usesText = this.level >= 20 ? 'Unlimited' : `${this.wildShapeUsesRemaining}/${this.wildShapeUses}`;
        const percentage = this.level >= 20 ? 100 : (this.wildShapeUsesRemaining / this.wildShapeUses) * 100;

        return `
            <div class="resource-tracker" style="margin-top: 15px;">
                <div class="resource-name">
                    🐻 Wild Shape ${this.currentlyWildShaped ? `(${this.wildShapeBeast})` : ''}
                </div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #8bc34a 0%, #7cb342 100%);">
                        ${usesText}
                    </div>
                </div>
                <div style="margin: 10px 0; font-size: 13px;">
                    <strong>Max CR:</strong> ${this.wildShapeMaxCR} | 
                    <strong>Duration:</strong> ${this.wildShapeMaxHours}h | 
                    <strong>Flying:</strong> ${this.canFly ? '✓' : '✗'} | 
                    <strong>Swimming:</strong> ${this.canSwim ? '✓' : '✗'}
                </div>
                <div class="resource-buttons">
                    <button id="wildshape-enter-btn" ${this.currentlyWildShaped || this.wildShapeUsesRemaining <= 0 ? 'disabled' : ''}>
                        Transform
                    </button>
                    <button id="wildshape-end-btn" ${!this.currentlyWildShaped ? 'disabled' : ''}>
                        Revert
                    </button>
                    <button id="wildshape-rest-btn">
                        Short/Long Rest
                    </button>
                </div>
                ${this.currentlyWildShaped ? this.renderWildShapeBenefits() : ''}
            </div>
        `;
    }

    renderWildShapeBenefits() {
        const canCastSpells = this.level >= 18;
        return `
            <div class="calculation-display" style="margin-top: 10px;">
                <strong style="color: #8bc34a;">Wild Shape Benefits:</strong>
                <div class="calculation-formula">
                    • Use beast's HP, AC, speed, and physical stats<br>
                    • Retain Intelligence, Wisdom, Charisma<br>
                    • Retain skill/save proficiencies<br>
                    • ${canCastSpells ? '<span style="color: #4caf50;">✓ Can cast druid spells (Beast Spells)</span>' : '✗ Cannot cast spells'}<br>
                    • Cannot speak or use items requiring hands<br>
                    • Excess damage carries over to normal form
                </div>
            </div>
        `;
    }

    renderNaturalRecovery() {
        const maxRecovery = Math.ceil(this.level / 2);
        
        return `
            <div class="calculation-display" style="margin-top: 15px;">
                <div class="ability-card-name">🌊 Natural Recovery</div>
                <div class="calculation-formula">
                    During a short rest, recover spell slots with combined level ≤ ${maxRecovery}<br>
                    (No slot can be 6th level or higher)
                </div>
                <button id="natural-recovery-btn" ${this.naturalRecoveryUsed ? 'disabled' : ''} style="margin-top: 8px; width: 100%;">
                    ${this.naturalRecoveryUsed ? 'Used (Resets on Long Rest)' : 'Use Natural Recovery'}
                </button>
            </div>
        `;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Druidic', desc: 'Secret language of druids' },
            { level: 1, name: 'Spellcasting', desc: `Prepare ${this.getMaxPreparedSpells()} spells, know ${this.cantripsKnown} cantrips` },
            { level: 2, name: 'Wild Shape', desc: `${this.wildShapeUses === 999 ? 'Unlimited' : this.wildShapeUses} uses, CR ${this.wildShapeMaxCR}, ${this.wildShapeMaxHours}h duration` },
            { level: 2, name: 'Druid Circle', desc: this.druidCircle || 'Choose your circle' },
            { level: 3, name: 'Circle Feature', desc: this.getCircleFeature(3) },
            { level: 4, name: 'Wild Shape Improvement', desc: 'CR 1/2, can swim' },
            { level: 6, name: 'Circle Feature', desc: this.getCircleFeature(6) },
            { level: 8, name: 'Wild Shape Improvement', desc: 'CR 1, can fly' },
            { level: 10, name: 'Circle Feature', desc: this.getCircleFeature(10) },
            { level: 14, name: 'Circle Feature', desc: this.getCircleFeature(14) },
            { level: 18, name: 'Timeless Body', desc: 'Age more slowly (10 years = 1 year)' },
            { level: 18, name: 'Beast Spells', desc: 'Cast druid spells in Wild Shape form' },
            { level: 20, name: 'Archdruid', desc: 'Unlimited Wild Shape, ignore verbal/somatic components' }
        ];

        let html = '<div class="feature-tree" style="margin-top: 15px;">';

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

    getCircleFeature(level) {
        if (this.druidCircle === 'Circle of the Land') {
            if (level === 3) return `Circle spells (${this.circleLandType || 'choose land type'})`;
            if (level === 6) return "Land's Stride - ignore difficult terrain";
            if (level === 10) return "Nature's Ward - immune to poison, charm/frighten from elementals/fey";
            if (level === 14) return "Nature's Sanctuary - beasts/plants must save to attack you";
        } else if (this.druidCircle === 'Circle of the Moon') {
            if (level === 3) return 'Combat Wild Shape - bonus action + use for healing';
            if (level === 6) return 'Primal Strike - attacks count as magical';
            if (level === 10) return 'Elemental Wild Shape - CR 5 elementals';
            if (level === 14) return 'Thousand Forms - alter self at will';
        }
        return 'Circle ability';
    }

    attachEventListeners() {
        // Wild Shape buttons
        const enterBtn = document.getElementById('wildshape-enter-btn');
        const endBtn = document.getElementById('wildshape-end-btn');
        const restBtn = document.getElementById('wildshape-rest-btn');

        if (enterBtn) {
            enterBtn.addEventListener('click', () => this.enterWildShape());
        }
        if (endBtn) {
            endBtn.addEventListener('click', () => this.exitWildShape());
        }
        if (restBtn) {
            restBtn.addEventListener('click', () => this.shortRest());
        }

        // Spell slot buttons
        const useButtons = document.querySelectorAll('.spell-use-btn');
        const restoreButtons = document.querySelectorAll('.spell-restore-btn');
        const longRestBtn = document.getElementById('spell-long-rest-btn');

        useButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = parseInt(e.target.dataset.level);
                this.useSpellSlot(level);
            });
        });

        restoreButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = parseInt(e.target.dataset.level);
                this.restoreSpellSlot(level);
            });
        });

        if (longRestBtn) {
            longRestBtn.addEventListener('click', () => this.longRest());
        }

        // Natural Recovery button
        const naturalRecoveryBtn = document.getElementById('natural-recovery-btn');
        if (naturalRecoveryBtn) {
            naturalRecoveryBtn.addEventListener('click', () => this.showNaturalRecoveryDialog());
        }
    }

    enterWildShape() {
        if (this.wildShapeUsesRemaining <= 0 || this.currentlyWildShaped) return;

        // Show dialog to enter beast name
        const beastName = prompt(`Enter beast name (CR ≤ ${this.wildShapeMaxCR}):\n\nExamples:\n- CR 1/4: Wolf, Giant Badger\n- CR 1/2: Crocodile, Giant Wasp\n- CR 1: Brown Bear, Giant Eagle`, 'Wolf');
        
        if (!beastName) return;

        this.currentlyWildShaped = true;
        this.wildShapeBeast = beastName;
        this.wildShapeUsesRemaining--;
        this.render();

        this.showNotification(`🐻 Transformed into ${beastName}! Duration: ${this.wildShapeMaxHours} hours`);
    }

    exitWildShape() {
        if (!this.currentlyWildShaped) return;

        const beast = this.wildShapeBeast;
        this.currentlyWildShaped = false;
        this.wildShapeBeast = '';
        this.render();

        this.showNotification(`Reverted from ${beast} form.`);
    }

    useSpellSlot(level) {
        const max = this.spellSlots[level];
        const used = this.spellSlotsUsed[level] || 0;

        if (used >= max) return;

        this.spellSlotsUsed[level] = used + 1;
        this.render();

        this.showNotification(`Used level ${level} spell slot. ${max - used - 1} remaining.`);
    }

    restoreSpellSlot(level) {
        const used = this.spellSlotsUsed[level] || 0;

        if (used <= 0) return;

        this.spellSlotsUsed[level] = used - 1;
        this.render();

        this.showNotification(`Restored level ${level} spell slot.`);
    }

    showNaturalRecoveryDialog() {
        const maxRecovery = Math.ceil(this.level / 2);
        
        let message = `Natural Recovery - Recover spell slots during short rest\n\n`;
        message += `You can recover spell slots with total level ≤ ${maxRecovery}\n`;
        message += `(No slot can be 6th level or higher)\n\n`;
        message += `Current used slots:\n`;
        
        for (let level = 1; level <= 5; level++) {
            const used = this.spellSlotsUsed[level] || 0;
            if (used > 0) {
                message += `Level ${level}: ${used} used\n`;
            }
        }
        
        message += `\nEnter slot levels to recover (e.g., "1,2,2" or "3,1"):\n`;
        message += `Must total ${maxRecovery} or less.`;
        
        const input = prompt(message);
        if (!input) return;
        
        // Parse input
        const levels = input.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
        
        // Validate
        const total = levels.reduce((sum, l) => sum + l, 0);
        const hasInvalidLevel = levels.some(l => l < 1 || l > 5 || !(l in this.spellSlots));
        
        if (total > maxRecovery) {
            alert(`Total ${total} exceeds maximum ${maxRecovery}`);
            return;
        }
        
        if (hasInvalidLevel) {
            alert('Invalid spell level(s)');
            return;
        }
        
        // Apply recovery
        levels.forEach(level => {
            if (this.spellSlotsUsed[level] > 0) {
                this.spellSlotsUsed[level]--;
            }
        });
        
        this.naturalRecoveryUsed = true;
        this.render();
        
        this.showNotification(`✨ Natural Recovery used! Recovered ${levels.length} spell slot(s).`);
    }

    shortRest() {
        this.wildShapeUsesRemaining = this.wildShapeUses;
        this.render();

        this.showNotification('Short rest completed. Wild Shape uses restored!');
    }

    longRest() {
        // Restore all spell slots
        for (let level in this.spellSlotsUsed) {
            this.spellSlotsUsed[level] = 0;
        }

        // Restore Wild Shape
        this.wildShapeUsesRemaining = this.wildShapeUses;
        this.currentlyWildShaped = false;
        this.wildShapeBeast = '';
        
        // Reset Natural Recovery
        this.naturalRecoveryUsed = false;

        this.render();

        this.showNotification('✨ Long rest completed. All resources restored!');
    }

    showNotification(message) {
        // Simple notification - could be enhanced with a toast system
        const notification = document.createElement('div');
        notification.className = 'feature-unlock-notice';
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '1000';
        notification.style.animation = 'slideIn 0.3s ease-out';

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    updateStats(stats) {
        this.stats = stats;
        this.render();
    }

    setLevel(level) {
        this.level = parseInt(level) || 1;
        this.updateWildShapeProgression();
        this.updateSpellSlots();
        this.updateCantripsKnown();
        this.render();
    }


    setCircleLandType(landType) {
        this.circleLandType = landType;
        this.render();
    }

    // Serialization methods for saving/loading
    getState() {
        return {
            level: this.level,
            stats: this.stats,
            druidCircle: this.druidCircle,
            circleLandType: this.circleLandType,
            wildShapeUsesRemaining: this.wildShapeUsesRemaining,
            currentlyWildShaped: this.currentlyWildShaped,
            wildShapeBeast: this.wildShapeBeast,
            spellSlotsUsed: this.spellSlotsUsed,
            naturalRecoveryUsed: this.naturalRecoveryUsed,
            knownCantrips: this.knownCantrips,
            preparedSpells: this.preparedSpells
        };
    }

    loadState(state) {
        if (state.level) this.level = state.level;
        if (state.stats) this.stats = state.stats;
        if (state.druidCircle) this.druidCircle = state.druidCircle;
        if (state.circleLandType) this.circleLandType = state.circleLandType;
        if (state.wildShapeUsesRemaining !== undefined) this.wildShapeUsesRemaining = state.wildShapeUsesRemaining;
        if (state.currentlyWildShaped !== undefined) this.currentlyWildShaped = state.currentlyWildShaped;
        if (state.wildShapeBeast) this.wildShapeBeast = state.wildShapeBeast;
        if (state.spellSlotsUsed) this.spellSlotsUsed = state.spellSlotsUsed;
        if (state.naturalRecoveryUsed !== undefined) this.naturalRecoveryUsed = state.naturalRecoveryUsed;
        if (state.knownCantrips) this.knownCantrips = state.knownCantrips;
        if (state.preparedSpells) this.preparedSpells = state.preparedSpells;

        this.updateWildShapeProgression();
        this.updateSpellSlots();
        this.updateCantripsKnown();
        this.render();
    }
}

// Export for global use
window.DruidFeatureManager = DruidFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Druid') {
        window.druidManager = new DruidFeatureManager();
    }
});