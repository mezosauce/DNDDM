
const campaignName = {{ campaign_name | tojson }};

async function makeChoice(answer) {
    if (!confirm(`Are you sure you want to ${answer}?`)) return;

    try {
        const response = await fetch(`/campaign/${encodeURIComponent(campaignName)}/question-state/submit`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ answer: answer })
        });

        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const data = await response.json();
            if (data.error) {
                alert('Error: ' + data.error);
            }
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}
