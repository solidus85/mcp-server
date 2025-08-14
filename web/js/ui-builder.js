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

    // Build parameter inputs with enhanced form builder
    buildParameterInputs(parameters, type) {
        if (!parameters || parameters.length === 0) {
            return '';
        }
        
        // Use the enhanced form builder if available
        if (window.formBuilder) {
            let html = '<div class="space-y-3">';
            parameters.forEach(param => {
                html += window.formBuilder.buildParameterField(param, type);
            });
            html += '</div>';
            return html;
        }
        
        // Fallback to original implementation
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
            html += this.buildAdvancedInputControl(inputId, schema, param);
            html += '</div>';
        });
        
        return html;
    }

    // Build advanced input control with more types
    buildAdvancedInputControl(inputId, schema, param = {}) {
        const baseClasses = 'w-full px-3 py-1 text-sm border rounded text-gray-900 dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:ring-2 focus:ring-blue-500';
        
        // Handle arrays
        if (schema.type === 'array') {
            if (schema.items?.enum) {
                // Multi-select for enum arrays
                return `
                    <select id="${inputId}" multiple size="4" class="${baseClasses}">
                        ${schema.items.enum.map(val => `<option value="${val}">${val}</option>`).join('')}
                    </select>
                    <div class="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</div>
                `;
            }
            // Simple array input (comma-separated)
            return `
                <input type="text" id="${inputId}" 
                       placeholder="Enter values separated by commas"
                       class="${baseClasses}">
                <div class="text-xs text-gray-500 mt-1">Separate values with commas</div>
            `;
        }
        
        // Handle enums
        if (schema.enum) {
            if (schema.enum.length <= 4) {
                // Radio buttons for small enums
                let html = '<div class="flex flex-wrap gap-3">';
                schema.enum.forEach((val, i) => {
                    html += `
                        <label class="flex items-center">
                            <input type="radio" name="${inputId}" value="${val}" 
                                   ${i === 0 ? 'checked' : ''}
                                   class="mr-2 text-blue-500">
                            <span class="text-sm">${val}</span>
                        </label>
                    `;
                });
                html += '</div>';
                return html;
            }
            // Dropdown for larger enums
            return `
                <select id="${inputId}" class="${baseClasses}">
                    <option value="">-- Select --</option>
                    ${schema.enum.map(val => `<option value="${val}">${val}</option>`).join('')}
                </select>
            `;
        }
        
        // Handle booleans
        if (schema.type === 'boolean') {
            return `
                <label class="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" id="${inputId}" class="sr-only peer">
                    <div class="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-600 peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 dark:bg-gray-700 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
                </label>
            `;
        }
        
        // Handle numbers
        if (schema.type === 'integer' || schema.type === 'number') {
            const step = schema.type === 'integer' ? '1' : 'any';
            return `
                <input type="number" id="${inputId}" 
                       step="${step}"
                       placeholder="${schema.example || schema.default || ''}"
                       ${schema.minimum !== undefined ? `min="${schema.minimum}"` : ''}
                       ${schema.maximum !== undefined ? `max="${schema.maximum}"` : ''}
                       class="${baseClasses}">
            `;
        }
        
        // Handle strings with formats
        if (schema.type === 'string') {
            const format = schema.format;
            
            switch(format) {
                case 'date-time':
                    return `<input type="datetime-local" id="${inputId}" class="${baseClasses}">`;
                case 'date':
                    return `<input type="date" id="${inputId}" class="${baseClasses}">`;
                case 'time':
                    return `<input type="time" id="${inputId}" class="${baseClasses}">`;
                case 'email':
                    return `<input type="email" id="${inputId}" placeholder="user@example.com" class="${baseClasses}">`;
                case 'uri':
                case 'url':
                    return `<input type="url" id="${inputId}" placeholder="https://example.com" class="${baseClasses}">`;
                case 'uuid':
                    return `
                        <input type="text" id="${inputId}" 
                               pattern="[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                               placeholder="00000000-0000-0000-0000-000000000000"
                               class="${baseClasses}">
                    `;
                case 'password':
                    return `<input type="password" id="${inputId}" class="${baseClasses}">`;
                default:
                    // Check for long text
                    if (schema.maxLength && schema.maxLength > 100) {
                        return `
                            <textarea id="${inputId}" rows="3" 
                                      placeholder="${schema.example || param.example || ''}"
                                      ${schema.maxLength ? `maxlength="${schema.maxLength}"` : ''}
                                      class="${baseClasses}"></textarea>
                        `;
                    }
                    // Regular text input
                    return `
                        <input type="text" id="${inputId}" 
                               placeholder="${schema.example || param.example || ''}"
                               ${schema.pattern ? `pattern="${schema.pattern}"` : ''}
                               ${schema.minLength ? `minlength="${schema.minLength}"` : ''}
                               ${schema.maxLength ? `maxlength="${schema.maxLength}"` : ''}
                               class="${baseClasses}">
                    `;
            }
        }
        
        // Default to text input
        return `
            <input type="text" id="${inputId}" 
                   placeholder="${schema.example || param.example || ''}"
                   class="${baseClasses}">
        `;
    }

    // Build request body template with enhanced schema resolution
    buildRequestBodyTemplate(requestBody, schemas) {
        if (!requestBody || !requestBody.content) {
            return null;
        }
        
        // Try different content types
        const contentTypes = ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data'];
        let content = null;
        let contentType = null;
        
        for (const type of contentTypes) {
            if (requestBody.content[type]) {
                content = requestBody.content[type];
                contentType = type;
                break;
            }
        }
        
        if (!content || !content.schema) return null;
        
        const schema = content.schema;
        
        // Resolve schema reference if needed
        let resolvedSchema = this.resolveSchemaRef(schema, schemas);
        
        // Build example object
        return this.buildExampleFromSchema(resolvedSchema, schemas);
    }

    // Resolve schema references including oneOf, anyOf, allOf
    resolveSchemaRef(schema, schemas) {
        if (!schema) return {};
        
        // Handle $ref
        if (schema.$ref) {
            const schemaName = schema.$ref.split('/').pop();
            return this.resolveSchemaRef(schemas[schemaName], schemas);
        }
        
        // Handle oneOf - use first option
        if (schema.oneOf && schema.oneOf.length > 0) {
            return this.resolveSchemaRef(schema.oneOf[0], schemas);
        }
        
        // Handle anyOf - use first option
        if (schema.anyOf && schema.anyOf.length > 0) {
            return this.resolveSchemaRef(schema.anyOf[0], schemas);
        }
        
        // Handle allOf - merge all schemas
        if (schema.allOf && schema.allOf.length > 0) {
            let merged = {};
            schema.allOf.forEach(s => {
                const resolved = this.resolveSchemaRef(s, schemas);
                merged = this.mergeSchemas(merged, resolved);
            });
            return merged;
        }
        
        return schema;
    }

    // Merge two schemas
    mergeSchemas(schema1, schema2) {
        const merged = { ...schema1 };
        
        Object.keys(schema2).forEach(key => {
            if (key === 'properties' && merged.properties) {
                merged.properties = { ...merged.properties, ...schema2.properties };
            } else if (key === 'required' && merged.required) {
                merged.required = [...new Set([...merged.required, ...schema2.required])];
            } else {
                merged[key] = schema2[key];
            }
        });
        
        return merged;
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

    // Get parameter values from inputs with enhanced type handling
    getParameterValues(parameters, type) {
        const values = {};
        
        if (!parameters) return values;
        
        parameters.forEach(param => {
            const inputId = `${type}-${param.name}`;
            const input = document.getElementById(inputId);
            const schema = param.schema || {};
            
            if (input) {
                let value;
                
                // Handle different input types
                if (input.type === 'checkbox') {
                    value = input.checked;
                } else if (input.type === 'radio') {
                    // For radio buttons, find the checked one
                    const checked = document.querySelector(`input[name="${inputId}"]:checked`);
                    value = checked ? checked.value : null;
                } else if (input.type === 'number') {
                    value = input.value ? Number(input.value) : null;
                } else if (input.tagName === 'SELECT' && input.multiple) {
                    // Handle multi-select
                    value = Array.from(input.selectedOptions).map(opt => opt.value);
                } else if (input.type === 'datetime-local' || input.type === 'date' || input.type === 'time') {
                    // Handle date/time inputs
                    value = input.value || null;
                    if (value && schema.format === 'date-time') {
                        // Convert to ISO string
                        value = new Date(value).toISOString();
                    }
                } else if (input.type === 'file') {
                    // Handle file inputs
                    value = input.files[0] || null;
                } else {
                    value = input.value || null;
                    
                    // Handle array inputs (comma-separated)
                    if (schema.type === 'array' && typeof value === 'string' && value.includes(',')) {
                        value = value.split(',').map(v => v.trim()).filter(v => v);
                    }
                }
                
                if (value !== null && value !== '' && (!Array.isArray(value) || value.length > 0)) {
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