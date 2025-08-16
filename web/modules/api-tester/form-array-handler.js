// Form array handler module - handles dynamic array item management

class FormArrayHandler {
    constructor(formRenderer) {
        this.formRenderer = formRenderer;
        this.arrayCounters = {};
    }

    // Initialize array counter for a specific array
    initArrayCounter(arrayId) {
        if (!this.arrayCounters[arrayId]) {
            this.arrayCounters[arrayId] = 0;
        }
    }

    // Add array item dynamically
    addArrayItem(arrayId, itemSchema) {
        // Initialize counter if needed
        this.initArrayCounter(arrayId);
        
        const container = document.getElementById(`${arrayId}-items`);
        if (!container) {
            console.error(`Array container not found: ${arrayId}-items`);
            return;
        }
        
        const itemIndex = this.arrayCounters[arrayId]++;
        const itemId = `${arrayId}-item-${itemIndex}`;
        
        const itemHtml = `
            <div class="array-item flex gap-2" data-item-id="${itemId}">
                ${this.formRenderer.buildInputControl(itemId, itemSchema)}
                <button type="button" onclick="window.formArrayHandler.removeArrayItem('${itemId}')" 
                        class="px-2 py-1 text-sm text-red-500 hover:text-red-700">
                    ✕
                </button>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', itemHtml);
    }

    // Remove array item
    removeArrayItem(itemId) {
        const item = document.querySelector(`[data-item-id="${itemId}"]`);
        if (item) {
            item.remove();
        }
    }

    // Get array values from form
    getArrayValues(arrayId) {
        const container = document.getElementById(`${arrayId}-items`);
        if (!container) return [];
        
        const values = [];
        container.querySelectorAll('.array-item').forEach(item => {
            const inputs = item.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                if (input.value) {
                    const value = input.type === 'number' ? Number(input.value) : input.value;
                    values.push(value);
                }
            });
        });
        
        return values;
    }

    // Clear all items from an array
    clearArrayItems(arrayId) {
        const container = document.getElementById(`${arrayId}-items`);
        if (container) {
            container.innerHTML = '';
        }
        // Reset counter
        this.arrayCounters[arrayId] = 0;
    }

    // Set array values (useful for editing existing data)
    setArrayValues(arrayId, values, itemSchema) {
        // Clear existing items
        this.clearArrayItems(arrayId);
        
        // Add new items with values
        values.forEach(value => {
            this.addArrayItem(arrayId, itemSchema);
            
            // Set the value of the last added item
            const container = document.getElementById(`${arrayId}-items`);
            const lastItem = container.querySelector('.array-item:last-child');
            if (lastItem) {
                const input = lastItem.querySelector('input, select, textarea');
                if (input) {
                    input.value = value;
                }
            }
        });
    }

    // Reset all array counters
    resetAllCounters() {
        this.arrayCounters = {};
    }
}