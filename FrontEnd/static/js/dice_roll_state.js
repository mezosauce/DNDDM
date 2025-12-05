// Phase 3 Dice State - Enhanced Dice Rolling with Backend Connection
const campaignName = decodeURIComponent(window.location.pathname.split('/')[2]);

// State management
let isRolling = false;
let rollResult = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dice Roll State initialized for campaign:', campaignName);
    updateStatModifier();
    highlightRelevantStat();
});

/**
 * Calculate and display the relevant stat modifier
 */
function updateStatModifier() {
    const statElements = document.querySelectorAll('.challenge-item');
    let relevantStat = 'strength';
    
    // Find the relevant stat from challenge info
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
    let statValue = 10;
    
    statBoxes.forEach(box => {
        const label = box.querySelector('.stat-label').textContent.toLowerCase();
        const statName = mapStatAbbreviation(label);
        
        if (statName === relevantStat.toLowerCase()) {
            const modText = box.querySelector('.stat-modifier').textContent;
            modifier = parseInt(modText.replace('+', '').replace('−', '-').replace(' ', ''));
            statValue = parseInt(box.querySelector('.stat-value').textContent);
            box.classList.add('active');
        }
    });
    
    // Update the stat modifier display
    const statModEl = document.getElementById('stat-mod');
    if (statModEl) {
        statModEl.textContent = modifier >= 0 ? `+${modifier}` : `${modifier}`;
    }
    
    console.log(`Relevant stat: ${relevantStat}, Value: ${statValue}, Modifier: ${modifier}`);
}

/**
 * Map stat abbreviation to full name
 */
function mapStatAbbreviation(abbr) {
    const mapping = {
        'str': 'strength',
        'dex': 'dexterity',
        'con': 'constitution',
        'int': 'intelligence',
        'wis': 'wisdom',
        'cha': 'charisma'
    };
    return mapping[abbr] || abbr;
}

/**
 * Highlight the stat box that's being used for this roll
 */
function highlightRelevantStat() {
    const statElements = document.querySelectorAll('.challenge-item');
    let relevantStat = 'strength';
    
    statElements.forEach(el => {
        const label = el.querySelector('.label');
        if (label && label.textContent.includes('Relevant Stat')) {
            const value = el.querySelector('.value').textContent.toLowerCase().trim();
            relevantStat = value;
        }
    });
    
    const statBoxes = document.querySelectorAll('.stat-box');
    statBoxes.forEach(box => {
        const stat = box.getAttribute('data-stat');
        if (stat && stat.toLowerCase() === relevantStat.toLowerCase()) {
            box.classList.add('active');
        }
    });
}

/**
 * Main dice rolling function - connects to backend
 */
