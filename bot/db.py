“””
db.py — PostgreSQL-слой через asyncpg.
Таблицы: menu_items, orders, order_items, restaurants, counters
“””
import json
import logging
import os
import time

import asyncpg

log = logging.getLogger(**name**)

DATABASE_URL = os.getenv(“DATABASE_URL”, “”)

pool: asyncpg.Pool | None = None

INITIAL_MENU = [
(1,“rolls”,“Филадельфия классик”,“Лосось, сливочный сыр, авокадо”,“Лосось, сливочный сыр Philadelphia, авокадо, нори, рис”,“280 г · 8 шт”,690,“🍣”,None,True),
(2,“rolls”,“Калифорния”,“Краб, авокадо, огурец, икра тобико”,“Крабовые палочки, авокадо, огурец, икра тобико, нори, рис”,“260 г · 8 шт”,620,“🦀”,None,True),
(3,“rolls”,“Дракон”,“Угорь, авокадо, огурец, соус унаги”,“Угорь, авокадо, огурец, соус унаги, нори, рис”,“300 г · 8 шт”,750,“🐉”,None,True),
(4,“rolls”,“Спайси тунец”,“Тунец, спайси соус, огурец”,“Тунец, острый майонез, огурец, нори, рис”,“250 г · 8 шт”,680,“🌶️”,None,True),
(5,“rolls”,“Радуга”,“Микс рыбы, авокадо, огурец”,“Лосось, тунец, угорь, авокадо, огурец, нори, рис”,“320 г · 8 шт”,790,“🌈”,None,True),
(6,“rolls”,“Запечённый лосось”,“Лосось, сыр, японский майонез”,“Лосось, сыр сливочный, японский майонез, нори, рис — запечено в духовке”,“280 г · 8 шт”,710,“🔥”,None,True),
(7,“rolls”,“Эби темпура”,“Тигровая креветка в темпуре, авокадо”,“Тигровая креветка в темпурном кляре, авокадо, соус спайси, нори, рис”,“290 г · 8 шт”,720,“🍤”,None,True),
(8,“rolls”,“Сицилия”,“Тунец, вяленые томаты, базилик”,“Тунец, вяленые томаты, листья базилика, соус песто, нори, рис”,“260 г · 8 шт”,700,“🍅”,None,True),
(9,“nigiri”,“Нигири лосось”,“Рис, свежий лосось”,“Свежий лосось суши-нарезки на рисовой подушке”,“80 г · 2 шт”,290,“🐟”,None,True),
(10,“nigiri”,“Нигири тунец”,“Рис, тунец”,“Тунец суши-нарезки на рисовой подушке”,“80 г · 2 шт”,310,“🐠”,None,True),
(11,“nigiri”,“Нигири угорь”,“Рис, угорь, соус унаги”,“Жареный угорь на рисовой подушке с соусом унаги”,“90 г · 2 шт”,340,“🐍”,None,True),
(12,“nigiri”,“Нигири креветка”,“Рис, тигровая креветка”,“Тигровая креветка на рисовой подушке”,“80 г · 2 шт”,270,“🦐”,None,True),
(13,“sashimi”,“Сашими лосось”,“Свежий лосось, ломтики”,“5 ломтиков свежего норвежского лосося”,“150 г · 5 шт”,490,“🐡”,None,True),
(14,“sashimi”,“Сашими тунец”,“Тунец, нарезка”,“5 ломтиков свежего тунца”,“150 г · 5 шт”,520,“🎣”,None,True),
(15,“sashimi”,“Сашими ассорти”,“Лосось, тунец, гребешок”,“9 ломтиков: лосось, тунец, морской гребешок”,“220 г · 9 шт”,890,“🍱”,None,True),
(16,“sets”,“Сет «Старт»”,“Филадельфия + Калифорния (2×8 шт)”,“Идеальный старт: Филадельфия классик и Калифорния, 16 кусочков”,“540 г · 16 шт”,1190,“🎁”,None,True),
(17,“sets”,“Сет «Семейный»”,“4 вида роллов (4×8 шт)”,“Большой набор на компанию: 4 любых ролла, 32 кусочка”,“1100 г · 32 шт”,2390,“👨👩👧👦”,None,True),
(18,“sets”,“Сет «Мясоед»”,“Угорь, Дракон, Спайси тунец”,“Три ролла для настоящих ценителей: Дракон, Угорь и Спайси тунец”,“840 г · 24 шт”,1990,“🥩”,None,True),
(19,“drinks”,“Мисо суп”,“Тофу, вакамэ, зелёный лук”,“Классический японский суп мисо с тофу, водорослями вакамэ и зелёным луком”,“250 мл”,190,“🍵”,None,True),
(20,“drinks”,“Зелёный чай”,“Японский сенча, горячий”,“Японский чай сенча высшего сорта, заварен при 80°C”,“400 мл”,150,“🍃”,None,True),
(21,“drinks”,“Лимонад матча”,“Матча, лайм, мята, содовая”,“Освежающий лимонад с церемониальным маття, лаймом, свежей мятой и содовой”,“400 мл”,220,“💚”,None,True),
(22,“drinks”,“Саке”,“Рисовое вино, 14%, горячее”,“Традиционное японское саке, подаётся горячим в керамическом тосканчике”,“100 мл”,280,“🍶”,None,True),
]

