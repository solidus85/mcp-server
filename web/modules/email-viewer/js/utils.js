// Utility functions for Email Viewer

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
        return 'UN';
    },
    
    // Generate color from string (for avatars)
    stringToColor(str) {
        if (!str) return '#6B7280';
        
        const colors = [
            '#EF4444', '#F59E0B', '#10B981', '#3B82F6', 
            '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'
        ];
        
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }
        
        return colors[Math.abs(hash) % colors.length];
    },
    
    // Truncate text with ellipsis
    truncate(text, maxLength = 100) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },
    
    // Extract text from HTML
    extractText(html) {
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
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
        const threads = {};
        
        emails.forEach(email => {
            const threadId = email.thread_id || email.id;
            if (!threads[threadId]) {
                threads[threadId] = {
                    id: threadId,
                    subject: email.subject,
                    emails: [],
                    participants: new Set(),
                    lastActivity: email.datetime_sent,
                    unreadCount: 0,
                    flagged: false,
                    project: email.project
                };
            }
            
            threads[threadId].emails.push(email);
            
            // Add sender to participants
            if (email.sender && email.sender.email) {
                threads[threadId].participants.add(email.sender.email);
            } else if (email.from) {
                threads[threadId].participants.add(email.from);
            }
            
            // Add recipients to participants
            if (email.recipients && email.recipients.length > 0) {
                email.recipients.forEach(r => {
                    if (r.person && r.person.email) {
                        threads[threadId].participants.add(r.person.email);
                    }
                });
            }
            
            // Update last activity
            if (new Date(email.datetime_sent) > new Date(threads[threadId].lastActivity)) {
                threads[threadId].lastActivity = email.datetime_sent;
            }
            
            // Count unread
            if (!email.is_read) {
                threads[threadId].unreadCount++;
            }
            
            // Check if flagged
            if (email.is_flagged) {
                threads[threadId].flagged = true;
            }
        });
        
        // Convert to array and sort by last activity
        return Object.values(threads).sort((a, b) => 
            new Date(b.lastActivity) - new Date(a.lastActivity)
        );
    },
    
    // Get project color class
    getProjectColorClass(projectName) {
        if (!projectName) return 'project-color-1';
        
        const hash = projectName.split('').reduce((acc, char) => 
            acc + char.charCodeAt(0), 0);
        
        const colorIndex = (hash % 5) + 1;
        return `project-color-${colorIndex}`;
    },
    
    // Parse email addresses from string
    parseEmailAddresses(emailString) {
        if (Array.isArray(emailString)) return emailString;
        if (!emailString) return [];
        
        return emailString.split(',').map(email => email.trim()).filter(Boolean);
    },
    
    // Show toast notification
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toastContainer');
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = document.createElement('i');
        icon.className = type === 'success' ? 'fas fa-check-circle' :
                        type === 'error' ? 'fas fa-exclamation-circle' :
                        'fas fa-info-circle';
        
        const text = document.createElement('span');
        text.textContent = message;
        
        toast.appendChild(icon);
        toast.appendChild(text);
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.classList.add('animate-fade-out');
            setTimeout(() => {
                container.removeChild(toast);
            }, 300);
        }, duration);
    },
    
    // Store and retrieve from localStorage
    storage: {
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                return defaultValue;
            }
        },
        
        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.error('Failed to save to localStorage:', e);
            }
        },
        
        remove(key) {
            localStorage.removeItem(key);
        }
    },
    
    // Session storage helpers
    session: {
        get(key, defaultValue = null) {
            try {
                const item = sessionStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                return defaultValue;
            }
        },
        
        set(key, value) {
            try {
                sessionStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.error('Failed to save to sessionStorage:', e);
            }
        },
        
        remove(key) {
            sessionStorage.removeItem(key);
        }
    }
};