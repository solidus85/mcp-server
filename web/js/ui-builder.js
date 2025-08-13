// UI Builder for dynamic form generation

class UIBuilder {
    constructor() {
        this.currentEndpoint = null;
    }

    // Build sidebar with grouped endpoints
    buildEndpointsList(openApiSpec) {
        const paths = openApiSpec.paths || {};
        const grouped = {};
        
        // Group endpoints by tag
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
        
        // Build HTML
        let html = '';
        Object.entries(grouped).sort().forEach(([tag, endpoints]) => {
            html += `
                <div class="mb-4">
                    <div class="collapsible expanded font-semibold text-gray-900 dark:text-white mb-2 cursor-pointer" data-tag="${tag}">
                        ${tag} (${endpoints.length})
                    </div>
                    <div class="endpoints-group pl-4 space-y-1" data-tag-group="${tag}">
            `;
            
            endpoints.sort((a, b) => a.path.localeCompare(b.path)).forEach(endpoint => {
                const methodClass = `method-${endpoint.method.toLowerCase()}`;
                html += `
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
            });
            
            html += `
                    </div>
                </div>
            `;
        });
        
        return html;
    }

    // Format path for display
    formatPath(path) {
        return path.replace('/api/v1', '').replace(/{([^}]+)}/g, ':$1');
    }

    // Build parameter inputs
    buildParameterInputs(parameters, type) {
        if (!parameters || parameters.length === 0) {
            return '';
        }
        
        let html = '';
        parameters.forEach(param => {
            const required = param.required ? '<span class="text-red-500">*</span>' : '';
            const inputId = `${type}-${param.name}`;
            const schema = param.schema || {};
            
            html += `
                <div class="parameter-input">
                    <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        ${param.name} ${required}
                        ${param.description ? `
                            <span class="text-gray-500 dark:text-gray-400 font-normal">
                                - ${param.description}
                            </span>
                        ` : ''}
                    </label>
            `;
            
            // Build appropriate input based on type
            if (schema.enum) {
                // Dropdown for enum values
                html += `
                    <select id="${inputId}" class="w-full px-3 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                        <option value="">-- Select --</option>
                        ${schema.enum.map(val => `<option value="${val}">${val}</option>`).join('')}
                    </select>
                `;
            } else if (schema.type === 'boolean') {
                // Checkbox for boolean
                html += `
                    <input type="checkbox" id="${inputId}" class="checkbox">
                `;
            } else if (schema.type === 'integer' || schema.type === 'number') {
                // Number input
                html += `
                    <input type="number" id="${inputId}" 
                           placeholder="${schema.example || ''}"
                           ${schema.minimum ? `min="${schema.minimum}"` : ''}
                           ${schema.maximum ? `max="${schema.maximum}"` : ''}
                           class="w-full px-3 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                `;
            } else {
                // Text input (default)
                html += `
                    <input type="text" id="${inputId}" 
                           placeholder="${schema.example || param.example || ''}"
                           class="w-full px-3 py-1 text-sm border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white">
                `;
            }
            
            html += '</div>';
        });
        
        return html;
    }

    // Build request body template
    buildRequestBodyTemplate(requestBody, schemas) {
        if (!requestBody || !requestBody.content || !requestBody.content['application/json']) {
            return null;
        }
        
        const schema = requestBody.content['application/json'].schema;
        if (!schema) return null;
        
        // Resolve schema reference if needed
        let resolvedSchema = schema;
        if (schema.$ref) {
            const schemaName = schema.$ref.split('/').pop();
            resolvedSchema = schemas[schemaName] || {};
        }
        
        // Build example object
        return this.buildExampleFromSchema(resolvedSchema, schemas);
    }

    // Build example object from schema
    buildExampleFromSchema(schema, schemas, depth = 0) {
        if (depth > 5) return {}; // Prevent infinite recursion
        
        if (schema.$ref) {
            const schemaName = schema.$ref.split('/').pop();
            return this.buildExampleFromSchema(schemas[schemaName] || {}, schemas, depth + 1);
        }
        
        if (schema.type === 'object' || schema.properties) {
            const obj = {};
            const properties = schema.properties || {};
            const required = schema.required || [];
            
            Object.entries(properties).forEach(([key, prop]) => {
                if (required.includes(key) || depth === 0) {
                    obj[key] = this.getExampleValue(prop, schemas, depth + 1);
                }
            });
            
            return obj;
        }
        
        if (schema.type === 'array') {
            const itemExample = this.getExampleValue(schema.items || {}, schemas, depth + 1);
            return [itemExample];
        }
        
        return this.getExampleValue(schema, schemas, depth);
    }

    // Get example value for a schema property
    getExampleValue(prop, schemas, depth = 0) {
        if (prop.example !== undefined) return prop.example;
        if (prop.default !== undefined) return prop.default;
        
        if (prop.$ref) {
            const schemaName = prop.$ref.split('/').pop();
            return this.buildExampleFromSchema(schemas[schemaName] || {}, schemas, depth);
        }
        
        if (prop.type === 'string') {
            if (prop.format === 'date-time') return new Date().toISOString();
            if (prop.format === 'date') return new Date().toISOString().split('T')[0];
            if (prop.format === 'email') return 'user@example.com';
            if (prop.format === 'uuid') return '00000000-0000-0000-0000-000000000000';
            if (prop.enum) return prop.enum[0];
            return 'string';
        }
        
        if (prop.type === 'integer') return 0;
        if (prop.type === 'number') return 0.0;
        if (prop.type === 'boolean') return false;
        if (prop.type === 'array') return [];
        if (prop.type === 'object') return {};
        
        return null;
    }

    // Get parameter values from inputs
    getParameterValues(parameters, type) {
        const values = {};
        
        if (!parameters) return values;
        
        parameters.forEach(param => {
            const inputId = `${type}-${param.name}`;
            const input = document.getElementById(inputId);
            
            if (input) {
                let value;
                
                if (input.type === 'checkbox') {
                    value = input.checked;
                } else if (input.type === 'number') {
                    value = input.value ? Number(input.value) : null;
                } else {
                    value = input.value || null;
                }
                
                if (value !== null && value !== '') {
                    values[param.name] = value;
                }
            }
        });
        
        return values;
    }

    // Build history item HTML
    buildHistoryItem(entry) {
        const statusClass = this.getStatusClass(entry.status);
        const timeAgo = this.getTimeAgo(new Date(entry.timestamp));
        
        return `
            <div class="history-item p-2 rounded border border-gray-200 dark:border-gray-700">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <span class="px-2 py-0.5 text-xs font-bold rounded method-${entry.method.toLowerCase()}">
                            ${entry.method}
                        </span>
                        <span class="text-sm text-gray-700 dark:text-gray-300">
                            ${this.formatPath(entry.path)}
                        </span>
                    </div>
                    <div class="flex items-center space-x-2 text-xs">
                        ${entry.status ? `
                            <span class="${statusClass} font-bold">${entry.status}</span>
                        ` : ''}
                        ${entry.responseTime ? `
                            <span class="text-gray-500">${entry.responseTime}ms</span>
                        ` : ''}
                        <span class="text-gray-500">${timeAgo}</span>
                    </div>
                </div>
                ${entry.error ? `
                    <div class="text-xs text-red-500 mt-1">${entry.error}</div>
                ` : ''}
            </div>
        `;
    }

    // Get status class based on status code
    getStatusClass(status) {
        if (!status) return '';
        if (status >= 200 && status < 300) return 'status-success';
        if (status >= 300 && status < 400) return 'status-redirect';
        if (status >= 400 && status < 500) return 'status-client-error';
        if (status >= 500) return 'status-server-error';
        return '';
    }

    // Get relative time string
    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        
        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        
        return date.toLocaleDateString();
    }
}

// Export for use in other scripts
window.UIBuilder = UIBuilder;