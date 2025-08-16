// Thread List Component

class ThreadList {
    constructor() {
        this.container = document.getElementById('threadList');
        this.countElement = document.getElementById('threadCount');
        this.threads = [];
        this.activeThreadId = null;
        this.currentFilter = 'all';
    }
    
    // Initialize the component
    init() {
        this.setupFilterButtons();
        this.loadThreads();
    }
    
    // Setup filter button handlers
    setupFilterButtons() {
        document.querySelectorAll('.filter-chip').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const filter = e.target.dataset.filter;
                this.setFilter(filter);
            });
        });
    }
    
    // Set active filter
    setFilter(filter) {
        this.currentFilter = filter;
        
        // Update button states
        document.querySelectorAll('.filter-chip').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
        
        this.renderThreads();
    }
    
    // Load threads from API
    async loadThreads() {
        this.showLoading();
        
        try {
            const response = await apiClient.getEmails(1, 100);
            const emails = response.items || [];
            
            // Group emails into threads
            this.threads = Utils.groupByThread(emails);
            
            this.renderThreads();
            this.updateCount();
            
        } catch (error) {
            console.error('Failed to load threads:', error);
            this.showError('Failed to load email threads');
        }
    }
    
    // Render thread list
    renderThreads() {
        // Filter threads based on current filter
        let filteredThreads = this.threads;
        
        if (this.currentFilter === 'unread') {
            filteredThreads = this.threads.filter(t => t.unreadCount > 0);
        } else if (this.currentFilter === 'flagged') {
            filteredThreads = this.threads.filter(t => t.flagged);
        } else if (this.currentFilter === 'recent') {
            const threeDaysAgo = new Date();
            threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
            filteredThreads = this.threads.filter(t => 
                new Date(t.lastActivity) > threeDaysAgo
            );
        }
        
        if (filteredThreads.length === 0) {
            this.showEmpty();
            return;
        }
        
        const html = filteredThreads.map(thread => 
            this.renderThreadItem(thread)
        ).join('');
        
        this.container.innerHTML = html;
        
        // Add click handlers
        this.container.querySelectorAll('.thread-item').forEach(item => {
            item.addEventListener('click', () => {
                const threadId = item.dataset.threadId;
                this.selectThread(threadId);
            });
        });
    }
    
    // Render single thread item
    renderThreadItem(thread) {
        const isActive = thread.id === this.activeThreadId;
        const isUnread = thread.unreadCount > 0;
        const lastEmail = thread.emails[thread.emails.length - 1];
        
        // Get participant names
        const participants = Array.from(thread.participants).slice(0, 3);
        const participantNames = participants.map(email => 
            email.split('@')[0]
        ).join(', ');
        const extraCount = thread.participants.size - 3;
        const participantText = extraCount > 0 ? 
            `${participantNames} (+${extraCount})` : participantNames;
        
        // Get last message preview
        const preview = lastEmail ? 
            Utils.truncate(Utils.extractText(lastEmail.body_text || lastEmail.body), 60) : '';
        
        return `
            <div class="thread-item ${isActive ? 'active' : ''} ${isUnread ? 'unread' : ''}" 
                 data-thread-id="${thread.id}">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        <div class="avatar" style="background-color: ${Utils.stringToColor(thread.subject)}">
                            ${Utils.getInitials(thread.subject)}
                        </div>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <div class="flex items-center space-x-2 mb-1">
                                    ${thread.flagged ? '<i class="fas fa-flag text-red-500 text-xs"></i>' : ''}
                                    <span class="text-sm ${isUnread ? 'font-semibold text-gray-900 dark:text-white' : 'text-gray-700 dark:text-gray-300'}">
                                        ${thread.subject}
                                    </span>
                                    ${thread.unreadCount > 0 ? `
                                        <span class="bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                                            ${thread.unreadCount}
                                        </span>
                                    ` : ''}
                                </div>
                                <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                                    ${participantText}
                                </div>
                                <div class="text-sm text-gray-600 dark:text-gray-400">
                                    ${preview}
                                </div>
                            </div>
                            <div class="flex-shrink-0 ml-2 text-right">
                                <div class="text-xs text-gray-500 dark:text-gray-400">
                                    ${Utils.formatDate(thread.lastActivity)}
                                </div>
                                ${thread.project ? `
                                    <div class="mt-1">
                                        <span class="project-badge ${Utils.getProjectColorClass(thread.project.name)}">
                                            ${thread.project.name}
                                        </span>
                                    </div>
                                ` : ''}
                                <div class="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                    ${thread.emails.length} message${thread.emails.length > 1 ? 's' : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Select a thread
    selectThread(threadId) {
        this.activeThreadId = threadId;
        
        // Update UI
        this.container.querySelectorAll('.thread-item').forEach(item => {
            item.classList.toggle('active', item.dataset.threadId === threadId);
        });
        
        // Trigger event for email chain viewer
        const thread = this.threads.find(t => t.id === threadId);
        if (thread) {
            window.dispatchEvent(new CustomEvent('threadSelected', { 
                detail: thread 
            }));
        }
    }
    
    // Update thread count
    updateCount() {
        const count = this.threads.length;
        this.countElement.textContent = `${count} thread${count !== 1 ? 's' : ''}`;
    }
    
    // Show loading state
    showLoading() {
        this.container.innerHTML = `
            <div class="p-8 text-center">
                <i class="fas fa-spinner fa-spin text-3xl text-gray-400 mb-3"></i>
                <p class="text-gray-500 dark:text-gray-400">Loading threads...</p>
            </div>
        `;
    }
    
    // Show empty state
    showEmpty() {
        this.container.innerHTML = `
            <div class="p-8 text-center text-gray-500 dark:text-gray-400">
                <i class="fas fa-inbox text-4xl mb-4"></i>
                <p>No email threads found</p>
                <p class="text-sm mt-2">Try adjusting your filters</p>
            </div>
        `;
    }
    
    // Show error state
    showError(message) {
        this.container.innerHTML = `
            <div class="p-8 text-center">
                <i class="fas fa-exclamation-triangle text-3xl text-red-500 mb-3"></i>
                <p class="text-red-600 dark:text-red-400">${message}</p>
                <button onclick="threadList.loadThreads()" 
                        class="mt-3 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                    Retry
                </button>
            </div>
        `;
    }
    
    // Refresh threads
    async refresh() {
        await this.loadThreads();
        Utils.showToast('Threads refreshed', 'success');
    }
    
    // Mark thread as read
    async markThreadAsRead(threadId) {
        const thread = this.threads.find(t => t.id === threadId);
        if (!thread) return;
        
        try {
            // Mark all emails in thread as read
            for (const email of thread.emails) {
                if (!email.is_read) {
                    await apiClient.markAsRead(email.id);
                    email.is_read = true;
                }
            }
            
            thread.unreadCount = 0;
            this.renderThreads();
            
        } catch (error) {
            console.error('Failed to mark thread as read:', error);
            Utils.showToast('Failed to mark thread as read', 'error');
        }
    }
}

// Create global instance
const threadList = new ThreadList();