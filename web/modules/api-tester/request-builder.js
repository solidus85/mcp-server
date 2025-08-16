// Request builder module - handles request construction, validation, and execution

class RequestBuilder {
    constructor(apiClient, uiBuilder, endpointsManager) {
        this.apiClient = apiClient;
        this.uiBuilder = uiBuilder;
        this.endpointsManager = endpointsManager;
        this.preferredBodyView = localStorage.getItem('preferredBodyView') || 'json';
    }

    // Initialize request builder
    init() {
        // Listen for endpoint selection
        window.addEventListener('endpointSelected', (event) => {
            this.buildParameterInputs(event.detail.data);
            this.buildRequestBodyTemplate(event.detail.data);
        });

        // Setup execute button
        document.getElementById('execute-btn').addEventListener('click', () => this.executeRequest());
        
        // Setup headers functionality
        this.setupHeaders();
    }

    // Build parameter inputs for current endpoint with validation
    buildParameterInputs(endpointData) {
        // Path parameters
        const pathParams = endpointData.parameters?.filter(p => p.in === 'path') || [];
        const pathSection = document.getElementById('path-params-section');
        const pathContainer = document.getElementById('path-params');
        
        if (pathParams.length > 0) {
            pathSection.classList.remove('hidden');
            pathContainer.innerHTML = this.uiBuilder.buildParameterInputs(pathParams, 'path');
            this.addValidationListeners(pathParams, 'path');
        } else {
            pathSection.classList.add('hidden');
        }
        
        // Query parameters
        const queryParams = endpointData.parameters?.filter(p => p.in === 'query') || [];
        const querySection = document.getElementById('query-params-section');
        const queryContainer = document.getElementById('query-params');
        
        if (queryParams.length > 0) {
            querySection.classList.remove('hidden');
            queryContainer.innerHTML = this.uiBuilder.buildParameterInputs(queryParams, 'query');
            this.addValidationListeners(queryParams, 'query');
        } else {
            querySection.classList.add('hidden');
        }
        
        // Show/hide body section based on method
        const currentEndpoint = this.endpointsManager.getCurrentEndpoint();
        const bodySection = document.getElementById('body-section');
        if (['POST', 'PUT', 'PATCH'].includes(currentEndpoint.method)) {
            bodySection.classList.remove('hidden');
            this.addBodyValidation();
        } else {
            bodySection.classList.add('hidden');
        }
    }

