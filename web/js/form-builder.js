// Enhanced Form Builder for dynamic form generation based on OpenAPI schemas

class FormBuilder {
    constructor() {
        this.formCounter = 0;
        this.arrayCounters = {};
        this.validationRules = {};
    }

    // Build complete form from OpenAPI endpoint data
    buildForm(endpointData, schemas) {
        const formId = `form-${++this.formCounter}`;
        let html = `<form id="${formId}" class="api-test-form">`;
        
        // Build path parameters
        const pathParams = endpointData.parameters?.filter(p => p.in === 'path') || [];
        if (pathParams.length > 0) {
            html += this.buildParameterSection(pathParams, 'Path Parameters', 'path');
        }
        
        // Build query parameters
        const queryParams = endpointData.parameters?.filter(p => p.in === 'query') || [];
        if (queryParams.length > 0) {
            html += this.buildParameterSection(queryParams, 'Query Parameters', 'query');
        }
        
        // Build header parameters
        const headerParams = endpointData.parameters?.filter(p => p.in === 'header') || [];
        if (headerParams.length > 0) {
            html += this.buildParameterSection(headerParams, 'Headers', 'header');
        }
        
        // Build request body
        if (endpointData.requestBody) {
            html += this.buildRequestBodySection(endpointData.requestBody, schemas);
        }
        
        html += '</form>';
        return html;
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
        
        // Add validation hints
        html += this.buildValidationHints(schema);
        
        html += '</div>';
        
        // Store validation rules
        this.validationRules[fieldId] = this.extractValidationRules(schema, param.required);
        
        return html;
    }

    // Build the appropriate input control based on schema
    buildInputControl(fieldId, schema, param = {}) {
        const baseClasses = 'w-full px-3 py-1.5 text-sm border rounded-md text-gray-900 dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400';
        
        // Handle enums
        if (schema.enum) {
            return this.buildEnumControl(fieldId, schema, baseClasses);
        }
        
        // Handle arrays
        if (schema.type === 'array') {
            return this.buildArrayControl(fieldId, schema, baseClasses);
        }
        
        // Handle objects
        if (schema.type === 'object') {
            return this.buildObjectControl(fieldId, schema, baseClasses);
        }
        
        // Handle primitive types
        switch (schema.type) {
            case 'boolean':
                return this.buildBooleanControl(fieldId, schema, baseClasses);
            
            case 'integer':
            case 'number':
                return this.buildNumberControl(fieldId, schema, baseClasses);
            
            case 'string':
                return this.buildStringControl(fieldId, schema, baseClasses, param);
            
            default:
                // Default to text input
                return `<input type="text" id="${fieldId}" class="${baseClasses}" />`;
        }
    }

