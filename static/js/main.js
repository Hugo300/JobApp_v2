/**
 * Main JavaScript file - Application initialization and common functionality
 */

// Application namespace
window.JobApp = {
    // Configuration
    config: {
        ajaxTimeout: 30000,
        autoSaveInterval: 30000,
        alertTimeout: 5000
    },

    // Initialize application
    init: function() {
        console.log('JobApp initializing...');
        
        // Initialize theme handling
        this.initTheme();
        
        // Initialize common event handlers
        this.initEventHandlers();
        
        // Initialize page-specific functionality
        this.initPageSpecific();
        
        console.log('JobApp initialized successfully');
    },

    // Theme handling
    initTheme: function() {
        const themeToggle = document.getElementById('themeToggle');
        const themeIcon = document.getElementById('themeIcon');
        const html = document.documentElement;
        
        if (!themeToggle || !themeIcon) return;
        
        // Check for saved theme preference or default to 'light'
        const currentTheme = localStorage.getItem('theme') || 'light';
        html.setAttribute('data-bs-theme', currentTheme);
        this.updateThemeIcon(currentTheme);
        
        // Theme toggle click handler
        themeToggle.addEventListener('click', () => {
            const currentTheme = html.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            html.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            this.updateThemeIcon(newTheme);
        });
    },

    updateThemeIcon: function(theme) {
        const themeIcon = document.getElementById('themeIcon');
        const themeToggle = document.getElementById('themeToggle');
        
        if (!themeIcon || !themeToggle) return;
        
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-sun';
            themeToggle.title = 'Switch to light mode';
        } else {
            themeIcon.className = 'fas fa-moon';
            themeToggle.title = 'Switch to dark mode';
        }
    },

    // Initialize common event handlers
    initEventHandlers: function() {
        // Handle all AJAX form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.hasAttribute('data-ajax')) {
                e.preventDefault();
                this.handleAjaxForm(form);
            }
        });

        // Handle scrape buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="scrape"]')) {
                e.preventDefault();
                this.handleScrapeJob(e.target);
            }
        });

        // Handle delete buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="delete"]')) {
                e.preventDefault();
                this.handleDelete(e.target);
            }
        });

        // Handle quick log buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="quick-log"]')) {
                e.preventDefault();
                this.handleQuickLog(e.target);
            }
        });
    },

    // Handle AJAX form submission
    handleAjaxForm: async function(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton ? submitButton.innerHTML : '';
        
        try {
            // Show loading state
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
            }

            const response = await window.ajax.submitForm(form);
            
            if (response.success) {
                window.UIUtils.showAlert(response.message || 'Operation completed successfully', 'success');
                
                // Handle redirects
                if (response.redirect) {
                    window.location.href = response.redirect;
                    return;
                }
                
                // Reload page if specified
                if (response.reload) {
                    window.location.reload();
                    return;
                }
            } else {
                window.UIUtils.showAlert(response.error || 'Operation failed', 'error');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            window.UIUtils.showAlert('An error occurred while submitting the form', 'error');
        } finally {
            // Restore button state
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }
        }
    },

    // Handle job scraping
    handleScrapeJob: async function(button) {
        const urlInput = document.getElementById('url');
        if (!urlInput || !urlInput.value.trim()) {
            window.UIUtils.showAlert('Please enter a job posting URL first', 'warning');
            return;
        }

        const url = urlInput.value.trim();
        
        // Validate URL format
        if (!window.UIUtils.isValidURL(url)) {
            window.UIUtils.showAlert('Please enter a valid URL (e.g., https://example.com/job)', 'warning');
            return;
        }

        const originalText = button.innerHTML;
        
        try {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Scraping...';

            const response = await window.ajax.scrapeJob(url);
            
            if (response.success) {
                // Highlight filled fields
                this.highlightFilledFields(['company', 'title', 'description']);
                
                let message = '✅ ' + (response.message || 'Job details scraped successfully!');
                if (response.title || response.company) {
                    message += `\n\n📋 Updated: ${response.title || 'No title'} at ${response.company || 'Unknown company'}`;
                }
                
                window.UIUtils.showAlert(message, 'success');
            }
        } catch (error) {
            console.error('Scraping error:', error);
        } finally {
            button.disabled = false;
            button.innerHTML = originalText;
        }
    },

    // Handle delete operations
    handleDelete: function(button) {
        const itemType = button.getAttribute('data-item-type') || 'item';
        const itemName = button.getAttribute('data-item-name') || 'this item';
        const confirmMessage = button.getAttribute('data-confirm-message') || 
                              `Are you sure you want to delete ${itemType} "${itemName}"?`;
        
        if (confirm(confirmMessage)) {
            const deleteUrl = button.getAttribute('data-delete-url');
            const form = button.closest('form');
            
            if (deleteUrl) {
                // AJAX delete
                this.performDelete(deleteUrl);
            } else if (form) {
                // Form submission
                form.submit();
            }
        }
    },

    // Perform AJAX delete
    performDelete: async function(url) {
        try {
            const response = await window.ajax.delete(url);
            
            if (response.success) {
                window.UIUtils.showAlert(response.message || 'Item deleted successfully', 'success');
                
                // Reload page or redirect
                if (response.redirect) {
                    window.location.href = response.redirect;
                } else {
                    window.location.reload();
                }
            } else {
                window.UIUtils.showAlert(response.error || 'Delete operation failed', 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            window.UIUtils.showAlert('An error occurred while deleting', 'error');
        }
    },

    // Handle quick log
    handleQuickLog: function(button) {
        const jobId = button.getAttribute('data-job-id');
        if (!jobId) return;

        // Show quick log modal (if implemented)
        const modal = document.getElementById('quickLogModal');
        if (modal) {
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
        }
    },

    // Highlight filled fields
    highlightFilledFields: function(fieldIds) {
        fieldIds.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field && field.value.trim()) {
                window.UIUtils.highlightElement(field, 'border-success', 3000);
            }
        });
    },

    // Initialize page-specific functionality
    initPageSpecific: function() {
        const page = document.body.getAttribute('data-page');
        
        switch (page) {
            case 'dashboard':
                this.initDashboard();
                break;
            case 'job-detail':
                this.initJobDetail();
                break;
            case 'new-job':
                this.initNewJob();
                break;
            case 'templates':
                this.initTemplates();
                break;
        }
    },

    // Dashboard specific initialization
    initDashboard: function() {
        // Auto-refresh statistics every 5 minutes
        setInterval(() => {
            this.refreshDashboardStats();
        }, 300000);
    },

    // Job detail specific initialization
    initJobDetail: function() {
        // Initialize log form if present
        const logForm = document.getElementById('logForm');
        if (logForm) {
            this.initLogForm(logForm);
        }
    },

    // New job specific initialization
    initNewJob: function() {
        // Setup auto-save for job form
        const jobForm = document.getElementById('jobForm');
        if (jobForm) {
            window.FormUtils.setupAutoSave(jobForm, 'new_job', this.config.autoSaveInterval);
            
            // Try to restore auto-saved data
            if (window.FormUtils.restoreAutoSave(jobForm, 'new_job')) {
                window.UIUtils.showAlert('Auto-saved data restored', 'info');
            }
        }
    },

    // Templates specific initialization
    initTemplates: function() {
        // Initialize template editor if present
        const editor = document.getElementById('templateEditor');
        if (editor) {
            this.initTemplateEditor(editor);
        }
    },

    // Initialize log form
    initLogForm: function(form) {
        // Setup character counter
        const noteField = form.querySelector('textarea[name="note"]');
        if (noteField) {
            const maxLength = parseInt(noteField.getAttribute('maxlength')) || 1000;
            window.FormUtils.setupCharacterCounter(noteField, maxLength);
        }
    },

    // Initialize template editor
    initTemplateEditor: function(editor) {
        // Add syntax highlighting or other editor features
        console.log('Template editor initialized');
    },

    // Refresh dashboard statistics
    refreshDashboardStats: async function() {
        try {
            const response = await window.ajax.get('/api/dashboard/stats');
            if (response.success) {
                // Update statistics display
                this.updateDashboardStats(response.data);
            }
        } catch (error) {
            console.error('Failed to refresh dashboard stats:', error);
        }
    },

    // Update dashboard statistics display
    updateDashboardStats: function(stats) {
        // Update stat cards with new data
        Object.entries(stats).forEach(([key, value]) => {
            const element = document.getElementById(`stat-${key}`);
            if (element) {
                element.textContent = value;
            }
        });
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.JobApp.init();
});

// Global utility functions for backward compatibility
window.scrapeJob = function() {
    const button = document.querySelector('[data-action="scrape"]');
    if (button) {
        window.JobApp.handleScrapeJob(button);
    }
};

window.showAlert = function(message, type, container) {
    window.UIUtils.showAlert(message, type, container);
};

window.getRelativeTime = function(timestamp) {
    return window.UIUtils.getRelativeTime(timestamp);
};
