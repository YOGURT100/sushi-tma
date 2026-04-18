"""
Sushi House — Telegram Bot v2
Заказы из Mini App, оплата Stars, адрес доставки, уведомления администратору.
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
    LabeledPrice,
    PreCheckoutQuery,
)
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ─── Настройки ────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN",  "YOUR_BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-app.vercel.app")
ADMIN_ID   = int(os.getenv("ADMIN_ID", "0"))

# Курс: сколько рублей стоит 1 Star (≈ 1 Star = $0.013 ≈ 1.2 ₽ по рынку).
# Значение можно скорректировать через переменную окружения.
STARS_RATE = float(os.getenv("STARS_RATE", "1.5"))  # ₽ за 1 Star

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

# Временное хранилище заказов, ожидающих оплаты Stars (user_id → order_dict)
pending_orders: dict[int, dict] = {}

PAYMENT_LABELS = {
    "stars": "⭐ Telegram Stars",
    "cash":  "💵 Наличные курьеру",
    "sbp":   "🏦 СБП (скоро)",
    "card":  "💳 Банковская карта (скоро)",
}


# ─── Утилиты ──────────────────────────────────────────────────────────────────
def rubles_to_stars(amount: int) -> int:
    """Конвертирует рубли → Telegram Stars (минимум 1)."""
    return max(1, round(amount / STARS_RATE))


def fmt_items(items: list[dict]) -> str:
    return "\n".join(
        f"  • {i['name']} × {i['qty']} — {i['price'] * i['qty']} ₽"
        for i in items
    )


def user_mention(user) -> str:
    return f"@{user.username}" if user.username else "—"


async def notify_admin(user, items: list, address: str, payment_label: str,
                       discount: int, total: int, stars_paid: int | None = None):
    """Отправляет структурированное уведомление администратору."""
    if not ADMIN_ID:
        return

    lines = fmt_items(items)
    discount_text = f"\n🏷 Скидка: {discount}%" if discount else ""
    stars_text = f"\n⭐ Оплачено: {stars_paid} Stars" if stars_paid else ""

    text = (
        f"🔔 <b>Новый заказ!</b>\n"
        f"{'─' * 30}\n"
        f"👤 <b>Клиент:</b> {user.full_name}\n"
        f"📱 <b>Username:</b> {user_mention(user)}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"{'─' * 30}\n"
        f"📋 <b>Состав заказа:</b>\n{lines}"
        f"{discount_text}\n"
        f"{'─' * 30}\n"
        f"📍 <b>Адрес доставки:</b>\n{address}\n"
        f"{'─' * 30}\n"
        f"💳 <b>Оплата:</b> {payment_label}"
        f"{stars_text}\n"
        f"💰 <b>Итого: {total} ₽</b>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять",  callback_data=f"accept_{user.id}"),
            InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{user.id}"),
        ],
        [
            InlineKeyboardButton(
                text="💬 Написать клиенту",
                url=f"tg://user?id={user.id}",
            ),
        ],
    ])

    try:
        await bot.send_message(ADMIN_ID, text, parse_mode="HTML", reply_markup=kb)
    except Exception as e:
        log.warning(f"Не удалось уведомить админа: {e}")


# ─── /start ───────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🍣 Открыть меню",       web_app=WebAppInfo(url=WEB_APP_URL))
    kb.button(text="📞 Связаться с нами",   url="https://t.me/keosOG")
    kb.adjust(1)

    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"🍱 Добро пожаловать в <b>Sushi House</b> — свежие роллы с доставкой.\n\n"
        f"⏱ Доставка: ~40 минут\n"
        f"🚚 Бесплатная доставка от 1500 ₽\n"
        f"🕐 Работаем: 10:00 — 23:00\n\n"
        f"Нажми кнопку ниже, чтобы открыть меню 👇",
        parse_mode="HTML",
        reply_markup=kb.as_markup(),
    )


# ─── Приём заказа из Mini App ─────────────────────────────────────────────────
@dp.message(F.web_app_data)
async def handle_order(message: Message):
    try:
        data     = json.loads(message.web_app_data.data)
        items    = data.get("items", [])
        total    = data.get("total", 0)
        discount = data.get("discount", 0)
        address  = data.get("address", "").strip()
        payment  = data.get("payment", "cash")

        if not items:
            await message.answer("❌ Заказ пустой. Попробуйте ещё раз.")
            return

        if not address:
            await message.answer("❌ Адрес доставки не указан. Пожалуйста, заполните его в форме заказа.")
            return

        user   = message.from_user
        lines  = fmt_items(items)
        p_label = PAYMENT_LABELS.get(payment, payment)
        discount_text = f"\n🏷 Скидка: {discount}%" if discount else ""

        # ── Оплата Telegram Stars ─────────────────────────────────────────────
        if payment == "stars":
            stars_amount = rubles_to_stars(total)

            # Сохраняем заказ до подтверждения оплаты
            pending_orders[user.id] = {
                "items":    items,
                "total":    total,
                "discount": discount,
                "address":  address,
                "payment":  payment,
            }

            await message.answer(
                f"⭐ <b>Оплата через Telegram Stars</b>\n\n"
                f"<b>Состав:</b>\n{lines}{discount_text}\n\n"
                f"📍 <b>Адрес:</b> {address}\n\n"
                f"💰 Сумма: <b>{total} ₽</b>\n"
                f"⭐ К оплате: <b>{stars_amount} Stars</b>\n\n"
                f"👇 Нажмите кнопку «Оплатить» в счёте ниже:",
                parse_mode="HTML",
            )

            desc_short = "; ".join(f"{i['name']} ×{i['qty']}" for i in items[:4])
            if len(items) > 4:
                desc_short += f" и ещё {len(items) - 4} позиции"

            await bot.send_invoice(
                chat_id=user.id,
                title="Заказ Sushi House 🍣",
                description=f"Доставка: {address}\n{desc_short}",
                payload=str(user.id),          # вернётся в successful_payment
                currency="XTR",                # Telegram Stars
                prices=[LabeledPrice(label="Оплата заказа", amount=stars_amount)],
            )
            return

        # ── Наличные / заглушки СБП и карты ──────────────────────────────────
        stub_note = ""
        if payment in ("sbp", "card"):
            stub_note = (
                "\n\n⚠️ <i>Онлайн-оплата временно недоступна. "
                "Наш оператор свяжется с вами для передачи реквизитов.</i>"
            )

        confirm_kb = InlineKeyboardBuilder()
        confirm_kb.button(text="🍣 Новый заказ", web_app=WebAppInfo(url=WEB_APP_URL))
        confirm_kb.button(text="📋 Мои заказы",  callback_data="my_orders")
        confirm_kb.adjust(1)

        await message.answer(
            f"✅ <b>Заказ принят!</b>\n\n"
            f"<b>📋 Состав:</b>\n{lines}{discount_text}\n\n"
            f"📍 <b>Адрес:</b> {address}\n"
            f"💳 <b>Оплата:</b> {p_label}\n"
            f"💰 <b>Итого: {total} ₽</b>\n\n"
            f"⏱ Ожидаемое время доставки: ~40 минут"
            f"{stub_note}",
            parse_mode="HTML",
            reply_markup=confirm_kb.as_markup(),
        )

        await notify_admin(user, items, address, p_label, discount, total)
        log.info(f"Заказ от {user.id} | {payment} | {total} ₽ | {len(items)} поз.")

    except json.JSONDecodeError:
        await message.answer("❌ Ошибка обработки заказа. Попробуйте ещё раз.")
    except Exception as e:
        log.error(f"Ошибка обработки заказа: {e}", exc_info=True)
        await message.answer("❌ Что-то пошло не так. Мы уже разбираемся!")


# ─── Stars: предварительная проверка ──────────────────────────────────────────
@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    # Здесь можно проверить наличие товаров на складе и т.д.
    await query.answer(ok=True)


# ─── Stars: успешная оплата ───────────────────────────────────────────────────
@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    user  = message.from_user
    order = pending_orders.pop(user.id, None)
    stars_paid = message.successful_payment.total_amount

    confirm_kb = InlineKeyboardBuilder()
    confirm_kb.button(text="🍣 Новый заказ", web_app=WebAppInfo(url=WEB_APP_URL))
    confirm_kb.button(text="📋 Мои заказы",  callback_data="my_orders")
    confirm_kb.adjust(1)

    if not order:
        await message.answer(
            f"✅ <b>Оплата получена!</b> ⭐ {stars_paid} Stars\n\n"
            f"Ваш заказ уже готовится 🍣",
            parse_mode="HTML",
            reply_markup=confirm_kb.as_markup(),
        )
        return

    items    = order["items"]
    total    = order["total"]
    discount = order["discount"]
    address  = order["address"]
    lines    = fmt_items(items)
    d_text   = f"\n🏷 Скидка: {discount}%" if discount else ""

    await message.answer(
        f"🎉 <b>Оплата прошла успешно!</b>\n"
        f"⭐ Списано: <b>{stars_paid} Stars</b>\n\n"
        f"<b>📋 Состав:</b>\n{lines}{d_text}\n\n"
        f"📍 <b>Адрес:</b> {address}\n"
        f"💰 <b>Итого: {total} ₽</b>\n\n"
        f"⏱ Ожидаемое время доставки: ~40 минут\n"
        f"👨‍🍳 Передаём заказ на кухню!",
        parse_mode="HTML",
        reply_markup=confirm_kb.as_markup(),
    )

    p_label = f"⭐ Telegram Stars ({stars_paid} Stars оплачено)"
    await notify_admin(user, items, address, p_label, discount, total, stars_paid)
    log.info(f"Stars оплата от {user.id}: {stars_paid} Stars | {total} ₽")


# ─── Callbacks администратора ─────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("accept_"))
async def admin_accept(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("✅ Заказ принят и передан на кухню!")
    try:
        await bot.send_message(
            user_id,
            "👨‍🍳 <b>Ваш заказ принят!</b>\n\n"
            "Мы уже готовим для вас. Ожидайте ~40 минут 🍣",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer("Заказ принят ✅")


@dp.callback_query(F.data.startswith("cancel_"))
async def admin_cancel(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("❌ Заказ отменён.")
    try:
        await bot.send_message(
            user_id,
            "😔 <b>Ваш заказ был отменён.</b>\n\n"
            "Пожалуйста, свяжитесь с нами для уточнения деталей.",
            parse_mode="HTML",
        )
    except Exception:
        pass
    await callback.answer("Заказ отменён ❌")


@dp.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    await callback.answer("История заказов появится в ближайшем обновлении!", show_alert=True)


# ─── Команды ──────────────────────────────────────────────────────────────────
@dp.message(F.text == "/menu")
async def cmd_menu(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🍣 Открыть меню", web_app=WebAppInfo(url=WEB_APP_URL))
    await message.answer("Вот наше меню 👇", reply_markup=kb.as_markup())


@dp.message(F.text == "/help")
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ <b>Помощь</b>\n\n"
        "/start — Главное меню\n"
        "/menu  — Открыть меню ресторана\n"
        "/help  — Эта справка\n\n"
        "📞 Поддержка: @keosOG",
        parse_mode="HTML",
    )


# ─── Запуск ───────────────────────────────────────────────────────────────────
async def main():
    log.info("Sushi House Bot запущен ✅")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
