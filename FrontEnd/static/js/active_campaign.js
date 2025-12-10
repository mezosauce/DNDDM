        const socket = io();
        let isLoading = false;
        let currentTurn = 0;
        let debugMode = false;
        let sessionStarted = false;
        let srdSearchResults = [];
        let selectedSrdIndex = -1;



function toggleBottomSearch() {
    const searchContent = document.getElementById('search-content');
    const toggleText = document.getElementById('search-toggle-text');
    
    if (searchContent.style.display === 'none') {
        searchContent.style.display = 'block';
        toggleText.textContent = '▼ Collapse';
    } else {
        searchContent.style.display = 'none';
        toggleText.textContent = '▲ Expand';
    }
}

// Add to the existing escapeHtml function if it doesn't exist:
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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
    
    // Show in a simple alert or insert into chat
    if (confirm(`View: ${result.title}\n\nAsk the DM about this?`)) {
        const input = document.getElementById('action-input');
        input.value = `Tell me about ${result.title}`;
        input.focus();
    }
}
        // Get data passed from HTML
        const sessionNumber = window.campaignData.sessionNumber;
        const campaignName = window.campaignData.campaignName;
        const preparationsContent = window.campaignData.preparationsContent;
        const isFirstSession = window.campaignData.isFirstSession;      
        // Parse quest details from preparations content
        function parseQuestDetails() {
            if (!preparationsContent) return;
            
            const sections = {
                'quest-hook': /### Quest Hook\s*\n(.*?)(?=###|$)/s,
                'quest-objective': /### Main Objective\s*\n(.*?)(?=###|$)/s,
                'quest-location': /### Starting Location\s*\n(.*?)(?=###|$)/s,
                'quest-npcs': /### Key NPCs\s*\n(.*?)(?=###|$)/s
            };
            
            for (const [id, regex] of Object.entries(sections)) {
                const match = preparationsContent.match(regex);
                if (match && match[1]) {
                    const element = document.getElementById(id);
                    if (element) {
                        element.textContent = match[1].trim().replace(/\*\*([^*]+)\*\*/g, '$1');
                    }
                }
            }
            
            // Populate full quest modal
            const fullContent = document.getElementById('full-quest-content');
            if (fullContent) {
                fullContent.innerHTML = `<pre style="white-space: pre-wrap; line-height: 1.6;">${escapeHtml(preparationsContent)}</pre>`;
            }
        }
        
        function toggleFullQuestDetails() {
            document.getElementById('quest-modal').style.display = 'block';
        }
        
        function closeQuestModal() {
            document.getElementById('quest-modal').style.display = 'none';
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('quest-modal');
            if (event.target === modal) {
                closeQuestModal();
            }
        }
        
        // Auto-start Session 1 with opening scene
        window.onload = () => {
            // Parse quest details
            parseQuestDetails();
            
            // Load saved notes
            const savedNotes = localStorage.getItem(`session_${sessionNumber}_notes`);
            if (savedNotes) {
                document.getElementById('session-notes').value = savedNotes;
            }

            // Apply HP bar widths from data attributes
            document.querySelectorAll('.hp-fill[data-hp-pct]').forEach(el => {
                const pct = el.getAttribute('data-hp-pct');
                if (pct !== null) {
                    el.style.width = pct + '%';
                }
            });
            
            
            // Check if this is Session 1 and hasn't been started yet
            const sessionStartedKey = `session_1_started_${campaignName}`;

            sessionStarted = localStorage.getItem(sessionStartedKey) === 'true';
            
            if (isFirstSession && !sessionStarted) {
                // Show banner and auto-start
                const banner = document.createElement('div');
                banner.className = 'session-start-banner';
                banner.innerHTML = ' Session 1 Beginning! The adventure starts now... ';
                document.querySelector('.phase-header').after(banner);
                
                // Auto-start after short delay
                setTimeout(() => {
                    banner.remove();
                    startSessionOne();
                }, 2000);
                
                // Mark as started
                localStorage.setItem(sessionStartedKey, 'true');
            } else {
                // Regular welcome message for ongoing sessions
                addMessage(`Session ${sessionNumber} continues! What do you do?`, 'system');
            }
        };
        
        async function startSessionOne() {
            addMessage('🎬 The Dungeon Master begins your tale...', 'system');
            
            // Disable input during opening scene
            const input = document.getElementById('action-input');
            const actionBtn = document.getElementById('action-btn');
            input.disabled = true;
            actionBtn.disabled = true;
            
            // Add AI thinking indicator
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'ai-thinking';
            thinkingDiv.id = 'ai-thinking';
            thinkingDiv.innerHTML = `
                <div class="thinking-dots">
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                </div>
                <span>Crafting your opening scene...</span>
            `;
            document.getElementById('chat-container').appendChild(thinkingDiv);
            
            try {
                const response = await fetch(`/campaign/${campaignName}/ai-assist`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        query: 'START_SESSION_1',
                        is_first_message: true,
                        campaign_name: campaignName
                    })
                });
                
                // Remove thinking indicator
                const thinking = document.getElementById('ai-thinking');
                if (thinking) thinking.remove();
                
                const data = await response.json();
                
                if (data.error) {
                    addMessage(`❌ Error: ${data.error}`, 'dm');
                    if (debugMode) {
                        addDebugInfo({ error: data.error });
                    }
                } else {
                    addMessage(data.response, 'dm');
                    if (debugMode && data.routing_info) {
                        addRoutingInfo(data.routing_info);
                    }
                }
            } catch (error) {
                const thinking = document.getElementById('ai-thinking');
                if (thinking) thinking.remove();
                addMessage(`❌ Connection Error: ${error.message}`, 'dm');
                if (debugMode) {
                    addDebugInfo({ error: error.message, stack: error.stack });
                }
            }
            
            // Re-enable input
            input.disabled = false;
            actionBtn.disabled = false;
            input.focus();
        }
        
        function toggleDebug() {
            debugMode = !debugMode;
            document.getElementById('debug-status').textContent = debugMode ? 'ON' : 'OFF';
            document.getElementById('debug-toggle').style.background = 
                debugMode ? 'rgba(81, 207, 102, 0.2)' : 'rgba(77, 171, 247, 0.2)';
        }
        
        async function takeAction() {
            if (isLoading) return;
            
            const input = document.getElementById('action-input');
            const action = input.value.trim();
            if (!action) return;
            
            addMessage(action, 'player');
            input.value = '';
            isLoading = true;
            
            // Disable button during loading
            const actionBtn = document.getElementById('action-btn');
            actionBtn.disabled = true;
            actionBtn.textContent = 'Processing...';
            
            // Add AI thinking indicator
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'ai-thinking';
            thinkingDiv.id = 'ai-thinking';
            thinkingDiv.innerHTML = `
                <div class="thinking-dots">
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                    <div class="thinking-dot"></div>
                </div>
                <span>DM is preparing a response...</span>
            `;
            document.getElementById('chat-container').appendChild(thinkingDiv);
            
            try {
                const response = await fetch(`/campaign/${campaignName}/ai-assist`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: action})
                });
                
                // Remove thinking indicator
                const thinking = document.getElementById('ai-thinking');
                if (thinking) thinking.remove();
                
                const data = await response.json();
                
                if (data.error) {
                    addMessage(`❌ Error: ${data.error}`, 'dm');
                    
                    // Show error details in debug mode
                    if (debugMode) {
                        addDebugInfo({
                            error: data.error,
                            query: action
                        });
                    }
                } else {
                    addMessage(data.response, 'dm');
                    
                    // Show routing info in debug mode
                    if (debugMode && data.routing_info) {
                        addRoutingInfo(data.routing_info);
                    }
                }
            } catch (error) {
                // Remove thinking indicator
                const thinking = document.getElementById('ai-thinking');
                if (thinking) thinking.remove();
                
                addMessage(`❌ Connection Error: ${error.message}`, 'dm');
                
                if (debugMode) {
                    addDebugInfo({
                        error: error.message,
                        query: action,
                        stack: error.stack
                    });
                }
            }
            
            // Re-enable button
            actionBtn.disabled = false;
            actionBtn.textContent = 'Take Action';
            isLoading = false;
        }
        
        function addMessage(text, type) {
            const container = document.getElementById('chat-container');
            const div = document.createElement('div');
            div.className = `message message-${type}`;
            
            let label = '';
            if (type === 'player') label = ' Player';
            else if (type === 'dm') label = '🎭 DM';
            else if (type === 'system') label = '📢 System';
            
            div.innerHTML = `
                ${label ? `<div class="message-label">${label}</div>` : ''}
                <div class="message-content">${escapeHtml(text)}</div>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
        
        function addRoutingInfo(routingInfo) {
            const container = document.getElementById('chat-container');
            const div = document.createElement('div');
            div.className = 'routing-info';
            
            let badges = '';
            if (routingInfo.categories && routingInfo.categories.length > 0) {
                badges = routingInfo.categories.map(cat => 
                    `<span class="routing-badge">${cat}</span>`
                ).join('');
            }
            
            div.innerHTML = `
                <strong>🔍 SRD Context Used:</strong><br>
                ${badges || 'None'}
                <br>
                <small>Files loaded: ${routingInfo.files_loaded || 0}</small>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
        
        function addDebugInfo(debugData) {
            const container = document.getElementById('chat-container');
            const div = document.createElement('div');
            div.className = 'error-details';
            div.innerHTML = `
                <strong>Debug Info:</strong><br>
                ${JSON.stringify(debugData, null, 2)}
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        async function roll(dice) {
            // Simple client-side dice roller
            const sides = parseInt(dice.replace('d', ''));
            const result = Math.floor(Math.random() * sides) + 1;
            
            displayDiceResult({
                dice: dice,
                total: result,
                natural_20: sides === 20 && result === 20,
                natural_1: sides === 20 && result === 1
            });
            
            addMessage(`Rolled ${dice}: ${result}`, 'system');
        }
        
        async function rollCustom() {
            const dice = document.getElementById('custom-dice').value;
            // Parse dice notation (e.g., "2d6+3")
            const match = dice.match(/(\d+)?d(\d+)([\+\-]\d+)?/i);
            
            if (!match) {
                alert('Invalid dice format. Use format like: 2d6+3');
                return;
            }
            
            const count = parseInt(match[1] || '1');
            const sides = parseInt(match[2]);
            const modifier = parseInt(match[3] || '0');
            
            let total = modifier;
            let rolls = [];
            
            for (let i = 0; i < count; i++) {
                const roll = Math.floor(Math.random() * sides) + 1;
                rolls.push(roll);
                total += roll;
            }
            
            displayDiceResult({
                dice: dice,
                total: total,
                rolls: rolls,
                natural_20: sides === 20 && rolls.includes(20),
                natural_1: sides === 20 && rolls.includes(1)
            });
            
            addMessage(`Rolled ${dice}: ${total} (${rolls.join(', ')})`, 'system');
        }
        
        function displayDiceResult(data) {
            const resultDiv = document.getElementById('dice-result');
            let className = 'dice-result';
            if (data.natural_20) className += ' natural-20';
            if (data.natural_1) className += ' natural-1';
            
            resultDiv.className = className;
            resultDiv.innerHTML = `
                ${data.dice}: ${data.total}
                ${data.natural_20 ? '<br>🌟 CRITICAL!' : ''}
                ${data.natural_1 ? '<br>💀 FUMBLE!' : ''}
            `;
        }
        
        function quickAction(action) {
            document.getElementById('action-input').value = action;
            takeAction();
        }
        
        
        async function endSession() {
            if (!confirm('End this session? Your notes will be saved.')) return;
            
            const notes = document.getElementById('session-notes').value;
            localStorage.setItem(`session_${sessionNumber}_notes`, notes);

            alert('Session ended! Notes saved to browser storage.');
            location.href = `/campaign/${campaignName}`;
        }
        
        // Keyboard shortcuts
        document.getElementById('action-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                takeAction();
            }
        });

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
                top_k: 8
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
        <div class="srd-result ${index === selectedSrdIndex ? 'active' : ''}" onclick="selectSrdResult(${index})">
            <div class="srd-result-title">${escapeHtml(result.title)}</div>
            <div class="srd-result-category">${result.category}</div>
            <div class="srd-result-snippet">${escapeHtml(result.snippet)}</div>
            <div class="srd-result-score">Relevance: ${(result.score * 100).toFixed(0)}%</div>
        </div>
    `).join('');
}

