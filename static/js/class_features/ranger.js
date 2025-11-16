/**
 * Ranger Class - D&D 5e SRD Implementation
 * Derived from the base Character class with full Ranger features
 */

// Assuming base Character class exists in the Head/campaign_manager
const Character = require('./Head/campaign_manager').Character;

class Ranger extends Character {
    /**
     * Ranger class implementation following D&D 5e SRD
     * Inherits from Character and adds Ranger-specific features
     */
    constructor(config = {}) {
        super(config);
        
        // Set class type
        this.char_class = "Ranger";
        
        // Ranger-specific attributes
        this.rangerArchetype = config.rangerArchetype || ""; // "Hunter" or "Beast Master"
        
        // Favored Enemy mechanics
        this.favoredEnemies = config.favoredEnemies || []; // List of enemy types
        this.favoredEnemyLanguages = config.favoredEnemyLanguages || []; // Languages learned
        
        // Natural Explorer mechanics
        this.favoredTerrains = config.favoredTerrains || []; // List of terrain types
        
        // Fighting Style
        this.fightingStyle = config.fightingStyle || ""; // "Archery", "Defense", "Dueling", or "Two-Weapon Fighting"
        
        // Spellcasting
        this.spellsKnown = config.spellsKnown || []; // Known spells
        this.spellSlots = config.spellSlots || {}; // Available slots by level
        this.spellsPrepared = config.spellsPrepared || []; // Prepared spells
        
        // Class features
        this.primevalAwarenessActive = false;
        this.landsStrideActive = false;
        this.hideInPlainSightActive = false;
        this.vanishActive = false;
        this.feralSensesActive = false;
        this.foeSlayerActive = false;
        
        // Hunter archetype features
        this.huntersPrey = config.huntersPrey || ""; // "Colossus Slayer", "Giant Killer", or "Horde Breaker"
        this.defensiveTactics = config.defensiveTactics || ""; // "Escape the Horde", "Multiattack Defense", or "Steel Will"
        this.multiattack = config.multiattack || ""; // "Volley" or "Whirlwind Attack"
        this.superiorHuntersDefense = config.superiorHuntersDefense || ""; // "Evasion", "Stand Against the Tide", or "Uncanny Dodge"
        
        // Set initial stats if not provided
        if (!this.stats || Object.values(this.stats).every(v => v === 10)) {
            // Rangers typically have high DEX and WIS
            this.stats = {
                strength: 12,
                dexterity: 15,
                constitution: 14,
                intelligence: 10,
                wisdom: 13,
                charisma: 8
            };
        }
        
        // Set hit points based on level (1d10 per level)
        if (this.level === 1) {
            this.max_hp = 10 + this._getModifier("constitution");
            this.hp = this.max_hp;
        }
        
        // Initialize proficiencies if empty
        if (!this.skillProficiencies || this.skillProficiencies.length === 0) {
            // Rangers choose three from: Animal Handling, Athletics, Insight, 
            // Investigation, Nature, Perception, Stealth, and Survival
            this.skillProficiencies = ["Perception", "Stealth", "Survival"];
        }
        
        if (!this.languagesKnown || this.languagesKnown.length === 0) {
            this.languagesKnown = ["Common"];
        }
        
        // Initialize spell slots
        this._initializeSpellSlots();
        
        // Apply level-based features
        this.applyLevelFeatures();
    }
    
    _getModifier(ability) {
        /** Calculate ability modifier */
        return Math.floor((this.stats[ability] - 10) / 2);
    }
    
    _initializeSpellSlots() {
        /** Initialize spell slots based on level */
        this.spellSlots = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0};
        
