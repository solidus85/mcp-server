// Email-specific API Client that extends shared functionality
(function() {
    'use strict';
    
    // Only initialize if not already defined
    if (window.EmailApiClient) {
        return;
    }
    
    class EmailApiClient {
        constructor() {
            // Use the shared API client for base functionality
            this.sharedClient = window.sharedApiClient || new window.SharedApiClient();
            this.baseUrl = this.sharedClient.baseUrl || 'http://localhost:8010/api/v1';
        }
        
        // Email-specific endpoints
        async getEmails(page = 1, size = 50, filters = {}) {
            const params = new URLSearchParams({
                page: page.toString(),
                size: size.toString(),
                ...filters
            });
            
            return this.sharedClient.get(`/emails?${params}`);
        }
        
        async getEmailById(emailId) {
            return this.sharedClient.get(`/emails/${emailId}`);
        }
        
        async getEmailThread(threadId) {
            return this.sharedClient.get(`/emails/threads/${threadId}`);
        }
        
        async markAsRead(emailId) {
            return this.sharedClient.post(`/emails/${emailId}/read`);
        }
        
        async markAsUnread(emailId) {
            return this.sharedClient.post(`/emails/${emailId}/unread`);
        }
        
        async flagEmail(emailId) {
            return this.sharedClient.post(`/emails/${emailId}/flag`);
        }
        
        async unflagEmail(emailId) {
            return this.sharedClient.post(`/emails/${emailId}/unflag`);
        }
        
        async deleteEmail(emailId) {
            return this.sharedClient.delete(`/emails/${emailId}`);
        }
        
        async bulkUpdateEmails(emailIds, updates) {
            return this.sharedClient.post('/emails/bulk-update', {
                email_ids: emailIds,
                update: updates
            });
        }
        
        async getEmailStats() {
            return this.sharedClient.get('/emails/stats');
        }
        
        async searchEmails(query) {
            return this.sharedClient.get(`/emails/search?q=${encodeURIComponent(query)}`);
        }
        
        // People endpoints
        async getPeople() {
            return this.sharedClient.get('/people');
        }
        
        async getPersonById(personId) {
            return this.sharedClient.get(`/people/${personId}`);
        }
        
        // Projects endpoints
        async getProjects() {
            return this.sharedClient.get('/projects');
        }
        
        async getProjectById(projectId) {
            return this.sharedClient.get(`/projects/${projectId}`);
        }
    }
    
    // Export and create instance
    window.EmailApiClient = EmailApiClient;
    
    // Create a single instance for the module
    if (!window.emailApiClient) {
        window.emailApiClient = new EmailApiClient();
    }
    
    // For backward compatibility
    if (!window.apiClient) {
        window.apiClient = window.emailApiClient;
    }
})();