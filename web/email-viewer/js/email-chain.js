// Email Chain Viewer Component

class EmailChain {
    constructor() {
        this.container = document.getElementById('emailChain');
        this.header = document.getElementById('chainHeader');
        this.emptyState = document.getElementById('emptyState');
        this.currentThread = null;
        this.emails = [];
    }
    
    // Initialize the component
    init() {
        this.setupEventListeners();
        this.setupActionButtons();
    }
    
    // Setup event listeners
    setupEventListeners() {
        // Listen for thread selection
        window.addEventListener('threadSelected', (e) => {
            this.loadThread(e.detail);
        });
    }
    
    // Setup action buttons
    setupActionButtons() {
        // Mark all as read
        document.getElementById('markAllReadBtn')?.addEventListener('click', () => {
            this.markAllAsRead();
        });
        
        // Flag thread
        document.getElementById('flagThreadBtn')?.addEventListener('click', () => {
            this.toggleThreadFlag();
        });
        
        // Archive thread
        document.getElementById('archiveThreadBtn')?.addEventListener('click', () => {
            this.archiveThread();
        });
        
        // Delete thread
        document.getElementById('deleteThreadBtn')?.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete this thread?')) {
                this.deleteThread();
            }
        });
    }
    
    // Load and display a thread
    async loadThread(thread) {
        this.currentThread = thread;
        this.showLoading();
        
        try {
            // If thread has a specific ID, load from API
            if (thread.id && thread.id.startsWith('thread_')) {
                // Get thread emails (summary)
                const threadEmails = await apiClient.getThreadEmails(thread.id);
                
                // Load full details for each email
                const fullEmails = [];
                for (const summary of threadEmails) {
                    try {
                        const fullEmail = await apiClient.getEmail(summary.id);
                        console.log('Loaded email:', fullEmail.subject, {
                            hasBody: !!fullEmail.body,
                            hasBodyText: !!fullEmail.body_text,
                            recipientCount: fullEmail.recipients?.length || 0
                        });
                        fullEmails.push(fullEmail);
                    } catch (err) {
                        console.warn('Failed to load email details:', summary.id, err);
                        fullEmails.push(summary); // Use summary as fallback
                    }
                }
                this.emails = fullEmails;
            } else {
                // Use emails from the thread object
                this.emails = thread.emails || [];
            }
            
            // Sort emails by date
            this.emails.sort((a, b) => 
                new Date(a.datetime_sent) - new Date(b.datetime_sent)
            );
            
            this.render();
            
        } catch (error) {
            console.error('Failed to load thread:', error);
            this.showError('Failed to load email thread');
        }
    }
    
    // Render the email chain
    render() {
        if (!this.currentThread || this.emails.length === 0) {
            this.showEmpty();
            return;
        }
        
        // Show header
        this.renderHeader();
        
        // Hide empty state
        this.emptyState.style.display = 'none';
        
        // Render emails
        const html = this.emails.map((email, index) => 
            this.renderEmail(email, index)
        ).join('');
        
        this.container.innerHTML = `
            <div class="max-w-4xl mx-auto">
                ${html}
            </div>
        `;
        
        // Add event handlers to email cards
        this.setupEmailCardHandlers();
    }
    
    // Render header
    renderHeader() {
        this.header.classList.remove('hidden');
        
        document.getElementById('chainSubject').textContent = this.currentThread.subject;
        
        const participantCount = this.currentThread.participants.size;
        const messageCount = this.emails.length;
        
        document.getElementById('chainInfo').textContent = 
            `${participantCount} participant${participantCount > 1 ? 's' : ''} • ` +
            `${messageCount} message${messageCount > 1 ? 's' : ''}`;
        
        // Update flag button state
        const flagBtn = document.getElementById('flagThreadBtn');
        const isFlagged = this.emails.some(e => e.is_flagged);
        flagBtn.innerHTML = isFlagged ? 
            '<i class="fas fa-flag"></i>' : 
            '<i class="far fa-flag"></i>';
    }
    
    // Render single email
    renderEmail(email, index) {
        const isUnread = !email.is_read;
        
        // Handle sender - use 'from' field if sender object not available
        const senderEmail = email.from || email.sender?.email || 'unknown@email.com';
        const sender = email.sender || { email: senderEmail, full_name: null };
        const senderName = sender.full_name || senderEmail.split('@')[0];
        const initials = Utils.getInitials(sender.full_name, senderEmail);
        const avatarColor = Utils.stringToColor(senderEmail);
        
        // Format recipients - handle different data structures
        let toEmails = '';
        let ccEmails = '';
        
        if (email.recipients && email.recipients.length > 0) {
            const toRecipients = email.recipients.filter(r => r.recipient_type === 'TO');
            const ccRecipients = email.recipients.filter(r => r.recipient_type === 'CC');
            
            toEmails = toRecipients.map(r => {
                const person = r.person;
                if (person) {
                    return person.full_name ? 
                        `${person.full_name} <${person.email}>` : 
                        person.email;
                }
                return 'Unknown';
            }).join(', ');
            
            ccEmails = ccRecipients.map(r => {
                const person = r.person;
                if (person) {
                    return person.full_name ? 
                        `${person.full_name} <${person.email}>` : 
                        person.email;
                }
                return 'Unknown';
            }).join(', ');
        } else {
            // Fallback if recipients not available
            toEmails = email.to || 'Recipients not available';
        }
        
        // Check if this is a reply
        const isReply = index > 0 || email.in_reply_to;
        
        return `
            <div class="email-card ${isUnread ? 'unread' : ''} ${isReply ? 'thread-line' : ''}" 
                 data-email-id="${email.id}">
                <div class="p-4">
                    <!-- Email Header -->
                    <div class="flex items-start justify-between mb-3">
                        <div class="flex items-start space-x-3">
                            <div class="avatar" style="background-color: ${avatarColor}">
                                ${initials}
                            </div>
                            <div>
                                <div class="font-semibold text-gray-900 dark:text-white">
                                    ${senderName}
                                    ${senderEmail !== senderName ? 
                                        `<span class="font-normal text-sm text-gray-500 dark:text-gray-400 ml-2">&lt;${senderEmail}&gt;</span>` 
                                        : ''}
                                </div>
                                <div class="text-sm text-gray-600 dark:text-gray-400">
                                    <div><strong>To:</strong> ${toEmails}</div>
                                    ${ccEmails ? `<div><strong>Cc:</strong> ${ccEmails}</div>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span class="text-sm text-gray-500 dark:text-gray-400">
                                ${Utils.formatDateTime(email.datetime_sent)}
                            </span>
                            <div class="flex space-x-1">
                                ${isUnread ? `
                                    <button class="action-btn mark-read-btn" title="Mark as read">
                                        <i class="fas fa-envelope-open text-sm"></i>
                                    </button>
                                ` : ''}
                                <button class="action-btn flag-btn" title="Flag email">
                                    <i class="${email.is_flagged ? 'fas' : 'far'} fa-flag text-sm"></i>
                                </button>
                                <button class="action-btn expand-btn" title="Collapse/Expand">
                                    <i class="fas fa-chevron-down text-sm"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Email Body -->
                    <div class="email-body">
                        ${email.project ? `
                            <div class="mb-3">
                                <span class="project-badge ${Utils.getProjectColorClass(email.project.name)}">
                                    <i class="fas fa-folder text-xs mr-1"></i>${email.project.name}
                                </span>
                            </div>
                        ` : ''}
                        
                        <div class="prose prose-sm dark:prose-invert max-w-none">
                            ${this.renderEmailBody(email)}
                        </div>
                        
                        ${email.attachments && email.attachments.length > 0 ? `
                            <div class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                                <div class="flex flex-wrap gap-2">
                                    ${email.attachments.map(att => `
                                        <span class="attachment-badge">
                                            <i class="fas fa-paperclip mr-1"></i>
                                            ${att.name || 'Attachment'}
                                        </span>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Render email body content
    renderEmailBody(email) {
        // Check if we have any body content
        if (!email.body && !email.body_text) {
            return '<p class="text-gray-500 italic">No email content available</p>';
        }
        
        // If we have HTML body, use it
        if (email.body && (email.body.includes('<html>') || email.body.includes('<body>'))) {
            // Extract body content from HTML
            let bodyContent = email.body;
            
            // Extract content between body tags if present
            const bodyMatch = bodyContent.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
            if (bodyMatch) {
                bodyContent = bodyMatch[1];
            }
            
            // Basic sanitization - in production, use a proper sanitizer
            return bodyContent
                .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
                .replace(/on\w+="[^"]*"/g, '')
                .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');
        }
        
        // Otherwise use text body or plain body
        const text = email.body_text || email.body || '';
        
        // Convert plain text to HTML with proper formatting
        return text
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .split('\n')
            .map(line => {
                // Preserve empty lines
                if (line.trim() === '') return '<br>';
                // Wrap non-empty lines in paragraphs
                return `<p class="mb-2">${line}</p>`;
            })
            .join('');
    }
    
    // Setup email card event handlers
    setupEmailCardHandlers() {
        // Expand/collapse buttons
        this.container.querySelectorAll('.expand-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const card = btn.closest('.email-card');
                card.classList.toggle('collapsed');
                
                const icon = btn.querySelector('i');
                icon.classList.toggle('fa-chevron-down');
                icon.classList.toggle('fa-chevron-up');
            });
        });
        
        // Mark as read buttons
        this.container.querySelectorAll('.mark-read-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const card = btn.closest('.email-card');
                const emailId = card.dataset.emailId;
                await this.markEmailAsRead(emailId);
            });
        });
        
        // Flag buttons
        this.container.querySelectorAll('.flag-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const card = btn.closest('.email-card');
                const emailId = card.dataset.emailId;
                await this.toggleEmailFlag(emailId);
            });
        });
    }
    
    // Mark email as read
    async markEmailAsRead(emailId) {
        try {
            await apiClient.markAsRead(emailId);
            
            // Update UI
            const card = this.container.querySelector(`[data-email-id="${emailId}"]`);
            card.classList.remove('unread');
            card.querySelector('.mark-read-btn')?.remove();
            
            // Update email in memory
            const email = this.emails.find(e => e.id === emailId);
            if (email) email.is_read = true;
            
            Utils.showToast('Email marked as read', 'success');
            
        } catch (error) {
            console.error('Failed to mark email as read:', error);
            Utils.showToast('Failed to mark email as read', 'error');
        }
    }
    
    // Toggle email flag
    async toggleEmailFlag(emailId) {
        const email = this.emails.find(e => e.id === emailId);
        if (!email) return;
        
        try {
            if (email.is_flagged) {
                await apiClient.unflagEmail(emailId);
                email.is_flagged = false;
            } else {
                await apiClient.flagEmail(emailId);
                email.is_flagged = true;
            }
            
            // Update UI
            const card = this.container.querySelector(`[data-email-id="${emailId}"]`);
            const icon = card.querySelector('.flag-btn i');
            icon.classList.toggle('fas');
            icon.classList.toggle('far');
            
            Utils.showToast(
                email.is_flagged ? 'Email flagged' : 'Email unflagged', 
                'success'
            );
            
        } catch (error) {
            console.error('Failed to toggle email flag:', error);
            Utils.showToast('Failed to update email flag', 'error');
        }
    }
    
    // Mark all emails in thread as read
    async markAllAsRead() {
        if (!this.emails) return;
        
        try {
            const unreadEmails = this.emails.filter(e => !e.is_read);
            
            for (const email of unreadEmails) {
                await apiClient.markAsRead(email.id);
                email.is_read = true;
            }
            
            // Update UI
            this.container.querySelectorAll('.email-card.unread').forEach(card => {
                card.classList.remove('unread');
                card.querySelector('.mark-read-btn')?.remove();
            });
            
            Utils.showToast('All emails marked as read', 'success');
            
            // Refresh thread list
            threadList.loadThreads();
            
        } catch (error) {
            console.error('Failed to mark all as read:', error);
            Utils.showToast('Failed to mark all as read', 'error');
        }
    }
    
    // Toggle thread flag
    async toggleThreadFlag() {
        // Implementation would flag/unflag all emails in thread
        Utils.showToast('Thread flag toggled', 'info');
    }
    
    // Archive thread
    async archiveThread() {
        // Implementation would move thread to archive
        Utils.showToast('Thread archived', 'info');
    }
    
    // Delete thread
    async deleteThread() {
        // Implementation would delete all emails in thread
        Utils.showToast('Thread deleted', 'info');
    }
    
    // Show loading state
    showLoading() {
        this.header.classList.add('hidden');
        this.emptyState.style.display = 'none';
        
        this.container.innerHTML = `
            <div class="flex items-center justify-center h-full">
                <div class="text-center">
                    <i class="fas fa-spinner fa-spin text-4xl text-gray-400 mb-4"></i>
                    <p class="text-gray-500 dark:text-gray-400">Loading email thread...</p>
                </div>
            </div>
        `;
    }
    
    // Show empty state
    showEmpty() {
        this.header.classList.add('hidden');
        this.emptyState.style.display = 'flex';
        this.container.innerHTML = '';
    }
    
    // Show error state
    showError(message) {
        this.header.classList.add('hidden');
        this.emptyState.style.display = 'none';
        
        this.container.innerHTML = `
            <div class="flex items-center justify-center h-full">
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                    <p class="text-red-600 dark:text-red-400">${message}</p>
                </div>
            </div>
        `;
    }
}

// Create global instance
const emailChain = new EmailChain();