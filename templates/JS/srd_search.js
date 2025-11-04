
        // Configuration
        const API_BASE = window.location.origin;
        let currentResults = [];
        let selectedIndex = -1;

        // Initialize
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });

        // Show/hide back to top button
        window.addEventListener('scroll', () => {
            const backToTop = document.getElementById('back-to-top');
            if (window.pageYOffset > 300) {
                backToTop.style.display = 'block';
            } else {
                backToTop.style.display = 'none';
            }
        });

        function scrollToTop() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function quickSearch(query) {
            document.getElementById('search-input').value = query;
            performSearch();
        }

        async function performSearch() {
            const query = document.getElementById('search-input').value.trim();
            if (!query) return;

            const resultsList = document.getElementById('results-list');
            const statsBar = document.getElementById('stats-bar');
            
            // Show loading
            resultsList.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Searching the SRD...</p>
                </div>
            `;

            const startTime = performance.now();

            try {
                const response = await fetch(`${API_BASE}/api/search`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query: query,
                        top_k: 10
                    })
                });

                const data = await response.json();
                const endTime = performance.now();
                const searchTime = Math.round(endTime - startTime);

                if (data.error) {
                    showError(data.error);
                    return;
                }

                currentResults = data.results || [];
                displayResults(currentResults);
                
                // Update stats
                document.getElementById('result-count').textContent = currentResults.length;
                document.getElementById('search-time').textContent = `${searchTime}ms`;
                statsBar.style.display = 'flex';

            } catch (error) {
                showError(`Connection error: ${error.message}`);
            }
        }

        function displayResults(results) {
            const resultsList = document.getElementById('results-list');

            if (results.length === 0) {
                resultsList.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">😕</div>
                        <h3>No Results Found</h3>
                        <p>Try a different search term or check your spelling</p>
                    </div>
                `;
                return;
            }

            resultsList.innerHTML = results.map((result, index) => `
                <div class="result-item" onclick="selectResult(${index})" data-index="${index}">
                    <div class="result-title">
                        ${escapeHtml(result.title)}
                        <span class="result-score">Score: ${result.score.toFixed(2)}</span>
                    </div>
                    <div class="result-category">${result.category}</div>
                    <div class="result-snippet">${escapeHtml(result.snippet)}</div>
                </div>
            `).join('');
        }

        async function selectResult(index) {
            if (index < 0 || index >= currentResults.length) return;

            selectedIndex = index;
            const result = currentResults[index];

            // Update visual selection
            document.querySelectorAll('.result-item').forEach((el, i) => {
                if (i === index) {
                    el.classList.add('active');
                } else {
                    el.classList.remove('active');
                }
            });

            // Display content
            await displayContent(result);
        }

        async function displayContent(result) {
            const viewer = document.getElementById('content-viewer');
            
            viewer.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading content...</p>
                </div>
            `;

            try {
                // Fetch the actual MD file content via API
                const response = await fetch(`${API_BASE}/api/srd/file`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        file_path: result.file_path
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Content not found');
                }

                const data = await response.json();
                
                if (data.error) {
                    throw new Error(data.error);
                }

                const html = convertMarkdownToHTML(data.content);

                viewer.innerHTML = `
                    <div class="viewer-content">
                        <div style="margin-bottom: 20px; padding: 10px; background: rgba(77, 171, 247, 0.1); border-radius: 6px;">
                            <small style="color: #888;">
                                📁 ${result.file_path} | 📂 ${result.category}
                            </small>
                        </div>
                        ${html}
                    </div>
                `;

            } catch (error) {
                viewer.innerHTML = `
                    <div class="error-message">
                        <h3>⚠️ Content Not Available</h3>
                        <p>${error.message}</p>
                        <hr style="margin: 20px 0; border: 1px solid #ff6b6b;">
                        <h4>Preview from Search:</h4>
                        <div style="margin-top: 15px; text-align: left; white-space: pre-wrap;">
                            ${escapeHtml(result.content)}
                        </div>
                    </div>
                `;
            }
        }

        function convertMarkdownToHTML(markdown) {
            // Basic markdown to HTML conversion
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

            return html;
        }

        function showError(message) {
            const resultsList = document.getElementById('results-list');
            resultsList.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Error</h3>
                    <p>${escapeHtml(message)}</p>
                </div>
            `;
            document.getElementById('stats-bar').style.display = 'none';
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (currentResults.length === 0) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (selectedIndex < currentResults.length - 1) {
                    selectResult(selectedIndex + 1);
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (selectedIndex > 0) {
                    selectResult(selectedIndex - 1);
                }
            }
        });
