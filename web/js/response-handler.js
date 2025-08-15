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
        document.getElementById('clear-history').addEventListener('click', () => this.clearRequestHistory());
        
        // Load initial history
        this.loadRequestHistory();
    }

    // Display response
    displayResponse(response) {
        // Show response section
        document.getElementById('response-status').classList.remove('hidden');
        document.getElementById('response-placeholder').classList.add('hidden');
        document.getElementById('response-body').classList.remove('hidden');
        
        // Update status
        const statusCode = document.getElementById('status-code');
        statusCode.textContent = `${response.status} ${response.statusText}`;
        statusCode.className = `font-bold ${this.uiBuilder.getStatusClass(response.status)}`;
        
        // Update response time
        document.getElementById('response-time').textContent = `${response.responseTime}ms`;
        
        // Update response body
        const responseBody = document.querySelector('#response-body code');
        const formattedData = typeof response.data === 'string' 
            ? response.data 
            : JSON.stringify(response.data, null, 2);
        
        responseBody.textContent = formattedData;
        
        // Highlight code if Prism is available
        if (typeof Prism !== 'undefined') {
            Prism.highlightElement(responseBody);
        }
    }

    // Display error
    displayError(error) {
        document.getElementById('response-status').classList.remove('hidden');
        document.getElementById('response-placeholder').classList.add('hidden');
        document.getElementById('response-body').classList.remove('hidden');
        
        const statusCode = document.getElementById('status-code');
        statusCode.textContent = 'Error';
        statusCode.className = 'font-bold status-client-error';
        
        const responseBody = document.querySelector('#response-body code');
        responseBody.textContent = JSON.stringify({ error: error.message }, null, 2);
        
        // Highlight code if Prism is available
        if (typeof Prism !== 'undefined') {
            Prism.highlightElement(responseBody);
        }
    }

    // Load request history
    loadRequestHistory() {
        const history = this.apiClient.getHistory();
        const container = document.getElementById('history-list');
        
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
            container.innerHTML = `
                <div class="text-center py-4 text-green-500 dark:text-green-400">
                    History cleared successfully!
                </div>
            `;
            
            // After 2 seconds, show the normal empty state
            setTimeout(() => {
                container.innerHTML = `
                    <div class="text-center py-4 text-gray-500 dark:text-gray-400">
                        No requests yet
                    </div>
                `;
            }, 2000);
        }
    }
}