// Task Pro JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap components
    initializeBootstrapComponents();

    // Setup auto-hiding alerts
    setupAutoHideAlerts();

    // Setup confirmation dialogs
    setupConfirmationDialogs();

    // Setup AJAX forms
    setupAjaxForms();

    // Setup real-time updates
    setupRealTimeUpdates();

    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
});

/**
 * Initialize Bootstrap components
 */
function initializeBootstrapComponents() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover'
        });
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup auto-hiding alerts
 */
function setupAutoHideAlerts() {
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            // Add fade out animation
            alert.style.transition = 'opacity 0.5s ease-out';
            alert.style.opacity = '0';

            setTimeout(function() {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 500);
        });
    }, 5000);
}

/**
 * Setup confirmation dialogs for dangerous actions
 */
function setupConfirmationDialogs() {
    // Delete confirmations
    var deleteLinks = document.querySelectorAll('.confirm-delete, [href*="delete"]');
    deleteLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Approval confirmations
    var approvalForms = document.querySelectorAll('form[action*="approve"]');
    approvalForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to approve this task?')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Rejection confirmations
    var rejectionForms = document.querySelectorAll('form[action*="reject"]');
    rejectionForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var notesField = form.querySelector('[name="approval_notes"]');
            if (!notesField || !notesField.value.trim()) {
                alert('Please provide rejection notes before rejecting the task.');
                e.preventDefault();
                return false;
            }
            if (!confirm('Are you sure you want to reject this task?')) {
                e.preventDefault();
                return false;
            }
        });
    });
}

/**
 * Setup AJAX forms for status updates
 */
function setupAjaxForms() {
    // Status update forms
    var statusForms = document.querySelectorAll('[data-ajax-form]');
    statusForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitAjaxForm(form);
        });
    });

    // Quick status updates
    var statusSelects = document.querySelectorAll('select[name="status"][onchange]');
    statusSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            updateTaskStatus(select);
        });
    });
}

/**
 * Submit AJAX form
 * @param {HTMLFormElement} form 
 */
function submitAjaxForm(form) {
    var formData = new FormData(form);
    var submitBtn = form.querySelector('button[type="submit"]');
    var originalText = submitBtn ? submitBtn.innerHTML : '';

    // Show loading state
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    }

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Success', data.message || 'Operation completed successfully', 'success');
            // Reload page or update UI as needed
            if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                location.reload();
            }
        } else {
            showNotification('Error', data.error || 'An error occurred', 'danger');
        }
    })
    .catch(error => {
        console.error('AJAX Error:', error);
        showNotification('Error', 'A network error occurred', 'danger');
    })
    .finally(() => {
        // Restore button state
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    });
}

/**
 * Update task status via AJAX
 * @param {HTMLSelectElement} selectElement 
 */
function updateTaskStatus(selectElement) {
    var form = selectElement.closest('form');
    if (!form) return;

    var formData = new FormData(form);

    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Status Updated', 'Task status has been updated successfully', 'success');
            // Update UI elements
            updateStatusBadges(data.new_status);
        } else {
            showNotification('Error', data.error || 'Failed to update status', 'danger');
            // Reset select to previous value
            selectElement.value = selectElement.dataset.previousValue || selectElement.value;
        }
    })
    .catch(error => {
        console.error('Status Update Error:', error);
        showNotification('Error', 'Failed to update status', 'danger');
        selectElement.value = selectElement.dataset.previousValue || selectElement.value;
    });

    // Store current value for potential rollback
    selectElement.dataset.previousValue = selectElement.value;
}

/**
 * Update status badges in the UI
 * @param {string} newStatus 
 */
function updateStatusBadges(newStatus) {
    var statusBadges = document.querySelectorAll('.badge[class*="status-"]');
    statusBadges.forEach(function(badge) {
        // Remove old status classes
        badge.className = badge.className.replace(/status-\S+/g, '');
        // Add new status class
        badge.classList.add('status-' + newStatus);
        // Update text
        badge.textContent = getStatusDisplayText(newStatus);
    });
}

/**
 * Get display text for status
 * @param {string} status 
 * @returns {string}
 */
function getStatusDisplayText(status) {
    var statusMap = {
        'assigned': 'Assigned',
        'in_progress': 'In Progress',
        'completed': 'Completed (Pending Approval)',
        'approved': 'Approved',
        'rejected': 'Rejected',
        'cancelled': 'Cancelled',
        'on_hold': 'On Hold'
    };
    return statusMap[status] || status;
}

