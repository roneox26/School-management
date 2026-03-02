/**
 * School Management System - Main JavaScript
 * Handles common functionality across all pages
 */

// ==================== Global Variables ====================
let searchTimeout;

// ==================== DOM Ready ====================
document.addEventListener('DOMContentLoaded', function() {
    initializeMobileMenu();
    initializeQuickSearch();
    initializeNotifications();
    initializeFormHandlers();
    initializeTableEnhancements();
    initializeTooltips();
    initializeAlertAutoHide();
    initializeBackgroundColorControl();
    loadSavedPreferences();
});

// ==================== Mobile Menu ====================
function initializeMobileMenu() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            sidebarOverlay.classList.toggle('show');
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            sidebarOverlay.classList.remove('show');
        });
    }
}

// ==================== Quick Search ====================
function initializeQuickSearch() {
    const quickSearch = document.getElementById('quickSearch');

    if (quickSearch) {
        quickSearch.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performQuickSearch(e.target.value);
            }, 300);
        });

        quickSearch.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                hideSearchResults();
            }
        });
    }

    // Hide search dropdown when clicking outside
    document.addEventListener('click', function(e) {
        const searchBox = document.getElementById('quickSearch');
        const dropdown = document.getElementById('searchDropdown');

        if (dropdown && searchBox && !searchBox.contains(e.target) && !dropdown.contains(e.target)) {
            hideSearchResults();
        }
    });
}

