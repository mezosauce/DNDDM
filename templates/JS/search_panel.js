>
        let currentCategory = '';
        let lastResults = [];
        
        // Category filter handling
        document.querySelectorAll('.category-chip').forEach(chip => {
            chip.addEventListener('click', function() {
                // Update active state
                document.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                
                currentCategory = this.dataset.category;
                
                // Re-run search if we have a query
                const query = document.getElementById('search-input').value;
                if (query) {
                    performSearch();
                }
            });
        });
        
        function handleEnter(event) {
            if (event.key === 'Enter') {
                performSearch();
            }
        }
        
        function quickSearch(query) {
            document.getElementById('search-input').value = query;
            performSearch();
        }
        
        async function performSearch() {
            const query = document.getElementById('search-input').value.trim();
            if (!query) return;
            
            const resultsDiv = document.getElementById('search-results');
            resultsDiv.innerHTML = '<div class="search-loading"><div class="spinner"></div><p>Searching...</p></div>';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        query: query,
                        top_k: 10,
                        category: currentCategory || undefined
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="search-empty">Error: ${data.error}</div>`;
                    return;
                }
                
                lastResults = data.results;
                displayResults(data.results);
                
            } catch (error) {
                resultsDiv.innerHTML = `<div class="search-empty">Connection error: ${error.message}</div>`;
            }
        }
        
        function displayResults(results) {
            const resultsDiv = document.getElementById('search-results');
            
            if (results.length === 0) {
                resultsDiv.innerHTML = '<div class="search-empty">No results found</div>';
                return;
            }
            
            resultsDiv.innerHTML = results.map((result, index) => `
                <div class="search-result" onclick="showDetails(${index})">
                    <div class="result-title">${escapeHtml(result.title)}</div>
                    <div class="result-category">${result.category}</div>
                    <div class="result-snippet">${escapeHtml(result.snippet)}</div>
                    <div class="result-score">Relevance: ${(result.score * 100).toFixed(0)}%</div>
                    <div class="result-actions">
                        <button class="result-btn btn-info" onclick="event.stopPropagation(); showDetails(${index})">
                            📖 View Full
                        </button>
                        <button class="result-btn btn-success" onclick="event.stopPropagation(); insertToChat('${escapeHtml(result.title)}')">
                            💬 Ask About This
                        </button>
                    </div>
                </div>
            `).join('');
        }
        
        function showDetails(index) {
            const result = lastResults[index];
            
            document.getElementById('modal-title').textContent = result.title;
            document.getElementById('modal-category').textContent = result.category;
            document.getElementById('modal-content').textContent = result.content;
            document.getElementById('detail-modal').style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('detail-modal').style.display = 'none';
        }
        
        function insertToChat(title) {
            // If this is embedded in active_campaign.html, send to chat
            if (window.parent && window.parent.document.getElementById('action-input')) {
                const input = window.parent.document.getElementById('action-input');
                input.value = `Tell me about ${title}`;
                input.focus();
                
                // Show feedback
                alert(`Added "${title}" to chat input`);
            } else {
                alert('Search result: ' + title);
            }
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        // Close modal on outside click
        window.onclick = function(event) {
            const modal = document.getElementById('detail-modal');
            if (event.target === modal) {
                closeModal();
            }
        }
        
        // Auto-focus search input
        window.onload = () => {
            const input = document.getElementById('search-input');
            if (input) input.focus();
        };
    </script>