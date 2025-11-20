/**
 * Base Class Features Utilities
 * Shared functionality for all class-specific feature displays
 */

class ClassFeatureManager {
    constructor(className) {
        this.className = className;
        this.level = 1;
        this.features = {};
    }

    setLevel(level) {
        this.level = parseInt(level) || 1;
        this.updateFeatureDisplay();
    }

    updateFeatureDisplay() {
        // Override in subclasses
    }

    isFeatureUnlocked(requiredLevel) {
        return this.level >= requiredLevel;
    }

    createFeatureNode(featureName, level, unlocked, description) {
        const node = document.createElement('div');
        node.className = `feature-node ${unlocked ? 'unlocked' : 'locked'}`;
        node.innerHTML = `
            <div class="feature-level">Lv ${level}</div>
            <div class="feature-name">${featureName}</div>
            ${description ? `<div class="feature-desc">${description}</div>` : ''}
        `;
        return node;
    }

    createResourceTracker(resourceName, current, max, color = '#ff6b6b') {
        const tracker = document.createElement('div');
        tracker.className = 'resource-tracker';
        tracker.innerHTML = `
            <div class="resource-name">${resourceName}</div>
            <div class="resource-bar">
                <div class="resource-fill" style="width: ${(current/max)*100}%; background: ${color};">
                    ${current}/${max}
                </div>
            </div>
            <div class="resource-buttons">
                <button onclick="this.parentElement.parentElement.querySelector('.resource-fill').dataset.current = Math.max(0, parseInt(this.parentElement.parentElement.querySelector('.resource-fill').dataset.current || ${current}) - 1); updateResourceDisplay(this.parentElement.parentElement)">-</button>
                <button onclick="this.parentElement.parentElement.querySelector('.resource-fill').dataset.current = Math.min(${max}, parseInt(this.parentElement.parentElement.querySelector('.resource-fill').dataset.current || ${current}) + 1); updateResourceDisplay(this.parentElement.parentElement)">+</button>
            </div>
        `;
        return tracker;
    }

    showSubclassSelector(level) {
        const metadata = window.classSelector?.getSelectedClassMetadata();
        if (!metadata || !metadata.subclasses) return;

        const subclassLevel = metadata.subclasses.level;
        if (level < subclassLevel) return;

        const container = document.getElementById('subclass-selector-container');
        if (!container) return;

        container.style.display = 'block';
        const select = document.getElementById('subclass-select');
        if (!select) return;

        // Populate options
        select.innerHTML = `<option value="">Choose ${metadata.subclasses.name}...</option>`;
        metadata.subclasses.options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option.name;
            opt.textContent = option.name;
            opt.title = option.description;
            select.appendChild(opt);
        });
    }
}

// Utility function to update resource displays
function updateResourceDisplay(trackerElement) {
    const fill = trackerElement.querySelector('.resource-fill');
    const current = parseInt(fill.dataset.current || fill.textContent.split('/')[0]);
    const max = parseInt(fill.textContent.split('/')[1]);
    
    fill.style.width = `${(current/max)*100}%`;
    fill.textContent = `${current}/${max}`;
}

// Format modifier for display
function formatModifier(value) {
    return value >= 0 ? `+${value}` : `${value}`;
}

// Calculate ability modifier
function calculateModifier(score) {
    return Math.floor((score - 10) / 2);
}

// Calculate proficiency bonus by level
function getProficiencyBonus(level) {
    if (level < 5) return 2;
    if (level < 9) return 3;
    if (level < 13) return 4;
    if (level < 17) return 5;
    return 6;
}

// Export for use in other modules
window.ClassFeatureManager = ClassFeatureManager;
window.formatModifier = formatModifier;
window.calculateModifier = calculateModifier;
window.getProficiencyBonus = getProficiencyBonus;