INITIAL_RESTAURANTS = [
(1,“Sushi House на Невском”,“Невский пр., 47”,“Санкт-Петербург”,“10:00–23:00”,”+7 (812) 000-01-01”,59.9340,30.3350,“🏢”,True),
(2,“Sushi House на Садовой”,“Садовая ул., 12”,“Санкт-Петербург”,“10:00–23:00”,”+7 (812) 000-01-02”,59.9267,30.3178,“🌿”,True),
(3,“Sushi House Васильевский”,“Большой пр. В.О., 55”,“Санкт-Петербург”,“11:00–22:00”,”+7 (812) 000-01-03”,59.9411,30.2786,“🏝”,True),
]

# ── Инициализация ─────────────────────────────────────────────────────────────

async def init():
global pool
pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
async with pool.acquire() as c:
await _create_tables(c)
await _seed(c)
log.info(“✅ PostgreSQL pool ready”)

async def _create_tables(c: asyncpg.Connection):
await c.execute(”””
CREATE TABLE IF NOT EXISTS counters (
key   TEXT PRIMARY KEY,
value BIGINT DEFAULT 0
);

```
CREATE TABLE IF NOT EXISTS restaurants (
    id        SERIAL PRIMARY KEY,
    name      TEXT NOT NULL,
    street    TEXT,
    city      TEXT,
    hours     TEXT,
    phone     TEXT,
    lat       DOUBLE PRECISION,
    lng       DOUBLE PRECISION,
    emoji     TEXT DEFAULT '🏢',
    active    BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS menu_items (
    id          SERIAL PRIMARY KEY,
    cat         TEXT NOT NULL,
    name        TEXT NOT NULL,
    desc        TEXT DEFAULT '',
    ingredients TEXT DEFAULT '',
    weight      TEXT DEFAULT '',
    price       INTEGER NOT NULL,
    emoji       TEXT DEFAULT '🍣',
    image       TEXT,
    available   BOOLEAN DEFAULT TRUE,
    sort_order  INTEGER DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id              TEXT PRIMARY KEY,
    user_id         BIGINT NOT NULL,
    user_name       TEXT,
    username        TEXT,
    status          TEXT DEFAULT 'new',
    total           INTEGER NOT NULL,
    discount        INTEGER DEFAULT 0,
    address         TEXT,
    payment         TEXT,
    stars_paid      INTEGER,
    admin_msg_id    BIGINT,
    restaurant_id   INTEGER REFERENCES restaurants(id),
    restaurant_name TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_items (
    id         SERIAL PRIMARY KEY,
    order_id   TEXT REFERENCES orders(id) ON DELETE CASCADE,
    item_name  TEXT,
    qty        INTEGER,
    price      INTEGER,
    emoji      TEXT
);
""")
# Индексы
await c.execute("""
    CREATE INDEX IF NOT EXISTS idx_orders_user_id   ON orders(user_id);
    CREATE INDEX IF NOT EXISTS idx_orders_status    ON orders(status);
    CREATE INDEX IF NOT EXISTS idx_orders_created   ON orders(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_order_items_oid  ON order_items(order_id);
""")
```

async def _seed(c: asyncpg.Connection):
# counter
await c.execute(“INSERT INTO counters VALUES (‘order_counter’,0) ON CONFLICT DO NOTHING”)
# restaurants
rc = await c.fetchval(“SELECT COUNT(*) FROM restaurants”)
if rc == 0:
await c.executemany(
“INSERT INTO restaurants (id,name,street,city,hours,phone,lat,lng,emoji,active) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)”,
INITIAL_RESTAURANTS
)
await c.execute(“SELECT setval(‘restaurants_id_seq’, (SELECT MAX(id) FROM restaurants))”)
# menu
mc = await c.fetchval(“SELECT COUNT(*) FROM menu_items”)
if mc == 0:
await c.executemany(
“INSERT INTO menu_items (id,cat,name,desc,ingredients,weight,price,emoji,image,available) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)”,
INITIAL_MENU
)
await c.execute(“SELECT setval(‘menu_items_id_seq’, (SELECT MAX(id) FROM menu_items))”)

