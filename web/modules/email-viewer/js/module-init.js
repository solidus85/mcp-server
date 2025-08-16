// Email Viewer Module Initialization
// This file manages the module's initialization and cleanup

(function() {
    'use strict';
    
    // Module namespace
    window.EmailViewerModule = window.EmailViewerModule || {};
    
    // Initialize function
    window.EmailViewerModule.initialize = function() {
        console.log('Initializing Email Viewer Module components...');
        
        // Check if components exist and initialize them
        if (window.threadList && window.threadList.init) {
            window.threadList.init();
        }
        
        if (window.emailChain && window.emailChain.init) {
            window.emailChain.init();
        }
        
        if (window.searchFilter && window.searchFilter.init) {
            window.searchFilter.init();
        }
        
        // Initialize the main app if it exists
        if (window.emailViewerApp && window.emailViewerApp.init) {
            window.emailViewerApp.init();
        }
    };
    
    // Cleanup function
    window.EmailViewerModule.cleanup = function() {
        console.log('Cleaning up Email Viewer Module...');
        
        // Clear any intervals or timeouts
        // Remove event listeners if needed
        
        // Don't delete the apiClient as it might be needed for other operations
    };
    
    // Auto-initialize if DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.EmailViewerModule.initialize);
    } else {
        // DOM is already loaded
        setTimeout(window.EmailViewerModule.initialize, 0);
    }
})();