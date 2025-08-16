// UI Template Builder - handles request body template generation from OpenAPI schemas

class UITemplateBuilder {
    constructor() {}

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
            return this.getStringExample(prop);
        }
        
        if (prop.type === 'integer') return 0;
        if (prop.type === 'number') return 0.0;
        if (prop.type === 'boolean') return false;
        if (prop.type === 'array') return [];
        if (prop.type === 'object') return {};
        
        return null;
    }

    // Get example value for string types
    getStringExample(prop) {
        if (prop.format === 'date-time') return new Date().toISOString();
        if (prop.format === 'date') return new Date().toISOString().split('T')[0];
        if (prop.format === 'time') return '12:00:00';
        if (prop.format === 'email') return 'user@example.com';
        if (prop.format === 'uri' || prop.format === 'url') return 'https://example.com';
        if (prop.format === 'uuid') return '00000000-0000-0000-0000-000000000000';
        if (prop.format === 'ipv4') return '192.168.1.1';
        if (prop.format === 'ipv6') return '2001:0db8:85a3:0000:0000:8a2e:0370:7334';
        if (prop.format === 'hostname') return 'example.com';
        if (prop.enum) return prop.enum[0];
        
        // Check for specific patterns
        if (prop.pattern) {
            if (prop.pattern.includes('phone')) return '+1234567890';
            if (prop.pattern.includes('zip')) return '12345';
        }
        
        // Check for naming hints
        const name = prop.title || '';
        if (name.toLowerCase().includes('name')) return 'John Doe';
        if (name.toLowerCase().includes('email')) return 'user@example.com';
        if (name.toLowerCase().includes('phone')) return '+1234567890';
        if (name.toLowerCase().includes('address')) return '123 Main St';
        if (name.toLowerCase().includes('city')) return 'New York';
        if (name.toLowerCase().includes('country')) return 'USA';
        if (name.toLowerCase().includes('description')) return 'Sample description text';
        
        return 'string';
    }
}