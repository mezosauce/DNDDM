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
        this.updateElement('class-saves', metadata.saves.join(', '));
        this.updateElement('class-armor-prof', metadata.armor_proficiencies.join(', '));
        this.updateElement('class-weapon-prof', metadata.weapon_proficiencies.join(', '));

        // Update skill info
        const skillInfo = `Choose ${metadata.skills.choose} from: ${metadata.skills.from.join(', ')}`;
        this.updateElement('skill-class-info', skillInfo);

        // Show subclass selector if appropriate
        const level = parseInt(document.getElementById('char-level')?.value) || 1;
        this.updateSubclassSelector(level);
    }

    updateElement(id, text) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = text;
        }
    }

    updateSubclassSelector(level) {
        const metadata = this.classMetadata[this.selectedClass];
        if (!metadata || !metadata.subclasses) return;

        const container = document.getElementById('subclass-selector-container');
        const select = document.getElementById('subclass-select');
        const levelReq = document.getElementById('subclass-level-req');

        if (!container || !select || !levelReq) return;

        levelReq.textContent = metadata.subclasses.level;

        if (level >= metadata.subclasses.level) {
            container.style.display = 'block';
            
            // Populate options
            select.innerHTML = `<option value="">Choose ${metadata.subclasses.name}...</option>`;
            metadata.subclasses.options.forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.name;
                opt.textContent = option.name;
                opt.title = option.description;
                select.appendChild(opt);
            });
        } else {
            container.style.display = 'none';
        }
    }

    initializeClassManager() {
        // Clean up existing manager
        if (this.classManagers[this.selectedClass]) {
            this.classManagers[this.selectedClass] = null;
        }

        // Get current stats and level
        const level = parseInt(document.getElementById('char-level')?.value) || 1;
        const stats = this.getCurrentStats();
        const subclass = document.getElementById('subclass-select')?.value || '';

        // Initialize class-specific container
        this.createClassFeaturesContainer();

        // Initialize class-specific manager
        switch(this.selectedClass) {
            case 'Barbarian':
                if (window.BarbarianFeatureManager) {
                    this.classManagers.Barbarian = new BarbarianFeatureManager();
                    this.classManagers.Barbarian.initialize(level, stats, subclass);
                }
                break;
            
            case 'Bard':
                if (window.BardFeatureManager) {
                    this.classManagers.Bard = new BardFeatureManager();
                    this.classManagers.Bard.initialize(level, stats, subclass);
                }
                break;

            // Add other classes as they're implemented
            default:
                this.showGenericFeatures(level);
        }
    }

    createClassFeaturesContainer() {
        // Check if container exists
        let container = document.getElementById('barbarian-features');
        if (!container) {
            // Create it in the appropriate tab
            const detailsTab = document.getElementById('tab-details');
            if (detailsTab) {
                container = document.createElement('div');
                container.id = 'barbarian-features';
                detailsTab.insertBefore(container, detailsTab.firstChild);
            }
        }
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
        const container = document.getElementById('barbarian-features');
        if (!container) return;

        const metadata = this.classMetadata[this.selectedClass];
        if (!metadata || !metadata.features_by_level) {
            container.innerHTML = '';
            return;
        }

        // Display generic feature list
        let html = '<div class="class-specific-section active">';
        html += '<div class="class-section-header">📖 Class Features</div>';
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
        this.updateSubclassSelector(level);
        
        // Update class manager if exists
        const manager = this.classManagers[this.selectedClass];
        if (manager && typeof manager.setLevel === 'function') {
            manager.setLevel(level);
        } else {
            // Update generic features
            this.showGenericFeatures(level);
        }
    }

    updateStats() {
        const stats = this.getCurrentStats();
        const manager = this.classManagers[this.selectedClass];
        
        if (manager && typeof manager.updateStats === 'function') {
            manager.updateStats(stats);
        }
    }

    updateSubclass(subclass) {
        const manager = this.classManagers[this.selectedClass];
        
        if (manager && typeof manager.setSubclass === 'function') {
            manager.setSubclass(subclass);
        }
    }

    getSelectedClassMetadata() {
        return this.classMetadata[this.selectedClass];
    }

    getSubclassLevel() {
        const metadata = this.classMetadata[this.selectedClass];
        return metadata?.subclasses?.level || 3;
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

    // Subclass selection
    const subclassSelect = document.getElementById('subclass-select');
    if (subclassSelect) {
        subclassSelect.addEventListener('change', (e) => {
            window.classSelector.updateSubclass(e.target.value);
        });
    }
});