# ── Меню ──────────────────────────────────────────────────────────────────────

async def get_menu(available_only=False) -> list[dict]:
q = “SELECT * FROM menu_items”
if available_only:
q += “ WHERE available = TRUE”
q += “ ORDER BY cat, id”
async with pool.acquire() as c:
rows = await c.fetch(q)
return [dict(r) for r in rows]

async def get_menu_item(item_id: int) -> dict | None:
async with pool.acquire() as c:
r = await c.fetchrow(“SELECT * FROM menu_items WHERE id=$1”, item_id)
return dict(r) if r else None

async def create_menu_item(data: dict) -> dict:
async with pool.acquire() as c:
r = await c.fetchrow(”””
INSERT INTO menu_items (cat,name,desc,ingredients,weight,price,emoji,image,available)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,TRUE)
RETURNING *
“””, data[“cat”], data[“name”], data.get(“desc”,””),
data.get(“ingredients”,””), data.get(“weight”,””),
int(data[“price”]), data.get(“emoji”,“🍣”), data.get(“image”))
return dict(r)

async def update_menu_item(item_id: int, data: dict) -> dict | None:
fields, vals, idx = [], [], 1
for k in (“cat”,“name”,“desc”,“ingredients”,“weight”,“price”,“emoji”,“image”,“available”,“sort_order”):
if k in data:
fields.append(f”{k}=${idx}”); vals.append(data[k]); idx+=1
if not fields:
return await get_menu_item(item_id)
vals.append(item_id)
async with pool.acquire() as c:
r = await c.fetchrow(
f”UPDATE menu_items SET {’,’.join(fields)} WHERE id=${idx} RETURNING *”, *vals)
return dict(r) if r else None

async def delete_menu_item(item_id: int) -> bool:
async with pool.acquire() as c:
r = await c.execute(“DELETE FROM menu_items WHERE id=$1”, item_id)
return r == “DELETE 1”

# ── Рестораны ─────────────────────────────────────────────────────────────────

async def get_restaurants(active_only=True) -> list[dict]:
q = “SELECT * FROM restaurants”
if active_only:
q += “ WHERE active=TRUE”
q += “ ORDER BY id”
async with pool.acquire() as c:
rows = await c.fetch(q)
return [dict(r) for r in rows]

async def get_restaurant(rid: int) -> dict | None:
async with pool.acquire() as c:
r = await c.fetchrow(“SELECT * FROM restaurants WHERE id=$1”, rid)
return dict(r) if r else None

# ── Заказы ────────────────────────────────────────────────────────────────────

async def next_order_id() -> str:
async with pool.acquire() as c:
n = await c.fetchval(
“UPDATE counters SET value=value+1 WHERE key=‘order_counter’ RETURNING value”)
return f”ORD-{n:04d}”

