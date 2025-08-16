// UI Endpoint Builder - handles endpoint list and grouping

class UIEndpointBuilder {
    constructor() {}

    // Build sidebar with grouped endpoints
    buildEndpointsList(openApiSpec) {
        const paths = openApiSpec.paths || {};
        const grouped = this.groupEndpointsByTag(paths);
        
        // Build HTML
        let html = '';
        Object.entries(grouped).sort().forEach(([tag, endpoints]) => {
            html += this.buildTagGroup(tag, endpoints);
        });
        
        return html;
    }

    // Group endpoints by tag
    groupEndpointsByTag(paths) {
        const grouped = {};
        
        Object.entries(paths).forEach(([path, pathData]) => {
            Object.entries(pathData).forEach(([method, endpointData]) => {
                if (typeof endpointData === 'object') {
                    const tags = endpointData.tags || ['Other'];
                    tags.forEach(tag => {
                        if (!grouped[tag]) {
                            grouped[tag] = [];
                        }
                        grouped[tag].push({
                            path,
                            method: method.toUpperCase(),
                            data: endpointData
                        });
                    });
                }
            });
        });
        
        return grouped;
    }

    // Build HTML for a tag group
    buildTagGroup(tag, endpoints) {
        let html = `
            <div class="mb-4">
                <div class="collapsible expanded font-semibold text-gray-900 dark:text-white mb-2 cursor-pointer" data-tag="${tag}">
                    ${tag} (${endpoints.length})
                </div>
                <div class="endpoints-group pl-4 space-y-1" data-tag-group="${tag}">
        `;
        
        endpoints.sort((a, b) => a.path.localeCompare(b.path)).forEach(endpoint => {
            html += this.buildEndpointItem(endpoint);
        });
        
        html += `
                </div>
            </div>
        `;
        
        return html;
    }

    // Build HTML for a single endpoint item
    buildEndpointItem(endpoint) {
        const methodClass = `method-${endpoint.method.toLowerCase()}`;
        return `
            <div class="endpoint-item p-2 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700" 
                 data-path="${endpoint.path}" 
                 data-method="${endpoint.method}">
                <div class="flex items-center space-x-2">
                    <span class="px-2 py-0.5 text-xs font-bold rounded ${methodClass}">
                        ${endpoint.method}
                    </span>
                    <span class="text-sm text-gray-700 dark:text-gray-300 truncate">
                        ${this.formatPath(endpoint.path)}
                    </span>
                </div>
                ${endpoint.data.summary ? `
                    <div class="text-xs text-gray-500 dark:text-gray-400 mt-1 pl-12 truncate">
                        ${endpoint.data.summary}
                    </div>
                ` : ''}
            </div>
        `;
    }

    // Format path for display
    formatPath(path) {
        return path.replace('/api/v1', '').replace(/{([^}]+)}/g, ':$1');
    }
}

// Export for use in other scripts
window.UIEndpointBuilder = UIEndpointBuilder;