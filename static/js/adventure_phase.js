
        const steps = [
            { key: 'quest_hook', name: 'Quest Hook', description: 'Choose the adventure that will draw your party in' },
            { key: 'objective', name: 'Main Objective', description: 'What does success look like?' },
            { key: 'location', name: 'Starting Location', description: 'Where does the adventure begin?' },
            { key: 'npcs', name: 'Key NPCs', description: 'Who will the party interact with?' },
            { key: 'equipment', name: 'Equipment', description: 'What should the party bring?' },
            { key: 'roles', name: 'Party Roles', description: 'How will the party work together?' }
        ];
        
        let currentStep = 0;
        let selections = {};
        let currentOptions = [];
        let selectedOptionIndex = null;
        
        function init() {
            updateProgress();
            showStep();
        }
        
        function updateProgress() {
            const items = document.querySelectorAll('#progress-checklist li');
            items.forEach((item, index) => {
                item.classList.remove('completed', 'active');
                if (index < currentStep) {
                    item.classList.add('completed');
                } else if (index === currentStep) {
                    item.classList.add('active');
                }
            });
        }
        
        function showStep() {
            const step = steps[currentStep];
            const stepDisplay = document.getElementById('step-display');
            const optionsContainer = document.getElementById('options-container');
            const buttonContainer = document.getElementById('button-container');
            
            stepDisplay.innerHTML = `
                <div class="step-container">
                    <div class="step-title">
                        <div class="step-number">${currentStep + 1}</div>
                        <span>${step.name}</span>
                    </div>
                    <p style="color: #b0b0b0; margin-bottom: 20px;">${step.description}</p>
                </div>
            `;
            
            optionsContainer.innerHTML = '';
            buttonContainer.innerHTML = `
                <button class="generate-btn" onclick="generateOptions()">
                    ✨ Generate ${step.name} Options
                </button>
            `;
            
            updateSelectionsDisplay();
        }
        
        async function generateOptions() {
            const step = steps[currentStep];
            const optionsContainer = document.getElementById('options-container');
            const buttonContainer = document.getElementById('button-container');
            
            optionsContainer.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating options...</p></div>';
            buttonContainer.innerHTML = '';
            
            try {
                const response = await fetch(`/campaign/${encodeURIComponent(window.campaignName)}/generate-options`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        step: step.key,
                        selections: selections
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    optionsContainer.innerHTML = `<p style="color: #ff6b6b;">Error: ${data.error}</p>`;
                    return;
                }
                
                currentOptions = data.options;
                displayOptions();
                
            } catch (error) {
                optionsContainer.innerHTML = `<p style="color: #ff6b6b;">Error: ${error.message}</p>`;
            }
        }
        
        function displayOptions() {
            const optionsContainer = document.getElementById('options-container');
            const buttonContainer = document.getElementById('button-container');
            
            optionsContainer.innerHTML = `
                <div class="options-container">
                    ${currentOptions.map((option, index) => `
                        <div class="option-card" onclick="selectOption(${index})">
                            <div class="option-title">${option.title}</div>
                            <div class="option-content">${option.content}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            
            buttonContainer.innerHTML = `
                <button onclick="regenerateOptions()" style="background: #666;">
                    🔄 Regenerate Options
                </button>
                <button class="next-btn" onclick="confirmSelection()" disabled id="next-btn">
                    → Continue to Next Step
                </button>
            `;
        }
        
        function selectOption(index) {
            selectedOptionIndex = index;
            
            // Update visual selection
            document.querySelectorAll('.option-card').forEach((card, i) => {
                card.classList.toggle('selected', i === index);
            });
            
            // Enable next button
            document.getElementById('next-btn').disabled = false;
        }
        
        function regenerateOptions() {
            generateOptions();
        }
        
        function confirmSelection() {
            if (selectedOptionIndex === null) return;
            
            const step = steps[currentStep];
            const selected = currentOptions[selectedOptionIndex];
            
            selections[step.key] = selected.title;
            
            currentStep++;
            selectedOptionIndex = null;
            
            if (currentStep < steps.length) {
                updateProgress();
                showStep();
            } else {
                showCompletion();
            }
        }
        
        function updateSelectionsDisplay() {
            const display = document.getElementById('selections-display');
            
            if (Object.keys(selections).length === 0) {
                display.innerHTML = '<p style="text-align: center; color: #888;">No selections yet</p>';
                return;
            }
            
            display.innerHTML = Object.entries(selections).map(([key, value]) => {
                const step = steps.find(s => s.key === key);
                return `
                    <div class="selection-item">
                        <div class="selection-label">${step ? step.name : key}</div>
                        <div class="selection-value">${value}</div>
                    </div>
                `;
            }).join('');
        }
        
        function showCompletion() {
            const stepDisplay = document.getElementById('step-display');
            const optionsContainer = document.getElementById('options-container');
            const buttonContainer = document.getElementById('button-container');
            
            stepDisplay.innerHTML = `
                <div class="step-container">
                    <div class="step-title">
                        <div class="step-number">✓</div>
                        <span>Quest Setup Complete!</span>
                    </div>
                    <p style="color: #51cf66; margin-bottom: 20px;">
                        All preparation steps are complete. You're ready to begin your adventure!
                    </p>
                </div>
            `;
            
            optionsContainer.innerHTML = `
                <div style="background: rgba(81, 207, 102, 0.1); padding: 20px; border-radius: 8px; border: 2px solid #51cf66;">
                    <h3 style="color: #51cf66; margin-bottom: 15px;">📋 Quest Summary</h3>
                    ${Object.entries(selections).map(([key, value]) => {
                        const step = steps.find(s => s.key === key);
                        return `<p style="margin: 10px 0;"><strong>${step ? step.name : key}:</strong> ${value}</p>`;
                    }).join('')}
                </div>
            `;
            
            buttonContainer.innerHTML = `
                <button class="advance-btn" onclick="beginAdventure()">
                    ⚔️ Begin Adventure (Start Session 1)
                </button>
            `;
            
            updateProgress();
        }
        
        async function beginAdventure() {
    if (!confirm('Ready to begin the adventure? This will start Session 1.')) return;
    
    try {
        // Save quest setup to markdown file
        await fetch(`/campaign/${encodeURIComponent(window.campaignName)}/save-quest-setup`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({selections: selections})
        });
        
        // Mark phase complete
        await fetch(`/campaign/${encodeURIComponent(window.campaignName)}/complete-phase`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({phase: 'call_to_adventure'})
        });
                
                // Advance to next phase
                const response = await fetch(`/campaign/${encodeURIComponent(window.campaignName)}/advance`, {
                    method: 'POST'
                });
                
                const result = await response.json();
        
            if (result.success) {
            alert('✓ Quest preparation saved to preparations.md!');
            location.href = `/campaign/${encodeURIComponent(window.campaignName)}`;
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
        
        // Initialize on page load
        window.onload = init;