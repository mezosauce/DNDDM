/**
 * Paladin Class Features UI
 * Handles Paladin-specific displays: Divine Sense, Lay on Hands, Spellcasting, Auras, Feature Tree
 */

class PaladinFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Paladin');
        this.divineSenseUsed = 0;
        this.divineSenseUses = 1;
        this.layOnHandsRemaining = 5;
        this.layOnHandsPool = 5;
        this.channelDivinityUsed = 0;
        this.channelDivinityUses = 1;
        this.cleansingTouchRemaining = 0;
        this.cleansingTouchUses = 0;
        this.stats = { strength: 10, dexterity: 10, constitution: 10, charisma: 10 };
        this.spellSlots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0};
        this.maxSpellSlots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0};
        this.sacredOath = '';
        this.fightingStyle = '';
    }

    initialize(level, stats, sacredOath = '', fightingStyle = '') {
        this.level = level;
        this.stats = stats || this.stats;
        this.sacredOath = sacredOath;
        this.fightingStyle = fightingStyle;
        this.updateFeatureProgression();
        this.render();
    }

    updateFeatureProgression() {
        // Divine Sense uses: 1 + CHA mod
        this.divineSenseUses = Math.max(1, 1 + calculateModifier(this.stats.charisma));

        // Lay on Hands pool: level × 5
        this.layOnHandsPool = this.level * 5;
        if (this.layOnHandsRemaining > this.layOnHandsPool) {
            this.layOnHandsRemaining = this.layOnHandsPool;
        }

        // Update spell slots based on level
        this.updateSpellSlots();

        // Channel Divinity uses
        if (this.level >= 18) this.channelDivinityUses = 3;
        else if (this.level >= 6) this.channelDivinityUses = 2;
        else this.channelDivinityUses = 1;

        // Cleansing Touch uses (level 14+)
        if (this.level >= 14) {
            this.cleansingTouchUses = Math.max(1, calculateModifier(this.stats.charisma));
            if (this.cleansingTouchRemaining > this.cleansingTouchUses) {
                this.cleansingTouchRemaining = this.cleansingTouchUses;
            }
        }
    }

    updateSpellSlots() {
        const slotProgression = {
            1: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            2: {1: 2, 2: 0, 3: 0, 4: 0, 5: 0},
            3: {1: 3, 2: 0, 3: 0, 4: 0, 5: 0},
            4: {1: 3, 2: 0, 3: 0, 4: 0, 5: 0},
            5: {1: 4, 2: 2, 3: 0, 4: 0, 5: 0},
            6: {1: 4, 2: 2, 3: 0, 4: 0, 5: 0},
            7: {1: 4, 2: 3, 3: 0, 4: 0, 5: 0},
            8: {1: 4, 2: 3, 3: 0, 4: 0, 5: 0},
            9: {1: 4, 2: 3, 3: 2, 4: 0, 5: 0},
            10: {1: 4, 2: 3, 3: 2, 4: 0, 5: 0},
            11: {1: 4, 2: 3, 3: 3, 4: 0, 5: 0},
            12: {1: 4, 2: 3, 3: 3, 4: 0, 5: 0},
            13: {1: 4, 2: 3, 3: 3, 4: 1, 5: 0},
            14: {1: 4, 2: 3, 3: 3, 4: 1, 5: 0},
            15: {1: 4, 2: 3, 3: 3, 4: 2, 5: 0},
            16: {1: 4, 2: 3, 3: 3, 4: 2, 5: 0},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}
        };

        if (slotProgression[this.level]) {
            this.maxSpellSlots = {...slotProgression[this.level]};
            // Only update current slots if they're at default (all zeros)
            if (Object.values(this.spellSlots).every(v => v === 0)) {
                this.spellSlots = {...slotProgression[this.level]};
            }
        }
    }

    getSpellSaveDC() {
        return 8 + this.getProficiencyBonus() + calculateModifier(this.stats.charisma);
    }

    getSpellAttackBonus() {
        return this.getProficiencyBonus() + calculateModifier(this.stats.charisma);
    }

    getAuraOfProtectionBonus() {
        return Math.max(1, calculateModifier(this.stats.charisma));
    }

    calculateDivineSmiteDamage(spellSlotLevel, isUndeadOrFiend = false) {
        let damageDice = 2 + (spellSlotLevel - 1);
        damageDice = Math.min(damageDice, 5);
        
        if (isUndeadOrFiend) {
            damageDice += 1;
        }
        
        return {
            dice: damageDice,
            description: `${damageDice}d8 radiant damage${isUndeadOrFiend ? ' (extra vs undead/fiend)' : ''}`
        };
    }

    render() {
        const container = document.getElementById('paladin-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    ✨ Paladin Features
                </div>
                
                ${this.renderDivineSenseTracker()}
                ${this.renderLayOnHandsTracker()}
                ${this.renderChannelDivinityTracker()}
                ${this.renderSpellcastingDisplay()}
                ${this.renderFightingStyleDisplay()}
                ${this.renderAurasDisplay()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderDivineSenseTracker() {
        const percentage = ((this.divineSenseUses - this.divineSenseUsed) / this.divineSenseUses) * 100;
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    🔮 Divine Sense
                </div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #9370db 0%, #8a2be2 100%);">
                        ${this.divineSenseUsed}/${this.divineSenseUses}
                    </div>
                </div>
                <div class="resource-buttons">
                    <button id="divine-sense-btn" ${this.divineSenseUsed >= this.divineSenseUses ? 'disabled' : ''}>
                        Use Divine Sense
                    </button>
                    <button id="divine-sense-reset-btn">
                        Long Rest
                    </button>
                </div>
                <div class="calculation-formula" style="margin-top: 5px; font-size: 0.9em;">
                    Detects celestials, fiends, undead within 60ft (1 min)
                </div>
            </div>
        `;
    }

    renderLayOnHandsTracker() {
        const percentage = (this.layOnHandsRemaining / this.layOnHandsPool) * 100;
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    🙏 Lay on Hands
                </div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #32cd32 0%, #228b22 100%);">
                        ${this.layOnHandsRemaining}/${this.layOnHandsPool} HP
                    </div>
                </div>
                <div class="resource-buttons">
                    <button id="lay-on-hands-heal-btn" ${this.layOnHandsRemaining <= 0 ? 'disabled' : ''}>
                        Heal
                    </button>
                    <button id="lay-on-hands-cure-btn" ${this.layOnHandsRemaining < 5 ? 'disabled' : ''}>
                        Cure Disease/Poison
                    </button>
                    <button id="lay-on-hands-reset-btn">
                        Reset Pool
                    </button>
                </div>
                <div class="calculation-formula" style="margin-top: 5px; font-size: 0.9em;">
                    ${this.level} × 5 = ${this.layOnHandsPool} HP pool | 5 HP per disease/poison
                </div>
            </div>
        `;
    }

    renderChannelDivinityTracker() {
        if (this.level < 3) return '';

        const percentage = ((this.channelDivinityUses - this.channelDivinityUsed) / this.channelDivinityUses) * 100;
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    ☀️ Channel Divinity
                </div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #ffd700 0%, #ff8c00 100%);">
                        ${this.channelDivinityUsed}/${this.channelDivinityUses}
                    </div>
                </div>
                <div class="resource-buttons">
                    <button id="channel-divinity-btn" ${this.channelDivinityUsed >= this.channelDivinityUses ? 'disabled' : ''}>
                        Use Channel Divinity
                    </button>
                    <button id="channel-divinity-reset-btn">
                        Short Rest
                    </button>
                </div>
                ${this.sacredOath === 'Oath of Devotion' ? this.renderDevotionOptions() : ''}
            </div>
        `;
    }

    renderDevotionOptions() {
        return `
            <div class="calculation-display" style="margin-top: 10px;">
                <strong style="color: #ffd700;">Oath of Devotion Options:</strong>
                <div class="calculation-formula">
                    • <strong>Sacred Weapon:</strong> +CHA to attack, magical, emits light<br>
                    • <strong>Turn the Unholy:</strong> Turn fiends/undead (WIS save)
                </div>
            </div>
        `;
    }

    renderSpellcastingDisplay() {
        if (this.level < 2) return '';

        const totalSlots = Object.values(this.spellSlots).reduce((a, b) => a + b, 0);
        const totalMaxSlots = Object.values(this.maxSpellSlots).reduce((a, b) => a + b, 0);
        
        return `
            <div class="calculation-display">
                <div class="ability-card-name"> Spellcasting</div>
                <div class="spell-slots-grid">
                    ${Object.entries(this.spellSlots).map(([level, slots]) => `
                        ${this.maxSpellSlots[level] > 0 ? `
                            <div class="spell-slot-level">
                                <div class="spell-slot-label">${level}</div>
                                <div class="spell-slot-counter">
                                    <button class="spell-slot-minus" data-level="${level}">-</button>
                                    <span class="spell-slot-count">${slots}</span>
                                    <button class="spell-slot-plus" data-level="${level}">+</button>
                                </div>
                                <div class="spell-slot-max">/ ${this.maxSpellSlots[level]}</div>
                            </div>
                        ` : ''}
                    `).join('')}
                </div>
                <div class="calculation-formula">
                    Spell Save DC: ${this.getSpellSaveDC()} | Attack: +${this.getSpellAttackBonus()}
                </div>
                <div class="calculation-formula">
                    Prepared Spells: ${Math.max(1, calculateModifier(this.stats.charisma) + Math.floor(this.level / 2))}
                </div>
                ${this.renderDivineSmiteCalculator()}
            </div>
        `;
    }

    renderDivineSmiteCalculator() {
        if (this.level < 2) return '';

        return `
            <div class="calculation-display" style="margin-top: 10px;">
                <strong style="color: #ff4500;">Divine Smite Damage:</strong>
                <div class="divine-smite-grid">
                    ${[1, 2, 3, 4, 5].map(level => {
                        if (this.maxSpellSlots[level] === 0) return '';
                        const normal = this.calculateDivineSmiteDamage(level, false);
                        const vsUndead = this.calculateDivineSmiteDamage(level, true);
                        return `
                            <div class="divine-smite-level">
                                <div>Level ${level}:</div>
                                <div>${normal.dice}d8</div>
                                <div>${vsUndead.dice}d8 vs evil</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    renderFightingStyleDisplay() {
        if (this.level < 2 || !this.fightingStyle) return '';

        const styleDescriptions = {
            'Defense': '+1 AC while wearing armor',
            'Dueling': '+2 damage with one-handed weapon',
            'Great Weapon Fighting': 'Reroll 1s and 2s on two-handed weapons',
            'Protection': 'Impose disadvantage with shield'
        };

        return `
            <div class="calculation-display">
                <div class="ability-card-name"> ${this.fightingStyle}</div>
                <div class="calculation-formula">
                    ${styleDescriptions[this.fightingStyle] || 'Combat style specialty'}
                </div>
            </div>
        `;
    }

    renderAurasDisplay() {
        const auras = [];
        
        if (this.level >= 6) {
            auras.push({
                name: 'Aura of Protection',
                range: this.level >= 18 ? 30 : 10,
                description: `+${this.getAuraOfProtectionBonus()} to saving throws for allies`
            });
        }
        
        if (this.level >= 10) {
            auras.push({
                name: 'Aura of Courage',
                range: this.level >= 18 ? 30 : 10,
                description: 'Immunity to frightened condition'
            });
        }
        
        if (this.level >= 7 && this.sacredOath === 'Oath of Devotion') {
            auras.push({
                name: 'Aura of Devotion',
                range: this.level >= 18 ? 30 : 10,
                description: 'Immunity to charmed condition'
            });
        }

        if (auras.length === 0) return '';

        return `
            <div class="calculation-display">
                <div class="ability-card-name">🛡️ Divine Auras</div>
                ${auras.map(aura => `
                    <div class="calculation-formula">
                        <strong>${aura.name}</strong> (${aura.range}ft): ${aura.description}
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Divine Sense', desc: `Detect celestials/fiends/undead (${this.divineSenseUses}/day)` },
            { level: 1, name: 'Lay on Hands', desc: `${this.layOnHandsPool} HP healing pool, cure diseases` },
            { level: 2, name: 'Fighting Style', desc: this.fightingStyle || 'Choose combat specialty' },
            { level: 2, name: 'Spellcasting', desc: 'Cast paladin spells using CHA' },
            { level: 2, name: 'Divine Smite', desc: 'Expend spell slots for radiant damage' },
            { level: 3, name: 'Divine Health', desc: 'Immunity to disease' },
            { level: 3, name: 'Sacred Oath', desc: this.sacredOath || 'Swear your sacred oath' },
            { level: 4, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two' },
            { level: 5, name: 'Extra Attack', desc: 'Attack twice when taking Attack action' },
            { level: 6, name: 'Aura of Protection', desc: `+${this.getAuraOfProtectionBonus()} to saves for allies` },
            { level: 7, name: 'Sacred Oath Feature', desc: this.sacredOath ? `${this.sacredOath} feature` : 'Oath feature' },
            { level: 8, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two' },
            { level: 9, name: '3rd-level Spell Slots', desc: 'Access to higher level spells' },
            { level: 10, name: 'Aura of Courage', desc: 'Immunity to frightened condition' },
            { level: 11, name: 'Improved Divine Smite', desc: '+1d8 radiant damage on melee attacks' },
            { level: 12, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two' },
            { level: 13, name: '4th-level Spell Slots', desc: 'Access to higher level spells' },
            { level: 14, name: 'Cleansing Touch', desc: `${this.cleansingTouchUses} uses to end spells` },
            { level: 15, name: 'Sacred Oath Feature', desc: this.sacredOath ? `${this.sacredOath} feature` : 'Oath feature' },
            { level: 16, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two' },
            { level: 17, name: '5th-level Spell Slots', desc: 'Access to highest level spells' },
            { level: 18, name: 'Aura Improvements', desc: 'Aura ranges increase to 30ft' },
            { level: 19, name: 'Ability Score Improvement', desc: '+2 to one ability or +1 to two' },
            { level: 20, name: 'Sacred Oath Feature', desc: this.sacredOath ? `${this.sacredOath} capstone` : 'Oath capstone' }
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

    attachEventListeners() {
        // Divine Sense
        const divineSenseBtn = document.getElementById('divine-sense-btn');
        const divineSenseResetBtn = document.getElementById('divine-sense-reset-btn');

        if (divineSenseBtn) {
            divineSenseBtn.addEventListener('click', () => this.useDivineSense());
        }
        if (divineSenseResetBtn) {
            divineSenseResetBtn.addEventListener('click', () => this.longRest());
        }

        // Lay on Hands
        const layOnHandsHealBtn = document.getElementById('lay-on-hands-heal-btn');
        const layOnHandsCureBtn = document.getElementById('lay-on-hands-cure-btn');
        const layOnHandsResetBtn = document.getElementById('lay-on-hands-reset-btn');

        if (layOnHandsHealBtn) {
            layOnHandsHealBtn.addEventListener('click', () => this.useLayOnHandsHeal());
        }
        if (layOnHandsCureBtn) {
            layOnHandsCureBtn.addEventListener('click', () => this.useLayOnHandsCure());
        }
        if (layOnHandsResetBtn) {
            layOnHandsResetBtn.addEventListener('click', () => this.resetLayOnHands());
        }

        // Channel Divinity
        const channelDivinityBtn = document.getElementById('channel-divinity-btn');
        const channelDivinityResetBtn = document.getElementById('channel-divinity-reset-btn');

        if (channelDivinityBtn) {
            channelDivinityBtn.addEventListener('click', () => this.useChannelDivinity());
        }
        if (channelDivinityResetBtn) {
            channelDivinityResetBtn.addEventListener('click', () => this.shortRest());
        }

        // Spell slots
        document.querySelectorAll('.spell-slot-minus').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = e.target.dataset.level;
                this.useSpellSlot(parseInt(level));
            });
        });

        document.querySelectorAll('.spell-slot-plus').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = e.target.dataset.level;
                this.regainSpellSlot(parseInt(level));
            });
        });
    }

    useDivineSense() {
        if (this.divineSenseUsed >= this.divineSenseUses) return;
        
        this.divineSenseUsed++;
        this.render();
        
        this.showNotification('🔮 Divine Sense activated! Detecting celestials, fiends, and undead within 60ft.');
    }

    useLayOnHandsHeal() {
        if (this.layOnHandsRemaining <= 0) return;
        
        const healAmount = prompt(`How many HP to heal? (Available: ${this.layOnHandsRemaining})`);
        const amount = parseInt(healAmount);
        
        if (amount && amount > 0 && amount <= this.layOnHandsRemaining) {
            this.layOnHandsRemaining -= amount;
            this.render();
            this.showNotification(`🙏 Healed ${amount} HP using Lay on Hands.`);
        }
    }

    useLayOnHandsCure() {
        if (this.layOnHandsRemaining < 5) {
            this.showNotification('Not enough healing power (need 5 HP to cure disease/poison).');
            return;
        }
        
        this.layOnHandsRemaining -= 5;
        this.render();
        this.showNotification('🙏 Cured one disease or neutralized one poison.');
    }

    resetLayOnHands() {
        this.layOnHandsRemaining = this.layOnHandsPool;
        this.render();
        this.showNotification('✨ Lay on Hands pool reset to full.');
    }

    useChannelDivinity() {
        if (this.channelDivinityUsed >= this.channelDivinityUses) return;
        
        this.channelDivinityUsed++;
        this.render();
        
        if (this.sacredOath === 'Oath of Devotion') {
            this.showNotification('☀️ Channel Divinity used! Choose: Sacred Weapon or Turn the Unholy.');
        } else {
            this.showNotification('☀️ Channel Divinity activated!');
        }
    }

    useSpellSlot(level) {
        if (this.spellSlots[level] <= 0) return;
        
        this.spellSlots[level]--;
        this.render();
        this.showNotification(` Used level ${level} spell slot.`);
    }

    regainSpellSlot(level) {
        if (this.spellSlots[level] >= this.maxSpellSlots[level]) return;
        
        this.spellSlots[level]++;
        this.render();
        this.showNotification(` Regained level ${level} spell slot.`);
    }

    longRest() {
        this.divineSenseUsed = 0;
        this.layOnHandsRemaining = this.layOnHandsPool;
        this.channelDivinityUsed = 0;
        this.cleansingTouchRemaining = this.cleansingTouchUses;
        
        // Reset spell slots
        for (const level in this.spellSlots) {
            this.spellSlots[level] = this.maxSpellSlots[level];
        }
        
        this.render();
        this.showNotification('✨ Long rest completed! All features restored.');
    }

    shortRest() {
        this.channelDivinityUsed = 0;
        this.render();
        this.showNotification('💫 Short rest completed! Channel Divinity restored.');
    }

    showNotification(message) {
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
        this.updateFeatureProgression();
        this.render();
    }

    setLevel(level) {
        this.level = parseInt(level) || 1;
        this.updateFeatureProgression();
        this.render();
    }

    setSacredOath(sacredOath) {
        this.sacredOath = sacredOath;
        this.render();
    }

    setFightingStyle(fightingStyle) {
        this.fightingStyle = fightingStyle;
        this.render();
    }

    getProficiencyBonus() {
        if (this.level < 5) return 2;
        else if (this.level < 9) return 3;
        else if (this.level < 13) return 4;
        else if (this.level < 17) return 5;
        else return 6;
    }
}

// Export for global use
window.PaladinFeatureManager = PaladinFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Paladin') {
        window.paladinManager = new PaladinFeatureManager();
    }
});