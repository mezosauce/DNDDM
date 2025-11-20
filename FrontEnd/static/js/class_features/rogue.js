/**
 * Rogue Class Features UI
 * Handles Rogue-specific displays: Sneak Attack, Expertise, Feature Tree
 */

class RogueFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Rogue');
        this.sneakAttackDice = 1;
        this.sneakAttackUsedThisTurn = false;
        this.expertiseSkills = new Set(['Stealth', 'Acrobatics']);
        this.expertiseThievesTools = false;
        this.stats = { dexterity: 10, intelligence: 10, wisdom: 10 };
        this.subclass = '';
        this.strokeOfLuckUsed = false;
    }

    initialize(level, stats, subclass = '') {
        this.level = level;
        this.stats = stats || this.stats;
        this.subclass = subclass;
        this.updateSneakAttackProgression();
        this.updateExpertise();
        this.render();
    }

    updateSneakAttackProgression() {
        // Sneak Attack dice progression based on level
        const sneakAttackLevels = {
            1: 1, 2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4, 9: 5, 10: 5,
            11: 6, 12: 6, 13: 7, 14: 7, 15: 8, 16: 8, 17: 9, 18: 9, 19: 10, 20: 10
        };
        this.sneakAttackDice = sneakAttackLevels[this.level] || 1;
    }

    updateExpertise() {
        // Update expertise based on level
        if (this.level >= 1) {
            // Level 1 expertise (default)
            this.expertiseSkills = new Set(['Stealth', 'Acrobatics']);
        }
        if (this.level >= 6) {
            // Level 6 additional expertise
            this.expertiseSkills.add('Sleight of Hand');
            this.expertiseSkills.add('Perception');
        }
    }

    calculateSneakAttackDamage() {
        // Average damage calculation (3.5 per d6)
        return (this.sneakAttackDice * 3.5).toFixed(1);
    }

    canSneakAttack(hasAdvantage = false, allyNearTarget = false, hasDisadvantage = false, weaponType = 'finesse') {
        if (this.sneakAttackUsedThisTurn) return false;
        if (weaponType !== 'finesse' && weaponType !== 'ranged') return false;
        if (hasDisadvantage) return false;
        return hasAdvantage || allyNearTarget;
    }

    render() {
        const container = document.getElementById('rogue-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    🗡️ Rogue Features
                </div>
                
                ${this.renderSneakAttackTracker()}
                ${this.renderExpertiseDisplay()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderSneakAttackTracker() {
        const avgDamage = this.calculateSneakAttackDamage();
        const usedStatus = this.sneakAttackUsedThisTurn ? '(USED THIS TURN)' : '(AVAILABLE)';
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    🎯 Sneak Attack ${usedStatus}
                </div>
                <div class="resource-info">
                    <div class="damage-display">
                        ${this.sneakAttackDice}d6 (Avg: ${avgDamage})
                    </div>
                    <div class="resource-buttons">
                        <button id="sneak-attack-btn" ${this.sneakAttackUsedThisTurn ? 'disabled' : ''}>
                            Use Sneak Attack
                        </button>
                        <button id="reset-turn-btn">
                            Reset Turn
                        </button>
                    </div>
                </div>
                ${this.renderSneakAttackConditions()}
            </div>
        `;
    }

    renderSneakAttackConditions() {
        return `
            <div class="calculation-display" style="margin-top: 10px;">
                <strong style="color: #4ecdc4;">Sneak Attack Conditions:</strong>
                <div class="calculation-formula">
                    • Must use finesse or ranged weapon<br>
                    • Must have advantage OR ally within 5ft of target<br>
                    • Cannot have disadvantage<br>
                    • Once per turn
                </div>
            </div>
        `;
    }

    renderExpertiseDisplay() {
        const dexMod = calculateModifier(this.stats.dexterity);
        const profBonus = this.getProficiencyBonus();
        const expertiseBonus = profBonus * 2;
        
        let expertiseHTML = '<div class="expertise-skills">';
        this.expertiseSkills.forEach(skill => {
            expertiseHTML += `
                <div class="expertise-skill">
                    <span class="skill-name">${skill}</span>
                    <span class="skill-bonus">+${expertiseBonus + dexMod}</span>
                </div>
            `;
        });
        expertiseHTML += '</div>';

        return `
            <div class="calculation-display">
                <div class="ability-card-name">🎓 Expertise</div>
                <div class="calculation-formula">
                    Proficiency Bonus: +${profBonus} × 2 = +${expertiseBonus}
                </div>
                <div class="expertise-container">
                    ${expertiseHTML}
                </div>
                ${this.expertiseThievesTools ? `
                    <div class="expertise-tools">
                        Thieves' Tools: +${expertiseBonus + dexMod}
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Expertise', desc: 'Double proficiency in 2 skills/thieves\' tools' },
            { level: 1, name: 'Sneak Attack', desc: `${this.sneakAttackDice}d6 extra damage with advantage or ally nearby` },
            { level: 1, name: 'Thieves\' Cant', desc: 'Secret language of rogues' },
            { level: 2, name: 'Cunning Action', desc: 'Dash, Disengage, or Hide as bonus action' },
            { level: 3, name: 'Roguish Archetype', desc: this.subclass || 'Choose your archetype' },
            { level: 5, name: 'Uncanny Dodge', desc: 'Use reaction to halve damage from an attack' },
            { level: 6, name: 'Expertise', desc: 'Double proficiency in 2 more skills/tools' },
            { level: 7, name: 'Evasion', desc: 'No damage on successful DEX saves, half on failed' },
            { level: 9, name: 'Archetype Feature', desc: this.getArchetypeFeatureName(9) },
            { level: 11, name: 'Reliable Talent', desc: 'Treat d20 rolls of 9 or lower as 10 for proficient skills' },
            { level: 13, name: 'Archetype Feature', desc: this.getArchetypeFeatureName(13) },
            { level: 14, name: 'Blindsense', desc: 'Sense hidden/invisible creatures within 10ft' },
            { level: 15, name: 'Slippery Mind', desc: 'Proficiency in Wisdom saving throws' },
            { level: 17, name: 'Archetype Feature', desc: this.getArchetypeFeatureName(17) },
            { level: 18, name: 'Elusive', desc: 'No attack rolls have advantage against you' },
            { level: 20, name: 'Stroke of Luck', desc: 'Turn miss into hit or failed check into 20 (1/rest)' }
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

    getArchetypeFeatureName(level) {
        if (!this.subclass) return 'Archetype feature';
        
        switch (this.subclass) {
            case 'Thief':
                if (level === 9) return 'Supreme Sneak';
                if (level === 13) return 'Use Magic Device';
                if (level === 17) return 'Thief\'s Reflexes';
                break;
            case 'Assassin':
                if (level === 9) return 'Infiltration Expertise';
                if (level === 13) return 'Impostor';
                if (level === 17) return 'Death Strike';
                break;
            case 'Arcane Trickster':
                if (level === 9) return 'Magical Ambush';
                if (level === 13) return 'Versatile Trickster';
                if (level === 17) return 'Spell Thief';
                break;
        }
        return 'Archetype feature';
    }

    attachEventListeners() {
        const sneakAttackBtn = document.getElementById('sneak-attack-btn');
        const resetTurnBtn = document.getElementById('reset-turn-btn');

        if (sneakAttackBtn) {
            sneakAttackBtn.addEventListener('click', () => this.useSneakAttack());
        }
        if (resetTurnBtn) {
            resetTurnBtn.addEventListener('click', () => this.resetTurn());
        }
    }

    useSneakAttack() {
        if (this.sneakAttackUsedThisTurn) return;
        
        this.sneakAttackUsedThisTurn = true;
        const damage = this.calculateSneakAttackDamage();
        this.render();
        
        this.showNotification(`🎯 SNEAK ATTACK! ${this.sneakAttackDice}d6 (${damage} avg) damage!`);
    }

    resetTurn() {
        this.sneakAttackUsedThisTurn = false;
        this.render();
        
        this.showNotification('🔄 Turn reset. Sneak Attack available.');
    }

    shortRest() {
        this.strokeOfLuckUsed = false;
        this.resetTurn();
        this.showNotification('✨ Short rest completed. Stroke of Luck restored!');
    }

    longRest() {
        this.strokeOfLuckUsed = false;
        this.resetTurn();
        this.showNotification('✨ Long rest completed. All features restored!');
    }

    useStrokeOfLuck() {
        if (this.strokeOfLuckUsed || this.level < 20) return false;
        
        this.strokeOfLuckUsed = true;
        this.showNotification('🍀 Stroke of Luck used! Miss becomes hit or failed check becomes 20!');
        return true;
    }

    getProficiencyBonus() {
        if (this.level < 5) return 2;
        if (this.level < 9) return 3;
        if (this.level < 13) return 4;
        if (this.level < 17) return 5;
        return 6;
    }

    isFeatureUnlocked(featureLevel) {
        return this.level >= featureLevel;
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
        this.updateSneakAttackProgression();
        this.updateExpertise();
        this.render();
    }

    setSubclass(subclass) {
        this.subclass = subclass;
        this.render();
    }

    setExpertise(skills, thievesTools = false) {
        this.expertiseSkills = new Set(skills);
        this.expertiseThievesTools = thievesTools;
        this.render();
    }
}

// Export for global use
window.RogueFeatureManager = RogueFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Rogue') {
        window.rogueManager = new RogueFeatureManager();
    }
});

// Utility functions (if not already defined globally)
function calculateModifier(score) {
    return Math.floor((score - 10) / 2);
}

function formatModifier(modifier) {
    return modifier >= 0 ? `+${modifier}` : `${modifier}`;
}