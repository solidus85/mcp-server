/**
 * Security utilities for input validation and sanitization
 * @module Security
 */

const Security = {
    /**
     * Validate email address format
     * @param {string} email - Email address to validate
     * @returns {boolean} - True if valid email
     */
    isValidEmail(email) {
        if (typeof email !== 'string') return false;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email) && email.length <= 254;
    },
    
    /**
     * Validate URL format
     * @param {string} url - URL to validate
     * @returns {boolean} - True if valid URL
     */
    isValidUrl(url) {
        if (typeof url !== 'string') return false;
        try {
            const urlObj = new URL(url);
            return ['http:', 'https:'].includes(urlObj.protocol);
        } catch {
            return false;
        }
    },
    
    /**
     * Sanitize filename for safe file operations
     * @param {string} filename - Filename to sanitize
     * @returns {string} - Sanitized filename
     */
    sanitizeFilename(filename) {
        if (typeof filename !== 'string') return 'file';
        
        // Remove path traversal attempts
        let safe = filename.replace(/\.\./g, '');
        safe = safe.replace(/[\/\\]/g, '_');
        
        // Remove special characters
        safe = safe.replace(/[^a-zA-Z0-9._-]/g, '_');
        
        // Limit length
        if (safe.length > 255) {
            const ext = safe.split('.').pop();
            safe = safe.substring(0, 250 - ext.length) + '.' + ext;
        }
        
        return safe || 'file';
    },
    
    /**
     * Validate and sanitize JSON input
     * @param {string} jsonString - JSON string to validate
     * @returns {Object|null} - Parsed JSON or null if invalid
     */
    parseJsonSafely(jsonString) {
        if (typeof jsonString !== 'string') return null;
        
        try {
            // Remove BOM and zero-width characters
            const cleaned = jsonString
                .replace(/^\uFEFF/, '')
                .replace(/[\u200B-\u200D\uFEFF]/g, '');
            
            const parsed = JSON.parse(cleaned);
            
            // Prevent prototype pollution
            if (parsed && typeof parsed === 'object') {
                if ('__proto__' in parsed || 'constructor' in parsed || 'prototype' in parsed) {
                    console.warn('Potential prototype pollution attempt detected');
                    return null;
                }
            }
            
            return parsed;
        } catch (e) {
            console.warn('Invalid JSON:', e.message);
            return null;
        }
    },
    
    /**
     * Create Content Security Policy header value
     * @param {Object} options - CSP options
     * @returns {string} - CSP header value
     */
    getCSPHeader(options = {}) {
        const defaults = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'unsafe-inline'"],
            'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.tailwindcss.com', 'https://cdnjs.cloudflare.com'],
            'img-src': ["'self'", 'data:', 'https:'],
            'font-src': ["'self'", 'https://cdnjs.cloudflare.com'],
            'connect-src': ["'self'", 'http://localhost:*'],
            'frame-ancestors': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"]
        };
        
        const policy = { ...defaults, ...options };
        
        return Object.entries(policy)
            .map(([key, values]) => `${key} ${values.join(' ')}`)
            .join('; ');
    },
    
    /**
     * Rate limiter for API calls
     * @param {string} key - Rate limit key
     * @param {number} maxRequests - Maximum requests allowed
     * @param {number} windowMs - Time window in milliseconds
     * @returns {boolean} - True if request is allowed
     */
    rateLimitCheck(key, maxRequests = 10, windowMs = 60000) {
        const now = Date.now();
        const storageKey = `rateLimit_${key}`;
        
        // Get existing data
        const data = window.Storage?.get(storageKey) || { requests: [], windowStart: now };
        
        // Clean old requests outside window
        data.requests = data.requests.filter(time => now - time < windowMs);
        
        // Check if limit exceeded
        if (data.requests.length >= maxRequests) {
            return false;
        }
        
        // Add current request
        data.requests.push(now);
        
        // Save updated data
        window.Storage?.set(storageKey, data);
        
        return true;
    },
    
    /**
     * Generate secure random string
     * @param {number} length - Length of string to generate
     * @returns {string} - Random string
     */
    generateSecureId(length = 32) {
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        const array = new Uint8Array(length);
        
        if (window.crypto && window.crypto.getRandomValues) {
            window.crypto.getRandomValues(array);
        } else {
            // Fallback for older browsers
            for (let i = 0; i < length; i++) {
                array[i] = Math.floor(Math.random() * 256);
            }
        }
        
        return Array.from(array, byte => chars[byte % chars.length]).join('');
    },
    
    /**
     * Validate and sanitize SQL-like input to prevent injection
     * @param {string} input - Input to sanitize
     * @returns {string} - Sanitized input
     */
    sanitizeSqlInput(input) {
        if (typeof input !== 'string') return '';
        
        // Remove SQL keywords and special characters
        const dangerous = /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE|UNION|FROM|WHERE|JOIN|SCRIPT|JAVASCRIPT|EVAL)\b|[;'"\\])/gi;
        
        return input.replace(dangerous, '');
    },
    
    /**
     * Check password strength
     * @param {string} password - Password to check
     * @returns {Object} - Strength score and suggestions
     */
    checkPasswordStrength(password) {
        const result = {
            score: 0,
            strength: 'weak',
            suggestions: []
        };
        
        if (!password || typeof password !== 'string') {
            result.suggestions.push('Password is required');
            return result;
        }
        
        // Length check
        if (password.length >= 8) result.score++;
        else result.suggestions.push('Use at least 8 characters');
        
        if (password.length >= 12) result.score++;
        
        // Complexity checks
        if (/[a-z]/.test(password)) result.score++;
        else result.suggestions.push('Include lowercase letters');
        
        if (/[A-Z]/.test(password)) result.score++;
        else result.suggestions.push('Include uppercase letters');
        
        if (/[0-9]/.test(password)) result.score++;
        else result.suggestions.push('Include numbers');
        
        if (/[^a-zA-Z0-9]/.test(password)) result.score++;
        else result.suggestions.push('Include special characters');
        
        // Common patterns check
        if (!/(.)\1{2,}/.test(password)) result.score++;
        else result.suggestions.push('Avoid repeating characters');
        
        if (!/^(password|123456|qwerty)/i.test(password)) result.score++;
        else result.suggestions.push('Avoid common passwords');
        
        // Determine strength
        if (result.score >= 7) result.strength = 'strong';
        else if (result.score >= 5) result.strength = 'medium';
        else result.strength = 'weak';
        
        return result;
    }
};

// Export for use in modules
window.Security = Security;

// Auto-cleanup rate limit data older than 1 hour
setInterval(() => {
    const storage = window.localStorage;
    const now = Date.now();
    const keys = [];
    
    for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key && key.startsWith('mcp_rateLimit_')) {
            keys.push(key);
        }
    }
    
    keys.forEach(key => {
        try {
            const data = JSON.parse(storage.getItem(key));
            if (data && data.requests) {
                data.requests = data.requests.filter(time => now - time < 3600000);
                if (data.requests.length === 0) {
                    storage.removeItem(key);
                } else {
                    storage.setItem(key, JSON.stringify(data));
                }
            }
        } catch (e) {
            // Invalid data, remove it
            storage.removeItem(key);
        }
    });
}, 300000); // Run every 5 minutes