async function selectSrdResult(index) {
    if (index < 0 || index >= srdSearchResults.length) return;
    
    selectedSrdIndex = index;
    const result = srdSearchResults[index];
    
    // Update visual selection
    document.querySelectorAll('.srd-result').forEach((el, i) => {
        if (i === index) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    });
    
    // Show full content in modal
    await showSRDDetailModal(result);
}

async function showSRDDetailModal(result) {
    // Create or get modal
    let modal = document.getElementById('srd-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'srd-modal';
        modal.className = 'srd-modal';
        modal.innerHTML = `
            <div class="srd-modal-content">
                <span class="srd-modal-close" onclick="closeSRDModal()">&times;</span>
                <div class="srd-modal-header">
                    <h2 id="srd-modal-title"></h2>
                    <div id="srd-modal-category" class="srd-result-category"></div>
                    <div id="srd-modal-file" style="font-size: 0.8em; color: #888; margin-top: 5px;"></div>
                </div>
                <div id="srd-modal-body">
                    <div class="srd-modal-loading">
                        <div class="spinner"></div>
                        <p>Loading content...</p>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Show modal
    modal.style.display = 'block';
    
    // Update header
    document.getElementById('srd-modal-title').textContent = result.title;
    document.getElementById('srd-modal-category').textContent = result.category;
    document.getElementById('srd-modal-file').textContent = `📁 ${result.file_path}`;
    
    // Load full content
    const bodyDiv = document.getElementById('srd-modal-body');
    bodyDiv.innerHTML = '<div class="srd-modal-loading"><div class="spinner"></div><p>Loading content...</p></div>';
    
    try {
        const response = await fetch('/api/srd/file', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_path: result.file_path })
        });
        
        if (!response.ok) {
            throw new Error('Content not found');
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Convert markdown to HTML
        const html = convertMarkdownToHTML(data.content);
        bodyDiv.innerHTML = `<div class="srd-content-viewer">${html}</div>`;
        
    } catch (error) {
        bodyDiv.innerHTML = `
            <div class="error-message">
                <h3>⚠️ Could not load full content</h3>
                <p>${error.message}</p>
                <hr style="margin: 20px 0; border: 1px solid #C19A6B;">
                <h4>Preview from Search:</h4>
                <div style="margin-top: 15px; white-space: pre-wrap; line-height: 1.6;">
                    ${escapeHtml(result.content)}
                </div>
            </div>
        `;
    }
}

function closeSRDModal() {
    const modal = document.getElementById('srd-modal');
    if (modal) modal.style.display = 'none';
}

function convertMarkdownToHTML(markdown) {
    let html = markdown;
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Code blocks
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Tables (basic)
    html = html.replace(/\|(.+)\|/g, (match) => {
        const cells = match.split('|').filter(s => s.trim());
        const cellsHtml = cells.map(cell => `<td>${cell.trim()}</td>`).join('');
        return `<tr>${cellsHtml}</tr>`;
    });
    html = html.replace(/(<tr>.*<\/tr>)+/g, '<table>$&</table>');
    
    // Lists
    html = html.replace(/^\* (.+)$/gim, '<li>$1</li>');
    html = html.replace(/^\- (.+)$/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)+/g, '<ul>$&</ul>');
    
    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    
    // Clean up
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p>(<h[1-6]>)/g, '$1');
    html = html.replace(/(<\/h[1-6]>)<\/p>/g, '$1');
    html = html.replace(/<p>(<table>)/g, '$1');
    html = html.replace(/(<\/table>)<\/p>/g, '$1');
    html = html.replace(/<p>(<ul>)/g, '$1');
    html = html.replace(/(<\/ul>)<\/p>/g, '$1');
    html = html.replace(/<p>(<pre>)/g, '$1');
    html = html.replace(/(<\/pre>)<\/p>/g, '$1');
    
    return html;
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('srd-modal');
    if (modal && event.target === modal) {
        closeSRDModal();
    }
});
