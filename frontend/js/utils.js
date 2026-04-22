/**
 * SmartStock - Утилиты и общие функции
 */

const Utils = {
    /**
     * Форматирование числа в валюту (рубли)
     */
    formatCurrency(value) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        }).format(value);
    },

    /**
     * Форматирование числа с разделителями
     */
    formatNumber(value) {
        return new Intl.NumberFormat('ru-RU').format(value);
    },

    /**
     * Форматирование даты
     */
    formatDate(dateString) {
        if (!dateString) return '—';
        return new Date(dateString).toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
        });
    },

    /**
     * Форматирование даты и времени
     */
    formatDateTime(dateString) {
        if (!dateString) return '—';
        return new Date(dateString).toLocaleString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    },

    /**
     * Получить класс статуса для остатков
     */
    getStockStatusClass(stock, threshold = 10) {
        if (stock <= 0) return 'status-out-of-stock';
        if (stock <= threshold) return 'status-low-stock';
        return 'status-in-stock';
    },

    /**
     * Получить текст статуса для остатков
     */
    getStockStatusText(stock, threshold = 10) {
        if (stock <= 0) return 'Нет на складе';
        if (stock <= threshold) return 'Мало на складе';
        return 'В наличии';
    },

    /**
     * Показать уведомление
     */
    showToast(message, type = 'info') {
        // Удаляем старые уведомления
        const existingToasts = document.querySelectorAll('.toast');
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `toast ${
            type === 'success' ? 'toast-success' :
            type === 'error' ? 'toast-error' :
            'toast-info'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    /**
     * Показать спиннер загрузки
     */
    showLoading(element) {
        if (!element) return;
        element.disabled = true;
        element.dataset.originalText = element.textContent;
        element.innerHTML = '<span class="spinner"></span> Загрузка...';
    },

    /**
     * Скрыть спиннер загрузки
     */
    hideLoading(element) {
        if (!element) return;
        element.disabled = false;
        element.textContent = element.dataset.originalText || 'Загрузка...';
    },

    /**
     * Получить параметры из URL
     */
    getUrlParams() {
        return Object.fromEntries(new URLSearchParams(window.location.search));
    },

    /**
     * Дебаунс функции
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Получить query параметр по имени
     */
    getQueryParam(name) {
        const params = new URLSearchParams(window.location.search);
        return params.get(name);
    },

    /**
     * Проверка на пустой объект
     */
    isEmpty(obj) {
        return Object.keys(obj).length === 0;
    },

    /**
     * Глубокое копирование объекта
     */
    deepClone(obj) {
        return JSON.parse(JSON.stringify(obj));
    },

    /**
     * Форматирование числа с сокращениями (1K, 1M)
     */
    formatCompact(value) {
        return new Intl.NumberFormat('ru-RU', {
            notation: 'compact',
            compactDisplay: 'short',
        }).format(value);
    },

    /**
     * Получить процентное изменение
     */
    calculateDelta(current, previous) {
        if (!previous || previous === 0) return 0;
        return Math.round(((current - previous) / previous) * 100);
    },

    /**
     * Форматирование дельты в процентах
     */
    formatDelta(delta) {
        if (delta > 0) return `+${delta}%`;
        if (delta < 0) return `${delta}%`;
        return '0%';
    },

    /**
     * Получить класс для дельты
     */
    getDeltaClass(delta) {
        if (delta > 0) return 'positive';
        if (delta < 0) return 'negative';
        return '';
    },

    /**
     * Сохранение в localStorage с обработкой ошибок
     */
    saveToStorage(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (e) {
            console.error('Error saving to localStorage:', e);
            return false;
        }
    },

    /**
     * Чтение из localStorage с обработкой ошибок
     */
    loadFromStorage(key) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (e) {
            console.error('Error loading from localStorage:', e);
            return null;
        }
    },

    /**
     * Удаление из localStorage
     */
    removeFromStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (e) {
            console.error('Error removing from localStorage:', e);
            return false;
        }
    },

    /**
     * Проверка валидности email
     */
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * Проверка валидности пароля
     */
    isValidPassword(password) {
        return password && password.length >= 6;
    },

    /**
     * Троттлинг функции
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
    },

    /**
     * Sleep функция
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * Retry функция с экспоненциальной задержкой
     */
    async retry(fn, retries = 3, delay = 1000) {
        try {
            return await fn();
        } catch (error) {
            if (retries === 0) throw error;
            await this.sleep(delay);
            return this.retry(fn, retries - 1, delay * 2);
        }
    },

    /**
     * Инициализация мобильного меню (бургер + оверлей)
     */
    initMobileNavigation() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar || document.querySelector('.mobile-nav-toggle')) return;

        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'mobile-nav-toggle';
        toggleButton.setAttribute('aria-label', 'Открыть меню');
        toggleButton.setAttribute('aria-expanded', 'false');
        toggleButton.innerHTML = '&#9776;';

        const overlay = document.createElement('div');
        overlay.className = 'mobile-nav-overlay';

        const closeMenu = () => {
            document.body.classList.remove('mobile-nav-open');
            toggleButton.setAttribute('aria-expanded', 'false');
            toggleButton.innerHTML = '&#9776;';
        };

        const openMenu = () => {
            document.body.classList.add('mobile-nav-open');
            toggleButton.setAttribute('aria-expanded', 'true');
            toggleButton.innerHTML = '&times;';
        };

        toggleButton.addEventListener('click', () => {
            if (document.body.classList.contains('mobile-nav-open')) {
                closeMenu();
            } else {
                openMenu();
            }
        });

        overlay.addEventListener('click', closeMenu);

        // Закрываем меню после перехода по пункту
        sidebar.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMenu);
        });

        // На desktop всегда закрываем состояние мобильного меню
        const mediaQuery = window.matchMedia('(min-width: 1025px)');
        const handleViewportChange = () => {
            if (mediaQuery.matches) {
                closeMenu();
            }
        };
        if (typeof mediaQuery.addEventListener === 'function') {
            mediaQuery.addEventListener('change', handleViewportChange);
        } else if (typeof mediaQuery.addListener === 'function') {
            mediaQuery.addListener(handleViewportChange);
        }

        document.body.appendChild(toggleButton);
        document.body.appendChild(overlay);
    },
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Utils.initMobileNavigation());
} else {
    Utils.initMobileNavigation();
}
