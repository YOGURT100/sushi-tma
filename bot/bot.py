"""
Sushi House Bot — Professional v4 (PostgreSQL)
• asyncpg + PostgreSQL — данные не теряются при рестарте
• Полный цикл статусов с уведомлениями
• Telegram Stars (provider_token="" — исправлен)
• REST API для веб-панели администратора
"""
import asyncio, hashlib, json, logging, os, time
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    LabeledPrice, Message, PreCheckoutQuery, WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

import db

# ── Конфигурация ─────────────────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN",   "YOUR_BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-app.vercel.app")
ADMIN_ID    = int(os.getenv("ADMIN_ID", "0"))
PORT        = int(os.getenv("PORT", "8080"))
STARS_RATE  = float(os.getenv("STARS_RATE", "1.5"))
ADMIN_TOKEN = hashlib.sha256(f"{ADMIN_ID}:{BOT_TOKEN}".encode()).hexdigest()[:24]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

pending_stars: dict[int, dict] = {}

# ── Константы ────────────────────────────────────────────────────────────────
STATUS_EMOJI  = {"new":"🆕","accepted":"✅","preparing":"👨‍🍳","ready":"📦","delivered":"🚀","cancelled":"❌"}
STATUS_LABEL  = {"new":"Новый","accepted":"Принят","preparing":"Готовится","ready":"Готов","delivered":"Доставлен","cancelled":"Отменён"}
PAY_LABEL     = {"stars":"⭐ Telegram Stars","cash":"💵 Наличные","sbp":"🏦 СБП","card":"💳 Карта"}
USER_MSGS = {
    "accepted":  "✅ <b>Заказ {id} принят!</b>\nНачинаем готовить — скоро будет готово 🍣",
    "preparing": "👨‍🍳 <b>Заказ {id} на кухне!</b>\nПовара уже готовят ваши роллы ✨",
    "ready":     "📦 <b>Заказ {id} готов!</b>\nПередаём курьеру — ожидайте звонка 🛵",
    "delivered": "🎉 <b>Заказ {id} доставлен!</b>\nПриятного аппетита! Спасибо за заказ 🙏",
    "cancelled": "😔 <b>Заказ {id} отменён.</b>\nЕсли вопросы — напишите @keosOG",
}

def rubles_to_stars(rub): return max(1, round(rub / STARS_RATE))

def fmt_items(items):
    return "\n".join(f"  • {i['item_name'] if 'item_name' in i else i['name']} ×{i['qty']} — {i['price']*i['qty']} ₽" for i in items)

def user_tag(u): return f"@{u.username}" if u.username else "—"

