// ─── Telegram SDK ─────────────────────────────────────
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  tg.enableClosingConfirmation();
}

// ─── MENU DATA ─────────────────────────────────────────
const MENU = [
  // РОЛЛЫ
  { id: 1, cat: 'rolls', name: 'Филадельфия классик', desc: 'Лосось, сливочный сыр, авокадо', weight: '280 г · 8 шт', price: 690, emoji: '🍣' },
  { id: 2, cat: 'rolls', name: 'Калифорния', desc: 'Краб, авокадо, огурец, икра тобико', weight: '260 г · 8 шт', price: 620, emoji: '🦀' },
  { id: 3, cat: 'rolls', name: 'Дракон', desc: 'Угорь, авокадо, огурец, соус унаги', weight: '300 г · 8 шт', price: 750, emoji: '🐉' },
  { id: 4, cat: 'rolls', name: 'Спайси тунец', desc: 'Тунец, спайси соус, огурец', weight: '250 г · 8 шт', price: 680, emoji: '🌶️' },
  { id: 5, cat: 'rolls', name: 'Радуга', desc: 'Микс рыбы, авокадо, огурец', weight: '320 г · 8 шт', price: 790, emoji: '🌈' },
  { id: 6, cat: 'rolls', name: 'Запечённый лосось', desc: 'Лосось, сыр, японский майонез', weight: '280 г · 8 шт', price: 710, emoji: '🔥' },
  { id: 7, cat: 'rolls', name: 'Эби темпура', desc: 'Тигровая креветка в темпуре, авокадо', weight: '290 г · 8 шт', price: 720, emoji: '🍤' },
  { id: 8, cat: 'rolls', name: 'Сицилия', desc: 'Тунец, вяленые томаты, базилик', weight: '260 г · 8 шт', price: 700, emoji: '🍅' },

  // НИГИРИ
  { id: 9,  cat: 'nigiri', name: 'Нигири лосось', desc: 'Рис, свежий лосось', weight: '80 г · 2 шт', price: 290, emoji: '🐟' },
  { id: 10, cat: 'nigiri', name: 'Нигири тунец', desc: 'Рис, тунец', weight: '80 г · 2 шт', price: 310, emoji: '🐠' },
  { id: 11, cat: 'nigiri', name: 'Нигири угорь', desc: 'Рис, угорь, соус унаги', weight: '90 г · 2 шт', price: 340, emoji: '🐍' },
  { id: 12, cat: 'nigiri', name: 'Нигири креветка', desc: 'Рис, тигровая креветка', weight: '80 г · 2 шт', price: 270, emoji: '🦐' },

  // САШИМИ
  { id: 13, cat: 'sashimi', name: 'Сашими лосось', desc: 'Свежий лосось, ломтики', weight: '150 г · 5 шт', price: 490, emoji: '🐡' },
  { id: 14, cat: 'sashimi', name: 'Сашими тунец', desc: 'Тунец, нарезка', weight: '150 г · 5 шт', price: 520, emoji: '🎣' },
  { id: 15, cat: 'sashimi', name: 'Сашими ассорти', desc: 'Лосось, тунец, гребешок', weight: '220 г · 9 шт', price: 890, emoji: '🍱' },

  // СЕТЫ
  { id: 16, cat: 'sets', name: 'Сет «Старт»', desc: 'Филадельфия, Калифорния (2×8 шт)', weight: '540 г · 16 шт', price: 1190, emoji: '🎁' },
  { id: 17, cat: 'sets', name: 'Сет «Семейный»', desc: '4 вида роллов на выбор (4×8 шт)', weight: '1100 г · 32 шт', price: 2390, emoji: '👨‍👩‍👧‍👦' },
  { id: 18, cat: 'sets', name: 'Сет «Мясоед»', desc: 'Угорь, Дракон, Спайси тунец', weight: '840 г · 24 шт', price: 1990, emoji: '🥩' },

  // НАПИТКИ
  { id: 19, cat: 'drinks', name: 'Мисо суп', desc: 'Тофу, вакамэ, зелёный лук', weight: '250 мл', price: 190, emoji: '🍵' },
  { id: 20, cat: 'drinks', name: 'Зелёный чай', desc: 'Японский сенча, горячий', weight: '400 мл', price: 150, emoji: '🍃' },
  { id: 21, cat: 'drinks', name: 'Лимонад матча', desc: 'Матча, лайм, мята, содовая', weight: '400 мл', price: 220, emoji: '💚' },
  { id: 22, cat: 'drinks', name: 'Саке', desc: 'Рисовое вино, 14%, горячее', weight: '100 мл', price: 280, emoji: '🍶' },
];

