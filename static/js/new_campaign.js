
        let selectedPartySize = null;
        
        function selectPartySize(size) {
            selectedPartySize = size;
            document.getElementById('party-size').value = size;
            
            // Update UI
            document.querySelectorAll('.party-btn').forEach(btn => {
                btn.classList.remove('selected');
            });
            event.target.classList.add('selected');
        }
        
        document.getElementById('campaign-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!selectedPartySize) {
                alert('Please select a party size');
                return;
            }
            
            const data = {
                name: document.getElementById('name').value,
                party_size: selectedPartySize,
                description: document.getElementById('description').value
            };
            
            const response = await fetch('/campaign/new', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                location.href = '/campaign/' + result.campaign;
            } else {
                alert('Error: ' + result.error);
            }
        });
