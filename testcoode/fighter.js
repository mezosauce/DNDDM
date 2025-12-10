/**
 * Fighter Class Features UI
 * Handles Fighter-specific displays: Fighting Styles, Second Wind, Action Surge, Feature Tree
 */

class FighterFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Fighter');
        this.secondWindUsed = false;
        this.actionSurgeUses = 0;
        this.actionSurgeMaxUses = 1;
        this.indomitableUses = 0;
        this.indomitableMaxUses = 0;
        this.extraAttacks = 1;
        this.fightingStyles = [];
        this.stats = { strength: 10, dexterity: 10, constitution: 10 };
        this.subclass = '';
    }

    initialize(level, stats, subclass = '', fightingStyles = []) {
        this.level = level;
        this.stats = stats || this.stats;
        this.subclass = subclass;
        this.fightingStyles = fightingStyles || ['Defense']; // Default style
        this.updateProgression();
        this.render();
    }

    updateProgression() {
        // Action Surge progression
        if (this.level >= 17) {
            this.actionSurgeMaxUses = 2;
        } else if (this.level >= 2) {
            this.actionSurgeMaxUses = 1;
        } else {
            this.actionSurgeMaxUses = 0;
        }

        // Indomitable progression
        if (this.level >= 17) {
            this.indomitableMaxUses = 3;
        } else if (this.level >= 13) {
            this.indomitableMaxUses = 2;
        } else if (this.level >= 9) {
            this.indomitableMaxUses = 1;
        } else {
            this.indomitableMaxUses = 0;
        }

        // Extra Attack progression
        if (this.level >= 20) {
            this.extraAttacks = 4;
        } else if (this.level >= 11) {
            this.extraAttacks = 3;
        } else if (this.level >= 5) {
            this.extraAttacks = 2;
        } else {
            this.extraAttacks = 1;
        }
    }

    calculateACWithFightingStyle(baseAC) {
        let ac = baseAC;
        if (this.fightingStyles.includes('Defense')) {
            ac += 1;
        }
        return ac;
    }

    getCriticalRange() {
        if (this.subclass === 'Champion') {
            if (this.level >= 15) return '18-20';
            if (this.level >= 3) return '19-20';
        }
        return '20';
    }

    getRemarkableAthleteBonus() {
        const proficiencyBonus = this.getProficiencyBonus();
        return Math.ceil(proficiencyBonus / 2);
    }

    getProficiencyBonus() {
        if (this.level < 5) return 2;
        if (this.level < 9) return 3;
        if (this.level < 13) return 4;
        if (this.level < 17) return 5;
        return 6;
    }

    render() {
        const container = document.getElementById('fighter-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                     Fighter Features
                </div>
                
                ${this.renderResourceTrackers()}
                ${this.renderFightingStyles()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderResourceTrackers() {
        const secondWindPercentage = this.secondWindUsed ? 0 : 100;
        const actionSurgePercentage = ((this.actionSurgeMaxUses - this.actionSurgeUses) / this.actionSurgeMaxUses) * 100;
        const indomitablePercentage = ((this.indomitableMaxUses - this.indomitableUses) / this.indomitableMaxUses) * 100;

        return `
            <div class="resource-trackers">
                <!-- Second Wind -->
                <div class="resource-tracker">
                    <div class="resource-name">
                        💨 Second Wind
                    </div>
                    <div class="resource-bar">
                        <div class="resource-fill" style="width: ${secondWindPercentage}%; background: linear-gradient(90deg, #4ecdc4 0%, #44a08d 100%);">
                            ${this.secondWindUsed ? 'Used' : 'Available'}
                        </div>
                    </div>
                    <div class="resource-buttons">
                        <button id="second-wind-btn" ${this.secondWindUsed ? 'disabled' : ''}>
                            Use Second Wind
                        </button>
                        <button id="short-rest-btn">
                            Short Rest
                        </button>
                    </div>
                </div>

                <!-- Action Surge -->
                <div class="resource-tracker">
                    <div class="resource-name">
                        ⚡ Action Surge
                    </div>
                    <div class="resource-bar">
                        <div class="resource-fill" style="width: ${actionSurgePercentage}%; background: linear-gradient(90deg, #ffd93d 0%, #ffb347 100%);">
                            ${this.actionSurgeUses}/${this.actionSurgeMaxUses}
                        </div>
                    </div>
                    <div class="resource-buttons">
                        <button id="action-surge-btn" ${this.actionSurgeUses >= this.actionSurgeMaxUses ? 'disabled' : ''}>
                            Use Action Surge
                        </button>
                        <button id="short-rest-btn-2">
                            Short Rest
                        </button>
                    </div>
                </div>

                <!-- Indomitable -->
                ${this.indomitableMaxUses > 0 ? `
                <div class="resource-tracker">
                    <div class="resource-name">
                        🛡️ Indomitable
                    </div>
                    <div class="resource-bar">
                        <div class="resource-fill" style="width: ${indomitablePercentage}%; background: linear-gradient(90deg, #6a89cc 0%, #4a69bd 100%);">
                            ${this.indomitableUses}/${this.indomitableMaxUses}
                        </div>
                    </div>
                    <div class="resource-buttons">
                        <button id="indomitable-btn" ${this.indomitableUses >= this.indomitableMaxUses ? 'disabled' : ''}>
                            Use Indomitable
                        </button>
                        <button id="long-rest-btn">
                            Long Rest
                        </button>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    renderFightingStyles() {
        const styleBenefits = {
            'Archery': '+2 to attack rolls with ranged weapons',
            'Defense': '+1 AC while wearing armor',
            'Dueling': '+2 damage with one-handed melee weapons (no other weapons)',
            'Great Weapon Fighting': 'Reroll 1s and 2s on damage dice for two-handed weapons',
            'Protection': 'Use reaction to impose disadvantage on attack against ally within 5ft (shield required)',
            'Two-Weapon Fighting': 'Add ability modifier to damage of off-hand attack'
        };

        let stylesHtml = this.fightingStyles.map(style => `
            <div class="fighting-style-card">
                <div class="fighting-style-name">${style}</div>
                <div class="fighting-style-desc">${styleBenefits[style] || 'No description available'}</div>
            </div>
        `).join('');

        // Show additional fighting style option for Champion at level 10
        const canChooseAdditionalStyle = this.subclass === 'Champion' && 
                                       this.level >= 10 && 
                                       this.fightingStyles.length < 2;

        if (canChooseAdditionalStyle) {
            stylesHtml += `
                <div class="fighting-style-selector">
                    <div class="fighting-style-name">➕ Additional Fighting Style</div>
                    <select id="additional-style-select">
                        <option value="">Choose a second fighting style...</option>
                        ${Object.keys(styleBenefits).map(style => 
                            !this.fightingStyles.includes(style) ? 
                            `<option value="${style}">${style}</option>` : ''
                        ).join('')}
                    </select>
                    <button id="add-style-btn">Add Style</button>
                </div>
            `;
        }

        // Show critical range for Champion
        let championFeatures = '';
        if (this.subclass === 'Champion') {
            const critRange = this.getCriticalRange();
            championFeatures = `
                <div class="champion-features">
                    <div class="calculation-display">
                        <div class="ability-card-name">🎯 Improved Critical</div>
                        <div class="calculation-result">
                            Critical Hit: ${critRange}
                        </div>
                    </div>
                    ${this.level >= 7 ? `
                    <div class="calculation-display">
                        <div class="ability-card-name">🏃 Remarkable Athlete</div>
                        <div class="calculation-formula">
                            +${this.getRemarkableAthleteBonus()} to STR/DEX/CON checks without proficiency
                        </div>
                    </div>
                    ` : ''}
                    ${this.level >= 18 ? `
                    <div class="calculation-display">
                        <div class="ability-card-name">❤️ Survivor</div>
                        <div class="calculation-formula">
                            Regain 5 + CON mod HP at start of turn if below half HP
                        </div>
                    </div>
                    ` : ''}
                </div>
            `;
        }

        return `
            <div class="fighting-styles-section">
                <div class="section-header">Fighting Styles</div>
                <div class="fighting-styles-grid">
                    ${stylesHtml}
                </div>
                ${championFeatures}
            </div>
        `;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Fighting Style', desc: this.fightingStyles.join(', ') || 'Choose a style' },
            { level: 1, name: 'Second Wind', desc: 'Bonus action to heal 1d10 + level, once per short rest' },
            { level: 2, name: 'Action Surge', desc: `Take one additional action, ${this.actionSurgeMaxUses} use(s) per short rest` },
            { level: 3, name: 'Martial Archetype', desc: this.subclass || 'Choose your archetype' },
            { level: 4, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 5, name: 'Extra Attack', desc: `Attack ${this.extraAttacks} times when you take the Attack action` },
            { level: 6, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 7, name: 'Archetype Feature', desc: this.getArchetypeFeatureDesc(7) },
            { level: 8, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 9, name: 'Indomitable', desc: `Reroll a failed saving throw, ${this.indomitableMaxUses} use(s) per long rest` },
            { level: 10, name: 'Archetype Feature', desc: this.getArchetypeFeatureDesc(10) },
            { level: 11, name: 'Extra Attack (2)', desc: 'Attack 3 times when you take the Attack action' },
            { level: 12, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 13, name: 'Indomitable (2 uses)', desc: 'Reroll failed saves twice per long rest' },
            { level: 14, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 15, name: 'Archetype Feature', desc: this.getArchetypeFeatureDesc(15) },
            { level: 16, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 17, name: 'Action Surge (2 uses)', desc: 'Use Action Surge twice per short rest' },
            { level: 17, name: 'Indomitable (3 uses)', desc: 'Reroll failed saves three times per long rest' },
            { level: 18, name: 'Archetype Feature', desc: this.getArchetypeFeatureDesc(18) },
            { level: 19, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two abilities' },
            { level: 20, name: 'Extra Attack (3)', desc: 'Attack 4 times when you take the Attack action' }
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

    getArchetypeFeatureDesc(level) {
        if (this.subclass === 'Champion') {
            switch(level) {
                case 3: return 'Improved Critical: Critical hit on 19-20';
                case 7: return 'Remarkable Athlete: Half proficiency to STR/DEX/CON checks';
                case 10: return 'Additional Fighting Style: Choose a second style';
                case 15: return 'Superior Critical: Critical hit on 18-20';
                case 18: return 'Survivor: Regain HP when below half HP';
                default: return 'Archetype feature';
            }
        } else if (this.subclass === 'Battle Master') {
            switch(level) {
                case 3: return 'Combat Superiority: Learn maneuvers and superiority dice';
                case 7: return 'Know Your Enemy: Insight into creature abilities';
                case 10: return 'Improved Combat Superiority: d10 superiority dice';
                case 15: return 'Relentless: Regain superiority dice when initiative rolled';
                case 18: return 'd12 superiority dice';
                default: return 'Archetype feature';
            }
        } else if (this.subclass === 'Eldritch Knight') {
            switch(level) {
                case 3: return 'Spellcasting: Learn wizard spells';
                case 7: return 'War Magic: Cast cantrip and make weapon attack';
                case 10: return 'Eldritch Strike: Disadvantage on saves against your spells';
                case 15: return 'Arcane Charge: Teleport when using Action Surge';
                case 18: return 'Improved War Magic: Attack after casting spell';
                default: return 'Archetype feature';
            }
        }
        return 'Choose archetype at level 3';
    }

    attachEventListeners() {
        // Second Wind
        const secondWindBtn = document.getElementById('second-wind-btn');
        if (secondWindBtn) {
            secondWindBtn.addEventListener('click', () => this.useSecondWind());
        }

        // Action Surge
        const actionSurgeBtn = document.getElementById('action-surge-btn');
        if (actionSurgeBtn) {
            actionSurgeBtn.addEventListener('click', () => this.useActionSurge());
        }

        // Indomitable
        const indomitableBtn = document.getElementById('indomitable-btn');
        if (indomitableBtn) {
            indomitableBtn.addEventListener('click', () => this.useIndomitable());
        }

        // Short Rest buttons
        const shortRestBtns = document.querySelectorAll('#short-rest-btn, #short-rest-btn-2');
        shortRestBtns.forEach(btn => {
            if (btn) btn.addEventListener('click', () => this.shortRest());
        });

        // Long Rest
        const longRestBtn = document.getElementById('long-rest-btn');
        if (longRestBtn) {
            longRestBtn.addEventListener('click', () => this.longRest());
        }

        // Additional Fighting Style (Champion)
        const addStyleBtn = document.getElementById('add-style-btn');
        if (addStyleBtn) {
            addStyleBtn.addEventListener('click', () => this.addAdditionalStyle());
        }
    }

    useSecondWind() {
        if (this.secondWindUsed) return;

        const healing = Math.floor(Math.random() * 10) + 1 + this.level; // 1d10 + level
        this.secondWindUsed = true;
        this.render();
        
        this.showNotification(`💨 Second Wind healed ${healing} HP!`);
        
        // In a real implementation, you'd update the character's HP here
        // this.character.hp = Math.min(this.character.hp + healing, this.character.maxHp);
    }

    useActionSurge() {
        if (this.actionSurgeUses >= this.actionSurgeMaxUses) return;

        this.actionSurgeUses++;
        this.render();
        
        this.showNotification('⚡ Action Surge activated! Take an additional action this turn.');
    }

    useIndomitable() {
        if (this.indomitableUses >= this.indomitableMaxUses) return;

        this.indomitableUses++;
        this.render();
        
        this.showNotification('🛡️ Indomitable activated! Reroll a failed saving throw.');
    }

    shortRest() {
        this.secondWindUsed = false;
        this.actionSurgeUses = 0;
        this.render();
        
        this.showNotification('✨ Short rest completed. Second Wind and Action Surge restored!');
    }

    longRest() {
        this.secondWindUsed = false;
        this.actionSurgeUses = 0;
        this.indomitableUses = 0;
        this.render();
        
        this.showNotification('🌙 Long rest completed. All features restored!');
    }

    addAdditionalStyle() {
        const select = document.getElementById('additional-style-select');
        if (!select || !select.value) return;

        const newStyle = select.value;
        if (this.fightingStyles.includes(newStyle)) {
            this.showNotification('You already have that fighting style!');
            return;
        }

        this.fightingStyles.push(newStyle);
        this.render();
        
        this.showNotification(`🎯 Added ${newStyle} fighting style!`);
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
        this.updateProgression();
        this.render();
    }

    setSubclass(subclass) {
        this.subclass = subclass;
        this.render();
    }

    setFightingStyles(styles) {
        this.fightingStyles = styles;
        this.render();
    }
}

// Export for global use
window.FighterFeatureManager = FighterFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Fighter') {
        window.fighterManager = new FighterFeatureManager();
    }
});