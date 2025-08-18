// Endpoints module - handles endpoint selection, display, and filtering

class EndpointsManager {
    constructor(uiBuilder) {
        this.uiBuilder = uiBuilder;
        this.openApiSpec = null;
        this.currentEndpoint = null;
    }

    // Load OpenAPI specification
    async loadOpenApiSpec() {
        try {
            const response = await fetch('/modules/api-tester/openapi.json');
            this.openApiSpec = await response.json();
            
            // Build endpoints list
            const endpointsList = document.getElementById('endpoints-list');
            if (endpointsList) {
                endpointsList.innerHTML = this.uiBuilder.buildEndpointsList(this.openApiSpec);
            }
            
            // Update statistics
            this.updateStatistics();
            
            // Setup endpoint click handlers
            this.setupEndpointHandlers();
            
            // Setup collapsible groups
            this.setupCollapsibles();
            
            return this.openApiSpec;
            
        } catch (error) {
            console.error('Failed to load OpenAPI spec:', error);
            const endpointsList = document.getElementById('endpoints-list');
            if (endpointsList) {
                endpointsList.innerHTML = `
                    <div class="text-center py-8 text-red-500">
                        Failed to load API specification
                    </div>
                `;
            }
            throw error;
        }
    }

    // Update statistics on welcome screen
    updateStatistics() {
        if (!this.openApiSpec) return;
        
        const paths = Object.keys(this.openApiSpec.paths || {});
        let totalEndpoints = 0;
        const tags = new Set();
        
        paths.forEach(path => {
            const pathData = this.openApiSpec.paths[path];
            Object.entries(pathData).forEach(([method, data]) => {
                if (typeof data === 'object') {
                    totalEndpoints++;
                    (data.tags || []).forEach(tag => tags.add(tag));
                }
            });
        });
        
        document.getElementById('total-endpoints').textContent = totalEndpoints;
        document.getElementById('total-tags').textContent = tags.size;
        document.getElementById('total-schemas').textContent = Object.keys(this.openApiSpec.components?.schemas || {}).length;
        document.getElementById('api-version').textContent = `v${this.openApiSpec.info?.version || '1.0.0'}`;
    }

    // Setup endpoint click handlers
    setupEndpointHandlers() {
        document.querySelectorAll('.endpoint-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectEndpoint(item.dataset.path, item.dataset.method);
            });
        });
    }

    // Setup collapsible groups
    setupCollapsibles() {
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
    selectEndpoint(path, method) {
        if (!path || !method) {
            console.error('Path and method are required');
            return null;
        }
        
        if (!this.openApiSpec || !this.openApiSpec.paths || !this.openApiSpec.paths[path]) {
            console.error('Invalid path:', path);
            return null;
        }
        
        // Update active state
        document.querySelectorAll('.endpoint-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = document.querySelector(`[data-path="${path}"][data-method="${method}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
        
        // Get endpoint data
        const endpointData = this.openApiSpec.paths[path][method.toLowerCase()];
        if (!endpointData) {
            console.error('Endpoint data not found for:', path, method);
            return null;
        }
        
        this.currentEndpoint = { path, method, data: endpointData };
        
        // Show testing panel
        const welcomeScreen = document.getElementById('welcome-screen');
        const testingPanel = document.getElementById('testing-panel');
        
        if (welcomeScreen) welcomeScreen.classList.add('hidden');
        if (testingPanel) testingPanel.classList.remove('hidden');
        
        // Update endpoint info
        this.updateEndpointInfo(path, method, endpointData);
        
        // Trigger event for other modules
        const event = new CustomEvent('endpointSelected', { 
            detail: this.currentEndpoint 
        });
        window.dispatchEvent(event);
        
        return this.currentEndpoint;
    }

    // Update endpoint information display
    updateEndpointInfo(path, method, data) {
        if (!path || !method || !data) {
            console.error('Invalid endpoint info');
            return;
        }
        
        // Method badge
        const methodBadge = document.getElementById('method-badge');
        if (methodBadge) {
            methodBadge.textContent = method;
            methodBadge.className = `px-3 py-1 text-xs font-bold rounded method-${method.toLowerCase()}`;
        }
        
        // Path
        const endpointPath = document.getElementById('endpoint-path');
        if (endpointPath) {
            endpointPath.textContent = path;
        }
        
        // Summary and description
        const endpointSummary = document.getElementById('endpoint-summary');
        if (endpointSummary) {
            endpointSummary.textContent = data.summary || 'No summary';
        }
        
        const endpointDescription = document.getElementById('endpoint-description');
        if (endpointDescription) {
            endpointDescription.textContent = data.description || '';
        }
        
        // Operation ID
        const operationId = document.getElementById('operation-id');
        if (operationId) {
            operationId.textContent = data.operationId || 'N/A';
        }
    }

    // Setup search functionality
    setupSearch() {
        const searchInput = document.getElementById('endpoint-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterEndpoints(e.target.value);
            });
        }
    }

    // Filter endpoints based on search
    filterEndpoints(searchTerm) {
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

    // Get current endpoint
    getCurrentEndpoint() {
        return this.currentEndpoint;
    }

    // Get OpenAPI spec
    getSpec() {
        return this.openApiSpec;
    }
}

// Export for use in other scripts
window.EndpointsManager = EndpointsManager;