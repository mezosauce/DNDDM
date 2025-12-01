/**
 * Class Selector and Feature Display Manager
 * Handles class selection, metadata display, and class-specific UI initialization
 */

class ClassSelector {
    constructor() {
        this.selectedClass = '';
        this.classMetadata = {};
        this.classManagers = {};
        this.loadMetadata();
    }

    async loadMetadata() {
        try {
            const response = await fetch('/static/data/class_metadata.json');
            this.classMetadata = await response.json();
            console.log('✓ Class metadata loaded');
        } catch (error) {
            console.error('Failed to load class metadata:', error);
        }
    }

    selectClass(className) {
        this.selectedClass = className;
        this.updateClassInfo();
        this.initializeClassManager();
    }

    updateClassInfo() {
        const metadata = this.classMetadata[this.selectedClass];
        if (!metadata) return;

        // Update info panel
        this.updateElement('class-hit-die', metadata.hit_die);
        this.updateElement('class-primary-abilities', metadata.primary_abilities.join(', '));
        
        // Update saving throw proficiencies
        if (metadata.saves) {
            this.updateElement('class-saves', metadata.saves.join(', '));
        }
        
        // Update skill proficiencies info
        if (metadata.skills) {
            const skillInfo = `Choose ${metadata.skills.choose} from: ${metadata.skills.from.join(', ')}`;
            this.updateElement('class-skills', skillInfo);
        }

        const level = parseInt(document.getElementById('char-level')?.value) || 1;
        
        // Update class abilities for current level
        this.updateClassAbilities(metadata, level);
    }

