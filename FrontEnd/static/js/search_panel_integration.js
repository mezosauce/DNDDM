
    // Add to existing script section
    
    let srdSearchResults = [];
    
    function quickSearchSRD(query) {
        document.getElementById('srd-search-input').value = query;
        searchSRD();
    }
    
    async function searchSRD() {
        const query = document.getElementById('srd-search-input').value.trim();
        if (!query) return;
        
        const resultsDiv = document.getElementById('srd-results');
        resultsDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #888;"><div class="spinner"></div>Searching...</div>';
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    query: query,
                    top_k: 5
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                resultsDiv.innerHTML = `<div style="color: #C19A6B; padding: 10px;">${data.error}</div>`;
                return;
            }
            
            srdSearchResults = data.results;
            displaySRDResults(data.results);
            
        } catch (error) {
            resultsDiv.innerHTML = `<div style="color: #C19A6B; padding: 10px;">Error: ${error.message}</div>`;
        }
    }
    
    function displaySRDResults(results) {
        const resultsDiv = document.getElementById('srd-results');
        
        if (results.length === 0) {
            resultsDiv.innerHTML = '<div style="text-align: center; color: #888; padding: 20px;">No results found</div>';
            return;
        }
        
        resultsDiv.innerHTML = results.map((result, index) => `
            <div class="srd-result" onclick="showSRDDetail(${index})">
                <div class="srd-result-title">${escapeHtml(result.title)}</div>
                <div class="srd-result-category">${result.category}</div>
                <div class="srd-result-snippet">${escapeHtml(result.snippet)}</div>
            </div>
        `).join('');
    }
    
    function showSRDDetail(index) {
        const result = srdSearchResults[index];
        
        // Create modal if it doesn't exist
        let modal = document.getElementById('srd-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'srd-modal';
            modal.className = 'srd-modal';
            modal.innerHTML = `
                <div class="srd-modal-content">
                    <span class="srd-modal-close" onclick="closeSRDModal()">&times;</span>
                    <h2 id="srd-modal-title"></h2>
                    <div id="srd-modal-category" style="display: inline-block; padding: 4px 10px; background: rgba(77, 171, 247, 0.2); border-radius: 4px; margin-bottom: 15px;"></div>
                    <pre id="srd-modal-content" style="white-space: pre-wrap; line-height: 1.6; color: #d0d0d0;"></pre>
                    <button onclick="askAboutSRD('${escapeHtml(result.title)}')" style="margin-top: 15px;">
                        💬 Ask DM About This
                    </button>
                </div>
            `;
            document.body.appendChild(modal);
        }
        
        document.getElementById('srd-modal-title').textContent = result.title;
        document.getElementById('srd-modal-category').textContent = result.category;
        document.getElementById('srd-modal-content').textContent = result.content;
        modal.style.display = 'block';
    }
    
    function closeSRDModal() {
        const modal = document.getElementById('srd-modal');
        if (modal) modal.style.display = 'none';
    }
    
    function askAboutSRD(title) {
        const input = document.getElementById('action-input');
        input.value = `Tell me about ${title}`;
        input.focus();
        closeSRDModal();
    }
    
    // Close modal on outside click
    document.addEventListener('click', function(event) {
        const modal = document.getElementById('srd-modal');
        if (modal && event.target === modal) {
            closeSRDModal();
        }
    });