# Module Template

This is a template for creating new modules in the MCP Server Web Application.

## Quick Start

1. **Copy this template folder** to create your new module:
   ```bash
   cp -r modules/_template modules/your-module-name
   ```

2. **Update the manifest.json** file with your module's information:
   - `id`: Unique identifier for your module (e.g., "data-analyzer")
   - `name`: Display name (e.g., "Data Analyzer")
   - `description`: Brief description of what your module does
   - `icon`: Font Awesome icon class (e.g., "fa-chart-bar")
   - `order`: Display order in navigation (lower numbers appear first)

3. **Modify module.js**:
   - Replace `ModuleName` with your module's class name
   - Replace `module-id` with your module's ID
   - Implement your module's functionality

4. **Customize index.html**:
   - Update the UI to match your module's needs
   - Add your module-specific HTML structure

5. **Register your module** in `/config/modules.json`:
   ```json
   {
     "id": "your-module-id",
     "name": "Your Module Name",
     "description": "What your module does",
     "icon": "fa-your-icon",
     "path": "/modules/your-module-id/",
     "entryPoint": "module.js",
     "enabled": true,
     "order": 3
   }
   ```

## Module Structure

### Files

- **manifest.json**: Module metadata and configuration
- **module.js**: Main module class with lifecycle methods
- **index.html**: Module UI template
- **README.md**: Module documentation

### Module Class Methods

#### Required Methods

- `init()`: Initialize the module when activated
- `destroy()`: Clean up when module is deactivated

#### Optional Methods

- `reload()`: Reload the module
- `getState()`: Get current module state
- `setState(state)`: Restore module state

### Available Services

Your module has access to these shared services:

- `window.eventBus`: Inter-module communication
- `window.authService`: Authentication management
- `window.sharedApiClient`: API communication
- `Storage`: Persistent storage utilities
- `Logger`: Logging utilities

### Events

Common events your module can listen to:

- `ModuleEvents.AUTH_LOGIN`: User logged in
- `ModuleEvents.AUTH_LOGOUT`: User logged out
- `ModuleEvents.DATA_UPDATED`: Data changed
- `ModuleEvents.UI_THEME_CHANGED`: Theme toggled

Emit notifications:
```javascript
this.eventBus.emit(ModuleEvents.UI_NOTIFICATION, {
    type: 'success|error|warning|info',
    title: 'Notification Title',
    message: 'Notification message',
    duration: 5000 // milliseconds
});
```

## Best Practices

1. **Initialization**: Always check if already initialized to prevent duplicate setup
2. **Cleanup**: Remove all event listeners and timers in the destroy method
3. **Error Handling**: Use try-catch blocks and show user-friendly error messages
4. **State Management**: Save important state to allow seamless module switching
5. **Performance**: Lazy load data and use pagination for large datasets
6. **Accessibility**: Include proper ARIA labels and keyboard navigation
7. **Responsive Design**: Ensure your module works on different screen sizes

## Example: Simple Data Viewer Module

```javascript
class DataViewerModule {
    constructor() {
        this.name = 'Data Viewer';
        this.id = 'data-viewer';
        this.initialized = false;
        this.data = [];
    }

    async init() {
        if (this.initialized) return;
        
        try {
            // Load and display data
            this.data = await this.apiClient.get('/api/data');
            this.renderData();
            
            // Setup refresh button
            document.getElementById('refreshBtn').onclick = () => {
                this.refreshData();
            };
            
            this.initialized = true;
        } catch (error) {
            this.showError('Failed to load data');
        }
    }

    renderData() {
        const container = document.getElementById('dataContainer');
        container.innerHTML = this.data.map(item => 
            `<div class="data-item">${item.name}</div>`
        ).join('');
    }

    async refreshData() {
        this.data = await this.apiClient.get('/api/data');
        this.renderData();
        this.showSuccess('Data refreshed');
    }

    destroy() {
        // Cleanup
        this.data = [];
        this.initialized = false;
    }
}
```

## Testing Your Module

1. **Start the development server**:
   ```bash
   python web/serve.py
   ```

2. **Open the application** in your browser:
   ```
   http://localhost:8090
   ```

3. **Check the console** for any errors

4. **Test module switching** to ensure proper cleanup

5. **Test with different auth states** (logged in/out)

## Need Help?

- Check existing modules for examples
- Review the core services documentation
- Test in isolation before integration