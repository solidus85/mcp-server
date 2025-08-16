// Main Application Controller

// Application state
let app = {
    authService: window.authService,
    apiClient: window.sharedApiClient,
    eventBus: window.eventBus,
    moduleLoader: window.moduleLoader,
    navigation: window.navigation
};

// Initialize application
async function initApp() {
    try {
        // Initialize module loader
        await app.moduleLoader.init('moduleContainer');
        
        // Initialize navigation
        await app.navigation.init('moduleNav');
        
        // Setup mobile navigation
        setupMobileNavigation();
        
        // Setup event listeners
        setupEventListeners();
        
        // Update auth status
        updateAuthStatus();
        
        // Test connection
        await testConnection();
        
        console.info('Application initialized successfully');
        
    } catch (error) {
        console.error('Failed to initialize application:', error);
        showNotification('error', 'Initialization Error', error.message);
    }
}

// Setup mobile navigation
function setupMobileNavigation() {
    const mobileNav = document.getElementById('mobileNav');
    const moduleNav = document.getElementById('moduleNav');
    
    if (mobileNav && moduleNav) {
        // Clone navigation for mobile
        mobileNav.innerHTML = moduleNav.innerHTML;
        
        // Update classes for mobile styling
        const navList = mobileNav.querySelector('.nav-list');
        if (navList) {
            navList.classList.remove('space-x-1');
            navList.classList.add('space-y-1', 'flex-col');
        }
    }
}

// Setup event listeners
function setupEventListeners() {
    // Theme toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Auth button
    const authButton = document.getElementById('authButton');
    if (authButton) {
        authButton.addEventListener('click', handleAuthButton);
    }
    
    // Settings button
    const settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', openSettings);
    }
    
    // Auth modal buttons
    const closeAuthBtn = document.getElementById('closeAuthModal');
    if (closeAuthBtn) {
        closeAuthBtn.addEventListener('click', closeAuthModal);
    }
    
    const showLoginBtn = document.getElementById('showLoginForm');
    if (showLoginBtn) {
        showLoginBtn.addEventListener('click', showLoginForm);
    }
    
    const showTokenBtn = document.getElementById('showTokenForm');
    if (showTokenBtn) {
        showTokenBtn.addEventListener('click', showTokenForm);
    }
    
    const performLoginBtn = document.getElementById('performLoginBtn');
    if (performLoginBtn) {
        performLoginBtn.addEventListener('click', performLogin);
    }
    
    const setTokenBtn = document.getElementById('setTokenBtn');
    if (setTokenBtn) {
        setTokenBtn.addEventListener('click', setApiToken);
    }
    
    // Auth events
    app.eventBus.on(ModuleEvents.AUTH_LOGIN, updateAuthStatus);
    app.eventBus.on(ModuleEvents.AUTH_LOGOUT, updateAuthStatus);
    
    // Module events
    app.eventBus.on(ModuleEvents.MODULE_LOADED, hideLoadingOverlay);
    app.eventBus.on(ModuleEvents.MODULE_ERROR, (data) => {
        hideLoadingOverlay();
        showNotification('error', 'Module Error', data.error);
    });
    
    // API events
    app.eventBus.on(ModuleEvents.API_REQUEST_START, showLoadingIndicator);
    app.eventBus.on(ModuleEvents.API_REQUEST_END, hideLoadingIndicator);
    
    // Notification events
    app.eventBus.on(ModuleEvents.UI_NOTIFICATION, (data) => {
        showNotification(data.type, data.title, data.message, data.duration);
    });
}

// Theme management
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.classList.contains('dark');
    
    if (isDark) {
        html.classList.remove('dark');
        localStorage.setItem('theme', 'light');
    } else {
        html.classList.add('dark');
        localStorage.setItem('theme', 'dark');
    }
    
    app.eventBus.emit(ModuleEvents.UI_THEME_CHANGED, { theme: isDark ? 'light' : 'dark' });
}

// Initialize theme
function initTheme() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
}

// Auth management
function updateAuthStatus() {
    const authButton = document.getElementById('authButton');
    const authUsername = document.getElementById('authUsername');
    
    if (!authButton || !authUsername) return;
    
    if (app.authService.isLoggedIn()) {
        const user = app.authService.getUser();
        authUsername.textContent = user?.username || 'Authenticated';
        authButton.textContent = 'Logout';
    } else {
        authUsername.textContent = 'Guest';
        authButton.textContent = 'Login';
    }
}

function handleAuthButton() {
    if (app.authService.isLoggedIn()) {
        app.authService.logout();
        updateAuthStatus();
        showNotification('info', 'Logged Out', 'You have been logged out successfully');
    } else {
        showAuthModal();
    }
}

function showAuthModal() {
    const authModal = document.getElementById('authModal');
    if (authModal) {
        authModal.classList.remove('hidden');
    }
}

