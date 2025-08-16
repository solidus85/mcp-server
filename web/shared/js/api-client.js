// Shared API Client
// Centralized API communication for all modules

/**
 * SharedApiClient handles all API communications for the application
 * Features: automatic retry, token refresh, request queuing, WebSocket support
 * @class
 */
class SharedApiClient {
    constructor() {
        // Validate dependencies
        if (!window.AppConfig?.api?.baseUrl) {
            throw new Error('AppConfig.api.baseUrl is required');
        }
        
        this.baseUrl = window.AppConfig.api.baseUrl;
        this.authService = window.authService || null;
        this.eventBus = window.eventBus || null;
        this.requestQueue = [];
        this.isProcessingQueue = false;
        this.activeRequests = new Map();
        this.requestTimeout = window.AppConfig.api?.timeout || 30000;
        this.maxRetries = window.AppConfig.api?.maxRetries || 3;
    }

    // Get headers for requests
    getHeaders(additionalHeaders = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...this.authService.getAuthHeaders(),
            ...additionalHeaders
        };

        return headers;
    }

    /**
     * Generic fetch wrapper with error handling and events
     * @param {string} endpoint - API endpoint or full URL
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} - Response data
     * @throws {Error} - API errors or network errors
     */
    async fetch(endpoint, options = {}) {
        // Input validation
        if (typeof endpoint !== 'string' || !endpoint.trim()) {
            throw new Error('Invalid endpoint provided');
        }
        
        const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
        
        // Create AbortController for timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout);
        
        // Prepare options
        const fetchOptions = {
            ...options,
            headers: this.getHeaders(options.headers),
            signal: controller.signal
        };

        // Remove Content-Type for FormData
        if (options.body instanceof FormData) {
            delete fetchOptions.headers['Content-Type'];
        }

        // Emit request start event
        this.eventBus.emit(ModuleEvents.API_REQUEST_START, {
            url,
            method: fetchOptions.method || 'GET'
        });

        try {
            // Check for duplicate requests
            const requestKey = `${fetchOptions.method || 'GET'}-${url}`;
            if (this.activeRequests.has(requestKey) && fetchOptions.method === 'GET') {
                return await this.activeRequests.get(requestKey);
            }
            
            const responsePromise = fetch(url, fetchOptions);
            if (fetchOptions.method === 'GET') {
                this.activeRequests.set(requestKey, responsePromise);
            }
            
            const response = await responsePromise;

            // Handle authentication errors
            if (response.status === 401) {
                // Try to refresh token
                try {
                    await this.authService.refreshToken();
                    // Retry request with new token
                    fetchOptions.headers = this.getHeaders(options.headers);
                    const retryResponse = await fetch(url, fetchOptions);
                    return this.handleResponse(retryResponse, url);
                } catch (error) {
                    // Refresh failed, user needs to login again
                    this.eventBus.emit(ModuleEvents.AUTH_TOKEN_EXPIRED);
                    throw new Error('Authentication expired. Please login again.');
                }
            }

            return this.handleResponse(response, url);

        } catch (error) {
            // Handle abort error
            if (error.name === 'AbortError') {
                const timeoutError = new Error(`Request timeout after ${this.requestTimeout}ms`);
                timeoutError.code = 'TIMEOUT';
                throw timeoutError;
            }
            
            // Emit request error event
            if (this.eventBus) {
                this.eventBus.emit(ModuleEvents.API_REQUEST_ERROR, {
                    url,
                    error: error.message
                });
            }

            if (window.Logger) {
                window.Logger.error('API request failed:', error);
            }
            throw error;

        } finally {
            clearTimeout(timeoutId);
            
            // Clean up active requests
            const requestKey = `${fetchOptions.method || 'GET'}-${url}`;
            this.activeRequests.delete(requestKey);
            
            // Emit request end event
            if (this.eventBus) {
                this.eventBus.emit(ModuleEvents.API_REQUEST_END, { url });
            }
        }
    }

    // Handle API response
    async handleResponse(response, url) {
        const contentType = response.headers.get('content-type');
        const isJson = contentType && contentType.includes('application/json');

        let data = null;
        if (isJson) {
            data = await response.json();
        } else if (response.ok) {
            data = await response.text();
        }

        if (!response.ok) {
            const errorMessage = data?.detail || data?.message || response.statusText;
            const error = new Error(errorMessage);
            error.status = response.status;
            error.data = data;

            // Emit request error event
            this.eventBus.emit(ModuleEvents.API_REQUEST_ERROR, {
                url,
                status: response.status,
                error: errorMessage
            });

            throw error;
        }

        // Emit request success event
        this.eventBus.emit(ModuleEvents.API_REQUEST_SUCCESS, {
            url,
            status: response.status,
            data
        });

        return data;
    }

    // GET request
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;

        return this.fetch(url, {
            method: 'GET'
        });
    }

    // POST request
    async post(endpoint, data = null) {
        const options = {
            method: 'POST'
        };

        if (data) {
            if (data instanceof FormData) {
                options.body = data;
            } else {
                options.body = JSON.stringify(data);
            }
        }

        return this.fetch(endpoint, options);
    }

    // PUT request
    async put(endpoint, data = null) {
        const options = {
            method: 'PUT'
        };

        if (data) {
            if (data instanceof FormData) {
                options.body = data;
            } else {
                options.body = JSON.stringify(data);
            }
        }

        return this.fetch(endpoint, options);
    }

    // PATCH request
    async patch(endpoint, data = null) {
        const options = {
            method: 'PATCH'
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        return this.fetch(endpoint, options);
    }

    // DELETE request
    async delete(endpoint) {
        return this.fetch(endpoint, {
            method: 'DELETE'
        });
    }

    // Upload file
    async upload(endpoint, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);

        // Add additional data to form
        Object.entries(additionalData).forEach(([key, value]) => {
            formData.append(key, value);
        });

        return this.post(endpoint, formData);
    }

    // Download file
    async download(endpoint, filename = null) {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            method: 'GET',
            headers: this.authService.getAuthHeaders()
        });

        if (!response.ok) {
            throw new Error(`Download failed: ${response.statusText}`);
        }

        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename || this.getFilenameFromResponse(response) || 'download';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        return true;
    }

    // Get filename from response headers
    getFilenameFromResponse(response) {
        const disposition = response.headers.get('content-disposition');
        if (!disposition) return null;

        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches && matches[1]) {
            return matches[1].replace(/['"]/g, '');
        }

        return null;
    }

    // Batch requests
    async batch(requests) {
        const promises = requests.map(request => {
            const { method, endpoint, data } = request;
            
            switch (method.toUpperCase()) {
                case 'GET':
                    return this.get(endpoint, data);
                case 'POST':
                    return this.post(endpoint, data);
                case 'PUT':
                    return this.put(endpoint, data);
                case 'PATCH':
                    return this.patch(endpoint, data);
                case 'DELETE':
                    return this.delete(endpoint);
                default:
                    return Promise.reject(new Error(`Unknown method: ${method}`));
            }
        });

        return Promise.allSettled(promises);
    }

    // Queue request (for offline support)
    queueRequest(request) {
        this.requestQueue.push({
            ...request,
            timestamp: Date.now(),
            id: Math.random().toString(36).substr(2, 9)
        });

        window.Logger.info('Request queued:', request);
        
        // Try to process queue
        this.processQueue();
    }

    // Process queued requests
    async processQueue() {
        if (this.isProcessingQueue || this.requestQueue.length === 0) {
            return;
        }

        this.isProcessingQueue = true;

        while (this.requestQueue.length > 0) {
            const request = this.requestQueue[0];

            try {
                // Check if online
                if (!navigator.onLine) {
                    window.Logger.info('Offline, waiting to process queue');
                    break;
                }

                // Process request
                const { method, endpoint, data } = request;
                await this[method.toLowerCase()](endpoint, data);

                // Remove from queue if successful
                this.requestQueue.shift();
                window.Logger.info('Queued request processed:', request.id);

            } catch (error) {
                window.Logger.error('Failed to process queued request:', error);
                
                // If auth error, stop processing
                if (error.status === 401) {
                    break;
                }

                // Remove request after 3 retries
                if (request.retries >= 3) {
                    this.requestQueue.shift();
                } else {
                    request.retries = (request.retries || 0) + 1;
                }

                // Wait before retrying
                await new Promise(resolve => setTimeout(resolve, 5000));
            }
        }

        this.isProcessingQueue = false;
    }

    /**
     * Create WebSocket connection with automatic reconnection
     * @param {string} endpoint - WebSocket endpoint
     * @param {Object} options - WebSocket options
     * @returns {WebSocket} - WebSocket instance
     */
    createWebSocket(endpoint, options = {}) {
        if (!endpoint || typeof endpoint !== 'string') {
            throw new Error('Invalid WebSocket endpoint');
        }
        
        const wsUrl = this.baseUrl.replace(/^http/, 'ws') + endpoint;
        const token = this.authService?.getToken();
        
        // Add token to URL securely
        const url = token ? `${wsUrl}?token=${encodeURIComponent(token)}` : wsUrl;
        
        const ws = new WebSocket(url);

        // Add automatic reconnection
        let reconnectAttempts = 0;
        const maxReconnectAttempts = options.maxReconnects || 5;
        const reconnectDelay = options.reconnectDelay || 1000;
        
        ws.onopen = () => {
            reconnectAttempts = 0;
            if (window.Logger) {
                window.Logger.info('WebSocket connected:', endpoint);
            }
            if (this.eventBus) {
                this.eventBus.emit('websocket:connected', { endpoint });
            }
        };

        ws.onclose = (event) => {
            if (window.Logger) {
                window.Logger.info('WebSocket disconnected:', endpoint, event.code, event.reason);
            }
            if (this.eventBus) {
                this.eventBus.emit('websocket:disconnected', { endpoint, code: event.code, reason: event.reason });
            }
            
            // Attempt reconnection if not closed intentionally
            if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(() => {
                    if (window.Logger) {
                        window.Logger.info(`Attempting WebSocket reconnection ${reconnectAttempts}/${maxReconnectAttempts}`);
                    }
                    this.createWebSocket(endpoint, options);
                }, reconnectDelay * Math.pow(2, reconnectAttempts - 1));
            }
        };

        ws.onerror = (error) => {
            if (window.Logger) {
                window.Logger.error('WebSocket error:', error);
            }
            if (this.eventBus) {
                this.eventBus.emit('websocket:error', { endpoint, error });
            }
        };

        return ws;
    }
}

// Create global API client instance
window.sharedApiClient = new SharedApiClient();

// Setup online/offline handlers
window.addEventListener('online', () => {
    window.Logger.info('Back online, processing queued requests');
    window.sharedApiClient.processQueue();
});

window.addEventListener('offline', () => {
    window.Logger.info('Gone offline');
});