// Email Viewer Module
// Module wrapper for the email viewing functionality

class EmailViewerModule {
    constructor() {
        this.name = 'Email Viewer';
        this.id = 'email-viewer';
        this.initialized = false;
        this.eventBus = window.eventBus;
        this.authService = window.authService;
        this.apiClient = window.sharedApiClient;
        this.emailApp = null;
    }

    async init() {
        if (this.initialized) {
            Logger.debug('Email Viewer module already initialized');
            return;
        }

        Logger.info('Initializing Email Viewer module');

        try {
            // Update the API client to use shared configuration
            this.patchApiClient();
            
            // Initialize email viewer components
            await this.initializeComponents();

            // Setup event listeners
            this.setupEventListeners();

            // Load initial data
            await this.loadInitialData();

            this.initialized = true;
            Logger.info('Email Viewer module initialized successfully');

        } catch (error) {
            Logger.error('Failed to initialize Email Viewer module:', error);
            throw error;
        }
    }

    patchApiClient() {
        // Update the email viewer's API client to use shared config
        if (window.ApiClient) {
            // Save original if needed
            window.OriginalEmailApiClient = window.ApiClient;
        }

        // Create new API client for email module
        window.apiClient = {
            baseUrl: AppConfig.api.baseUrl,
            authToken: this.authService.getToken(),
            headers: {
                'Authorization': `Bearer ${this.authService.getToken()}`,
                'Content-Type': 'application/json'
            },

            setAuthToken: (token) => {
                window.apiClient.authToken = token;
                window.apiClient.headers['Authorization'] = `Bearer ${token}`;
            },

            fetchApi: async (endpoint, options = {}) => {
                return this.apiClient.fetch(endpoint, options);
            },

            getEmails: async (page = 1, size = 50, filters = {}) => {
                return this.apiClient.get('/emails/', { page, size, ...filters });
            },

            getEmail: async (emailId) => {
                return this.apiClient.get(`/emails/${emailId}`);
            },

            getThreadEmails: async (threadId) => {
                return this.apiClient.get(`/emails/thread/${threadId}`);
            },

            searchEmails: async (query, filters = {}) => {
                return this.apiClient.get('/emails/search', { q: query, ...filters });
            },

            updateEmail: async (emailId, updates) => {
                return this.apiClient.patch(`/emails/${emailId}`, updates);
            },

            markAsRead: async (emailId) => {
                return this.apiClient.post(`/emails/${emailId}/mark-read`);
            },

            markAsUnread: async (emailId) => {
                return this.apiClient.post(`/emails/${emailId}/mark-unread`);
            },

            flagEmail: async (emailId) => {
                return this.apiClient.post(`/emails/${emailId}/flag`);
            },

            unflagEmail: async (emailId) => {
                return this.apiClient.post(`/emails/${emailId}/unflag`);
            },

            deleteEmail: async (emailId) => {
                return this.apiClient.delete(`/emails/${emailId}`);
            },

            bulkUpdateEmails: async (emailIds, updates) => {
                return this.apiClient.post('/emails/bulk-update', {
                    email_ids: emailIds,
                    update: updates
                });
            },

            getEmailStats: async () => {
                return this.apiClient.get('/emails/stats/overall');
            },

            getProjects: async () => {
                return this.apiClient.get('/projects/');
            },

            getPeople: async () => {
                return this.apiClient.get('/people/');
            },

            testConnection: async () => {
                try {
                    await this.apiClient.get('/health');
                    return true;
                } catch (error) {
                    return false;
                }
            }
        };

        // Update token when auth changes
        if (this.authService.isLoggedIn()) {
            window.apiClient.setAuthToken(this.authService.getToken());
        }
    }

    async initializeComponents() {
        // Check if email viewer app exists
        if (typeof EmailApp !== 'undefined') {
            this.emailApp = new EmailApp();
            await this.emailApp.init();
        } else if (typeof initEmailViewer === 'function') {
            await initEmailViewer();
        }

        // Initialize any other components
        if (typeof ThreadList !== 'undefined') {
            window.threadList = new ThreadList();
        }

        if (typeof EmailChain !== 'undefined') {
            window.emailChain = new EmailChain();
        }

        if (typeof SearchFilter !== 'undefined') {
            window.searchFilter = new SearchFilter();
        }
    }

    setupEventListeners() {
        // Listen for auth changes
        this.eventBus.on(ModuleEvents.AUTH_LOGIN, () => {
            this.onAuthChange();
        });

        this.eventBus.on(ModuleEvents.AUTH_LOGOUT, () => {
            this.onAuthChange();
        });

        // Listen for data refresh events
        this.eventBus.on('emails:refresh', () => {
            this.refreshEmails();
        });

        // Setup refresh button if exists
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn && !refreshBtn.hasAttribute('data-listener-attached')) {
            refreshBtn.addEventListener('click', () => this.refreshEmails());
            refreshBtn.setAttribute('data-listener-attached', 'true');
        }

        // Setup search input if exists
        const searchInput = document.getElementById('searchInput');
        if (searchInput && !searchInput.hasAttribute('data-listener-attached')) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
            searchInput.setAttribute('data-listener-attached', 'true');
        }
    }

    onAuthChange() {
        // Update API client token
        if (this.authService.isLoggedIn()) {
            window.apiClient.setAuthToken(this.authService.getToken());
        }

        // Reload emails
        this.refreshEmails();
    }

    async loadInitialData() {
        try {
            // Test connection
            const connected = await window.apiClient.testConnection();
            this.updateConnectionStatus(connected);

            if (connected) {
                // Load emails
                await this.loadEmails();
            }

        } catch (error) {
            Logger.error('Failed to load initial data:', error);
            this.eventBus.emit(ModuleEvents.UI_NOTIFICATION, {
                type: 'error',
                title: 'Load Error',
                message: 'Failed to load emails'
            });
        }
    }

    async loadEmails() {
        if (typeof window.threadList !== 'undefined' && window.threadList.loadThreads) {
            await window.threadList.loadThreads();
        } else {
            // Fallback: direct API call
            try {
                const emails = await window.apiClient.getEmails();
                Logger.info('Emails loaded:', emails);
            } catch (error) {
                Logger.error('Failed to load emails:', error);
            }
        }
    }

    async refreshEmails() {
        Logger.info('Refreshing emails');
        await this.loadEmails();
        
        this.eventBus.emit(ModuleEvents.UI_NOTIFICATION, {
            type: 'info',
            title: 'Refreshed',
            message: 'Email list updated',
            duration: 2000
        });
    }

    handleSearch(query) {
        if (typeof window.searchFilter !== 'undefined' && window.searchFilter.applySearch) {
            window.searchFilter.applySearch(query);
        }
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            if (connected) {
                statusElement.innerHTML = '<i class="fas fa-circle text-xs mr-1"></i>Connected';
                statusElement.className = 'text-sm px-2 py-1 rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
            } else {
                statusElement.innerHTML = '<i class="fas fa-circle text-xs mr-1"></i>Disconnected';
                statusElement.className = 'text-sm px-2 py-1 rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
            }
        }
    }

    async destroy() {
        Logger.info('Destroying Email Viewer module');
        
        // Clean up event listeners
        this.eventBus.off(ModuleEvents.AUTH_LOGIN);
        this.eventBus.off(ModuleEvents.AUTH_LOGOUT);
        this.eventBus.off('emails:refresh');

        // Clean up components
        if (this.emailApp && typeof this.emailApp.destroy === 'function') {
            this.emailApp.destroy();
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
window['email-viewerModule'] = new EmailViewerModule();

Logger.info('Email Viewer module loaded');