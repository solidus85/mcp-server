// UI Builder - Coordinator module that uses other UI modules

class UIBuilder {
    constructor() {
        this.currentEndpoint = null;
        
        // Initialize sub-modules
        this.endpointBuilder = new UIEndpointBuilder();
        this.parameterBuilder = new UIParameterBuilder();
        this.templateBuilder = new UITemplateBuilder();
        this.historyBuilder = new UIHistoryBuilder();
    }

    // Build sidebar with grouped endpoints (delegate to endpoint builder)
    buildEndpointsList(openApiSpec) {
        return this.endpointBuilder.buildEndpointsList(openApiSpec);
    }

    // Format path for display (delegate to endpoint builder)
    formatPath(path) {
        return this.endpointBuilder.formatPath(path);
    }

    // Build parameter inputs (delegate to parameter builder)
    buildParameterInputs(parameters, type) {
        return this.parameterBuilder.buildParameterInputs(parameters, type);
    }

    // Build advanced input control (delegate to parameter builder)
    buildAdvancedInputControl(inputId, schema, param = {}) {
        return this.parameterBuilder.buildAdvancedInputControl(inputId, schema, param);
    }

    // Build request body template (delegate to template builder)
    buildRequestBodyTemplate(requestBody, schemas) {
        return this.templateBuilder.buildRequestBodyTemplate(requestBody, schemas);
    }

    // Resolve schema references (delegate to template builder)
    resolveSchemaRef(schema, schemas) {
        return this.templateBuilder.resolveSchemaRef(schema, schemas);
    }

    // Merge schemas (delegate to template builder)
    mergeSchemas(schema1, schema2) {
        return this.templateBuilder.mergeSchemas(schema1, schema2);
    }

    // Build example from schema (delegate to template builder)
    buildExampleFromSchema(schema, schemas, depth = 0) {
        return this.templateBuilder.buildExampleFromSchema(schema, schemas, depth);
    }

    // Get example value (delegate to template builder)
    getExampleValue(prop, schemas, depth = 0) {
        return this.templateBuilder.getExampleValue(prop, schemas, depth);
    }

    // Get parameter values from inputs (delegate to parameter builder)
    getParameterValues(parameters, type) {
        return this.parameterBuilder.getParameterValues(parameters, type);
    }

    // Build history item HTML (delegate to history builder)
    buildHistoryItem(entry) {
        return this.historyBuilder.buildHistoryItem(entry);
    }

    // Get status class based on status code (delegate to history builder)
    getStatusClass(status) {
        return this.historyBuilder.getStatusClass(status);
    }

    // Get relative time string (delegate to history builder)
    getTimeAgo(date) {
        return this.historyBuilder.getTimeAgo(date);
    }
}

// Export for use in other scripts
window.UIBuilder = UIBuilder;