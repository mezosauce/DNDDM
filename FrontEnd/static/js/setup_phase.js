
        // Reference Data
        const ALL_SKILLS = [
            'Acrobatics', 'Animal Handling', 'Arcana', 'Athletics',
            'Deception', 'History', 'Insight', 'Intimidation',
            'Investigation', 'Medicine', 'Nature', 'Perception',
            'Performance', 'Persuasion', 'Religion', 'Sleight of Hand',
            'Stealth', 'Survival'
        ];
        
        const ALL_LANGUAGES = [
            'Common', 'Dwarvish', 'Elvish', 'Giant', 'Gnomish',
            'Goblin', 'Halfling', 'Orc', 'Abyssal', 'Celestial',
            'Draconic', 'Deep Speech', 'Infernal', 'Primordial',
            'Sylvan', 'Undercommon'
        ];
        
        const RACIAL_LANGUAGES = {
            'Human': ['Common'],
            'Elf': ['Common', 'Elvish'],
            'Dwarf': ['Common', 'Dwarvish'],
            'Halfling': ['Common', 'Halfling'],
            'Dragonborn': ['Common', 'Draconic'],
            'Gnome': ['Common', 'Gnomish'],
            'Half-Elf': ['Common', 'Elvish'],
            'Half-Orc': ['Common', 'Orc'],
            'Tiefling': ['Common', 'Infernal']
        };
        
        const PERSONALITY_TRAITS = [
            "I idolize a particular hero of my faith, and constantly refer to that person's deeds and example.",
            "I can find common ground between the fiercest enemies, empathizing with them and always working toward peace.",
            "I see omens in every event and action. The gods try to speak to us, we just need to listen",
            "Nothing can shake my optimistic attitude.",
            "I quote (or misquote) sacred texts and proverbs in almost every situation.",
            "I am tolerant (or intolerant) of other faiths and respect (or condemn) the worship of other gods.",
            "I've enjoyed fine food, drink, and high society among my temple's elite. Rough living grates on me.",
            "I've spent so long in the temple that I have little practical experience dealing with people in the outside world."
    ];

        const IDEALS = [
            "Tradition. The ancient traditions of worship and sacrifice must be preserved and upheld. (Lawful)",
            "Charity. I always try to help those in need, no matter what the personal cost. (Good)",
            "Change. We must help bring about the changes the gods are constantly working in the world. (Chaotic)",
            "Power. I hope to one day rise to the top of my faith's religious hierarchy. (Lawful)",
            "Faith. I trust that my deity will guide my actions. I have faith that if I work hard, things will go well. (Lawful)",
            "Aspiration. I seek to prove myself worthy of my god's favor by matching my actions against his or her teachings. (Any)"
    ];

        const BONDS = [
            "I would die to recover an ancient relic of my faith that was lost long ago.",
            "I will someday get revenge on the corrupt temple hierarchy who branded me a heretic.",
            "I owe my life to the priest who took me in when my parents died.",
            "Everything I do is for the common people.",
            "I will do anything to protect the temple where I served.",
            "I seek to preserve a sacred text that my enemies consider heretical and seek to destroy."
    ];

        const FLAWS = [
            "I judge others harshly, and myself even more severely.",
            "I put too much trust in those who wield power within my temple's hierarchy.",
            "My piety sometimes leads me to blindly trust those that profess faith in my god.",
            "I am inflexible in my thinking.",
            "I am suspicious of strangers and expect the worst of them.",
            "Once I pick a goal, I become obsessed with it to the detriment of everything else in my life."
        ];
        
        const MAX_POINTS = 60;
        let selectedSkills = [];
        let selectedLanguages = [];
        let selectedTraits = [];
        let racialLanguages = [];
        let selectedIdeal = null;
        let selectedBond = null;
        let selectedFlaw = null;
        
        let traitsRolled = false;
        let idealRolled = false;
        let bondRolled = false;
        let flawRolled = false;

        // Call this BEFORE anything else:
        document.addEventListener('DOMContentLoaded', function() {
            createPersonalityTraitsList();
            
        });

        function createPersonalityTraitsList() {
            const container = document.getElementById('personality-traits-list');
            
            if (!container) {
                console.error('Container #personality-traits-list not found!');
                return;
            }
            
            container.innerHTML = ''; // Clear existing
            
            PERSONALITY_TRAITS.forEach((trait, index) => {
                const div = document.createElement('div');
                div.className = 'dice-option';
                div.textContent = `${index + 1}. ${trait}`;
                
                container.appendChild(div);
            });
        }

    

            
            function selectPersonalityTrait(index) {
                const trait = PERSONALITY_TRAITS[index];
                const options = document.querySelectorAll('#personality-traits-list .dice-option');
                
                 
                if (!options[index]) {
                    console.error('Option not found at index:', index);
                    return
                }

                // Allow up to 2 traits
                if (selectedTraits.length < 2) {
                    selectedTraits.push(trait);
                    options[index].classList.add('selected');
                }
                
                updateTraitsDisplay();
            }

            function selectIdeal(index) {
                const ideal = IDEALS[index];
                selectedIdeal = ideal;
                
                // Remove previous selection
                document.querySelectorAll('#ideals-list .dice-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                
                // Add new selection
                const options = document.querySelectorAll('#ideals-list .dice-option');
                if (options[index]) {
                    options[index].classList.add('selected');
                }
                updateIdealDisplay();
            }

            function selectBond(index) {
                const bond = BONDS[index];
                selectedBond = bond;
                
                // Remove previous selection
                document.querySelectorAll('#bonds-list .dice-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                
                // Add new selection
                const options = document.querySelectorAll('#bonds-list .dice-option');
                if (options[index]) {
                    options[index].classList.add('selected');
                }
                updateBondDisplay();
            }

            function selectFlaw(index) {
                const flaw = FLAWS[index];
                selectedFlaw = flaw;
                
                // Remove previous selection
                document.querySelectorAll('#flaws-list .dice-option').forEach(opt => {
                    opt.classList.remove('selected');
                });
                
                // Add new selection
                const options = document.querySelectorAll('#flaws-list .dice-option');
                if (options[index]) {
                    options[index].classList.add('selected');
                }
                updateFlawDisplay();
            }

            function rollD8() {

                const roll1 = Math.floor(Math.random() * 8);
                
                selectPersonalityTrait(roll1);
                
                // Get all options
                const allOptions = optionsList.querySelectorAll('.dice-option');
                allOptions.forEach(opt => opt.classList.remove('highlighted'));
                
                // Highlight the rolled option
                if (allOptions[result]) {
                    allOptions[result].classList.add('highlighted');
                    
                    // Scroll into view
                    allOptions[result].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
                
                // Select the trait
                selectPersonalityTrait(result);
            }

            

        function rollD6Ideal() {
            
            
            const roll = Math.floor(Math.random() * 6);
            selectIdeal(roll);
            
            const option = document.querySelectorAll('#ideals-list .dice-option')[roll];
            option.classList.add('roll-animation');
            setTimeout(() => option.classList.remove('roll-animation'), 600);
            
            // Disable the roll button
            idealRolled = true;
            const btn = document.getElementById('roll-ideal-btn');
            btn.disabled = true;
            btn.textContent = '🎲 Already Rolled (click options to change)';
            btn.classList.add('rolled');
            
    }

        function rollD6Bond() {
            if (bondRolled) {
                alert('You have already rolled for your bond. Click on the options to manually change your selection.');
                return;
            }
            
            const roll = Math.floor(Math.random() * 6);
            selectBond(roll);
            
            const option = document.querySelectorAll('#bonds-list .dice-option')[roll];
            option.classList.add('roll-animation');
            setTimeout(() => option.classList.remove('roll-animation'), 600);
            
            // Disable the roll button
            bondRolled = true;
            const btn = document.getElementById('roll-bond-btn');
            btn.disabled = true;
            btn.textContent = '🎲 Already Rolled (click options to change)';
            btn.classList.add('rolled');
            
    }

        function rollD6Flaw() {
            if (flawRolled) {
                alert('You have already rolled for your flaw. Click on the options to manually change your selection.');
                return;
            }
            
            const roll = Math.floor(Math.random() * 6);
            selectFlaw(roll);
            
            const option = document.querySelectorAll('#flaws-list .dice-option')[roll];
            option.classList.add('roll-animation');
            setTimeout(() => option.classList.remove('roll-animation'), 600);
            
            // Disable the roll button
            flawRolled = true;
            const btn = document.getElementById('roll-flaw-btn');
            
            btn.disabled = true;
            btn.textContent = '🎲 Already Rolled (click options to change)';
            btn.classList.add('rolled');
        
    }


        // ============================================================================
        // DISPLAY UPDATE FUNCTIONS
        // ============================================================================

        function updateTraitsDisplay() {
            const display = document.getElementById('selected-traits-display');
            if (selectedTraits.length === 0) {
                display.innerHTML = '<em style="color: #888;">No traits selected yet</em>';
            } else {
                display.innerHTML = selectedTraits.map((trait, i) => 
                    `<div class="selection-item"><strong>Trait ${i + 1}:</strong> ${trait}</div>`
                ).join('');
            }
        }

        function updateIdealDisplay() {
            const display = document.getElementById('selected-ideal-display');
            if (!selectedIdeal) {
                display.innerHTML = '<em style="color: #888;">No ideal selected yet</em>';
            } else {
                display.innerHTML = `<div class="selection-item">${selectedIdeal}</div>`;
            }
        }

        function updateBondDisplay() {
            const display = document.getElementById('selected-bond-display');
            if (!selectedBond) {
                display.innerHTML = '<em style="color: #888;">No bond selected yet</em>';
            } else {
                display.innerHTML = `<div class="selection-item">${selectedBond}</div>`;
            }
        }

        function updateFlawDisplay() {
            const display = document.getElementById('selected-flaw-display');
            if (!selectedFlaw) {
                display.innerHTML = '<em style="color: #888;">No flaw selected yet</em>';
            } else {
                display.innerHTML = `<div class="selection-item">${selectedFlaw}</div>`;
            }
        }

        // ============================================================================
        // POPULATE LISTS
        // ============================================================================

        function populatePersonalityTraits() {
    const container = document.getElementById('personality-traits-list');
    container.innerHTML = PERSONALITY_TRAITS.map((trait, index) => `
        <div class="dice-option">
            <span class="dice-number">${index + 1}</span>
            <span class="dice-text">${trait}</span>
        </div>
    `).join('');
}

        function populateIdealsList() {
            const container = document.getElementById('ideals-list');
            container.innerHTML = IDEALS.map((ideal, index) => `
                <div class="dice-option">
                    <span class="dice-number">${index + 1}</span>
                    <span class="dice-text">${ideal}</span>
                </div>
            `).join('');
}

       function populateBondsList() {
        const container = document.getElementById('bonds-list');
        container.innerHTML = BONDS.map((bond, index) => `
            <div class="dice-option" >
                <span class="dice-number">${index + 1}</span>
                <span class="dice-text">${bond}</span>
            </div>
        `).join('');
    }

        function populateFlawsList() {
            const container = document.getElementById('flaws-list');
            container.innerHTML = FLAWS.map((flaw, index) => `
                <div class="dice-option" onclick="handleFlawClick(${index})">
                    <span class="dice-number">${index + 1}</span>
                    <span class="dice-text">${flaw}</span>
                </div>
            `).join('');
        }



        // Tab Management
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(el => {
                el.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(el => {
                el.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById('tab-' + tabName).classList.add('active');
            event.target.classList.add('active');
        }
        

        function onClassChange() {
            const classSelect = document.getElementById('char-class');
            const selectedClass = classSelect.value;
            
            // Update class selector
            if (window.classSelector) {
                window.classSelector.selectClass(selectedClass);
            }
            
            // Show/hide class info panel
            const infoPanel = document.getElementById('class-info-panel');
            if (infoPanel) {
                infoPanel.style.display = selectedClass ? 'block' : 'none';
            }
            
            // Update displayed stats based on class
            updateClassStats();
            
            // Check if subclass selector should be shown
            const level = parseInt(document.getElementById('char-level').value) || 1;
            
            // Call existing function if it exists
            if (typeof updateClassSkills === 'function') {
                updateClassSkills();
            }
        }
     
        // Update displayed stats based on selected class
        function updateClassStats() {
            const classSelect = document.getElementById('char-class');
            const selectedClass = classSelect.value;
            
            // Default stats for each class (from the Python classes)
            const classStats = {
                'Barbarian': { strength: 15, dexterity: 13, constitution: 14, intelligence: 10, wisdom: 12, charisma: 8,  hp: 100, max_hp: 100, ac: 50 },
                'Bard': { strength: 8, dexterity: 14, constitution: 12, intelligence: 10, wisdom: 13, charisma: 15,  hp: 80, max_hp: 80, ac: 12 },
                'Cleric': { strength: 10, dexterity: 12, constitution: 14, intelligence: 11, wisdom: 16, charisma: 13, hp: 100, max_hp: 100, ac: 10},
                'Druid': { strength: 10, dexterity: 13, constitution: 14, intelligence: 12, wisdom: 15, charisma: 8, hp: 90, max_hp: 90, ac: 11 }
            };
            
            if (selectedClass && classStats[selectedClass]) {
                const stats = classStats[selectedClass];
                document.getElementById('str').value = stats.strength;
                document.getElementById('dex').value = stats.dexterity;
                document.getElementById('con').value = stats.constitution;
                document.getElementById('int').value = stats.intelligence;
                document.getElementById('wis').value = stats.wisdom;
                document.getElementById('cha').value = stats.charisma;

                document.getElementById('char-hp').value = stats.hp;
                document.getElementById('char-max-hp').value = stats.max_hp;
                document.getElementById('char-ac').value = stats.ac;
            } else {
                // Reset to default
                ['str', 'dex', 'con', 'int', 'wis', 'cha'].forEach(stat => {
                    document.getElementById(stat).value = 10;
                });
                document.getElementById('char-hp').value = 10;
                document.getElementById('char-max-hp').value = 10;
                document.getElementById('char-ac').value = 10;
            }
        }
        // ============================================================================
        // INITIALIZATION
        // ============================================================================

        // Initialize on load
        window.onload = () => {
            
            // Initialize displays
            updateTraitsDisplay();
            updateIdealDisplay();
            updateBondDisplay();
            updateFlawDisplay();
            
            // Populate all the lists
            populateSkillsList();
            populateLanguagesList();
            populateIdealsList();
            populateBondsList();
            populateFlawsList();
        };
        
       
        
        // Skills List
        function populateSkillsList() {
            const container = document.getElementById('skills-list');
            container.innerHTML = ALL_SKILLS.map(skill => `
                <label class="multi-select-item">
                    <input type="checkbox" value="${skill}" onchange="toggleSkill('${skill}')">
                    ${skill}
                </label>
            `).join('');
        }
        
        function toggleSkill(skill) {
            if (selectedSkills.includes(skill)) {
                selectedSkills = selectedSkills.filter(s => s !== skill);
            } else {
                selectedSkills.push(skill);
            }
            
            // Update visual selection
            updateSkillsVisual();
            
            // Check for conflicts
            checkSkillConflicts();
        }
        
        function updateSkillsVisual() {
            document.querySelectorAll('#skills-list .multi-select-item').forEach(el => {
                const checkbox = el.querySelector('input');
                if (checkbox.checked) {
                    el.classList.add('selected');
                } else {
                    el.classList.remove('selected');
                }
            });
        }
        
        function checkSkillConflicts() {
            const warningBox = document.getElementById('skill-warning');
            const warningText = document.getElementById('skill-warning-text');
            
            if (selectedSkills.length > 2) {
                warningBox.style.display = 'block';
                warningText.textContent = `You have selected ${selectedSkills.length} skills. Backgrounds typically grant 2 skill proficiencies.`;
            } else {
                warningBox.style.display = 'none';
            }
        }
        
        function updateClassSkills() {
        }
        
        // Languages List
        function populateLanguagesList() {
            const container = document.getElementById('languages-list');
            container.innerHTML = ALL_LANGUAGES.map(lang => `
                <label class="multi-select-item">
                    <input type="checkbox" value="${lang}" onchange="toggleLanguage('${lang}')" id="lang-${lang}">
                    ${lang}
                </label>
            `).join('');
        }
        
        function toggleLanguage(language) {
            if (selectedLanguages.includes(language)) {
                selectedLanguages = selectedLanguages.filter(l => l !== language);
            } else {
                selectedLanguages.push(language);
            }
            
            updateLanguagesVisual();
        }
        
        function updateLanguagesVisual() {
            document.querySelectorAll('#languages-list .multi-select-item').forEach(el => {
                const checkbox = el.querySelector('input');
                if (checkbox.checked) {
                    el.classList.add('selected');
                } else {
                    el.classList.remove('selected');
                }
            });
        }
        
        function updateRacialLanguages() {
            const race = document.getElementById('char-race').value;
            racialLanguages = RACIAL_LANGUAGES[race] || ['Common'];
            
            document.getElementById('racial-lang-list').textContent = racialLanguages.join(', ');
            
            // Disable racial languages in the selection list
            ALL_LANGUAGES.forEach(lang => {
                const checkbox = document.getElementById('lang-' + lang);
                if (checkbox) {
                    if (racialLanguages.includes(lang)) {
                        checkbox.disabled = true;
                        checkbox.checked = false;
                        checkbox.parentElement.style.opacity = '0.5';
                    } else {
                        checkbox.disabled = false;
                        checkbox.parentElement.style.opacity = '1';
                    }
                }
            });
        }
        
        
        // Background Info
        function updateBackgroundInfo() {
            const background = document.getElementById('char-background').value;
            const featureField = document.getElementById('char-bg-feature');
            
            // Simple examples - would be enhanced with full background data
            const features = {
                'Acolyte': 'Shelter of the Faithful: You can receive free healing and care at temples of your faith.',
                'Criminal': 'Criminal Contact: You have a reliable contact in the criminal underworld.',
                'Folk Hero': 'Rustic Hospitality: Common folk will shelter and hide you from the law.',
                'Noble': 'Position of Privilege: You are welcome in high society.',
                'Sage': 'Researcher: You know how to obtain information from libraries and archives.',
                'Soldier': 'Military Rank: You have a rank from your military career.'
            };
            
            if (features[background]) {
                featureField.value = features[background];
            }
        }
        
        // Form Submission
        document.getElementById('character-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const str = parseInt(document.getElementById('str').value) || 10;
            const dex = parseInt(document.getElementById('dex').value) || 10;
            const con = parseInt(document.getElementById('con').value) || 10;
            const int = parseInt(document.getElementById('int').value) || 10;
            const wis = parseInt(document.getElementById('wis').value) || 10;
            const cha = parseInt(document.getElementById('cha').value) || 10;
            
            const allLanguages = [...racialLanguages, ...selectedLanguages];
            
            const data = {
                name: document.getElementById('char-name').value,
                race: document.getElementById('char-race').value,
                char_class: document.getElementById('char-class').value,
                background: document.getElementById('char-background').value,
                alignment: document.getElementById('char-alignment').value,
                level: parseInt(document.getElementById('char-level').value),
                hp: parseInt(document.getElementById('char-hp').value),
                max_hp: parseInt(document.getElementById('char-max-hp').value),
                ac: parseInt(document.getElementById('char-ac').value),
                stats: {
                    strength: str,
                    dexterity: dex,
                    constitution: con,
                    intelligence: int,
                    wisdom: wis,
                    charisma: cha
                },
                background_feature: document.getElementById('char-bg-feature').value,
                skill_proficiencies: selectedSkills,
                languages_known: allLanguages,
                personality_traits: selectedTraits,           
                ideal: selectedIdeal || '',                   
                bond: selectedBond || '',
                flaw: selectedFlaw || '',                     

            };
            
            const response = await fetch(`/campaign/${encodeURIComponent(window.campaignName)}/character/add`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                location.reload();
            } else {
                alert('Error: ' + result.error);
            }
        });
        
        async function advancePhase() {
            if (!confirm('Ready to move to the next phase?')) return;
            
            const response = await fetch(`/campaign/${encodeURIComponent(window.campaignName)}/advance`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                location.href = `/campaign/${encodeURIComponent(window.campaignName)}`;
            } else {
                alert('Error: ' + result.error);
            }
        }
    
        