    updateClassAbilities(metadata, level) {
        const container = document.getElementById('class-abilities-list');
        if (!container) return;

        if (!metadata || !metadata.features_by_level) {
            container.innerHTML = '<p style="color: #888;">No abilities data available</p>';
            return;
        }

        let html = '<div class="abilities-full-grid">';
        html += '<div class="abilities-grid-header"><span>Level</span><span>Abilities</span></div>';
        
        for (let lvl = 1; lvl <= 20; lvl++) {
            const features = metadata.features_by_level[lvl.toString()] || [];
            const isUnlocked = lvl <= level;
            const hasFeatures = features.length > 0;
            
            html += `
                <div class="ability-row ${isUnlocked ? 'unlocked' : 'locked'}">
                    <div class="ability-level-cell">${lvl}</div>
                    <div class="ability-features-cell">
                        ${hasFeatures ? features.map(f => `<span class="ability-tag">${f}</span>`).join('') : '<span class="no-ability">—</span>'}
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        container.innerHTML = html;
    }

    updateElement(id, text) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = text;
        }
    }


    initializeClassManager() {
        // Clean up existing managers
        Object.keys(this.classManagers).forEach(key => {
            this.classManagers[key] = null;
        });

        // Get current stats and level
        const level = parseInt(document.getElementById('char-level')?.value) || 1;
        const stats = this.getCurrentStats();

        // Create/update class-specific container
        this.createClassFeaturesContainer();

        // Initialize class-specific manager
        switch(this.selectedClass) {
            case 'Barbarian':
                if (window.BarbarianFeatureManager) {
                    this.classManagers.Barbarian = new BarbarianFeatureManager();
                    this.classManagers.Barbarian.initialize(level, stats);
                }
                break;
            
            case 'Bard':
                if (window.BardFeatureManager) {
                    this.classManagers.Bard = new BardFeatureManager();
                    this.classManagers.Bard.initialize(level, stats);
                }
                break;

            case 'Cleric':
                if (window.ClericFeatureManager) {
                    this.classManagers.Cleric = new ClericFeatureManager();
                    this.classManagers.Cleric.initialize(level, stats);
                }
                break;

            case 'Druid':
                if (window.DruidFeatureManager) {
                    this.classManagers.Druid = new DruidFeatureManager();
                    this.classManagers.Druid.initialize(level, stats);
                }
                break;

            default:
                this.showGenericFeatures(level);
        }
    }

    createClassFeaturesContainer() {
        // Get the parent container where class features should be rendered
        const parentContainer = document.getElementById('class-features-container');
        if (!parentContainer) return;

        // Clear any existing class feature containers
        parentContainer.innerHTML = '';

        // Create container for the selected class
        const classContainerId = `${this.selectedClass.toLowerCase()}-features`;
        const container = document.createElement('div');
        container.id = classContainerId;
        container.className = 'class-features-wrapper';
        parentContainer.appendChild(container);
    }

    getCurrentStats() {
        return {
            strength: parseInt(document.getElementById('str')?.value) || 10,
            dexterity: parseInt(document.getElementById('dex')?.value) || 10,
            constitution: parseInt(document.getElementById('con')?.value) || 10,
            intelligence: parseInt(document.getElementById('int')?.value) || 10,
            wisdom: parseInt(document.getElementById('wis')?.value) || 10,
            charisma: parseInt(document.getElementById('cha')?.value) || 10
        };
    }

    showGenericFeatures(level) {
        const container = document.getElementById('class-features-container');
        if (!container) return;

        const metadata = this.classMetadata[this.selectedClass];
        if (!metadata || !metadata.features_by_level) {
            container.innerHTML = '<p style="color: #888; text-align: center;">Select a class to view features</p>';
            return;
        }

        // Display generic feature list
        let html = '<div class="class-specific-section active">';
        html += `<div class="class-section-header">📖 ${this.selectedClass} Features</div>`;
        html += '<div class="feature-tree">';

        for (let lvl = 1; lvl <= 20; lvl++) {
            const features = metadata.features_by_level[lvl.toString()];
            if (features && features.length > 0) {
                features.forEach(feature => {
                    const unlocked = lvl <= level;
                    html += `
                        <div class="feature-node ${unlocked ? 'unlocked' : 'locked'}">
                            <div class="feature-level">Lv ${lvl}</div>
                            <div style="flex: 1;">
                                <div class="feature-name">${feature}</div>
                            </div>
                        </div>
                    `;
                });
            }
        }

        html += '</div></div>';
        container.innerHTML = html;
    }

    updateLevel(newLevel) {
        const level = parseInt(newLevel) || 1;
        
        // Update class abilities display
        const metadata = this.classMetadata[this.selectedClass];
        if (metadata) {
            this.updateClassAbilities(metadata, level);
        }
        
        // Update class manager if exists
        const manager = this.classManagers[this.selectedClass];
        if (manager && typeof manager.setLevel === 'function') {
            manager.setLevel(level);
        } else if (this.selectedClass) {
            // Update generic features or reinitialize
            this.initializeClassManager();
        }
    }

    updateStats() {
        const stats = this.getCurrentStats();
        const manager = this.classManagers[this.selectedClass];
        
        if (manager && typeof manager.updateStats === 'function') {
            manager.updateStats(stats);
        }
    }

    getSelectedClassMetadata() {
        return this.classMetadata[this.selectedClass];
    }

}

// Initialize global class selector
window.classSelector = new ClassSelector();

// Set up event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Class selection
    const classSelect = document.getElementById('char-class');
    if (classSelect) {
        classSelect.addEventListener('change', (e) => {
            window.classSelector.selectClass(e.target.value);
        });
    }

    // Level changes
    const levelInput = document.getElementById('char-level');
    if (levelInput) {
        levelInput.addEventListener('change', (e) => {
            window.classSelector.updateLevel(e.target.value);
        });
        levelInput.addEventListener('input', (e) => {
            window.classSelector.updateLevel(e.target.value);
        });
    }

    // Stat changes
    ['str', 'dex', 'con', 'int', 'wis', 'cha'].forEach(stat => {
        const input = document.getElementById(stat);
        if (input) {
            input.addEventListener('change', () => {
                window.classSelector.updateStats();
            });
        }
    });
});