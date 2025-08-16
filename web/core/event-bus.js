// Event Bus for Inter-Module Communication
// Provides a centralized event system for modules to communicate

class EventBus {
    constructor() {
        this.events = new Map();
        this.history = [];
        this.maxHistorySize = 100;
    }

    // Subscribe to an event
    on(event, callback, context = null) {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }

        const listener = { callback, context };
        this.events.get(event).push(listener);

        // Return unsubscribe function
        return () => this.off(event, callback, context);
    }

    // Subscribe to an event once
    once(event, callback, context = null) {
        const onceWrapper = (...args) => {
            callback.apply(context, args);
            this.off(event, onceWrapper, context);
        };

        return this.on(event, onceWrapper, context);
    }

    // Unsubscribe from an event
    off(event, callback = null, context = null) {
        if (!this.events.has(event)) {
            return;
        }

        if (callback === null) {
            // Remove all listeners for this event
            this.events.delete(event);
            return;
        }

        const listeners = this.events.get(event);
        const filtered = listeners.filter(listener => {
            return listener.callback !== callback || listener.context !== context;
        });

        if (filtered.length === 0) {
            this.events.delete(event);
        } else {
            this.events.set(event, filtered);
        }
    }

    // Emit an event
    emit(event, data = null) {
        // Add to history
        this.addToHistory(event, data);

        if (!this.events.has(event)) {
            Logger.debug(`No listeners for event: ${event}`);
            return;
        }

        const listeners = this.events.get(event);
        listeners.forEach(listener => {
            try {
                listener.callback.call(listener.context, data);
            } catch (error) {
                Logger.error(`Error in event listener for ${event}:`, error);
            }
        });

        Logger.debug(`Event emitted: ${event}`, data);
    }

    // Emit an event asynchronously
    async emitAsync(event, data = null) {
        // Add to history
        this.addToHistory(event, data);

        if (!this.events.has(event)) {
            Logger.debug(`No listeners for event: ${event}`);
            return;
        }

        const listeners = this.events.get(event);
        const promises = listeners.map(listener => {
            return new Promise((resolve) => {
                try {
                    const result = listener.callback.call(listener.context, data);
                    resolve(result);
                } catch (error) {
                    Logger.error(`Error in event listener for ${event}:`, error);
                    resolve(null);
                }
            });
        });

        const results = await Promise.all(promises);
        Logger.debug(`Async event emitted: ${event}`, data);
        return results;
    }

    // Add event to history
    addToHistory(event, data) {
        this.history.push({
            event,
            data,
            timestamp: Date.now()
        });

        // Trim history if too large
        if (this.history.length > this.maxHistorySize) {
            this.history.shift();
        }
    }

    // Get event history
    getHistory(event = null) {
        if (event === null) {
            return [...this.history];
        }
        return this.history.filter(item => item.event === event);
    }

    // Clear event history
    clearHistory() {
        this.history = [];
    }

    // Get all registered events
    getEvents() {
        return Array.from(this.events.keys());
    }

    // Get listener count for an event
    getListenerCount(event) {
        if (!this.events.has(event)) {
            return 0;
        }
        return this.events.get(event).length;
    }

    // Clear all event listeners
    clear() {
        this.events.clear();
        Logger.debug('All event listeners cleared');
    }
}

// Create global event bus instance
window.eventBus = new EventBus();

// Common events that modules can use
const ModuleEvents = {
    // Authentication events
    AUTH_LOGIN: 'auth:login',
    AUTH_LOGOUT: 'auth:logout',
    AUTH_TOKEN_EXPIRED: 'auth:token_expired',
    AUTH_TOKEN_REFRESHED: 'auth:token_refreshed',

    // Module events
    MODULE_LOADED: 'module:loaded',
    MODULE_ACTIVATED: 'module:activated',
    MODULE_DEACTIVATED: 'module:deactivated',
    MODULE_SWITCHED: 'module:switched',
    MODULE_ERROR: 'module:error',

    // Data events
    DATA_LOADED: 'data:loaded',
    DATA_UPDATED: 'data:updated',
    DATA_DELETED: 'data:deleted',
    DATA_ERROR: 'data:error',

    // UI events
    UI_THEME_CHANGED: 'ui:theme_changed',
    UI_SIDEBAR_TOGGLED: 'ui:sidebar_toggled',
    UI_NOTIFICATION: 'ui:notification',
    UI_MODAL_OPEN: 'ui:modal_open',
    UI_MODAL_CLOSE: 'ui:modal_close',

    // API events
    API_REQUEST_START: 'api:request_start',
    API_REQUEST_SUCCESS: 'api:request_success',
    API_REQUEST_ERROR: 'api:request_error',
    API_REQUEST_END: 'api:request_end',
};

// Export for use in modules
window.ModuleEvents = ModuleEvents;