        if (this.level >= 2) {
            this.spellSlots[1] = 2;
        }
        if (this.level >= 3) {
            this.spellSlots[1] = 3;
        }
        if (this.level >= 5) {
            this.spellSlots[1] = 4;
            this.spellSlots[2] = 2;
        }
        if (this.level >= 7) {
            this.spellSlots[2] = 3;
        }
        if (this.level >= 9) {
            this.spellSlots[3] = 2;
        }
        if (this.level >= 11) {
            this.spellSlots[3] = 3;
        }
        if (this.level >= 13) {
            this.spellSlots[4] = 1;
        }
        if (this.level >= 15) {
            this.spellSlots[4] = 2;
        }
        if (this.level >= 17) {
            this.spellSlots[5] = 1;
        }
        if (this.level >= 19) {
            this.spellSlots[5] = 2;
        }
    }
    
    applyLevelFeatures() {
        /** Apply features based on current level according to SRD */
        // Level 1 features
        if (this.level >= 1) {
            // These would typically be chosen during character creation
            // For now, we'll set defaults
            if (this.favoredEnemies.length === 0) {
                this.favoredEnemies = ["Beasts"];
                this.favoredEnemyLanguages = ["Sylvan"]; // Example language
            }
            if (this.favoredTerrains.length === 0) {
                this.favoredTerrains = ["Forest"];
            }
        }
        
        // Level 2 features
        if (this.level >= 2) {
            if (!this.fightingStyle) {
                this.fightingStyle = "Archery"; // Default choice
            }
            this._initializeSpellSlots();
        }
        
        // Level 3 features
        if (this.level >= 3) {
            this.primevalAwarenessActive = true;
            if (!this.rangerArchetype) {
                this.rangerArchetype = "Hunter"; // Default archetype
            }
            if (this.rangerArchetype === "Hunter" && !this.huntersPrey) {
                this.huntersPrey = "Colossus Slayer"; // Default Hunter feature
            }
        }
        
        // Level 5 features
        if (this.level >= 5) {
            // Extra Attack handled in attack logic
        }
        
        // Level 6 features
        if (this.level >= 6) {
            // Additional favored enemy and terrain
            if (this.favoredEnemies.length < 2) {
                this.favoredEnemies.push("Humanoids (Gnolls, Orcs)");
                this.favoredEnemyLanguages.push("Orc");
            }
            if (this.favoredTerrains.length < 2) {
                this.favoredTerrains.push("Mountain");
            }
        }
        
        // Level 7 features
        if (this.level >= 7 && this.rangerArchetype === "Hunter") {
            if (!this.defensiveTactics) {
                this.defensiveTactics = "Escape the Horde"; // Default
            }
        }
        
        // Level 8 features
        if (this.level >= 8) {
            this.landsStrideActive = true;
        }
        
        // Level 10 features
        if (this.level >= 10) {
            this.hideInPlainSightActive = true;
            if (this.favoredTerrains.length < 3) {
                this.favoredTerrains.push("Swamp");
            }
        }
        
        // Level 11 features
        if (this.level >= 11 && this.rangerArchetype === "Hunter") {
            if (!this.multiattack) {
                this.multiattack = "Volley"; // Default
            }
        }
        
        // Level 14 features
        if (this.level >= 14) {
            this.vanishActive = true;
            if (this.favoredEnemies.length < 3) {
                this.favoredEnemies.push("Undead");
                this.favoredEnemyLanguages.push("Infernal");
            }
        }
        
        // Level 15 features
        if (this.level >= 15 && this.rangerArchetype === "Hunter") {
            if (!this.superiorHuntersDefense) {
                this.superiorHuntersDefense = "Evasion"; // Default
            }
        }
        
        // Level 18 features
        if (this.level >= 18) {
            this.feralSensesActive = true;
        }
        
        // Level 20 features
        if (this.level >= 20) {
            this.foeSlayerActive = true;
        }
    }
    
    getSpellSaveDC() {
        /** Calculate spell save DC: 8 + proficiency bonus + Wisdom modifier */
        return 8 + this.getProficiencyBonus() + this._getModifier("wisdom");
    }
    
    getSpellAttackBonus() {
        /** Calculate spell attack bonus: proficiency bonus + Wisdom modifier */
        return this.getProficiencyBonus() + this._getModifier("wisdom");
    }
    
    getProficiencyBonus() {
        /** Calculate proficiency bonus based on level */
        if (this.level < 5) {
            return 2;
        } else if (this.level < 9) {
            return 3;
        } else if (this.level < 13) {
            return 4;
        } else if (this.level < 17) {
            return 5;
        } else {
            return 6;
        }
    }
    
    getFavoredEnemyBenefits(enemyType) {
        /** Get benefits against favored enemies */
        const isFavored = this.favoredEnemies.includes(enemyType) || 
                         this.favoredEnemies.some(enemy => 
                             enemy.toLowerCase().includes(enemyType.toLowerCase())
                         );
        
        return {
            isFavored: isFavored,
            advantageTracking: isFavored,
            advantageRecallInformation: isFavored,
            wisdomModifierToAttack: isFavored && this.foeSlayerActive
        };
    }
    
    getNaturalExplorerBenefits(terrainType) {
        /** Get benefits in favored terrain */
        const isFavored = this.favoredTerrains.includes(terrainType);
        
        return {
            isFavored: isFavored,
            doubleProficiency: isFavored,
            noDifficultTerrain: isFavored,
            cannotGetLost: isFavored,
            remainAlertWhileTraveling: isFavored,
            stealthAtNormalPace: isFavored,
            doubleForaging: isFavored,
            enhancedTracking: isFavored
        };
    }
    
    getFightingStyleBenefits() {
        /** Get benefits from fighting style */
        const benefits = {
            "Archery": {rangedAttackBonus: 2},
            "Defense": {acBonus: 1},
            "Dueling": {damageBonus: 2, conditions: ["oneHandedMelee", "noOtherWeapons"]},
            "Two-Weapon Fighting": {addAbilityModifierOffhand: true}
        };
        return benefits[this.fightingStyle] || {};
    }
    
    usePrimevalAwareness(spellSlotLevel) {
        /**
         * Use Primeval Awareness feature
         * Returns detection information for creature types
         */
        if (!this.spellSlots[spellSlotLevel] || this.spellSlots[spellSlotLevel] <= 0) {
            return {success: false, message: "No spell slot available"};
        }
        
        // Consume spell slot
        this.spellSlots[spellSlotLevel] -= 1;
        
        const duration = spellSlotLevel; // 1 minute per spell slot level
        
        return {
            success: true,
            duration: duration,
            range: "1 mile (6 miles in favored terrain)",
            creatureTypes: [
                "aberrations", "celestials", "dragons", "elementals", 
                "fey", "fiends", "undead"
            ],
            detectsPresence: true,
            revealsLocation: false,
            revealsNumber: false
        };
    }
    
    hideInPlainSight() {
        /** Use Hide in Plain Sight feature */
        if (!this.hideInPlainSightActive) {
            return {success: false, message: "Feature not available"};
        }
        
        return {
            success: true,
            preparationTime: "1 minute",
            materialsNeeded: ["natural materials"],
            stealthBonus: 10,
            conditions: ["must remain still", "against solid surface"],
            endsOn: ["movement", "action", "reaction"]
        };
    }
    
    getHunterFeatures() {
        /** Get Hunter archetype features */
        if (this.rangerArchetype !== "Hunter") {
            return {};
        }
        
        const features = {
            huntersPrey: this.huntersPrey,
            defensiveTactics: this.defensiveTactics,
            multiattack: this.multiattack,
            superiorHuntersDefense: this.superiorHuntersDefense
        };
        
        // Add descriptions
        const descriptions = {
            "Colossus Slayer": "Extra 1d8 damage vs wounded creatures (once per turn)",
            "Giant Killer": "Reaction attack vs Large+ creatures that attack you",
            "Horde Breaker": "Extra attack vs different creature within 5ft of target",
            "Escape the Horde": "Disadvantage on opportunity attacks vs you",
            "Multiattack Defense": "+4 AC vs subsequent attacks from same creature",
            "Steel Will": "Advantage vs frightened saves",
            "Volley": "Ranged attack vs all creatures in 10ft radius",
            "Whirlwind Attack": "Melee attack vs all creatures within 5ft",
            "Evasion": "No damage on successful Dex saves, half on failed",
            "Stand Against the Tide": "Redirect missed melee attacks to other creatures",
            "Uncanny Dodge": "Use reaction to halve attack damage"
        };
        
        return {
            features: features,
            descriptions: descriptions
        };
    }
    
    calculateAttackBonus(weaponType, isRanged = false) {
        /** Calculate attack bonus with fighting style benefits */
        let baseBonus = this.getProficiencyBonus() + this._getModifier("dexterity");
        
        // Apply fighting style benefits
        const styleBenefits = this.getFightingStyleBenefits();
        
        if (isRanged && styleBenefits.rangedAttackBonus) {
            baseBonus += styleBenefits.rangedAttackBonus;
        }
        
        return baseBonus;
    }
    
    calculateDamageBonus(weaponType, isMainHand = true) {
        /** Calculate damage bonus with fighting style benefits */
        let baseBonus = this._getModifier("dexterity");
        
        // Apply fighting style benefits
        const styleBenefits = this.getFightingStyleBenefits();
        
        if (styleBenefits.damageBonus && isMainHand && this._meetsDuelingConditions()) {
            baseBonus += styleBenefits.damageBonus;
        }
        
        return baseBonus;
    }
    
    _meetsDuelingConditions() {
        /** Check if conditions for Dueling fighting style are met */
        if (this.fightingStyle !== "Dueling") {
            return false;
        }
        
        // In a real implementation, this would check equipped weapons
        // For now, we'll assume the conditions can be met
        return true;
    }
    
    getExtraAttackCount() {
        /** Get number of attacks (2 at level 5+) */
        return this.level >= 5 ? 2 : 1;
    }
    
    longRest() {
        /** Reset resources on long rest */
        this._initializeSpellSlots(); // Reset spell slots
        this.hp = this.max_hp;
    }
    
    levelUp() {
        /** Level up the ranger */
        this.level += 1;
        
        // Increase HP (1d10 + CON mod per level, or 6 + CON mod average)
        const hpGain = 6 + this._getModifier("constitution");
        this.max_hp += hpGain;
        this.hp += hpGain;
        
        // Reapply level-based features
        this.applyLevelFeatures();
        
        // Update spell slots
        this._initializeSpellSlots();
    }
    
    getCharacterSheet() {
        /** Generate a complete character sheet */
        return {
            name: this.name,
            race: this.race,
            class: `${this.char_class} ${this.level}`,
            background: this.background,
            alignment: this.alignment,
            rangerArchetype: this.rangerArchetype || "Not chosen (Level 3+)",
            
            hitPoints: `${this.hp}/${this.max_hp}`,
            armorClass: this.ac,
            speed: 30,
            
            abilityScores: this.stats,
            proficiencyBonus: this.getProficiencyBonus(),
            
            savingThrows: {
                strength: this._getModifier("strength") + this.getProficiencyBonus(),
                dexterity: this._getModifier("dexterity") + this.getProficiencyBonus()
            },
            
            skills: this.skillProficiencies,
            languages: [...this.languagesKnown, ...this.favoredEnemyLanguages],
            
            rangerFeatures: {
                favoredEnemies: this.favoredEnemies,
                favoredTerrains: this.favoredTerrains,
                fightingStyle: this.fightingStyle,
                spellcasting: `DC ${this.getSpellSaveDC()}, +${this.getSpellAttackBonus()} to hit`,
                primevalAwareness: this.primevalAwarenessActive,
                landsStride: this.landsStrideActive,
                hideInPlainSight: this.hideInPlainSightActive,
                vanish: this.vanishActive,
                feralSenses: this.feralSensesActive,
                foeSlayer: this.foeSlayerActive,
                extraAttack: this.level >= 5
            },
            
            spellSlots: this.spellSlots,
            spellsKnown: this.spellsKnown,
            
            hunterFeatures: this.rangerArchetype === "Hunter" ? this.getHunterFeatures() : {},
            
            inventory: this.inventory,
            currency: this.currency,
            totalWealthGP: this.getTotalGoldValue(),
            
            personality: {
                traits: this.personalityTraits,
                ideal: this.ideal,
                bond: this.bond,
                flaw: this.flaw
            },
            
            notes: this.notes
        };
    }
    
    toString() {
        /** String representation */
        const archetypeStr = this.rangerArchetype ? ` (${this.rangerArchetype})` : "";
        const spellsStr = this.level >= 2 ? ` | Spells: ${Object.values(this.spellSlots).reduce((a, b) => a + b, 0)} slots` : "";
        return `${this.name} - Level ${this.level} ${this.race} ${this.char_class}${archetypeStr} | HP: ${this.hp}/${this.max_hp} | AC: ${this.ac}${spellsStr}`;
    }
}

