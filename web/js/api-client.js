// API Client for making requests to the MCP Server

class APIClient {
    constructor() {
        this.baseUrl = localStorage.getItem('baseUrl') || 'http://localhost:8000';
        this.token = localStorage.getItem('authToken') || null;
        this.history = JSON.parse(localStorage.getItem('requestHistory') || '[]');
    }

    setBaseUrl(url) {
        this.baseUrl = url.replace(/\/$/, ''); // Remove trailing slash
        localStorage.setItem('baseUrl', this.baseUrl);
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('authToken', token);
        } else {
            localStorage.removeItem('authToken');
        }
    }

    getToken() {
        return this.token;
    }

    async login(username, password) {
        try {
            const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: username,
                    password: password
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            this.setToken(data.access_token);
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    async makeRequest(method, path, options = {}) {
        const startTime = Date.now();
        
        // Build full URL
        let url = `${this.baseUrl}${path}`;
        
        // Handle path parameters
        if (options.pathParams) {
            Object.entries(options.pathParams).forEach(([key, value]) => {
                url = url.replace(`{${key}}`, encodeURIComponent(value));
            });
        }
        
        // Handle query parameters
        if (options.queryParams) {
            const params = new URLSearchParams();
            Object.entries(options.queryParams).forEach(([key, value]) => {
                if (value !== '' && value !== null && value !== undefined) {
                    params.append(key, value);
                }
            });
            const queryString = params.toString();
            if (queryString) {
                url += `?${queryString}`;
            }
        }
        
        // Build headers
        const headers = {
            ...options.headers
        };
        
        // Add auth token if available
        if (this.token && !headers['Authorization']) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        // Add content-type for JSON body
        if (options.body && typeof options.body === 'object' && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }
        
        // Build request options
        const requestOptions = {
            method: method,
            headers: headers
        };
        
        // Add body if present
        if (options.body) {
            if (typeof options.body === 'object') {
                requestOptions.body = JSON.stringify(options.body);
            } else {
                requestOptions.body = options.body;
            }
        }
        
        try {
            const response = await fetch(url, requestOptions);
            const responseTime = Date.now() - startTime;
            
            // Get response data
            let responseData = null;
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
            } else {
                responseData = await response.text();
            }
            
            // Save to history
            this.addToHistory({
                method,
                path,
                url,
                status: response.status,
                statusText: response.statusText,
                responseTime,
                timestamp: new Date().toISOString(),
                success: response.ok
            });
            
            return {
                ok: response.ok,
                status: response.status,
                statusText: response.statusText,
                headers: Object.fromEntries(response.headers.entries()),
                data: responseData,
                responseTime
            };
        } catch (error) {
            // Save error to history
            this.addToHistory({
                method,
                path,
                url,
                error: error.message,
                timestamp: new Date().toISOString(),
                success: false
            });
            
            throw error;
        }
    }

    addToHistory(entry) {
        this.history.unshift(entry);
        // Keep only last 50 entries
        if (this.history.length > 50) {
            this.history = this.history.slice(0, 50);
        }
        localStorage.setItem('requestHistory', JSON.stringify(this.history));
    }

    getHistory() {
        return this.history;
    }

    clearHistory() {
        this.history = [];
        localStorage.removeItem('requestHistory');
    }

    // Helper method to test connection
    async testConnection() {
        try {
            const response = await this.makeRequest('GET', '/api/v1/health');
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    // Helper to validate token
    async validateToken() {
        if (!this.token) return false;
        
        try {
            const response = await this.makeRequest('GET', '/api/v1/auth/me');
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Export for use in other scripts
window.APIClient = APIClient;