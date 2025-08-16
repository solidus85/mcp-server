// Application Configuration
// Central configuration for the MCP Server Web Application

const AppConfig = {
    // API Configuration
    api: {
        protocol: 'http',
        host: 'localhost',
        port: 8010,
        basePath: '/api/v1',
        get baseUrl() {
            return `${this.protocol}://${this.host}:${this.port}${this.basePath}`;
        }
    },

    // Authentication Configuration
    auth: {
        tokenKey: 'authToken',
        userKey: 'currentUser',
        defaultToken: 'my-personal-api-token-12345',
        tokenExpiry: 30 * 60 * 1000, // 30 minutes in milliseconds
    },

    // Module Configuration
    modules: {
        defaultModule: 'api-tester',
        enabledModules: ['api-tester', 'email-viewer'],
        lazyLoad: true,
    },

    // UI Configuration
    ui: {
        theme: 'light', // 'light' or 'dark'
        sidebarCollapsed: false,
        animationsEnabled: true,
    },

    // Storage Configuration
    storage: {
        prefix: 'mcp_',
        type: 'localStorage', // 'localStorage' or 'sessionStorage'
    },

    // Development Configuration
    dev: {
        debug: false,
        logLevel: 'info', // 'debug', 'info', 'warn', 'error'
        mockMode: false,
    }
};

// Storage utilities
const Storage = {
    get(key) {
        const storage = window[AppConfig.storage.type];
        const value = storage.getItem(AppConfig.storage.prefix + key);
        try {
            return JSON.parse(value);
        } catch {
            return value;
        }
    },

    set(key, value) {
        const storage = window[AppConfig.storage.type];
        const stringValue = typeof value === 'string' ? value : JSON.stringify(value);
        storage.setItem(AppConfig.storage.prefix + key, stringValue);
    },

    remove(key) {
        const storage = window[AppConfig.storage.type];
        storage.removeItem(AppConfig.storage.prefix + key);
    },

    clear() {
        const storage = window[AppConfig.storage.type];
        const keysToRemove = [];
        for (let i = 0; i < storage.length; i++) {
            const key = storage.key(i);
            if (key && key.startsWith(AppConfig.storage.prefix)) {
                keysToRemove.push(key);
            }
        }
        keysToRemove.forEach(key => storage.removeItem(key));
    }
};

// Logger utility
const Logger = {
    debug(...args) {
        if (AppConfig.dev.debug && ['debug'].includes(AppConfig.dev.logLevel)) {
            console.log('[DEBUG]', ...args);
        }
    },

    info(...args) {
        if (['debug', 'info'].includes(AppConfig.dev.logLevel)) {
            console.info('[INFO]', ...args);
        }
    },

    warn(...args) {
        if (['debug', 'info', 'warn'].includes(AppConfig.dev.logLevel)) {
            console.warn('[WARN]', ...args);
        }
    },

    error(...args) {
        console.error('[ERROR]', ...args);
    }
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AppConfig, Storage, Logger };
}