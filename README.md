# SmartStock

![Python](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)

**SaaS-платформа ИИ-прогнозирования спроса и управления товарными запасами для продавцов маркетплейсов**

[Цель](#-цель) · [Возможности](#-возможности) · [Стек](#-стек) · [Структура](#-структура-проекта) · [Быстрый старт](#-быстрый-старт)

---

## 🎯 Цель

**SmartStock** помогает продавцам на маркетплейсах принимать решения на данных, а не на интуиции:

- собирать и хранить историю цен, остатков и продаж;
- прогнозировать спрос с помощью ML (CatBoost / Prophet);
- видеть ABC/XYZ-аналитику, топы и динамику остатков;
- получать рекомендации по рекламным кампаниям через LLM;
- получать уведомления и отчёты в Telegram.

Проект ориентирован на облачный SaaS: веб-дашборд, REST API и Telegram-бот работают как единая система.

---

## ✨ Возможности


| Модуль                     | Что даёт                                                               |
| -------------------------- | ---------------------------------------------------------------------- |
| **Лендинг**                | Публичная витрина продукта                                             |
| **Веб-дашборд**            | Товары, избранное, аналитика, прогнозы, профиль                        |
| **REST API**               | Auth (JWT), products, sales, dashboard, analytics, admin, ad-campaigns |
| **ML-пайплайн**            | Ежедневный сбор данных → фичи → прогноз продаж                         |
| **Telegram-бот**           | Привязка аккаунта, меню, аналитика «на ходу»                           |
| **Рекламные рекомендации** | Генерация стратегий через xAI (Grok)                                   |
| **Админка**                | Скрапер, переобучение модели, системные логи                           |


---

## 🛠 Стек

### Backend

- **Python 3.12** · **FastAPI** · **Uvicorn**
- **SQLAlchemy 2** (async) · **Alembic** · **asyncpg**
- **PostgreSQL 16**
- **Pydantic v2** · **PyJWT** (RS256) · **Passlib / bcrypt**

### ML & Data

- **CatBoost** · **Prophet** · **pandas** · **numpy** · **matplotlib / plotly**
- Планировщик: **APScheduler**

### Clients

- **Frontend:** HTML + Tailwind CSS + Chart.js
- **Bot:** aiogram 3
- **LLM:** xAI Grok API (`httpx`)

### Infra

- **Docker** · **Docker Compose**
- Nginx (на проде) · healthchecks · weekly DB backup script

---

## 📁 Структура проекта

```text
SmartStock/
├── src/                      # Backend-приложение
│   ├── api/v1/endpoints/     # REST-эндпоинты
│   ├── db/
│   │   ├── models/           # SQLAlchemy-модели
│   │   ├── repositories/     # Доступ к данным
│   │   └── schemas/          # Pydantic-схемы
│   ├── ml/                   # Движок и модель прогнозов
│   ├── services/             # Бизнес-логика
│   ├── scripts/              # Одноразовые скрипты (train on deploy)
│   ├── utils/                # Auth-зависимости, валидаторы
│   └── main.py               # Точка входа FastAPI
├── bot/                      # Telegram-бот (aiogram)
├── frontend/                 # Веб-дашборд (статика)
├── landing/                  # Лендинг (/)
├── migrations/               # Alembic-миграции
├── tests/                    # unit + integration
├── docker/                   # entrypoint, backup
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
├── settings.py
└── .env.example
```

---

## 🚀 Быстрый старт

### Требования

- Docker + Docker Compose
- (опционально) Python 3.12 + venv — для локальной разработки без Docker

### 1. Клонировать репозиторий

```bash
git clone https://github.com/Chipolinio/SmartStock.git
cd SmartStock
```

### 2. Настроить окружение

```bash
cp .env.example .env
```

Отредактируй `.env`:


| Переменная        | Назначение                            |
| ----------------- | ------------------------------------- |
| `POSTGRES_*`      | БД приложения                         |
| `POSTGRES_*_TEST` | БД для тестов                         |
| `BOT_TOKEN`       | токен Telegram-бота                   |
| `LLM_API_KEY`     | ключ xAI (для рекламных рекомендаций) |
| `COOKIE_SECURE`   | `false` для локального HTTP           |


JWT-ключи (`certs/private.pem`, `certs/public.pem`) генерируются автоматически при старте контейнера, если их нет.

### 3. Поднять стек

```bash
docker compose up -d --build
```

Что поднимется:


| Сервис        | Порт / роль                              |
| ------------- | ---------------------------------------- |
| `db`          | PostgreSQL                               |
| `migrate`     | `alembic upgrade head` (один раз)        |
| `train_model` | обучение модели при деплое (best-effort) |
| `backend`     | API + фронт + лендинг → `127.0.0.1:8000` |
| `bot`         | Telegram-бот                             |


### 4. Открыть в браузере


| URL                                                                | Страница           |
| ------------------------------------------------------------------ | ------------------ |
| [http://127.0.0.1:8000/](http://127.0.0.1:8000/)                   | Лендинг            |
| [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)         | Вход / регистрация |
| [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard) | Дашборд            |
| [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)           | Swagger (OpenAPI)  |
| [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)       | Healthcheck        |


### 5. Остановить

```bash
docker compose down
```

---

## 🧪 Тесты

```bash
# через compose (нужен сервис db_test)
docker compose up -d db_test

# локально в venv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest tests/ -v
```

Конфиг pytest: `pyproject.toml` (`asyncio_mode = auto`).

---

## 🔄 Типичный цикл разработки

```bash
# после изменений кода бэкенда / лендинга / фронта
docker compose build backend
docker compose up -d backend

# миграции
docker compose run --rm migrate

# логи
docker compose logs -f backend
docker compose logs -f bot
```

> Лендинг и фронт копируются в образ на этапе `COPY` в Dockerfile.  
> После `git pull` на сервере нужен **rebuild** backend, иначе сайт останется со старыми статическими файлами.

---

## 📡 API (кратко)

Базовый префикс: `/api/v1`


| Группа       | Префикс         |
| ------------ | --------------- |
| Auth         | `/auth`         |
| Products     | `/products`     |
| Sales        | `/sales`        |
| Dashboard    | `/dashboard`    |
| User         | `/user`         |
| Analytics    | `/analytics`    |
| Ad campaigns | `/ad-campaigns` |
| Admin        | `/admin`        |


Интерактивная документация: `[/docs](http://127.0.0.1:8000/docs)`.

---

