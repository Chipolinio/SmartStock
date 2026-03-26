/**
 * SmartStock API Client
 * Модуль для работы с бэкенд API
 */

const API_BASE_URL = window.location.origin;

class SmartStockAPI {
    /**
     * Базовый метод для запросов
     * @param {string} endpoint - API endpoint
     * @param {object} options - Fetch options
     */
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            ...options,
            credentials: 'include', // Cookies для аутентификации
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);

            // Обработка 401 ошибки
            if (response.status === 401) {
                console.warn('Unauthorized - redirecting to login');
                // window.location.href = '/login';  // Закомментировано для отладки
                throw new Error('Unauthorized');
            }

            // Обработка ошибок
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || errorData.detail || `HTTP ${response.status}`);
            }

            // Для 204 No Content
            if (response.status === 204) {
                return null;
            }

            // Для 202 Accepted
            if (response.status === 202) {
                const data = await response.json().catch(() => ({}));
                return { status: 'accepted', ...data };
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * GET запрос
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST запрос
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    /**
     * PUT запрос
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    /**
     * PATCH запрос
     */
    async patch(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    /**
     * DELETE запрос
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // ========================================================================
    // AUTH (Аутентификация)
    // ========================================================================

    async login(email, password) {
        return this.post('/auth/login/', { email, password });
    }

    async register(email, password) {
        return this.post('/auth/registration/', { email, password });
    }

    async getCurrentUser() {
        return this.get('/auth/me');
    }

    // ========================================================================
    // USER (Пользовательские функции)
    // ========================================================================

    async getProfile() {
        return this.get('/user/profile');
    }

    async updateProfile(data) {
        return this.patch('/user/profile', data);
    }

    // Избранное
    async getFavorites() {
        return this.get('/user/favorites');
    }

    async addToFavorites(wbArticle) {
        return this.post(`/user/favorites`, { wb_article: wbArticle });
    }

    async deleteFromFavorites(wbArticle) {
        return this.delete(`/user/favorites/${wbArticle}`);
    }

    async batchAddToFavorites(productIds) {
        return this.post('/user/favorites/batch', { product_ids: productIds });
    }

    // Telegram
    async getTelegramInfo() {
        return this.get('/user/telegram/info');
    }

    async linkTelegram(telegramId, userId) {
        return this.post('/user/telegram/link', { telegram_id: telegramId, user_id: userId });
    }

    async unlinkTelegram() {
        return this.delete('/user/telegram/unlink');
    }

    // ========================================================================
    // PRODUCTS (Товары)
    // ========================================================================

    async getProducts(params = {}) {
        return this.get('/products/', params);
    }

    async getProductById(productId) {
        return this.get(`/products/${productId}`);
    }

    async getProductDetailed(productId) {
        return this.get(`/products/${productId}/detailed`);
    }

    // ========================================================================
    // SALES (История данных и аналитика по товарам)
    // ========================================================================

    async getStockHistory(productId, limit = 30) {
        return this.get(`/sales/stock/${productId}`, { limit });
    }

    async getSalesHistory(productId, limit = 30) {
        return this.get(`/sales/sale/${productId}`, { limit });
    }

    async getPriceHistory(productId, limit = 30) {
        return this.get(`/sales/price/${productId}`, { limit });
    }

    async getDeliveryHistory(productId, limit = 30) {
        return this.get(`/sales/delivery/${productId}`, { limit });
    }

    async getSocialHistory(productId, limit = 30) {
        return this.get(`/sales/social/${productId}`, { limit });
    }

    async getPredictedSalesHistory(productId, limit = 30) {
        return this.get(`/sales/predicted_sale/${productId}`, { limit });
    }

    async getProductAnalytics(productId) {
        return this.get(`/sales/analytics/${productId}`);
    }

    // ========================================================================
    // DASHBOARD (Дашборд и прогнозы)
    // ========================================================================

    async getDashboardKPI(days = 30) {
        return this.get('/dashboard/kpi', { days });
    }

    async getSalesDynamics(params = {}) {
        return this.get('/dashboard/sales-dynamics', params);
    }

    async getStockDynamics(params = {}) {
        return this.get('/dashboard/stock-dynamics', params);
    }

    async getLowStock(limit = 10) {
        return this.get('/dashboard/low-stock', { limit });
    }

    async getABCAnalysis(params = {}) {
        return this.get('/dashboard/abc-analysis', params);
    }

    async getXYZAnalysis(params = {}) {
        return this.get('/dashboard/xyz-analysis', params);
    }

    async getTopProductsByRevenue(params = {}) {
        return this.get('/dashboard/top-products-by-revenue', params);
    }

    async getTopProductsBySales(params = {}) {
        return this.get('/dashboard/top-products-by-sales', params);
    }

    async getProductsRating(params = {}) {
        return this.get('/dashboard/products-rating', params);
    }

    // Прогнозы
    async getProductForecasts(params = {}) {
        return this.get('/dashboard/forecasts', params);
    }

    async getForecastHistory(params = {}) {
        return this.get('/dashboard/forecasts/history', params);
    }

    async getForecastSummary() {
        return this.get('/dashboard/forecasts/summary');
    }

    // ========================================================================
    // ANALYTICS (Конструктор отчетов)
    // ========================================================================

    async aggregateAnalytics(data) {
        return this.post('/analytics/aggregate', data);
    }

    // ========================================================================
    // ADMIN (Админ-панель)
    // ========================================================================

    // Products CRUD
    async createProduct(data) {
        return this.post('/admin/products/', data);
    }

    async bulkCreateProducts(products) {
        return this.post('/admin/products/bulk', products);
    }

    async updateProduct(productId, data) {
        return this.patch(`/admin/products/${productId}`, data);
    }

    async deleteProduct(productId) {
        return this.delete(`/admin/products/${productId}`);
    }

    // Sales data creation
    async createStockRecord(data) {
        return this.post('/admin/sales/stock', data);
    }

    async bulkCreateStockRecords(records) {
        return this.post('/admin/sales/stock/bulk', records);
    }

    async createSaleRecord(data) {
        return this.post('/admin/sales/sale', data);
    }

    async bulkCreateSaleRecords(records) {
        return this.post('/admin/sales/sale/bulk', records);
    }

    async createPriceRecord(data) {
        return this.post('/admin/sales/price', data);
    }

    async bulkCreatePriceRecords(records) {
        return this.post('/admin/sales/price/bulk', records);
    }

    async createDeliveryRecord(data) {
        return this.post('/admin/sales/delivery', data);
    }

    async bulkCreateDeliveryRecords(records) {
        return this.post('/admin/sales/delivery/bulk', records);
    }

    async createSocialRecord(data) {
        return this.post('/admin/sales/social', data);
    }

    async bulkCreateSocialRecords(records) {
        return this.post('/admin/sales/social/bulk', records);
    }

    // Full payload & Analytics
    async processFullPayload(data) {
        return this.post('/admin/sales/full-payload', data);
    }

    async uploadAnalytics(data) {
        return this.post('/admin/sales/analytics', data);
    }

    // Scraper
    async runScraper(article) {
        return this.post('/admin/scraper/run', null, { article });
    }

    // ML
    async trainModel() {
        return this.post('/admin/ml/train');
    }

    async runForecast() {
        return this.post('/admin/ml/forecast');
    }

    // Logs
    async getSystemLogs(params = {}) {
        return this.get('/admin/logs', params);
    }
}

// Экспорт экземпляра API
const api = new SmartStockAPI();
