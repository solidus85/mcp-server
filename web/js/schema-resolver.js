// Schema resolver module - handles OpenAPI schema resolution and references

class SchemaResolver {
    constructor() {
        // Cache for resolved schemas to avoid redundant resolution
        this.resolvedSchemaCache = new Map();
    }

    // Resolve schema references
    resolveSchema(schema, schemas) {
        if (!schema) return {};
        
        // Check cache first
        const cacheKey = JSON.stringify(schema);
        if (this.resolvedSchemaCache.has(cacheKey)) {
            return this.resolvedSchemaCache.get(cacheKey);
        }
        
        let resolved = this._resolveSchemaInternal(schema, schemas);
        
        // Cache the result
        this.resolvedSchemaCache.set(cacheKey, resolved);
        
        return resolved;
    }

    // Internal schema resolution logic
    _resolveSchemaInternal(schema, schemas) {
        // Handle $ref references
        if (schema.$ref) {
            return this._resolveReference(schema.$ref, schemas);
        }
        
        // Handle oneOf - use the first option for simplicity
        if (schema.oneOf) {
            return this.resolveSchema(schema.oneOf[0], schemas);
        }
        
        // Handle anyOf - use the first option for simplicity
        if (schema.anyOf) {
            return this.resolveSchema(schema.anyOf[0], schemas);
        }
        
        // Handle allOf - merge all schemas
        if (schema.allOf) {
            return this._mergeAllOf(schema.allOf, schemas);
        }
        
        // Handle discriminator
        if (schema.discriminator) {
            return this._resolveDiscriminator(schema, schemas);
        }
        
        // Resolve nested schemas in properties
        if (schema.type === 'object' && schema.properties) {
            const resolved = { ...schema };
            resolved.properties = {};
            
            Object.entries(schema.properties).forEach(([key, prop]) => {
                resolved.properties[key] = this.resolveSchema(prop, schemas);
            });
            
            return resolved;
        }
        
        // Resolve array items
        if (schema.type === 'array' && schema.items) {
            const resolved = { ...schema };
            resolved.items = this.resolveSchema(schema.items, schemas);
            return resolved;
        }
        
        // Return schema as-is if no resolution needed
        return schema;
    }

    // Resolve a $ref reference
    _resolveReference(ref, schemas) {
        // Handle different reference formats
        if (ref.startsWith('#/components/schemas/')) {
            const schemaName = ref.replace('#/components/schemas/', '');
            const referenced = schemas[schemaName];
            
            if (!referenced) {
                console.warn(`Schema reference not found: ${schemaName}`);
                return {};
            }
            
            // Recursively resolve the referenced schema
            return this.resolveSchema(referenced, schemas);
        }
        
        // Handle relative references
        if (ref.startsWith('#/')) {
            const path = ref.substring(2).split('/');
            let current = schemas;
            
            for (const segment of path) {
                current = current[segment];
                if (!current) {
                    console.warn(`Schema reference path not found: ${ref}`);
                    return {};
                }
            }
            
            return this.resolveSchema(current, schemas);
        }
        
        console.warn(`Unsupported reference format: ${ref}`);
        return {};
    }

    // Merge allOf schemas
    _mergeAllOf(allOfSchemas, schemas) {
        let merged = {};
        
        allOfSchemas.forEach(s => {
            const resolved = this.resolveSchema(s, schemas);
            
            // Merge properties
            if (resolved.properties) {
                merged.properties = { ...(merged.properties || {}), ...resolved.properties };
            }
            
            // Merge required arrays
            if (resolved.required) {
                merged.required = [...(merged.required || []), ...resolved.required];
                // Remove duplicates
                merged.required = [...new Set(merged.required)];
            }
            
            // Merge other properties (taking the last value for conflicts)
            Object.entries(resolved).forEach(([key, value]) => {
                if (key !== 'properties' && key !== 'required') {
                    merged[key] = value;
                }
            });
        });
        
        return merged;
    }

    // Resolve discriminator-based schemas
    _resolveDiscriminator(schema, schemas) {
        // For now, just return the base schema
        // In a full implementation, this would handle polymorphic schemas
        const resolved = { ...schema };
        delete resolved.discriminator;
        
        if (resolved.oneOf) {
            // If there's a oneOf with discriminator, merge common properties
            const commonProps = this._extractCommonProperties(resolved.oneOf, schemas);
            resolved.properties = { ...(resolved.properties || {}), ...commonProps };
            delete resolved.oneOf;
        }
        
        return resolved;
    }

    // Extract common properties from multiple schemas
    _extractCommonProperties(schemaList, schemas) {
        if (!schemaList || schemaList.length === 0) return {};
        
        const resolvedSchemas = schemaList.map(s => this.resolveSchema(s, schemas));
        
        // Find properties that exist in all schemas
        const firstSchema = resolvedSchemas[0];
        const commonProps = {};
        
        if (firstSchema.properties) {
            Object.entries(firstSchema.properties).forEach(([key, prop]) => {
                // Check if this property exists in all other schemas
                const existsInAll = resolvedSchemas.every(s => 
                    s.properties && s.properties[key]
                );
                
                if (existsInAll) {
                    commonProps[key] = prop;
                }
            });
        }
        
        return commonProps;
    }

    // Clear the cache
    clearCache() {
        this.resolvedSchemaCache.clear();
    }

    // Get schema type information
    getSchemaType(schema) {
        if (schema.type) return schema.type;
        
        // Infer type from other properties
        if (schema.properties) return 'object';
        if (schema.items) return 'array';
        if (schema.enum) return 'string'; // Most enums are strings
        
        return 'string'; // Default fallback
    }

    // Check if schema is nullable
    isNullable(schema) {
        return schema.nullable === true || 
               (Array.isArray(schema.type) && schema.type.includes('null'));
    }

    // Get default value for schema
    getDefaultValue(schema) {
        if (schema.default !== undefined) return schema.default;
        
        const type = this.getSchemaType(schema);
        
        switch (type) {
            case 'object':
                return {};
            case 'array':
                return [];
            case 'boolean':
                return false;
            case 'integer':
            case 'number':
                return 0;
            case 'string':
                return '';
            default:
                return null;
        }
    }
}