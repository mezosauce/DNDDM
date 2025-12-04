// Extract campaign name from URL: /campaign/{name}/question-state
const campaignName = window.location.pathname.split('/')[2];

async function makeChoice(answer) {
    // Visual feedback
    const card = event.currentTarget;
    card.style.opacity = '0.5';
    card.style.pointerEvents = 'none';
    
    // Disable all cards
    document.querySelectorAll('.choice-card').forEach(c => {
        c.style.pointerEvents = 'none';
    });

    try {
        const response = await fetch(`/campaign/${encodeURIComponent(campaignName)}/question-state/submit`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ answer: answer })
        });

        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            // Handle JSON response with redirect URL
            const data = await response.json();
            if (data.redirect) {
                window.location.href = data.redirect;
            } else if (data.error) {
                alert('Error: ' + data.error);
                // Re-enable cards
                document.querySelectorAll('.choice-card').forEach(c => {
                    c.style.pointerEvents = 'auto';
                    c.style.opacity = '1';
                });
            }
        } else {
            const data = await response.json();
            alert('Error: ' + (data.error || 'Unknown error'));
            // Re-enable cards
            document.querySelectorAll('.choice-card').forEach(c => {
                c.style.pointerEvents = 'auto';
                c.style.opacity = '1';
            });
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error submitting choice: ' + error.message);
        // Re-enable cards
        document.querySelectorAll('.choice-card').forEach(c => {
            c.style.pointerEvents = 'auto';
            c.style.opacity = '1';
        });
    }
}