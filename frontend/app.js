/* ────────────────────────────────────────────────────────────────────────────
   Sushi House — Customer Mini App v3
   • Event delegation (исправлен баг корзины)
   • Чистое управление состоянием через единый объект state
   • Checkout: адрес + способ оплаты
   • Вкладки: Меню / Адреса
   ──────────────────────────────────────────────────────────────────────────── */

const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); tg.enableClosingConfirmation(); }

// ── Конфиг ───────────────────────────────────────────────────────────────────
const API_BASE = window.SUSHI_API_URL || '';   // Если есть бэкенд — подставить URL

const PROMOS = { 'SUSHI10': 10, 'ROLL20': 20, 'WELCOME15': 15 };

const LOCATIONS = [
  { id:1, name:'Sushi House на Невском', address:'Невский пр., 47, Санкт-Петербург', hours:'10:00 – 23:00', phone:'+7 (812) 000-01-01', coords:[59.9340, 30.3350], emoji:'🏢' },
  { id:2, name:'Sushi House на Садовой', address:'Садовая ул., 12, Санкт-Петербург', hours:'10:00 – 23:00', phone:'+7 (812) 000-01-02', coords:[59.9267, 30.3178], emoji:'🌿' },
  { id:3, name:'Sushi House на Васильевском', address:'Большой пр. В.О., 55, Санкт-Петербург', hours:'11:00 – 22:00', phone:'+7 (812) 000-01-03', coords:[59.9411, 30.2786], emoji:'🏝' },
];

// ── Состояние ─────────────────────────────────────────────────────────────────
const S = {
  menu:       [],          // загружается с бэкенда или из INITIAL_MENU
  cart:       {},          // { itemId: qty }
  category:   'all',
  discount:   0,
  promoCode:  '',
  tab:        'menu',      // 'menu' | 'locations'
  cartOpen:   false,
  checkoutOpen: false,
};

// Статическое меню (фолбэк, если нет API)
const INITIAL_MENU = [
  {id:1,cat:'rolls',name:'Филадельфия классик',desc:'Лосось, сливочный сыр, авокадо',weight:'280 г · 8 шт',price:690,emoji:'🍣',image:null,available:true},
  {id:2,cat:'rolls',name:'Калифорния',desc:'Краб, авокадо, огурец, икра тобико',weight:'260 г · 8 шт',price:620,emoji:'🦀',image:null,available:true},
  {id:3,cat:'rolls',name:'Дракон',desc:'Угорь, авокадо, огурец, соус унаги',weight:'300 г · 8 шт',price:750,emoji:'🐉',image:null,available:true},
  {id:4,cat:'rolls',name:'Спайси тунец',desc:'Тунец, спайси соус, огурец',weight:'250 г · 8 шт',price:680,emoji:'🌶️',image:null,available:true},
  {id:5,cat:'rolls',name:'Радуга',desc:'Микс рыбы, авокадо, огурец',weight:'320 г · 8 шт',price:790,emoji:'🌈',image:null,available:true},
  {id:6,cat:'rolls',name:'Запечённый лосось',desc:'Лосось, сыр, японский майонез',weight:'280 г · 8 шт',price:710,emoji:'🔥',image:null,available:true},
  {id:7,cat:'rolls',name:'Эби темпура',desc:'Тигровая креветка в темпуре, авокадо',weight:'290 г · 8 шт',price:720,emoji:'🍤',image:null,available:true},
  {id:8,cat:'rolls',name:'Сицилия',desc:'Тунец, вяленые томаты, базилик',weight:'260 г · 8 шт',price:700,emoji:'🍅',image:null,available:true},
  {id:9,cat:'nigiri',name:'Нигири лосось',desc:'Рис, свежий лосось',weight:'80 г · 2 шт',price:290,emoji:'🐟',image:null,available:true},
  {id:10,cat:'nigiri',name:'Нигири тунец',desc:'Рис, тунец',weight:'80 г · 2 шт',price:310,emoji:'🐠',image:null,available:true},
  {id:11,cat:'nigiri',name:'Нигири угорь',desc:'Рис, угорь, соус унаги',weight:'90 г · 2 шт',price:340,emoji:'🐍',image:null,available:true},
  {id:12,cat:'nigiri',name:'Нигири креветка',desc:'Рис, тигровая креветка',weight:'80 г · 2 шт',price:270,emoji:'🦐',image:null,available:true},
  {id:13,cat:'sashimi',name:'Сашими лосось',desc:'Свежий лосось, ломтики',weight:'150 г · 5 шт',price:490,emoji:'🐡',image:null,available:true},
  {id:14,cat:'sashimi',name:'Сашими тунец',desc:'Тунец, нарезка',weight:'150 г · 5 шт',price:520,emoji:'🎣',image:null,available:true},
  {id:15,cat:'sashimi',name:'Сашими ассорти',desc:'Лосось, тунец, гребешок',weight:'220 г · 9 шт',price:890,emoji:'🍱',image:null,available:true},
  {id:16,cat:'sets',name:'Сет «Старт»',desc:'Филадельфия + Калифорния (2×8 шт)',weight:'540 г · 16 шт',price:1190,emoji:'🎁',image:null,available:true},
  {id:17,cat:'sets',name:'Сет «Семейный»',desc:'4 вида роллов (4×8 шт)',weight:'1100 г · 32 шт',price:2390,emoji:'👨‍👩‍👧‍👦',image:null,available:true},
  {id:18,cat:'sets',name:'Сет «Мясоед»',desc:'Угорь, Дракон, Спайси тунец',weight:'840 г · 24 шт',price:1990,emoji:'🥩',image:null,available:true},
  {id:19,cat:'drinks',name:'Мисо суп',desc:'Тофу, вакамэ, зелёный лук',weight:'250 мл',price:190,emoji:'🍵',image:null,available:true},
  {id:20,cat:'drinks',name:'Зелёный чай',desc:'Японский сенча, горячий',weight:'400 мл',price:150,emoji:'🍃',image:null,available:true},
  {id:21,cat:'drinks',name:'Лимонад матча',desc:'Матча, лайм, мята, содовая',weight:'400 мл',price:220,emoji:'💚',image:null,available:true},
  {id:22,cat:'drinks',name:'Саке',desc:'Рисовое вино, 14%, горячее',weight:'100 мл',price:280,emoji:'🍶',image:null,available:true},
];