async def create_order(user_id, user_name, username, items, total,
discount, address, payment, restaurant_id=None,
restaurant_name=None, stars_paid=None) -> dict:
oid = await next_order_id()
async with pool.acquire() as c:
async with c.transaction():
r = await c.fetchrow(”””
INSERT INTO orders
(id,user_id,user_name,username,total,discount,address,
payment,stars_paid,restaurant_id,restaurant_name)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
RETURNING *
“””, oid, user_id, user_name, username, total, discount,
address, payment, stars_paid, restaurant_id, restaurant_name)
if items:
await c.executemany(”””
INSERT INTO order_items (order_id,item_name,qty,price,emoji)
VALUES ($1,$2,$3,$4,$5)
“””, [(oid, i[“name”], i[“qty”], i[“price”], i.get(“emoji”,””)) for i in items])
return await get_order(oid)

async def get_order(order_id: str) -> dict | None:
async with pool.acquire() as c:
row = await c.fetchrow(“SELECT * FROM orders WHERE id=$1”, order_id)
if not row:
return None
order = dict(row)
items = await c.fetch(
“SELECT * FROM order_items WHERE order_id=$1 ORDER BY id”, order_id)
order[“items”] = [dict(i) for i in items]
return order

async def update_order_status(order_id: str, status: str) -> dict | None:
async with pool.acquire() as c:
r = await c.fetchrow(”””
UPDATE orders SET status=$1, updated_at=NOW()
WHERE id=$2 RETURNING *
“””, status, order_id)
if not r:
return None
order = dict(r)
items = await c.fetch(
“SELECT * FROM order_items WHERE order_id=$1 ORDER BY id”, order_id)
order[“items”] = [dict(i) for i in items]
return order

async def update_order_admin_msg(order_id: str, msg_id: int):
async with pool.acquire() as c:
await c.execute(
“UPDATE orders SET admin_msg_id=$1 WHERE id=$2”, msg_id, order_id)

async def get_orders(limit=100, status=None, user_id=None) -> list[dict]:
cond, vals = [], []
idx = 1
if status and status != “all”:
cond.append(f”status=${idx}”); vals.append(status); idx+=1
if user_id:
cond.append(f”user_id=${idx}”); vals.append(user_id); idx+=1
where = f”WHERE {’ AND ’.join(cond)}” if cond else “”
vals.append(limit)
async with pool.acquire() as c:
rows = await c.fetch(
f”SELECT * FROM orders {where} ORDER BY created_at DESC LIMIT ${idx}”, *vals)
orders = []
for row in rows:
order = dict(row)
items = await c.fetch(
“SELECT * FROM order_items WHERE order_id=$1 ORDER BY id”, order[“id”])
order[“items”] = [dict(i) for i in items]
orders.append(order)
return orders

async def get_stats() -> dict:
async with pool.acquire() as c:
total_orders  = await c.fetchval(“SELECT COUNT(*) FROM orders”)
today_orders  = await c.fetchval(“SELECT COUNT(*) FROM orders WHERE created_at > NOW()-INTERVAL ‘1 day’”)
week_orders   = await c.fetchval(“SELECT COUNT(*) FROM orders WHERE created_at > NOW()-INTERVAL ‘7 days’”)
today_rev     = await c.fetchval(“SELECT COALESCE(SUM(total),0) FROM orders WHERE created_at > NOW()-INTERVAL ‘1 day’”)
week_rev      = await c.fetchval(“SELECT COALESCE(SUM(total),0) FROM orders WHERE created_at > NOW()-INTERVAL ‘7 days’”)
total_rev     = await c.fetchval(“SELECT COALESCE(SUM(total),0) FROM orders”)
pending       = await c.fetchval(“SELECT COUNT(*) FROM orders WHERE status IN (‘new’,‘accepted’,‘preparing’,‘ready’)”)
menu_total    = await c.fetchval(“SELECT COUNT(*) FROM menu_items”)
menu_avail    = await c.fetchval(“SELECT COUNT(*) FROM menu_items WHERE available=TRUE”)
return {
“total_orders”: total_orders, “today_orders”: today_orders,
“week_orders”: week_orders, “today_revenue”: today_rev,
“week_revenue”: week_rev,   “total_revenue”: total_rev,
“pending”: pending, “menu_total”: menu_total, “menu_available”: menu_avail,
}
