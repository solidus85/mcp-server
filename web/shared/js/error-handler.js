/**
 * Global error handling and reporting
 * @module ErrorHandler
 */

class ErrorHandler {
    constructor() {
        this.errors = [];
        this.maxErrors = 100;
        this.errorListeners = new Set();
        this.setupGlobalHandlers();
    }
    
    /**
     * Setup global error handlers
     * @private
     */
    setupGlobalHandlers() {
        // Handle uncaught errors
        window.addEventListener('error', (event) => {
            this.handleError({
                type: 'uncaught',
                message: event.message,
                filename: event.filename,
                line: event.lineno,
                column: event.colno,
                error: event.error,
                timestamp: Date.now()
            });
            
            // Prevent default error handling in production
            if (window.AppConfig?.dev?.debug !== true) {
                event.preventDefault();
            }
        });
        
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError({
                type: 'unhandledRejection',
                message: event.reason?.message || String(event.reason),
                error: event.reason,
                promise: event.promise,
                timestamp: Date.now()
            });
            
            // Prevent default handling in production
            if (window.AppConfig?.dev?.debug !== true) {
                event.preventDefault();
            }
        });
    }
    
    /**
     * Handle an error
     * @param {Error|Object} error - Error object or error details
     * @param {Object} context - Additional context
     */
    handleError(error, context = {}) {
        // Normalize error object
        const errorInfo = this.normalizeError(error);
        
        // Add context
        errorInfo.context = context;
        errorInfo.userAgent = navigator.userAgent;
        errorInfo.url = window.location.href;
        errorInfo.timestamp = errorInfo.timestamp || Date.now();
        
        // Store error
        this.storeError(errorInfo);
        
        // Log error
        this.logError(errorInfo);
        
        // Notify listeners
        this.notifyListeners(errorInfo);
        
        // Send to server if critical
        if (this.isCriticalError(errorInfo)) {
            this.reportToServer(errorInfo);
        }
        
        // Show user notification for certain errors
        if (this.shouldNotifyUser(errorInfo)) {
            this.showUserNotification(errorInfo);
        }
    }
    
    /**
     * Normalize error object
     * @private
     * @param {any} error - Error to normalize
     * @returns {Object} - Normalized error object
     */
    normalizeError(error) {
        if (error instanceof Error) {
            return {
                type: error.constructor.name,
                message: error.message,
                stack: error.stack,
                code: error.code,
                statusCode: error.status || error.statusCode
            };
        }
        
        if (typeof error === 'object' && error !== null) {
            return {
                type: error.type || 'Error',
                message: error.message || JSON.stringify(error),
                ...error
            };
        }
        
        return {
            type: 'Error',
            message: String(error)
        };
    }
    
    /**
     * Store error in memory
     * @private
     * @param {Object} errorInfo - Error information
     */
    storeError(errorInfo) {
        this.errors.push(errorInfo);
        
        // Limit stored errors
        if (this.errors.length > this.maxErrors) {
            this.errors.shift();
        }
        
        // Store in session storage for debugging
        if (window.AppConfig?.dev?.debug) {
            try {
                const stored = window.sessionStorage.getItem('mcp_errors') || '[]';
                const errors = JSON.parse(stored);
                errors.push(errorInfo);
                
                // Keep only last 50 errors in storage
                if (errors.length > 50) {
                    errors.splice(0, errors.length - 50);
                }
                
                window.sessionStorage.setItem('mcp_errors', JSON.stringify(errors));
            } catch (e) {
                // Storage failed, ignore
            }
        }
    }
    
    /**
     * Log error to console
     * @private
     * @param {Object} errorInfo - Error information
     */
    logError(errorInfo) {
        if (window.Logger) {
            window.Logger.error('Error occurred:', errorInfo);
        } else {
            console.error('Error occurred:', errorInfo);
        }
    }
    
    /**
     * Check if error is critical
     * @private
     * @param {Object} errorInfo - Error information
     * @returns {boolean} - True if critical
     */
    isCriticalError(errorInfo) {
        // Network errors
        if (errorInfo.type === 'NetworkError') return true;
        
        // Authentication errors
        if (errorInfo.statusCode === 401 || errorInfo.statusCode === 403) return true;
        
        // Server errors
        if (errorInfo.statusCode >= 500) return true;
        
        // Security errors
        if (errorInfo.message && errorInfo.message.includes('SecurityError')) return true;
        
        return false;
    }
    
    /**
     * Check if user should be notified
     * @private
     * @param {Object} errorInfo - Error information
     * @returns {boolean} - True if should notify
     */
    shouldNotifyUser(errorInfo) {
        // Don't notify for console errors in development
        if (window.AppConfig?.dev?.debug && errorInfo.type === 'uncaught') {
            return false;
        }
        
        // Notify for network errors
        if (errorInfo.type === 'NetworkError') return true;
        
        // Notify for auth errors
        if (errorInfo.statusCode === 401) return true;
        
        // Notify for server errors
        if (errorInfo.statusCode >= 500) return true;
        
        return false;
    }
    
    /**
     * Show user notification
     * @private
     * @param {Object} errorInfo - Error information
     */
    showUserNotification(errorInfo) {
        let message = 'An error occurred';
        let type = 'error';
        
        if (errorInfo.statusCode === 401) {
            message = 'Authentication required. Please log in.';
        } else if (errorInfo.statusCode >= 500) {
            message = 'Server error. Please try again later.';
        } else if (errorInfo.type === 'NetworkError') {
            message = 'Network error. Please check your connection.';
        } else if (errorInfo.message) {
            message = errorInfo.message;
        }
        
        // Use Utils.showToast if available
        if (window.Utils?.showToast) {
            window.Utils.showToast(message, type, 5000);
        } else {
            // Fallback to console
            console.error(message);
        }
    }
    
    /**
     * Report error to server
     * @private
     * @param {Object} errorInfo - Error information
     */
    async reportToServer(errorInfo) {
        // Don't report in development unless explicitly enabled
        if (window.AppConfig?.dev?.debug && !window.AppConfig?.dev?.reportErrors) {
            return;
        }
        
        try {
            // Sanitize error info before sending
            const sanitized = {
                type: errorInfo.type,
                message: errorInfo.message?.substring(0, 500),
                url: errorInfo.url,
                timestamp: errorInfo.timestamp,
                userAgent: errorInfo.userAgent?.substring(0, 200),
                context: JSON.stringify(errorInfo.context).substring(0, 1000)
            };
            
            // Send to error reporting endpoint if available
            if (window.sharedApiClient) {
                await window.sharedApiClient.post('/errors/report', sanitized);
            }
        } catch (e) {
            // Error reporting failed, log locally
            console.error('Failed to report error to server:', e);
        }
    }
    
    /**
     * Add error listener
     * @param {Function} listener - Listener function
     * @returns {Function} - Unsubscribe function
     */
    addListener(listener) {
        this.errorListeners.add(listener);
        return () => this.errorListeners.delete(listener);
    }
    
    /**
     * Notify all listeners
     * @private
     * @param {Object} errorInfo - Error information
     */
    notifyListeners(errorInfo) {
        this.errorListeners.forEach(listener => {
            try {
                listener(errorInfo);
            } catch (e) {
                console.error('Error in error listener:', e);
            }
        });
    }
    
    /**
     * Get recent errors
     * @param {number} count - Number of errors to get
     * @returns {Array} - Recent errors
     */
    getRecentErrors(count = 10) {
        return this.errors.slice(-count);
    }
    
    /**
     * Clear stored errors
     */
    clearErrors() {
        this.errors = [];
        try {
            window.sessionStorage.removeItem('mcp_errors');
        } catch (e) {
            // Ignore storage errors
        }
    }
    
    /**
     * Create error boundary wrapper
     * @param {Function} fn - Function to wrap
     * @param {Object} context - Error context
     * @returns {Function} - Wrapped function
     */
    createErrorBoundary(fn, context = {}) {
        return (...args) => {
            try {
                const result = fn.apply(this, args);
                
                // Handle async functions
                if (result && typeof result.catch === 'function') {
                    return result.catch(error => {
                        this.handleError(error, { ...context, args });
                        throw error;
                    });
                }
                
                return result;
            } catch (error) {
                this.handleError(error, { ...context, args });
                throw error;
            }
        };
    }
    
    /**
     * Wrap object methods with error boundaries
     * @param {Object} obj - Object to wrap
     * @param {Array<string>} methods - Methods to wrap
     * @param {Object} context - Error context
     */
    wrapMethods(obj, methods, context = {}) {
        methods.forEach(method => {
            if (typeof obj[method] === 'function') {
                const original = obj[method];
                obj[method] = this.createErrorBoundary(original.bind(obj), {
                    ...context,
                    method
                });
            }
        });
    }
}

// Create global error handler instance
window.errorHandler = new ErrorHandler();

// Export for modules
window.ErrorHandler = ErrorHandler;