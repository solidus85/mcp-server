// Main application logic for MCP Server API Tester - Modularized version

// Global instances
let apiClient;
let uiBuilder;
let authManager;
let endpointsManager;
let requestBuilder;
let responseHandler;
let uiHelpers;

// Initialize function that can be called directly
async function initApiTesterApp() {
    // Initialize core services (these are defined in external scripts)
    apiClient = new APIClient();
    uiBuilder = new UIBuilder();
    
    // Initialize modules
    authManager = new AuthManager(apiClient);
    endpointsManager = new EndpointsManager(uiBuilder);
    requestBuilder = new RequestBuilder(apiClient, uiBuilder, endpointsManager);
    responseHandler = new ResponseHandler(apiClient, uiBuilder);
    uiHelpers = new UIHelpers(apiClient);
    
    // Make requestBuilder globally accessible for inline onclick handlers
    window.requestBuilder = requestBuilder;
    
    // Initialize all modules
    uiHelpers.init();
    authManager.setupEventListeners();
    requestBuilder.init();
    responseHandler.init();
    endpointsManager.setupSearch();
    
    // Load OpenAPI spec and setup endpoints
    try {
        await endpointsManager.loadOpenApiSpec();
    } catch (error) {
        console.error('Failed to initialize application:', error);
    }
    
    // Update auth status
    await authManager.updateAuthStatus();
    
    // Test initial connection
    await uiHelpers.testConnection();
}

// Initialize on DOMContentLoaded if running standalone
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApiTesterApp);
} else {
    // DOM is already loaded, initialize immediately
    initApiTesterApp();
}