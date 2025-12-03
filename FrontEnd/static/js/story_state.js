// Story State Page - Phase 3
const campaignName = window.location.pathname.split('/')[2];

function generateNarrative() {
    const button = document.querySelector('.generate-btn');
    const narrativeBox = document.getElementById('narrative-content');
    
    button.disabled = true;
    button.textContent = '⏳ Generating...';
    
    narrativeBox.innerHTML = '<div class="loading"><p>Generating narrative content...</p></div>';
    
    fetch(`/campaign/${campaignName}/story-state/ai-generate`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({force_regenerate: false})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            narrativeBox.innerHTML = `<p>${data.content}</p>`;
            
            // Replace generate button with continue button
            const actionButtons = document.getElementById('action-buttons');
            actionButtons.innerHTML = `
                <button class="continue-btn" onclick="advanceStory()">
                    → Continue to Next Step
                </button>
            `;
        } else {
            narrativeBox.innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
            button.disabled = false;
            button.textContent = '✨ Generate Story Content';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        narrativeBox.innerHTML = `<p style="color: red;">Error generating content</p>`;
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
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            return response.json();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error advancing story');
        button.disabled = false;
        button.textContent = '→ Continue to Next Step';
    });
}