function closeAuthModal() {
    const authModal = document.getElementById('authModal');
    if (authModal) {
        authModal.classList.add('hidden');
    }
}

function showLoginForm() {
    const loginForm = document.getElementById('loginForm');
    const tokenForm = document.getElementById('tokenForm');
    
    if (loginForm) loginForm.classList.remove('hidden');
    if (tokenForm) tokenForm.classList.add('hidden');
}

function showTokenForm() {
    const loginForm = document.getElementById('loginForm');
    const tokenForm = document.getElementById('tokenForm');
    
    if (loginForm) loginForm.classList.add('hidden');
    if (tokenForm) tokenForm.classList.remove('hidden');
}

async function performLogin() {
    const usernameInput = document.getElementById('loginUsername');
    const passwordInput = document.getElementById('loginPassword');
    
    if (!usernameInput || !passwordInput) return;
    
    const username = usernameInput.value;
    const password = passwordInput.value;
    
    if (!username || !password) {
        showNotification('error', 'Invalid Input', 'Please enter username and password');
        return;
    }
    
    try {
        await app.authService.login(username, password);
        closeAuthModal();
        updateAuthStatus();
        showNotification('success', 'Login Successful', `Welcome back, ${username}!`);
    } catch (error) {
        showNotification('error', 'Login Failed', error.message);
    }
}

function setApiToken() {
    const tokenInput = document.getElementById('apiToken');
    
    if (!tokenInput) return;
    
    const token = tokenInput.value;
    
    if (!token) {
        showNotification('error', 'Invalid Input', 'Please enter an API token');
        return;
    }
    
    app.authService.setToken(token);
    closeAuthModal();
    updateAuthStatus();
    showNotification('success', 'Token Set', 'API token has been set successfully');
}

// Connection testing
async function testConnection() {
    try {
        await app.apiClient.get('/health');
        setConnectionStatus('connected');
    } catch (error) {
        setConnectionStatus('disconnected');
        if (typeof Logger !== 'undefined') Logger.warn('API connection failed:', error);
    }
}

function setConnectionStatus(status) {
    const statusElement = document.getElementById('connectionStatus');
    if (!statusElement) {
        console.warn('Connection status element not found');
        return;
    }
    
    const icon = statusElement.querySelector('i');
    const text = statusElement.querySelector('span');
    
    if (!icon || !text) {
        console.warn('Connection status icon or text not found');
        return;
    }
    
    if (status === 'connected') {
        statusElement.className = 'flex items-center space-x-2 px-3 py-1 rounded-full bg-green-100 dark:bg-green-900';
        icon.className = 'fas fa-circle text-xs text-green-500';
        text.className = 'text-sm text-green-800 dark:text-green-200';
        text.textContent = 'Connected';
    } else {
        statusElement.className = 'flex items-center space-x-2 px-3 py-1 rounded-full bg-red-100 dark:bg-red-900';
        icon.className = 'fas fa-circle text-xs text-red-500';
        text.className = 'text-sm text-red-800 dark:text-red-200';
        text.textContent = 'Disconnected';
    }
}

// Settings
function openSettings() {
    showNotification('info', 'Settings', 'Settings panel coming soon!');
}

// Loading indicators
let loadingCount = 0;

function showLoadingIndicator() {
    loadingCount++;
    if (loadingCount === 1) {
        // Show subtle loading indicator
        // Could add a progress bar or spinner here
    }
}

function hideLoadingIndicator() {
    loadingCount = Math.max(0, loadingCount - 1);
    if (loadingCount === 0) {
        // Hide loading indicator
    }
}

function showLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('hidden');
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

// Notifications
function showNotification(type, title, message, duration = 5000) {
    const container = document.getElementById('notificationContainer');
    
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification p-4 rounded-lg shadow-lg max-w-sm animate-slide-in`;
    
    // Set color based on type
    const colors = {
        success: 'bg-green-500 text-white',
        error: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-white',
        info: 'bg-blue-500 text-white'
    };
    
    notification.classList.add(...(colors[type] || colors.info).split(' '));
    
    notification.innerHTML = `
        <div class="flex items-start space-x-3">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <div class="flex-1">
                <h4 class="font-semibold">${title}</h4>
                <p class="text-sm opacity-90">${message}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="text-white opacity-75 hover:opacity-100">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Auto remove after duration
    setTimeout(() => {
        notification.classList.add('animate-slide-out');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Initialize theme and app on load
initTheme();

// Start app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

// Periodic connection check
setInterval(testConnection, 30000);

// Export functions for global use
window.showNotification = showNotification;
window.showAuthModal = showAuthModal;
window.closeAuthModal = closeAuthModal;
window.showLoginForm = showLoginForm;
window.showTokenForm = showTokenForm;
window.performLogin = performLogin;
window.setApiToken = setApiToken;