// Example usage and testing
if (require.main === module) {
    // Create a new Ranger
    const ranger = new Ranger({
        name: "Aragorn",
        race: "Human",
        char_class: "Ranger",
        background: "Outlander",
        level: 1,
        stats: {
            strength: 14,
            dexterity: 16,
            constitution: 14,
            intelligence: 12,
            wisdom: 15,
            charisma: 10
        },
        alignment: "Neutral Good",
        personalityTraits: ["I feel far more comfortable around animals than people", "I'm always picking things up and fiddling with them"],
        ideal: "Greater Good. It is each person's responsibility to make the most happiness for the whole tribe.",
        bond: "I suffer awful visions of a coming disaster and will do anything to prevent it.",
        flaw: "I am too enamored of ale, wine, and other intoxicants."
    });
    
    // Set starting equipment
    ranger.inventory = ["Longbow", "Arrows (20)", "Shortsword", "Shortsword", "Leather Armor", "Explorer's Pack"];
    
    console.log("=".repeat(60));
    console.log("RANGER CHARACTER SHEET");
    console.log("=".repeat(60));
    console.log(ranger.toString());
    console.log();
    
    // Display character sheet
    const sheet = ranger.getCharacterSheet();
    console.log(`Name: ${sheet.name}`);
    console.log(`Class: ${sheet.class}`);
    console.log(`Race: ${sheet.race}`);
    console.log(`Background: ${sheet.background}`);
    console.log(`Alignment: ${sheet.alignment}`);
    console.log();
    
    console.log(`HP: ${sheet.hitPoints} | AC: ${sheet.armorClass} | Speed: ${sheet.speed} ft`);
    console.log();
    
    console.log("Ability Scores:");
    for (const [ability, score] of Object.entries(sheet.abilityScores)) {
        const modifier = Math.floor((score - 10) / 2);
        const sign = modifier >= 0 ? '+' : '';
        console.log(`  ${ability.charAt(0).toUpperCase() + ability.slice(1)}: ${score} (${sign}${modifier})`);
    }
    console.log();
    
    console.log(`Proficiency Bonus: +${sheet.proficiencyBonus}`);
    console.log();
    
    console.log("Favored Enemies:");
    for (const enemy of sheet.rangerFeatures.favoredEnemies) {
        console.log(`  • ${enemy}`);
    }
    console.log();
    
    console.log("Favored Terrains:");
    for (const terrain of sheet.rangerFeatures.favoredTerrains) {
        console.log(`  • ${terrain}`);
    }
    console.log();
    
    console.log(`Fighting Style: ${sheet.rangerFeatures.fightingStyle}`);
    console.log(`Spellcasting: ${sheet.rangerFeatures.spellcasting}`);
    console.log();
    
    console.log("Class Features:");
    for (const [feature, value] of Object.entries(sheet.rangerFeatures)) {
        if (!["favoredEnemies", "favoredTerrains", "fightingStyle", "spellcasting"].includes(feature)) {
            if (value && value !== false) {
                console.log(`  • ${feature}: ${typeof value === 'string' ? value : '✓'}`);
            }
        }
    }
    console.log();
    
    console.log("Spell Slots:");
    for (const [level, slots] of Object.entries(sheet.spellSlots)) {
        if (slots > 0) {
            console.log(`  Level ${level}: ${slots}`);
        }
    }
    console.log();
    
    console.log("Equipment:");
    for (const item of ranger.inventory) {
        console.log(`  • ${item}`);
    }
    console.log();
    
    // Test leveling up
    console.log("=".repeat(60));
    console.log("TESTING LEVEL UP");
    console.log("=".repeat(60));
    
    console.log(`\nCurrent level: ${ranger.level}`);
    console.log(`Current HP: ${ranger.hp}/${ranger.max_hp}`);
    
    ranger.levelUp(); // Level 2
    ranger.levelUp(); // Level 3
    ranger.rangerArchetype = "Hunter";
    ranger.applyLevelFeatures();
    
    console.log(`\nAfter leveling up to 3:`);
    console.log(`New level: ${ranger.level}`);
    console.log(`New HP: ${ranger.hp}/${ranger.max_hp}`);
    console.log(`Features unlocked: Fighting Style, Spellcasting, Primeval Awareness, Hunter Archetype`);
    console.log(`Hunter's Prey: ${ranger.huntersPrey}`);
    
    // Test favored enemy benefits
    console.log("\n" + "=".repeat(60));
    console.log("TESTING FAVORED ENEMY");
    console.log("=".repeat(60));
    
    const benefits = ranger.getFavoredEnemyBenefits("Beasts");
    console.log(`Against Beasts (Favored Enemy):`);
    console.log(`  Advantage on tracking: ${benefits.advantageTracking}`);
    console.log(`  Advantage on recall: ${benefits.advantageRecallInformation}`);
    
    // Test natural explorer benefits
    console.log("\n" + "=".repeat(60));
    console.log("TESTING NATURAL EXPLORER");
    console.log("=".repeat(60));
    
    const terrainBenefits = ranger.getNaturalExplorerBenefits("Forest");
    console.log(`In Forest (Favored Terrain):`);
    console.log(`  Double proficiency: ${terrainBenefits.doubleProficiency}`);
    console.log(`  No difficult terrain: ${terrainBenefits.noDifficultTerrain}`);
    console.log(`  Cannot get lost: ${terrainBenefits.cannotGetLost}`);
    
    console.log("\n" + "=".repeat(60));
    console.log(ranger.toString());
    console.log("=".repeat(60));
}

module.exports = Ranger;