async function rollDice() {
    if (isRolling) {
        console.log('Roll already in progress');
        return;
    }
    
    isRolling = true;
    const button = document.getElementById('roll-btn');
    const dice = document.getElementById('dice');
    const resultDisplay = document.getElementById('result-display');
    const narrativeResult = document.getElementById('narrative-result');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    try {
        // Disable button and show loading
        button.disabled = true;
        button.classList.add('rolling');
        
        // Hide previous results
        resultDisplay.classList.remove('result-visible');
        resultDisplay.classList.add('result-hidden');
        narrativeResult.classList.add('hidden');
        narrativeResult.className = 'narrative-result hidden';
        
        // Start dice animation
        dice.classList.add('rolling');
        
        console.log('Starting dice roll animation...');
        
        // Wait for animation to start (500ms)
        await sleep(500);
        
        // Show loading overlay
        loadingOverlay.classList.add('active');
        
        console.log(`Making API call to /campaign/${campaignName}/dice-state/roll`);
        
        // Make API call to backend
        const response = await fetch(`/campaign/${campaignName}/dice-state/roll`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API Error:', errorText);
            throw new Error(`Server error: ${response.status} - ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Roll result:', data);
        
        // Store result
        rollResult = data;
        
        // Hide loading overlay
        loadingOverlay.classList.remove('active');
        
        // Continue animation until completion (2s total)
        const remainingTime = 2000 - 500;
        await sleep(remainingTime);
        
        // Stop animation
        dice.classList.remove('rolling');
        
        if (data.success && data.result) {
            // Display the result
            await displayResult(data);
            
            // Show redirect message after 3 seconds
            setTimeout(() => {
                showRedirectMessage();
            }, 3000);
            
            // Auto-redirect after 5 seconds
            setTimeout(() => {
                if (data.redirect) {
                    console.log('Redirecting to:', data.redirect);
                    window.location.href = data.redirect;
                }
            }, 5000);
        } else {
            throw new Error(data.error || 'Invalid response from server');
        }
        
    } catch (error) {
        console.error('Error rolling dice:', error);
        
        // Hide loading overlay
        loadingOverlay.classList.remove('active');
        
        // Stop animation
        dice.classList.remove('rolling');
        button.classList.remove('rolling');
        
        // Show error in narrative result
        narrativeResult.innerHTML = `<p style="color: #ff6b6b; font-weight: 600;">⚠️ Error: ${error.message}</p>
            <p style="margin-top: 10px; font-size: 0.9em; opacity: 0.8;">Please try refreshing the page or contact support if the issue persists.</p>`;
        narrativeResult.classList.remove('hidden');
        narrativeResult.classList.add('failure');
        
        // Re-enable button after error
        button.disabled = false;
        isRolling = false;
        
    }
}

/**
 * Display roll result with animations
 */
async function displayResult(data) {
    const { result, narrative, breakdown } = data;
    
    console.log('Displaying result:', result);
    
    const rollNumber = document.getElementById('roll-number');
    const totalScore = document.getElementById('total-score');
    const resultDisplay = document.getElementById('result-display');
    const narrativeResult = document.getElementById('narrative-result');
    const button = document.getElementById('roll-btn');
    const resultBadge = document.getElementById('result-badge');
    const successIndicator = document.getElementById('success-indicator');
    
    // Update roll number
    rollNumber.textContent = result.raw_roll || result.total;
    
    // Update total score
    totalScore.textContent = `Total: ${result.total} (DC ${result.target})`;
    
    // Determine outcome
    const outcome = result.outcome || (result.success ? 'success' : 'failure');
    const outcomeData = getOutcomeData(outcome);
    
    // Update roll number color
    rollNumber.style.color = outcomeData.color;
    
    // Update result badge
    if (resultBadge) {
        resultBadge.querySelector('.badge-icon').textContent = outcomeData.emoji;
        resultBadge.querySelector('.badge-text').textContent = outcomeData.text;
    }
    
    // Update success indicator
    if (successIndicator) {
        successIndicator.textContent = outcomeData.emoji;
    }
    
    // Show result display with animation
    resultDisplay.classList.remove('result-hidden');
    resultDisplay.classList.add('result-visible');
    
    // Wait for result animation
    await sleep(500);
    
    // Build narrative text
    let narrativeText = `<div style="margin-bottom: 20px;">
        <p style="font-size: 1.3em; margin-bottom: 15px; font-weight: 600;">
            ${outcomeData.emoji} ${outcomeData.text}
        </p>
        ${result.success ? 
            `<p style="font-size: 1.1em; color: #51cf66;">You rolled ${result.total} against DC ${result.target} — Success by ${result.margin}!</p>` :
            `<p style="font-size: 1.1em; color: #ff6b6b;">You rolled ${result.total} against DC ${result.target} — Failed by ${Math.abs(result.margin)}!</p>`
        }
    </div>`;
    
    if (narrative) {
        narrativeText += `<div style="margin-bottom: 20px; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 10px;">
            <p style="font-size: 1.05em; line-height: 1.7;">${narrative}</p>
        </div>`;
    }
    
    if (breakdown) {
        narrativeText += `<div style="font-size: 0.95em; opacity: 0.85; margin-top: 20px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.2);">
            <p style="font-weight: 600; margin-bottom: 10px;">📊 Roll Breakdown:</p>
            ${breakdown.replace(/\n/g, '<br>')}
        </div>`;
    }
    
    // Show narrative result
    narrativeResult.innerHTML = narrativeText;
    narrativeResult.classList.remove('hidden');
    narrativeResult.classList.add(outcomeData.className);
    
    // Update button
    button.classList.remove('rolling');
    button.querySelector('.btn-text').textContent = 'Continuing Story...';
    button.querySelector('.btn-icon').textContent = '⏭️';
}

/**
 * Show redirect message
 */
function showRedirectMessage() {
    const button = document.getElementById('roll-btn');
    button.querySelector('.btn-text').textContent = 'Redirecting...';
    button.querySelector('.btn-icon').textContent = '🔄';
}

/**
 * Get outcome display data
 */
function getOutcomeData(outcome) {
    const outcomes = {
        'critical_success': {
            emoji: '🌟',
            text: 'Critical Success!',
            color: '#38ef7d',
            className: 'critical-success'
        },
        'success': {
            emoji: '✅',
            text: 'Success!',
            color: '#51cf66',
            className: 'success'
        },
        'failure': {
            emoji: '❌',
            text: 'Failure',
            color: '#ff6b6b',
            className: 'failure'
        },
        'critical_failure': {
            emoji: '💥',
            text: 'Critical Failure!',
            color: '#e53935',
            className: 'critical-failure'
        }
    };
    
    return outcomes[outcome] || outcomes['success'];
}

/**
 * Sleep utility function
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Rotate dice to show specific face (optional enhancement)
 */
function rotateDiceToFace(faceNumber) {
    const dice = document.getElementById('dice');
    const rotations = {
        1: 'rotateX(0deg) rotateY(0deg)',
        2: 'rotateX(0deg) rotateY(180deg)',
        3: 'rotateX(0deg) rotateY(90deg)',
        4: 'rotateX(0deg) rotateY(-90deg)',
        5: 'rotateX(90deg) rotateY(0deg)',
        6: 'rotateX(-90deg) rotateY(0deg)',
        7: 'rotateX(45deg) rotateY(45deg)',
        8: 'rotateX(-45deg) rotateY(-45deg)',
        9: 'rotateX(90deg) rotateY(90deg)',
        10: 'rotateX(-90deg) rotateY(-90deg)',
        11: 'rotateX(180deg) rotateY(0deg)',
        12: 'rotateX(0deg) rotateY(-180deg)',
        13: 'rotateX(135deg) rotateY(45deg)',
        14: 'rotateX(-135deg) rotateY(-45deg)',
        15: 'rotateX(45deg) rotateY(135deg)',
        16: 'rotateX(-45deg) rotateY(-135deg)',
        17: 'rotateX(90deg) rotateY(180deg)',
        18: 'rotateX(-90deg) rotateY(180deg)',
        19: 'rotateX(180deg) rotateY(90deg)',
        20: 'rotateX(180deg) rotateY(-90deg)'
    };
    
    if (rotations[faceNumber]) {
        dice.style.transform = rotations[faceNumber];
    }
}

// Debug helpers
window.debugDiceRoll = {
    campaignName,
    rollResult,
    testConnection: async function() {
        console.log('Testing backend connection...');
        try {
            const response = await fetch(`/campaign/${campaignName}/dice-state/roll`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            });
            const data = await response.json();
            console.log('Backend response:', data);
            return data;
        } catch (error) {
            console.error('Backend connection error:', error);
            return { error: error.message };
        }
    }
};

console.log('Debug helpers available: window.debugDiceRoll');