def admin_kb(order_id, current_status):
    flow = ["accepted","preparing","ready","delivered"]
    rows, row = [], []
    for st in flow:
        if st != current_status:
            row.append(InlineKeyboardButton(
                text=f"{STATUS_EMOJI[st]} {STATUS_LABEL[st]}",
                callback_data=f"st_{order_id}_{st}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    if current_status not in ("cancelled","delivered"):
        rows.append([InlineKeyboardButton(text="❌ Отменить", callback_data=f"st_{order_id}_cancelled")])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None

async def notify_user(user_id, order_id, status):
    msg = USER_MSGS.get(status)
    if not msg: return
    try:
        await bot.send_message(user_id, msg.format(id=order_id), parse_mode="HTML")
    except Exception as e:
        log.warning(f"notify_user {user_id}: {e}")

async def send_admin_notification(user, order):
    if not ADMIN_ID: return
    items = order.get("items", [])
    lines = fmt_items(items)
    disc_line  = f"\n🏷 Скидка: {order['discount']}%" if order.get("discount") else ""
    stars_line = f"\n⭐ Stars: {order.get('stars_paid','—')}" if order["payment"] == "stars" else ""
    rest_line  = f"\n🏠 Ресторан: {order.get('restaurant_name','—')}" if order.get("restaurant_name") else ""
    text = (
        f"🔔 <b>Новый заказ {order['id']}!</b>\n{'─'*28}\n"
        f"👤 {user.full_name}  {user_tag(user)}\n"
        f"🆔 <code>{user.id}</code>\n{'─'*28}\n"
        f"📋 <b>Состав:</b>\n{lines}{disc_line}\n{'─'*28}\n"
		f"📍 <b>Адрес:</b> {order.get('address','—')}\n"
        f"💳 <b>Оплата:</b> {PAY_LABEL.get(order['payment'], order['payment'])}{stars_line}\n"
        f"💰 <b>Итого: {order['total']} ₽</b>{rest_line}"
    )
    try:
        msg = await bot.send_message(ADMIN_ID, text, parse_mode="HTML",
                                     reply_markup=admin_kb(order["id"], "new"))
        await db.update_order_admin_msg(order["id"], msg.message_id)
    except Exception as e:
        log.warning(f"admin notify: {e}")

# ── Handlers ──────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🍣 Открыть меню",     web_app=WebAppInfo(url=WEB_APP_URL))
    kb.button(text="📞 Связаться с нами", url="https://t.me/keosOG")
    kb.adjust(1)
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"🍱 <b>Sushi House</b> — свежие роллы с доставкой.\n\n"
        f"⏱ Доставка ~40 мин · 🚚 Бесплатно от 1500 ₽ · 🕐 10:00–23:00",
        parse_mode="HTML", reply_markup=kb.as_markup(),
    )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Нет доступа.")
    admin_url = f"{WEB_APP_URL}/admin.html"
    kb = InlineKeyboardBuilder()
    kb.button(text="⚙️ Панель управления", web_app=WebAppInfo(url=admin_url))
    await message.answer(
        f"👑 <b>Панель администратора</b>\n\n"
        f"🔑 API-токен:\n<code>{ADMIN_TOKEN}</code>\n\n"
        f"Скопируйте токен и вставьте при входе в панель.",
        parse_mode="HTML", reply_markup=kb.as_markup(),
    )

@dp.message(Command("orders"))
async def cmd_orders(message: Message):
    if message.from_user.id != ADMIN_ID: return
    orders = await db.get_orders(limit=10)
    if not orders: return await message.answer("📭 Заказов нет.")
    lines = [f"{STATUS_EMOJI.get(o['status'],'?')} <b>{o['id']}</b> · {o['total']} ₽ · "
             f"{o['created_at'].strftime('%d.%m %H:%M')}" for o in orders]
    await message.answer("📋 <b>Последние 10 заказов:</b>\n\n" + "\n".join(lines), parse_mode="HTML")

@dp.message(F.web_app_data)
async def handle_order(message: Message):
    try:
        data    = json.loads(message.web_app_data.data)
        items   = data.get("items", [])
        total   = data.get("total", 0)
        disc    = data.get("discount", 0)
        address = data.get("address", "").strip()
        payment = data.get("payment", "cash")
        rest_id = data.get("restaurant_id")
        rest_nm = data.get("restaurant_name", "")
        user    = message.from_user

        if not items:   return await message.answer("❌ Заказ пустой.")
        if not address: return await message.answer("❌ Укажите адрес доставки.")

        if payment == "stars":
            stars_amt = rubles_to_stars(total)
            pending_stars[user.id] = {
                "items":items,"total":total,"discount":disc,"address":address,
                "payment":"stars","restaurant_id":rest_id,"restaurant_name":rest_nm,
            }
            desc = "; ".join(f"{i['name']} ×{i['qty']}" for i in items[:3])
            if len(items) > 3: desc += f" +{len(items)-3}"
            await message.answer(
                f"⭐ <b>Оплата через Telegram Stars</b>\n\n"
                f"💰 {total} ₽ → <b>{stars_amt} Stars</b>\n"
                f"📍 {address}\n\nНажмите «Оплатить» в счёте ниже 👇",
                parse_mode="HTML",
            )
            await bot.send_invoice(
                chat_id=user.id, title="Заказ Sushi House 🍣",
                description=f"{desc} · {address}",
                payload=f"order_{user.id}",
                provider_token="",   # ← пусто = Stars XTR
                currency="XTR",
                prices=[LabeledPrice(label="Оплата заказа", amount=stars_amt)],
            )
            return

        order = await db.create_order(
            user_id=user.id, user_name=user.full_name, username=user.username or "",
            items=items, total=total, discount=disc, address=address, payment=payment,
            restaurant_id=rest_id, restaurant_name=rest_nm,
        )
        pay_label = PAY_LABEL.get(payment, payment)
        stub = "\n\n⚠️ <i>Онлайн-оплата временно недоступна. Оператор свяжется с вами.</i>" \
               if payment in ("sbp","card") else ""
        disc_line = f"\n🏷 Скидка: {disc}%" if disc else ""
        rest_line = f"\n🏠 Ресторан: {rest_nm}" if rest_nm else ""
        kb = InlineKeyboardBuilder()
        kb.button(text="🍣 Ещё заказать", web_app=WebAppInfo(url=WEB_APP_URL))

        await message.answer(
            f"✅ <b>Заказ {order['id']} принят!</b>\n\n"
            f"{fmt_items(order['items'])}{disc_line}\n\n"
            f"📍 <b>Адрес:</b> {address}\n"
            f"💳 <b>Оплата:</b> {pay_label}{rest_line}\n"
            f"💰 <b>Итого: {total} ₽</b>\n\n"
            f"⏱ Ожидайте ~40 минут{stub}",
            parse_mode="HTML", reply_markup=kb.as_markup(),
        )
        await send_admin_notification(user, order)
        log.info(f"Order {order['id']} from {user.id} | {payment} | {total}₽")

    except Exception as e:
        log.error(f"handle_order: {e}", exc_info=True)
        await message.answer("❌ Ошибка при обработке заказа. Попробуйте позже.")

@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def on_stars_paid(message: Message):
    user       = message.from_user
    stars_paid = message.successful_payment.total_amount
    pending    = pending_stars.pop(user.id, {})

    order = await db.create_order(
        user_id=user.id, user_name=user.full_name, username=user.username or "",
        items=pending.get("items",[]), total=pending.get("total",0),
        discount=pending.get("discount",0), address=pending.get("address","—"),
        payment="stars", stars_paid=stars_paid,
        restaurant_id=pending.get("restaurant_id"),
        restaurant_name=pending.get("restaurant_name",""),
    )
    disc_line = f"\n🏷 Скидка: {order['discount']}%" if order.get("discount") else ""
    kb = InlineKeyboardBuilder()
    kb.button(text="🍣 Ещё заказать", web_app=WebAppInfo(url=WEB_APP_URL))

    await message.answer(
        f"🎉 <b>Оплата прошла! Заказ {order['id']} принят.</b>\n\n"
        f"{fmt_items(order['items'])}{disc_line}\n\n"
        f"📍 <b>Адрес:</b> {order.get('address','—')}\n"
        f"⭐ <b>Списано: {stars_paid} Stars</b>\n\n"
        f"⏱ Ожидайте ~40 минут 🍣",
        parse_mode="HTML", reply_markup=kb.as_markup(),
    )
    await send_admin_notification(user, order)
    log.info(f"Stars order {order['id']} | {stars_paid} Stars")

@dp.callback_query(F.data.startswith("st_"))
async def on_status(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        return await cb.answer("⛔ Нет доступа.", show_alert=True)
    parts = cb.data.split("_", 2)
    if len(parts) != 3: return
    _, order_id, new_status = parts

    order = await db.update_order_status(order_id, new_status)
    if not order: return await cb.answer("❌ Заказ не найден.", show_alert=True)

    try:
        st_line = f"\n\n{STATUS_EMOJI[new_status]} <b>Статус: {STATUS_LABEL[new_status]}</b>"
        orig = cb.message.html_text or ""
        if "\n\n" in orig and "Статус:" in orig:
            orig = orig[:orig.rfind("\n\n")]
        new_kb = admin_kb(order_id, new_status) if new_status not in ("delivered","cancelled") else None
        await cb.message.edit_text(orig + st_line, parse_mode="HTML", reply_markup=new_kb)
    except Exception:
        pass

    await notify_user(order["user_id"], order_id, new_status)
    await cb.answer(f"{STATUS_EMOJI[new_status]} {STATUS_LABEL[new_status]}")
    log.info(f"Order {order_id} → {new_status}")

# ── REST API ──────────────────────────────────────────────────────────────────
CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Admin-Token",
}

def jr(data, status=200):
    def serializer(obj):
        if hasattr(obj, 'isoformat'): return obj.isoformat()
        raise TypeError(f"Not serializable: {type(obj)}")
    return web.Response(
        text=json.dumps(data, ensure_ascii=False, default=serializer),
        content_type="application/json", status=status, headers=CORS,
    )

def is_admin(req): return req.headers.get("X-Admin-Token","") == ADMIN_TOKEN

async def h_options(req): return web.Response(headers=CORS)

# Menu
async def h_menu_get(req):
    items = await db.get_menu()
    return jr({"items": items})

async def h_menu_post(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    b = await req.json()
    item = await db.create_menu_item(b)
    return jr(item, 201)

async def h_menu_put(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    iid = int(req.match_info["id"])
    b   = await req.json()
    item = await db.update_menu_item(iid, b)
    return jr(item) if item else jr({"error":"Not found"},404)

async def h_menu_del(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    iid = int(req.match_info["id"])
    ok  = await db.delete_menu_item(iid)
    return jr({"ok": ok})

# Restaurants
async def h_restaurants(req):
    items = await db.get_restaurants()
    return jr({"restaurants": items})

# Orders
async def h_orders_get(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    status = req.rel_url.query.get("status")
    orders = await db.get_orders(limit=200, status=status)
    return jr({"orders": orders})

async def h_order_status(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    oid    = req.match_info["id"]
    b      = await req.json()
    status = b.get("status")
    order  = await db.update_order_status(oid, status)
    if not order: return jr({"error":"Not found"},404)
    asyncio.create_task(notify_user(order["user_id"], oid, status))
    return jr(order)

# Stats
async def h_stats(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    stats = await db.get_stats()
    return jr(stats)

def build_api():
    app = web.Application()
    app.router.add_options("/{p:.*}", h_options)
    app.router.add_get("/api/menu",                h_menu_get)
    app.router.add_post("/api/menu",               h_menu_post)
    app.router.add_put("/api/menu/{id}",           h_menu_put)
    app.router.add_delete("/api/menu/{id}",        h_menu_del)
    app.router.add_get("/api/restaurants",         h_restaurants)
    app.router.add_get("/api/orders",              h_orders_get)
    app.router.add_put("/api/orders/{id}/status",  h_order_status)
    app.router.add_get("/api/stats",               h_stats)
    return app

# ── Запуск ────────────────────────────────────────────────────────────────────
async def main():
    log.info(f"Admin token: {ADMIN_TOKEN}")
    await db.init()
    runner = web.AppRunner(build_api())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    log.info(f"API on :{PORT}")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())