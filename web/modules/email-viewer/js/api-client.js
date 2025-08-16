// API Client for Email Viewer
(function() {
    // Avoid redeclaration if already defined
    if (window.EmailApiClient) {
        return;
    }

class ApiClient {
    constructor() {
        // Read from config or use defaults that match .env file
        this.baseUrl = 'http://localhost:8010/api/v1';
        this.authToken = Utils.storage.get('authToken') || 'my-personal-api-token-12345';
        this.headers = {
            'Authorization': `Bearer ${this.authToken}`,
            'Content-Type': 'application/json'
        };
    }
    
    // Set authentication token
    setAuthToken(token) {
        this.authToken = token;
        this.headers['Authorization'] = `Bearer ${token}`;
        Utils.storage.set('authToken', token);
    }
    
    // Generic fetch wrapper with error handling
    async fetchApi(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                headers: {
                    ...this.headers,
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    // Get all emails with pagination
    async getEmails(page = 1, size = 50, filters = {}) {
        const params = new URLSearchParams({
            page: page.toString(),
            size: size.toString(),
            ...filters
        });
        
        return this.fetchApi(`/emails/?${params}`);
    }
    
    // Get single email by ID
    async getEmail(emailId) {
        return this.fetchApi(`/emails/${emailId}`);
    }
    
    // Get emails in a thread
    async getThreadEmails(threadId) {
        return this.fetchApi(`/emails/thread/${threadId}`);
    }
    
    // Search emails
    async searchEmails(query, filters = {}) {
        const params = new URLSearchParams({
            q: query,
            ...filters
        });
        
        return this.fetchApi(`/emails/search?${params}`);
    }
    
    // Update email (mark as read, flag, etc.)
    async updateEmail(emailId, updates) {
        return this.fetchApi(`/emails/${emailId}`, {
            method: 'PATCH',
            body: JSON.stringify(updates)
        });
    }
    
    // Mark email as read
    async markAsRead(emailId) {
        return this.fetchApi(`/emails/${emailId}/mark-read`, {
            method: 'POST'
        });
    }
    
    // Mark email as unread
    async markAsUnread(emailId) {
        return this.fetchApi(`/emails/${emailId}/mark-unread`, {
            method: 'POST'
        });
    }
    
    // Flag email
    async flagEmail(emailId) {
        return this.fetchApi(`/emails/${emailId}/flag`, {
            method: 'POST'
        });
    }
    
    // Unflag email
    async unflagEmail(emailId) {
        return this.fetchApi(`/emails/${emailId}/unflag`, {
            method: 'POST'
        });
    }
    
    // Delete email
    async deleteEmail(emailId) {
        return this.fetchApi(`/emails/${emailId}`, {
            method: 'DELETE'
        });
    }
    
    // Bulk update emails
    async bulkUpdateEmails(emailIds, updates) {
        return this.fetchApi('/emails/bulk-update', {
            method: 'POST',
            body: JSON.stringify({
                email_ids: emailIds,
                update: updates
            })
        });
    }
    
    // Get email statistics
    async getEmailStats() {
        return this.fetchApi('/emails/stats/overall');
    }
    
    // Get projects
    async getProjects() {
        return this.fetchApi('/projects/');
    }
    
    // Get people
    async getPeople() {
        return this.fetchApi('/people/');
    }
    
    // Test connection
    async testConnection() {
        try {
            await this.fetchApi('/health');
            return true;
        } catch (error) {
            return false;
        }
    }
}

// Create global instance
    // Export class
    window.EmailApiClient = ApiClient;
    
    // Create instance
    const emailApiClient = new ApiClient();
    
    // Expose as apiClient for the module to use
    window.apiClient = emailApiClient;
})();