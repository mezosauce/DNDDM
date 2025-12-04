// Dice State Page - Phase 3
const campaignName = window.location.pathname.split('/')[2];

async function rollDice() {
    const button = document.querySelector('.roll-btn');
    button.disabled = true;
    button.textContent = '🎲 Rolling...';
    
    try {
        const response = await fetch(`/campaign/${campaignName}/dice-state/roll`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Display result
            displayResult(data);
            
            // Wait 2 seconds then redirect
            setTimeout(() => {
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            }, 2000);
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
            button.disabled = false;
            button.textContent = '🎲 Roll Dice';
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error rolling dice: ' + error.message);
        button.disabled = false;
        button.textContent = '🎲 Roll Dice';
    }
}

function displayResult(data) {
    const resultBox = document.getElementById('result-display');
    if (!resultBox) return;
    
    const { result, narrative, breakdown } = data;
    
    let outcomeClass = 'success';
    if (result.outcome === 'critical_success') outcomeClass = 'crit-success';
    else if (result.outcome === 'failure') outcomeClass = 'failure';
    else if (result.outcome === 'critical_failure') outcomeClass = 'crit-failure';
    
    resultBox.innerHTML = `
        <div class="result-box ${outcomeClass}">
            <div class="dice-roll">${result.raw_roll}</div>
            <div class="result-text">${narrative}</div>
            <div class="breakdown">${breakdown.replace(/\n/g, '<br>')}</div>
        </div>
    `;
}