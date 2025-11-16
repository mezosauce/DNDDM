
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
        
        const MAX_POINTS = 0;
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

        // Dice Rolling
        function rollD8() {
    if (traitsRolled) {
        alert('You have already rolled for personality traits. Click on the options to manually change your selection.');
        return;
    }
    
    const roll = Math.floor(Math.random() * 8);
    selectPersonalityTrait(roll);
    
    // Add visual feedback
    const option = document.querySelectorAll('.dice-option')[roll];
    option.classList.add('roll-animation');
    setTimeout(() => option.classList.remove('roll-animation'), 600);
    
    // Disable the roll button
    traitsRolled = true;
    const btn = document.getElementById('roll-traits-btn');
    btn.disabled = true;
    btn.textContent = '🎲 Already Rolled (click options to change)';
    btn.classList.add('rolled');
}


            function selectPersonalityTrait(index) {
                const trait = PERSONALITY_TRAITS[index];
                const options = document.querySelectorAll('#personality-traits-list .dice-option');
                
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
                document.querySelectorAll('#ideals-list .dice-option')[index].classList.add('selected');
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
                document.querySelectorAll('#bonds-list .dice-option')[index].classList.add('selected');
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
                document.querySelectorAll('#flaws-list .dice-option')[index].classList.add('selected');
                updateFlawDisplay();
            }

        function rollD6Ideal() {
            if (idealRolled) {
                alert('You have already rolled for your ideal. Click on the options to manually change your selection.');
                return;
            }
            
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
                <div class="dice-option">
                    <span class="dice-number">${index + 1}</span>
                    <span class="dice-text">${bond}</span>
                </div>
            `).join('');
        }

        function populateFlawsList() {
            const container = document.getElementById('flaws-list');
            container.innerHTML = FLAWS.map((flaw, index) => `
                <div class="dice-option">
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
        
        // Initialize on load
        window.onload = () => {
            // Class selection handler
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
    
    // Check if subclass selector should be shown
    const level = parseInt(document.getElementById('char-level').value) || 1;
    updateSubclassDisplay(level);
    
    // Call existing function if it exists
    if (typeof updateClassSkills === 'function') {
        updateClassSkills();
    }
}

        // Level change handler - GLOBAL
        function onLevelChange() {
            const level = parseInt(document.getElementById('char-level').value) || 1;
            updateSubclassDisplay(level);
            updatePoints(); // Existing function
        }

        function updateSubclassDisplay(level) {
            const classSelect = document.getElementById('char-class');
            const selectedClass = classSelect.value;
            
            if (!selectedClass || !window.classSelector) return;
            
            const subclassLevel = window.classSelector.getSubclassLevel();
            const container = document.getElementById('subclass-selector-container');
            const levelReq = document.getElementById('subclass-level-req');
            
            if (container && levelReq) {
                levelReq.textContent = subclassLevel;
                container.style.display = level >= subclassLevel ? 'block' : 'none';
            }
        }

        // ============================================================================
        // TAB MANAGEMENT
        // ============================================================================

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

        // ============================================================================
        // INITIALIZATION
        // ============================================================================

        // Initialize on load
        window.onload = () => {
            updatePoints();
            populateSkillsList();
            populateLanguagesList();
            populatePersonalityTraits();
            populateIdealsList();
            populateBondsList();
            populateFlawsList();
            updateCurrencyTotal();
            
            // Initialize displays
            updateTraitsDisplay();
            updateIdealDisplay();
            updateBondDisplay();
            updateFlawDisplay();
            
            // Add currency change listeners
            ['pp', 'gp', 'ep', 'sp', 'cp'].forEach(coin => {
                document.getElementById('curr-' + coin).addEventListener('input', updateCurrencyTotal);
            });
            
            // Add level change listener
            document.getElementById('char-level')?.addEventListener('change', onLevelChange);
            document.getElementById('char-level')?.addEventListener('input', onLevelChange);
        };
        
        // Ability Score Points
        function updatePoints() {
            const str = parseInt(document.getElementById('str').value) || 0;
            const dex = parseInt(document.getElementById('dex').value) || 0;
            const con = parseInt(document.getElementById('con').value) || 0;
            const int = parseInt(document.getElementById('int').value) || 0;
            const wis = parseInt(document.getElementById('wis').value) || 0;
            const cha = parseInt(document.getElementById('cha').value) || 0;
            
            const total = str + dex + con + int + wis + cha;
            const remaining = MAX_POINTS - total;
            
            const pointsLeftSpan = document.getElementById('points-left');
            const pointsDiv = document.getElementById('points-remaining');
            
            pointsLeftSpan.textContent = remaining;
            
            if (remaining < 0) {
                pointsDiv.classList.add('over-budget');
            } else {
                pointsDiv.classList.remove('over-budget');
            }
        }
        
        // Currency Total
        function updateCurrencyTotal() {
            const pp = parseFloat(document.getElementById('curr-pp').value) || 0;
            const gp = parseFloat(document.getElementById('curr-gp').value) || 0;
            const ep = parseFloat(document.getElementById('curr-ep').value) || 0;
            const sp = parseFloat(document.getElementById('curr-sp').value) || 0;
            const cp = parseFloat(document.getElementById('curr-cp').value) || 0;
            
            const total = (pp * 10) + gp + (ep * 0.5) + (sp * 0.1) + (cp * 0.01);
            document.getElementById('total-gold').textContent = total.toFixed(2);
        }
        
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
            // This would check against class skills
            // For now, just warn if more than 2 selected
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
            // This would be enhanced to show which skills the class already grants
            // For now, just a placeholder
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
        
        
        function toggleTrait(index) {
            const trait = PERSONALITY_TRAITS[index];
            const element = document.querySelectorAll('.trait-option')[index];
            
            if (selectedTraits.includes(trait)) {
                selectedTraits = selectedTraits.filter(t => t !== trait);
                element.classList.remove('selected');
            } else {
                if (selectedTraits.length < 2) {
                    selectedTraits.push(trait);
                    element.classList.add('selected');
                } else {
                    alert('You can only select 2 personality traits. Deselect one first.');
                }
            }
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
            
            // Validate points
            const str = parseInt(document.getElementById('str').value);
            const dex = parseInt(document.getElementById('dex').value);
            const con = parseInt(document.getElementById('con').value);
            const int = parseInt(document.getElementById('int').value);
            const wis = parseInt(document.getElementById('wis').value);
            const cha = parseInt(document.getElementById('cha').value);
            
            const total = str + dex + con + int + wis + cha;
            
            if (total > MAX_POINTS) {
                alert(`Total ability points (${total}) exceeds maximum of ${MAX_POINTS}!`);
                return;
            }
            
            // Collect inventory
            const inventoryText = document.getElementById('char-inventory').value;
            const inventory = inventoryText ? inventoryText.split(',').map(i => i.trim()) : [];
            
            // Collect tool proficiencies
            const toolsText = document.getElementById('char-tools').value;
            const tools = toolsText ? toolsText.split(',').map(t => t.trim()) : [];
            
            // Combine racial and selected languages
            const allLanguages = [...racialLanguages, ...selectedLanguages];
            
            const data = {
                name: document.getElementById('char-name').value,
                race: document.getElementById('char-race').value,
                class: document.getElementById('char-class').value,
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
                tool_proficiencies: tools,
                languages_known: allLanguages,
                personality_traits: selectedTraits,           
                ideal: selectedIdeal || '',                   
                bond: selectedBond || '',                     
                flaw: selectedFlaw || '',                     
                currency: {
                    pp: parseInt(document.getElementById('curr-pp').value) || 0,
                    gp: parseInt(document.getElementById('curr-gp').value) || 0,
                    ep: parseInt(document.getElementById('curr-ep').value) || 0,
                    sp: parseInt(document.getElementById('curr-sp').value) || 0,
                    cp: parseInt(document.getElementById('curr-cp').value) || 0
                },
                inventory: inventory,
                notes: document.getElementById('char-notes').value
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
        };
        
