/**
 * Barbarian Class Features UI
 * Handles Barbarian-specific displays: Rage, Unarmored Defense, Feature Tree
 */
// API base used by frontend to reach the backend service.
// Defaults to "/" (same origin) so it works when served from the same Flask app.
// Override with window.API_BASE if needed for cross-origin use.
const API_BASE = (typeof window !== 'undefined' && window.API_BASE) ? window.API_BASE : '';

class BarbarianFeatureManager extends ClassFeatureManager {
    constructor() {
        super('Barbarian');
        this.ragesUsed = 0;
        this.ragesPerDay = 2;
        this.rageDamage = 2;
        this.currentlyRaging = false;
        this.stats = { strength: 10, dexterity: 10, constitution: 10 };
    }

    initialize(level, stats, subclass = '') {
        this.level = level;
        this.stats = stats || this.stats;
        this.subclass = subclass;
        this.updateRageProgression();
        this.render();
    }

    updateRageProgression() {
        // Rage uses per day based on level
        if (this.level >= 20) this.ragesPerDay = 999; // Unlimited
        else if (this.level >= 17) this.ragesPerDay = 6;
        else if (this.level >= 12) this.ragesPerDay = 5;
        else if (this.level >= 6) this.ragesPerDay = 4;
        else if (this.level >= 3) this.ragesPerDay = 3;
        else this.ragesPerDay = 2;

        // Rage damage based on level
        if (this.level >= 16) this.rageDamage = 4;
        else if (this.level >= 9) this.rageDamage = 3;
        else this.rageDamage = 2;
    }

    calculateUnarmoredDefense() {
        const dexMod = calculateModifier(this.stats.dexterity);
        const conMod = calculateModifier(this.stats.constitution);
        return 10 + dexMod + conMod;
    }

    render() {
        const container = document.getElementById('barbarian-features');
        if (!container) return;

        container.innerHTML = `
            <div class="class-specific-section active">
                <div class="class-section-header">
                    ⚔️ Barbarian Features
                </div>
                
                ${this.renderRageTracker()}
                ${this.renderUnarmoredDefenseDisplay()}
                ${this.renderFeatureTree()}
            </div>
        `;

        this.attachEventListeners();
    }

    renderRageTracker() {
        const rageText = this.level >= 20 ? 'Unlimited' : `${this.ragesUsed}/${this.ragesPerDay}`;
        const percentage = this.level >= 20 ? 100 : ((this.ragesPerDay - this.ragesUsed) / this.ragesPerDay) * 100;
        
        return `
            <div class="resource-tracker">
                <div class="resource-name">
                    🔥 Rage ${this.currentlyRaging ? '(ACTIVE)' : ''}
                </div>
                <div class="resource-bar">
                    <div class="resource-fill" style="width: ${percentage}%; background: linear-gradient(90deg, #ff6b6b 0%, #ee5a52 100%);">
                        ${rageText}
                    </div>
                </div>
                <div class="resource-buttons">
                    <button id="rage-enter-btn" ${this.currentlyRaging || this.ragesUsed >= this.ragesPerDay ? 'disabled' : ''}>
                        Enter Rage
                    </button>
                    <button id="rage-end-btn" ${!this.currentlyRaging ? 'disabled' : ''}>
                        End Rage
                    </button>
                    <button id="rage-reset-btn">
                        Long Rest
                    </button>
                </div>
                ${this.currentlyRaging ? this.renderRageBenefits() : ''}
            </div>
        `;
    }

    renderRageBenefits() {
        return `
            <div class="calculation-display" style="margin-top: 10px;">
                <strong style="color: #ff6b6b;">Rage Benefits:</strong>
                <div class="calculation-formula">
                    • Advantage on Strength checks and saves<br>
                    • +${this.rageDamage} damage on melee attacks (STR-based)<br>
                    • Resistance to physical damage (B/P/S)<br>
                    • Cannot cast spells or concentrate
                </div>
            </div>
        `;
    }

    renderUnarmoredDefenseDisplay() {
        const ac = this.calculateUnarmoredDefense();
        const dexMod = calculateModifier(this.stats.dexterity);
        const conMod = calculateModifier(this.stats.constitution);
        
        return `
            <div class="calculation-display">
                <div class="ability-card-name">🛡️ Unarmored Defense</div>
                <div class="calculation-formula">
                    AC = 10 + DEX (${formatModifier(dexMod)}) + CON (${formatModifier(conMod)})
                </div>
                <div class="calculation-result">
                    AC ${ac}
                </div>
            </div>
        `;
    }

