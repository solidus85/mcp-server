// UI helpers module - handles theme, base URL, connection testing, and other UI utilities

class UIHelpers {
    constructor(apiClient) {
        this.apiClient = apiClient;
    }

    // Initialize UI helpers
    init() {
        this.setupTheme();
        this.updateBaseUrl();
        this.setupBaseUrlListener();
        
        // Make connection tester globally available for auth module
        window.connectionTester = () => this.testConnection();
    }

    // Setup theme toggle
    setupTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        if (savedTheme === 'dark') {
            document.documentElement.classList.add('dark');
        }
        
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                document.documentElement.classList.toggle('dark');
                const newTheme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
                localStorage.setItem('theme', newTheme);
            });
        }
    }

    // Update base URL from saved value
    updateBaseUrl() {
        const savedUrl = localStorage.getItem('baseUrl');
        // If the saved URL is the old default, update it to the new one
        if (savedUrl === 'http://localhost:8000') {
            localStorage.setItem('baseUrl', 'http://localhost:8010');
            const baseUrlInput = document.getElementById('base-url');
            if (baseUrlInput) baseUrlInput.value = 'http://localhost:8010';
            this.apiClient.setBaseUrl('http://localhost:8010');
        } else if (savedUrl) {
            const baseUrlInput = document.getElementById('base-url');
            if (baseUrlInput) baseUrlInput.value = savedUrl;
        }
        // If no saved URL, the HTML default (8010) will be used
    }

    // Setup base URL change listener
    setupBaseUrlListener() {
        const baseUrlInput = document.getElementById('base-url');
        if (baseUrlInput) {
            baseUrlInput.addEventListener('change', (e) => {
            this.apiClient.setBaseUrl(e.target.value);
                this.testConnection();
            });
        }
    }

    // Test connection to server
    async testConnection() {
        const isConnected = await this.apiClient.testConnection();
        const baseUrlInput = document.getElementById('base-url');
        
        if (baseUrlInput && isConnected) {
            baseUrlInput.classList.remove('border-red-500');
            baseUrlInput.classList.add('border-green-500');
        } else if (baseUrlInput) {
            baseUrlInput.classList.remove('border-green-500');
            baseUrlInput.classList.add('border-red-500');
        }
        
        return isConnected;
    }
}

// Export for use in other scripts
window.UIHelpers = UIHelpers;