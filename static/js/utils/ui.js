/**
 * UI utility functions for common interface operations
 */

class UIUtils {
    constructor() {
        this.alertContainer = null;
        this.defaultAlertTimeout = 5000;
    }

    /**
     * Show alert message
     */
    showAlert(message, type = 'info', container = null, timeout = null) {
        const alertContainer = container || this.getAlertContainer();
        
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${this.getBootstrapAlertClass(type)} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Insert alert
        alertContainer.appendChild(alertDiv);

        // Auto-dismiss for success/info alerts
        if ((type === 'success' || type === 'info') && timeout !== false) {
            const dismissTimeout = timeout || this.defaultAlertTimeout;
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, dismissTimeout);
        }

        return alertDiv;
    }

    /**
     * Get or create alert container
     */
    getAlertContainer() {
        if (!this.alertContainer) {
            this.alertContainer = document.querySelector('.alert-container');
            if (!this.alertContainer) {
                this.alertContainer = document.createElement('div');
                this.alertContainer.className = 'alert-container';
                
                // Insert after main container or at top of body
                const main = document.querySelector('main');
                if (main) {
                    main.insertBefore(this.alertContainer, main.firstChild);
                } else {
                    document.body.insertBefore(this.alertContainer, document.body.firstChild);
                }
            }
        }
        return this.alertContainer;
    }

    /**
     * Convert alert type to Bootstrap class
     */
    getBootstrapAlertClass(type) {
        const typeMap = {
            'error': 'danger',
            'warning': 'warning',
            'success': 'success',
            'info': 'info'
        };
        return typeMap[type] || 'info';
    }

    /**
     * Show loading spinner
     */
    showLoading(element, message = 'Loading...') {
        const loadingHtml = `
            <div class="text-center py-4 loading-spinner">
                <div class="spinner-border text-primary mb-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-muted mb-0">${message}</p>
            </div>
        `;
        element.innerHTML = loadingHtml;
    }

    /**
     * Hide loading spinner
     */
    hideLoading(element) {
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    }

    /**
     * Highlight element temporarily
     */
    highlightElement(element, className = 'border-success', duration = 3000) {
        element.classList.add(className);
        setTimeout(() => {
            element.classList.remove(className);
        }, duration);
    }

    /**
     * Animate element
     */
    animateElement(element, animation = 'fadeIn', duration = 500) {
        element.style.animation = `${animation} ${duration}ms ease-in-out`;
        setTimeout(() => {
            element.style.animation = '';
        }, duration);
    }

    /**
     * Smooth scroll to element
     */
    scrollToElement(element, offset = 0) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showAlert('Copied to clipboard!', 'success');
            return true;
        } catch (err) {
            console.error('Failed to copy text: ', err);
            this.showAlert('Failed to copy to clipboard', 'error');
            return false;
        }
    }

    /**
     * Format relative time
     */
    getRelativeTime(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffInSeconds = Math.floor((now - time) / 1000);

        if (diffInSeconds < 60) {
            return 'just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 2592000) {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days} day${days > 1 ? 's' : ''} ago`;
        } else {
            return time.toLocaleDateString();
        }
    }

    /**
     * Update all relative time elements
     */
    updateRelativeTimes() {
        const elements = document.querySelectorAll('.relative-time');
        elements.forEach(element => {
            const timestamp = element.getAttribute('data-timestamp');
            if (timestamp) {
                element.textContent = `(${this.getRelativeTime(timestamp)})`;
            }
        });
    }

    /**
     * Initialize character counter for textarea
     */
    initCharacterCounter(textareaId, maxLength, counterId = null) {
        const textarea = document.getElementById(textareaId);
        const counter = counterId ? document.getElementById(counterId) : 
                       document.querySelector(`[data-counter-for="${textareaId}"]`);

        if (!textarea || !counter) return;

        const updateCounter = () => {
            const currentLength = textarea.value.length;
            counter.textContent = currentLength;

            // Update counter color based on usage
            counter.className = '';
            if (currentLength > maxLength * 0.9) {
                counter.className = 'text-danger';
            } else if (currentLength > maxLength * 0.8) {
                counter.className = 'text-warning';
            }
        };

        textarea.addEventListener('input', updateCounter);
        updateCounter(); // Initialize
    }

    /**
     * Initialize tooltips
     */
    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    /**
     * Initialize popovers
     */
    initPopovers() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    /**
     * Debounce function
     */
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }

    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    /**
     * Format file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    /**
     * Validate URL format
     */
    isValidURL(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }

    /**
     * Validate email format
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    /**
     * Initialize common UI components
     */
    init() {
        // Initialize Bootstrap components
        this.initTooltips();
        this.initPopovers();

        // Update relative times every minute
        this.updateRelativeTimes();
        setInterval(() => this.updateRelativeTimes(), 60000);

        // Initialize character counters
        document.querySelectorAll('textarea[maxlength]').forEach(textarea => {
            const maxLength = parseInt(textarea.getAttribute('maxlength'));
            const counterId = textarea.getAttribute('data-counter');
            if (counterId) {
                this.initCharacterCounter(textarea.id, maxLength, counterId);
            }
        });
    }
}

// Create global instance
window.UIUtils = new UIUtils();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.UIUtils.init();
});
