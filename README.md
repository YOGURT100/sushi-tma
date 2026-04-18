# 🍣 Sushi House — Telegram Mini App

Полноценный бот для суши-ресторана с Mini App: меню, корзина, оформление заказов.

---

## 📁 Структура проекта

```
sushi-tma/
├── frontend/          ← Деплоится на Vercel
│   ├── index.html
│   ├── style.css
│   └── app.js
└── bot/               ← Деплоится на Railway
    ├── bot.py
    ├── requirements.txt
    ├── Procfile
    └── .env.example
```

---

## 🚀 Деплой шаг за шагом

### Шаг 1 — Создать бота в Telegram

1. Открыть [@BotFather](https://t.me/BotFather)
2. Написать `/newbot`
3. Ввести название: `Sushi House`
4. Ввести username: `sushihouse_mybot`
5. **Скопировать TOKEN** — он понадобится дальше

---

### Шаг 2 — Залить код на GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/ВАШ_ЛОГИН/sushi-tma.git
git push -u origin main
```

---

### Шаг 3 — Деплой фронтенда на Vercel

1. Зайти на [vercel.com](https://vercel.com) → Sign up (через GitHub)
2. **New Project** → импортировать `sushi-tma`
3. **Root Directory** → указать `frontend`
4. Нажать **Deploy**
5. Получить URL вида: `https://sushi-tma-xyz.vercel.app`

> ✅ Теперь Mini App доступен по HTTPS — именно это нужно Telegram.

---

### Шаг 4 — Деплой бота на Railway

1. Зайти на [railway.app](https://railway.app) → Login with GitHub
2. **New Project** → Deploy from GitHub → выбрать `sushi-tma`
3. **Root Directory** → указать `bot`
4. Перейти в **Variables** и добавить:
   | Ключ | Значение |
   |------|----------|
   | `BOT_TOKEN` | Токен из BotFather |
   | `WEB_APP_URL` | URL с Vercel |
   | `ADMIN_ID` | Ваш Telegram ID (узнать: @userinfobot) |
5. Railway сам запустит бота

---

### Шаг 5 — Привязать Mini App к боту

В [@BotFather](https://t.me/BotFather):
```
/newapp
→ Выбрать вашего бота
→ Название: Sushi House Menu
→ Описание: Меню и корзина
→ Web App URL: https://sushi-tma-xyz.vercel.app
```

---

## 🎉 Готово!

Напишите боту `/start` — появится кнопка **«Открыть меню»**.

---

## ✨ Функциональность

### Mini App (frontend)
- 22 позиции в 5 категориях: Роллы, Нигири, Сашими, Сеты, Напитки
- Корзина с добавлением/удалением позиций
- Промокоды: `SUSHI10`, `ROLL20`, `WELCOME15`
- Бесплатная доставка от 1500 ₽
- Адаптивный интерфейс (тёмная тема)
- Haptic feedback при нажатиях

### Бот (backend)
- Команды: `/start`, `/menu`, `/help`
- Приём заказов из Mini App
- Уведомления администратору с кнопками Принять/Отменить
- Уведомление пользователя о статусе заказа

---

## 🛠 Локальный тест

```bash
cd bot
pip install -r requirements.txt
cp .env.example .env
# Заполни .env своими данными
python bot.py
```

Фронтенд можно открыть прямо в браузере — `frontend/index.html`.
Некоторые Telegram-функции работают только внутри Telegram.

---

## 📝 Промокоды

| Код | Скидка |
|-----|--------|
| `SUSHI10` | 10% |
| `ROLL20` | 20% |
| `WELCOME15` | 15% |

---

## 🔧 Настройка меню

Откройте `frontend/app.js` и найдите массив `MENU`.
Добавьте, удалите или измените позиции по образцу:

```js
{ id: 23, cat: 'rolls', name: 'Мой ролл', desc: 'Описание', weight: '280 г · 8 шт', price: 650, emoji: '🍙' },
```

Категории: `rolls` · `nigiri` · `sashimi` · `sets` · `drinks`