// ── Утилиты ───────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const byQ = sel => document.querySelector(sel);
const byQA = sel => document.querySelectorAll(sel);

function haptic(type) {
  if (!tg?.HapticFeedback) return;
  if (type === 'light')   tg.HapticFeedback.impactOccurred('light');
  if (type === 'medium')  tg.HapticFeedback.impactOccurred('medium');
  if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
  if (type === 'error')   tg.HapticFeedback.notificationOccurred('error');
}

function toast(msg, isErr = false) {
  const el = $('toast');
  el.textContent = msg;
  el.className = 'toast' + (isErr ? ' toast--err' : '') + ' toast--show';
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('toast--show'), 2600);
}

function calcTotals() {
  let subtotal = 0, qty = 0;
  for (const [id, q] of Object.entries(S.cart)) {
    const item = S.menu.find(m => m.id === +id);
    if (!item) continue;
    subtotal += item.price * q;
    qty += q;
  }
  const discAmt  = Math.round(subtotal * S.discount / 100);
  const delivery = subtotal >= 1500 ? 0 : 199;
  const total    = subtotal - discAmt + delivery;
  return { subtotal, discAmt, delivery, total, qty };
}

function getItem(id) { return S.menu.find(m => m.id === +id); }

// ── Загрузка меню ─────────────────────────────────────────────────────────────
async function loadMenu() {
  if (API_BASE) {
    try {
      const r = await fetch(`${API_BASE}/api/menu`);
      const d = await r.json();
      S.menu = d.items.filter(i => i.available !== false);
      return;
    } catch { /* fallback */ }
  }
  S.menu = INITIAL_MENU;
}

// ── Event Delegation (единая точка входа для всех кликов) ─────────────────────
document.addEventListener('click', e => {
  const el = e.target.closest('[data-a]');
  if (!el) return;
  e.preventDefault();
  const a  = el.dataset.a;
  const id = el.dataset.id ? +el.dataset.id : null;

  switch (a) {
    // Корзина
    case 'add':      modifyCart(id, +1); break;
    case 'sub':      modifyCart(id, -1); break;
    // Навигация
    case 'tab':      setTab(el.dataset.tab); break;
    case 'cat':      setCat(el.dataset.cat); break;
    // Корзина / чекаут
    case 'open-cart':     openCart();     break;
    case 'close-cart':    closeCart();    break;
    case 'open-checkout': openCheckout(); break;
    case 'back-cart':     backToCart();   break;
    case 'submit':        submitOrder();  break;
    case 'reset':         resetAll();     break;
    case 'apply-promo':   applyPromo();   break;
    // Оплата
    case 'pay':      selectPayment(el.dataset.pay); break;
    // Карта
    case 'map-open': openMap(+el.dataset.loc); break;
  }
});

