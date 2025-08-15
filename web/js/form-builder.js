// Enhanced Form Builder - Coordinator module that uses other form modules

class FormBuilder {
    constructor() {
        this.formCounter = 0;
        
        // Initialize sub-modules
        this.validation = new FormValidation();
        this.renderer = new FormRenderer();
        this.schemaResolver = new SchemaResolver();
        this.arrayHandler = new FormArrayHandler(this.renderer);
        
        // Make array handler globally accessible for onclick handlers
        window.formArrayHandler = this.arrayHandler;
    }

    // Build complete form from OpenAPI endpoint data
    buildForm(endpointData, schemas) {
        const formId = `form-${++this.formCounter}`;
        let html = `<form id="${formId}" class="api-test-form">`;
        
        // Build path parameters
        const pathParams = endpointData.parameters?.filter(p => p.in === 'path') || [];
        if (pathParams.length > 0) {
            html += this.renderer.buildParameterSection(pathParams, 'Path Parameters', 'path');
            // Store validation rules
            pathParams.forEach(param => {
                const fieldId = `path-${param.name}`;
                this.validation.storeValidationRules(fieldId, param.schema || {}, param.required);
            });
        }
        
        // Build query parameters
        const queryParams = endpointData.parameters?.filter(p => p.in === 'query') || [];
        if (queryParams.length > 0) {
            html += this.renderer.buildParameterSection(queryParams, 'Query Parameters', 'query');
            // Store validation rules
            queryParams.forEach(param => {
                const fieldId = `query-${param.name}`;
                this.validation.storeValidationRules(fieldId, param.schema || {}, param.required);
            });
        }
        
        // Build header parameters
        const headerParams = endpointData.parameters?.filter(p => p.in === 'header') || [];
        if (headerParams.length > 0) {
            html += this.renderer.buildParameterSection(headerParams, 'Headers', 'header');
            // Store validation rules
            headerParams.forEach(param => {
                const fieldId = `header-${param.name}`;
                this.validation.storeValidationRules(fieldId, param.schema || {}, param.required);
            });
        }
        
        // Build request body
        if (endpointData.requestBody) {
            html += this.buildRequestBodySection(endpointData.requestBody, schemas);
        }
        
        html += '</form>';
        return html;
    }

    // Build request body section
    buildRequestBodySection(requestBody, schemas) {
        const content = requestBody.content?.['application/json'];
        if (!content) return '';
        
        const schema = this.schemaResolver.resolveSchema(content.schema, schemas);
        const required = requestBody.required || false;
        
        // Debug: log what we're getting
        console.log('Building request body for schema:', schema);
        
        let html = `
            <div class="request-body-section mb-4">
        `;
        
        if (schema.type === 'object') {
            html += this.buildObjectFields(schema, schemas, 'body');
        } else {
            html += this.renderer.buildInputControl('request-body', schema);
            // Store validation rules
            this.validation.storeValidationRules('request-body', schema, required);
        }
        
        html += '</div>';
        return html;
    }

    // Build object fields recursively
    buildObjectFields(schema, schemas, prefix) {
        const html = this.renderer.buildObjectFields(schema, schemas, prefix, this.schemaResolver);
        
        // Store validation rules for each field
        const properties = schema.properties || {};
        const required = schema.required || [];
        
        Object.entries(properties).forEach(([key, prop]) => {
            const fieldId = `${prefix}-${key}`;
            const resolvedProp = this.schemaResolver.resolveSchema(prop, schemas);
            const isRequired = required.includes(key);
            
            // Skip redundant "Request Body" fields
            if (key === 'Request Body' || key === 'request_body' || key === 'requestBody') {
                return;
            }
            
            // Store validation rules
            this.validation.storeValidationRules(fieldId, resolvedProp, isRequired);
            
            // Recursively handle nested objects
            if (resolvedProp.type === 'object' && resolvedProp.properties) {
                this.storeNestedValidationRules(resolvedProp, schemas, fieldId);
            }
        });
        
        return html;
    }

    // Store validation rules for nested object properties
    storeNestedValidationRules(schema, schemas, prefix) {
        const properties = schema.properties || {};
        const required = schema.required || [];
        
        Object.entries(properties).forEach(([key, prop]) => {
            const fieldId = `${prefix}-${key}`;
            const resolvedProp = this.schemaResolver.resolveSchema(prop, schemas);
            const isRequired = required.includes(key);
            
            this.validation.storeValidationRules(fieldId, resolvedProp, isRequired);
            
            // Recursively handle deeper nesting
            if (resolvedProp.type === 'object' && resolvedProp.properties) {
                this.storeNestedValidationRules(resolvedProp, schemas, fieldId);
            }
        });
    }

    // Validate a field (delegate to validation module)
    validateField(fieldId, value) {
        return this.validation.validateField(fieldId, value);
    }

    // Validate entire form (delegate to validation module)
    validateForm(formId) {
        return this.validation.validateForm(formId);
    }

    // Show field error (delegate to validation module)
    showFieldError(field, message) {
        this.validation.showFieldError(field, message);
    }

    // Clear field error (delegate to validation module)
    clearFieldError(field) {
        this.validation.clearFieldError(field);
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
            const values = this.arrayHandler.getArrayValues(arrayId);
            
            if (values.length > 0) {
                const fieldName = arrayId.replace('array-', '').split('-').pop();
                data[fieldName] = values;
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

    // Reset form
    resetForm(formId) {
        const form = document.getElementById(formId);
        if (form) {
            form.reset();
            // Clear validation errors
            form.querySelectorAll('.field-error').forEach(error => error.remove());
            form.querySelectorAll('.border-red-500').forEach(field => {
                field.classList.remove('border-red-500');
                field.classList.add('border-gray-300', 'dark:border-gray-600');
            });
        }
        
        // Reset array counters
        this.arrayHandler.resetAllCounters();
        
        // Clear validation rules
        this.validation.clearValidationRules();
    }

    // Build validation hints (delegate to validation module)
    buildValidationHints(schema) {
        return this.validation.buildValidationHints(schema);
    }
}

// Create global instance
window.formBuilder = new FormBuilder();