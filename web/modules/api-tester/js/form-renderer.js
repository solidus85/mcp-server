// Form renderer module - handles HTML generation for forms

class FormRenderer {
    constructor() {
        this.baseClasses = 'w-full px-3 py-1.5 text-sm border rounded-md text-gray-900 dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400';
    }

    // Build parameter section
    buildParameterSection(parameters, title, type) {
        let html = `
            <div class="parameter-section mb-4" data-param-type="${type}">
                <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">${title}</h4>
                <div class="space-y-3">
        `;
        
        parameters.forEach(param => {
            html += this.buildParameterField(param, type);
        });
        
        html += `
                </div>
            </div>
        `;
        
        return html;
    }

    // Build individual parameter field
    buildParameterField(param, type) {
        const fieldId = `${type}-${param.name}`;
        const schema = param.schema || {};
        const required = param.required ? '<span class="text-red-500 ml-1">*</span>' : '';
        
        let html = `
            <div class="parameter-field" data-field-name="${param.name}">
                <label for="${fieldId}" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                    ${param.name}${required}
        `;
        
        // Add description as tooltip
        if (param.description) {
            html += `
                <span class="ml-2 text-gray-500 dark:text-gray-400 text-xs font-normal">
                    ${param.description}
                </span>
            `;
        }
        
        html += '</label>';
        
        // Build the appropriate input control
        html += this.buildInputControl(fieldId, schema, param);
        
        html += '</div>';
        
        return html;
    }

    // Build the appropriate input control based on schema
    buildInputControl(fieldId, schema, param = {}) {
        // Handle enums
        if (schema.enum) {
            return this.buildEnumControl(fieldId, schema);
        }
        
        // Handle arrays
        if (schema.type === 'array') {
            return this.buildArrayControl(fieldId, schema);
        }
        
        // Handle objects
        if (schema.type === 'object') {
            return this.buildObjectControl(fieldId, schema);
        }
        
        // Handle primitive types
        switch (schema.type) {
            case 'boolean':
                return this.buildBooleanControl(fieldId, schema);
            
            case 'integer':
            case 'number':
                return this.buildNumberControl(fieldId, schema);
            
            case 'string':
                return this.buildStringControl(fieldId, schema, param);
            
            default:
                // Default to text input
                return `<input type="text" id="${fieldId}" class="${this.baseClasses}" />`;
        }
    }

    // Build enum control (select or radio)
    buildEnumControl(fieldId, schema) {
        const options = schema.enum;
        
        if (options.length <= 4) {
            // Use radio buttons for small sets
            let html = '<div class="flex flex-wrap gap-3">';
            options.forEach((option, index) => {
                const optionId = `${fieldId}-${index}`;
                html += `
                    <label class="flex items-center">
                        <input type="radio" id="${optionId}" name="${fieldId}" value="${option}" 
                               class="mr-2 text-blue-500 focus:ring-blue-500">
                        <span class="text-sm">${option}</span>
                    </label>
                `;
            });
            html += '</div>';
            return html;
        } else {
            // Use select for larger sets
            let html = `<select id="${fieldId}" class="${this.baseClasses}">`;
            html += '<option value="">-- Select --</option>';
            options.forEach(option => {
                html += `<option value="${option}">${option}</option>`;
            });
            html += '</select>';
            return html;
        }
    }

    // Build array control with add/remove functionality
    buildArrayControl(fieldId, schema) {
        const itemSchema = schema.items || {};
        const arrayId = `array-${fieldId}`;
        
        let html = `
            <div class="array-control" data-array-id="${arrayId}">
                <div class="array-items space-y-2" id="${arrayId}-items">
                    <!-- Array items will be added here -->
                </div>
                <button type="button" onclick="window.formArrayHandler.addArrayItem('${arrayId}', ${JSON.stringify(itemSchema).replace(/"/g, '&quot;')})" 
                        class="mt-2 px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600">
                    + Add Item
                </button>
            </div>
        `;
        
        return html;
    }

    // Build object control with nested fields
    buildObjectControl(fieldId, schema) {
        const properties = schema.properties || {};
        const required = schema.required || [];
        
        let html = `
            <div class="object-control border-l-2 border-gray-300 dark:border-gray-600 pl-4 ml-2 space-y-3">
        `;
        
        Object.entries(properties).forEach(([key, prop]) => {
            // Skip if this looks like a "Request Body" label
            if (key.toLowerCase().replace(/[_\s-]/g, '') === 'requestbody') {
                return;
            }
            
            const nestedFieldId = `${fieldId}-${key}`;
            const isRequired = required.includes(key);
            
            html += `
                <div class="nested-field">
                    <label class="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                        ${key}${isRequired ? '<span class="text-red-500 ml-1">*</span>' : ''}
                    </label>
                    ${this.buildInputControl(nestedFieldId, prop)}
                </div>
            `;
        });
        
        html += '</div>';
        return html;
    }

