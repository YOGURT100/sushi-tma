# 🍣 Sushi House — Professional Telegram Mini App v3

Полноценная система: бот + Mini App + REST API + Веб-панель администратора.

---

## 📁 Структура

```
sushi-tma/
├── frontend/               ← Vercel (статика)
│   ├── index.html          Клиентский Mini App
│   ├── style.css
│   ├── app.js
│   ├── admin.html          Панель администратора
│   ├── admin.css
│   └── admin.js
└── bot/                    ← Railway (Python)
    ├── bot.py              Бот + aiohttp REST API
    ├── requirements.txt
    ├── Procfile
    ├── runtime.txt
    ├── .env.example
    └── data/               (создаётся автоматически)
        ├── menu.json
        └── orders.json
```

---

## 🚀 Деплой

### Шаг 1 — BotFather
```
/newbot → получить TOKEN
/newapp → указать URL Vercel как Web App URL
```

### Шаг 2 — Vercel (фронтенд)
1. Vercel → New Project → импорт репо
2. **Root Directory** → `frontend`
3. Deploy → скопировать URL `https://xxx.vercel.app`

### Шаг 3 — Railway (бот + API)
1. Railway → New Project → Deploy from GitHub
2. **Root Directory** → `bot`
3. Variables:
   | Ключ | Значение |
   |---|---|
   | `BOT_TOKEN` | Токен из BotFather |
   | `WEB_APP_URL` | URL с Vercel |
   | `ADMIN_ID` | Ваш Telegram ID |
   | `PORT` | `8080` |
   | `STARS_RATE` | `1.5` |
4. Скопировать Railway URL вида `https://xxx.up.railway.app`

### Шаг 4 — Подключить Admin-панель
1. Напишите боту `/admin` — получите API-токен
2. Откройте `https://xxx.vercel.app/admin.html`
3. Введите Railway URL + токен → Подключиться

---

## ✨ Функционал

### Mini App (клиент)
- 22 позиции в 5 категориях
- Корзина с event delegation (баг множественного добавления исправлен)
- Промокоды: `SUSHI10`, `ROLL20`, `WELCOME15`
- Оформление с адресом и выбором оплаты
- Telegram Stars (нативный инвойс XTR)
- Наличные / заглушки СБП и карты
- Раздел «Адреса» с картой и телефоном
- Toast-уведомления вместо alert()
- Тема Telegram (авто-синхронизация)

### Бот
- `/start` — главное меню
- `/admin` — токен + ссылка на панель (только для ADMIN_ID)
- `/orders` — последние 10 заказов
- Приём заказов из Mini App
- Stars: send_invoice с `provider_token=""` (исправлено)
- Уведомления пользователю при каждом изменении статуса
- Кнопки управления статусом прямо в Telegram

### Цикл статусов
```
new → accepted → preparing → ready → delivered
           ↘         ↘        ↘       ↘
                        cancelled
```
При каждом переходе пользователь получает уведомление в бот.

### Панель администратора
- **Дашборд**: статистика за день/неделю, активные заказы
- **Заказы**: фильтр по статусу, управление прямо из панели
- **Меню**: добавление, редактирование, удаление, пауза
- **Адреса**: список точек с картой
- Авто-обновление каждые 30 сек
- Адаптивный: боковое меню на ПК, нижняя навигация на мобильном

---

## 🔧 Локальный запуск

```bash
cd bot
pip install -r requirements.txt
cp .env.example .env
# Заполни .env
python bot.py
```

Фронтенд: открыть `frontend/index.html` в браузере.
Admin-панель: `frontend/admin.html` (потребует Railway URL + токен).
