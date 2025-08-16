// Main Application Controller

class EmailViewerApp {
    constructor() {
        this.isDarkMode = Utils.storage.get('darkMode', false);
        this.connectionStatus = 'checking';
    }
    
    // Initialize the application
    async init() {
        console.log('Initializing Email Viewer...');
        
        // Apply saved theme
        this.applyTheme();
        
        // Setup theme toggle
        this.setupThemeToggle();
        
        // Setup refresh button
        this.setupRefreshButton();
        
        // Check API connection
        await this.checkConnection();
        
        // Initialize components
        threadList.init();
        emailChain.init();
        searchFilter.init();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Setup auto-refresh
        this.setupAutoRefresh();
        
        console.log('Email Viewer initialized successfully');
    }
    
    // Check API connection
    async checkConnection() {
        const statusElement = document.getElementById('connectionStatus');
        
        try {
            const isConnected = await apiClient.testConnection();
            
            if (isConnected) {
                this.connectionStatus = 'connected';
                statusElement.innerHTML = '<i class="fas fa-circle text-xs mr-1"></i>Connected';
                statusElement.className = 'text-sm px-2 py-1 rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
            } else {
                throw new Error('Connection failed');
            }
            
        } catch (error) {
            this.connectionStatus = 'disconnected';
            statusElement.innerHTML = '<i class="fas fa-circle text-xs mr-1"></i>Disconnected';
            statusElement.className = 'text-sm px-2 py-1 rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
            
            Utils.showToast('Failed to connect to API server', 'error');
            
            // Retry connection after 5 seconds
            setTimeout(() => this.checkConnection(), 5000);
        }
    }
    
    // Setup theme toggle
    setupThemeToggle() {
        const themeToggle = document.getElementById('themeToggle');
        
        themeToggle.addEventListener('click', () => {
            this.isDarkMode = !this.isDarkMode;
            Utils.storage.set('darkMode', this.isDarkMode);
            this.applyTheme();
        });
    }
    
    // Apply theme
    applyTheme() {
        if (this.isDarkMode) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }
    
    // Setup refresh button
    setupRefreshButton() {
        const refreshBtn = document.getElementById('refreshBtn');
        
        refreshBtn.addEventListener('click', async () => {
            // Add spinning animation
            const icon = refreshBtn.querySelector('i');
            icon.classList.add('fa-spin');
            
            // Refresh threads
            await threadList.refresh();
            
            // Remove spinning animation
            setTimeout(() => {
                icon.classList.remove('fa-spin');
            }, 500);
        });
    }
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            // j/k - Navigate threads
            if (e.key === 'j' || e.key === 'k') {
                this.navigateThreads(e.key === 'j' ? 'next' : 'prev');
            }
            
            // Enter - Open selected thread
            if (e.key === 'Enter') {
                this.openSelectedThread();
            }
            
            // r - Refresh
            if (e.key === 'r' && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
                document.getElementById('refreshBtn').click();
            }
            
            // / - Focus search
            if (e.key === '/') {
                e.preventDefault();
                document.getElementById('searchInput').focus();
            }
            
            // Escape - Clear search
            if (e.key === 'Escape') {
                const searchInput = document.getElementById('searchInput');
                if (searchInput.value) {
                    searchInput.value = '';
                    searchInput.dispatchEvent(new Event('input'));
                }
            }
            
            // m - Mark as read/unread
            if (e.key === 'm') {
                this.toggleReadStatus();
            }
            
            // f - Flag/unflag
            if (e.key === 'f') {
                this.toggleFlag();
            }
        });
    }
    
    // Navigate threads with keyboard
    navigateThreads(direction) {
        const threads = document.querySelectorAll('.thread-item');
        if (threads.length === 0) return;
        
        let currentIndex = -1;
        threads.forEach((thread, index) => {
            if (thread.classList.contains('active')) {
                currentIndex = index;
            }
        });
        
        let newIndex;
        if (direction === 'next') {
            newIndex = currentIndex < threads.length - 1 ? currentIndex + 1 : currentIndex;
        } else {
            newIndex = currentIndex > 0 ? currentIndex - 1 : 0;
        }
        
        if (newIndex !== currentIndex && threads[newIndex]) {
            threads[newIndex].click();
            threads[newIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    // Open selected thread
    openSelectedThread() {
        const activeThread = document.querySelector('.thread-item.active');
        if (activeThread) {
            activeThread.click();
        }
    }
    
    // Toggle read status of current email/thread
    toggleReadStatus() {
        // Implementation depends on current focus
        const activeThread = document.querySelector('.thread-item.active');
        if (activeThread) {
            const threadId = activeThread.dataset.threadId;
            threadList.markThreadAsRead(threadId);
        }
    }
    
    // Toggle flag of current email/thread
    toggleFlag() {
        // Implementation depends on current focus
        Utils.showToast('Flag toggled', 'info');
    }
    
    // Setup auto-refresh
    setupAutoRefresh() {
        // Refresh every 60 seconds if connected
        setInterval(() => {
            if (this.connectionStatus === 'connected') {
                threadList.loadThreads();
            }
        }, 60000);
    }
    
    // Handle responsive layout
    handleResponsive() {
        const sidebar = document.getElementById('threadSidebar');
        const viewer = document.getElementById('emailViewer');
        
        // Add mobile toggle button if needed
        if (window.innerWidth < 768) {
            sidebar.classList.add('hidden-mobile');
            
            // Add toggle button logic here
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const app = new EmailViewerApp();
    app.init();
    
    // Make app instance globally available for debugging
    window.emailViewerApp = app;
});