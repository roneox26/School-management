/**
 * Theme Manager for School Management System
 * Handles dark mode toggle and theme persistence
 */

class ThemeManager {
    constructor() {
        this.currentTheme = this.getSavedTheme() || 'light';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        this.createThemeToggle();
        this.addKeyboardShortcut();
    }

    getSavedTheme() {
        return localStorage.getItem('theme');
    }

    saveTheme(theme) {
        localStorage.setItem('theme', theme);
    }

    applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
        this.currentTheme = theme;
        this.saveTheme(theme);
        this.updateToggleButton();
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        this.showThemeNotification(newTheme);
    }

    createThemeToggle() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.insertToggleButton());
        } else {
            this.insertToggleButton();
        }
    }

    insertToggleButton() {
        const themeToggle = document.createElement('div');
        themeToggle.className = 'dropdown me-2';
        themeToggle.id = 'themeToggleContainer';
        themeToggle.innerHTML = `
            <button class="btn btn-link p-2" type="button" id="themeToggleBtn" title="Toggle Theme (Ctrl+Shift+T)">
                <i class="fas fa-moon fs-5 text-muted" id="themeIcon"></i>
            </button>
        `;

        // Find the notification dropdown and insert before it
        const targetContainer = document.querySelector('.top-navbar .d-flex.align-items-center');
        if (targetContainer) {
            const firstChild = targetContainer.firstElementChild;
            if (firstChild) {
                targetContainer.insertBefore(themeToggle, firstChild);
            } else {
                targetContainer.appendChild(themeToggle);
            }
        }

        // Add click event
        const toggleBtn = document.getElementById('themeToggleBtn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleTheme());
        }

        // Update initial icon
        this.updateToggleButton();
    }

    updateToggleButton() {
        const icon = document.getElementById('themeIcon');
        if (icon) {
            if (this.currentTheme === 'dark') {
                icon.className = 'fas fa-sun fs-5 text-warning';
            } else {
                icon.className = 'fas fa-moon fs-5 text-muted';
            }
        }
    }

    addKeyboardShortcut() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+Shift+T to toggle theme
            if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                this.toggleTheme();
            }
        });
    }

    showThemeNotification(theme) {
        const message = theme === 'dark' ? 'Dark mode enabled' : 'Light mode enabled';
        const icon = theme === 'dark' ? 'moon' : 'sun';

        // Check if showToast function exists
        if (typeof window.showToast === 'function') {
            window.showToast(message, 'info');
        } else {
            // Fallback notification
            this.showFallbackNotification(message, icon);
        }
    }

    showFallbackNotification(message, icon) {
        const notification = document.createElement('div');
        notification.className = 'position-fixed top-0 end-0 m-3 p-3 bg-primary text-white rounded shadow-lg';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            <i class="fas fa-${icon} me-2"></i>
            ${message}
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    // Public method to get current theme
    getTheme() {
        return this.currentTheme;
    }

    // Public method to set theme programmatically
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.applyTheme(theme);
        }
    }
}

// Initialize theme manager when DOM is ready
let themeManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        themeManager = new ThemeManager();
        window.themeManager = themeManager;
    });
} else {
    themeManager = new ThemeManager();
    window.themeManager = themeManager;
}

// Export for use in other scripts
window.ThemeManager = ThemeManager;
