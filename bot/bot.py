"""
Sushi House — Telegram Bot
Принимает заказы от Mini App и управляет меню.

Запуск:
  pip install -r requirements.txt
  python bot.py
"""

import asyncio
import json
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ─── Настройки ────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8304197356:AAGLJANZgarJSsKJmDRkkRW7jBeFp3v4SGg")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-app.vercel.app")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5266981342"))  # Ваш Telegram ID для уведомлений

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ─── /start ───────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(
        text="🍣 Открыть меню",
        web_app=WebAppInfo(url=WEB_APP_URL),
    )
    kb.button(
        text="📞 Связаться с нами",
        url="https://t.me/@keosOG",
    )
    kb.adjust(1)

    user_name = message.from_user.first_name
    await message.answer(
        f"👋 Привет, {user_name}!\n\n"
        f"🍱 Добро пожаловать в <b>Sushi House</b> — свежие роллы с доставкой.\n\n"
        f"⏱ Доставка: ~40 минут\n"
        f"🚚 Бесплатная доставка от 1500 ₽\n"
        f"🕐 Работаем: 10:00 — 23:00\n\n"
        f"Нажми кнопку ниже, чтобы открыть меню:",
        parse_mode="HTML",
        reply_markup=kb.as_markup(),
    )


# ─── Получение заказа из Mini App ─────────────────────────
@dp.message(F.web_app_data)
async def handle_order(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        items = data.get("items", [])
        total = data.get("total", 0)
        discount = data.get("discount", 0)

        if not items:
            await message.answer("❌ Заказ пустой. Попробуйте ещё раз.")
            return

        # Формируем текст заказа
        lines = "\n".join(
            f"• {i['name']} × {i['qty']} — {i['price'] * i['qty']} ₽"
            for i in items
        )
        discount_text = f"\n🏷 Скидка: {discount}%" if discount else ""
        order_text = (
            f"✅ <b>Ваш заказ принят!</b>\n\n"
            f"<b>Состав заказа:</b>\n{lines}\n"
            f"{discount_text}\n"
            f"💰 <b>Итого: {total} ₽</b>\n\n"
            f"⏱ Ожидаемое время доставки: ~40 минут\n"
            f"📞 Если есть вопросы — напишите нам."
        )

        # Подтверждение пользователю
        confirm_kb = InlineKeyboardBuilder()
        confirm_kb.button(text="📋 Мои заказы", callback_data="my_orders")
        confirm_kb.button(text="🍣 Новый заказ", web_app=WebAppInfo(url=WEB_APP_URL))
        confirm_kb.adjust(1)

        await message.answer(order_text, parse_mode="HTML", reply_markup=confirm_kb.as_markup())

        # Уведомление администратору
        if ADMIN_ID:
            admin_text = (
                f"🔔 <b>Новый заказ!</b>\n"
                f"👤 От: {message.from_user.full_name} (@{message.from_user.username or '—'})\n"
                f"🆔 User ID: {message.from_user.id}\n\n"
                f"<b>Заказ:</b>\n{lines}\n"
                f"{discount_text}\n"
                f"💰 <b>Сумма: {total} ₽</b>"
            )
            admin_kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"accept_{message.from_user.id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отменить",
                    callback_data=f"cancel_{message.from_user.id}",
                ),
            ]])
            try:
                await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=admin_kb)
            except Exception as e:
                log.warning(f"Не удалось уведомить админа: {e}")

        log.info(f"Заказ от {message.from_user.id}: {total} ₽, {len(items)} позиций")

    except json.JSONDecodeError:
        await message.answer("❌ Ошибка обработки заказа. Попробуйте ещё раз.")
    except Exception as e:
        log.error(f"Ошибка обработки заказа: {e}")
        await message.answer("❌ Что-то пошло не так. Мы уже разбираемся!")


# ─── Callbacks для администратора ─────────────────────────
@dp.callback_query(F.data.startswith("accept_"))
async def admin_accept(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup()
    await callback.message.answer("✅ Заказ принят и передан на кухню!")
    try:
        await bot.send_message(user_id, "👨‍🍳 Ваш заказ принят на кухне! Готовим для вас 🍣")
    except Exception:
        pass
    await callback.answer("Заказ принят")


@dp.callback_query(F.data.startswith("cancel_"))
async def admin_cancel(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup()
    await callback.message.answer("❌ Заказ отменён.")
    try:
        await bot.send_message(
            user_id,
            "😔 К сожалению, ваш заказ был отменён.\n"
            "Пожалуйста, свяжитесь с нами для уточнения деталей."
        )
    except Exception:
        pass
    await callback.answer("Заказ отменён")


@dp.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    await callback.answer("История заказов скоро появится!", show_alert=True)


# ─── Команды ──────────────────────────────────────────────
@dp.message(F.text == "/menu")
async def cmd_menu(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🍣 Открыть меню", web_app=WebAppInfo(url=WEB_APP_URL))
    await message.answer("Вот наше меню:", reply_markup=kb.as_markup())


@dp.message(F.text == "/help")
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "/start — Главное меню\n"
        "/menu — Открыть меню ресторана\n"
        "/help — Эта справка\n\n"
        "По вопросам: @your_support",
        parse_mode="HTML",
    )


# ─── Запуск ───────────────────────────────────────────────
async def main():
    log.info("Бот запущен...")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
