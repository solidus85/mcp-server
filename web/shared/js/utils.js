// Shared Utility Functions

const Utils = {
    // Format date for display
    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 7) {
            return date.toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric',
                year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
            });
        } else if (days > 0) {
            return `${days} day${days > 1 ? 's' : ''} ago`;
        } else if (hours > 0) {
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (minutes > 0) {
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else {
            return 'Just now';
        }
    },
    
    // Format full date/time
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Get initials from name or email
    getInitials(name, email) {
        if (name) {
            const parts = name.split(' ');
            if (parts.length >= 2) {
                return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
            }
            return name.substring(0, 2).toUpperCase();
        }
        if (email) {
            return email.substring(0, 2).toUpperCase();
        }
        return '??';
    },
    
    // Generate color from string (for avatars)
    stringToColor(str) {
        if (!str) return '#6B7280';
        
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        
        const colors = [
            '#EF4444', '#F59E0B', '#10B981', '#3B82F6', 
            '#6366F1', '#8B5CF6', '#EC4899', '#14B8A6'
        ];
        
        return colors[Math.abs(hash) % colors.length];
    },
    
    // Escape HTML
    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text ? text.replace(/[&<>"']/g, m => map[m]) : '';
    },
    
    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Group emails by thread
    groupByThread(emails) {
        const threads = new Map();
        
        emails.forEach(email => {
            const threadId = email.thread_id || email.id;
            if (!threads.has(threadId)) {
                threads.set(threadId, {
                    id: threadId,
                    subject: email.subject,
                    participants: new Set(),
                    messages: [],
                    latestDate: email.created_at,
                    unreadCount: 0,
                    flagged: false
                });
            }
            
            const thread = threads.get(threadId);
            thread.messages.push(email);
            
            // Add participants
            if (email.sender) thread.participants.add(email.sender);
            if (email.recipients) {
                email.recipients.forEach(r => thread.participants.add(r));
            }
            
            // Update metadata
            if (new Date(email.created_at) > new Date(thread.latestDate)) {
                thread.latestDate = email.created_at;
            }
            if (!email.is_read) thread.unreadCount++;
            if (email.is_flagged) thread.flagged = true;
        });
        
        // Sort messages within threads
        threads.forEach(thread => {
            thread.messages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
        });
        
        // Convert to array and sort by latest date
        return Array.from(threads.values())
            .sort((a, b) => new Date(b.latestDate) - new Date(a.latestDate));
    },
    
    // Local storage wrapper with JSON support
    storage: {
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.error('Storage get error:', e);
                return defaultValue;
            }
        },
        
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (e) {
                console.error('Storage set error:', e);
                return false;
            }
        },
        
        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (e) {
                console.error('Storage remove error:', e);
                return false;
            }
        },
        
        clear() {
            try {
                localStorage.clear();
                return true;
            } catch (e) {
                console.error('Storage clear error:', e);
                return false;
            }
        }
    }
};

// Export for use in modules
window.Utils = Utils;