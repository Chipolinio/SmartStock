/**
 * SmartStock - Модуль аутентификации и авторизации
 */

const AuthHelper = {
    currentUser: null,

    /**
     * Проверка авторизации и загрузка данных пользователя
     * Вызывается ТОЛЬКО при входе/регистрации
     */
    async checkAuth(redirect = false) {
        // Не используем /auth/me - просто возвращаем null
        // Данные пользователя устанавливаются через setCurrentUser после логина
        return this.currentUser;
    },

    /**
     * Установить данные текущего пользователя (вызывается ПОСЛЕ успешного логина)
     * Данные берём из cookies (JWT payload) или устанавливаем вручную
     */
    async setCurrentUser(userData = null) {
        if (userData) {
            this.currentUser = userData;
            return userData;
        }
        // Если userData не передан, пробуем получить с бэкенда
        // Но это может не работать если /auth/me недоступен
        try {
            this.currentUser = await api.getCurrentUser();
            return this.currentUser;
        } catch (error) {
            console.log('setCurrentUser: не удалось получить данные пользователя');
            this.currentUser = null;
            return null;
        }
    },

    /**
     * Установить пользователя из данных токена (альтернатива setCurrentUser)
     */
    setUserFromToken(email, role, isPro, isActive) {
        this.currentUser = {
            email,
            role,
            is_pro: isPro,
            is_active: isActive
        };
        return this.currentUser;
    },

    /**
     * Проверка, является ли пользователь админом
     */
    isAdmin() {
        return this.currentUser && this.currentUser.role === 'admin';
    },

    /**
     * Проверка, является ли пользователь PRO
     */
    isPro() {
        return this.currentUser && this.currentUser.is_pro === true;
    },

    /**
     * Проверка активности пользователя
     */
    isActive() {
        return this.currentUser && this.currentUser.is_active === true;
    },

    /**
     * Обновление навигации в зависимости от роли
     */
    updateNavigation() {
        const adminLinks = document.querySelectorAll('[data-requires-admin]');
        const proLinks = document.querySelectorAll('[data-requires-pro]');
        const userLinks = document.querySelectorAll('[data-requires-user]');

        // Показываем все пользовательские ссылки
        userLinks.forEach(link => {
            link.style.display = '';
            link.closest('li')?.classList.remove('hidden');
        });

        // Админские ссылки показываем только если пользователь админ
        // (проверяем по данным которые установили после логина)
        if (this.currentUser && this.isAdmin()) {
            adminLinks.forEach(link => {
                link.style.display = '';
                link.closest('li')?.classList.remove('hidden');
            });
        } else {
            adminLinks.forEach(link => {
                link.style.display = 'none';
                link.closest('li')?.classList.add('hidden');
            });
        }

        proLinks.forEach(link => {
            link.style.display = 'none'; // PRO функционал пока скрыт
        });

        // Обновляем информацию о пользователе
        const userInfoElements = document.querySelectorAll('[data-user-info]');
        if (this.currentUser && this.currentUser.email) {
            userInfoElements.forEach(el => {
                const roleBadge = this.isAdmin() ? ' [Admin]' : '';
                el.textContent = this.currentUser.email + roleBadge;
            });
        }
    },

    /**
     * Выход из системы
     */
    logout() {
        window.location.href = '/login';
    },

    /**
     * Проверка прав доступа к странице
     */
    async checkPageAccess(requiredRole = 'user') {
        const user = await this.checkAuth(true);

        if (!user) {
            return false;
        }

        if (requiredRole === 'admin' && !this.isAdmin()) {
            window.location.href = '/dashboard';
            Utils.showToast('Доступ запрещен', 'error');
            return false;
        }

        if (requiredRole === 'pro' && !this.isPro() && !this.isAdmin()) {
            window.location.href = '/dashboard';
            Utils.showToast('Требуется PRO аккаунт', 'error');
            return false;
        }

        return true;
    },

    /**
     * Получить ID текущего пользователя
     */
    getUserId() {
        return this.currentUser ? this.currentUser.id : null;
    },

    /**
     * Получить email текущего пользователя
     */
    getEmail() {
        return this.currentUser ? this.currentUser.email : null;
    },

    /**
     * Получить роль текущего пользователя
     */
    getRole() {
        return this.currentUser ? this.currentUser.role : null;
    },

    /**
     * Проверка на авторизацию без редиректа
     */
    async isAuthenticated() {
        try {
            this.currentUser = await api.getCurrentUser();
            return true;
        } catch (error) {
            return false;
        }
    },

    /**
     * Принудительное обновление данных пользователя
     */
    async refreshUser() {
        try {
            this.currentUser = await api.getCurrentUser();
            this.updateNavigation();
            return this.currentUser;
        } catch (error) {
            console.error('Failed to refresh user:', error);
            return null;
        }
    },
};
