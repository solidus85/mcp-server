// Shared Authentication Service
// Centralized authentication management for all modules

class AuthService {
    constructor() {
        this.token = null;
        this.user = null;
        this.isAuthenticated = false;
        this.eventBus = window.eventBus || new EventBus();
        this.storage = window.Storage;
        this.config = window.AppConfig.auth;
        
        // Initialize from storage
        this.loadFromwindow.Storage();
    }

    // Initialize authentication state from storage
    loadFromwindow.Storage() {
        const storedToken = this.storage.get(this.config.tokenKey);
        const storedUser = this.storage.get(this.config.userKey);

        if (storedToken) {
            this.token = storedToken;
            this.isAuthenticated = true;
            
            if (storedUser) {
                this.user = storedUser;
            }

            // Check if token is expired
            if (this.isTokenExpired()) {
                window.Logger.warn('Stored token is expired');
                this.logout();
            } else {
                window.Logger.info('Authentication restored from storage');
                this.eventBus.emit(ModuleEvents.AUTH_LOGIN, { user: this.user });
            }
        } else {
            // Try default token if configured
            if (this.config.defaultToken) {
                this.token = this.config.defaultToken;
                this.isAuthenticated = true;
                window.Logger.info('Using default authentication token');
            }
        }
    }

    // Login with username and password
    async login(username, password) {
        try {
            const response = await fetch(`${window.AppConfig.api.baseUrl}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            
            // Store authentication data
            this.setAuthData(data.access_token, data.user);

            window.Logger.info('Login successful');
            return { success: true, user: this.user };

        } catch (error) {
            window.Logger.error('Login failed:', error);
            throw error;
        }
    }

    // Register a new user
    async register(username, email, password) {
        try {
            const response = await fetch(`${window.AppConfig.api.baseUrl}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, email, password })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }

            const data = await response.json();
            
            window.Logger.info('Registration successful');
            return { success: true, user: data };

        } catch (error) {
            window.Logger.error('Registration failed:', error);
            throw error;
        }
    }

    // Set authentication data
    setAuthData(token, user = null) {
        this.token = token;
        this.user = user;
        this.isAuthenticated = true;

        // Store in local storage
        this.storage.set(this.config.tokenKey, token);
        if (user) {
            this.storage.set(this.config.userKey, user);
        }

        // Set token expiry
        const expiryTime = Date.now() + this.config.tokenExpiry;
        this.storage.set('tokenExpiry', expiryTime);

        // Emit login event
        this.eventBus.emit(ModuleEvents.AUTH_LOGIN, { user, token });
    }

    // Set token directly (for manual token entry)
    setToken(token) {
        this.setAuthData(token);
        window.Logger.info('Token set manually');
    }

    // Logout
    logout() {
        this.token = null;
        this.user = null;
        this.isAuthenticated = false;

        // Clear storage
        this.storage.remove(this.config.tokenKey);
        this.storage.remove(this.config.userKey);
        this.storage.remove('tokenExpiry');

        // Emit logout event
        this.eventBus.emit(ModuleEvents.AUTH_LOGOUT);

        window.Logger.info('Logged out');
    }

    // Get current token
    getToken() {
        return this.token;
    }

    // Get current user
    getUser() {
        return this.user;
    }

    // Check if authenticated
    isLoggedIn() {
        return this.isAuthenticated && !this.isTokenExpired();
    }

    // Check if token is expired
    isTokenExpired() {
        const expiry = this.storage.get('tokenExpiry');
        if (!expiry) {
            return false; // No expiry set, assume valid
        }
        return Date.now() > expiry;
    }

    // Refresh token
    async refreshToken() {
        if (!this.token) {
            throw new Error('No token to refresh');
        }

        try {
            const response = await fetch(`${window.AppConfig.api.baseUrl}/auth/refresh`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const data = await response.json();
            
            // Update token
            this.setAuthData(data.access_token, this.user);
            
            // Emit refresh event
            this.eventBus.emit(ModuleEvents.AUTH_TOKEN_REFRESHED, { token: data.access_token });

            window.Logger.info('Token refreshed successfully');
            return data.access_token;

        } catch (error) {
            window.Logger.error('Token refresh failed:', error);
            
            // Emit token expired event
            this.eventBus.emit(ModuleEvents.AUTH_TOKEN_EXPIRED);
            
            // Logout on refresh failure
            this.logout();
            throw error;
        }
    }

    // Get authorization headers
    getAuthHeaders() {
        if (!this.token) {
            return {};
        }

        return {
            'Authorization': `Bearer ${this.token}`
        };
    }

    // Verify current token with server
    async verifyToken() {
        if (!this.token) {
            return false;
        }

        try {
            const response = await fetch(`${window.AppConfig.api.baseUrl}/auth/verify`, {
                method: 'GET',
                headers: this.getAuthHeaders()
            });

            return response.ok;

        } catch (error) {
            window.Logger.error('Token verification failed:', error);
            return false;
        }
    }

    // Get user profile
    async getProfile() {
        if (!this.isLoggedIn()) {
            throw new Error('Not authenticated');
        }

        try {
            const response = await fetch(`${window.AppConfig.api.baseUrl}/auth/profile`, {
                method: 'GET',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to fetch profile');
            }

            const profile = await response.json();
            
            // Update stored user data
            this.user = profile;
            this.storage.set(this.config.userKey, profile);

            return profile;

        } catch (error) {
            window.Logger.error('Failed to fetch profile:', error);
            throw error;
        }
    }

    // Update user profile
    async updateProfile(updates) {
        if (!this.isLoggedIn()) {
            throw new Error('Not authenticated');
        }

        try {
            const response = await fetch(`${window.AppConfig.api.baseUrl}/auth/profile`, {
                method: 'PATCH',
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (!response.ok) {
                throw new Error('Failed to update profile');
            }

            const profile = await response.json();
            
            // Update stored user data
            this.user = profile;
            this.storage.set(this.config.userKey, profile);

            return profile;

        } catch (error) {
            window.Logger.error('Failed to update profile:', error);
            throw error;
        }
    }

    // Setup auto-refresh timer
    setupAutoRefresh() {
        // Clear existing timer
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        // Set up new timer (refresh 5 minutes before expiry)
        const refreshInterval = this.config.tokenExpiry - (5 * 60 * 1000);
        
        this.refreshTimer = setInterval(async () => {
            if (this.isLoggedIn() && this.isTokenExpired()) {
                try {
                    await this.refreshToken();
                } catch (error) {
                    window.Logger.error('Auto-refresh failed:', error);
                }
            }
        }, refreshInterval);
    }

    // Clear auto-refresh timer
    clearAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }
}

// Create global auth service instance
window.authService = new AuthService();

// Setup auto-refresh
window.authService.setupAutoRefresh();