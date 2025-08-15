// Main application logic for MCP Server API Tester

// Global variables
let apiClient;
let uiBuilder;
let openApiSpec;
let currentEndpoint = null;
let preferredBodyView = localStorage.getItem('preferredBodyView') || 'json'; // Store user's preferred view mode

// Initialize application
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize classes
    apiClient = new APIClient();
    uiBuilder = new UIBuilder();
    
    // Load OpenAPI spec
    await loadOpenApiSpec();
    
    // Setup UI
    setupTheme();
    setupEventListeners();
    updateAuthStatus();
    updateBaseUrl();
    loadRequestHistory();
    
    // Test connection
    testConnection();
});

// Load OpenAPI specification
async function loadOpenApiSpec() {
    try {
        const response = await fetch('openapi.json');
        openApiSpec = await response.json();
        
        // Build endpoints list
        const endpointsList = document.getElementById('endpoints-list');
        endpointsList.innerHTML = uiBuilder.buildEndpointsList(openApiSpec);
        
        // Update statistics
        updateStatistics();
        
        // Setup endpoint click handlers
        setupEndpointHandlers();
        
        // Setup collapsible groups
        setupCollapsibles();
        
    } catch (error) {
        console.error('Failed to load OpenAPI spec:', error);
        document.getElementById('endpoints-list').innerHTML = `
            <div class="text-center py-8 text-red-500">
                Failed to load API specification
            </div>
        `;
    }
}

// Update statistics on welcome screen
function updateStatistics() {
    if (!openApiSpec) return;
    
    const paths = Object.keys(openApiSpec.paths || {});
    let totalEndpoints = 0;
    const tags = new Set();
    
    paths.forEach(path => {
        const pathData = openApiSpec.paths[path];
        Object.entries(pathData).forEach(([method, data]) => {
            if (typeof data === 'object') {
                totalEndpoints++;
                (data.tags || []).forEach(tag => tags.add(tag));
            }
        });
    });
    
    document.getElementById('total-endpoints').textContent = totalEndpoints;
    document.getElementById('total-tags').textContent = tags.size;
    document.getElementById('total-schemas').textContent = Object.keys(openApiSpec.components?.schemas || {}).length;
    document.getElementById('api-version').textContent = `v${openApiSpec.info?.version || '1.0.0'}`;
}

// Setup theme toggle
function setupTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.documentElement.classList.add('dark');
    }
    
    document.getElementById('theme-toggle').addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        const newTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
        localStorage.setItem('theme', newTheme);
    });
}

// Setup event listeners
function setupEventListeners() {
    // Base URL change
    document.getElementById('base-url').addEventListener('change', (e) => {
        apiClient.setBaseUrl(e.target.value);
        testConnection();
    });
    
    // Auth button
    document.getElementById('auth-btn').addEventListener('click', () => {
        const modal = document.getElementById('auth-modal');
        modal.classList.remove('hidden');
    });
    
    // Auth modal buttons
    document.getElementById('auth-cancel').addEventListener('click', () => {
        document.getElementById('auth-modal').classList.add('hidden');
    });
    
    document.getElementById('auth-token-toggle').addEventListener('click', () => {
        const tokenSection = document.getElementById('auth-token-section');
        tokenSection.classList.toggle('hidden');
        const btn = document.getElementById('auth-token-toggle');
        btn.textContent = tokenSection.classList.contains('hidden') ? 'Use Token' : 'Use Login';
    });
    
    document.getElementById('auth-submit').addEventListener('click', handleAuth);
    
    // Execute button
    document.getElementById('execute-btn').addEventListener('click', executeRequest);
    
    // Add header button
    document.getElementById('add-header').addEventListener('click', addHeaderInput);
    
    // Search endpoints
    document.getElementById('endpoint-search').addEventListener('input', (e) => {
        filterEndpoints(e.target.value);
    });
    
    // Clear history button
    document.getElementById('clear-history').addEventListener('click', clearRequestHistory);
    
    // Headers section toggle
    document.getElementById('headers-toggle').addEventListener('click', toggleHeadersSection);
}

