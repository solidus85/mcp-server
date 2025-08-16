// Authentication module - handles login, token management, and auth status

class AuthManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
    }

    // Setup authentication event listeners
    setupEventListeners() {
        // Auth button
        const authBtn = document.getElementById('auth-btn');
        if (authBtn) {
            authBtn.addEventListener('click', () => {
                const modal = document.getElementById('auth-modal');
                if (modal) modal.classList.remove('hidden');
            });
        }
        
        // Auth modal buttons
        const authCancel = document.getElementById('auth-cancel');
        if (authCancel) {
            authCancel.addEventListener('click', () => {
                const modal = document.getElementById('auth-modal');
                if (modal) modal.classList.add('hidden');
            });
        }
        
        const authTokenToggle = document.getElementById('auth-token-toggle');
        if (authTokenToggle) {
            authTokenToggle.addEventListener('click', () => {
                const tokenSection = document.getElementById('auth-token-section');
                if (tokenSection) {
                    tokenSection.classList.toggle('hidden');
                    authTokenToggle.textContent = tokenSection.classList.contains('hidden') ? 'Use Token' : 'Use Login';
                }
            });
        }
        
        const authSubmit = document.getElementById('auth-submit');
        if (authSubmit) {
            authSubmit.addEventListener('click', () => this.handleAuth());
        }
    }

    // Handle authentication
    async handleAuth() {
        const tokenSection = document.getElementById('auth-token-section');
        if (!tokenSection) return;
        
        if (!tokenSection.classList.contains('hidden')) {
            // Use token directly
            const tokenInput = document.getElementById('auth-token');
            const token = tokenInput ? tokenInput.value : '';
            if (token) {
                this.apiClient.setToken(token);
                const modal = document.getElementById('auth-modal');
                if (modal) modal.classList.add('hidden');
                await this.updateAuthStatus();
            }
        } else {
            // Login with username/password
            const usernameInput = document.getElementById('auth-username');
            const passwordInput = document.getElementById('auth-password');
            const username = usernameInput ? usernameInput.value : '';
            const password = passwordInput ? passwordInput.value : '';
            
            if (username && password) {
                try {
                    await this.apiClient.login(username, password);
                    const modal = document.getElementById('auth-modal');
                    if (modal) modal.classList.add('hidden');
                    await this.updateAuthStatus();
                    
                    // Clear form
                    if (usernameInput) usernameInput.value = '';
                    if (passwordInput) passwordInput.value = '';
                } catch (error) {
                    alert(`Login failed: ${error.message}`);
                }
            }
        }
    }

    // Update auth status display
    async updateAuthStatus() {
        const indicator = document.getElementById('auth-indicator');
        const text = document.getElementById('auth-text');
        const btn = document.getElementById('auth-btn');
        
        // Return early if elements don't exist
        if (!indicator && !text && !btn) return;
        
        console.log('updateAuthStatus: Token exists?', !!this.apiClient.getToken());
        
        if (this.apiClient.getToken()) {
            console.log('updateAuthStatus: Validating token...');
            const validation = await this.apiClient.validateToken();
            console.log('updateAuthStatus: Validation result:', validation);
            
            if (validation.valid) {
                console.log('updateAuthStatus: Token is valid, showing authenticated state');
                if (indicator) indicator.className = 'w-2 h-2 bg-green-500 rounded-full auth-authenticated';
                if (text) text.textContent = 'Authenticated';
                if (btn) {
                    if (btn) btn.textContent = 'Logout';
                    if (btn) btn.onclick = () => {
                        this.apiClient.setToken(null);
                        this.updateAuthStatus();
                    };
                }
            } else {
                console.log('updateAuthStatus: Token validation failed, reason:', validation.reason);
                // Handle different failure reasons
                if (validation.reason === 'api-offline') {
                    // API is offline - keep token but show offline status
                    if (indicator) indicator.className = 'w-2 h-2 bg-yellow-500 rounded-full';
                    if (text) text.textContent = 'API Offline';
                    if (btn) btn.textContent = 'Retry';
                    if (btn) btn.onclick = () => {
                        this.updateAuthStatus();
                        // Also trigger connection test if available
                        if (window.connectionTester) {
                            window.connectionTester();
                        }
                    };
                } else if (validation.reason === 'invalid-token') {
                    // Token is actually invalid
                    this.apiClient.setToken(null);
                    if (indicator) indicator.className = 'w-2 h-2 bg-red-500 rounded-full';
                    if (text) text.textContent = 'Token invalid';
                    if (btn) btn.textContent = 'Login';
                    if (btn) btn.onclick = () => {
                        document.getElementById('auth-modal').classList.remove('hidden');
                    };
                } else {
                    // Some other error
                    console.error('updateAuthStatus: Unknown validation failure reason:', validation);
                    if (indicator) indicator.className = 'w-2 h-2 bg-red-500 rounded-full';
                    if (text) text.textContent = 'Auth error';
                    if (btn) btn.textContent = 'Login';
                    if (btn) btn.onclick = () => {
                        document.getElementById('auth-modal').classList.remove('hidden');
                    };
                }
            }
        } else {
            console.log('updateAuthStatus: No token, showing not authenticated state');
            if (indicator) indicator.className = 'w-2 h-2 bg-red-500 rounded-full';
            if (text) text.textContent = 'Not authenticated';
            if (btn) btn.textContent = 'Login';
            if (btn) btn.onclick = () => {
                document.getElementById('auth-modal').classList.remove('hidden');
            };
        }
    }
}

// Export for use in other scripts
window.AuthManager = AuthManager;
console.log('AuthManager loaded and exported to window');