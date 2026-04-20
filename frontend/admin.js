/* ────────────────────────────────────────────────────────────────────────────
   Sushi House — Admin Panel v3
   Секции: Dashboard · Orders · Menu · Locations
   ──────────────────────────────────────────────────────────────────────────── */

const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

// ── Конфиг ───────────────────────────────────────────────────────────────────
let API_BASE = '';
let API_TOKEN = '';

const LOCATIONS = [
  { id:1, name:'Sushi House на Невском', addr:'Невский пр., 47, СПб', hours:'10:00–23:00', phone:'+7 (812) 000-01-01', coords:[59.9340,30.3350], emoji:'🏢' },
  { id:2, name:'Sushi House на Садовой', addr:'Садовая ул., 12, СПб',  hours:'10:00–23:00', phone:'+7 (812) 000-01-02', coords:[59.9267,30.3178], emoji:'🌿' },
  { id:3, name:'Sushi House Васильевский', addr:'Большой пр. В.О., 55, СПб', hours:'11:00–22:00', phone:'+7 (812) 000-01-03', coords:[59.9411,30.2786], emoji:'🏝' },
];

const STATUS_CFG = {
  new:       { label:'🆕 Новый',     cls:'st-new',       next:['accepted','cancelled'] },
  accepted:  { label:'✅ Принят',    cls:'st-accepted',  next:['preparing','cancelled'] },
  preparing: { label:'👨‍🍳 Готовится', cls:'st-preparing', next:['ready','cancelled'] },
  ready:     { label:'📦 Готов',     cls:'st-ready',     next:['delivered','cancelled'] },
  delivered: { label:'🚀 Доставлен', cls:'st-delivered', next:[] },
  cancelled: { label:'❌ Отменён',   cls:'st-cancelled', next:[] },
};

// ── State ────────────────────────────────────────────────────────────────────
let orders = [];
let menu   = [];
let stats  = {};
let currentSection   = 'dashboard';
let ordersFilter     = 'all';
let menuFilter       = 'all';
let autoRefreshTimer = null;
let editingItemId    = null;

// ── DOM ───────────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Toast ──────────────────────────────────────────────────────────────────────
function toast(msg, isErr = false) {
  const el = $('a-toast');
  el.textContent = msg;
  el.className = 'a-toast show' + (isErr ? ' err' : '');
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 2600);
}

// ── API ───────────────────────────────────────────────────────────────────────
async function api(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', 'X-Admin-Token': API_TOKEN },
  };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API_BASE + path, opts);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

async function loadAll() {
  try {
    const [s, o, m] = await Promise.all([
      api('GET','/api/stats'),
      api('GET','/api/orders'),
      api('GET','/api/menu'),
    ]);
    stats  = s;
    orders = o.orders || [];
    menu   = m.items  || [];
    updateBadges();
    return true;
  } catch(e) {
    toast('Ошибка загрузки данных. Проверьте API URL.', true);
    return false;
  }
}

async function loadStats() {
  try { stats = await api('GET','/api/stats'); } catch {}
}
async function loadOrders() {
  try { const d = await api('GET','/api/orders'); orders = d.orders || []; } catch {}
}
async function loadMenu() {
  try { const d = await api('GET','/api/menu'); menu = d.items || []; } catch {}
}

function updateBadges() {
  const pending = orders.filter(o => ['new','accepted','preparing'].includes(o.status)).length;
  [$('nav-badge-orders'), $('bn-badge-orders')].forEach(el => {
    if (!el) return;
    el.textContent = pending || '';
    el.style.display = pending ? '' : 'none';
  });
}

