// Response handler module - handles response display and history management

class ResponseHandler {
    constructor(apiClient, uiBuilder) {
        this.apiClient = apiClient;
        this.uiBuilder = uiBuilder;
    }

    // Initialize response handler
    init() {
        // Listen for request completion
        window.addEventListener('requestCompleted', (event) => {
            this.displayResponse(event.detail);
        });

        // Listen for request errors
        window.addEventListener('requestError', (event) => {
            this.displayError(event.detail);
        });

        // Listen for history reload
        window.addEventListener('reloadHistory', () => {
            this.loadRequestHistory();
        });

        // Setup clear history button
        const clearHistoryBtn = document.getElementById('clear-history');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => this.clearRequestHistory());
        }
        
        // Load initial history
        this.loadRequestHistory();
    }

    // Display response
    displayResponse(response) {
        // Show response section
        const responseStatus = document.getElementById('response-status');
        const responsePlaceholder = document.getElementById('response-placeholder');
        const responseBodyEl = document.getElementById('response-body');
        
        if (responseStatus) responseStatus.classList.remove('hidden');
        if (responsePlaceholder) responsePlaceholder.classList.add('hidden');
        if (responseBodyEl) responseBodyEl.classList.remove('hidden');
        
        // Update status
        const statusCode = document.getElementById('status-code');
        if (statusCode) {
            statusCode.textContent = `${response.status} ${response.statusText}`;
            statusCode.className = `font-bold ${this.uiBuilder.getStatusClass(response.status)}`;
        }
        
        // Update response time
        const responseTime = document.getElementById('response-time');
        if (responseTime) {
            responseTime.textContent = `${response.responseTime}ms`;
        }
        
        // Update response body
        const responseBody = document.querySelector('#response-body code');
        if (responseBody) {
            const formattedData = typeof response.data === 'string' 
                ? response.data 
                : JSON.stringify(response.data, null, 2);
            
            responseBody.textContent = formattedData;
        }
        
        // Highlight code if Prism is available
        if (typeof Prism !== 'undefined' && responseBody) {
            Prism.highlightElement(responseBody);
        }
    }

    // Display error
    displayError(error) {
        const responseStatus = document.getElementById('response-status');
        const responsePlaceholder = document.getElementById('response-placeholder');
        const responseBodyEl = document.getElementById('response-body');
        
        if (responseStatus) responseStatus.classList.remove('hidden');
        if (responsePlaceholder) responsePlaceholder.classList.add('hidden');
        if (responseBodyEl) responseBodyEl.classList.remove('hidden');
        
        const statusCode = document.getElementById('status-code');
        if (statusCode) {
            statusCode.textContent = 'Error';
            statusCode.className = 'font-bold status-client-error';
        }
        
        const responseBody = document.querySelector('#response-body code');
        if (responseBody) {
            responseBody.textContent = JSON.stringify({ error: error.message }, null, 2);
        }
        
        // Highlight code if Prism is available
        if (typeof Prism !== 'undefined' && responseBody) {
            Prism.highlightElement(responseBody);
        }
    }

    // Load request history
    loadRequestHistory() {
        const history = this.apiClient.getHistory();
        const container = document.getElementById('history-list');
        
        // Return early if container doesn't exist
        if (!container) {
            console.warn('History list container not found');
            return;
        }
        
        if (history.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4 text-gray-500 dark:text-gray-400">
                    No requests yet
                </div>
            `;
        } else {
            container.innerHTML = history.slice(0, 10)
                .map(entry => this.uiBuilder.buildHistoryItem(entry))
                .join('');
        }
    }

    // Clear request history
    clearRequestHistory() {
        if (confirm('Are you sure you want to clear all request history?')) {
            this.apiClient.clearHistory();
            this.loadRequestHistory();
            
            // Show a temporary success message
            const container = document.getElementById('history-list');
            if (!container) {
                console.warn('History list container not found');
                return;
            }
            
            container.innerHTML = `
                <div class="text-center py-4 text-green-500 dark:text-green-400">
                    History cleared successfully!
                </div>
            `;
            
            // After 2 seconds, show the normal empty state
            setTimeout(() => {
                const container = document.getElementById('history-list');
                if (container) {
                    container.innerHTML = `
                        <div class="text-center py-4 text-gray-500 dark:text-gray-400">
                            No requests yet
                        </div>
                    `;
                }
            }, 2000);
        }
    }
}

// Export for use in other scripts
window.ResponseHandler = ResponseHandler;