// ── Модификация корзины (ГЛАВНЫЙ ФИЧ) ────────────────────────────────────────
function modifyCart(itemId, delta) {
  const curr = S.cart[itemId] ?? 0;
  const next  = curr + delta;
  if (next <= 0) delete S.cart[itemId];
  else           S.cart[itemId] = next;
  haptic('light');
  // Перерисовываем только карточку + шапку
  renderCard(itemId);
  renderCartBadge();
  if (S.cartOpen)     renderCartList();
  if (S.checkoutOpen) renderCheckoutSummary();
}

// ── Таб-навигация ─────────────────────────────────────────────────────────────
function setTab(tab) {
  S.tab = tab;
  byQA('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  $('view-menu').style.display      = tab === 'menu'      ? ''     : 'none';
  $('view-locations').style.display = tab === 'locations' ? 'block': 'none';
}

// ── Фильтр категорий ──────────────────────────────────────────────────────────
function setCat(cat) {
  S.category = cat;
  byQA('.cat-btn').forEach(b => b.classList.toggle('active', b.dataset.cat === cat));
  renderGrid();
}

// ── Рендер меню ───────────────────────────────────────────────────────────────
function renderGrid() {
  const items = S.category === 'all'
    ? S.menu
    : S.menu.filter(m => m.cat === S.category);

  $('menu-grid').innerHTML = items.map(item => {
    const qty = S.cart[item.id] ?? 0;
    const img = item.image
      ? `<img class="card-img" src="${item.image}" alt="${item.name}" loading="lazy">`
      : `<div class="card-img emoji-img">${item.emoji}</div>`;
    const ctrl = qty === 0
      ? `<button class="add-btn" data-a="add" data-id="${item.id}">+</button>`
      : `<div class="counter">
           <button class="counter-btn" data-a="sub" data-id="${item.id}">−</button>
           <span class="counter-qty">${qty}</span>
           <button class="counter-btn" data-a="add" data-id="${item.id}">+</button>
         </div>`;
    return `
      <div class="menu-card" id="mcard-${item.id}">
        ${img}
        <div class="card-body">
          <div class="card-name">${item.name}</div>
          <div class="card-desc">${item.desc}</div>
          <div class="card-weight">${item.weight}</div>
          <div class="card-footer">
            <div class="card-price">${item.price} ₽</div>
            <div class="card-ctrl" id="ctrl-${item.id}">${ctrl}</div>
          </div>
        </div>
      </div>`;
  }).join('');
}

// Перерисовывает только зону управления одной карточки (без полного ре-рендера)
function renderCard(itemId) {
  const ctrl = $(`ctrl-${itemId}`);
  if (!ctrl) return;
  const qty = S.cart[itemId] ?? 0;
  ctrl.innerHTML = qty === 0
    ? `<button class="add-btn" data-a="add" data-id="${itemId}">+</button>`
    : `<div class="counter">
         <button class="counter-btn" data-a="sub" data-id="${itemId}">−</button>
         <span class="counter-qty">${qty}</span>
         <button class="counter-btn" data-a="add" data-id="${itemId}">+</button>
       </div>`;
}

// ── Корзина ───────────────────────────────────────────────────────────────────
function renderCartBadge() {
  const { qty } = calcTotals();
  const badge = $('cart-badge');
  badge.textContent = qty;
  badge.classList.toggle('visible', qty > 0);
}

function openCart() {
  S.cartOpen = true;
  renderCartList();
  $('cart-panel').classList.add('open');
  $('cart-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  haptic('medium');
}
function closeCart() {
  S.cartOpen = false;
  $('cart-panel').classList.remove('open');
  $('cart-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

function renderCartList() {
  const entries = Object.entries(S.cart).filter(([,q]) => q > 0);
  const { subtotal, discAmt, delivery, total } = calcTotals();
  const empty   = $('cart-empty');
  const footer  = $('cart-footer');
  const items   = $('cart-items');

  if (entries.length === 0) {
    empty.style.display  = 'block';
    footer.style.display = 'none';
    items.innerHTML = '';
    items.appendChild(empty);
    return;
  }
  empty.style.display  = 'none';
  footer.style.display = 'block';

  items.innerHTML = entries.map(([id, qty]) => {
    const item = getItem(id);
    if (!item) return '';
    return `
      <div class="cart-item">
        <div class="ci-emoji">${item.emoji}</div>
        <div class="ci-info">
          <div class="ci-name">${item.name}</div>
          <div class="ci-price">${item.price} ₽ × ${qty} = ${item.price * qty} ₽</div>
        </div>
        <div class="ci-controls">
          <button class="ci-btn" data-a="sub" data-id="${item.id}">−</button>
          <span class="ci-qty">${qty}</span>
          <button class="ci-btn" data-a="add" data-id="${item.id}">+</button>
        </div>
      </div>`;
  }).join('');

  $('s-subtotal').textContent  = subtotal + ' ₽';
  $('s-delivery').textContent  = delivery === 0 ? 'Бесплатно' : delivery + ' ₽';
  $('s-total').textContent     = total + ' ₽';
  const dr = $('discount-row');
  if (discAmt > 0) {
    dr.style.display = 'flex';
    $('s-discount').textContent = '−' + discAmt + ' ₽';
  } else {
    dr.style.display = 'none';
  }
}

// ── Промокод ──────────────────────────────────────────────────────────────────
function applyPromo() {
  const code = $('promo-input').value.trim().toUpperCase();
  if (PROMOS[code]) {
    S.discount  = PROMOS[code];
    S.promoCode = code;
    haptic('success');
    renderCartList();
    toast(`Скидка ${S.discount}% применена!`);
  } else {
    haptic('error');
    toast('Промокод не найден', true);
  }
}

// ── Checkout ──────────────────────────────────────────────────────────────────
function openCheckout() {
  const entries = Object.entries(S.cart).filter(([,q]) => q > 0);
  if (!entries.length) return;
  closeCart();
  S.checkoutOpen = true;
  renderCheckoutSummary();
  $('checkout-panel').classList.add('open');
  document.body.style.overflow = 'hidden';
  haptic('medium');
}
function backToCart() {
  $('checkout-panel').classList.remove('open');
  S.checkoutOpen = false;
  openCart();
}

function renderCheckoutSummary() {
  const entries = Object.entries(S.cart).filter(([,q]) => q > 0);
  const { subtotal, discAmt, delivery, total } = calcTotals();
  const starsAmt = Math.max(1, Math.round(total / 1.5));

  let html = entries.map(([id, qty]) => {
    const item = getItem(id); if (!item) return '';
    return `<div class="co-sum-row">
      <span class="co-sum-e">${item.emoji}</span>
      <span class="co-sum-n">${item.name}</span>
      <span class="co-sum-q">×${qty}</span>
      <span class="co-sum-p">${item.price * qty} ₽</span>
    </div>`;
  }).join('');

  if (discAmt > 0) html += `<div class="co-sum-row co-sum-disc">
    <span class="co-sum-e">🏷</span><span class="co-sum-n">Скидка ${S.discount}%</span>
    <span class="co-sum-q"></span><span class="co-sum-p">−${discAmt} ₽</span></div>`;
  html += `<div class="co-sum-row">
    <span class="co-sum-e">🚚</span><span class="co-sum-n">Доставка</span>
    <span class="co-sum-q"></span>
    <span class="co-sum-p">${delivery === 0 ? 'Бесплатно' : delivery + ' ₽'}</span></div>`;

  $('co-summary').innerHTML = html;
  $('co-total').textContent = total + ' ₽';
  $('stars-hint').textContent = `≈ ${starsAmt} ⭐`;
}

// Выбор оплаты
let selectedPayment = 'stars';
function selectPayment(pay) {
  selectedPayment = pay;
  byQA('.pay-opt').forEach(el => el.classList.toggle('sel', el.dataset.pay === pay));
  $('stars-hint-row').style.display = pay === 'stars' ? 'flex' : 'none';
}

// ── Отправка заказа ───────────────────────────────────────────────────────────
function submitOrder() {
  const street  = $('addr-street').value.trim();
  const apt     = $('addr-apt').value.trim();
  const comment = $('addr-comment').value.trim();
  if (!street) {
    haptic('error');
    $('addr-street').classList.add('input-err');
    $('addr-street').focus();
    toast('Укажите улицу и номер дома', true);
    return;
  }
  let address = street;
  if (apt)     address += `, кв./оф. ${apt}`;
  if (comment) address += ` (${comment})`;

  const entries   = Object.entries(S.cart).filter(([,q]) => q > 0);
  const orderData = entries.map(([id, qty]) => {
    const item = getItem(id);
    return { name: item.name, qty, price: item.price, emoji: item.emoji };
  });
  const { total } = calcTotals();

  const payload = JSON.stringify({
    items:   orderData,
    total,
    discount: S.discount,
    address,
    payment: selectedPayment,
  });

  haptic('success');

  if (tg) {
    tg.sendData(payload);
  } else {
    // Dev режим (браузер без Telegram)
    console.log('Order payload:', payload);
  }

  $('checkout-panel').classList.remove('open');
  document.body.style.overflow = '';
  S.checkoutOpen = false;

  const successText = selectedPayment === 'stars'
    ? 'Счёт для оплаты Stars отправлен в бот. После оплаты заказ поступит на кухню!'
    : selectedPayment === 'cash'
    ? 'Заказ принят! Оплата наличными при получении. Ожидайте ~40 минут 🍣'
    : 'Заказ принят! Оператор свяжется для подтверждения оплаты.';
  $('success-text').textContent = successText;
  $('success-screen').style.display = 'flex';
}

// ── Сброс ─────────────────────────────────────────────────────────────────────
function resetAll() {
  S.cart = {}; S.discount = 0; S.promoCode = '';
  ['promo-input','addr-street','addr-apt','addr-comment'].forEach(id => { const el=$(id); if(el) el.value=''; });
  $('success-screen').style.display = 'none';
  document.body.style.overflow = '';
  renderCartBadge();
  renderGrid();
}

// ── Раздел «Адреса» ───────────────────────────────────────────────────────────
function renderLocations() {
  $('view-locations').innerHTML = `
    <div class="loc-hero">
      <div class="loc-hero-text">
        <div class="loc-hero-title">🗺 Наши точки</div>
        <div class="loc-hero-sub">Самовывоз или доставка — выбирайте!</div>
      </div>
    </div>
    <div class="loc-list">
      ${LOCATIONS.map(loc => `
        <div class="loc-card">
          <div class="loc-card-head">
            <span class="loc-icon">${loc.emoji}</span>
            <div>
              <div class="loc-name">${loc.name}</div>
              <div class="loc-addr">📍 ${loc.address}</div>
            </div>
          </div>
          <div class="loc-meta">
            <div class="loc-meta-item">🕐 ${loc.hours}</div>
            <div class="loc-meta-item">📞 ${loc.phone}</div>
          </div>
          <div class="loc-actions">
            <button class="loc-btn loc-btn--map" data-a="map-open" data-loc="${loc.id}">
              🗺 Открыть на карте
            </button>
            <a class="loc-btn loc-btn--call" href="tel:${loc.phone.replace(/\D/g,'')}">
              📞 Позвонить
            </a>
          </div>
        </div>`).join('')}
    </div>
    <div class="loc-info-card">
      <div class="loc-info-title">🚚 Условия доставки</div>
      <div class="loc-info-row"><span>Зона доставки</span><span>до 10 км</span></div>
      <div class="loc-info-row"><span>Время</span><span>30–50 минут</span></div>
      <div class="loc-info-row"><span>Бесплатно от</span><span>1 500 ₽</span></div>
      <div class="loc-info-row"><span>Стоимость доставки</span><span>199 ₽</span></div>
      <div class="loc-info-row"><span>Минимальный заказ</span><span>500 ₽</span></div>
    </div>`;
}

function openMap(locId) {
  const loc = LOCATIONS.find(l => l.id === locId);
  if (!loc) return;
  const [lat, lng] = loc.coords;
  const url = `https://maps.google.com/maps?q=${lat},${lng}&z=16&t=m`;
  if (tg) tg.openLink(url);
  else window.open(url, '_blank');
}

// ── Тема Telegram ─────────────────────────────────────────────────────────────
function applyTheme() {
  if (!tg?.themeParams) return;
  const p = tg.themeParams;
  const r = document.documentElement;
  if (p.bg_color)           r.style.setProperty('--bg',   p.bg_color);
  if (p.text_color)         r.style.setProperty('--text', p.text_color);
  if (p.hint_color)         r.style.setProperty('--hint', p.hint_color);
  if (p.secondary_bg_color) r.style.setProperty('--bg2',  p.secondary_bg_color);
}
if (tg) tg.onEvent('themeChanged', applyTheme);

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
  applyTheme();
  // addr-street ошибка сбрасывается при вводе
  document.addEventListener('input', e => {
    if (e.target.id === 'addr-street') e.target.classList.remove('input-err');
  });
  await loadMenu();
  renderGrid();
  renderCartBadge();
  renderLocations();
  // Дефолтный выбор оплаты
  selectPayment('stars');
})();
