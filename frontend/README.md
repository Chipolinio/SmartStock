# SmartStock Frontend

Фронтенд-приложение системы аналитики продаж SmartStock.

## 📁 Структура файлов

```
frontend/
├── css/
│   └── styles.css          # Основные стили
├── js/
│   ├── api-client.js       # API клиент для работы с бэкендом
│   ├── auth.js             # Модуль аутентификации и авторизации
│   └── utils.js            # Вспомогательные утилиты
├── login.html              # Страница входа/регистрации
├── dashboard.html          # Главный дашборд
├── products.html           # Каталог товаров
├── product_analytics.html  # Аналитика товара (детальная страница)
├── favorites.html          # Избранное
├── forecasts.html          # Прогнозы продаж
├── profile.html            # Профиль пользователя
├── telegram.html           # Интеграция с Telegram
├── admin.html              # Админ-панель (только для admin)
├── analytics-sales.html    # Динамика продаж
├── analytics-stock.html    # Динамика остатков
├── analytics-abc.html      # ABC-анализ
├── analytics-xyz.html      # XYZ-анализ
├── analytics-tops.html     # Топы товаров
└── reports-builder.html    # Конструктор отчетов
```

## 🎨 Цветовая палитра

| Цвет | Значение | Использование |
|------|----------|---------------|
| `#F3F6FD` | Фон страниц (Content BG) | Базовый фон |
| `#FFFFFF` | Фон карточек | Карточки, таблицы, блоки |
| `#070F26` | Текст и заголовки | Основной текст |
| `#123273` | Акцент (Primary) | Кнопки, активные элементы |
| `#F2F2F2` | Границы | Разделители, границы |
| `#E4E9FC` | Hover/Subtle | Подсветка при наведении |

## 🗺️ Карта страниц

| Страница | Путь | Описание |
|----------|------|----------|
| **Вход** | `/login.html` | Аутентификация и регистрация |
| **Дашборд** | `/dashboard.html` | Главная страница с KPI и графиками |
| **Товары** | `/products.html` | Каталог всех товаров с фильтрами |
| **Аналитика товара** | `/product_analytics.html?id=` | Детальная аналитика по товару |
| **Избранное** | `/favorites.html` | Управление избранными товарами |
| **Прогнозы** | `/forecasts.html` | ML-прогнозы продаж |
| **Профиль** | `/profile.html` | Настройки аккаунта |
| **Telegram** | `/telegram.html` | Привязка Telegram бота |
| **Аналитика продаж** | `/analytics-sales.html` | Динамика продаж и выручки |
| **Аналитика остатков** | `/analytics-stock.html` | Динамика складских запасов |
| **ABC-анализ** | `/analytics-abc.html` | Классификация по вкладу в выручку |
| **XYZ-анализ** | `/analytics-xyz.html` | Классификация по стабильности |
| **Топы** | `/analytics-tops.html` | Рейтинги товаров |
| **Конструктор отчетов** | `/reports-builder.html` | Кастомные отчеты |
| **Админка** | `/admin.html` | Управление системой (admin only) |

## 🔌 API

Базовый URL API: `http://localhost:8000/api/v1`

### Основные эндпоинты:

#### Auth
- `POST /auth/login/` - Вход
- `POST /auth/registration/` - Регистрация
- `GET /auth/me` - Текущий пользователь

#### Dashboard
- `GET /dashboard/kpi` - KPI дашборда
- `GET /dashboard/sales-dynamics` - Динамика продаж
- `GET /dashboard/stock-dynamics` - Динамика остатков
- `GET /dashboard/abc-analysis` - ABC-анализ
- `GET /dashboard/xyz-analysis` - XYZ-анализ
- `GET /dashboard/top-products-by-revenue` - Топ по выручке
- `GET /dashboard/forecasts/summary` - Сводка прогнозов

#### Products
- `GET /products/` - Список товаров
- `GET /products/{id}` - Детали товара

#### User
- `GET /user/favorites` - Избранное
- `POST /user/favorites` - Добавить в избранное
- `DELETE /user/favorites/{article}` - Удалить из избранного
- `GET /user/telegram/info` - Информация о Telegram
- `POST /user/telegram/link` - Привязать Telegram
- `DELETE /user/telegram/unlink` - Отвязать Telegram

#### Analytics
- `POST /analytics/aggregate` - Конструктор отчетов

#### Admin
- `POST /admin/scraper/run` - Запуск скрапера
- `POST /admin/ml/train` - Переобучение модели
- `POST /admin/ml/forecast` - Запуск прогноза
- `GET /admin/logs` - Системные логи

## 🚀 Запуск

1. Откройте `login.html` в браузере
2. Или используйте локальный сервер:
```bash
cd frontend
python -m http.server 8080
```

## 📦 Зависимости

- TailwindCSS (CDN)
- Chart.js (CDN)

## 🔐 Авторизация

Приложение использует JWT токены в HttpOnly cookies. Все запросы к API требуют авторизации (кроме login/register).

### Роли:
- **user** - базовый доступ
- **admin** - полный доступ к админ-панели

## 📝 Примечания

- Все даты в формате `YYYY-MM-DD`
- Пагинация: `skip`/`limit`
- Временные ряды: `limit` = количество дней
