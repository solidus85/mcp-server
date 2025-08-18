// API Tester Module
// Module wrapper for the API testing functionality

class ApiTesterModule {
    constructor() {
        this.name = 'API Tester';
        this.id = 'api-tester';
        this.initialized = false;
        this.eventBus = window.eventBus;
        this.authService = window.authService;
        this.apiClient = window.sharedApiClient;
    }

    async init() {
        if (this.initialized) {
            window.Logger.debug('API Tester module already initialized');
            return;
        }

        window.Logger.info('Initializing API Tester module');

        try {
            // Update paths in the module's scripts to use shared services
            this.patchApiClient();
            
            // Initialize the original app.js if it exists
            if (typeof initApiTester === 'function') {
                await initApiTester();
            }

            // Setup event listeners
            this.setupEventListeners();

            this.initialized = true;
            window.Logger.info('API Tester module initialized successfully');

        } catch (error) {
            window.Logger.error('Failed to initialize API Tester module:', error);
            throw error;
        }
    }

    patchApiClient() {
        // Override the module's API client with the shared one
        if (window.APIClient) {
            // Save original if needed
            window.OriginalAPIClient = window.APIClient;
            
            // Create a wrapper that uses shared client
            window.APIClient = class {
                constructor() {
                    return window.sharedApiClient;
                }
            };
        }

        // Ensure global apiClient uses shared instance
        window.apiClient = window.sharedApiClient;
    }

    setupEventListeners() {
        // Listen for auth changes
        this.eventBus.on(ModuleEvents.AUTH_LOGIN, () => {
            this.onAuthChange();
        });

        this.eventBus.on(ModuleEvents.AUTH_LOGOUT, () => {
            this.onAuthChange();
        });
    }

    onAuthChange() {
        // Update auth status in the module if needed
        if (typeof updateAuthStatus === 'function') {
            updateAuthStatus();
        }
    }

    async destroy() {
        window.Logger.info('Destroying API Tester module');
        
        // Clean up event listeners
        this.eventBus.off(ModuleEvents.AUTH_LOGIN);
        this.eventBus.off(ModuleEvents.AUTH_LOGOUT);

        // Clean up any module-specific resources
        if (typeof cleanupApiTester === 'function') {
            cleanupApiTester();
        }

        this.initialized = false;
    }

    // Module interface methods
    async reload() {
        await this.destroy();
        await this.init();
    }

    getState() {
        return {
            initialized: this.initialized,
            // Add any module-specific state
        };
    }

    setState(state) {
        // Restore module state if needed
    }
}

// Register module
window['api-testerModule'] = new ApiTesterModule();

// Make initialization function available globally for backward compatibility
window.initApiTester = async function() {
    // Original initialization code from app.js
    // This will be called by the module's init method
    
    // Check if the original app.js functions exist
    if (typeof document !== 'undefined' && document.readyState === 'loading') {
        // Wait for DOM if still loading
        return new Promise((resolve) => {
            document.addEventListener('DOMContentLoaded', resolve);
        });
    }
};

window.Logger.info('API Tester module loaded');