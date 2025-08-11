/**
 * Form utility functions for validation and handling
 */

class FormUtils {
    constructor() {
        this.validators = {};
        this.defaultErrorClass = 'is-invalid';
        this.defaultSuccessClass = 'is-valid';
    }

    /**
     * Add custom validator
     */
    addValidator(name, validatorFunction) {
        this.validators[name] = validatorFunction;
    }

    /**
     * Validate single field
     */
    validateField(field, rules = []) {
        const value = field.value.trim();
        const errors = [];

        for (const rule of rules) {
            if (typeof rule === 'string') {
                // Built-in validator
                const error = this.runBuiltInValidator(rule, value, field);
                if (error) errors.push(error);
            } else if (typeof rule === 'function') {
                // Custom validator function
                const error = rule(value, field);
                if (error) errors.push(error);
            } else if (typeof rule === 'object') {
                // Validator with options
                const { validator, message, ...options } = rule;
                const error = this.runValidator(validator, value, field, options, message);
                if (error) errors.push(error);
            }
        }

        this.showFieldValidation(field, errors);
        return errors.length === 0;
    }

    /**
     * Run built-in validator
     */
    runBuiltInValidator(validator, value, field) {
        switch (validator) {
            case 'required':
                return value === '' ? 'This field is required' : null;
            
            case 'email':
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return value && !emailRegex.test(value) ? 'Please enter a valid email address' : null;
            
            case 'url':
                try {
                    if (value) new URL(value);
                    return null;
                } catch {
                    return 'Please enter a valid URL';
                }
            
            case 'phone':
                const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
                return value && !phoneRegex.test(value.replace(/[\s\-\(\)\.]/g, '')) ? 
                       'Please enter a valid phone number' : null;
            
            case 'number':
                return value && isNaN(value) ? 'Please enter a valid number' : null;
            
            default:
                return null;
        }
    }

    /**
     * Run custom validator
     */
    runValidator(validatorName, value, field, options = {}, customMessage = null) {
        if (this.validators[validatorName]) {
            const result = this.validators[validatorName](value, field, options);
            return result === true ? null : (customMessage || result);
        }
        return null;
    }

    /**
     * Show field validation state
     */
    showFieldValidation(field, errors = []) {
        // Remove existing validation classes
        field.classList.remove(this.defaultErrorClass, this.defaultSuccessClass);
        
        // Remove existing error messages
        const existingError = field.parentNode.querySelector('.invalid-feedback');
        if (existingError) {
            existingError.remove();
        }

        if (errors.length > 0) {
            // Show error state
            field.classList.add(this.defaultErrorClass);
            
            // Create error message element
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.textContent = errors[0]; // Show first error
            
            field.parentNode.appendChild(errorDiv);
        } else if (field.value.trim() !== '') {
            // Show success state for non-empty fields
            field.classList.add(this.defaultSuccessClass);
        }
    }

    /**
     * Validate entire form
     */
    validateForm(form, validationRules = {}) {
        let isValid = true;
        const errors = {};

        // Validate each field with rules
        for (const [fieldName, rules] of Object.entries(validationRules)) {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const fieldValid = this.validateField(field, rules);
                if (!fieldValid) {
                    isValid = false;
                    errors[fieldName] = 'Validation failed';
                }
            }
        }