// ── Навигация ─────────────────────────────────────────────────────────────────
function showSection(name) {
  currentSection = name;
  ['dashboard','orders','menu','locations'].forEach(s => {
    $(`sec-${s}`).style.display = s === name ? '' : 'none';
  });
  document.querySelectorAll('.sb-link,.bn-btn').forEach(el => {
    el.classList.toggle('active', el.dataset.section === name);
  });
  switch(name) {
    case 'dashboard': renderDashboard(); break;
    case 'orders':    renderOrders();    break;
    case 'menu':      renderMenu();      break;
    case 'locations': renderLocations(); break;
  }
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
function renderDashboard() {
  const g = $('stats-grid');
  const fmt = n => n?.toLocaleString('ru-RU') ?? '…';
  g.innerHTML = `
    <div class="stat-card stat-card--accent">
      <div class="stat-icon">🛒</div>
      <div class="stat-val">${fmt(stats.today_orders)}</div>
      <div class="stat-label">Заказов сегодня</div>
    </div>
    <div class="stat-card stat-card--green">
      <div class="stat-icon">💰</div>
      <div class="stat-val">${fmt(stats.today_revenue)} ₽</div>
      <div class="stat-label">Выручка сегодня</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">⏳</div>
      <div class="stat-val">${fmt(stats.pending)}</div>
      <div class="stat-label">Активных заказов</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">📦</div>
      <div class="stat-val">${fmt(stats.week_orders)}</div>
      <div class="stat-label">Заказов за неделю</div>
    </div>
    <div class="stat-card stat-card--blue">
      <div class="stat-icon">📈</div>
      <div class="stat-val">${fmt(stats.week_revenue)} ₽</div>
      <div class="stat-label">Выручка за неделю</div>
    </div>
    <div class="stat-card">
      <div class="stat-icon">🍱</div>
      <div class="stat-val">${fmt(stats.menu_available)} / ${fmt(stats.menu_total)}</div>
      <div class="stat-label">Позиций в меню</div>
    </div>`;

  // Активные заказы
  const active = orders.filter(o => ['new','accepted','preparing','ready'].includes(o.status));
  const list   = $('active-orders-list');
  if (!active.length) {
    list.innerHTML = '<div class="order-card--empty">🎉 Нет активных заказов</div>'; return;
  }
  list.innerHTML = active.map(o => renderOrderCard(o, true)).join('');
}

// ── Orders ───────────────────────────────────────────────────────────────────
function renderOrders() {
  const filtered = ordersFilter === 'all'
    ? orders
    : orders.filter(o => o.status === ordersFilter);
  const list = $('orders-list');
  if (!filtered.length) {
    list.innerHTML = '<div class="order-card--empty">Заказов не найдено</div>'; return;
  }
  list.innerHTML = filtered.map(o => renderOrderCard(o)).join('');
}

function renderOrderCard(o, compact = false) {
  const cfg  = STATUS_CFG[o.status] || STATUS_CFG.new;
  const dt   = new Date(o.created_at * 1000).toLocaleString('ru-RU', {day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
  const payMap = {stars:'⭐ Stars', cash:'💵 Наличные', sbp:'🏦 СБП', card:'💳 Карта'};
  const itemsHtml = o.items?.map(i => `<div>${i.emoji||'•'} ${i.name} × ${i.qty} — ${i.price*i.qty} ₽</div>`).join('') || '';
  const starsLine = o.payment === 'stars' ? ` (${o.stars_paid || '—'} Stars)` : '';
  const discLine  = o.discount ? `<div class="order-meta-item">🏷 Скидка <b>${o.discount}%</b></div>` : '';

  const nextBtns = STATUS_CFG[o.status]?.next?.map(st => {
    const c   = STATUS_CFG[st];
    const cls = st === 'cancelled' ? 'status-btn--cancel' : st === 'accepted' ? 'status-btn--accept' : '';
    return `<button class="status-btn ${cls}" data-order-id="${o.id}" data-next-status="${st}">${c.label}</button>`;
  }).join('') || '';

  return `
    <div class="order-card" id="ocard-${o.id}">
      <div class="order-head">
        <span class="order-id">${o.id}</span>
        <span class="order-status ${cfg.cls}">${cfg.label}</span>
        <span style="margin-left:auto;font-size:12px;color:var(--hint)">${dt}</span>
      </div>
      <div class="order-meta">
        <div class="order-meta-item">👤 <b>${o.user_name}</b> ${o.username ? '@'+o.username : ''}</div>
        <div class="order-meta-item">💳 <b>${payMap[o.payment]||o.payment}${starsLine}</b></div>
        <div class="order-meta-item">📍 <b>${o.address}</b></div>
        ${discLine}
      </div>
      ${!compact ? `<div class="order-items-list">${itemsHtml}</div>` : ''}
      <div class="order-total">💰 Итого: ${o.total} ₽</div>
      ${nextBtns ? `<div class="order-actions">${nextBtns}</div>` : ''}
    </div>`;
}

async function changeOrderStatus(orderId, newStatus) {
  try {
    await api('PUT', `/api/orders/${orderId}/status`, { status: newStatus });
    toast(`✅ Статус обновлён: ${STATUS_CFG[newStatus]?.label}`);
    await loadOrders();
    updateBadges();
    if (currentSection === 'orders')    renderOrders();
    if (currentSection === 'dashboard') renderDashboard();
  } catch(e) {
    toast('Ошибка обновления статуса', true);
  }
}

// ── Menu ──────────────────────────────────────────────────────────────────────
function renderMenu() {
  const items = menuFilter === 'all' ? menu : menu.filter(i => i.cat === menuFilter);
  const grid  = $('menu-admin-grid');
  if (!items.length) {
    grid.innerHTML = '<div class="order-card--empty">Позиций нет</div>'; return;
  }
  const catLabel = {rolls:'Роллы',nigiri:'Нигири',sashimi:'Сашими',sets:'Сеты',drinks:'Напитки'};
  grid.innerHTML = items.map(item => {
    const avail  = item.available !== false;
    const imgEl  = item.image
      ? `<img src="${item.image}" alt="" onerror="this.style.display='none'">`
      : item.emoji;
    return `
      <div class="ma-card ${avail ? '' : 'unavail'}" id="mcard-${item.id}">
        <div class="ma-card-img">
          ${imgEl}
          <span class="ma-card-badge ${avail ? '' : 'ma-card-badge--paused'}">
            ${avail ? catLabel[item.cat]||item.cat : '⏸ Пауза'}
          </span>
        </div>
        <div class="ma-card-body">
          <div class="ma-card-name">${item.name}</div>
          <div class="ma-card-cat">${item.desc}</div>
          <div class="ma-card-price">${item.price} ₽</div>
          <div class="ma-card-weight">${item.weight}</div>
          <div class="ma-card-actions">
            <button class="ma-btn ma-btn--pause ${avail ? '' : 'active'}"
              data-ma="toggle" data-id="${item.id}">${avail ? '⏸ Пауза' : '▶ Включить'}</button>
            <button class="ma-btn ma-btn--edit" data-ma="edit" data-id="${item.id}">✏️</button>
            <button class="ma-btn ma-btn--del"  data-ma="del"  data-id="${item.id}">🗑</button>
          </div>
        </div>
      </div>`;
  }).join('');
}

async function toggleAvailability(itemId) {
  const item = menu.find(i => i.id === +itemId);
  if (!item) return;
  const newVal = item.available === false;  // toggle
  try {
    await api('PUT', `/api/menu/${itemId}`, { available: newVal });
    item.available = newVal;
    toast(newVal ? '▶ Позиция включена' : '⏸ Позиция на паузе');
    renderMenu();
  } catch {
    toast('Ошибка', true);
  }
}

function openItemModal(itemId = null) {
  editingItemId = itemId;
  const item = itemId ? menu.find(i => i.id === +itemId) : null;
  $('item-modal-title').textContent = item ? 'Редактировать позицию' : 'Добавить позицию';
  $('item-id').value     = itemId || '';
  $('item-name').value   = item?.name    || '';
  $('item-desc').value   = item?.desc    || '';
  $('item-price').value  = item?.price   || '';
  $('item-weight').value = item?.weight  || '';
  $('item-emoji').value  = item?.emoji   || '🍣';
  $('item-image').value  = item?.image   || '';
  $('item-cat').value    = item?.cat     || 'rolls';
  $('item-err').textContent = '';
  $('item-modal').style.display = 'flex';
}

function closeItemModal() {
  $('item-modal').style.display = 'none';
  editingItemId = null;
}

async function saveItem() {
  const name  = $('item-name').value.trim();
  const price = +$('item-price').value;
  if (!name || !price) {
    $('item-err').textContent = 'Заполните обязательные поля (название, цена)';
    return;
  }
  const body = {
    name, price,
    cat:    $('item-cat').value,
    desc:   $('item-desc').value.trim(),
    weight: $('item-weight').value.trim(),
    emoji:  $('item-emoji').value.trim() || '🍣',
    image:  $('item-image').value.trim() || null,
  };
  try {
    if (editingItemId) {
      await api('PUT', `/api/menu/${editingItemId}`, body);
      toast('✅ Позиция обновлена');
    } else {
      await api('POST', '/api/menu', body);
      toast('✅ Позиция добавлена');
    }
    closeItemModal();
    await loadMenu();
    renderMenu();
  } catch(e) {
    $('item-err').textContent = 'Ошибка сохранения: ' + e.message;
  }
}

function confirmDelete(itemId) {
  const item = menu.find(i => i.id === +itemId);
  $('confirm-title').textContent = 'Удалить позицию?';
  $('confirm-text').textContent  = item ? `«${item.name}» будет удалена из меню.` : '';
  $('confirm-modal').style.display = 'flex';
  $('confirm-yes').onclick = async () => {
    $('confirm-modal').style.display = 'none';
    try {
      await api('DELETE', `/api/menu/${itemId}`);
      toast('🗑 Позиция удалена');
      await loadMenu();
      renderMenu();
    } catch {
      toast('Ошибка удаления', true);
    }
  };
}

// ── Locations ─────────────────────────────────────────────────────────────────
function renderLocations() {
  $('locations-list').innerHTML = LOCATIONS.map(loc => `
    <div class="loc-admin-card">
      <div class="la-head">
        <div class="la-icon">${loc.emoji}</div>
        <div>
          <div class="la-name">${loc.name}</div>
          <div class="la-addr">📍 ${loc.addr}</div>
        </div>
      </div>
      <div class="la-meta">
        <div class="la-meta-item">
          <div class="la-meta-label">Часы работы</div>
          <div class="la-meta-val">🕐 ${loc.hours}</div>
        </div>
        <div class="la-meta-item">
          <div class="la-meta-label">Телефон</div>
          <div class="la-meta-val">📞 <a href="tel:${loc.phone.replace(/\D/g,'')}" style="color:var(--blue);text-decoration:none">${loc.phone}</a></div>
        </div>
        <div class="la-meta-item">
          <div class="la-meta-label">Координаты</div>
          <div class="la-meta-val" style="font-size:11px">${loc.coords.join(', ')}</div>
        </div>
      </div>
      <button class="la-map-btn" onclick="openGMap(${loc.coords[0]},${loc.coords[1]})">
        🗺 Открыть на карте
      </button>
    </div>`).join('');
}

function openGMap(lat, lng) {
  const url = `https://maps.google.com/maps?q=${lat},${lng}&z=16`;
  if (tg) tg.openLink(url);
  else window.open(url, '_blank');
}

// ── Setup ─────────────────────────────────────────────────────────────────────
function loadCreds() {
  API_BASE  = localStorage.getItem('sh_api_base')  || '';
  API_TOKEN = localStorage.getItem('sh_api_token') || '';
  return !!(API_BASE && API_TOKEN);
}
function saveCreds(base, token) {
  localStorage.setItem('sh_api_base',  base);
  localStorage.setItem('sh_api_token', token);
  API_BASE  = base;
  API_TOKEN = token;
}

async function initApp() {
  if (!loadCreds()) {
    $('setup-modal').style.display = 'flex';
    return;
  }
  const ok = await loadAll();
  if (!ok) {
    $('setup-modal').style.display = 'flex';
    return;
  }
  $('setup-modal').style.display = 'none';
  $('app').style.display = '';
  showSection('dashboard');
  startAutoRefresh();
}

function startAutoRefresh() {
  clearInterval(autoRefreshTimer);
  autoRefreshTimer = setInterval(async () => {
    await loadAll();
    if (currentSection === 'dashboard') renderDashboard();
    if (currentSection === 'orders')    renderOrders();
  }, 30000);  // каждые 30 сек
}

// ── Event Listeners ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Setup save
  $('setup-save-btn').onclick = async () => {
    const base  = $('setup-url').value.trim().replace(/\/+$/, '');
    const token = $('setup-token').value.trim();
    if (!base || !token) { $('setup-err').textContent = 'Заполните оба поля'; return; }
    saveCreds(base, token);
    $('setup-err').textContent = '';
    await initApp();
  };

  // Navigation
  document.addEventListener('click', e => {
    const navEl = e.target.closest('[data-section]');
    if (navEl) { showSection(navEl.dataset.section); return; }

    // Order status buttons
    const statusBtn = e.target.closest('[data-next-status]');
    if (statusBtn) {
      changeOrderStatus(statusBtn.dataset.orderId, statusBtn.dataset.nextStatus);
      return;
    }

    // Menu actions
    const maBtn = e.target.closest('[data-ma]');
    if (maBtn) {
      const action = maBtn.dataset.ma;
      const id     = maBtn.dataset.id;
      if (action === 'toggle') toggleAvailability(id);
      if (action === 'edit')   openItemModal(id);
      if (action === 'del')    confirmDelete(id);
      return;
    }
  });

  // Orders filter
  $('orders-filter').addEventListener('click', e => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    ordersFilter = btn.dataset.status;
    $('orders-filter').querySelectorAll('.filter-btn')
      .forEach(b => b.classList.toggle('active', b === btn));
    renderOrders();
  });

  // Menu filter
  document.querySelector('.menu-filter-bar').addEventListener('click', e => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    menuFilter = btn.dataset.mcat;
    document.querySelectorAll('.menu-filter-bar .filter-btn')
      .forEach(b => b.classList.toggle('active', b === btn));
    renderMenu();
  });

  // Refresh buttons
  $('refresh-btn').onclick = async () => {
    await loadAll();
    renderDashboard();
    toast('Данные обновлены');
  };
  $('orders-refresh-btn').onclick = async () => {
    await loadOrders();
    renderOrders();
    toast('Обновлено');
  };

  // Add menu item
  $('add-item-btn').onclick = () => openItemModal(null);

  // Item modal
  $('item-modal-close').onclick  = closeItemModal;
  $('item-cancel-btn').onclick   = closeItemModal;
  $('item-save-btn').onclick     = saveItem;

  // Confirm modal
  $('confirm-no').onclick = () => { $('confirm-modal').style.display = 'none'; };

  // Settings button (сбросить настройки)
  $('sb-settings-btn').onclick = () => {
    if (!confirm('Сбросить настройки подключения?')) return;
    localStorage.removeItem('sh_api_base');
    localStorage.removeItem('sh_api_token');
    clearInterval(autoRefreshTimer);
    $('app').style.display = 'none';
    $('setup-modal').style.display = 'flex';
  };

  // Close modals by overlay click
  $('item-modal').addEventListener('click', e => {
    if (e.target === $('item-modal')) closeItemModal();
  });
  $('confirm-modal').addEventListener('click', e => {
    if (e.target === $('confirm-modal')) $('confirm-modal').style.display = 'none';
  });

  // Enter in setup
  [$('setup-url'), $('setup-token')].forEach(el => {
    el.addEventListener('keydown', e => { if (e.key === 'Enter') $('setup-save-btn').click(); });
  });

  // Enter in item form
  [$('item-name'), $('item-price'), $('item-weight'), $('item-emoji')].forEach(el => {
    el.addEventListener('keydown', e => { if (e.key === 'Enter') saveItem(); });
  });

  initApp();
});
