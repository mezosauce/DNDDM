/**
 * Class Selector System
 * Handles dynamic class selection and UI updates
 */

class ClassSelector {
    constructor() {
        this.selectedClass = null;
        this.classMetadata = null;
        this.loadClassMetadata();
    }

    async loadClassMetadata() {
        try {
            const response = await fetch('/static/data/class_metadata.json');
            this.classMetadata = await response.json();
        } catch (error) {
            console.error('Failed to load class metadata:', error);
            this.classMetadata = {};
        }
    }

    selectClass(className) {
        this.selectedClass = className;
        this.updateUI(className);
    }

    updateUI(className) {
        // Hide all class-specific sections
        document.querySelectorAll('.class-specific-section').forEach(section => {
            section.style.display = 'none';
        });

        // Show selected class section if it exists
        const classSection = document.getElementById(`class-section-${className}`);
        if (classSection) {
            classSection.style.display = 'block';
        }

        // Update class info display
        this.updateClassInfo(className);
        
        // Update skill options based on class
        this.updateSkillOptions(className);
    }

    updateClassInfo(className) {
        const metadata = this.classMetadata[className];
        if (!metadata) return;

        // Update hit die display
        const hitDieEl = document.getElementById('class-hit-die');
        if (hitDieEl) {
            hitDieEl.textContent = metadata.hit_die || 'd8';
        }

        // Update primary abilities
        const primaryAbilitiesEl = document.getElementById('class-primary-abilities');
        if (primaryAbilitiesEl) {
            primaryAbilitiesEl.textContent = metadata.primary_abilities?.join(', ') || 'Various';
        }

        // Update saving throws
        const savesEl = document.getElementById('class-saves');
        if (savesEl) {
            savesEl.textContent = metadata.saves?.join(', ') || 'None';
        }

        // Update proficiencies info
        const armorProfEl = document.getElementById('class-armor-prof');
        if (armorProfEl) {
            armorProfEl.textContent = metadata.armor_proficiencies?.join(', ') || 'None';
        }

        const weaponProfEl = document.getElementById('class-weapon-prof');
        if (weaponProfEl) {
            weaponProfEl.textContent = metadata.weapon_proficiencies?.join(', ') || 'None';
        }
    }

    updateSkillOptions(className) {
        const metadata = this.classMetadata[className];
        if (!metadata || !metadata.skills) return;

        const skillWarning = document.getElementById('skill-class-info');
        if (skillWarning) {
            const numSkills = metadata.skills.choose || 2;
            const availableSkills = metadata.skills.from || [];
            
            skillWarning.innerHTML = `
                <div style="background: rgba(77, 171, 247, 0.1); border: 2px solid #4dabf7; border-radius: 6px; padding: 10px; margin: 10px 0;">
                    <strong style="color: #4dabf7;">Class Skills:</strong> Choose ${numSkills} from: ${availableSkills.join(', ')}
                </div>
            `;
        }
    }

    getSelectedClassMetadata() {
        return this.classMetadata[this.selectedClass];
    }

    isSkillAvailableForClass(skillName) {
        const metadata = this.getSelectedClassMetadata();
        if (!metadata || !metadata.skills) return true;
        
        return metadata.skills.from?.includes(skillName) ?? true;
    }

    getSubclassLevel() {
        const metadata = this.getSelectedClassMetadata();
        return metadata?.subclasses?.level || 3;
    }

    getSubclassOptions() {
        const metadata = this.getSelectedClassMetadata();
        return metadata?.subclasses?.options || [];
    }
}

// Global instance
window.classSelector = new ClassSelector();

// Hook into existing class selection
function onClassChange() {
    const classSelect = document.getElementById('char-class');
    if (classSelect) {
        const selectedClass = classSelect.value;
        window.classSelector.selectClass(selectedClass);
        
        // Call existing function if it exists
        if (typeof updateClassSkills === 'function') {
            updateClassSkills();
        }
    }
}