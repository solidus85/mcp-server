// Module Loader System
// Handles dynamic loading and lifecycle management of application modules

class ModuleLoader {
    constructor() {
        this.modules = new Map();
        this.currentModule = null;
        this.moduleContainer = null;
        this.eventBus = window.eventBus || new EventBus();
    }

    async init(containerId) {
        this.moduleContainer = document.getElementById(containerId);
        if (!this.moduleContainer) {
            throw new Error(`Module container with id '${containerId}' not found`);
        }

        // Load module registry
        await this.loadModuleRegistry();
        
        Logger.info('ModuleLoader initialized');
    }

    async loadModuleRegistry() {
        try {
            const response = await fetch('/config/modules.json');
            const registry = await response.json();
            
            this.registry = registry;
            Logger.info('Module registry loaded:', registry);
            
            return registry;
        } catch (error) {
            Logger.error('Failed to load module registry:', error);
            throw error;
        }
    }

    async loadModule(moduleId) {
        // Check if module is already loaded
        if (this.modules.has(moduleId)) {
            Logger.debug(`Module ${moduleId} already loaded`);
            return this.modules.get(moduleId);
        }

        // Find module in registry
        const moduleConfig = this.registry.modules.find(m => m.id === moduleId);
        if (!moduleConfig) {
            throw new Error(`Module ${moduleId} not found in registry`);
        }

        if (!moduleConfig.enabled) {
            throw new Error(`Module ${moduleId} is disabled`);
        }

        Logger.info(`Loading module: ${moduleId}`);

        try {
            // Create module instance
            const module = {
                id: moduleId,
                config: moduleConfig,
                instance: null,
                element: null,
                loaded: false
            };

            // Load module HTML
            const htmlPath = `${moduleConfig.path}index.html`;
            const response = await fetch(htmlPath);
            const html = await response.text();

            // Create module container
            const moduleElement = document.createElement('div');
            moduleElement.id = `module-${moduleId}`;
            moduleElement.className = 'module-content hidden';
            moduleElement.innerHTML = html;

            // Extract and execute scripts from the module HTML
            const scripts = moduleElement.querySelectorAll('script');
            const scriptPromises = [];

            scripts.forEach(script => {
                if (script.src) {
                    // External script
                    const scriptPromise = this.loadScript(script.src, moduleId);
                    scriptPromises.push(scriptPromise);
                } else {
                    // Inline script - will be executed after external scripts
                    script.setAttribute('data-module', moduleId);
                }
            });

            // Wait for external scripts to load
            await Promise.all(scriptPromises);

            // Execute inline scripts
            scripts.forEach(script => {
                if (!script.src) {
                    try {
                        // Create a new script element to execute the code
                        const newScript = document.createElement('script');
                        newScript.textContent = script.textContent;
                        newScript.setAttribute('data-module', moduleId);
                        document.head.appendChild(newScript);
                    } catch (error) {
                        Logger.error(`Error executing inline script for module ${moduleId}:`, error);
                    }
                }
            });

            // Remove script tags from module element
            scripts.forEach(script => script.remove());

            // Load module JavaScript if specified
            if (moduleConfig.entryPoint) {
                const modulePath = `${moduleConfig.path}${moduleConfig.entryPoint}`;
                try {
                    await this.loadScript(modulePath, moduleId);
                    
                    // Check if module registered itself
                    if (window[`${moduleId}Module`]) {
                        module.instance = window[`${moduleId}Module`];
                    }
                } catch (error) {
                    Logger.warn(`Module entry point not found or failed to load: ${modulePath}`);
                }
            }

            module.element = moduleElement;
            module.loaded = true;

            // Store module
            this.modules.set(moduleId, module);

            // Emit module loaded event
            this.eventBus.emit('module:loaded', { moduleId, module });

            Logger.info(`Module ${moduleId} loaded successfully`);
            return module;

        } catch (error) {
            Logger.error(`Failed to load module ${moduleId}:`, error);
            throw error;
        }
    }

    async loadScript(src, moduleId) {
        return new Promise((resolve, reject) => {
            // Check if script is already loaded
            const existingScript = document.querySelector(`script[src="${src}"]`);
            if (existingScript) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = src;
            script.setAttribute('data-module', moduleId);
            script.onload = resolve;
            script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
            document.head.appendChild(script);
        });
    }

    async switchToModule(moduleId) {
        Logger.info(`Switching to module: ${moduleId}`);

        // Deactivate current module
        if (this.currentModule) {
            await this.deactivateModule(this.currentModule);
        }

        // Load module if not already loaded
        let module = this.modules.get(moduleId);
        if (!module) {
            module = await this.loadModule(moduleId);
        }

        // Activate new module
        await this.activateModule(moduleId);

        this.currentModule = moduleId;

        // Update URL hash
        window.location.hash = `/${moduleId}`;

        // Emit module switched event
        this.eventBus.emit('module:switched', { moduleId, module });
    }

    async activateModule(moduleId) {
        const module = this.modules.get(moduleId);
        if (!module) {
            throw new Error(`Module ${moduleId} not loaded`);
        }

        Logger.debug(`Activating module: ${moduleId}`);

        // Clear container and add module element
        this.moduleContainer.innerHTML = '';
        this.moduleContainer.appendChild(module.element);

        // Show module element
        module.element.classList.remove('hidden');

        // Call module's init method if it exists
        if (module.instance && typeof module.instance.init === 'function') {
            try {
                await module.instance.init();
            } catch (error) {
                Logger.error(`Error initializing module ${moduleId}:`, error);
            }
        }

        // Emit module activated event
        this.eventBus.emit('module:activated', { moduleId, module });
    }

    async deactivateModule(moduleId) {
        const module = this.modules.get(moduleId);
        if (!module) {
            return;
        }

        Logger.debug(`Deactivating module: ${moduleId}`);

        // Call module's destroy method if it exists
        if (module.instance && typeof module.instance.destroy === 'function') {
            try {
                await module.instance.destroy();
            } catch (error) {
                Logger.error(`Error destroying module ${moduleId}:`, error);
            }
        }

        // Hide module element
        if (module.element) {
            module.element.classList.add('hidden');
        }

        // Emit module deactivated event
        this.eventBus.emit('module:deactivated', { moduleId, module });
    }

    getModule(moduleId) {
        return this.modules.get(moduleId);
    }

    getCurrentModule() {
        return this.currentModule;
    }

    getLoadedModules() {
        return Array.from(this.modules.keys());
    }

    async reloadModule(moduleId) {
        Logger.info(`Reloading module: ${moduleId}`);

        // Deactivate if current
        if (this.currentModule === moduleId) {
            await this.deactivateModule(moduleId);
        }

        // Remove from cache
        this.modules.delete(moduleId);

        // Reload
        const module = await this.loadModule(moduleId);

        // Reactivate if was current
        if (this.currentModule === moduleId) {
            await this.activateModule(moduleId);
        }

        return module;
    }
}

// Create global instance
window.moduleLoader = new ModuleLoader();