// Setup endpoint click handlers
function setupEndpointHandlers() {
    document.querySelectorAll('.endpoint-item').forEach(item => {
        item.addEventListener('click', () => {
            selectEndpoint(item.dataset.path, item.dataset.method);
        });
    });
}

// Setup collapsible groups
function setupCollapsibles() {
    document.querySelectorAll('.collapsible').forEach(collapsible => {
        collapsible.addEventListener('click', () => {
            collapsible.classList.toggle('expanded');
            const group = document.querySelector(`[data-tag-group="${collapsible.dataset.tag}"]`);
            if (group) {
                group.style.display = collapsible.classList.contains('expanded') ? 'block' : 'none';
            }
        });
    });
}

// Select an endpoint
function selectEndpoint(path, method) {
    // Update active state
    document.querySelectorAll('.endpoint-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-path="${path}"][data-method="${method}"]`).classList.add('active');
    
    // Get endpoint data
    const endpointData = openApiSpec.paths[path][method.toLowerCase()];
    currentEndpoint = { path, method, data: endpointData };
    
    // Show testing panel
    document.getElementById('welcome-screen').classList.add('hidden');
    document.getElementById('testing-panel').classList.remove('hidden');
    
    // Update endpoint info
    updateEndpointInfo(path, method, endpointData);
    
    // Build parameter inputs
    buildParameterInputs(endpointData);
    
    // Build request body template
    buildRequestBodyTemplate(endpointData);
}

// Update endpoint information display
function updateEndpointInfo(path, method, data) {
    // Method badge
    const methodBadge = document.getElementById('method-badge');
    methodBadge.textContent = method;
    methodBadge.className = `px-3 py-1 text-xs font-bold rounded method-${method.toLowerCase()}`;
    
    // Path
    document.getElementById('endpoint-path').textContent = path;
    
    // Summary and description
    document.getElementById('endpoint-summary').textContent = data.summary || 'No summary';
    document.getElementById('endpoint-description').textContent = data.description || '';
    
    // Operation ID
    document.getElementById('operation-id').textContent = data.operationId || 'N/A';
}

// Build parameter inputs for current endpoint with validation
function buildParameterInputs(endpointData) {
    // Path parameters
    const pathParams = endpointData.parameters?.filter(p => p.in === 'path') || [];
    const pathSection = document.getElementById('path-params-section');
    const pathContainer = document.getElementById('path-params');
    
    if (pathParams.length > 0) {
        pathSection.classList.remove('hidden');
        pathContainer.innerHTML = uiBuilder.buildParameterInputs(pathParams, 'path');
        // Add real-time validation
        addValidationListeners(pathParams, 'path');
    } else {
        pathSection.classList.add('hidden');
    }
    
    // Query parameters
    const queryParams = endpointData.parameters?.filter(p => p.in === 'query') || [];
    const querySection = document.getElementById('query-params-section');
    const queryContainer = document.getElementById('query-params');
    
    if (queryParams.length > 0) {
        querySection.classList.remove('hidden');
        queryContainer.innerHTML = uiBuilder.buildParameterInputs(queryParams, 'query');
        // Add real-time validation
        addValidationListeners(queryParams, 'query');
    } else {
        querySection.classList.add('hidden');
    }
    
    // Show/hide body section based on method
    const bodySection = document.getElementById('body-section');
    if (['POST', 'PUT', 'PATCH'].includes(currentEndpoint.method)) {
        bodySection.classList.remove('hidden');
        // Add JSON validation for body
        addBodyValidation();
    } else {
        bodySection.classList.add('hidden');
    }
}

// Add validation listeners to parameter inputs
function addValidationListeners(parameters, type) {
    if (!window.formBuilder) return;
    
    parameters.forEach(param => {
        const inputId = `${type}-${param.name}`;
        const input = document.getElementById(inputId);
        
        if (input) {
            // Add validation on blur
            input.addEventListener('blur', () => {
                const value = input.type === 'checkbox' ? input.checked : input.value;
                const validation = window.formBuilder.validateField(inputId, value);
                
                if (!validation.valid) {
                    window.formBuilder.showFieldError(input, validation.errors[0]);
                } else {
                    window.formBuilder.clearFieldError(input);
                }
            });
            
            // Clear error on focus
            input.addEventListener('focus', () => {
                window.formBuilder.clearFieldError(input);
            });
        }
    });
}

// Add JSON validation for request body
function addBodyValidation() {
    const bodyInput = document.getElementById('request-body');
    if (!bodyInput) return;
    
    let validationTimeout;
    
    bodyInput.addEventListener('input', () => {
        clearTimeout(validationTimeout);
        validationTimeout = setTimeout(() => {
            try {
                if (bodyInput.value.trim()) {
                    JSON.parse(bodyInput.value);
                    bodyInput.classList.remove('border-red-500');
                    bodyInput.classList.add('border-green-500');
                }
            } catch (e) {
                bodyInput.classList.remove('border-green-500');
                bodyInput.classList.add('border-red-500');
                
                // Show error message
                let errorDiv = bodyInput.parentElement.querySelector('.json-error');
                if (!errorDiv) {
                    errorDiv = document.createElement('div');
                    errorDiv.className = 'json-error text-xs text-red-500 mt-1';
                    bodyInput.parentElement.appendChild(errorDiv);
                }
                errorDiv.textContent = `JSON Error: ${e.message}`;
            }
        }, 500);
    });
    
    // Clear validation on focus
    bodyInput.addEventListener('focus', () => {
        bodyInput.classList.remove('border-red-500', 'border-green-500');
        const errorDiv = bodyInput.parentElement.querySelector('.json-error');
        if (errorDiv) errorDiv.remove();
    });
}

// Build request body template with enhanced form option
function buildRequestBodyTemplate(endpointData) {
    if (!endpointData.requestBody) return;
    
    const bodySection = document.getElementById('body-section');
    if (!bodySection) return;
    
    // Check if we should use form builder for complex schemas
    const content = endpointData.requestBody.content?.['application/json'];
    const schema = content?.schema;
    
    if (schema && window.formBuilder) {
        // Determine button states based on preferred view
        const formButtonClass = preferredBodyView === 'form' 
            ? 'px-2 py-1 text-xs bg-blue-500 text-white rounded' 
            : 'px-2 py-1 text-xs bg-gray-300 text-gray-700 rounded';
        const jsonButtonClass = preferredBodyView === 'json' 
            ? 'px-2 py-1 text-xs bg-blue-500 text-white rounded' 
            : 'px-2 py-1 text-xs bg-gray-300 text-gray-700 rounded';
        const formViewHidden = preferredBodyView === 'json' ? 'hidden' : '';
        const jsonViewHidden = preferredBodyView === 'form' ? 'hidden' : '';
        
        // Add toggle for form vs JSON view
        const toggleHtml = `
            <div class="flex items-center justify-between mb-2">
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">Request Body</h4>
                <div class="flex items-center space-x-2">
                    <button type="button" id="body-view-form" class="${formButtonClass}">Form</button>
                    <button type="button" id="body-view-json" class="${jsonButtonClass}">JSON</button>
                </div>
            </div>
        `;
        
        // Build form view
        const formHtml = window.formBuilder.buildRequestBodySection(endpointData.requestBody, openApiSpec.components?.schemas || {});
        
        // Update body section
        bodySection.innerHTML = `
            ${toggleHtml}
            <div id="body-form-view" class="${formViewHidden}">
                ${formHtml}
            </div>
            <div id="body-json-view" class="${jsonViewHidden}">
                <textarea id="request-body" rows="10" class="w-full px-3 py-2 text-sm font-mono border rounded text-gray-900 dark:bg-gray-700 dark:border-gray-600 dark:text-white"></textarea>
            </div>
        `;
        
        // Add toggle listeners
        document.getElementById('body-view-form')?.addEventListener('click', () => {
            preferredBodyView = 'form'; // Save preference
            localStorage.setItem('preferredBodyView', 'form'); // Persist preference
            document.getElementById('body-form-view').classList.remove('hidden');
            document.getElementById('body-json-view').classList.add('hidden');
            document.getElementById('body-view-form').classList.add('bg-blue-500', 'text-white');
            document.getElementById('body-view-form').classList.remove('bg-gray-300', 'text-gray-700');
            document.getElementById('body-view-json').classList.remove('bg-blue-500', 'text-white');
            document.getElementById('body-view-json').classList.add('bg-gray-300', 'text-gray-700');
        });
        
        document.getElementById('body-view-json')?.addEventListener('click', () => {
            preferredBodyView = 'json'; // Save preference
            localStorage.setItem('preferredBodyView', 'json'); // Persist preference
            // Convert form data to JSON
            const formData = window.formBuilder.getFormData('body-form');
            if (Object.keys(formData).length > 0) {
                document.getElementById('request-body').value = JSON.stringify(formData, null, 2);
            }
            
            document.getElementById('body-form-view').classList.add('hidden');
            document.getElementById('body-json-view').classList.remove('hidden');
            document.getElementById('body-view-json').classList.add('bg-blue-500', 'text-white');
            document.getElementById('body-view-json').classList.remove('bg-gray-300', 'text-gray-700');
            document.getElementById('body-view-form').classList.remove('bg-blue-500', 'text-white');
            document.getElementById('body-view-form').classList.add('bg-gray-300', 'text-gray-700');
        });
    }
    
    // Build template
    const template = uiBuilder.buildRequestBodyTemplate(
        endpointData.requestBody,
        openApiSpec.components?.schemas || {}
    );
    
    if (template) {
        const bodyTextarea = document.getElementById('request-body');
        if (bodyTextarea) {
            bodyTextarea.value = JSON.stringify(template, null, 2);
        }
    }
}

// Execute the current request with validation
async function executeRequest() {
    if (!currentEndpoint) return;
    
    // Validate form if using form builder
    if (window.formBuilder) {
        const pathParams = currentEndpoint.data.parameters?.filter(p => p.in === 'path') || [];
        const queryParams = currentEndpoint.data.parameters?.filter(p => p.in === 'query') || [];
        
        // Validate all parameters
        let hasErrors = false;
        [...pathParams, ...queryParams].forEach(param => {
            const inputId = `${param.in}-${param.name}`;
            const input = document.getElementById(inputId);
            if (input && param.required) {
                const value = input.type === 'checkbox' ? input.checked : input.value;
                if (!value || value === '') {
                    window.formBuilder.showFieldError(input, 'This field is required');
                    hasErrors = true;
                }
            }
        });
        
        if (hasErrors) {
            alert('Please fix validation errors before executing');
            return;
        }
    }
    
    const btn = document.getElementById('execute-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Executing...';
    
    try {
        // Gather parameters
        const pathParams = uiBuilder.getParameterValues(
            currentEndpoint.data.parameters?.filter(p => p.in === 'path'),
            'path'
        );
        
        const queryParams = uiBuilder.getParameterValues(
            currentEndpoint.data.parameters?.filter(p => p.in === 'query'),
            'query'
        );
        
        // Get headers
        const headers = {};
        document.querySelectorAll('#headers .flex').forEach(row => {
            const inputs = row.querySelectorAll('input');
            if (inputs[0]?.value && inputs[1]?.value) {
                headers[inputs[0].value] = inputs[1].value;
            }
        });
        
        // Get body
        let body = null;
        if (['POST', 'PUT', 'PATCH'].includes(currentEndpoint.method)) {
            // Check if form view is active
            const formView = document.getElementById('body-form-view');
            if (formView && !formView.classList.contains('hidden')) {
                // Get data from form
                body = window.formBuilder.getFormData('body-form');
            } else {
                // Get data from JSON textarea
                const bodyText = document.getElementById('request-body')?.value;
                if (bodyText) {
                    try {
                        body = JSON.parse(bodyText);
                    } catch (e) {
                        alert('Invalid JSON in request body');
                        throw e;
                    }
                }
            }
        }
        
        // Make request
        const response = await apiClient.makeRequest(
            currentEndpoint.method,
            currentEndpoint.path,
            { pathParams, queryParams, headers, body }
        );
        
        // Display response
        displayResponse(response);
        
    } catch (error) {
        displayError(error);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Execute';
        loadRequestHistory();
    }
}

// Display response
function displayResponse(response) {
    // Show response section
    document.getElementById('response-status').classList.remove('hidden');
    document.getElementById('response-placeholder').classList.add('hidden');
    document.getElementById('response-body').classList.remove('hidden');
    
    // Update status
    const statusCode = document.getElementById('status-code');
    statusCode.textContent = `${response.status} ${response.statusText}`;
    statusCode.className = `font-bold ${uiBuilder.getStatusClass(response.status)}`;
    
    // Update response time
    document.getElementById('response-time').textContent = `${response.responseTime}ms`;
    
    // Update response body
    const responseBody = document.querySelector('#response-body code');
    const formattedData = typeof response.data === 'string' 
        ? response.data 
        : JSON.stringify(response.data, null, 2);
    
    responseBody.textContent = formattedData;
    Prism.highlightElement(responseBody);
}

// Display error
function displayError(error) {
    document.getElementById('response-status').classList.remove('hidden');
    document.getElementById('response-placeholder').classList.add('hidden');
    document.getElementById('response-body').classList.remove('hidden');
    
    const statusCode = document.getElementById('status-code');
    statusCode.textContent = 'Error';
    statusCode.className = 'font-bold status-client-error';
    
    const responseBody = document.querySelector('#response-body code');
    responseBody.textContent = JSON.stringify({ error: error.message }, null, 2);
    Prism.highlightElement(responseBody);
}

// Handle authentication
async function handleAuth() {
    const tokenSection = document.getElementById('auth-token-section');
    
    if (!tokenSection.classList.contains('hidden')) {
        // Use token directly
        const token = document.getElementById('auth-token').value;
        if (token) {
            apiClient.setToken(token);
            document.getElementById('auth-modal').classList.add('hidden');
            await updateAuthStatus();  // Wait for status update
        }
    } else {
        // Login with username/password
        const username = document.getElementById('auth-username').value;
        const password = document.getElementById('auth-password').value;
        
        try {
            await apiClient.login(username, password);
            document.getElementById('auth-modal').classList.add('hidden');
            await updateAuthStatus();  // Wait for status update
            
            // Clear form
            document.getElementById('auth-username').value = '';
            document.getElementById('auth-password').value = '';
        } catch (error) {
            alert(`Login failed: ${error.message}`);
        }
    }
}

// Update auth status display
async function updateAuthStatus() {
    const indicator = document.getElementById('auth-indicator');
    const text = document.getElementById('auth-text');
    const btn = document.getElementById('auth-btn');
    
    console.log('updateAuthStatus: Token exists?', !!apiClient.getToken());
    
    if (apiClient.getToken()) {
        console.log('updateAuthStatus: Validating token...');
        const validation = await apiClient.validateToken();
        console.log('updateAuthStatus: Validation result:', validation);
        
        if (validation.valid) {
            console.log('updateAuthStatus: Token is valid, showing authenticated state');
            indicator.className = 'w-2 h-2 bg-green-500 rounded-full auth-authenticated';
            text.textContent = 'Authenticated';
            btn.textContent = 'Logout';
            btn.onclick = () => {
                apiClient.setToken(null);
                updateAuthStatus();
            };
        } else {
            console.log('updateAuthStatus: Token validation failed, reason:', validation.reason);
            // Handle different failure reasons
            if (validation.reason === 'api-offline') {
                // API is offline - keep token but show offline status
                indicator.className = 'w-2 h-2 bg-yellow-500 rounded-full';
                text.textContent = 'API Offline';
                btn.textContent = 'Retry';
                btn.onclick = () => {
                    updateAuthStatus();
                    testConnection();
                };
            } else if (validation.reason === 'invalid-token') {
                // Token is actually invalid
                apiClient.setToken(null);
                indicator.className = 'w-2 h-2 bg-red-500 rounded-full';
                text.textContent = 'Token invalid';
                btn.textContent = 'Login';
                btn.onclick = () => {
                    document.getElementById('auth-modal').classList.remove('hidden');
                };
            } else {
                // Some other error
                console.error('updateAuthStatus: Unknown validation failure reason:', validation);
                indicator.className = 'w-2 h-2 bg-red-500 rounded-full';
                text.textContent = 'Auth error';
                btn.textContent = 'Login';
                btn.onclick = () => {
                    document.getElementById('auth-modal').classList.remove('hidden');
                };
            }
        }
    } else {
        console.log('updateAuthStatus: No token, showing not authenticated state');
        indicator.className = 'w-2 h-2 bg-red-500 rounded-full';
        text.textContent = 'Not authenticated';
        btn.textContent = 'Login';
        btn.onclick = () => {
            document.getElementById('auth-modal').classList.remove('hidden');
        };
    }
}

// Update base URL from saved value
function updateBaseUrl() {
    const savedUrl = localStorage.getItem('baseUrl');
    // If the saved URL is the old default, update it to the new one
    if (savedUrl === 'http://localhost:8000') {
        localStorage.setItem('baseUrl', 'http://localhost:8010');
        document.getElementById('base-url').value = 'http://localhost:8010';
        apiClient.setBaseUrl('http://localhost:8010');
    } else if (savedUrl) {
        document.getElementById('base-url').value = savedUrl;
    }
    // If no saved URL, the HTML default (8010) will be used
}

// Test connection to server
async function testConnection() {
    const isConnected = await apiClient.testConnection();
    const baseUrlInput = document.getElementById('base-url');
    
    if (isConnected) {
        baseUrlInput.classList.remove('border-red-500');
        baseUrlInput.classList.add('border-green-500');
    } else {
        baseUrlInput.classList.remove('border-green-500');
        baseUrlInput.classList.add('border-red-500');
    }
}

// Add header input row
function addHeaderInput() {
    const container = document.getElementById('headers');
    const newRow = document.createElement('div');
    newRow.className = 'flex space-x-2';
    newRow.innerHTML = `
        <input type="text" placeholder="Header name" class="flex-1 px-3 py-1 text-sm border rounded text-gray-900 dark:bg-gray-700 dark:border-gray-600 dark:text-white header-input">
        <input type="text" placeholder="Header value" class="flex-1 px-3 py-1 text-sm border rounded text-gray-900 dark:bg-gray-700 dark:border-gray-600 dark:text-white header-input">
        <button onclick="this.parentElement.remove(); updateHeaderCount();" class="px-2 py-1 text-sm text-red-500 hover:text-red-700">×</button>
    `;
    container.appendChild(newRow);
    
    // Add change listeners to update count
    newRow.querySelectorAll('.header-input').forEach(input => {
        input.addEventListener('input', updateHeaderCount);
    });
    
    updateHeaderCount();
}

// Toggle headers section visibility
function toggleHeadersSection() {
    const content = document.getElementById('headers-content');
    const arrow = document.getElementById('headers-arrow');
    
    if (content.classList.contains('hidden')) {
        content.classList.remove('hidden');
        arrow.classList.add('rotate-90');
    } else {
        content.classList.add('hidden');
        arrow.classList.remove('rotate-90');
    }
}

// Update header count
function updateHeaderCount() {
    const headers = document.querySelectorAll('#headers .flex');
    let count = 0;
    
    headers.forEach(row => {
        const inputs = row.querySelectorAll('input');
        if (inputs[0]?.value && inputs[1]?.value) {
            count++;
        }
    });
    
    document.getElementById('headers-count').textContent = `(${count})`;
}

// Filter endpoints based on search
function filterEndpoints(searchTerm) {
    const term = searchTerm.toLowerCase();
    
    document.querySelectorAll('.endpoint-item').forEach(item => {
        const path = item.dataset.path.toLowerCase();
        const method = item.dataset.method.toLowerCase();
        const summary = item.querySelector('.text-xs')?.textContent.toLowerCase() || '';
        
        if (path.includes(term) || method.includes(term) || summary.includes(term)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// Load request history
function loadRequestHistory() {
    const history = apiClient.getHistory();
    const container = document.getElementById('history-list');
    
    if (history.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4 text-gray-500 dark:text-gray-400">
                No requests yet
            </div>
        `;
    } else {
        container.innerHTML = history.slice(0, 10)
            .map(entry => uiBuilder.buildHistoryItem(entry))
            .join('');
    }
}

// Clear request history
function clearRequestHistory() {
    if (confirm('Are you sure you want to clear all request history?')) {
        apiClient.clearHistory();
        loadRequestHistory();
        
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