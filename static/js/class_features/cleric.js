/**
 * Cleric Class Features UI
 * Handles Cleric-specific displays: Spellcasting, Channel Divinity, Divine Domain Features
 */

class ClericFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Cleric');
        this.stats = { strength: 10, dexterity: 10, constitution: 10, intelligence: 10, wisdom: 10, charisma: 10 };
        
        // Spellcasting
        this.cantripsKnown = 3;
        this.spellSlots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0};
        this.spellSlotsUsed = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0};
        this.spellsPrepared = [];
        this.domainSpells = [];
        
        // Channel Divinity
        this.channelDivinityUses = 0;
        this.channelDivinityUsed = 0;
        
        // Domain
        this.divineomain = '';
        this.deity = '';
        
        // Features
        this.destroyUndeadCR = 0;
        this.divineInterventionAvailable = false;
        this.divineInterventionAutoSuccess = false;
    }

    initialize(level, stats, subclass = '', deity = '') {
        this.level = level;
        this.stats = stats || this.stats;
        this.divineDomain = subclass;
        this.deity = deity;
        this.updateSpellProgression();
        this.updateDomainFeatures();
        this.render();
    }

    updateSpellProgression() {
        // Cantrips known
        if (this.level >= 10) this.cantripsKnown = 5;
        else if (this.level >= 4) this.cantripsKnown = 4;
        else this.cantripsKnown = 3;

        // Spell slots by level
        const spellSlotTable = {
            1:  {1: 2, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            2:  {1: 3, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            3:  {1: 4, 2: 2, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            4:  {1: 4, 2: 3, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            5:  {1: 4, 2: 3, 3: 2, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            6:  {1: 4, 2: 3, 3: 3, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            7:  {1: 4, 2: 3, 3: 3, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            8:  {1: 4, 2: 3, 3: 3, 4: 2, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0},
            9:  {1: 4, 2: 3, 3: 3, 4: 3, 5: 1, 6: 0, 7: 0, 8: 0, 9: 0},
            10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 0, 7: 0, 8: 0, 9: 0},
            11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 0, 8: 0, 9: 0},
            12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 0, 8: 0, 9: 0},
            13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 0, 9: 0},
            14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 0, 9: 0},
            15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 0},
            16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 0},
            17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
            18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
            19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
            20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1}
        };

        if (spellSlotTable[this.level]) {
            this.spellSlots = {...spellSlotTable[this.level]};
        }

        // Channel Divinity uses
        if (this.level >= 18) this.channelDivinityUses = 3;
        else if (this.level >= 6) this.channelDivinityUses = 2;
        else if (this.level >= 2) this.channelDivinityUses = 1;
        else this.channelDivinityUses = 0;

        // Destroy Undead CR
        if (this.level >= 17) this.destroyUndeadCR = 4;
        else if (this.level >= 14) this.destroyUndeadCR = 3;
        else if (this.level >= 11) this.destroyUndeadCR = 2;
        else if (this.level >= 8) this.destroyUndeadCR = 1;
        else if (this.level >= 5) this.destroyUndeadCR = 0.5;
        else this.destroyUndeadCR = 0;

        // Divine Intervention
        this.divineInterventionAvailable = this.level >= 10;
        this.divineInterventionAutoSuccess = this.level >= 20;
    }

    updateDomainFeatures() {
        // Update domain spells based on level and domain
        if (this.divineDomain === 'Life') {
            this.domainSpells = [];
            if (this.level >= 1) this.domainSpells.push('Bless', 'Cure Wounds');
            if (this.level >= 3) this.domainSpells.push('Lesser Restoration', 'Spiritual Weapon');
            if (this.level >= 5) this.domainSpells.push('Beacon of Hope', 'Revivify');
            if (this.level >= 7) this.domainSpells.push('Death Ward', 'Guardian of Faith');
            if (this.level >= 9) this.domainSpells.push('Mass Cure Wounds', 'Raise Dead');
        }
    }

    getSpellSaveDC() {
        const wisMod = calculateModifier(this.stats.wisdom);
        const profBonus = getProficiencyBonus(this.level);
        return 8 + profBonus + wisMod;
    }

    getSpellAttackBonus() {
        const wisMod = calculateModifier(this.stats.wisdom);
        const profBonus = getProficiencyBonus(this.level);
        return profBonus + wisMod;
    }

    getMaxPreparedSpells() {
        const wisMod = calculateModifier(this.stats.wisdom);
        return Math.max(1, wisMod + this.level);
    }

    render() {
        const container = document.getElementById('cleric-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    ✨ Cleric Features
                </div>
                
                ${this.renderSpellcastingInfo()}
                ${this.renderSpellSlots()}
                ${this.renderChannelDivinity()}
                ${this.renderDomainFeatures()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderSpellcastingInfo() {
        const spellSaveDC = this.getSpellSaveDC();
        const spellAttack = this.getSpellAttackBonus();
        const maxPrepared = this.getMaxPreparedSpells();
        const wisMod = calculateModifier(this.stats.wisdom);

        return `
            <div class="calculation-display">
                <div class="ability-card-name">📖 Spellcasting</div>
                <div class="calculation-formula">
                    <strong>Cantrips Known:</strong> ${this.cantripsKnown}<br>
                    <strong>Spells Prepared:</strong> ${this.spellsPrepared.length}/${maxPrepared} (WIS ${formatModifier(wisMod)} + Level ${this.level})<br>
                    <strong>Domain Spells:</strong> ${this.domainSpells.length} (always prepared)
                </div>
                <div class="calculation-result">
                    <strong>Spell Save DC:</strong> ${spellSaveDC} (8 + Prof + WIS)<br>
                    <strong>Spell Attack:</strong> ${formatModifier(spellAttack)} (Prof + WIS)
                </div>
            </div>
        `;
    }

    renderSpellSlots() {
        let html = '<div class="resource-tracker"><div class="resource-name">🔮 Spell Slots</div>';
        
        for (let level = 1; level <= 9; level++) {
            const total = this.spellSlots[level];
            if (total === 0) continue;
            
            const used = this.spellSlotsUsed[level] || 0;
            const remaining = total - used;
            const percentage = (remaining / total) * 100;
            
            html += `
                <div class="spell-slot-row" style="margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: bold;">Level ${level}</span>
                        <span>${remaining}/${total}</span>
                    </div>
                    <div class="resource-bar">
                        <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #4ecdc4 0%, #44a9a3 100%);">
                        </div>
                    </div>
                    <div class="resource-buttons" style="margin-top: 4px;">
                        <button class="spell-slot-use" data-level="${level}" ${used >= total ? 'disabled' : ''}>
                            Use Slot
                        </button>
                    </div>
                </div>
            `;
        }
        
        html += `
            <div class="resource-buttons" style="margin-top: 10px;">
                <button id="spell-slots-reset-btn">Long Rest (Restore All)</button>
            </div>
        </div>`;
        
        return html;
    }

    renderChannelDivinity() {
        if (this.level < 2) return '';
        
        const remaining = this.channelDivinityUses - this.channelDivinityUsed;
        const percentage = (remaining / this.channelDivinityUses) * 100;
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">⚡ Channel Divinity</div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #ffd93d 0%, #f5c542 100%);">
                        ${remaining}/${this.channelDivinityUses}
                    </div>
                </div>
                <div class="calculation-formula" style="margin-top: 8px;">
                    <strong>Options:</strong><br>
                    • Turn Undead (DC ${this.getSpellSaveDC()})<br>
                    ${this.destroyUndeadCR > 0 ? `• Destroy Undead (CR ${this.destroyUndeadCR} or lower)<br>` : ''}
                    ${this.renderDomainChannelDivinity()}
                </div>
                <div class="resource-buttons">
                    <button id="channel-divinity-use-btn" ${this.channelDivinityUsed >= this.channelDivinityUses ? 'disabled' : ''}>
                        Use Channel Divinity
                    </button>
                    <button id="channel-divinity-short-rest-btn">
                        Short Rest
                    </button>
                </div>
            </div>
        `;
    }

    renderDomainChannelDivinity() {
        if (this.divineDomain === 'Life' && this.level >= 2) {
            const hpPool = 5 * this.level;
            return `• Preserve Life (${hpPool} HP pool)<br>`;
        }
        return '';
    }

    renderDomainFeatures() {
        if (!this.divineDomain) return '';
        
        let features = '';
        
        if (this.divineDomain === 'Life') {
            features = this.renderLifeDomainFeatures();
        }
        
        if (!features) return '';
        
        return `
            <div class="calculation-display">
                <div class="ability-card-name">🛡️ ${this.divineDomain} Domain Features</div>
                ${features}
            </div>
        `;
    }

    renderLifeDomainFeatures() {
        let html = '<div class="calculation-formula">';
        
        if (this.level >= 1) {
            html += `
                <strong>• Bonus Proficiency:</strong> Heavy Armor<br>
                <strong>• Disciple of Life:</strong> Healing spells restore +2+spell level HP<br>
            `;
        }
        
        if (this.level >= 2) {
            html += `<strong>• Preserve Life:</strong> Channel Divinity (${5 * this.level} HP pool)<br>`;
        }
        
        if (this.level >= 6) {
            html += `<strong>• Blessed Healer:</strong> Heal self for 2+spell level when healing others<br>`;
        }
        
        if (this.level >= 8) {
            const dice = this.level >= 14 ? 2 : 1;
            html += `<strong>• Divine Strike:</strong> +${dice}d8 radiant damage (1/turn)<br>`;
        }
        
        if (this.level >= 17) {
            html += `<strong>• Supreme Healing:</strong> Maximize healing spell dice<br>`;
        }
        
        html += '</div>';
        return html;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Spellcasting', desc: `${this.cantripsKnown} cantrips, prepare ${this.getMaxPreparedSpells()} spells` },
            { level: 1, name: 'Divine Domain', desc: this.divineDomain || 'Choose your domain' },
            { level: 2, name: 'Channel Divinity (1/rest)', desc: `Turn Undead, DC ${this.getSpellSaveDC()}` },
            { level: 5, name: 'Destroy Undead', desc: `CR ${this.destroyUndeadCR} or lower` },
            { level: 6, name: 'Channel Divinity (2/rest)', desc: 'Two uses per short rest' },
            { level: 8, name: 'Divine Strike / Cantrip', desc: 'Domain feature improves' },
            { level: 10, name: 'Divine Intervention', desc: `${this.level}% chance of success` },
            { level: 14, name: 'Destroy Undead (CR 3)', desc: 'More powerful undead affected' },
            { level: 17, name: 'Destroy Undead (CR 4)', desc: 'Even stronger undead affected' },
            { level: 18, name: 'Channel Divinity (3/rest)', desc: 'Three uses per short rest' },
            { level: 20, name: 'Divine Intervention Improvement', desc: 'Automatically succeeds' }
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
        // Spell slot use buttons
        const slotButtons = document.querySelectorAll('.spell-slot-use');
        slotButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = parseInt(e.target.dataset.level);
                this.useSpellSlot(level);
            });
        });

        // Spell slots reset
        const slotsResetBtn = document.getElementById('spell-slots-reset-btn');
        if (slotsResetBtn) {
            slotsResetBtn.addEventListener('click', () => this.longRest());
        }

        // Channel Divinity use
        const channelUseBtn = document.getElementById('channel-divinity-use-btn');
        if (channelUseBtn) {
            channelUseBtn.addEventListener('click', () => this.useChannelDivinity());
        }

        // Channel Divinity short rest
        const channelRestBtn = document.getElementById('channel-divinity-short-rest-btn');
        if (channelRestBtn) {
            channelRestBtn.addEventListener('click', () => this.shortRest());
        }
    }

    useSpellSlot(level) {
        const used = this.spellSlotsUsed[level] || 0;
        const total = this.spellSlots[level];
        
        if (used >= total) return;
        
        this.spellSlotsUsed[level] = used + 1;
        this.render();
        
        this.showNotification(`🔮 Used Level ${level} spell slot`);
    }

    useChannelDivinity() {
        if (this.channelDivinityUsed >= this.channelDivinityUses) return;
        
        this.channelDivinityUsed++;
        this.render();
        
        this.showNotification('⚡ Channel Divinity used!');
    }

    shortRest() {
        this.channelDivinityUsed = 0;
        this.render();
        
        this.showNotification('🌙 Short rest completed. Channel Divinity restored!');
    }

    longRest() {
        // Reset all spell slots
        this.spellSlotsUsed = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0};
        
        // Reset Channel Divinity
        this.channelDivinityUsed = 0;
        
        this.render();
        
        this.showNotification('✨ Long rest completed. All spell slots and Channel Divinity restored!');
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
        this.updateDomainFeatures();
        this.render();
    }

    setSubclass(subclass) {
        this.divineDomain = subclass;
        this.updateDomainFeatures();
        this.render();
    }

    setDeity(deity) {
        this.deity = deity;
        this.render();
    }
}

// Export for global use
window.ClericFeatureManager = ClericFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Cleric') {
        window.clericManager = new ClericFeatureManager();
    }
});