const PROMOS = {
  'SUSHI10': 10,
  'ROLL20': 20,
  'WELCOME15': 15,
};

// ─── STATE ─────────────────────────────────────────────
let cart = {};         // { id: qty }
let currentCat = 'all';
let discount = 0;
let cartOpen = false;

// ─── RENDER MENU ───────────────────────────────────────
function renderMenu() {
  const grid = document.getElementById('menu-grid');
  const items = currentCat === 'all'
    ? MENU
    : MENU.filter(i => i.cat === currentCat);

  grid.innerHTML = items.map(item => {
    const qty = cart[item.id] || 0;
    const controls = qty === 0
      ? `<button class="add-btn" onclick="addToCart(${item.id})">+</button>`
      : `<div class="counter">
           <button class="counter-btn" onclick="removeFromCart(${item.id})">−</button>
           <span class="counter-qty">${qty}</span>
           <button class="counter-btn" onclick="addToCart(${item.id})">+</button>
         </div>`;

    return `
      <div class="menu-card" id="card-${item.id}">
        <div class="card-img emoji-img">${item.emoji}</div>
        <div class="card-body">
          <div class="card-name">${item.name}</div>
          <div class="card-desc">${item.desc}</div>
          <div class="card-weight">${item.weight}</div>
          <div class="card-footer">
            <div class="card-price">${item.price} ₽</div>
            ${controls}
          </div>
        </div>
      </div>`;
  }).join('');
}

// ─── RENDER CART ────────────────────────────────────────
function renderCart() {
  const cartItems = document.getElementById('cart-items');
  const cartEmpty = document.getElementById('cart-empty');
  const cartFooter = document.getElementById('cart-footer');

  const entries = Object.entries(cart).filter(([, qty]) => qty > 0);

  if (entries.length === 0) {
    cartEmpty.style.display = 'block';
    cartFooter.style.display = 'none';
    cartItems.innerHTML = '';
    cartItems.appendChild(cartEmpty);
    updateCartBadge(0);
    return;
  }

  cartEmpty.style.display = 'none';
  cartFooter.style.display = 'block';

  let html = '';
  let subtotal = 0;
  let totalQty = 0;

  entries.forEach(([idStr, qty]) => {
    const id = Number(idStr);
    const item = MENU.find(m => m.id === id);
    const lineTotal = item.price * qty;
    subtotal += lineTotal;
    totalQty += qty;

    html += `
      <div class="cart-item">
        <div class="ci-emoji">${item.emoji}</div>
        <div class="ci-info">
          <div class="ci-name">${item.name}</div>
          <div class="ci-price">${item.price} ₽ × ${qty} = ${lineTotal} ₽</div>
        </div>
        <div class="ci-controls">
          <button class="ci-btn remove" onclick="removeFromCart(${id}); renderCart();">−</button>
          <span class="ci-qty">${qty}</span>
          <button class="ci-btn" onclick="addToCart(${id}); renderCart();">+</button>
        </div>
      </div>`;
  });

  cartItems.innerHTML = html;

  const discountAmt = Math.round(subtotal * discount / 100);
  const delivery = subtotal >= 1500 ? 0 : 199;
  const total = subtotal - discountAmt + delivery;

  document.getElementById('subtotal').textContent = subtotal + ' ₽';
  document.getElementById('delivery-cost').textContent = delivery === 0 ? 'Бесплатно' : delivery + ' ₽';
  document.getElementById('total-price').textContent = total + ' ₽';

  const discountRow = document.getElementById('discount-row');
  if (discountAmt > 0) {
    discountRow.style.display = 'flex';
    document.getElementById('discount-val').textContent = '−' + discountAmt + ' ₽';
  } else {
    discountRow.style.display = 'none';
  }

  updateCartBadge(totalQty);
}

// ─── CART ACTIONS ───────────────────────────────────────
function addToCart(id) {
  cart[id] = (cart[id] || 0) + 1;
  haptic('light');
  updateCardControls(id);
  renderCart();
}