    // Build boolean control (checkbox or switch)
    buildBooleanControl(fieldId, schema) {
        return `
            <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" id="${fieldId}" class="sr-only peer">
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                <span class="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">
                    ${schema.default === true ? 'On' : 'Off'}
                </span>
            </label>
        `;
    }

    // Build number control with min/max/step
    buildNumberControl(fieldId, schema) {
        const min = schema.minimum !== undefined ? `min="${schema.minimum}"` : '';
        const max = schema.maximum !== undefined ? `max="${schema.maximum}"` : '';
        const step = schema.type === 'integer' ? 'step="1"' : 'step="any"';
        const placeholder = schema.example || schema.default || '';
        
        return `
            <input type="number" id="${fieldId}" 
                   ${min} ${max} ${step}
                   placeholder="${placeholder}"
                   class="${this.baseClasses}" />
        `;
    }

    // Build string control with format-specific inputs
    buildStringControl(fieldId, schema, param = {}) {
        const format = schema.format;
        const placeholder = schema.example || schema.default || '';
        
        // Handle different string formats
        switch (format) {
            case 'date-time':
                return `<input type="datetime-local" id="${fieldId}" class="${this.baseClasses}" />`;
            
            case 'date':
                return `<input type="date" id="${fieldId}" class="${this.baseClasses}" />`;
            
            case 'time':
                return `<input type="time" id="${fieldId}" class="${this.baseClasses}" />`;
            
            case 'email':
                return `<input type="email" id="${fieldId}" placeholder="user@example.com" class="${this.baseClasses}" />`;
            
            case 'uri':
            case 'url':
                return `<input type="url" id="${fieldId}" placeholder="https://example.com" class="${this.baseClasses}" />`;
            
            case 'uuid':
                return `<input type="text" id="${fieldId}" 
                        pattern="[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" 
                        placeholder="00000000-0000-0000-0000-000000000000"
                        class="${this.baseClasses}" />`;
            
            case 'password':
                return `<input type="password" id="${fieldId}" class="${this.baseClasses}" />`;
            
            case 'binary':
            case 'byte':
                return `<input type="file" id="${fieldId}" class="${this.baseClasses}" />`;
            
            default:
                // Check for multiline text
                if (schema.maxLength && schema.maxLength > 100) {
                    return `<textarea id="${fieldId}" rows="4" placeholder="${placeholder}" class="${this.baseClasses}"></textarea>`;
                }
                
                // Default text input with pattern if provided
                const pattern = schema.pattern ? `pattern="${schema.pattern}"` : '';
                const minLength = schema.minLength ? `minlength="${schema.minLength}"` : '';
                const maxLength = schema.maxLength ? `maxlength="${schema.maxLength}"` : '';
                
                return `<input type="text" id="${fieldId}" 
                        ${pattern} ${minLength} ${maxLength}
                        placeholder="${placeholder}"
                        class="${this.baseClasses}" />`;
        }
    }

    // Build object fields recursively
    buildObjectFields(schema, schemas, prefix, schemaResolver) {
        const properties = schema.properties || {};
        const required = schema.required || [];
        
        // Don't show a "Request Body" label - it's redundant
        let html = '<div class="space-y-3">';
        
        Object.entries(properties).forEach(([key, prop]) => {
            const fieldId = `${prefix}-${key}`;
            const resolvedProp = schemaResolver.resolveSchema(prop, schemas);
            const isRequired = required.includes(key);
            
            // Skip if the key contains "Request Body" to avoid redundancy
            if (key === 'Request Body' || key === 'request_body' || key === 'requestBody') {
                return;
            }
            
            html += `
                <div class="field-group">
                    <label for="${fieldId}" class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                        ${key}${isRequired ? '<span class="text-red-500 ml-1">*</span>' : ''}
                        ${resolvedProp.description ? `
                            <span class="ml-2 text-gray-500 dark:text-gray-400 text-xs font-normal">
                                ${resolvedProp.description}
                            </span>
                        ` : ''}
                    </label>
            `;
            
            if (resolvedProp.type === 'object') {
                html += this.buildObjectFields(resolvedProp, schemas, fieldId, schemaResolver);
            } else {
                html += this.buildInputControl(fieldId, resolvedProp);
            }
            
            html += '</div>';
        });
        
        html += '</div>';
        return html;
    }
}