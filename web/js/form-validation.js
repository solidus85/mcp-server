// Form validation module - handles all validation logic for forms

class FormValidation {
    constructor() {
        this.validationRules = {};
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

    // Store validation rules for a field
    storeValidationRules(fieldId, schema, required = false) {
        this.validationRules[fieldId] = this.extractValidationRules(schema, required);
    }

    // Get validation rules for a field
    getValidationRules(fieldId) {
        return this.validationRules[fieldId];
    }

    // Clear all validation rules
    clearValidationRules() {
        this.validationRules = {};
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
            if ((rules.format === 'uri' || rules.format === 'url') && !this.isValidUri(value)) {
                errors.push('Invalid URI');
            }
            if (rules.format === 'uuid' && !this.isValidUuid(value)) {
                errors.push('Invalid UUID format');
            }
            if (rules.format === 'date' && !this.isValidDate(value)) {
                errors.push('Invalid date format');
            }
            if (rules.format === 'date-time' && !this.isValidDateTime(value)) {
                errors.push('Invalid date-time format');
            }
        }
        
        return {
            valid: errors.length === 0,
            errors: errors
        };
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
        field.classList.remove('border-gray-300', 'dark:border-gray-600');
        
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
        field.classList.add('border-gray-300', 'dark:border-gray-600');
        
        const errorDiv = field.parentElement.querySelector('.field-error');
        if (errorDiv) errorDiv.remove();
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

    // UUID validation helper
    isValidUuid(uuid) {
        return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(uuid);
    }

    // Date validation helper
    isValidDate(date) {
        const regex = /^\d{4}-\d{2}-\d{2}$/;
        if (!regex.test(date)) return false;
        const d = new Date(date);
        return d instanceof Date && !isNaN(d);
    }

    // DateTime validation helper
    isValidDateTime(dateTime) {
        // Check for both ISO format and HTML datetime-local format
        const isoRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(\.\d{3})?([+-]\d{2}:\d{2}|Z)?$/;
        const htmlRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
        
        if (!isoRegex.test(dateTime) && !htmlRegex.test(dateTime)) return false;
        
        const d = new Date(dateTime);
        return d instanceof Date && !isNaN(d);
    }

    // Build validation hints for display
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
}