function performQuickSearch(query) {
    if (query.length < 2) {
        hideSearchResults();
        return;
    }

    fetch(`/smart_search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            showSearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
            hideSearchResults();
        });
}

function showSearchResults(results) {
    const dropdown = document.getElementById('searchDropdown');
    if (!dropdown) return;

    if (results.length === 0) {
        dropdown.innerHTML = '<div class="p-3 text-center text-muted">No results found</div>';
        dropdown.style.display = 'block';
        return;
    }

    dropdown.innerHTML = results.map(result => `
        <a href="${result.url}" class="d-block text-decoration-none p-3 rounded-2 hover-bg-light border-bottom">
            <div class="d-flex align-items-center">
                <i class="${result.icon} me-3 text-primary"></i>
                <div>
                    <div class="fw-semibold">${result.title}</div>
                    <small class="text-muted">${result.subtitle}</small>
                </div>
            </div>
        </a>
    `).join('');
    dropdown.style.display = 'block';
}

function hideSearchResults() {
    const dropdown = document.getElementById('searchDropdown');
    if (dropdown) {
        dropdown.style.display = 'none';
    }
}

// ==================== Notifications ====================
function initializeNotifications() {
    loadNotifications();
    // Auto-refresh notifications every 30 seconds
    setInterval(loadNotifications, 30000);
}

function loadNotifications() {
    fetch('/get_notifications')
        .then(response => response.json())
        .then(notifications => {
            updateNotificationUI(notifications);
        })
        .catch(error => console.error('Notification error:', error));
}

function updateNotificationUI(notifications) {
    const badge = document.getElementById('notificationBadge');
    const dropdown = document.getElementById('notificationDropdown');

    if (!badge || !dropdown) return;

    if (notifications.length > 0) {
        badge.textContent = notifications.length;
        badge.style.display = 'block';

        const notificationHTML = notifications.map(notif => `
            <li>
                <a class="dropdown-item py-3" href="${notif.action || '#'}">
                    <div class="d-flex align-items-start">
                        <i class="fas fa-${notif.type === 'warning' ? 'exclamation-triangle text-warning' : notif.type === 'error' ? 'exclamation-circle text-danger' : 'info-circle text-info'} me-3 mt-1"></i>
                        <div class="flex-grow-1">
                            <div class="fw-semibold">${notif.title}</div>
                            <div class="text-muted small">${notif.message}</div>
                            <div class="text-muted small mt-1">${notif.time}</div>
                        </div>
                    </div>
                </a>
            </li>
        `).join('');

        dropdown.innerHTML = `
            <li><h6 class="dropdown-header d-flex justify-content-between align-items-center">
                <span>Notifications</span>
                <span class="badge bg-primary rounded-pill">${notifications.length}</span>
            </h6></li>
            ${notificationHTML}
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item text-center py-2 text-primary" href="/reports">View All Reports</a></li>
        `;
    } else {
        badge.style.display = 'none';
        dropdown.innerHTML = `
            <li><h6 class="dropdown-header">Notifications</h6></li>
            <li><div class="dropdown-item-text text-center text-muted py-3">
                <i class="fas fa-bell-slash mb-2 d-block"></i>
                No new notifications
            </div></li>
        `;
    }
}

// ==================== Form Handlers ====================
function initializeFormHandlers() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Add loading state on submit
        form.addEventListener('submit', function(e) {
            const invalidInputs = form.querySelectorAll(':invalid');
            if (invalidInputs.length > 0) {
                e.preventDefault();
                invalidInputs[0].focus();
                invalidInputs[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                showLoading();
            }
        });
    });
}

// ==================== Table Enhancements ====================
function initializeTableEnhancements() {
    const tableRows = document.querySelectorAll('.table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.005)';
        });

        row.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
}

// ==================== Tooltips ====================
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// ==================== Alert Auto-Hide ====================
function initializeAlertAutoHide() {
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            if (alert.classList.contains('alert-success')) {
                const bsAlert = new bootstrap.Alert(alert);
                setTimeout(() => bsAlert.close(), 5000);
            }
        });
    }, 100);
}

// ==================== Loading Overlay ====================
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Hide loading on page load complete
window.addEventListener('load', hideLoading);

// ==================== Background Color Control ====================
function initializeBackgroundColorControl() {
    setTimeout(function() {
        const bgColorControl = document.createElement('div');
        bgColorControl.className = 'dropdown me-3';
        bgColorControl.innerHTML = `
            <button class="btn btn-link p-2" type="button" data-bs-toggle="dropdown" title="Theme">
                <i class="fas fa-palette fs-5 text-muted"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
                <li><h6 class="dropdown-header">Background Colors</h6></li>
                <li><a class="dropdown-item" href="#" onclick="changeBackgroundColor('#f8fafc'); return false;">Default Light</a></li>
                <li><a class="dropdown-item" href="#" onclick="changeBackgroundColor('#1e293b'); return false;">Dark Blue</a></li>
                <li><a class="dropdown-item" href="#" onclick="changeBackgroundColor('#111827'); return false;">Dark Gray</a></li>
                <li><a class="dropdown-item" href="#" onclick="changeBackgroundColor('#0f172a'); return false;">Night Mode</a></li>
                <li><a class="dropdown-item" href="#" onclick="changeBackgroundColor('#fef3c7'); return false;">Warm Light</a></li>
                <li><a class="dropdown-item" href="#" onclick="changeBackgroundColor('#dcfce7'); return false;">Green Light</a></li>
            </ul>
        `;

        const notificationDropdown = document.querySelector('.d-flex.align-items-center .dropdown');
        if (notificationDropdown) {
            notificationDropdown.parentNode.insertBefore(bgColorControl, notificationDropdown);
        }
    }, 100);
}

function changeBackgroundColor(color) {
    document.documentElement.style.setProperty('--background-color', color);
    localStorage.setItem('custom-bg-color', color);
    
    // Adjust text color for dark backgrounds
    if (color === '#1e293b' || color === '#111827' || color === '#0f172a') {
        document.documentElement.style.setProperty('--text-primary', '#f1f5f9');
        document.documentElement.style.setProperty('--text-secondary', '#cbd5e1');
    } else {
        document.documentElement.style.setProperty('--text-primary', '#1e293b');
        document.documentElement.style.setProperty('--text-secondary', '#64748b');
    }
}

function loadSavedPreferences() {
    const savedBgColor = localStorage.getItem('custom-bg-color');
    if (savedBgColor) {
        changeBackgroundColor(savedBgColor);
    }
}

// ==================== Smooth Page Navigation ====================
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            if (this.href && !this.href.includes('#')) {
                e.preventDefault();
                showLoading();
                setTimeout(() => {
                    window.location.href = this.href;
                }, 150);
            }
        });
    });
});

// ==================== Toast Notification System ====================
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const iconMap = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${iconMap[type]} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// ==================== Bulk Operations ====================
function initializeBulkOperations() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionButtons();
        });
    }
    
    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActionButtons);
    });
}

function updateBulkActionButtons() {
    const selectedItems = document.querySelectorAll('.item-checkbox:checked');
    const bulkActionButtons = document.querySelectorAll('.bulk-action-btn');
    
    if (selectedItems.length > 0) {
        bulkActionButtons.forEach(btn => btn.disabled = false);
    } else {
        bulkActionButtons.forEach(btn => btn.disabled = true);
    }
}

function getSelectedItems() {
    const checkboxes = document.querySelectorAll('.item-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// ==================== Confirmation Dialog ====================
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// ==================== Export Utilities ====================
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const csvRow = Array.from(cols).map(col => {
            return '"' + col.textContent.trim().replace(/"/g, '""') + '"';
        });
        csv.push(csvRow.join(','));
    });
    
    downloadCSV(csv.join('\n'), filename);
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', filename);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// ==================== Date Utilities ====================
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ==================== Number Utilities ====================
function formatCurrency(amount) {
    return '৳' + parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    });
}

// ==================== Debounce Utility ====================
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== Make functions globally available ====================
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.changeBackgroundColor = changeBackgroundColor;
window.confirmAction = confirmAction;
window.exportTableToCSV = exportTableToCSV;
window.formatDate = formatDate;
window.formatDateTime = formatDateTime;
window.formatCurrency = formatCurrency;
window.getSelectedItems = getSelectedItems;
