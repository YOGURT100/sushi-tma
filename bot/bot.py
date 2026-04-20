"""
Sushi House Bot — Professional v3
• JSON-хранилище заказов и меню с уникальными ID
• aiohttp REST API для веб-панели администратора
• Telegram Stars (provider_token="" — исправлен)
• Полный цикл статусов: new→accepted→preparing→ready→delivered
• Уведомления пользователю при каждом изменении статуса
• /admin — отправляет токен и ссылку на панель
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
    LabeledPrice, Message, PreCheckoutQuery, WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# ── Конфигурация ──────────────────────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN",   "8304197356:AAGLJANZgarJSsKJmDRkkRW7jBeFp3v4SGg")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-app.vercel.app")
ADMIN_ID    = int(os.getenv("ADMIN_ID", "5266981342"))
PORT        = int(os.getenv("PORT", "8080"))
STARS_RATE  = float(os.getenv("STARS_RATE", "1.5"))   # руб. за 1 Star

ADMIN_TOKEN = hashlib.sha256(f"{ADMIN_ID}:{BOT_TOKEN}".encode()).hexdigest()[:24]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

# ── JSON-хранилище ───────────────────────────────────────────────────────────
DATA_DIR   = Path(__file__).parent / "data"
MENU_FILE  = DATA_DIR / "menu.json"
ORDER_FILE = DATA_DIR / "orders.json"
DATA_DIR.mkdir(exist_ok=True)

INITIAL_MENU = [
    {"id":1,"cat":"rolls","name":"Филадельфия классик","desc":"Лосось, сливочный сыр, авокадо","weight":"280 г · 8 шт","price":690,"emoji":"🍣","image":None,"available":True},
    {"id":2,"cat":"rolls","name":"Калифорния","desc":"Краб, авокадо, огурец, икра тобико","weight":"260 г · 8 шт","price":620,"emoji":"🦀","image":None,"available":True},
    {"id":3,"cat":"rolls","name":"Дракон","desc":"Угорь, авокадо, огурец, соус унаги","weight":"300 г · 8 шт","price":750,"emoji":"🐉","image":None,"available":True},
    {"id":4,"cat":"rolls","name":"Спайси тунец","desc":"Тунец, спайси соус, огурец","weight":"250 г · 8 шт","price":680,"emoji":"🌶️","image":None,"available":True},
    {"id":5,"cat":"rolls","name":"Радуга","desc":"Микс рыбы, авокадо, огурец","weight":"320 г · 8 шт","price":790,"emoji":"🌈","image":None,"available":True},
    {"id":6,"cat":"rolls","name":"Запечённый лосось","desc":"Лосось, сыр, японский майонез","weight":"280 г · 8 шт","price":710,"emoji":"🔥","image":None,"available":True},
    {"id":7,"cat":"rolls","name":"Эби темпура","desc":"Тигровая креветка в темпуре, авокадо","weight":"290 г · 8 шт","price":720,"emoji":"🍤","image":None,"available":True},
    {"id":8,"cat":"rolls","name":"Сицилия","desc":"Тунец, вяленые томаты, базилик","weight":"260 г · 8 шт","price":700,"emoji":"🍅","image":None,"available":True},
    {"id":9,"cat":"nigiri","name":"Нигири лосось","desc":"Рис, свежий лосось","weight":"80 г · 2 шт","price":290,"emoji":"🐟","image":None,"available":True},
    {"id":10,"cat":"nigiri","name":"Нигири тунец","desc":"Рис, тунец","weight":"80 г · 2 шт","price":310,"emoji":"🐠","image":None,"available":True},
    {"id":11,"cat":"nigiri","name":"Нигири угорь","desc":"Рис, угорь, соус унаги","weight":"90 г · 2 шт","price":340,"emoji":"🐍","image":None,"available":True},
    {"id":12,"cat":"nigiri","name":"Нигири креветка","desc":"Рис, тигровая креветка","weight":"80 г · 2 шт","price":270,"emoji":"🦐","image":None,"available":True},
    {"id":13,"cat":"sashimi","name":"Сашими лосось","desc":"Свежий лосось, ломтики","weight":"150 г · 5 шт","price":490,"emoji":"🐡","image":None,"available":True},
    {"id":14,"cat":"sashimi","name":"Сашими тунец","desc":"Тунец, нарезка","weight":"150 г · 5 шт","price":520,"emoji":"🎣","image":None,"available":True},
    {"id":15,"cat":"sashimi","name":"Сашими ассорти","desc":"Лосось, тунец, гребешок","weight":"220 г · 9 шт","price":890,"emoji":"🍱","image":None,"available":True},
    {"id":16,"cat":"sets","name":"Сет «Старт»","desc":"Филадельфия + Калифорния (2×8 шт)","weight":"540 г · 16 шт","price":1190,"emoji":"🎁","image":None,"available":True},
    {"id":17,"cat":"sets","name":"Сет «Семейный»","desc":"4 вида роллов (4×8 шт)","weight":"1100 г · 32 шт","price":2390,"emoji":"👨‍👩‍👧‍👦","image":None,"available":True},
    {"id":18,"cat":"sets","name":"Сет «Мясоед»","desc":"Угорь, Дракон, Спайси тунец","weight":"840 г · 24 шт","price":1990,"emoji":"🥩","image":None,"available":True},
    {"id":19,"cat":"drinks","name":"Мисо суп","desc":"Тофу, вакамэ, зелёный лук","weight":"250 мл","price":190,"emoji":"🍵","image":None,"available":True},
    {"id":20,"cat":"drinks","name":"Зелёный чай","desc":"Японский сенча, горячий","weight":"400 мл","price":150,"emoji":"🍃","image":None,"available":True},
    {"id":21,"cat":"drinks","name":"Лимонад матча","desc":"Матча, лайм, мята, содовая","weight":"400 мл","price":220,"emoji":"💚","image":None,"available":True},
    {"id":22,"cat":"drinks","name":"Саке","desc":"Рисовое вино, 14%, горячее","weight":"100 мл","price":280,"emoji":"🍶","image":None,"available":True},
]


def _read(path, default_fn):
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    d = default_fn()
    _write(path, d)
    return d

def _write(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_menu():   return _read(MENU_FILE,  lambda: {"items": INITIAL_MENU, "next_id": 23})
def save_menu(d):  _write(MENU_FILE, d)
def load_orders(): return _read(ORDER_FILE, lambda: {"orders": [], "counter": 0})
def save_orders(d): _write(ORDER_FILE, d)

def create_order(**kw):
    data = load_orders()
    data["counter"] = data.get("counter", 0) + 1
    order = {"id": f"ORD-{data['counter']:04d}", "created_at": time.time(),
             "updated_at": time.time(), "status": "new", **kw}
    data["orders"].insert(0, order)
    save_orders(data)
    return order

def update_order(order_id, **kw):
    data = load_orders()
    for o in data["orders"]:
        if o["id"] == order_id:
            o.update(kw)
            o["updated_at"] = time.time()
            save_orders(data)
            return o
    return None

# Pending Stars заказы (до подтверждения оплаты)
pending_stars: dict[int, dict] = {}

# ── Константы статусов ────────────────────────────────────────────────────────
STATUS_EMOJI  = {"new":"🆕","accepted":"✅","preparing":"👨‍🍳","ready":"📦","delivered":"🚀","cancelled":"❌"}
STATUS_LABEL  = {"new":"Новый","accepted":"Принят","preparing":"Готовится","ready":"Готов","delivered":"Доставлен","cancelled":"Отменён"}
USER_MSGS = {
    "accepted":  "✅ <b>Заказ {id} принят!</b>\nНачинаем готовить — скоро будет готово 🍣",
    "preparing": "👨‍🍳 <b>Заказ {id} на кухне!</b>\nПовара уже готовят ваши роллы ✨",
    "ready":     "📦 <b>Заказ {id} готов!</b>\nПередаём курьеру — ожидайте звонка 🛵",
    "delivered": "🎉 <b>Заказ {id} доставлен!</b>\nПриятного аппетита! Спасибо за заказ 🙏",
    "cancelled": "😔 <b>Заказ {id} отменён.</b>\nЕсли вопросы — напишите @keosOG",
}

def rubles_to_stars(rub): return max(1, round(rub / STARS_RATE))
def fmt_items(items): return "\n".join(f"  • {i['name']} ×{i['qty']} — {i['price']*i['qty']} ₽" for i in items)
def user_tag(u): return f"@{u.username}" if u.username else "—"

def admin_kb(order_id, current_status):
    flow = ["accepted", "preparing", "ready", "delivered"]
    rows, row = [], []
    for st in flow:
        if st != current_status:
            row.append(InlineKeyboardButton(text=f"{STATUS_EMOJI[st]} {STATUS_LABEL[st]}",
                                            callback_data=f"st_{order_id}_{st}"))
        if len(row) == 2:
            rows.append(row); row = []
    if row: rows.append(row)
    if current_status not in ("cancelled", "delivered"):
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
    pay_map = {"stars":"⭐ Telegram Stars","cash":"💵 Наличные","sbp":"🏦 СБП","card":"💳 Карта"}
    stars_line = f"\n⭐ Stars оплачено: {order.get('stars_paid','—')}" if order["payment"] == "stars" else ""
    disc_line  = f"\n🏷 Скидка: {order['discount']}%" if order.get("discount") else ""
    text = (
        f"🔔 <b>Новый заказ {order['id']}!</b>\n{'─'*28}\n"
        f"👤 {user.full_name}  {user_tag(user)}\n"
        f"🆔 <code>{user.id}</code>\n{'─'*28}\n"
        f"📋 <b>Состав:</b>\n{fmt_items(order['items'])}{disc_line}\n{'─'*28}\n"
        f"📍 <b>Адрес:</b> {order['address']}\n"
        f"💳 <b>Оплата:</b> {pay_map.get(order['payment'], order['payment'])}{stars_line}\n"
        f"💰 <b>Итого: {order['total']} ₽</b>\n"
        f"🕐 {time.strftime('%d.%m.%Y %H:%M', time.localtime(order['created_at']))}"
    )
    try:
        msg = await bot.send_message(ADMIN_ID, text, parse_mode="HTML",
                                     reply_markup=admin_kb(order["id"], "new"))
        update_order(order["id"], admin_msg_id=msg.message_id)
    except Exception as e:
        log.warning(f"admin notify: {e}")


# ── Telegram Handlers ─────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🍣 Открыть меню",     web_app=WebAppInfo(url=WEB_APP_URL))
    kb.button(text="📞 Связаться с нами", url="https://t.me/keosOG")
    kb.adjust(1)
    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"🍱 <b>Sushi House</b> — свежие роллы с доставкой.\n\n"
        f"⏱ Доставка ~40 мин · 🚚 Бесплатно от 1500 ₽\n🕐 10:00 — 23:00",
        parse_mode="HTML", reply_markup=kb.as_markup(),
    )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ Нет доступа.")
    admin_url = f"{WEB_APP_URL}/admin.html"
    kb = InlineKeyboardBuilder()
    kb.button(text="⚙️ Открыть панель управления", web_app=WebAppInfo(url=admin_url))
    await message.answer(
        f"👑 <b>Панель администратора</b>\n\n"
        f"🔑 API-токен:\n<code>{ADMIN_TOKEN}</code>\n\n"
        f"Скопируйте токен и вставьте при первом входе в панель.",
        parse_mode="HTML", reply_markup=kb.as_markup(),
    )

@dp.message(Command("orders"))
async def cmd_orders(message: Message):
    if message.from_user.id != ADMIN_ID: return
    orders = load_orders()["orders"][:10]
    if not orders: return await message.answer("📭 Заказов нет.")
    lines = [f"{STATUS_EMOJI.get(o['status'],'?')} <b>{o['id']}</b> · {o['total']} ₽ · "
             f"{time.strftime('%d.%m %H:%M', time.localtime(o['created_at']))}" for o in orders]
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
        user    = message.from_user

        if not items:   return await message.answer("❌ Заказ пустой.")
        if not address: return await message.answer("❌ Укажите адрес доставки.")

        if payment == "stars":
            stars_amt = rubles_to_stars(total)
            pending_stars[user.id] = {"items":items,"total":total,"discount":disc,"address":address,"payment":"stars"}
            desc = "; ".join(f"{i['name']} ×{i['qty']}" for i in items[:3])
            if len(items) > 3: desc += f" +{len(items)-3}"
            await message.answer(
                f"⭐ <b>Оплата через Telegram Stars</b>\n\n"
                f"💰 {total} ₽ → <b>{stars_amt} Stars</b>\n📍 {address}\n\nНажмите «Оплатить» ниже 👇",
                parse_mode="HTML",
            )
            await bot.send_invoice(
                chat_id=user.id, title="Заказ Sushi House 🍣",
                description=f"{desc} · {address}",
                payload=f"order_{user.id}",
                provider_token="",          # ← пусто = Stars
                currency="XTR",
                prices=[LabeledPrice(label="Оплата заказа", amount=stars_amt)],
            )
            return

        order = create_order(
            user_id=user.id, user_name=user.full_name, username=user.username or "",
            items=items, total=total, discount=disc, address=address, payment=payment,
        )
        pay_label = {"cash":"💵 Наличные","sbp":"🏦 СБП","card":"💳 Карта"}.get(payment, payment)
        stub = "\n\n⚠️ <i>Онлайн-оплата временно недоступна. Оператор свяжется с вами.</i>" \
               if payment in ("sbp","card") else ""
        disc_line = f"\n🏷 Скидка: {disc}%" if disc else ""
        kb = InlineKeyboardBuilder()
        kb.button(text="🍣 Ещё заказать", web_app=WebAppInfo(url=WEB_APP_URL))

        await message.answer(
            f"✅ <b>Заказ {order['id']} принят!</b>\n\n"
            f"{fmt_items(items)}{disc_line}\n\n"
            f"📍 <b>Адрес:</b> {address}\n"
            f"💳 <b>Оплата:</b> {pay_label}\n"
            f"💰 <b>Итого: {total} ₽</b>\n\n"
            f"⏱ Ожидайте ~40 минут{stub}",
            parse_mode="HTML", reply_markup=kb.as_markup(),
        )
        await send_admin_notification(user, order)
        log.info(f"Order {order['id']} from {user.id} | {payment} | {total}₽")

    except Exception as e:
        log.error(f"handle_order: {e}", exc_info=True)
        await message.answer("❌ Ошибка обработки заказа. Попробуйте позже.")

@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)

@dp.message(F.successful_payment)
async def on_stars_paid(message: Message):
    user       = message.from_user
    stars_paid = message.successful_payment.total_amount
    pending    = pending_stars.pop(user.id, {})

    order = create_order(
        user_id=user.id, user_name=user.full_name, username=user.username or "",
        items=pending.get("items",[]), total=pending.get("total",0),
        discount=pending.get("discount",0), address=pending.get("address","—"),
        payment="stars", stars_paid=stars_paid,
    )
    disc_line = f"\n🏷 Скидка: {order['discount']}%" if order.get("discount") else ""
    kb = InlineKeyboardBuilder()
    kb.button(text="🍣 Ещё заказать", web_app=WebAppInfo(url=WEB_APP_URL))

    await message.answer(
        f"🎉 <b>Оплата прошла! Заказ {order['id']} принят.</b>\n\n"
        f"{fmt_items(order['items'])}{disc_line}\n\n"
        f"📍 <b>Адрес:</b> {order['address']}\n"
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

    order = update_order(order_id, status=new_status)
    if not order: return await cb.answer("❌ Заказ не найден.", show_alert=True)

    # Обновляем сообщение у админа
    try:
        st_line = f"\n\n{STATUS_EMOJI[new_status]} <b>Статус: {STATUS_LABEL[new_status]}</b>"
        orig = cb.message.html_text
        # Убираем старую строку статуса
        if "\n\n" in orig and "Статус:" in orig:
            orig = orig[:orig.rfind("\n\n")]
        new_kb = admin_kb(order_id, new_status) if new_status not in ("delivered","cancelled") else None
        await cb.message.edit_text(orig + st_line, parse_mode="HTML", reply_markup=new_kb)
    except Exception:
        try:
            await cb.message.edit_reply_markup(
                reply_markup=admin_kb(order_id, new_status) if new_status not in ("delivered","cancelled") else None
            )
        except Exception:
            pass

    await notify_user(order["user_id"], order_id, new_status)
    await cb.answer(f"{STATUS_EMOJI[new_status]} {STATUS_LABEL[new_status]}")
    log.info(f"Order {order_id} → {new_status}")


# ── aiohttp REST API ──────────────────────────────────────────────────────────
CORS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Admin-Token",
}

def jr(data, status=200):
    return web.Response(text=json.dumps(data, ensure_ascii=False),
                        content_type="application/json", status=status, headers=CORS)

def is_admin(req): return req.headers.get("X-Admin-Token","") == ADMIN_TOKEN

async def h_options(req): return web.Response(headers=CORS)

async def h_menu_get(req):           return jr(load_menu())
async def h_menu_post(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    b = await req.json(); data = load_menu()
    nid = data.get("next_id", len(data["items"])+1)
    item = {"id":nid,"cat":b.get("cat","rolls"),"name":b["name"],"desc":b.get("desc",""),
            "weight":b.get("weight",""),"price":int(b["price"]),"emoji":b.get("emoji","🍣"),
            "image":b.get("image"),"available":True}
    data["items"].append(item); data["next_id"]=nid+1; save_menu(data)
    return jr(item,201)

async def h_menu_put(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    iid=int(req.match_info["id"]); b=await req.json(); data=load_menu()
    for item in data["items"]:
        if item["id"]==iid:
            item.update({k:v for k,v in b.items() if k!="id"}); save_menu(data); return jr(item)
    return jr({"error":"Not found"},404)

async def h_menu_del(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    iid=int(req.match_info["id"]); data=load_menu()
    data["items"]=[i for i in data["items"] if i["id"]!=iid]; save_menu(data)
    return jr({"ok":True})

async def h_orders_get(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    return jr(load_orders())

async def h_order_status(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    oid=req.match_info["id"]; b=await req.json(); status=b.get("status")
    order=update_order(oid, status=status)
    if not order: return jr({"error":"Not found"},404)
    asyncio.create_task(notify_user(order["user_id"], oid, status))
    return jr(order)

async def h_stats(req):
    if not is_admin(req): return jr({"error":"Unauthorized"},401)
    orders=load_orders()["orders"]; menu=load_menu()
    now=time.time(); day=now-86400; week=now-604800
    return jr({
        "total_orders":    len(orders),
        "today_orders":    sum(1 for o in orders if o["created_at"]>day),
        "week_orders":     sum(1 for o in orders if o["created_at"]>week),
        "today_revenue":   sum(o["total"] for o in orders if o["created_at"]>day),
        "week_revenue":    sum(o["total"] for o in orders if o["created_at"]>week),
        "total_revenue":   sum(o["total"] for o in orders),
        "pending":         sum(1 for o in orders if o["status"] in ("new","accepted","preparing")),
        "menu_total":      len(menu["items"]),
        "menu_available":  sum(1 for i in menu["items"] if i.get("available",True)),
    })

def build_api():
    app = web.Application()
    app.router.add_options("/{p:.*}", h_options)
    app.router.add_get("/api/menu",                 h_menu_get)
    app.router.add_post("/api/menu",                h_menu_post)
    app.router.add_put("/api/menu/{id}",            h_menu_put)
    app.router.add_delete("/api/menu/{id}",         h_menu_del)
    app.router.add_get("/api/orders",               h_orders_get)
    app.router.add_put("/api/orders/{id}/status",   h_order_status)
    app.router.add_get("/api/stats",                h_stats)
    return app

# ── Запуск ────────────────────────────────────────────────────────────────────
async def main():
    log.info(f"Admin token: {ADMIN_TOKEN}")
    runner = web.AppRunner(build_api())
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    log.info(f"API on :{PORT}")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