/**
 * Setup real-time updates (using polling for now)
 */
function setupRealTimeUpdates() {
    // Update notification count periodically
    if (document.querySelector('.notification-count')) {
        setInterval(updateNotificationCount, 30000); // Every 30 seconds
    }

    // Update dashboard stats periodically
    if (document.querySelector('.stat-number')) {
        setInterval(updateDashboardStats, 60000); // Every minute
    }
}

/**
 * Update notification count
 */
function updateNotificationCount() {
    fetch('/ajax/notification-count/', {
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        var countElement = document.querySelector('.notification-count');
        if (countElement && data.count !== undefined) {
            if (data.count > 0) {
                countElement.textContent = data.count;
                countElement.style.display = 'inline';
            } else {
                countElement.style.display = 'none';
            }
        }
    })
    .catch(error => console.log('Notification update error:', error));
}

/**
 * Update dashboard statistics
 */
function updateDashboardStats() {
    fetch('/ajax/task-stats/', {
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        // Update stat numbers
        Object.keys(data).forEach(function(key) {
            var element = document.querySelector(`.stat-${key} .stat-number`);
            if (element) {
                animateNumber(element, parseInt(element.textContent), data[key]);
            }
        });
    })
    .catch(error => console.log('Stats update error:', error));
}

/**
 * Animate number change
 * @param {HTMLElement} element 
 * @param {number} from 
 * @param {number} to 
 */
function animateNumber(element, from, to) {
    if (from === to) return;

    var duration = 1000;
    var startTime = Date.now();

    function update() {
        var now = Date.now();
        var progress = Math.min((now - startTime) / duration, 1);
        var current = Math.floor(from + (to - from) * progress);

        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/**
 * Setup keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + N for new task (admin only)
        if ((e.ctrlKey || e.metaKey) && e.key === 'n' && document.querySelector('[href*="task/create"]')) {
            e.preventDefault();
            window.location.href = document.querySelector('[href*="task/create"]').href;
        }

        // Ctrl/Cmd + / for search
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            var searchField = document.querySelector('input[placeholder*="search"], input[placeholder*="Search"]');
            if (searchField) {
                searchField.focus();
            }
        }

        // ESC to close modals
        if (e.key === 'Escape') {
            var modals = document.querySelectorAll('.modal.show');
            modals.forEach(function(modal) {
                var bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
}

/**
 * Show notification toast
 * @param {string} title 
 * @param {string} message 
 * @param {string} type 
 */
function showNotification(title, message, type = 'info') {
    // Create notification element
    var notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';

    notification.innerHTML = `
        <strong>${title}</strong> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(function() {
        if (notification.parentNode) {
            notification.classList.remove('show');
            setTimeout(function() {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 150);
        }
    }, 5000);
}

/**
 * Get CSRF token from cookies or form
 * @returns {string}
 */
function getCsrfToken() {
    var token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) {
        return token.value;
    }

    // Try to get from cookie
    var name = 'csrftoken';
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Format date for display
 * @param {Date} date 
 * @returns {string}
 */
function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

/**
 * Debounce function calls
 * @param {Function} func 
 * @param {number} wait 
 * @returns {Function}
 */
function debounce(func, wait) {
    var timeout;
    return function executedFunction(...args) {
        var later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Setup search functionality with debouncing
 */
function setupSearch() {
    var searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="search"], input[placeholder*="Search"]');

    searchInputs.forEach(function(input) {
        var debouncedSearch = debounce(function(query) {
            performSearch(query, input);
        }, 300);

        input.addEventListener('input', function(e) {
            debouncedSearch(e.target.value);
        });
    });
}

/**
 * Perform search operation
 * @param {string} query 
 * @param {HTMLInputElement} input 
 */
function performSearch(query, input) {
    if (query.length < 2) return;

    var form = input.closest('form');
    if (form) {
        // Auto-submit search form after delay
        setTimeout(function() {
            form.submit();
        }, 100);
    }
}

// Initialize additional features
document.addEventListener('DOMContentLoaded', function() {
    setupSearch();
});

// Export functions for global access
window.TaskManager = {
    showNotification: showNotification,
    updateTaskStatus: updateTaskStatus,
    getCsrfToken: getCsrfToken,
    formatDate: formatDate,
    debounce: debounce
};
