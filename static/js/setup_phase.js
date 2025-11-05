
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
            "I idolize a particular hero and constantly refer to their deeds",
            "I can find common ground between the fiercest enemies",
            "I see omens in every event and action",
            "Nothing can shake my optimistic attitude",
            "I quote (or misquote) sacred texts and proverbs",
            "I am tolerant of other faiths and respect other gods",
            "I've enjoyed fine food and high society",
            "I have little practical experience dealing with people"
        ];
        
        const MAX_POINTS = 60;
        let selectedSkills = [];
        let selectedLanguages = [];
        let selectedTraits = [];
        let racialLanguages = [];
        
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
            updatePoints();
            populateSkillsList();
            populateLanguagesList();
            populatePersonalityTraits();
            updateCurrencyTotal();
            
            // Add currency change listeners
            ['pp', 'gp', 'ep', 'sp', 'cp'].forEach(coin => {
                document.getElementById('curr-' + coin).addEventListener('input', updateCurrencyTotal);
            });
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
        
        // Personality Traits
        function populatePersonalityTraits() {
            const container = document.getElementById('personality-traits-list');
            container.innerHTML = PERSONALITY_TRAITS.map((trait, index) => `
                <div class="trait-option" onclick="toggleTrait(${index})">
                    ${trait}
                </div>
            `).join('');
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
                ideal: document.getElementById('char-ideal').value,
                bond: document.getElementById('char-bond').value,
                flaw: document.getElementById('char-flaw').value,
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
