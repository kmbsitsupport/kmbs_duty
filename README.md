# 5Stars Alarm — Telegram Bot + Mini App

## Що це

Telegram бот з веб-застосунком (Mini App) для управління розкладом, чеклістами та сповіщеннями.

## Швидкий старт

### 1. Налаштуй змінні середовища

Скопіюй `.env.example` в `.env` і заповни:

```env
BOT_TOKEN=123456:ABC-DEF...          # від @BotFather
ADMIN_TELEGRAM_ID=810376283          # твій Telegram ID
BACKEND_URL=http://localhost:8000    # для локального запуску
WEBAPP_URL=https://твій-домен.com    # HTTPS URL для Mini App (Railway/Render)
SECRET_KEY=random_string_here
DATABASE_URL=sqlite+aiosqlite:///./app.db
```

### 2. Отримай токен бота

1. Напиши @BotFather → `/newbot`
2. Скопіюй токен в `.env`

### 3. Локальний запуск (тест через ngrok)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Bot:**
```bash
cd bot
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**ngrok для HTTPS:**
```bash
ngrok http 5173
# Скопіюй HTTPS URL → встав в WEBAPP_URL в .env
```

### 4. Деплой на Railway

1. Зайди на [railway.app](https://railway.app) → New Project
2. Deploy from GitHub repo (або push цей проект)
3. Додай сервіси: backend, bot, frontend
4. Виставте змінні середовища з `.env`
5. Railway автоматично дасть HTTPS домен

### 5. Налаштування Mini App у BotFather

```
@BotFather → /newapp або /setmenubutton
URL: https://твій-домен.com/app
```

---

## Структура

```
backend/        FastAPI API
  routers/
    admin.py        — завантаження файлів, призначення людей
    checklists.py   — CRUD чеклістів
    alerts.py       — алерти/сповіщення
    schedule.py     — розклад
    users.py        — реєстрація юзерів
    notifications.py — масові розсилки

bot/            aiogram 3 бот
  handlers/
    start.py    — /start, кнопка Mini App
    admin.py    — /admin, /notify
  scheduler.py  — APScheduler, надсилає алерти щохвилини

frontend/       React + Vite
  src/pages/
    App.tsx     — Mini App для користувача (розклад + чеклісти)
    Admin.tsx   — Адмінка (люди, чеклісти, алерти, розсилка)
```

---

## Формат Excel/CSV для розкладу

| name | date | time_start | time_end | description | location |
|------|------|------------|----------|-------------|----------|
| Богдан | 2026-05-28 | 09:00 | 17:00 | Тренінг | Київ |

Колонки можна також на укр: `ім'я`, `дата`, `початок`, `кінець`, `опис`, `місце`

---

## Як це працює

1. Адмін завантажує Excel з розкладом → система парсить і створює людей
2. Адмін прив'язує Telegram ID до кожної людини
3. Адмін створює чеклісти та алерти
4. Бот автоматично надсилає алерти в чат з кнопкою "Відкрити застосунок"
5. Користувач натискає → Mini App відкривається з розкладом і чеклістами
6. Адмін може передати права іншому через адмінку
