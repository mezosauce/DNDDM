
const campaignName = {{ campaign_name | tojson }};

async function generateNarrative() {
    const narrativeBox = document.getElementById('narrative-content');
    const actionButtons = document.getElementById('action-buttons');

    // Show loading
    narrativeBox.innerHTML = '<div class="loading"><div class="spinner"></div><p>Generating narrative...</p></div>';
    actionButtons.innerHTML = '';

    try {
        const response = await fetch(`/campaign/${encodeURIComponent(campaignName)}/story-state/ai-generate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                force_regenerate: false
            })
        });

        const data = await response.json();

        if (data.error) {
            narrativeBox.innerHTML = `<p style="color: #ff6b6b;">Error: ${data.error}</p>`;
            return;
        }

        // Display content
        narrativeBox.innerHTML = data.content;

        // Show continue button
        actionButtons.innerHTML = `
            <button class="continue-btn" onclick="advanceStory()">
                → Continue to Next Step
            </button>
        `;

    } catch (error) {
        narrativeBox.innerHTML = `<p style="color: #ff6b6b;">Error: ${error.message}</p>`;
    }
}

function advanceStory() {
    if (!confirm('Ready to continue to the next step?')) return;

    // Submit form to advance
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/campaign/${encodeURIComponent(campaignName)}/story-state/advance`;
    document.body.appendChild(form);
    form.submit();
}
