/**
 * Monk Class Features UI
 * Handles Monk-specific displays: Ki Points, Martial Arts, Unarmored Defense, Feature Tree
 */

class MonkFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Monk');
        this.kiPoints = 0;
        this.kiPointsMax = 0;
        this.martialArtsDie = 4;
        this.unarmoredMovement = 0;
        this.stats = { dexterity: 10, wisdom: 10, constitution: 10 };
        this.subclass = '';
        this.kiSaveDC = 0;
    }

    initialize(level, stats, subclass = '') {
        this.level = level;
        this.stats = stats || this.stats;
        this.subclass = subclass;
        this.updateKiProgression();
        this.calculateKiSaveDC();
        this.render();
    }

    updateKiProgression() {
        // Ki points based on level
        if (this.level >= 20) this.kiPointsMax = 20;
        else if (this.level >= 19) this.kiPointsMax = 19;
        else if (this.level >= 18) this.kiPointsMax = 18;
        else if (this.level >= 17) this.kiPointsMax = 17;
        else if (this.level >= 16) this.kiPointsMax = 16;
        else if (this.level >= 15) this.kiPointsMax = 15;
        else if (this.level >= 14) this.kiPointsMax = 14;
        else if (this.level >= 13) this.kiPointsMax = 13;
        else if (this.level >= 12) this.kiPointsMax = 12;
        else if (this.level >= 11) this.kiPointsMax = 11;
        else if (this.level >= 10) this.kiPointsMax = 10;
        else if (this.level >= 9) this.kiPointsMax = 9;
        else if (this.level >= 8) this.kiPointsMax = 8;
        else if (this.level >= 7) this.kiPointsMax = 7;
        else if (this.level >= 6) this.kiPointsMax = 6;
        else if (this.level >= 5) this.kiPointsMax = 5;
        else if (this.level >= 4) this.kiPointsMax = 4;
        else if (this.level >= 3) this.kiPointsMax = 3;
        else if (this.level >= 2) this.kiPointsMax = 2;
        else this.kiPointsMax = 0;

        // Martial Arts die progression
        if (this.level >= 17) this.martialArtsDie = 10;
        else if (this.level >= 11) this.martialArtsDie = 8;
        else if (this.level >= 5) this.martialArtsDie = 6;
        else this.martialArtsDie = 4;

        // Unarmored Movement progression
        if (this.level >= 18) this.unarmoredMovement = 30;
        else if (this.level >= 14) this.unarmoredMovement = 25;
        else if (this.level >= 10) this.unarmoredMovement = 20;
        else if (this.level >= 6) this.unarmoredMovement = 15;
        else if (this.level >= 2) this.unarmoredMovement = 10;
        else this.unarmoredMovement = 0;
    }

    calculateKiSaveDC() {
        const wisMod = calculateModifier(this.stats.wisdom);
        const profBonus = this.getProficiencyBonus();
        this.kiSaveDC = 8 + profBonus + wisMod;
    }

    getProficiencyBonus() {
        if (this.level < 5) return 2;
        else if (this.level < 9) return 3;
        else if (this.level < 13) return 4;
        else if (this.level < 17) return 5;
        else return 6;
    }

    calculateUnarmoredDefense() {
        const dexMod = calculateModifier(this.stats.dexterity);
        const wisMod = calculateModifier(this.stats.wisdom);
        return 10 + dexMod + wisMod;
    }

    render() {
        const container = document.getElementById('monk-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    🧘 Monk Features
                </div>
                
                ${this.renderKiTracker()}
                ${this.renderUnarmoredDefenseDisplay()}
                ${this.renderUnarmoredMovementDisplay()}
                ${this.renderMartialArtsDisplay()}
                ${this.renderKiAbilities()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderKiTracker() {
        const percentage = this.kiPointsMax > 0 ? (this.kiPoints / this.kiPointsMax) * 100 : 0;
        const kiText = this.kiPointsMax > 0 ? `${this.kiPoints}/${this.kiPointsMax}` : 'Unavailable (Level 2+)';
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    ✨ Ki Points
                </div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #4ecdc4 0%, #44a08d 100%);">
                        ${kiText}
                    </div>
                </div>
                <div class="resource-buttons">
                    <button id="ki-short-rest-btn" ${this.kiPointsMax === 0 ? 'disabled' : ''}>
                        Short Rest
                    </button>
                    <button id="ki-reset-btn">
                        Long Rest
                    </button>
                </div>
                ${this.kiPointsMax > 0 ? `
                    <div class="calculation-display" style="margin-top: 10px;">
                        <strong style="color: #4ecdc4;">Ki Save DC:</strong> ${this.kiSaveDC}
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderUnarmoredDefenseDisplay() {
        const ac = this.calculateUnarmoredDefense();
        const dexMod = calculateModifier(this.stats.dexterity);
        const wisMod = calculateModifier(this.stats.wisdom);
        
        return `
            <div class="calculation-display">
                <div class="ability-card-name">🛡️ Unarmored Defense</div>
                <div class="calculation-formula">
                    AC = 10 + DEX (${formatModifier(dexMod)}) + WIS (${formatModifier(wisMod)})
                </div>
                <div class="calculation-result">
                    AC ${ac}
                </div>
            </div>
        `;
    }

    renderUnarmoredMovementDisplay() {
        if (this.unarmoredMovement === 0) return '';
        
        const specialMovement = this.level >= 9 ? 
            '<div class="calculation-formula" style="margin-top: 5px; font-size: 0.9em;">Can move on vertical surfaces and liquids</div>' : '';
        
        return `
            <div class="calculation-display">
                <div class="ability-card-name">🏃 Unarmored Movement</div>
                <div class="calculation-formula">
                    Speed = 30 ft + ${this.unarmoredMovement} ft
                </div>
                <div class="calculation-result">
                    Total Speed: ${30 + this.unarmoredMovement} ft
                </div>
                ${specialMovement}
            </div>
        `;
    }

    renderMartialArtsDisplay() {
        return `
            <div class="calculation-display">
                <div class="ability-card-name">🥋 Martial Arts</div>
                <div class="calculation-formula">
                    Unarmed Strike: d${this.martialArtsDie} damage
                </div>
                <div class="calculation-formula">
                    Use DEX for attack and damage rolls
                </div>
                <div class="calculation-formula">
                    Bonus action unarmed strike after Attack action
                </div>
            </div>
        `;
    }

    renderKiAbilities() {
        if (this.kiPointsMax === 0) return '';

        const abilities = [
            { id: 'flurry-of-blows', name: 'Flurry of Blows', cost: 1, desc: 'Two unarmed strikes as bonus action' },
            { id: 'patient-defense', name: 'Patient Defense', cost: 1, desc: 'Dodge as bonus action' },
            { id: 'step-of-the-wind', name: 'Step of the Wind', cost: 1, desc: 'Disengage/Dash + double jump' },
            { id: 'stunning-strike', name: 'Stunning Strike', cost: 1, desc: 'Stun target on hit (CON save)' }
        ];

        // Add subclass-specific abilities
        if (this.subclass === 'Way of the Open Hand' && this.level >= 6) {
            abilities.push({ 
                id: 'wholeness-of-body', 
                name: 'Wholeness of Body', 
                cost: 0, 
                desc: 'Heal 3× level HP (1/long rest)' 
            });
        }

        if (this.level >= 18) {
            abilities.push({ 
                id: 'empty-body', 
                name: 'Empty Body', 
                cost: 4, 
                desc: 'Invisible + resistance to all damage (1 min)' 
            });
        }

        let html = '<div class="ki-abilities-grid">';
        abilities.forEach(ability => {
            const canUse = ability.cost === 0 || this.kiPoints >= ability.cost;
            html += `
                <div class="ki-ability ${canUse ? '' : 'disabled'}">
                    <button class="ki-ability-btn" data-ability="${ability.id}" ${!canUse ? 'disabled' : ''}>
                        ${ability.name}
                        ${ability.cost > 0 ? `<span class="ki-cost">${ability.cost} Ki</span>` : ''}
                    </button>
                    <div class="ki-ability-desc">${ability.desc}</div>
                </div>
            `;
        });
        html += '</div>';

        return `
            <div class="ki-abilities-section">
                <div class="ability-card-name">🌀 Ki Abilities</div>
                ${html}
            </div>
        `;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Unarmored Defense', desc: '10 + DEX + WIS when not wearing armor' },
            { level: 1, name: 'Martial Arts', desc: `d${this.martialArtsDie} damage, DEX for attacks, bonus action strike` },
            { level: 2, name: 'Ki', desc: `${this.kiPointsMax} points, Flurry/Patient/Step abilities` },
            { level: 2, name: 'Unarmored Movement', desc: `+${this.unarmoredMovement} ft speed` },
            { level: 3, name: 'Monastic Tradition', desc: this.subclass || 'Choose your tradition' },
            { level: 3, name: 'Deflect Missiles', desc: 'Reduce ranged damage, catch and throw back' },
            { level: 4, name: 'Slow Fall', desc: 'Reduce falling damage by 5× level' },
            { level: 5, name: 'Extra Attack', desc: 'Attack twice when you take the Attack action' },
            { level: 5, name: 'Stunning Strike', desc: 'Spend 1 ki to stun target on hit' },
            { level: 6, name: 'Ki-Empowered Strikes', desc: 'Unarmed strikes count as magical' },
            { level: 7, name: 'Evasion', desc: 'No damage on successful DEX saves, half on failed' },
            { level: 7, name: 'Stillness of Mind', desc: 'Action to end charmed/frightened effects' },
            { level: 9, name: 'Unarmored Movement', desc: 'Move on vertical surfaces and liquids' },
            { level: 10, name: 'Purity of Body', desc: 'Immunity to disease and poison' },
            { level: 13, name: 'Tongue of Sun/Moon', desc: 'Understand/speak all languages' },
            { level: 14, name: 'Diamond Soul', desc: 'Proficiency in all saves, ki to reroll' },
            { level: 15, name: 'Timeless Body', desc: 'No aging, no need for food/water' },
            { level: 18, name: 'Empty Body', desc: '4 ki: invisible + damage resistance' },
            { level: 20, name: 'Perfect Self', desc: 'Regain 4 ki when initiative with 0 ki' }
        ];

        // Add subclass-specific features
        if (this.subclass === 'Way of the Open Hand') {
            features.splice(5, 0, { level: 3, name: 'Open Hand Technique', desc: 'Prone, push, or no reactions on Flurry hits' });
            if (this.level >= 6) features.splice(8, 0, { level: 6, name: 'Wholeness of Body', desc: 'Heal 3× level HP (1/long rest)' });
            if (this.level >= 11) features.splice(12, 0, { level: 11, name: 'Tranquility', desc: 'Sanctuary after long rest' });
            if (this.level >= 17) features.splice(17, 0, { level: 17, name: 'Quivering Palm', desc: '3 ki: delayed instakill (CON save)' });
        }

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
        const shortRestBtn = document.getElementById('ki-short-rest-btn');
        const resetBtn = document.getElementById('ki-reset-btn');

        if (shortRestBtn) {
            shortRestBtn.addEventListener('click', () => this.shortRest());
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.longRest());
        }

        // Attach Ki ability buttons
        document.querySelectorAll('.ki-ability-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const ability = e.target.closest('.ki-ability-btn').dataset.ability;
                this.useKiAbility(ability);
            });
        });
    }

    useKiAbility(ability) {
        let cost = 1;
        let message = '';

        switch(ability) {
            case 'flurry-of-blows':
                message = '🌀 Flurry of Blows! Two unarmed strikes as bonus action.';
                break;
            case 'patient-defense':
                message = '🛡️ Patient Defense! Dodge as bonus action.';
                break;
            case 'step-of-the-wind':
                message = '💨 Step of the Wind! Disengage/Dash + double jump distance.';
                break;
            case 'stunning-strike':
                message = '💫 Stunning Strike! Target must make CON save or be stunned.';
                break;
            case 'wholeness-of-body':
                cost = 0;
                const healing = 3 * this.level;
                message = `💚 Wholeness of Body! Healed ${healing} HP.`;
                break;
            case 'empty-body':
                cost = 4;
                message = '👻 Empty Body! Invisible and resistant to all damage (except force) for 1 minute.';
                break;
            default:
                return;
        }

        if (cost > 0 && this.kiPoints >= cost) {
            this.kiPoints -= cost;
            this.showNotification(message);
            this.render();
        } else if (cost === 0) {
            this.showNotification(message);
        }
    }

    shortRest() {
        if (this.kiPointsMax === 0) return;
        
        this.kiPoints = this.kiPointsMax;
        this.render();
        
        this.showNotification('✨ Short rest completed. Ki points restored!');
    }

    longRest() {
        this.kiPoints = this.kiPointsMax;
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
        this.calculateKiSaveDC();
        this.render();
    }

    setLevel(level) {
        this.level = parseInt(level) || 1;
        this.updateKiProgression();
        this.calculateKiSaveDC();
        this.render();
    }

    setSubclass(subclass) {
        this.subclass = subclass;
        this.render();
    }
}

// Export for global use
window.MonkFeatureManager = MonkFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Monk') {
        window.monkManager = new MonkFeatureManager();
    }
});

// Utility functions (if not already defined globally)
if (typeof calculateModifier === 'undefined') {
    function calculateModifier(score) {
        return Math.floor((score - 10) / 2);
    }
}

if (typeof formatModifier === 'undefined') {
    function formatModifier(modifier) {
        return modifier >= 0 ? `+${modifier}` : modifier.toString();
    }
}