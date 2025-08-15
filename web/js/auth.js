// Authentication module - handles login, token management, and auth status

class AuthManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
    }

    // Setup authentication event listeners
    setupEventListeners() {
        // Auth button
        document.getElementById('auth-btn').addEventListener('click', () => {
            const modal = document.getElementById('auth-modal');
            modal.classList.remove('hidden');
        });
        
        // Auth modal buttons
        document.getElementById('auth-cancel').addEventListener('click', () => {
            document.getElementById('auth-modal').classList.add('hidden');
        });
        
        document.getElementById('auth-token-toggle').addEventListener('click', () => {
            const tokenSection = document.getElementById('auth-token-section');
            tokenSection.classList.toggle('hidden');
            const btn = document.getElementById('auth-token-toggle');
            btn.textContent = tokenSection.classList.contains('hidden') ? 'Use Token' : 'Use Login';
        });
        
        document.getElementById('auth-submit').addEventListener('click', () => this.handleAuth());
    }

    // Handle authentication
    async handleAuth() {
        const tokenSection = document.getElementById('auth-token-section');
        
        if (!tokenSection.classList.contains('hidden')) {
            // Use token directly
            const token = document.getElementById('auth-token').value;
            if (token) {
                this.apiClient.setToken(token);
                document.getElementById('auth-modal').classList.add('hidden');
                await this.updateAuthStatus();
            }
        } else {
            // Login with username/password
            const username = document.getElementById('auth-username').value;
            const password = document.getElementById('auth-password').value;
            
            try {
                await this.apiClient.login(username, password);
                document.getElementById('auth-modal').classList.add('hidden');
                await this.updateAuthStatus();
                
                // Clear form
                document.getElementById('auth-username').value = '';
                document.getElementById('auth-password').value = '';
            } catch (error) {
                alert(`Login failed: ${error.message}`);
            }
        }
    }

    // Update auth status display
    async updateAuthStatus() {
        const indicator = document.getElementById('auth-indicator');
        const text = document.getElementById('auth-text');
        const btn = document.getElementById('auth-btn');
        
        console.log('updateAuthStatus: Token exists?', !!this.apiClient.getToken());
        
        if (this.apiClient.getToken()) {
            console.log('updateAuthStatus: Validating token...');
            const validation = await this.apiClient.validateToken();
            console.log('updateAuthStatus: Validation result:', validation);
            
            if (validation.valid) {
                console.log('updateAuthStatus: Token is valid, showing authenticated state');
                indicator.className = 'w-2 h-2 bg-green-500 rounded-full auth-authenticated';
                text.textContent = 'Authenticated';
                btn.textContent = 'Logout';
                btn.onclick = () => {
                    this.apiClient.setToken(null);
                    this.updateAuthStatus();
                };
            } else {
                console.log('updateAuthStatus: Token validation failed, reason:', validation.reason);
                // Handle different failure reasons
                if (validation.reason === 'api-offline') {
                    // API is offline - keep token but show offline status
                    indicator.className = 'w-2 h-2 bg-yellow-500 rounded-full';
                    text.textContent = 'API Offline';
                    btn.textContent = 'Retry';
                    btn.onclick = () => {
                        this.updateAuthStatus();
                        // Also trigger connection test if available
                        if (window.connectionTester) {
                            window.connectionTester();
                        }
                    };
                } else if (validation.reason === 'invalid-token') {
                    // Token is actually invalid
                    this.apiClient.setToken(null);
                    indicator.className = 'w-2 h-2 bg-red-500 rounded-full';
                    text.textContent = 'Token invalid';
                    btn.textContent = 'Login';
                    btn.onclick = () => {
                        document.getElementById('auth-modal').classList.remove('hidden');
                    };
                } else {
                    // Some other error
                    console.error('updateAuthStatus: Unknown validation failure reason:', validation);
                    indicator.className = 'w-2 h-2 bg-red-500 rounded-full';
                    text.textContent = 'Auth error';
                    btn.textContent = 'Login';
                    btn.onclick = () => {
                        document.getElementById('auth-modal').classList.remove('hidden');
                    };
                }
            }
        } else {
            console.log('updateAuthStatus: No token, showing not authenticated state');
            indicator.className = 'w-2 h-2 bg-red-500 rounded-full';
            text.textContent = 'Not authenticated';
            btn.textContent = 'Login';
            btn.onclick = () => {
                document.getElementById('auth-modal').classList.remove('hidden');
            };
        }
    }
}