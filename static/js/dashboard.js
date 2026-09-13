/**
 * Dashboard-specific JavaScript
 * Handles charts, statistics, and dashboard widgets
 */

// ==================== Chart Initialization ====================
let attendanceChart, feeChart;

document.addEventListener('DOMContentLoaded', function () {
    initializeCharts();
    initializeSmartNotifications();
    initializeUptime();
    initializeRealTimeUpdates();
});

// ==================== Charts ====================
function initializeCharts() {
    const attendanceCanvas = document.getElementById('attendanceChart');
    const feeCanvas = document.getElementById('feeChart');

    if (attendanceCanvas) {
        initializeAttendanceChart();
    }

    if (feeCanvas) {
        initializeFeeChart();
    }
}

function initializeAttendanceChart() {
    const ctx = document.getElementById('attendanceChart').getContext('2d');

    attendanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Student Attendance %',
                data: [85, 92, 78, 88, 90, 75, 82],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.4,
                fill: true
            }, {
                label: 'Teacher Attendance %',
                data: [95, 98, 88, 92, 94, 85, 90],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function (value) {
                            return value + '%';
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

function initializeFeeChart() {
    const ctx = document.getElementById('feeChart').getContext('2d');

    // Get data from template variables (if available)
    const collectedFees = parseFloat(document.getElementById('feeChart').dataset.collected || 0);
    const pendingFees = parseFloat(document.getElementById('feeChart').dataset.pending || 0);
    const overdueFees = parseFloat(document.getElementById('feeChart').dataset.overdue || 5000);

    feeChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Collected', 'Pending', 'Overdue'],
            datasets: [{
                data: [collectedFees, pendingFees, overdueFees],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(255, 99, 132, 0.8)'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return label + ': ৳' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// ==================== Smart Notifications ====================
function initializeSmartNotifications() {
    const container = document.getElementById('smartNotifications');
    if (!container) return;

    const notifications = generateSmartNotifications();
    renderSmartNotifications(notifications);
}

function generateSmartNotifications() {
    const notifications = [];

    // Get data from page (you can pass this from Flask template)
    const attendancePercentage = parseFloat(document.querySelector('[data-attendance]')?.dataset.attendance || 100);
    const teacherAttendance = parseFloat(document.querySelector('[data-teacher-attendance]')?.dataset.teacherAttendance || 100);
    const totalFees = parseFloat(document.querySelector('[data-total-fees]')?.dataset.totalFees || 0);
    const recentSmsCount = parseInt(document.querySelector('[data-sms-count]')?.dataset.smsCount || 0);

    // Low attendance alert
    if (attendancePercentage < 80) {
        notifications.push({
            type: 'warning',
            icon: 'fas fa-exclamation-triangle',
            message: `Today's attendance is ${attendancePercentage}% - Below target of 80%`,
            action: 'View Attendance',
            actionUrl: '/attendance'
        });
    }

    // Fee collection alert
    if (totalFees > 50000) {
        notifications.push({
            type: 'info',
            icon: 'fas fa-money-bill-wave',
            message: `৳${totalFees.toLocaleString()} in pending fees - Send reminders?`,
            action: 'Send SMS Reminders',
            actionUrl: '/send_sms'
        });
    }

    // Teacher attendance
    if (teacherAttendance < 90) {
        notifications.push({
            type: 'warning',
            icon: 'fas fa-user-tie',
            message: `Teacher attendance is ${teacherAttendance}%`,
            action: 'Check Details',
            actionUrl: '/teacher_attendance'
        });
    }

    // Recent SMS activity
    if (recentSmsCount > 0) {
        notifications.push({
            type: 'success',
            icon: 'fas fa-sms',
            message: `${recentSmsCount} SMS sent recently`,
            action: 'View SMS Log',
            actionUrl: '/sms_management'
        });
    }

    return notifications;
}

function renderSmartNotifications(notifications) {
    const container = document.getElementById('smartNotifications');
    if (!container) return;

    if (notifications.length === 0) {
        container.innerHTML = '<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>All systems running smoothly!</div>';
        return;
    }

    container.innerHTML = notifications.map(notif => `
        <div class="alert alert-${notif.type} alert-dismissible fade show" role="alert">
            <i class="${notif.icon} me-2"></i>
            ${notif.message}
            <a href="${notif.actionUrl}" class="btn btn-sm btn-outline-${notif.type} ms-2">${notif.action}</a>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `).join('');
}

// ==================== Uptime Counter ====================
function initializeUptime() {
    const uptimeElement = document.getElementById('uptime');
    if (!uptimeElement) return;

    updateUptime();
    setInterval(updateUptime, 60000); // Update every minute
}

function updateUptime() {
    const uptimeElement = document.getElementById('uptime');
    if (!uptimeElement) return;

    // Get start time from data attribute or use current time
    const startTime = new Date(uptimeElement.dataset.startTime || Date.now());
    const now = new Date();
    const diff = now - startTime;

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    uptimeElement.textContent = `${hours}h ${minutes}m`;
}

// ==================== Real-time Updates ====================
function initializeRealTimeUpdates() {
    // Update statistics every 5 minutes
    setInterval(refreshDashboardStats, 300000);
}

function refreshDashboardStats() {
    fetch('/api/dashboard_stats')
        .then(response => response.json())
        .then(data => {
            updateDashboardStats(data);
        })
        .catch(error => console.error('Error refreshing stats:', error));
}

function updateDashboardStats(data) {
    // Update stat cards
    const statCards = {
        'total_students': data.total_students,
        'total_teachers': data.total_teachers,
        'total_classes': data.total_classes,
        'attendance_percentage': data.attendance_percentage
    };

    Object.keys(statCards).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            animateValue(element, parseFloat(element.textContent), statCards[key], 1000);
        }
    });
}

function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current);
    }, 16);
}

// ==================== Export Dashboard ====================
function exportDashboard() {
    window.print();
}

// ==================== Widget Customization ====================
function toggleWidget(widgetId) {
    const widget = document.getElementById(widgetId);
    if (widget) {
        widget.classList.toggle('d-none');
        saveWidgetPreferences();
    }
}

function saveWidgetPreferences() {
    const widgets = document.querySelectorAll('[data-widget]');
    const preferences = {};

    widgets.forEach(widget => {
        const id = widget.dataset.widget;
        preferences[id] = !widget.classList.contains('d-none');
    });

    localStorage.setItem('dashboard_widgets', JSON.stringify(preferences));
}

function loadWidgetPreferences() {
    const saved = localStorage.getItem('dashboard_widgets');
    if (!saved) return;

    const preferences = JSON.parse(saved);
    Object.keys(preferences).forEach(id => {
        const widget = document.querySelector(`[data-widget="${id}"]`);
        if (widget && !preferences[id]) {
            widget.classList.add('d-none');
        }
    });
}

// Load widget preferences on page load
document.addEventListener('DOMContentLoaded', loadWidgetPreferences);

// ==================== Make functions globally available ====================
window.exportDashboard = exportDashboard;
window.toggleWidget = toggleWidget;
window.refreshDashboardStats = refreshDashboardStats;
