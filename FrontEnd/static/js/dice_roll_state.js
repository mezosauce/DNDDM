// Phase 3 Dice State - Dice Rolling with Animation
const campaignName = window.location.pathname.split('/')[2];

// Calculate stat modifier on page load
document.addEventListener('DOMContentLoaded', function() {
    updateStatModifier();
});

function updateStatModifier() {
    // Get the relevant stat from the page
    const statElements = document.querySelectorAll('.challenge-item');
    let relevantStat = 'strength';
    
    statElements.forEach(el => {
        const label = el.querySelector('.label');
        if (label && label.textContent.includes('Relevant Stat')) {
            const value = el.querySelector('.value').textContent.toLowerCase().trim();
            relevantStat = value;
        }
    });
    
    // Get stat value from the stats grid
    const statBoxes = document.querySelectorAll('.stat-box');
    let modifier = 0;
    
    statBoxes.forEach(box => {
        const label = box.querySelector('.stat-label').textContent.toLowerCase();
        if (label === relevantStat.substring(0, 3)) {
            const modText = box.querySelector('.stat-modifier').textContent;
            modifier = parseInt(modText.replace('+', '').replace('−', '-'));
        }
    });
    
    // Update the stat modifier display
    const statModEl = document.getElementById('stat-mod');
    if (statModEl) {
        statModEl.textContent = modifier >= 0 ? `+${modifier}` : `${modifier}`;
    }
}

async function rollDice() {
    const button = document.getElementById('roll-btn');
    const dice = document.getElementById('dice');
    const resultDisplay = document.getElementById('result-display');
    const narrativeResult = document.getElementById('narrative-result');
    
    // Disable button
    button.disabled = true;
    button.classList.add('rolling');
    
    // Hide previous results
    resultDisplay.classList.remove('result-visible');
    resultDisplay.classList.add('result-hidden');
    narrativeResult.classList.add('hidden');
    narrativeResult.className = 'narrative-result hidden';
    
    // Start dice animation
    dice.classList.add('rolling');
    
    try {
        // Wait for animation to play for a bit
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Make API call
        const response = await fetch(`/campaign/${campaignName}/dice-state/roll`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Roll failed');
        }
        
        // Continue animation until it completes (1.5s total)
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Stop animation and show result
        dice.classList.remove('rolling');
        
        if (data.success) {
            displayResult(data);
            
            // Auto-redirect after 4 seconds
            setTimeout(() => {
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            }, 4000);
        } else {
            throw new Error(data.error || 'Unknown error');
        }
        
    } catch (error) {
        console.error('Error rolling dice:', error);
        
        // Stop animation
        dice.classList.remove('rolling');
        button.classList.remove('rolling');
        
        // Show error
        narrativeResult.textContent = `Error: ${error.message}`;
        narrativeResult.classList.remove('hidden');
        narrativeResult.classList.add('failure');
        
        // Re-enable button
        button.disabled = false;
    }
}

function displayResult(data) {
    const { result, narrative, breakdown } = data;
    const rollNumber = document.getElementById('roll-number');
    const totalScore = document.getElementById('total-score');
    const resultDisplay = document.getElementById('result-display');
    const narrativeResult = document.getElementById('narrative-result');
    const button = document.getElementById('roll-btn');
    
    // Update roll number and total
    rollNumber.textContent = result.raw_roll;
    totalScore.textContent = `Total: ${result.total} (DC ${result.target})`;
    
    // Show result display with animation
    resultDisplay.classList.remove('result-hidden');
    resultDisplay.classList.add('result-visible');
    
    // Determine outcome class
    let outcomeClass = 'success';
    if (result.outcome === 'critical_success') {
        outcomeClass = 'critical-success';
        rollNumber.style.color = '#38ef7d';
    } else if (result.outcome === 'critical_failure') {
        outcomeClass = 'critical-failure';
        rollNumber.style.color = '#e53935';
    } else if (result.outcome === 'failure') {
        outcomeClass = 'failure';
        rollNumber.style.color = '#ff6b6b';
    } else {
        rollNumber.style.color = '#51cf66';
    }
    
    // Build narrative text with breakdown
    let narrativeText = `<p style="font-size: 1.1em; margin-bottom: 15px;"><strong>${getOutcomeEmoji(result.outcome)} ${getOutcomeText(result.outcome)}</strong></p>`;
    narrativeText += `<p style="margin-bottom: 15px;">${narrative}</p>`;
    
    if (breakdown) {
        narrativeText += `<div style="font-size: 0.9em; opacity: 0.8; margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);">`;
        narrativeText += breakdown.replace(/\n/g, '<br>');
        narrativeText += `</div>`;
    }
    
    // Show narrative result
    narrativeResult.innerHTML = narrativeText;
    narrativeResult.classList.remove('hidden');
    narrativeResult.classList.add(outcomeClass);
    
    // Update button
    button.classList.remove('rolling');
    button.querySelector('.btn-text').textContent = 'Continuing...';
    button.querySelector('.btn-icon').textContent = '⏭️';
}

function getOutcomeEmoji(outcome) {
    const emojis = {
        'critical_success': '🌟',
        'success': '✅',
        'failure': '❌',
        'critical_failure': '💥'
    };
    return emojis[outcome] || '🎲';
}

function getOutcomeText(outcome) {
    const texts = {
        'critical_success': 'Critical Success!',
        'success': 'Success!',
        'failure': 'Failure',
        'critical_failure': 'Critical Failure!'
    };
    return texts[outcome] || 'Result';
}

// Rotate dice to show different faces (optional visual enhancement)
function rotateDiceToFace(faceNumber) {
    const dice = document.getElementById('dice');
    const rotations = {
        1: 'rotateX(0deg) rotateY(0deg)',
        2: 'rotateX(0deg) rotateY(180deg)',
        3: 'rotateX(0deg) rotateY(90deg)',
        4: 'rotateX(0deg) rotateY(-90deg)',
        5: 'rotateX(90deg) rotateY(0deg)',
        6: 'rotateX(-90deg) rotateY(0deg)'
    };
    
    if (rotations[faceNumber]) {
        dice.style.transform = rotations[faceNumber];
    }
}