        return { isValid, errors };
    }

    /**
     * Setup real-time validation
     */
    setupRealTimeValidation(form, validationRules = {}) {
        for (const [fieldName, rules] of Object.entries(validationRules)) {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                // Validate on blur
                field.addEventListener('blur', () => {
                    this.validateField(field, rules);
                });

                // Clear validation on focus
                field.addEventListener('focus', () => {
                    field.classList.remove(this.defaultErrorClass, this.defaultSuccessClass);
                    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
                    if (errorDiv) errorDiv.remove();
                });
            }
        }
    }

    /**
     * Serialize form data to object
     */
    serializeForm(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            if (data[key]) {
                // Handle multiple values (checkboxes, etc.)
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }

    /**
     * Populate form with data
     */
    populateForm(form, data) {
        for (const [key, value] of Object.entries(data)) {
            const field = form.querySelector(`[name="${key}"]`);
            if (field) {
                if (field.type === 'checkbox' || field.type === 'radio') {
                    field.checked = field.value === value;
                } else {
                    field.value = value;
                }
            }
        }
    }

    /**
     * Clear form validation
     */
    clearValidation(form) {
        const fields = form.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            field.classList.remove(this.defaultErrorClass, this.defaultSuccessClass);
            const errorDiv = field.parentNode.querySelector('.invalid-feedback');
            if (errorDiv) errorDiv.remove();
        });
    }

    /**
     * Reset form
     */
    resetForm(form) {
        form.reset();
        this.clearValidation(form);
    }

    /**
     * Handle form submission with AJAX
     */
    async submitFormAjax(form, options = {}) {
        const {
            onSuccess = null,
            onError = null,
            showLoading = true,
            validateBeforeSubmit = true,
            validationRules = {}
        } = options;

        // Validate form if rules provided
        if (validateBeforeSubmit && Object.keys(validationRules).length > 0) {
            const validation = this.validateForm(form, validationRules);
            if (!validation.isValid) {
                return { success: false, errors: validation.errors };
            }
        }

        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton ? submitButton.innerHTML : '';
        
        if (showLoading && submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Submitting...';
        }

        try {
            const response = await window.ajax.submitForm(form, {
                onSuccess: onSuccess,
                onError: onError
            });

            return response;
        } catch (error) {
            console.error('Form submission error:', error);
            return { success: false, error: error.message };
        } finally {
            // Restore button state
            if (showLoading && submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            }
        }
    }

    /**
     * Auto-save form data to localStorage
     */
    setupAutoSave(form, key, interval = 30000) {
        const saveData = () => {
            const data = this.serializeForm(form);
            localStorage.setItem(`autosave_${key}`, JSON.stringify(data));
        };

        // Save on input changes
        form.addEventListener('input', window.UIUtils.debounce(saveData, 1000));

        // Save periodically
        const intervalId = setInterval(saveData, interval);

        // Return cleanup function
        return () => {
            clearInterval(intervalId);
            localStorage.removeItem(`autosave_${key}`);
        };
    }

    /**
     * Restore auto-saved form data
     */
    restoreAutoSave(form, key) {
        const savedData = localStorage.getItem(`autosave_${key}`);
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                this.populateForm(form, data);
                return true;
            } catch (error) {
                console.error('Error restoring auto-saved data:', error);
                localStorage.removeItem(`autosave_${key}`);
            }
        }
        return false;
    }

    /**
     * Setup character counter for textarea
     */
    setupCharacterCounter(textarea, maxLength, counterElement = null) {
        if (!counterElement) {
            // Create counter element
            counterElement = document.createElement('small');
            counterElement.className = 'form-text text-end';
            textarea.parentNode.appendChild(counterElement);
        }

        const updateCounter = () => {
            const currentLength = textarea.value.length;
            counterElement.textContent = `${currentLength}/${maxLength}`;
            
            // Update color based on usage
            if (currentLength > maxLength * 0.9) {
                counterElement.className = 'form-text text-end text-danger';
            } else if (currentLength > maxLength * 0.8) {
                counterElement.className = 'form-text text-end text-warning';
            } else {
                counterElement.className = 'form-text text-end text-muted';
            }
        };

        textarea.addEventListener('input', updateCounter);
        updateCounter(); // Initialize
    }

    /**
     * Initialize form utilities
     */
    init() {
        // Setup common validators
        this.addValidator('minLength', (value, field, options) => {
            const minLength = options.length || 0;
            return value.length >= minLength ? true : `Minimum ${minLength} characters required`;
        });

        this.addValidator('maxLength', (value, field, options) => {
            const maxLength = options.length || Infinity;
            return value.length <= maxLength ? true : `Maximum ${maxLength} characters allowed`;
        });

        this.addValidator('match', (value, field, options) => {
            const matchField = document.querySelector(`[name="${options.field}"]`);
            return matchField && value === matchField.value ? true : 'Fields do not match';
        });

        // Auto-setup character counters
        document.querySelectorAll('textarea[maxlength]').forEach(textarea => {
            const maxLength = parseInt(textarea.getAttribute('maxlength'));
            this.setupCharacterCounter(textarea, maxLength);
        });
    }
}

// Create global instance
window.FormUtils = new FormUtils();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.FormUtils.init();
});
