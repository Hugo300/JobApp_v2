/**
 * AJAX utility functions for consistent API communication
 */

class AjaxHelper {
    constructor() {
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };
    }

    /**
     * Get CSRF token from the page
     */
    getCSRFToken() {
        const token = document.querySelector('input[name="csrf_token"]');
        return token ? token.value : null;
    }

    /**
     * Add CSRF token to headers
     */
    addCSRFToken(headers = {}) {
        const token = this.getCSRFToken();
        if (token) {
            headers['X-CSRFToken'] = token;
        }
        return headers;
    }

    /**
     * Generic AJAX request handler
     */
    async request(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: this.addCSRFToken(this.defaultHeaders),
            credentials: 'same-origin'
        };

        const finalOptions = { ...defaultOptions, ...options };
        
        // Merge headers
        if (options.headers) {
            finalOptions.headers = { ...finalOptions.headers, ...options.headers };
        }

        try {
            const response = await fetch(url, finalOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('AJAX request failed:', error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(url, params = {}) {
        const urlParams = new URLSearchParams(params);
        const fullUrl = urlParams.toString() ? `${url}?${urlParams}` : url;
        
        return this.request(fullUrl, { method: 'GET' });
    }

    /**
     * POST request
     */
    async post(url, data = {}) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * POST form data
     */
    async postForm(url, formData) {
        const headers = this.addCSRFToken({});
        delete headers['Content-Type']; // Let browser set it for FormData
        
        return this.request(url, {
            method: 'POST',
            headers: headers,
            body: formData
        });
    }

    /**
     * PUT request
     */
    async put(url, data = {}) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }

    /**
     * Upload file with progress tracking
     */
    async uploadFile(url, file, onProgress = null) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            const formData = new FormData();
            formData.append('file', file);

            // Add CSRF token
            const token = this.getCSRFToken();
            if (token) {
                formData.append('csrf_token', token);
            }

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    onProgress(percentComplete);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } catch (e) {
                        resolve(xhr.responseText);
                    }
                } else {
                    reject(new Error(`Upload failed with status: ${xhr.status}`));
                }
            });

            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });

            xhr.open('POST', url);
            xhr.send(formData);
        });
    }

    /**
     * Handle common response patterns
     */
    handleResponse(response, options = {}) {
        const {
            onSuccess = null,
            onError = null,
            showSuccessMessage = true,
            showErrorMessage = true,
            successMessageContainer = null,
            errorMessageContainer = null
        } = options;

        if (response.success) {
            if (onSuccess) {
                onSuccess(response);
            }
            if (showSuccessMessage && response.message) {
                this.showMessage(response.message, 'success', successMessageContainer);
            }
        } else {
            if (onError) {
                onError(response);
            }
            if (showErrorMessage) {
                const errorMsg = response.error || response.message || 'An error occurred';
                this.showMessage(errorMsg, 'error', errorMessageContainer);
            }
        }

        return response;
    }

    /**
     * Show message to user
     */
    showMessage(message, type = 'info', container = null) {
        // Use the UI utility to show messages
        if (window.UIUtils) {
            window.UIUtils.showAlert(message, type, container);
        } else {
            // Fallback to alert
            alert(message);
        }
    }

    /**
     * Scrape job details from URL
     */
    async scrapeJob(url) {
        try {
            const response = await this.post('/job/scrape', { url: url });
            return this.handleResponse(response, {
                onSuccess: (data) => {
                    // Auto-fill form fields if they exist
                    if (data.title) {
                        const titleField = document.getElementById('title');
                        if (titleField) titleField.value = data.title;
                    }
                    if (data.company) {
                        const companyField = document.getElementById('company');
                        if (companyField) companyField.value = data.company;
                    }
                    if (data.description) {
                        const descField = document.getElementById('description');
                        if (descField) descField.value = data.description;
                    }
                }
            });
        } catch (error) {
            this.showMessage('Failed to scrape job details: ' + error.message, 'error');
            throw error;
        }
    }

    /**
     * Submit form via AJAX
     */
    async submitForm(form, options = {}) {
        const formData = new FormData(form);
        const url = form.action || window.location.href;
        
        try {
            const response = await this.postForm(url, formData);
            return this.handleResponse(response, options);
        } catch (error) {
            this.showMessage('Form submission failed: ' + error.message, 'error');
            throw error;
        }
    }

    /**
     * Load content into element
     */
    async loadContent(url, targetElement, showLoading = true) {
        if (showLoading) {
            targetElement.innerHTML = '<div class="text-center py-3"><div class="spinner-border" role="status"></div></div>';
        }

        try {
            const content = await this.get(url);
            targetElement.innerHTML = content;
        } catch (error) {
            targetElement.innerHTML = `<div class="alert alert-danger">Failed to load content: ${error.message}</div>`;
            throw error;
        }
    }
}

// Create global instance
window.AjaxHelper = new AjaxHelper();

// Convenience functions
window.ajax = {
    get: (url, params) => window.AjaxHelper.get(url, params),
    post: (url, data) => window.AjaxHelper.post(url, data),
    postForm: (url, formData) => window.AjaxHelper.postForm(url, formData),
    put: (url, data) => window.AjaxHelper.put(url, data),
    delete: (url) => window.AjaxHelper.delete(url),
    upload: (url, file, onProgress) => window.AjaxHelper.uploadFile(url, file, onProgress),
    scrapeJob: (url) => window.AjaxHelper.scrapeJob(url),
    submitForm: (form, options) => window.AjaxHelper.submitForm(form, options),
    loadContent: (url, element, showLoading) => window.AjaxHelper.loadContent(url, element, showLoading)
};