function removeFromCart(id) {
  if (!cart[id]) return;
  cart[id]--;
  if (cart[id] === 0) delete cart[id];
  haptic('light');
  updateCardControls(id);
  renderCart();
}

function updateCardControls(id) {
  const card = document.getElementById('card-' + id);
  if (!card) return;
  const footer = card.querySelector('.card-footer');
  const item = MENU.find(m => m.id === id);
  const qty = cart[id] || 0;
  const footerContent = `
    <div class="card-price">${item.price} ₽</div>
    ${qty === 0
      ? `<button class="add-btn" onclick="addToCart(${id})">+</button>`
      : `<div class="counter">
           <button class="counter-btn" onclick="removeFromCart(${id})">−</button>
           <span class="counter-qty">${qty}</span>
           <button class="counter-btn" onclick="addToCart(${id})">+</button>
         </div>`}`;
  footer.innerHTML = footerContent;
}

function updateCartBadge(qty) {
  const badge = document.getElementById('cart-badge');
  badge.textContent = qty;
  badge.classList.toggle('visible', qty > 0);
}

// ─── TOGGLE CART ────────────────────────────────────────
function toggleCart() {
  cartOpen = !cartOpen;
  document.getElementById('cart-panel').classList.toggle('open', cartOpen);
  document.getElementById('cart-overlay').classList.toggle('open', cartOpen);
  document.body.style.overflow = cartOpen ? 'hidden' : '';

  if (cartOpen) {
    haptic('medium');
    renderCart();
  }
}

// ─── FILTER CATEGORY ────────────────────────────────────
function filterCategory(cat, btn) {
  currentCat = cat;
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderMenu();
}

// ─── PROMO ──────────────────────────────────────────────
function applyPromo() {
  const code = document.getElementById('promo-input').value.trim().toUpperCase();
  if (PROMOS[code]) {
    discount = PROMOS[code];
    haptic('success');
    renderCart();
    alert(`Промокод применён! Скидка ${discount}%`);
  } else {
    haptic('error');
    alert('Промокод не найден');
  }
}

// ─── ORDER ──────────────────────────────────────────────
function placeOrder() {
  const entries = Object.entries(cart).filter(([, q]) => q > 0);
  if (entries.length === 0) return;

  haptic('success');

  const orderData = entries.map(([idStr, qty]) => {
    const item = MENU.find(m => m.id === Number(idStr));
    return { name: item.name, qty, price: item.price };
  });

  const subtotal = orderData.reduce((s, i) => s + i.price * i.qty, 0);
  const discountAmt = Math.round(subtotal * discount / 100);
  const delivery = subtotal >= 1500 ? 0 : 199;
  const total = subtotal - discountAmt + delivery;

  const payload = JSON.stringify({ items: orderData, total, discount });

  if (tg) {
    tg.sendData(payload);
  }

  // Закрыть корзину и показать успех
  document.getElementById('cart-panel').classList.remove('open');
  document.getElementById('cart-overlay').classList.remove('open');
  document.getElementById('success-screen').style.display = 'flex';
}

function resetOrder() {
  cart = {};
  discount = 0;
  document.getElementById('promo-input').value = '';
  document.getElementById('success-screen').style.display = 'none';
  document.body.style.overflow = '';
  cartOpen = false;
  renderMenu();
  renderCart();
}

// ─── HAPTIC ─────────────────────────────────────────────
function haptic(type) {
  if (!tg?.HapticFeedback) return;
  if (type === 'light')   tg.HapticFeedback.impactOccurred('light');
  if (type === 'medium')  tg.HapticFeedback.impactOccurred('medium');
  if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
  if (type === 'error')   tg.HapticFeedback.notificationOccurred('error');
}

// ─── THEME ──────────────────────────────────────────────
if (tg) {
  tg.onEvent('themeChanged', () => {
    document.body.style.setProperty('--bg', tg.themeParams.bg_color || '#0f0f0f');
    document.body.style.setProperty('--text', tg.themeParams.text_color || '#ffffff');
    document.body.style.setProperty('--hint', tg.themeParams.hint_color || '#888888');
    document.body.style.setProperty('--bg2', tg.themeParams.secondary_bg_color || '#1a1a1a');
  });
}

// ─── INIT ───────────────────────────────────────────────
renderMenu();
renderCart();
