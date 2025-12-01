/**
 * Bard Class Features UI
 * Handles Bard-specific displays: Bardic Inspiration, Spellcasting, Feature Tree
 */

class BardFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Bard');
        this.stats = { 
            strength: 10, 
            dexterity: 10, 
            constitution: 10, 
            intelligence: 10, 
            wisdom: 10, 
            charisma: 10 
        };
        
        // Bardic Inspiration
        this.bardicInspirationDie = 'd6';
        this.bardicInspirationUses = 0;
        this.bardicInspirationRemaining = 0;
        
        // Spellcasting
        this.spellSlots = {};
        this.spellSlotsUsed = {};
        this.cantripsKnown = 0;
        this.maxCantrips = 2;
        this.spellsKnown = 0;
        this.maxSpellsKnown = 4;
        
        // Features
        this.jackOfAllTrades = false;
        this.songOfRestDie = '';
        this.fontOfInspiration = false;
        this.countercharm = false;
        this.expertiseCount = 0;
        this.magicalSecretsCount = 0;
        
        // College
        this.college = '';
    }

    initialize(level, stats) {
        this.level = level;
        this.stats = stats || this.stats;
        this.updateProgression();
        this.render();
    }

    updateProgression() {
        // Bardic Inspiration die progression
        if (this.level >= 15) this.bardicInspirationDie = 'd12';
        else if (this.level >= 10) this.bardicInspirationDie = 'd10';
        else if (this.level >= 5) this.bardicInspirationDie = 'd8';
        else this.bardicInspirationDie = 'd6';

        // Calculate uses based on Charisma modifier
        const chaMod = calculateModifier(this.stats.charisma);
        this.bardicInspirationUses = Math.max(1, chaMod);
        if (this.bardicInspirationRemaining === 0) {
            this.bardicInspirationRemaining = this.bardicInspirationUses;
        }

        // Update spell slots
        this.spellSlots = this.getSpellSlotsForLevel(this.level);
        if (Object.keys(this.spellSlotsUsed).length === 0) {
            this.spellSlotsUsed = {};
            Object.keys(this.spellSlots).forEach(level => {
                this.spellSlotsUsed[level] = 0;
            });
        }

        // Cantrips and spells known
        this.maxCantrips = this.getMaxCantrips();
        this.maxSpellsKnown = this.getMaxSpellsKnown();

        // Class features
        this.jackOfAllTrades = this.level >= 2;
        this.fontOfInspiration = this.level >= 5;
        this.countercharm = this.level >= 6;

        // Song of Rest progression
        if (this.level >= 17) this.songOfRestDie = 'd12';
        else if (this.level >= 13) this.songOfRestDie = 'd10';
        else if (this.level >= 9) this.songOfRestDie = 'd8';
        else if (this.level >= 2) this.songOfRestDie = 'd6';
        else this.songOfRestDie = '';

        // Expertise count
        if (this.level >= 10) this.expertiseCount = 4;
        else if (this.level >= 3) this.expertiseCount = 2;
        else this.expertiseCount = 0;

        // Magical Secrets
        if (this.level >= 18) this.magicalSecretsCount = 6;
        else if (this.level >= 14) this.magicalSecretsCount = 4;
        else if (this.level >= 10) this.magicalSecretsCount = 2;
        else this.magicalSecretsCount = 0;
    }

    getSpellSlotsForLevel(level) {
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
        return spellSlotTable[level] || {1: 2};
    }

    getMaxCantrips() {
        if (this.level >= 10) return 4;
        if (this.level >= 4) return 3;
        return 2;
    }

    getMaxSpellsKnown() {
        const spellsKnownTable = {
            1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11, 9: 12, 10: 14,
            11: 15, 12: 15, 13: 16, 14: 18, 15: 19, 16: 19, 17: 20, 18: 22,
            19: 22, 20: 22
        };
        return spellsKnownTable[this.level] || 4;
    }

    getSpellSaveDC() {
        const profBonus = getProficiencyBonus(this.level);
        const chaMod = calculateModifier(this.stats.charisma);
        return 8 + profBonus + chaMod;
    }

    getSpellAttackBonus() {
        const profBonus = getProficiencyBonus(this.level);
        const chaMod = calculateModifier(this.stats.charisma);
        return profBonus + chaMod;
    }

    render() {
        const container = document.getElementById('bard-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    🎵 Bard Features
                </div>
                
                ${this.renderBardicInspiration()}
                ${this.renderSpellcasting()}
                ${this.renderSpellSlots()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderBardicInspiration() {
        const percentage = (this.bardicInspirationRemaining / this.bardicInspirationUses) * 100;
        const restoreText = this.fontOfInspiration ? 'Short or Long Rest' : 'Long Rest';
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    🎭 Bardic Inspiration (${this.bardicInspirationDie})
                </div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #9b59b6 0%, #8e44ad 100%);">
                        ${this.bardicInspirationRemaining}/${this.bardicInspirationUses}
                    </div>
                </div>
                <div class="resource-buttons">
                    <button id="inspiration-use-btn" ${this.bardicInspirationRemaining <= 0 ? 'disabled' : ''}>
                        Use Inspiration
                    </button>
                    <button id="inspiration-short-rest-btn" ${!this.fontOfInspiration ? 'disabled' : ''}>
                        Short Rest
                    </button>
                    <button id="inspiration-long-rest-btn">
                        Long Rest
                    </button>
                </div>
                <div class="calculation-display" style="margin-top: 10px;">
                    <div class="calculation-formula">
                        Uses: Charisma modifier (${Math.max(1, calculateModifier(this.stats.charisma))})<br>
                        Restores on: ${restoreText}<br>
                        Grant an ally a ${this.bardicInspirationDie} to add to ability checks, attack rolls, or saving throws
                    </div>
                </div>
            </div>
        `;
    }

    renderSpellcasting() {
        const spellSaveDC = this.getSpellSaveDC();
        const spellAttackBonus = this.getSpellAttackBonus();
        
        return `
            <div class="calculation-display">
                <div class="ability-card-name">✨ Spellcasting</div>
                <div class="calculation-formula">
                    <strong>Spell Save DC:</strong> 8 + Prof (${getProficiencyBonus(this.level)}) + CHA (${formatModifier(calculateModifier(this.stats.charisma))}) = ${spellSaveDC}<br>
                    <strong>Spell Attack:</strong> Prof (${getProficiencyBonus(this.level)}) + CHA (${formatModifier(calculateModifier(this.stats.charisma))}) = ${formatModifier(spellAttackBonus)}<br>
                    <strong>Cantrips Known:</strong> ${this.cantripsKnown}/${this.maxCantrips}<br>
                    <strong>Spells Known:</strong> ${this.spellsKnown}/${this.maxSpellsKnown}
                </div>
            </div>
        `;
    }

    renderSpellSlots() {
        let html = '<div class="spell-slots-container">';
        html += '<div class="resource-name">📖 Spell Slots</div>';
        
        const sortedLevels = Object.keys(this.spellSlots).sort((a, b) => parseInt(a) - parseInt(b));
        
        sortedLevels.forEach(level => {
            const total = this.spellSlots[level];
            const used = this.spellSlotsUsed[level] || 0;
            const remaining = total - used;
            const percentage = (remaining / total) * 100;
            
            html += `
                <div class="spell-slot-row">
                    <div class="spell-slot-level">Level ${level}</div>
                    <div class="resource-bar" style="flex: 1;">
                        <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);">
                            ${remaining}/${total}
                        </div>
                    </div>
                    <div class="spell-slot-buttons">
                        <button class="spell-slot-use-btn" data-level="${level}" ${remaining <= 0 ? 'disabled' : ''}>Use</button>
                        <button class="spell-slot-restore-btn" data-level="${level}" ${used <= 0 ? 'disabled' : ''}>Restore</button>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Spellcasting', desc: 'Learn and cast bard spells using Charisma' },
            { level: 1, name: 'Bardic Inspiration', desc: `${this.bardicInspirationDie}, ${this.bardicInspirationUses} uses` },
            { level: 2, name: 'Jack of All Trades', desc: 'Add half proficiency to non-proficient ability checks' },
            { level: 2, name: 'Song of Rest', desc: this.songOfRestDie ? `Heal extra ${this.songOfRestDie} during short rest` : 'Not yet available' },
            { level: 3, name: 'Bard College', desc: this.college || 'Choose your college' },
            { level: 3, name: 'Expertise', desc: 'Double proficiency bonus for 2 skills' },
            { level: 5, name: 'Font of Inspiration', desc: 'Bardic Inspiration recharges on short rest' },
            { level: 6, name: 'Countercharm', desc: 'Grant advantage vs. being frightened or charmed' },
            { level: 10, name: 'Magical Secrets', desc: 'Learn 2 spells from any class' },
            { level: 10, name: 'Expertise (4 total)', desc: 'Double proficiency bonus for 2 more skills' },
            { level: 14, name: 'Magical Secrets (4 total)', desc: 'Learn 2 more spells from any class' },
            { level: 18, name: 'Magical Secrets (6 total)', desc: 'Learn 2 more spells from any class' },
            { level: 20, name: 'Superior Inspiration', desc: 'Regain 1 Bardic Inspiration if you have none at initiative' }
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
        // Bardic Inspiration buttons
        const useInspirationBtn = document.getElementById('inspiration-use-btn');
        const shortRestBtn = document.getElementById('inspiration-short-rest-btn');
        const longRestBtn = document.getElementById('inspiration-long-rest-btn');

        if (useInspirationBtn) {
            useInspirationBtn.addEventListener('click', () => this.useBardicInspiration());
        }
        if (shortRestBtn) {
            shortRestBtn.addEventListener('click', () => this.shortRest());
        }
        if (longRestBtn) {
            longRestBtn.addEventListener('click', () => this.longRest());
        }

        // Spell slot buttons
        document.querySelectorAll('.spell-slot-use-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = parseInt(e.target.dataset.level);
                this.useSpellSlot(level);
            });
        });

        document.querySelectorAll('.spell-slot-restore-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const level = parseInt(e.target.dataset.level);
                this.restoreSpellSlot(level);
            });
        });
    }

    useBardicInspiration() {
        if (this.bardicInspirationRemaining <= 0) return;
        
        this.bardicInspirationRemaining--;
        this.render();
        
        this.showNotification(`🎭 Bardic Inspiration granted! (${this.bardicInspirationDie})`);
    }

    useSpellSlot(level) {
        if (!this.spellSlots[level]) return;
        if (this.spellSlotsUsed[level] >= this.spellSlots[level]) return;
        
        this.spellSlotsUsed[level]++;
        this.render();
        
        this.showNotification(`✨ Level ${level} spell slot used`);
    }

    restoreSpellSlot(level) {
        if (!this.spellSlots[level]) return;
        if (this.spellSlotsUsed[level] <= 0) return;
        
        this.spellSlotsUsed[level]--;
        this.render();
        
        this.showNotification(`✨ Level ${level} spell slot restored`);
    }

    shortRest() {
        if (this.fontOfInspiration) {
            this.bardicInspirationRemaining = this.bardicInspirationUses;
            this.render();
            this.showNotification('🎵 Short rest completed. Bardic Inspiration restored!');
        } else {
            this.showNotification('⚠️ Font of Inspiration (Level 5) required for short rest recovery');
        }
    }

    longRest() {
        // Restore all spell slots
        Object.keys(this.spellSlots).forEach(level => {
            this.spellSlotsUsed[level] = 0;
        });
        
        // Restore Bardic Inspiration
        this.bardicInspirationRemaining = this.bardicInspirationUses;
        
        this.render();
        this.showNotification('✨ Long rest completed. All resources restored!');
    }

    showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'feature-unlock-notice';
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.padding = '15px 20px';
        notification.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        notification.style.color = 'white';
        notification.style.borderRadius = '8px';
        notification.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        notification.style.zIndex = '1000';
        notification.style.animation = 'slideIn 0.3s ease-out';
        notification.style.fontWeight = '500';
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    updateStats(stats) {
        this.stats = stats;
        this.updateProgression();
        this.render();
    }

    setLevel(level) {
        this.level = parseInt(level) || 1;
        this.updateProgression();
        this.render();
    }


    updateSpellsKnown(cantrips, spells) {
        this.cantripsKnown = cantrips || 0;
        this.spellsKnown = spells || 0;
        this.render();
    }
}

// Export for global use
window.BardFeatureManager = BardFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Bard') {
        window.bardManager = new BardFeatureManager();
    }
});