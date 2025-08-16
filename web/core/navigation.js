// Navigation System for Module Switching
// Handles routing and navigation between modules

class Navigation {
    constructor() {
        this.currentRoute = null;
        this.routes = new Map();
        this.navContainer = null;
        this.moduleLoader = window.moduleLoader;
        this.eventBus = window.eventBus;
    }

    async init(navContainerId) {
        this.navContainer = document.getElementById(navContainerId);
        if (!this.navContainer) {
            window.Logger.warn(`Navigation container with id '${navContainerId}' not found`);
        }

        // Setup hash change listener
        window.addEventListener('hashchange', () => this.handleHashChange());
        
        // Setup popstate listener for browser back/forward
        window.addEventListener('popstate', () => this.handleHashChange());

        // Load module registry and build navigation
        await this.buildNavigation();

        // Handle initial route
        this.handleInitialRoute();

        window.Logger.info('Navigation system initialized');
    }

    async buildNavigation() {
        if (!this.navContainer) {
            return;
        }

        try {
            // Get module registry
            const registry = this.moduleLoader.registry || await this.moduleLoader.loadModuleRegistry();
            
            // Clear existing navigation
            this.navContainer.innerHTML = '';

            // Create navigation items
            const navList = document.createElement('ul');
            navList.className = 'nav-list flex space-x-1';

            registry.modules
                .filter(module => module.enabled)
                .sort((a, b) => a.order - b.order)
                .forEach(module => {
                    const navItem = this.createNavItem(module);
                    navList.appendChild(navItem);
                    
                    // Register route
                    this.routes.set(module.id, module);
                });

            this.navContainer.appendChild(navList);
            
        } catch (error) {
            window.Logger.error('Failed to build navigation:', error);
        }
    }

    createNavItem(module) {
        const li = document.createElement('li');
        li.className = 'nav-item';

        const button = document.createElement('button');
        button.className = 'nav-link px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors';
        button.setAttribute('data-module', module.id);
        
        // Add icon
        if (module.icon) {
            const icon = document.createElement('i');
            icon.className = `fas ${module.icon}`;
            button.appendChild(icon);
        }

        // Add text
        const text = document.createElement('span');
        text.textContent = module.name;
        button.appendChild(text);

        // Add click handler
        button.addEventListener('click', (e) => {
            e.preventDefault();
            this.navigateTo(module.id);
        });

        // Add tooltip
        if (module.description) {
            button.title = module.description;
        }

        li.appendChild(button);
        return li;
    }

    async navigateTo(moduleId) {
        if (this.currentRoute === moduleId) {
            window.Logger.debug(`Already on module: ${moduleId}`);
            return;
        }

        window.Logger.info(`Navigating to: ${moduleId}`);

        try {
            // Update navigation UI
            this.updateNavigationUI(moduleId);

            // Switch module
            await this.moduleLoader.switchToModule(moduleId);

            // Update current route
            this.currentRoute = moduleId;

            // Emit navigation event
            this.eventBus.emit('navigation:changed', { 
                from: this.currentRoute, 
                to: moduleId 
            });

        } catch (error) {
            window.Logger.error(`Failed to navigate to module ${moduleId}:`, error);
            
            // Show error notification
            this.showNavigationError(moduleId, error);
            
            // Revert URL if navigation failed
            if (this.currentRoute) {
                window.location.hash = `/${this.currentRoute}`;
            } else {
                window.location.hash = '';
            }
        }
    }

    updateNavigationUI(activeModuleId) {
        if (!this.navContainer) {
            return;
        }

        // Remove active class from all nav items
        const navLinks = this.navContainer.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('bg-blue-500', 'text-white');
            link.classList.add('bg-gray-100', 'dark:bg-gray-700', 'text-gray-700', 'dark:text-gray-300');
        });

        // Add active class to current nav item
        const activeLink = this.navContainer.querySelector(`[data-module="${activeModuleId}"]`);
        if (activeLink) {
            activeLink.classList.remove('bg-gray-100', 'dark:bg-gray-700', 'text-gray-700', 'dark:text-gray-300');
            activeLink.classList.add('bg-blue-500', 'text-white');
        }
    }

    handleHashChange() {
        const hash = window.location.hash.slice(1); // Remove #
        const moduleId = hash.replace('/', '').split('/')[0]; // Extract module ID

        if (moduleId && this.routes.has(moduleId)) {
            this.navigateTo(moduleId);
        } else if (!moduleId) {
            // Navigate to default module
            this.navigateToDefault();
        }
    }

    handleInitialRoute() {
        const hash = window.location.hash.slice(1);
        const moduleId = hash.replace('/', '').split('/')[0];

        if (moduleId && this.routes.has(moduleId)) {
            this.navigateTo(moduleId);
        } else {
            this.navigateToDefault();
        }
    }

    async navigateToDefault() {
        const registry = this.moduleLoader.registry;
        if (registry && registry.defaultModule) {
            await this.navigateTo(registry.defaultModule);
        } else if (this.routes.size > 0) {
            // Navigate to first available module
            const firstModule = this.routes.keys().next().value;
            await this.navigateTo(firstModule);
        }
    }

    showNavigationError(moduleId, error) {
        // Emit error event for UI to handle
        this.eventBus.emit('ui:notification', {
            type: 'error',
            title: 'Navigation Error',
            message: `Failed to load module "${moduleId}": ${error.message}`,
            duration: 5000
        });
    }

    // Get current module ID
    getCurrentModule() {
        return this.currentRoute;
    }

    // Get available routes
    getRoutes() {
        return Array.from(this.routes.keys());
    }

    // Refresh navigation (e.g., after module registry changes)
    async refresh() {
        await this.buildNavigation();
        
        // Re-highlight current module
        if (this.currentRoute) {
            this.updateNavigationUI(this.currentRoute);
        }
    }

    // Add custom route handler
    addRoute(path, handler) {
        this.routes.set(path, { custom: true, handler });
    }

    // Remove custom route
    removeRoute(path) {
        const route = this.routes.get(path);
        if (route && route.custom) {
            this.routes.delete(path);
        }
    }
}

// Create global navigation instance
window.navigation = new Navigation();