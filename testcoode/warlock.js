/**
 * Warlock Class Features UI
 * Handles Warlock-specific displays: Pact Magic, Eldritch Invocations, Patron Features
 */

class WarlockFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Warlock');
        this.spellSlotsUsed = 0;
        this.spellSlots = 1;
        this.spellSlotLevel = 1;
        this.cantripsKnown = 2;
        this.spellsKnown = 2;
        this.invocationsKnown = 0;
        this.currentInvocations = new Set();
        this.stats = { charisma: 10, constitution: 10, dexterity: 10 };
        this.patron = '';
        this.pactBoon = '';
        
        // Mystic Arcanum tracking
        this.mysticArcanum = {
            6: { spell: '', used: false },
            7: { spell: '', used: false },
            8: { spell: '', used: false },
            9: { spell: '', used: false }
        };
        
        // Fiend patron features
        this.temporaryHP = 0;
        this.darkOnesLuckUsed = false;
        this.fiendishResistance = '';
        this.hurlThroughHellUsed = false;
        
        // Pact features
        this.hasFamiliar = false;
        this.familiarForm = '';
        this.pactWeapon = '';
        this.bookOfShadows = false;
        this.tomeCantrips = new Set();
    }

    initialize(level, stats, patron = '', pactBoon = '') {
        this.level = level;
        this.stats = stats || this.stats;
        this.patron = patron;
        this.pactBoon = pactBoon;
        this.updateSpellProgression();
        this.updatePactFeatures();
        this.render();
    }

    updateSpellProgression() {
        const progression = {
            1: { slots: 1, slotLevel: 1, cantrips: 2, spells: 2, invocations: 0 },
            2: { slots: 2, slotLevel: 1, cantrips: 2, spells: 3, invocations: 2 },
            3: { slots: 2, slotLevel: 2, cantrips: 2, spells: 4, invocations: 2 },
            4: { slots: 2, slotLevel: 2, cantrips: 3, spells: 5, invocations: 2 },
            5: { slots: 2, slotLevel: 3, cantrips: 3, spells: 6, invocations: 3 },
            6: { slots: 2, slotLevel: 3, cantrips: 3, spells: 7, invocations: 3 },
            7: { slots: 2, slotLevel: 4, cantrips: 3, spells: 8, invocations: 4 },
            8: { slots: 2, slotLevel: 4, cantrips: 3, spells: 9, invocations: 4 },
            9: { slots: 2, slotLevel: 5, cantrips: 3, spells: 10, invocations: 5 },
            10: { slots: 2, slotLevel: 5, cantrips: 4, spells: 10, invocations: 5 },
            11: { slots: 3, slotLevel: 5, cantrips: 4, spells: 11, invocations: 5 },
            12: { slots: 3, slotLevel: 5, cantrips: 4, spells: 11, invocations: 6 },
            13: { slots: 3, slotLevel: 5, cantrips: 4, spells: 12, invocations: 6 },
            14: { slots: 3, slotLevel: 5, cantrips: 4, spells: 12, invocations: 6 },
            15: { slots: 3, slotLevel: 5, cantrips: 4, spells: 13, invocations: 7 },
            16: { slots: 3, slotLevel: 5, cantrips: 4, spells: 13, invocations: 7 },
            17: { slots: 4, slotLevel: 5, cantrips: 4, spells: 14, invocations: 7 },
            18: { slots: 4, slotLevel: 5, cantrips: 4, spells: 14, invocations: 8 },
            19: { slots: 4, slotLevel: 5, cantrips: 4, spells: 15, invocations: 8 },
            20: { slots: 4, slotLevel: 5, cantrips: 4, spells: 15, invocations: 8 }
        };

        const features = progression[this.level] || progression[1];
        this.spellSlots = features.slots;
        this.spellSlotLevel = features.slotLevel;
        this.cantripsKnown = features.cantrips;
        this.spellsKnown = features.spells;
        this.invocationsKnown = features.invocations;
    }

    updatePactFeatures() {
        // Enable Pact Boon at level 3
        if (this.level >= 3 && this.pactBoon) {
            if (this.pactBoon === 'Pact of the Chain') {
                this.hasFamiliar = true;
                if (!this.familiarForm) this.familiarForm = 'Imp';
            } else if (this.pactBoon === 'Pact of the Tome') {
                this.bookOfShadows = true;
            }
        }

        // Enable Mystic Arcanum at appropriate levels
        if (this.level >= 11 && !this.mysticArcanum[6].spell) {
            this.mysticArcanum[6].spell = 'Choose 6th-level spell';
        }
        if (this.level >= 13 && !this.mysticArcanum[7].spell) {
            this.mysticArcanum[7].spell = 'Choose 7th-level spell';
        }
        if (this.level >= 15 && !this.mysticArcanum[8].spell) {
            this.mysticArcanum[8].spell = 'Choose 8th-level spell';
        }
        if (this.level >= 17 && !this.mysticArcanum[9].spell) {
            this.mysticArcanum[9].spell = 'Choose 9th-level spell';
        }
    }

    calculateSpellSaveDC() {
        const chaMod = calculateModifier(this.stats.charisma);
        return 8 + this.getProficiencyBonus() + chaMod;
    }

    calculateSpellAttack() {
        const chaMod = calculateModifier(this.stats.charisma);
        return this.getProficiencyBonus() + chaMod;
    }

    getProficiencyBonus() {
        if (this.level < 5) return 2;
        if (this.level < 9) return 3;
        if (this.level < 13) return 4;
        if (this.level < 17) return 5;
        return 6;
    }

    render() {
        const container = document.getElementById('warlock-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    🔮 Warlock Features
                </div>
                
                ${this.renderPatronDisplay()}
                ${this.renderPactMagicTracker()}
                ${this.renderEldritchInvocations()}
                ${this.renderMysticArcanum()}
                ${this.renderPactFeatures()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderPatronDisplay() {
        if (!this.patron) return '';
        
        let patronFeatures = '';
        if (this.patron === 'The Fiend') {
            patronFeatures = `
                <div class="patron-features">
                    <div class="feature-name">The Fiend Features:</div>
                    <div class="feature-desc">
                        • Dark One's Blessing: ${this.temporaryHP} temporary HP<br>
                        • Dark One's Own Luck: ${this.darkOnesLuckUsed ? 'USED' : 'AVAILABLE'}<br>
                        • Fiendish Resilience: ${this.fiendishResistance || 'Not set'}<br>
                        • Hurl Through Hell: ${this.hurlThroughHellUsed ? 'USED' : 'AVAILABLE'}
                    </div>
                </div>
            `;
        }

        return `
            <div class="calculation-display">
                <div class="ability-card-name">👁️ Otherworldly Patron</div>
                <div class="calculation-formula">
                    ${this.patron}
                </div>
                ${patronFeatures}
            </div>
        `;
    }

    renderPactMagicTracker() {
        const percentage = ((this.spellSlots - this.spellSlotsUsed) / this.spellSlots) * 100;
        const spellSaveDC = this.calculateSpellSaveDC();
        const spellAttack = this.calculateSpellAttack();
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    ✨ Pact Magic
                </div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #9b59b6 0%, #8e44ad 100%);">
                        ${this.spellSlotsUsed}/${this.spellSlots} (Level ${this.spellSlotLevel})
                    </div>
                </div>
                <div class="spellcasting-info">
                    <div class="spell-stat">
                        <strong>Spell Save DC:</strong> ${spellSaveDC}
                    </div>
                    <div class="spell-stat">
                        <strong>Spell Attack:</strong> +${spellAttack}
                    </div>
                    <div class="spell-stat">
                        <strong>Cantrips Known:</strong> ${this.cantripsKnown}
                    </div>
                    <div class="spell-stat">
                        <strong>Spells Known:</strong> ${this.spellsKnown}
                    </div>
                </div>
                <div class="resource-buttons">
                    <button id="spell-slot-btn" ${this.spellSlotsUsed >= this.spellSlots ? 'disabled' : ''}>
                        Use Spell Slot
                    </button>
                    <button id="short-rest-btn">
                        Short Rest
                    </button>
                    <button id="long-rest-btn">
                        Long Rest
                    </button>
                    ${this.level >= 20 ? '<button id="eldritch-master-btn">Eldritch Master</button>' : ''}
                </div>
            </div>
        `;
    }

    renderEldritchInvocations() {
        const invocationList = Array.from(this.currentInvocations);
        const availableSlots = this.invocationsKnown - this.currentInvocations.size;
        
        return `
            <div class="calculation-display">
                <div class="ability-card-name"> Eldritch Invocations</div>
                <div class="calculation-formula">
                    Known: ${this.currentInvocations.size}/${this.invocationsKnown}
                    ${availableSlots > 0 ? ` (${availableSlots} available)` : ''}
                </div>
                ${invocationList.length > 0 ? `
                    <div class="invocation-list">
                        ${invocationList.map(inv => `<div class="invocation-item">• ${inv}</div>`).join('')}
                    </div>
                ` : '<div class="feature-desc">No invocations selected</div>'}
                <div class="resource-buttons">
                    <button id="add-invocation-btn" ${availableSlots <= 0 ? 'disabled' : ''}>
                        Add Invocation
                    </button>
                    <button id="remove-invocation-btn" ${invocationList.length === 0 ? 'disabled' : ''}>
                        Remove Invocation
                    </button>
                </div>
            </div>
        `;
    }

    renderMysticArcanum() {
        if (this.level < 11) return '';
        
        const arcanumItems = [];
        for (let level = 6; level <= 9; level++) {
            if (this.mysticArcanum[level].spell) {
                const used = this.mysticArcanum[level].used;
                arcanumItems.push(`
                    <div class="arcanum-item ${used ? 'used' : 'available'}">
                        <div class="arcanum-level">Level ${level}</div>
                        <div class="arcanum-spell">${this.mysticArcanum[level].spell}</div>
                        <div class="arcanum-status">${used ? 'USED' : 'READY'}</div>
                    </div>
                `);
            }
        }

        if (arcanumItems.length === 0) return '';

        return `
            <div class="calculation-display">
                <div class="ability-card-name">🔮 Mystic Arcanum</div>
                <div class="arcanum-container">
                    ${arcanumItems.join('')}
                </div>
            </div>
        `;
    }

    renderPactFeatures() {
        if (!this.pactBoon) return '';

        let pactContent = '';
        switch (this.pactBoon) {
            case 'Pact of the Chain':
                pactContent = `
                    <div class="pact-detail">
                        <strong>Familiar:</strong> ${this.familiarForm}
                    </div>
                    <div class="resource-buttons">
                        <button id="change-familiar-btn">Change Familiar</button>
                    </div>
                `;
                break;
            case 'Pact of the Blade':
                pactContent = `
                    <div class="pact-detail">
                        <strong>Pact Weapon:</strong> ${this.pactWeapon || 'None summoned'}
                    </div>
                    <div class="resource-buttons">
                        <button id="summon-weapon-btn">Summon Weapon</button>
                        <button id="dismiss-weapon-btn" ${!this.pactWeapon ? 'disabled' : ''}>Dismiss</button>
                    </div>
                `;
                break;
            case 'Pact of the Tome':
                const cantripList = Array.from(this.tomeCantrips);
                pactContent = `
                    <div class="pact-detail">
                        <strong>Book of Shadows Cantrips:</strong>
                        ${cantripList.length > 0 ? 
                            `<div class="cantrip-list">${cantripList.map(c => `<div>• ${c}</div>`).join('')}</div>` :
                            '<div>No cantrips added</div>'
                        }
                    </div>
                    <div class="resource-buttons">
                        <button id="add-cantrip-btn" ${this.tomeCantrips.size >= 3 ? 'disabled' : ''}>Add Cantrip</button>
                    </div>
                `;
                break;
        }

        return `
            <div class="calculation-display">
                <div class="ability-card-name">📖 ${this.pactBoon}</div>
                ${pactContent}
            </div>
        `;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Otherworldly Patron', desc: this.patron || 'Choose your patron' },
            { level: 1, name: 'Pact Magic', desc: `${this.spellSlots} slot(s) of ${this.spellSlotLevel}th level` },
            { level: 2, name: 'Eldritch Invocations', desc: `${this.invocationsKnown} invocations known` },
            { level: 3, name: 'Pact Boon', desc: this.pactBoon || 'Choose your pact' },
            { level: 4, name: 'Ability Score Improvement', desc: '' },
            { level: 5, name: 'Pact Magic Improvement', desc: `${this.spellSlots} slots of ${this.spellSlotLevel}th level` },
            { level: 6, name: 'Patron Feature', desc: this.patron ? `${this.patron} feature` : '' },
            { level: 7, name: 'Pact Magic Improvement', desc: `${this.spellSlots} slots of ${this.spellSlotLevel}th level` },
            { level: 8, name: 'Ability Score Improvement', desc: '' },
            { level: 9, name: 'Pact Magic Improvement', desc: `${this.spellSlots} slots of ${this.spellSlotLevel}th level` },
            { level: 10, name: 'Patron Feature', desc: this.patron ? `${this.patron} feature` : '' },
            { level: 11, name: 'Mystic Arcanum (6th)', desc: 'Cast one 6th-level spell per long rest' },
            { level: 12, name: 'Ability Score Improvement', desc: '' },
            { level: 13, name: 'Mystic Arcanum (7th)', desc: 'Cast one 7th-level spell per long rest' },
            { level: 14, name: 'Patron Feature', desc: this.patron ? `${this.patron} feature` : '' },
            { level: 15, name: 'Mystic Arcanum (8th)', desc: 'Cast one 8th-level spell per long rest' },
            { level: 16, name: 'Ability Score Improvement', desc: '' },
            { level: 17, name: 'Mystic Arcanum (9th)', desc: 'Cast one 9th-level spell per long rest' },
            { level: 18, name: 'Pact Magic Improvement', desc: `${this.spellSlots} slots of ${this.spellSlotLevel}th level` },
            { level: 19, name: 'Ability Score Improvement', desc: '' },
            { level: 20, name: 'Eldritch Master', desc: 'Regain all spell slots once per long rest' }
        ];

        let html = '<div class="feature-tree">';
        
        features.forEach(feature => {
            const unlocked = this.isFeatureUnlocked(feature.level);
            html += `
                <div class="feature-node ${unlocked ? 'unlocked' : 'locked'}">
                    <div class="feature-level">Lv ${feature.level}</div>
                    <div style="flex: 1;">
                        <div class="feature-name">${feature.name}</div>
                        ${feature.desc ? `<div class="feature-desc">${feature.desc}</div>` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    attachEventListeners() {
        // Spell slot management
        const spellSlotBtn = document.getElementById('spell-slot-btn');
        const shortRestBtn = document.getElementById('short-rest-btn');
        const longRestBtn = document.getElementById('long-rest-btn');
        const eldritchMasterBtn = document.getElementById('eldritch-master-btn');

        if (spellSlotBtn) spellSlotBtn.addEventListener('click', () => this.useSpellSlot());
        if (shortRestBtn) shortRestBtn.addEventListener('click', () => this.shortRest());
        if (longRestBtn) longRestBtn.addEventListener('click', () => this.longRest());
        if (eldritchMasterBtn) eldritchMasterBtn.addEventListener('click', () => this.eldritchMaster());

        // Invocation management
        const addInvocationBtn = document.getElementById('add-invocation-btn');
        const removeInvocationBtn = document.getElementById('remove-invocation-btn');

        if (addInvocationBtn) addInvocationBtn.addEventListener('click', () => this.addInvocation());
        if (removeInvocationBtn) removeInvocationBtn.addEventListener('click', () => this.removeInvocation());

        // Pact feature management
        const changeFamiliarBtn = document.getElementById('change-familiar-btn');
        const summonWeaponBtn = document.getElementById('summon-weapon-btn');
        const dismissWeaponBtn = document.getElementById('dismiss-weapon-btn');
        const addCantripBtn = document.getElementById('add-cantrip-btn');

        if (changeFamiliarBtn) changeFamiliarBtn.addEventListener('click', () => this.changeFamiliar());
        if (summonWeaponBtn) summonWeaponBtn.addEventListener('click', () => this.summonWeapon());
        if (dismissWeaponBtn) dismissWeaponBtn.addEventListener('click', () => this.dismissWeapon());
        if (addCantripBtn) addCantripBtn.addEventListener('click', () => this.addTomeCantrip());
    }

    useSpellSlot() {
        if (this.spellSlotsUsed >= this.spellSlots) return;
        
        this.spellSlotsUsed++;
        this.render();
        
        this.showNotification(`✨ Used spell slot (${this.spellSlots - this.spellSlotsUsed} remaining)`);
    }

    shortRest() {
        this.spellSlotsUsed = 0;
        this.darkOnesLuckUsed = false;
        this.render();
        
        this.showNotification('🧘 Short rest completed. Spell slots restored!');
    }

    longRest() {
        this.spellSlotsUsed = 0;
        this.darkOnesLuckUsed = false;
        this.hurlThroughHellUsed = false;
        this.temporaryHP = 0;
        
        // Reset Mystic Arcanum
        for (let level in this.mysticArcanum) {
            this.mysticArcanum[level].used = false;
        }
        
        this.render();
        this.showNotification('✨ Long rest completed. All resources restored!');
    }

    eldritchMaster() {
        if (this.level < 20) return;
        
        this.spellSlotsUsed = 0;
        this.render();
        this.showNotification('🔮 Eldritch Master: All spell slots restored!');
    }

    addInvocation() {
        if (this.currentInvocations.size >= this.invocationsKnown) return;
        
        const invocation = prompt('Enter invocation name:');
        if (invocation) {
            this.currentInvocations.add(invocation);
            this.render();
            this.showNotification(` Learned: ${invocation}`);
        }
    }

    removeInvocation() {
        if (this.currentInvocations.size === 0) return;
        
        const invocation = Array.from(this.currentInvocations)[0]; // Remove first one for simplicity
        this.currentInvocations.delete(invocation);
        this.render();
        this.showNotification(` Removed: ${invocation}`);
    }

    changeFamiliar() {
        const forms = ['Imp', 'Pseudodragon', 'Quasit', 'Sprite'];
        const newForm = prompt(`Choose familiar form: ${forms.join(', ')}`, this.familiarForm);
        if (newForm && forms.includes(newForm)) {
            this.familiarForm = newForm;
            this.render();
            this.showNotification(`🐾 Familiar changed to: ${newForm}`);
        }
    }

    summonWeapon() {
        const weapon = prompt('Enter weapon form:', this.pactWeapon || 'Longsword');
        if (weapon) {
            this.pactWeapon = weapon;
            this.render();
            this.showNotification(` Summoned: ${weapon}`);
        }
    }

    dismissWeapon() {
        this.pactWeapon = '';
        this.render();
        this.showNotification(' Pact weapon dismissed');
    }

    addTomeCantrip() {
        if (this.tomeCantrips.size >= 3) return;
        
        const cantrip = prompt('Enter cantrip name:');
        if (cantrip) {
            this.tomeCantrips.add(cantrip);
            this.render();
            this.showNotification(`📖 Added cantrip: ${cantrip}`);
        }
    }

    // Fiend patron methods
    darkOnesBlessing() {
        const chaMod = calculateModifier(this.stats.charisma);
        this.temporaryHP = Math.max(chaMod + this.level, 1);
        this.render();
        this.showNotification(`😈 Dark One's Blessing: +${this.temporaryHP} temporary HP`);
    }

    darkOnesOwnLuck() {
        if (this.darkOnesLuckUsed) return false;
        this.darkOnesLuckUsed = true;
        this.render();
        this.showNotification(' Dark One\'s Own Luck: Added d10 to roll');
        return true;
    }

    setFiendishResistance() {
        const damageType = prompt('Enter damage type to resist:');
        if (damageType) {
            this.fiendishResistance = damageType;
            this.render();
            this.showNotification(`🛡️ Fiendish Resistance: ${damageType}`);
        }
    }

    hurlThroughHell() {
        if (this.hurlThroughHellUsed) return false;
        this.hurlThroughHellUsed = true;
        this.render();
        this.showNotification('🔥 Hurl Through Hell: Target takes 10d10 psychic damage');
        return true;
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
        this.render();
    }

    setLevel(level) {
        this.level = parseInt(level) || 1;
        this.updateSpellProgression();
        this.updatePactFeatures();
        this.render();
    }

    setPatron(patron) {
        this.patron = patron;
        this.render();
    }

    setPactBoon(pactBoon) {
        this.pactBoon = pactBoon;
        this.updatePactFeatures();
        this.render();
    }
}

// Export for global use
window.WarlockFeatureManager = WarlockFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Warlock') {
        window.warlockManager = new WarlockFeatureManager();
    }
});