    // Add validation listeners to parameter inputs
    addValidationListeners(parameters, type) {
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
    addBodyValidation() {
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
    buildRequestBodyTemplate(endpointData) {
        if (!endpointData.requestBody) return;
        
        const bodySection = document.getElementById('body-section');
        if (!bodySection) return;
        
        // Check if we should use form builder for complex schemas
        const content = endpointData.requestBody.content?.['application/json'];
        const schema = content?.schema;
        const openApiSpec = this.endpointsManager.getSpec();
        
        if (schema && window.formBuilder) {
            // Determine button states based on preferred view
            const formButtonClass = this.preferredBodyView === 'form' 
                ? 'px-2 py-1 text-xs bg-blue-500 text-white rounded' 
                : 'px-2 py-1 text-xs bg-gray-300 text-gray-700 rounded';
            const jsonButtonClass = this.preferredBodyView === 'json' 
                ? 'px-2 py-1 text-xs bg-blue-500 text-white rounded' 
                : 'px-2 py-1 text-xs bg-gray-300 text-gray-700 rounded';
            const formViewHidden = this.preferredBodyView === 'json' ? 'hidden' : '';
            const jsonViewHidden = this.preferredBodyView === 'form' ? 'hidden' : '';
            
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
            this.setupBodyViewToggle();
        }
        
        // Build template
        const template = this.uiBuilder.buildRequestBodyTemplate(
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

    // Setup body view toggle
    setupBodyViewToggle() {
        document.getElementById('body-view-form')?.addEventListener('click', () => {
            this.preferredBodyView = 'form';
            localStorage.setItem('preferredBodyView', 'form');
            document.getElementById('body-form-view').classList.remove('hidden');
            document.getElementById('body-json-view').classList.add('hidden');
            document.getElementById('body-view-form').classList.add('bg-blue-500', 'text-white');
            document.getElementById('body-view-form').classList.remove('bg-gray-300', 'text-gray-700');
            document.getElementById('body-view-json').classList.remove('bg-blue-500', 'text-white');
            document.getElementById('body-view-json').classList.add('bg-gray-300', 'text-gray-700');
        });
        
        document.getElementById('body-view-json')?.addEventListener('click', () => {
            this.preferredBodyView = 'json';
            localStorage.setItem('preferredBodyView', 'json');
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

    // Execute the current request with validation
    async executeRequest() {
        const currentEndpoint = this.endpointsManager.getCurrentEndpoint();
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
            const pathParams = this.uiBuilder.getParameterValues(
                currentEndpoint.data.parameters?.filter(p => p.in === 'path'),
                'path'
            );
            
            const queryParams = this.uiBuilder.getParameterValues(
                currentEndpoint.data.parameters?.filter(p => p.in === 'query'),
                'query'
            );
            
            // Get headers
            const headers = this.getHeaders();
            
            // Get body
            let body = null;
            if (['POST', 'PUT', 'PATCH'].includes(currentEndpoint.method)) {
                body = this.getRequestBody();
            }
            
            // Make request
            const response = await this.apiClient.makeRequest(
                currentEndpoint.method,
                currentEndpoint.path,
                { pathParams, queryParams, headers, body }
            );
            
            // Trigger response event
            const event = new CustomEvent('requestCompleted', { detail: response });
            window.dispatchEvent(event);
            
        } catch (error) {
            // Trigger error event
            const event = new CustomEvent('requestError', { detail: error });
            window.dispatchEvent(event);
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Execute';
            // Trigger history reload
            window.dispatchEvent(new CustomEvent('reloadHistory'));
        }
    }

    // Get headers from UI
    getHeaders() {
        const headers = {};
        document.querySelectorAll('#headers .flex').forEach(row => {
            const inputs = row.querySelectorAll('input');
            if (inputs[0]?.value && inputs[1]?.value) {
                headers[inputs[0].value] = inputs[1].value;
            }
        });
        return headers;
    }

    // Get request body
    getRequestBody() {
        // Check if form view is active
        const formView = document.getElementById('body-form-view');
        if (formView && !formView.classList.contains('hidden')) {
            // Get data from form
            return window.formBuilder.getFormData('body-form');
        } else {
            // Get data from JSON textarea
            const bodyText = document.getElementById('request-body')?.value;
            if (bodyText) {
                try {
                    return JSON.parse(bodyText);
                } catch (e) {
                    alert('Invalid JSON in request body');
                    throw e;
                }
            }
        }
        return null;
    }

    // Setup headers functionality
    setupHeaders() {
        document.getElementById('add-header').addEventListener('click', () => this.addHeaderInput());
        document.getElementById('headers-toggle').addEventListener('click', () => this.toggleHeadersSection());
    }

    // Add header input row
    addHeaderInput() {
        const container = document.getElementById('headers');
        const newRow = document.createElement('div');
        newRow.className = 'flex space-x-2';
        newRow.innerHTML = `
            <input type="text" placeholder="Header name" class="flex-1 px-3 py-1 text-sm border rounded text-gray-900 dark:bg-gray-700 dark:border-gray-600 dark:text-white header-input">
            <input type="text" placeholder="Header value" class="flex-1 px-3 py-1 text-sm border rounded text-gray-900 dark:bg-gray-700 dark:border-gray-600 dark:text-white header-input">
            <button onclick="this.parentElement.remove(); window.requestBuilder.updateHeaderCount();" class="px-2 py-1 text-sm text-red-500 hover:text-red-700">×</button>
        `;
        container.appendChild(newRow);
        
        // Add change listeners to update count
        newRow.querySelectorAll('.header-input').forEach(input => {
            input.addEventListener('input', () => this.updateHeaderCount());
        });
        
        this.updateHeaderCount();
    }

    // Toggle headers section visibility
    toggleHeadersSection() {
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
    updateHeaderCount() {
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
}