// UI Parameter Builder - handles parameter input generation and value extraction

class UIParameterBuilder {
    constructor() {
        this.baseClasses = 'w-full px-3 py-1 text-sm border rounded text-gray-900 dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:ring-2 focus:ring-blue-500';
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
            html += this.buildParameterField(param, type);
        });
        
        return html;
    }

    // Build a single parameter field
    buildParameterField(param, type) {
        const required = param.required ? '<span class="text-red-500">*</span>' : '';
        const inputId = `${type}-${param.name}`;
        const schema = param.schema || {};
        
        let html = `
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
        
        return html;
    }

    // Build advanced input control with more types
    buildAdvancedInputControl(inputId, schema, param = {}) {
        // Handle arrays
        if (schema.type === 'array') {
            return this.buildArrayInput(inputId, schema);
        }
        
        // Handle enums
        if (schema.enum) {
            return this.buildEnumInput(inputId, schema);
        }
        
        // Handle booleans
        if (schema.type === 'boolean') {
            return this.buildBooleanInput(inputId);
        }
        
        // Handle numbers
        if (schema.type === 'integer' || schema.type === 'number') {
            return this.buildNumberInput(inputId, schema);
        }
        
        // Handle strings with formats
        if (schema.type === 'string') {
            return this.buildStringInput(inputId, schema, param);
        }
        
        // Default to text input
        return this.buildDefaultInput(inputId, schema, param);
    }

    // Build array input
    buildArrayInput(inputId, schema) {
        if (schema.items?.enum) {
            // Multi-select for enum arrays
            return `
                <select id="${inputId}" multiple size="4" class="${this.baseClasses}">
                    ${schema.items.enum.map(val => `<option value="${val}">${val}</option>`).join('')}
                </select>
                <div class="text-xs text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple</div>
            `;
        }
        // Simple array input (comma-separated)
        return `
            <input type="text" id="${inputId}" 
                   placeholder="Enter values separated by commas"
                   class="${this.baseClasses}">
            <div class="text-xs text-gray-500 mt-1">Separate values with commas</div>
        `;
    }

    // Build enum input
    buildEnumInput(inputId, schema) {
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
            <select id="${inputId}" class="${this.baseClasses}">
                <option value="">-- Select --</option>
                ${schema.enum.map(val => `<option value="${val}">${val}</option>`).join('')}
            </select>
        `;
    }

    // Build boolean input
    buildBooleanInput(inputId) {
        return `
            <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" id="${inputId}" class="sr-only peer">
                <div class="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-600 peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 dark:bg-gray-700 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
            </label>
        `;
    }

    // Build number input
    buildNumberInput(inputId, schema) {
        const step = schema.type === 'integer' ? '1' : 'any';
        return `
            <input type="number" id="${inputId}" 
                   step="${step}"
                   placeholder="${schema.example || schema.default || ''}"
                   ${schema.minimum !== undefined ? `min="${schema.minimum}"` : ''}
                   ${schema.maximum !== undefined ? `max="${schema.maximum}"` : ''}
                   class="${this.baseClasses}">
        `;
    }

    // Build string input with formats
    buildStringInput(inputId, schema, param) {
        const format = schema.format;
        
        switch(format) {
            case 'date-time':
                return `<input type="datetime-local" id="${inputId}" class="${this.baseClasses}">`;
            case 'date':
                return `<input type="date" id="${inputId}" class="${this.baseClasses}">`;
            case 'time':
                return `<input type="time" id="${inputId}" class="${this.baseClasses}">`;
            case 'email':
                return `<input type="email" id="${inputId}" placeholder="user@example.com" class="${this.baseClasses}">`;
            case 'uri':
            case 'url':
                return `<input type="url" id="${inputId}" placeholder="https://example.com" class="${this.baseClasses}">`;
            case 'uuid':
                return `
                    <input type="text" id="${inputId}" 
                           pattern="[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                           placeholder="00000000-0000-0000-0000-000000000000"
                           class="${this.baseClasses}">
                `;
            case 'password':
                return `<input type="password" id="${inputId}" class="${this.baseClasses}">`;
            default:
                // Check for long text
                if (schema.maxLength && schema.maxLength > 100) {
                    return `
                        <textarea id="${inputId}" rows="3" 
                                  placeholder="${schema.example || param.example || ''}"
                                  ${schema.maxLength ? `maxlength="${schema.maxLength}"` : ''}
                                  class="${this.baseClasses}"></textarea>
                    `;
                }
                // Regular text input
                return `
                    <input type="text" id="${inputId}" 
                           placeholder="${schema.example || param.example || ''}"
                           ${schema.pattern ? `pattern="${schema.pattern}"` : ''}
                           ${schema.minLength ? `minlength="${schema.minLength}"` : ''}
                           ${schema.maxLength ? `maxlength="${schema.maxLength}"` : ''}
                           class="${this.baseClasses}">
                `;
        }
    }

    // Build default input
    buildDefaultInput(inputId, schema, param) {
        return `
            <input type="text" id="${inputId}" 
                   placeholder="${schema.example || param.example || ''}"
                   class="${this.baseClasses}">
        `;
    }

    // Get parameter values from inputs with enhanced type handling
    getParameterValues(parameters, type) {
        const values = {};
        
        if (!parameters) return values;
        
        parameters.forEach(param => {
            const inputId = `${type}-${param.name}`;
            const value = this.getInputValue(inputId, param.schema || {});
            
            if (value !== null && value !== '' && (!Array.isArray(value) || value.length > 0)) {
                values[param.name] = value;
            }
        });
        
        return values;
    }

    // Get value from a specific input
    getInputValue(inputId, schema) {
        const input = document.getElementById(inputId);
        if (!input) return null;
        
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
        
        return value;
    }
}