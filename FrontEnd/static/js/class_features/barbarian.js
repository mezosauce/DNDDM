/**
 * Barbarian Feature Manager
 * Client-side tracking of Barbarian class features and resources
 */

class BarbarianFeatureManager extends BaseFeatureManager {
    constructor() {
        super();
        this.className = 'Barbarian';
        
        // Rage tracking
        this.ragesPerDay = 2;
        this.ragesUsed = 0;
        this.rageDamage = 2;
        this.currentlyRaging = false;
        
        // Level-based features
        this.recklessAttackAvailable = false;
        this.dangerSenseActive = false;
        this.fastMovement = 0;
        this.brutalCriticalDice = 0;
        this.feralInstinct = false;
        this.relentlessRage = false;
        this.persistentRage = false;
        this.indomitableMight = false;
    }
    
    /**
     * Initialize from character data
     */
    initialize(level, stats) {
        this.level = level;
        this.stats = stats;
        
        // Calculate level-based resources
        this.calculateLevelFeatures();
        
        console.log(`[BarbarianFeatures] Initialized level ${level} barbarian`);
    }
    
    /**
     * Calculate features based on level
     */
    calculateLevelFeatures() {
        // Rage progression
        if (this.level >= 1) {
            this.ragesPerDay = 2;
            this.rageDamage = 2;
        }
        if (this.level >= 3) this.ragesPerDay = 3;
        if (this.level >= 6) this.ragesPerDay = 4;
        if (this.level >= 9) {
            this.rageDamage = 3;
            this.brutalCriticalDice = 1;
        }
        if (this.level >= 12) this.ragesPerDay = 5;
        if (this.level >= 13) this.brutalCriticalDice = 2;
        if (this.level >= 16) this.rageDamage = 4;
        if (this.level >= 17) {
            this.ragesPerDay = 6;
            this.brutalCriticalDice = 3;
        }
        if (this.level >= 20) this.ragesPerDay = 999; // Unlimited
        
        // Class features by level
        if (this.level >= 2) {
            this.recklessAttackAvailable = true;
            this.dangerSenseActive = true;
        }
        if (this.level >= 5) this.fastMovement = 10;
        if (this.level >= 7) this.feralInstinct = true;
        if (this.level >= 11) this.relentlessRage = true;
        if (this.level >= 15) this.persistentRage = true;
        if (this.level >= 18) this.indomitableMight = true;
    }
    
    /**
     * Update state from combat data
     */
    updateFromCombatState(participantData) {
        if (participantData.rage) {
            this.currentlyRaging = participantData.rage.active || false;
            const remaining = participantData.rage.uses_remaining || 0;
            this.ragesUsed = this.ragesPerDay - remaining;
        }
    }
    
    /**
     * Get available actions for the action menu
     */
    getAvailableActions() {
        const actions = [];
        
        // Rage
        if (!this.currentlyRaging && this.ragesUsed < this.ragesPerDay) {
            actions.push({
                name: 'Rage',
                description: `Enter a rage: +${this.rageDamage} damage, advantage on STR checks, resistance to physical damage`,
                cost: `${this.ragesUsed}/${this.ragesPerDay} uses`,
                available: true,
                type: 'skill',
                target_type: 'self',
                data: { skill_name: 'Rage' },
                auto_target_single: true
            });
        }
        
        // Reckless Attack (Level 2+)
        if (this.level >= 2) {
            actions.push({
                name: 'Reckless Attack',
                description: 'Gain advantage on attack rolls this turn, enemies have advantage against you',
                cost: 'Free (once per turn)',
                available: true,
                type: 'skill',
                target_type: 'enemy',
                data: { skill_name: 'Reckless Attack' }
            });
        }
        
        return actions;
    }
    
    /**
     * Attempt to enter rage
     */
    enterRage() {
        if (this.ragesUsed >= this.ragesPerDay) {
            console.log('[BarbarianFeatures] No rage uses remaining');
            return false;
        }
        if (this.currentlyRaging) {
            console.log('[BarbarianFeatures] Already raging');
            return false;
        }
        
        this.currentlyRaging = true;
        this.ragesUsed++;
        console.log(`[BarbarianFeatures] Entered rage (${this.ragesUsed}/${this.ragesPerDay} used)`);
        return true;
    }
    
    /**
     * End rage
     */
    endRage() {
        this.currentlyRaging = false;
        console.log('[BarbarianFeatures] Rage ended');
    }
    
    /**
     * Get ability modifier
     */
    getModifier(ability) {
        const score = this.stats[ability] || 10;
        return Math.floor((score - 10) / 2);
    }
    
    /**
     * Get proficiency bonus based on level
     */
    getProficiencyBonus() {
        if (this.level < 5) return 2;
        if (this.level < 9) return 3;
        if (this.level < 13) return 4;
        if (this.level < 17) return 5;
        return 6;
    }
    
    /**
     * Get display info for UI
     */
    getDisplayInfo() {
        return {
            className: this.className,
            level: this.level,
            features: {
                rage: {
                    active: this.currentlyRaging,
                    uses: `${this.ragesUsed}/${this.ragesPerDay}`,
                    damage: `+${this.rageDamage}`,
                    remaining: this.ragesPerDay - this.ragesUsed
                },
                recklessAttack: this.recklessAttackAvailable,
                dangerSense: this.dangerSenseActive,
                fastMovement: this.fastMovement > 0 ? `+${this.fastMovement}ft` : null,
                brutalCritical: this.brutalCriticalDice > 0 ? `+${this.brutalCriticalDice} dice` : null,
                feralInstinct: this.feralInstinct,
                relentlessRage: this.relentlessRage,
                persistentRage: this.persistentRage,
                indomitableMight: this.indomitableMight
            }
        };
    }
    
    /**
     * Get feature descriptions for tooltip/info
     */
    getFeatureDescriptions() {
        const descriptions = [];
        
        if (this.currentlyRaging) {
            descriptions.push({
                name: 'Rage (Active)',
                description: `+${this.rageDamage} melee damage, advantage on STR checks/saves, resistance to physical damage`
            });
        }
        
        if (this.recklessAttackAvailable) {
            descriptions.push({
                name: 'Reckless Attack',
                description: 'Gain advantage on melee attacks, but attacks against you have advantage'
            });
        }
        
        if (this.dangerSenseActive) {
            descriptions.push({
                name: 'Danger Sense',
                description: 'Advantage on DEX saves against effects you can see'
            });
        }
        
        if (this.fastMovement > 0) {
            descriptions.push({
                name: 'Fast Movement',
                description: `+${this.fastMovement}ft movement speed when not wearing heavy armor`
            });
        }
        
        if (this.brutalCriticalDice > 0) {
            descriptions.push({
                name: 'Brutal Critical',
                description: `Roll ${this.brutalCriticalDice} additional weapon damage ${this.brutalCriticalDice === 1 ? 'die' : 'dice'} on critical hits`
            });
        }
        
        return descriptions;
    }
}

// Export to global scope - THIS IS CRITICAL!
window.BarbarianFeatureManager = BarbarianFeatureManager;