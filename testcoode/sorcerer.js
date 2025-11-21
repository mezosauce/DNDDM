/**
 * Sorcerer Class Features UI
 * Handles Sorcerer-specific displays: Spell Slots, Sorcery Points, Metamagic, Sorcerous Origin
 */

class SorcererFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Sorcerer');
        this.sorceryPoints = 0;
        this.maxSorceryPoints = 0;
        this.metamagicOptions = new Set();
        this.availableMetamagicCount = 0;
        this.spellSlots = {};
        this.maxSpellSlots = {};
        this.cantripsKnown = [];
        this.spellsKnown = [];
        this.sorcerousOrigin = '';
        this.dragonAncestor = '';
        this.dragonDamageType = '';
        this.stats = { charisma: 10, constitution: 10, dexterity: 10 };
    }

    initialize(level, stats, subclass = '') {
        this.level = level;
        this.stats = stats || this.stats;
        this.sorcerousOrigin = subclass;
        this.updateSpellProgression();
        this.updateSorceryPoints();
        this.updateMetamagicProgression();
        this.render();
    }

    updateSpellProgression() {
        // Spell slot progression based on level
        const spellSlotTable = {
            1: {1: 2},
            2: {1: 3},
            3: {1: 4, 2: 2},
            4: {1: 4, 2: 3},
            5: {1: 4, 2: 3, 3: 2},
            6: {1: 4, 2: 3, 3: 3},
            7: {1: 4, 2: 3, 3: 3, 4: 1},
            8: {1: 4, 2: 3, 3: 3, 4: 2},
            9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
            18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        };

        this.maxSpellSlots = spellSlotTable[this.level] || {1: 2};
        this.spellSlots = {...this.maxSpellSlots};

        // Cantrips known progression
        const cantripsKnown = this.level >= 10 ? 6 : this.level >= 4 ? 5 : 4;
        if (this.cantripsKnown.length < cantripsKnown) {
            while (this.cantripsKnown.length < cantripsKnown) {
                this.cantripsKnown.push(`Cantrip ${this.cantripsKnown.length + 1}`);
            }
        }

        // Spells known progression
        const spellsKnownTable = {
            1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10,
            10: 11, 11: 12, 12: 12, 13: 13, 14: 13, 15: 14, 16: 14,
            17: 15, 18: 15, 19: 15, 20: 15
        };
        const targetSpells = spellsKnownTable[this.level] || 2;
        if (this.spellsKnown.length < targetSpells) {
            while (this.spellsKnown.length < targetSpells) {
                this.spellsKnown.push(`Spell ${this.spellsKnown.length + 1}`);
            }
        }
    }

    updateSorceryPoints() {
        // Sorcery Points progression
        const sorceryPointTable = {
            2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
            11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 
            18: 18, 19: 19, 20: 20
        };

        this.maxSorceryPoints = sorceryPointTable[this.level] || 0;
        this.sorceryPoints = Math.min(this.sorceryPoints, this.maxSorceryPoints);
    }

    updateMetamagicProgression() {
        // Metamagic options available
        if (this.level >= 17) this.availableMetamagicCount = 4;
        else if (this.level >= 10) this.availableMetamagicCount = 3;
        else if (this.level >= 3) this.availableMetamagicCount = 2;
        else this.availableMetamagicCount = 0;

        // Ensure we don't have more metamagic options than allowed
        if (this.metamagicOptions.size > this.availableMetamagicCount) {
            const excess = Array.from(this.metamagicOptions).slice(this.availableMetamagicCount);
            excess.forEach(option => this.metamagicOptions.delete(option));
        }
    }

    getSpellSaveDC() {
        const chaMod = calculateModifier(this.stats.charisma);
        const profBonus = this.getProficiencyBonus();
        return 8 + profBonus + chaMod;
    }

    getSpellAttackBonus() {
        const chaMod = calculateModifier(this.stats.charisma);
        const profBonus = this.getProficiencyBonus();
        return profBonus + chaMod;
    }

    getProficiencyBonus() {
        if (this.level < 5) return 2;
        else if (this.level < 9) return 3;
        else if (this.level < 13) return 4;
        else if (this.level < 17) return 5;
        else return 6;
    }

    calculateDraconicResilience() {
        if (this.sorcerousOrigin !== 'Draconic Bloodline') return null;
        
        const dexMod = calculateModifier(this.stats.dexterity);
        return 13 + dexMod;
    }

    render() {
        const container = document.getElementById('sorcerer-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    🔮 Sorcerer Features
                </div>
                
                ${this.renderSpellcastingInfo()}
                ${this.renderSorceryPointsTracker()}
                ${this.renderSpellSlots()}
                ${this.renderMetamagicOptions()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderSpellcastingInfo() {
        const spellDC = this.getSpellSaveDC();
        const spellAttack = this.getSpellAttackBonus();
        const chaMod = calculateModifier(this.stats.charisma);
        const profBonus = this.getProficiencyBonus();

        let draconicAC = '';
        if (this.sorcerousOrigin === 'Draconic Bloodline') {
            const ac = this.calculateDraconicResilience();
            draconicAC = `
                <div class="calculation-display" style="margin-top: 10px;">
                    <div class="ability-card-name">🐉 Draconic Resilience</div>
                    <div class="calculation-formula">
                        AC = 13 + DEX (${formatModifier(calculateModifier(this.stats.dexterity))})
                    </div>
                    <div class="calculation-result">
                        AC ${ac}
                    </div>
                </div>
            `;
        }

        return `
            <div class="calculation-display">
                <div class="ability-card-name">✨ Spellcasting</div>
                <div class="calculation-formula">
                    Spell Save DC = 8 + Proficiency (${profBonus}) + CHA (${formatModifier(chaMod)})
                </div>
                <div class="calculation-result">
                    DC ${spellDC}
                </div>
                <div class="calculation-formula" style="margin-top: 5px;">
                    Spell Attack = Proficiency (${profBonus}) + CHA (${formatModifier(chaMod)})
                </div>
                <div class="calculation-result">
                    +${spellAttack}
                </div>
                ${draconicAC}
            </div>
        `;
    }

    renderSorceryPointsTracker() {
        if (this.level < 2) return '';

        const percentage = (this.sorceryPoints / this.maxSorceryPoints) * 100;
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    💫 Sorcery Points
                </div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #9b59b6 0%, #8e44ad 100%);">
                        ${this.sorceryPoints}/${this.maxSorceryPoints}
                    </div>
                </div>
                <div class="resource-buttons">
                    <button id="sorcery-long-rest-btn">
                        Long Rest
                    </button>
                    <button id="sorcery-short-rest-btn" ${this.level < 20 ? 'disabled' : ''}>
                        Short Rest
                    </button>
                </div>
                ${this.level >= 20 ? '<div style="font-size: 0.8em; color: #666; margin-top: 5px;">Level 20: Regain 4 SP on short rest</div>' : ''}
            </div>
        `;
    }

    renderSpellSlots() {
        if (!Object.keys(this.spellSlots).length) return '';

        let html = '<div class="spell-slots-container">';
        html += '<div class="spell-slots-header">Spell Slots</div>';
        html += '<div class="spell-slots-grid">';

        // Sort spell levels
        const spellLevels = Object.keys(this.spellSlots).map(Number).sort((a, b) => a - b);
        
        spellLevels.forEach(level => {
            const current = this.spellSlots[level];
            const max = this.maxSpellSlots[level];
            const percentage = (current / max) * 100;
            
            html += `
                <div class="spell-slot-level">
                    <div class="spell-slot-label">Level ${level}</div>
                    <div class="spell-slot-bar">
                        <div class="spell-slot-fill" style="width: ${percentage}%">
                            ${current}/${max}
                        </div>
                    </div>
                    ${this.level >= 2 ? `
                        <div class="spell-slot-buttons">
                            <button class="convert-slot-btn" data-level="${level}">
                                Convert to SP
                            </button>
                            ${this.canCreateSpellSlot(level) ? `
                                <button class="create-slot-btn" data-level="${level}">
                                    Create from SP
                                </button>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    renderMetamagicOptions() {
        if (this.level < 3) return '';

        const metamagicDescriptions = {
            'Careful Spell': 'Cost: 1 SP - Chosen creatures auto-succeed on saves',
            'Distant Spell': 'Cost: 1 SP - Double range or touch→30ft',
            'Empowered Spell': 'Cost: 1 SP - Reroll damage dice',
            'Extended Spell': 'Cost: 1 SP - Double duration (max 24h)',
            'Heightened Spell': 'Cost: 3 SP - Target has disadvantage on first save',
            'Quickened Spell': 'Cost: 2 SP - Cast time: action→bonus action',
            'Subtle Spell': 'Cost: 1 SP - No somatic/verbal components',
            'Twinned Spell': 'Cost: spell level SP - Target second creature'
        };

        const allOptions = Object.keys(metamagicDescriptions);
        const selectedOptions = Array.from(this.metamagicOptions);

        let html = `
            <div class="metamagic-container">
                <div class="metamagic-header">
                    🔥 Metamagic Options (${selectedOptions.length}/${this.availableMetamagicCount})
                </div>
        `;

        // Selected metamagic options
        if (selectedOptions.length > 0) {
            html += '<div class="selected-metamagic">';
            selectedOptions.forEach(option => {
                html += `
                    <div class="metamagic-option selected">
                        <div class="metamagic-name">${option}</div>
                        <div class="metamagic-desc">${metamagicDescriptions[option]}</div>
                        <button class="remove-metamagic-btn" data-option="${option}">Remove</button>
                    </div>
                `;
            });
            html += '</div>';
        }

        // Available options to choose from
        if (selectedOptions.length < this.availableMetamagicCount) {
            html += '<div class="available-metamagic">';
            html += '<div style="margin-bottom: 8px; font-weight: bold;">Available Options:</div>';
            
            allOptions.forEach(option => {
                if (!this.metamagicOptions.has(option)) {
                    html += `
                        <div class="metamagic-option available">
                            <div class="metamagic-name">${option}</div>
                            <div class="metamagic-desc">${metamagicDescriptions[option]}</div>
                            <button class="add-metamagic-btn" data-option="${option}">Add</button>
                        </div>
                    `;
                }
            });
            html += '</div>';
        }

        html += '</div>';
        return html;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Spellcasting', desc: `${this.cantripsKnown.length} cantrips, ${this.spellsKnown.length} spells known` },
            { level: 1, name: 'Sorcerous Origin', desc: this.sorcerousOrigin || 'Choose your origin' },
            { level: 2, name: 'Font of Magic', desc: `${this.maxSorceryPoints} sorcery points, flexible casting` },
            { level: 3, name: 'Metamagic', desc: `${this.availableMetamagicCount} options available` },
            { level: 4, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 6, name: 'Sorcerous Origin Feature', desc: this.getOriginFeatureName(6) },
            { level: 8, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 10, name: 'Metamagic', desc: 'Learn 1 additional metamagic option' },
            { level: 12, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 14, name: 'Sorcerous Origin Feature', desc: this.getOriginFeatureName(14) },
            { level: 16, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 17, name: 'Metamagic', desc: 'Learn 1 additional metamagic option' },
            { level: 18, name: 'Sorcerous Origin Feature', desc: this.getOriginFeatureName(18) },
            { level: 19, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 20, name: 'Sorcerous Restoration', desc: 'Regain 4 sorcery points on short rest' }
        ];

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

    getOriginFeatureName(level) {
        if (this.sorcerousOrigin === 'Draconic Bloodline') {
            if (level === 6) return 'Elemental Affinity';
            if (level === 14) return 'Dragon Wings';
            if (level === 18) return 'Draconic Presence';
        }
        return 'Origin Feature';
    }

    attachEventListeners() {
        // Sorcery point buttons
        const longRestBtn = document.getElementById('sorcery-long-rest-btn');
        const shortRestBtn = document.getElementById('sorcery-short-rest-btn');

        if (longRestBtn) {
            longRestBtn.addEventListener('click', () => this.longRest());
        }
        if (shortRestBtn) {
            shortRestBtn.addEventListener('click', () => this.shortRest());
        }

        // Spell slot conversion buttons
        document.querySelectorAll('.convert-slot-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = parseInt(e.target.dataset.level);
                this.convertSlotToPoints(level);
            });
        });

        document.querySelectorAll('.create-slot-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = parseInt(e.target.dataset.level);
                this.createSlotFromPoints(level);
            });
        });

        // Metamagic buttons
        document.querySelectorAll('.add-metamagic-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const option = e.target.dataset.option;
                this.addMetamagicOption(option);
            });
        });

        document.querySelectorAll('.remove-metamagic-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const option = e.target.dataset.option;
                this.removeMetamagicOption(option);
            });
        });
    }

    canCreateSpellSlot(level) {
        const costTable = {1: 2, 2: 3, 3: 5, 4: 6, 5: 7};
        return this.sorceryPoints >= (costTable[level] || 999);
    }

    convertSlotToPoints(level) {
        if (!this.spellSlots[level] || this.spellSlots[level] <= 0) {
            this.showNotification('No spell slots of that level available!');
            return;
        }

        if (this.sorceryPoints + level > this.maxSorceryPoints) {
            this.showNotification('Not enough sorcery point capacity!');
            return;
        }

        this.spellSlots[level]--;
        this.sorceryPoints += level;
        this.render();
        
        this.showNotification(`Converted Level ${level} slot to ${level} sorcery points!`);
    }

    createSlotFromPoints(level) {
        const costTable = {1: 2, 2: 3, 3: 5, 4: 6, 5: 7};
        const cost = costTable[level];

        if (!cost) {
            this.showNotification('Cannot create spell slots above level 5!');
            return;
        }

        if (this.sorceryPoints < cost) {
            this.showNotification(`Not enough sorcery points! Need ${cost}, have ${this.sorceryPoints}`);
            return;
        }

        this.sorceryPoints -= cost;
        this.spellSlots[level] = (this.spellSlots[level] || 0) + 1;
        this.render();
        
        this.showNotification(`Created Level ${level} spell slot for ${cost} sorcery points!`);
    }

    addMetamagicOption(option) {
        if (this.metamagicOptions.size >= this.availableMetamagicCount) {
            this.showNotification(`Maximum ${this.availableMetamagicCount} metamagic options reached!`);
            return;
        }

        this.metamagicOptions.add(option);
        this.render();
        
        this.showNotification(`Added ${option} metamagic option!`);
    }

    removeMetamagicOption(option) {
        this.metamagicOptions.delete(option);
        this.render();
        
        this.showNotification(`Removed ${option} metamagic option.`);
    }

    longRest() {
        // Reset spell slots
        this.spellSlots = {...this.maxSpellSlots};
        
        // Reset sorcery points
        this.sorceryPoints = this.maxSorceryPoints;
        
        this.render();
        
        this.showNotification('✨ Long rest completed! Spell slots and sorcery points restored.');
    }

    shortRest() {
        if (this.level >= 20) {
            this.sorceryPoints = Math.min(this.sorceryPoints + 4, this.maxSorceryPoints);
            this.render();
            this.showNotification('✨ Short rest: Regained 4 sorcery points!');
        } else {
            this.showNotification('Sorcerous Restoration available at level 20.');
        }
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
        this.updateSpellProgression();
        this.updateSorceryPoints();
        this.updateMetamagicProgression();
        this.render();
    }

    setSubclass(subclass) {
        this.sorcerousOrigin = subclass;
        this.render();
    }

    setDragonAncestor(ancestor, damageType) {
        this.dragonAncestor = ancestor;
        this.dragonDamageType = damageType;
        this.render();
    }
}

// Export for global use
window.SorcererFeatureManager = SorcererFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Sorcerer') {
        window.sorcererManager = new SorcererFeatureManager();
    }
});