    renderFeatureTree() {
        const features = [
            { level: 1, name: 'Rage', desc: `${this.ragesPerDay} uses per day, +${this.rageDamage} damage` },
            { level: 1, name: 'Unarmored Defense', desc: '10 + DEX + CON when not wearing armor' },
            { level: 2, name: 'Reckless Attack', desc: 'Advantage on melee attacks, enemies have advantage on you' },
            { level: 2, name: 'Danger Sense', desc: 'Advantage on DEX saves vs. effects you can see' },
            { level: 3, name: 'Primal Path', desc: this.subclass || 'Choose your path' },
            { level: 5, name: 'Extra Attack', desc: 'Attack twice when you take the Attack action' },
            { level: 5, name: 'Fast Movement', desc: '+10 ft speed when not wearing heavy armor' },
            { level: 7, name: 'Feral Instinct', desc: 'Advantage on initiative, can act in surprise round' },
            { level: 9, name: 'Brutal Critical (1 die)', desc: 'Roll 1 extra weapon damage die on crits' },
            { level: 11, name: 'Relentless Rage', desc: 'Con save to stay at 1 HP when you drop to 0 while raging' },
            { level: 13, name: 'Brutal Critical (2 dice)', desc: 'Roll 2 extra weapon damage dice on crits' },
            { level: 15, name: 'Persistent Rage', desc: 'Rage only ends if you fall unconscious or choose to end it' },
            { level: 17, name: 'Brutal Critical (3 dice)', desc: 'Roll 3 extra weapon damage dice on crits' },
            { level: 18, name: 'Indomitable Might', desc: 'STR checks less than STR score use STR score instead' },
            { level: 20, name: 'Primal Champion', desc: '+4 STR and CON (max 24), unlimited rages' }
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
        const enterBtn = document.getElementById('rage-enter-btn');
        const endBtn = document.getElementById('rage-end-btn');
        const resetBtn = document.getElementById('rage-reset-btn');

        if (enterBtn) {
            enterBtn.addEventListener('click', () => this.enterRage());
        }
        if (endBtn) {
            endBtn.addEventListener('click', () => this.endRage());
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.longRest());
        }
    }

    enterRage() {
        if (this.ragesUsed >= this.ragesPerDay || this.currentlyRaging) return;
        
        this.currentlyRaging = true;
        this.ragesUsed++;
        this.render();
        // Optimistically update UI then notify backend
        this.showNotification('🔥 RAGE ACTIVATED! +' + this.rageDamage + ' damage, advantage on STR checks!');

        // Send to backend if available
        if (this.characterName) {
            fetch(`${API_BASE}/api/barbarian/${encodeURIComponent(this.characterName)}/enter_rage`, {
                method: 'POST', headers: {'Content-Type': 'application/json'}
            }).catch(() => {});
        }
    }

    endRage() {
        if (!this.currentlyRaging) return;
        
        this.currentlyRaging = false;
        this.render();
        this.showNotification('Rage ended.');

        if (this.characterName) {
            fetch(`${API_BASE}/api/barbarian/${encodeURIComponent(this.characterName)}/end_rage`, {
                method: 'POST', headers: {'Content-Type': 'application/json'}
            }).catch(() => {});
        }
    }

    longRest() {
        this.ragesUsed = 0;
        this.currentlyRaging = false;
        this.render();
        this.showNotification('✨ Long rest completed. Rages restored!');

        if (this.characterName) {
            fetch(`${API_BASE}/api/barbarian/${encodeURIComponent(this.characterName)}/long_rest`, {
                method: 'POST', headers: {'Content-Type': 'application/json'}
            }).catch(() => {});
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
        if (this.characterName) {
            fetch(`${API_BASE}/api/barbarian/${encodeURIComponent(this.characterName)}/update_stats`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({stats: stats})
            }).catch(() => {});
        }
    }

    setLevel(level) {
        this.level = parseInt(level) || 1;
        this.updateRageProgression();
        this.render();
        if (this.characterName) {
            fetch(`${API_BASE}/api/barbarian/${encodeURIComponent(this.characterName)}/set_level`, {
                method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({level: this.level})
            }).catch(() => {});
        }
    }

    setSubclass(subclass) {
        this.subclass = subclass;
        this.render();
    }

    setCharacterName(name) {
        this.characterName = name;

        // Ensure backend has this character - create minimal record if missing
        (async () => {
            try {
                const res = await fetch(`${API_BASE}/api/barbarian/${encodeURIComponent(this.characterName)}`);
                if (res.status === 404) {
                    // Create minimal character on backend so subsequent calls succeed
                    await fetch(`${API_BASE}/api/barbarian/${encodeURIComponent(this.characterName)}/create`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            level: this.level || 1,
                            stats: this.stats || {strength:15,dexterity:13,constitution:14,intelligence:10,wisdom:12,charisma:8},
                            race: 'Human',
                            background: ''
                        })
                    });
                }
            } catch (e) {
                // Ignore network errors; keep UI functional offline
                console.warn('Could not verify/create backend character:', e);
            }
        })();
    }
}

// Export for global use
window.BarbarianFeatureManager = BarbarianFeatureManager;

// Auto-initialize if on character creation page
document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.getElementById('char-class');
    if (classSelect && classSelect.value === 'Barbarian') {
        window.barbarianManager = new BarbarianFeatureManager();
    }
});