    // Build enum control (select or radio)
    buildEnumControl(fieldId, schema, baseClasses) {
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
            let html = `<select id="${fieldId}" class="${baseClasses}">`;
            html += '<option value="">-- Select --</option>';
            options.forEach(option => {
                html += `<option value="${option}">${option}</option>`;
            });
            html += '</select>';
            return html;
        }
    }

    // Build array control with add/remove functionality
    buildArrayControl(fieldId, schema, baseClasses) {
        const itemSchema = schema.items || {};
        const arrayId = `array-${fieldId}`;
        this.arrayCounters[arrayId] = 0;
        
        let html = `
            <div class="array-control" data-array-id="${arrayId}">
                <div class="array-items space-y-2" id="${arrayId}-items">
                    <!-- Array items will be added here -->
                </div>
                <button type="button" onclick="formBuilder.addArrayItem('${arrayId}', ${JSON.stringify(itemSchema).replace(/"/g, '&quot;')})" 
                        class="mt-2 px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600">
                    + Add Item
                </button>
            </div>
        `;
        
        return html;
    }

    // Add array item dynamically
    addArrayItem(arrayId, itemSchema) {
        const container = document.getElementById(`${arrayId}-items`);
        const itemIndex = this.arrayCounters[arrayId]++;
        const itemId = `${arrayId}-item-${itemIndex}`;
        
        const itemHtml = `
            <div class="array-item flex gap-2" data-item-id="${itemId}">
                ${this.buildInputControl(itemId, itemSchema)}
                <button type="button" onclick="formBuilder.removeArrayItem('${itemId}')" 
                        class="px-2 py-1 text-sm text-red-500 hover:text-red-700">
                    ✕
                </button>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', itemHtml);
    }

    // Remove array item
    removeArrayItem(itemId) {
        const item = document.querySelector(`[data-item-id="${itemId}"]`);
        if (item) item.remove();
    }

    // Build object control with nested fields
    buildObjectControl(fieldId, schema, baseClasses) {
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
    buildBooleanControl(fieldId, schema, baseClasses) {
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
    buildNumberControl(fieldId, schema, baseClasses) {
        const min = schema.minimum !== undefined ? `min="${schema.minimum}"` : '';
        const max = schema.maximum !== undefined ? `max="${schema.maximum}"` : '';
        const step = schema.type === 'integer' ? 'step="1"' : 'step="any"';
        const placeholder = schema.example || schema.default || '';
        
        return `
            <input type="number" id="${fieldId}" 
                   ${min} ${max} ${step}
                   placeholder="${placeholder}"
                   class="${baseClasses}" />
        `;
    }

    // Build string control with format-specific inputs
    buildStringControl(fieldId, schema, baseClasses, param = {}) {
        const format = schema.format;
        const placeholder = schema.example || schema.default || '';
        
        // Handle different string formats
        switch (format) {
            case 'date-time':
                return `<input type="datetime-local" id="${fieldId}" class="${baseClasses}" />`;
            
            case 'date':
                return `<input type="date" id="${fieldId}" class="${baseClasses}" />`;
            
            case 'time':
                return `<input type="time" id="${fieldId}" class="${baseClasses}" />`;
            
            case 'email':
                return `<input type="email" id="${fieldId}" placeholder="user@example.com" class="${baseClasses}" />`;
            
            case 'uri':
            case 'url':
                return `<input type="url" id="${fieldId}" placeholder="https://example.com" class="${baseClasses}" />`;
            
            case 'uuid':
                return `<input type="text" id="${fieldId}" 
                        pattern="[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" 
                        placeholder="00000000-0000-0000-0000-000000000000"
                        class="${baseClasses}" />`;
            
            case 'password':
                return `<input type="password" id="${fieldId}" class="${baseClasses}" />`;
            
            case 'binary':
            case 'byte':
                return `<input type="file" id="${fieldId}" class="${baseClasses}" />`;
            
            default:
                // Check for multiline text
                if (schema.maxLength && schema.maxLength > 100) {
                    return `<textarea id="${fieldId}" rows="4" placeholder="${placeholder}" class="${baseClasses}"></textarea>`;
                }
                
                // Default text input with pattern if provided
                const pattern = schema.pattern ? `pattern="${schema.pattern}"` : '';
                const minLength = schema.minLength ? `minlength="${schema.minLength}"` : '';
                const maxLength = schema.maxLength ? `maxlength="${schema.maxLength}"` : '';
                
                return `<input type="text" id="${fieldId}" 
                        ${pattern} ${minLength} ${maxLength}
                        placeholder="${placeholder}"
                        class="${baseClasses}" />`;
        }
    }

    // Build validation hints
    buildValidationHints(schema) {
        const hints = [];
        
        if (schema.minimum !== undefined) {
            hints.push(`Min: ${schema.minimum}`);
        }
        if (schema.maximum !== undefined) {
            hints.push(`Max: ${schema.maximum}`);
        }
        if (schema.minLength !== undefined) {
            hints.push(`Min length: ${schema.minLength}`);
        }
        if (schema.maxLength !== undefined) {
            hints.push(`Max length: ${schema.maxLength}`);
        }
        if (schema.pattern) {
            hints.push(`Pattern: ${schema.pattern}`);
        }
        if (schema.format) {
            hints.push(`Format: ${schema.format}`);
        }
        
        if (hints.length > 0) {
            return `
                <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    ${hints.join(' • ')}
                </div>
            `;
        }
        
        return '';
    }

    // Build request body section
    buildRequestBodySection(requestBody, schemas) {
        const content = requestBody.content?.['application/json'];
        if (!content) return '';
        
        const schema = this.resolveSchema(content.schema, schemas);
        const required = requestBody.required || false;
        
        // Debug: log what we're getting
        console.log('Building request body for schema:', schema);
        
        let html = `
            <div class="request-body-section mb-4">
        `;
        
        if (schema.type === 'object') {
            html += this.buildObjectFields(schema, schemas, 'body');
        } else {
            html += this.buildInputControl('request-body', schema);
        }
        
        html += '</div>';
        return html;
    }

    // Build object fields recursively
    buildObjectFields(schema, schemas, prefix) {
        const properties = schema.properties || {};
        const required = schema.required || [];
        
        // Debug: log the properties we're processing
        console.log('Building fields for properties:', Object.keys(properties));
        
        // Don't show a "Request Body" label - it's redundant
        let html = '<div class="space-y-3">';
        
        Object.entries(properties).forEach(([key, prop]) => {
            console.log(`Processing property: "${key}"`);  // Debug log
            const fieldId = `${prefix}-${key}`;
            const resolvedProp = this.resolveSchema(prop, schemas);
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
                html += this.buildObjectFields(resolvedProp, schemas, fieldId);
            } else {
                html += this.buildInputControl(fieldId, resolvedProp);
            }
            
            html += this.buildValidationHints(resolvedProp);
            html += '</div>';
            
            // Store validation rules
            this.validationRules[fieldId] = this.extractValidationRules(resolvedProp, isRequired);
        });
        
        html += '</div>';
        return html;
    }

    // Resolve schema references
    resolveSchema(schema, schemas) {
        if (!schema) return {};
        
        if (schema.$ref) {
            const refPath = schema.$ref.split('/');
            const schemaName = refPath[refPath.length - 1];
            return schemas[schemaName] || {};
        }
        
        // Handle oneOf, anyOf, allOf
        if (schema.oneOf) {
            // For simplicity, use the first option
            return this.resolveSchema(schema.oneOf[0], schemas);
        }
        if (schema.anyOf) {
            return this.resolveSchema(schema.anyOf[0], schemas);
        }
        if (schema.allOf) {
            // Merge all schemas
            let merged = {};
            schema.allOf.forEach(s => {
                const resolved = this.resolveSchema(s, schemas);
                merged = { ...merged, ...resolved };
            });
            return merged;
        }
        
        return schema;
    }

    // Extract validation rules from schema
    extractValidationRules(schema, required = false) {
        const rules = {
            required: required,
            type: schema.type,
            format: schema.format
        };
        
        if (schema.minimum !== undefined) rules.minimum = schema.minimum;
        if (schema.maximum !== undefined) rules.maximum = schema.maximum;
        if (schema.minLength !== undefined) rules.minLength = schema.minLength;
        if (schema.maxLength !== undefined) rules.maxLength = schema.maxLength;
        if (schema.pattern) rules.pattern = new RegExp(schema.pattern);
        if (schema.enum) rules.enum = schema.enum;
        
        return rules;
    }

    // Validate a field
    validateField(fieldId, value) {
        const rules = this.validationRules[fieldId];
        if (!rules) return { valid: true };
        
        const errors = [];
        
        // Check required
        if (rules.required && (!value || value === '')) {
            errors.push('This field is required');
        }
        
        if (value && value !== '') {
            // Type validation
            if (rules.type === 'integer' && !Number.isInteger(Number(value))) {
                errors.push('Must be an integer');
            }
            if (rules.type === 'number' && isNaN(Number(value))) {
                errors.push('Must be a number');
            }
            
            // Range validation
            if (rules.minimum !== undefined && Number(value) < rules.minimum) {
                errors.push(`Must be at least ${rules.minimum}`);
            }
            if (rules.maximum !== undefined && Number(value) > rules.maximum) {
                errors.push(`Must be at most ${rules.maximum}`);
            }
            
            // Length validation
            if (rules.minLength !== undefined && value.length < rules.minLength) {
                errors.push(`Must be at least ${rules.minLength} characters`);
            }
            if (rules.maxLength !== undefined && value.length > rules.maxLength) {
                errors.push(`Must be at most ${rules.maxLength} characters`);
            }
            
            // Pattern validation
            if (rules.pattern && !rules.pattern.test(value)) {
                errors.push('Invalid format');
            }
            
            // Enum validation
            if (rules.enum && !rules.enum.includes(value)) {
                errors.push(`Must be one of: ${rules.enum.join(', ')}`);
            }
            
            // Format validation
            if (rules.format === 'email' && !this.isValidEmail(value)) {
                errors.push('Invalid email address');
            }
            if (rules.format === 'uri' && !this.isValidUri(value)) {
                errors.push('Invalid URI');
            }
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    // Email validation helper
    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    // URI validation helper
    isValidUri(uri) {
        try {
            new URL(uri);
            return true;
        } catch {
            return false;
        }
    }

    // Validate entire form
    validateForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return { valid: false, errors: {} };
        
        const errors = {};
        let isValid = true;
        
        // Validate all fields with validation rules
        Object.keys(this.validationRules).forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                const value = field.type === 'checkbox' ? field.checked : field.value;
                const validation = this.validateField(fieldId, value);
                
                if (!validation.valid) {
                    errors[fieldId] = validation.errors;
                    isValid = false;
                    this.showFieldError(field, validation.errors[0]);
                } else {
                    this.clearFieldError(field);
                }
            }
        });
        
        return { valid: isValid, errors };
    }

    // Show field error
    showFieldError(field, message) {
        field.classList.add('border-red-500');
        field.classList.remove('border-gray-300');
        
        // Remove existing error message
        const existingError = field.parentElement.querySelector('.field-error');
        if (existingError) existingError.remove();
        
        // Add new error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-xs text-red-500 mt-1';
        errorDiv.textContent = message;
        field.parentElement.appendChild(errorDiv);
    }

    // Clear field error
    clearFieldError(field) {
        field.classList.remove('border-red-500');
        field.classList.add('border-gray-300');
        
        const errorDiv = field.parentElement.querySelector('.field-error');
        if (errorDiv) errorDiv.remove();
    }

    // Get form data as object
    getFormData(formId) {
        const form = document.getElementById(formId);
        if (!form) return {};
        
        const data = {};
        
        // Get all input elements
        form.querySelectorAll('input, select, textarea').forEach(field => {
            const fieldId = field.id;
            if (!fieldId) return;
            
            let value;
            if (field.type === 'checkbox') {
                value = field.checked;
            } else if (field.type === 'radio') {
                if (field.checked) {
                    value = field.value;
                }
            } else if (field.type === 'number') {
                value = field.value ? Number(field.value) : null;
            } else if (field.type === 'file') {
                value = field.files[0];
            } else {
                value = field.value || null;
            }
            
            if (value !== undefined && value !== null && value !== '') {
                // Handle nested fields
                if (fieldId.includes('-')) {
                    const parts = fieldId.split('-');
                    this.setNestedValue(data, parts, value);
                } else {
                    data[fieldId] = value;
                }
            }
        });
        
        // Handle array fields
        form.querySelectorAll('.array-control').forEach(arrayControl => {
            const arrayId = arrayControl.dataset.arrayId;
            const items = [];
            
            arrayControl.querySelectorAll('.array-item input, .array-item select, .array-item textarea').forEach(field => {
                if (field.value) {
                    items.push(field.type === 'number' ? Number(field.value) : field.value);
                }
            });
            
            if (items.length > 0) {
                const fieldName = arrayId.replace('array-', '').split('-').pop();
                data[fieldName] = items;
            }
        });
        
        return data;
    }

    // Set nested value in object
    setNestedValue(obj, path, value) {
        const lastKey = path.pop();
        const target = path.reduce((current, key) => {
            if (!current[key]) current[key] = {};
            return current[key];
        }, obj);
        target[lastKey] = value;
    }
}

// Create global instance
window.formBuilder = new FormBuilder();