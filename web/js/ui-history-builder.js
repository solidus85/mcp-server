// UI History Builder - handles history item generation and status formatting

class UIHistoryBuilder {
    constructor() {}

    // Build history item HTML
    buildHistoryItem(entry) {
        const statusClass = this.getStatusClass(entry.status);
        const timeAgo = this.getTimeAgo(new Date(entry.timestamp));
        
        return `
            <div class="history-item p-2 rounded border border-gray-200 dark:border-gray-700">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <span class="px-2 py-0.5 text-xs font-bold rounded method-${entry.method.toLowerCase()}">
                            ${entry.method}
                        </span>
                        <span class="text-sm text-gray-700 dark:text-gray-300">
                            ${this.formatPath(entry.path)}
                        </span>
                    </div>
                    <div class="flex items-center space-x-2 text-xs">
                        ${entry.status ? `
                            <span class="${statusClass} font-bold">${entry.status}</span>
                        ` : ''}
                        ${entry.responseTime ? `
                            <span class="text-gray-500">${entry.responseTime}ms</span>
                        ` : ''}
                        <span class="text-gray-500">${timeAgo}</span>
                    </div>
                </div>
                ${entry.error ? `
                    <div class="text-xs text-red-500 mt-1">${entry.error}</div>
                ` : ''}
            </div>
        `;
    }

    // Get status class based on status code
    getStatusClass(status) {
        if (!status) return '';
        if (status >= 200 && status < 300) return 'status-success';
        if (status >= 300 && status < 400) return 'status-redirect';
        if (status >= 400 && status < 500) return 'status-client-error';
        if (status >= 500) return 'status-server-error';
        return '';
    }

    // Get relative time string
    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        
        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        
        return date.toLocaleDateString();
    }

    // Format path for display
    formatPath(path) {
        return path.replace('/api/v1', '').replace(/{([^}]+)}/g, ':$1');
    }

    // Build history list from entries
    buildHistoryList(entries) {
        if (!entries || entries.length === 0) {
            return `
                <div class="text-center py-4 text-gray-500 dark:text-gray-400">
                    No requests yet
                </div>
            `;
        }
        
        return entries.map(entry => this.buildHistoryItem(entry)).join('');
    }

    // Build history statistics
    buildHistoryStats(entries) {
        if (!entries || entries.length === 0) {
            return {
                total: 0,
                successful: 0,
                failed: 0,
                averageTime: 0
            };
        }
        
        let successful = 0;
        let failed = 0;
        let totalTime = 0;
        let timeCount = 0;
        
        entries.forEach(entry => {
            if (entry.status >= 200 && entry.status < 300) {
                successful++;
            } else if (entry.status >= 400) {
                failed++;
            }
            
            if (entry.responseTime) {
                totalTime += entry.responseTime;
                timeCount++;
            }
        });
        
        return {
            total: entries.length,
            successful,
            failed,
            averageTime: timeCount > 0 ? Math.round(totalTime / timeCount) : 0
        };
    }

    // Build history stats display
    buildHistoryStatsDisplay(stats) {
        return `
            <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-2">
                <span>Total: ${stats.total}</span>
                <span class="text-green-500">Success: ${stats.successful}</span>
                <span class="text-red-500">Failed: ${stats.failed}</span>
                <span>Avg: ${stats.averageTime}ms</span>
            </div>
        `;
    }
}