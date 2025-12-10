// Story State Page - Phase 3
const campaignName = window.location.pathname.split('/')[2];

function generateNarrative() {
    const button = document.querySelector('.generate-btn');
    const narrativeBox = document.getElementById('narrative-content');
    
    button.disabled = true;
    button.textContent = '⏳ Generating...';
    
    narrativeBox.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating narrative content...</p></div>';
    
    fetch(`/campaign/${campaignName}/story-state/ai-generate`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({force_regenerate: false})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Format the content with proper line breaks
            const formattedContent = data.content.replace(/\n/g, '<br>');
            narrativeBox.innerHTML = `<p>${formattedContent}</p>`;
            
            // Replace generate button with continue button
            const actionButtons = document.getElementById('action-buttons');
            const isConditional = data.is_conditional_evaluation || false;
            
            actionButtons.innerHTML = `
                <button class="continue-btn" onclick="advanceStory()">
                    ${isConditional ? ' Evaluate & Continue' : '→ Continue to Next Step'}
                </button>
            `;
        } else {
            narrativeBox.innerHTML = `<p style="color: #C19A6B;">Error: ${data.error}</p>`;
            button.disabled = false;
            button.textContent = '✨ Generate Story Content';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        narrativeBox.innerHTML = `<p style="color: #C19A6B;">Error generating content. Please try again.</p>`;
        button.disabled = false;
        button.textContent = '✨ Generate Story Content';
    });
}

function advanceStory() {
    const button = document.querySelector('.continue-btn');
    button.disabled = true;
    button.textContent = '⏳ Advancing...';
    
    fetch(`/campaign/${campaignName}/story-state/advance`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Follow the redirect URL
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                // Fallback - reload the page
                window.location.reload();
            }
        } else {
            alert('Error: ' + (data.error || 'Unknown error'));
            button.disabled = false;
            button.textContent = '→ Continue to Next Step';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error advancing story. Please try again.');
        button.disabled = false;
        button.textContent = '→ Continue to Next Step';
    });
}