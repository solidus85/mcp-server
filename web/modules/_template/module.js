// Module Template
// Replace 'ModuleName' with your actual module name

class ModuleNameModule {
    constructor() {
        this.name = 'Module Name';
        this.id = 'module-id';
        this.version = '1.0.0';
        this.initialized = false;
        
        // Access to shared services
        this.eventBus = window.eventBus;
        this.authService = window.authService;
        this.apiClient = window.sharedApiClient;
        this.storage = Storage;
        this.logger = Logger;
        
        // Module-specific properties
        this.config = {};
        this.state = {};
    }

    /**
     * Initialize the module
     * Called when the module is activated
     */
    async init() {
        if (this.initialized) {
            this.logger.debug(`${this.name} module already initialized`);
            return;
        }

        this.logger.info(`Initializing ${this.name} module`);

        try {
            // Load module configuration
            this.loadConfig();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize UI components
            await this.initializeUI();
            
            // Load initial data
            await this.loadInitialData();

            this.initialized = true;
            this.logger.info(`${this.name} module initialized successfully`);

            // Emit initialization event
            this.eventBus.emit(`module:${this.id}:initialized`, { module: this });

        } catch (error) {
            this.logger.error(`Failed to initialize ${this.name} module:`, error);
            throw error;
        }
    }

    /**
     * Load module configuration
     */
    loadConfig() {
        // Load configuration from storage or use defaults
        const savedConfig = this.storage.get(`${this.id}_config`);
        this.config = {
            // Default configuration
            setting1: 'default1',
            setting2: 'default2',
            // Override with saved config
            ...savedConfig
        };
    }

    /**
     * Save module configuration
     */
    saveConfig() {
        this.storage.set(`${this.id}_config`, this.config);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for auth changes
        this.eventBus.on(ModuleEvents.AUTH_LOGIN, this.onAuthLogin.bind(this));
        this.eventBus.on(ModuleEvents.AUTH_LOGOUT, this.onAuthLogout.bind(this));
        
        // Listen for data updates
        this.eventBus.on(ModuleEvents.DATA_UPDATED, this.onDataUpdated.bind(this));
        
        // Module-specific events
        this.setupModuleEvents();
    }

    /**
     * Setup module-specific event listeners
     */
    setupModuleEvents() {
        // Add your module-specific event listeners here
        
        // Example: Button click handler
        const actionButton = document.getElementById('moduleActionButton');
        if (actionButton) {
            actionButton.addEventListener('click', () => this.handleAction());
        }
    }

    /**
     * Initialize UI components
     */
    async initializeUI() {
        // Initialize any UI components
        this.updateUIState();
        
        // Example: Setup form handlers, initialize widgets, etc.
    }

    /**
     * Update UI state based on current data
     */
    updateUIState() {
        // Update UI elements based on current state
        const statusElement = document.getElementById('moduleStatus');
        if (statusElement) {
            statusElement.textContent = this.initialized ? 'Ready' : 'Initializing...';
        }
    }

    /**
     * Load initial data for the module
     */
    async loadInitialData() {
        try {
            // Load data from API
            const data = await this.apiClient.get('/your-endpoint');
            this.processData(data);
            
        } catch (error) {
            this.logger.error('Failed to load initial data:', error);
            this.showError('Failed to load data');
        }
    }

    /**
     * Process loaded data
     */
    processData(data) {
        // Process and store data
        this.state.data = data;
        
        // Update UI with new data
        this.renderData(data);
    }

    /**
     * Render data in the UI
     */
    renderData(data) {
        // Render data in the module's UI
        const container = document.getElementById('moduleDataContainer');
        if (container) {
            // Example: Render data as a list
            container.innerHTML = data.map(item => `
                <div class="data-item">
                    <h3>${item.title}</h3>
                    <p>${item.description}</p>
                </div>
            `).join('');
        }
    }

    /**
     * Handle module actions
     */
    async handleAction() {
        this.logger.info('Module action triggered');
        
        try {
            // Perform action
            const result = await this.apiClient.post('/your-action-endpoint', {
                // Action data
            });
            
            // Handle result
            this.showSuccess('Action completed successfully');
            
            // Refresh data if needed
            await this.refreshData();
            
        } catch (error) {
            this.logger.error('Action failed:', error);
            this.showError('Action failed');
        }
    }

    /**
     * Refresh module data
     */
    async refreshData() {
        await this.loadInitialData();
        
        // Emit refresh event
        this.eventBus.emit(`module:${this.id}:refreshed`, { module: this });
    }

    /**
     * Handle authentication login
     */
    onAuthLogin(data) {
        this.logger.info('User logged in');
        // Handle auth change
        this.refreshData();
    }

    /**
     * Handle authentication logout
     */
    onAuthLogout() {
        this.logger.info('User logged out');
        // Clear sensitive data
        this.state = {};
        this.updateUIState();
    }

    /**
     * Handle data updates from other modules
     */
    onDataUpdated(data) {
        // Handle data updates if relevant to this module
        if (data.type === 'relevant-data-type') {
            this.refreshData();
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.eventBus.emit(ModuleEvents.UI_NOTIFICATION, {
            type: 'success',
            title: this.name,
            message: message,
            duration: 3000
        });
    }

    /**
     * Show error message
     */
    showError(message) {
        this.eventBus.emit(ModuleEvents.UI_NOTIFICATION, {
            type: 'error',
            title: this.name,
            message: message,
            duration: 5000
        });
    }

    /**
     * Destroy the module
     * Called when the module is deactivated
     */
    async destroy() {
        this.logger.info(`Destroying ${this.name} module`);
        
        // Clean up event listeners
        this.eventBus.off(ModuleEvents.AUTH_LOGIN, this.onAuthLogin);
        this.eventBus.off(ModuleEvents.AUTH_LOGOUT, this.onAuthLogout);
        this.eventBus.off(ModuleEvents.DATA_UPDATED, this.onDataUpdated);
        
        // Clean up module-specific resources
        this.cleanupResources();
        
        // Save current state if needed
        this.saveState();
        
        this.initialized = false;
        
        // Emit destroy event
        this.eventBus.emit(`module:${this.id}:destroyed`, { module: this });
    }

    /**
     * Clean up module resources
     */
    cleanupResources() {
        // Clean up timers, intervals, websockets, etc.
        // Example:
        // if (this.refreshTimer) {
        //     clearInterval(this.refreshTimer);
        //     this.refreshTimer = null;
        // }
    }

    /**
     * Reload the module
     */
    async reload() {
        await this.destroy();
        await this.init();
    }

    /**
     * Get module state
     * Used for persisting state across module switches
     */
    getState() {
        return {
            initialized: this.initialized,
            config: this.config,
            state: this.state
        };
    }

    /**
     * Set module state
     * Used for restoring state
     */
    setState(state) {
        if (state) {
            this.config = state.config || {};
            this.state = state.state || {};
            this.updateUIState();
        }
    }

    /**
     * Save module state to storage
     */
    saveState() {
        const state = this.getState();
        this.storage.set(`${this.id}_state`, state);
    }

    /**
     * Load module state from storage
     */
    loadState() {
        const state = this.storage.get(`${this.id}_state`);
        if (state) {
            this.setState(state);
        }
    }
}

// Register module
// Replace 'module-id' with your actual module ID
window['module-idModule'] = new ModuleNameModule();

// Log module registration
Logger.info('Module Name module loaded');