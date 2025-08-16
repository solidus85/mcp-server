// Search and Filter Component

class SearchFilter {
    constructor() {
        this.searchInput = document.getElementById('searchInput');
        this.filterBtn = document.getElementById('filterBtn');
        this.filterModal = document.getElementById('filterModal');
        this.activeFilters = {};
        this.searchDebounced = Utils.debounce(this.performSearch.bind(this), 500);
    }
    
    // Initialize the component
    init() {
        this.setupSearchInput();
        this.setupFilterModal();
        this.loadProjects();
    }
    
    // Setup search input
    setupSearchInput() {
        this.searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            if (query.length >= 2 || query.length === 0) {
                this.searchDebounced(query);
            }
        });
        
        // Handle Enter key
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const query = e.target.value.trim();
                this.performSearch(query);
            }
        });
    }
    
    // Setup filter modal
    setupFilterModal() {
        // Open modal
        this.filterBtn.addEventListener('click', () => {
            this.filterModal.classList.remove('hidden');
        });
        
        // Close modal
        document.getElementById('cancelFilter').addEventListener('click', () => {
            this.filterModal.classList.add('hidden');
        });
        
        // Apply filters
        document.getElementById('applyFilter').addEventListener('click', () => {
            this.applyFilters();
        });
        
        // Close on background click
        this.filterModal.addEventListener('click', (e) => {
            if (e.target === this.filterModal) {
                this.filterModal.classList.add('hidden');
            }
        });
    }
    
    // Load projects for filter dropdown
    async loadProjects() {
        try {
            const response = await apiClient.getProjects();
            const projects = response.items || [];
            
            const select = document.getElementById('projectFilter');
            select.innerHTML = '<option value="">All Projects</option>';
            
            projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.id;
                option.textContent = project.name;
                select.appendChild(option);
            });
            
        } catch (error) {
            console.error('Failed to load projects:', error);
        }
    }
    
    // Perform search
    async performSearch(query) {
        if (!query) {
            // Clear search and reload all threads
            threadList.loadThreads();
            return;
        }
        
        try {
            const response = await apiClient.searchEmails(query, this.activeFilters);
            const emails = response.results || [];
            
            // Group into threads and display
            threadList.threads = Utils.groupByThread(emails);
            threadList.renderThreads();
            threadList.updateCount();
            
            Utils.showToast(`Found ${emails.length} emails`, 'info');
            
        } catch (error) {
            console.error('Search failed:', error);
            Utils.showToast('Search failed', 'error');
        }
    }
    
    // Apply filters
    applyFilters() {
        // Collect filter values
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const projectId = document.getElementById('projectFilter').value;
        const showUnread = document.getElementById('showUnread').checked;
        const showFlagged = document.getElementById('showFlagged').checked;
        
        // Build filter object
        this.activeFilters = {};
        
        if (startDate) {
            this.activeFilters.date_from = new Date(startDate).toISOString();
        }
        
        if (endDate) {
            this.activeFilters.date_to = new Date(endDate).toISOString();
        }
        
        if (projectId) {
            this.activeFilters.project_id = projectId;
        }
        
        if (showUnread) {
            this.activeFilters.is_read = false;
        }
        
        if (showFlagged) {
            this.activeFilters.is_flagged = true;
        }
        
        // Close modal
        this.filterModal.classList.add('hidden');
        
        // Apply filters
        this.reloadWithFilters();
        
        // Update filter button to show active state
        const hasFilters = Object.keys(this.activeFilters).length > 0;
        this.filterBtn.classList.toggle('bg-blue-500', hasFilters);
        this.filterBtn.classList.toggle('text-white', hasFilters);
        this.filterBtn.classList.toggle('bg-gray-100', !hasFilters);
        this.filterBtn.classList.toggle('dark:bg-gray-700', !hasFilters);
        this.filterBtn.classList.toggle('text-gray-700', !hasFilters);
        this.filterBtn.classList.toggle('dark:text-gray-300', !hasFilters);
    }
    
    // Reload threads with current filters
    async reloadWithFilters() {
        try {
            const response = await apiClient.getEmails(1, 100, this.activeFilters);
            const emails = response.items || [];
            
            threadList.threads = Utils.groupByThread(emails);
            threadList.renderThreads();
            threadList.updateCount();
            
            if (Object.keys(this.activeFilters).length > 0) {
                Utils.showToast('Filters applied', 'success');
            }
            
        } catch (error) {
            console.error('Failed to apply filters:', error);
            Utils.showToast('Failed to apply filters', 'error');
        }
    }
    
    // Clear all filters
    clearFilters() {
        this.activeFilters = {};
        
        // Reset form inputs
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        document.getElementById('projectFilter').value = '';
        document.getElementById('showUnread').checked = false;
        document.getElementById('showFlagged').checked = false;
        
        // Reset filter button appearance
        this.filterBtn.classList.remove('bg-blue-500', 'text-white');
        this.filterBtn.classList.add('bg-gray-100', 'dark:bg-gray-700', 'text-gray-700', 'dark:text-gray-300');
        
        // Reload without filters
        threadList.loadThreads();
    }
}

// Create global instance
const searchFilter = new SearchFilter();