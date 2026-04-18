// ─── Telegram SDK ─────────────────────────────────────────────────────────────
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  tg.enableClosingConfirmation();
}

// ─── MENU DATA ────────────────────────────────────────────────────────────────
const MENU = [
  // РОЛЛЫ
  { id: 1,  cat: 'rolls',   name: 'Филадельфия классик',  desc: 'Лосось, сливочный сыр, авокадо',          weight: '280 г · 8 шт', price: 690,  emoji: '🍣' },
  { id: 2,  cat: 'rolls',   name: 'Калифорния',            desc: 'Краб, авокадо, огурец, икра тобико',      weight: '260 г · 8 шт', price: 620,  emoji: '🦀' },
  { id: 3,  cat: 'rolls',   name: 'Дракон',                desc: 'Угорь, авокадо, огурец, соус унаги',      weight: '300 г · 8 шт', price: 750,  emoji: '🐉' },
  { id: 4,  cat: 'rolls',   name: 'Спайси тунец',          desc: 'Тунец, спайси соус, огурец',              weight: '250 г · 8 шт', price: 680,  emoji: '🌶️' },
  { id: 5,  cat: 'rolls',   name: 'Радуга',                desc: 'Микс рыбы, авокадо, огурец',              weight: '320 г · 8 шт', price: 790,  emoji: '🌈' },
  { id: 6,  cat: 'rolls',   name: 'Запечённый лосось',     desc: 'Лосось, сыр, японский майонез',           weight: '280 г · 8 шт', price: 710,  emoji: '🔥' },
  { id: 7,  cat: 'rolls',   name: 'Эби темпура',           desc: 'Тигровая креветка в темпуре, авокадо',    weight: '290 г · 8 шт', price: 720,  emoji: '🍤' },
  { id: 8,  cat: 'rolls',   name: 'Сицилия',               desc: 'Тунец, вяленые томаты, базилик',          weight: '260 г · 8 шт', price: 700,  emoji: '🍅' },
  // НИГИРИ
  { id: 9,  cat: 'nigiri',  name: 'Нигири лосось',         desc: 'Рис, свежий лосось',                      weight: '80 г · 2 шт',  price: 290,  emoji: '🐟' },
  { id: 10, cat: 'nigiri',  name: 'Нигири тунец',          desc: 'Рис, тунец',                              weight: '80 г · 2 шт',  price: 310,  emoji: '🐠' },
  { id: 11, cat: 'nigiri',  name: 'Нигири угорь',          desc: 'Рис, угорь, соус унаги',                  weight: '90 г · 2 шт',  price: 340,  emoji: '🐍' },
  { id: 12, cat: 'nigiri',  name: 'Нигири креветка',       desc: 'Рис, тигровая креветка',                  weight: '80 г · 2 шт',  price: 270,  emoji: '🦐' },
  // САШИМИ
  { id: 13, cat: 'sashimi', name: 'Сашими лосось',         desc: 'Свежий лосось, ломтики',                  weight: '150 г · 5 шт', price: 490,  emoji: '🐡' },
  { id: 14, cat: 'sashimi', name: 'Сашими тунец',          desc: 'Тунец, нарезка',                          weight: '150 г · 5 шт', price: 520,  emoji: '🎣' },
  { id: 15, cat: 'sashimi', name: 'Сашими ассорти',        desc: 'Лосось, тунец, гребешок',                 weight: '220 г · 9 шт', price: 890,  emoji: '🍱' },
  // СЕТЫ
  { id: 16, cat: 'sets',    name: 'Сет «Старт»',           desc: 'Филадельфия, Калифорния (2×8 шт)',         weight: '540 г · 16 шт',price: 1190, emoji: '🎁' },
  { id: 17, cat: 'sets',    name: 'Сет «Семейный»',        desc: '4 вида роллов на выбор (4×8 шт)',          weight: '1100 г · 32 шт',price: 2390,emoji: '👨‍👩‍👧‍👦' },
  { id: 18, cat: 'sets',    name: 'Сет «Мясоед»',          desc: 'Угорь, Дракон, Спайси тунец',             weight: '840 г · 24 шт',price: 1990, emoji: '🥩' },
  // НАПИТКИ
  { id: 19, cat: 'drinks',  name: 'Мисо суп',              desc: 'Тофу, вакамэ, зелёный лук',               weight: '250 мл',       price: 190,  emoji: '🍵' },
  { id: 20, cat: 'drinks',  name: 'Зелёный чай',           desc: 'Японский сенча, горячий',                  weight: '400 мл',       price: 150,  emoji: '🍃' },
  { id: 21, cat: 'drinks',  name: 'Лимонад матча',         desc: 'Матча, лайм, мята, содовая',               weight: '400 мл',       price: 220,  emoji: '💚' },
  { id: 22, cat: 'drinks',  name: 'Саке',                  desc: 'Рисовое вино, 14%, горячее',               weight: '100 мл',       price: 280,  emoji: '🍶' },
];

const PROMOS = { 'SUSHI10': 10, 'ROLL20': 20, 'WELCOME15': 15 };

// ─── STATE ────────────────────────────────────────────────────────────────────
let cart       = {};
let currentCat = 'all';
let discount   = 0;
let cartOpen   = false;

// ─── HELPERS ──────────────────────────────────────────────────────────────────
function calcTotals() {
  const entries  = Object.entries(cart).filter(([, q]) => q > 0);
  const subtotal = entries.reduce((s, [id, q]) => {
    const item = MENU.find(m => m.id === Number(id));
    return s + item.price * q;
  }, 0);
  const discountAmt = Math.round(subtotal * discount / 100);
  const delivery    = subtotal >= 1500 ? 0 : 199;
  const total       = subtotal - discountAmt + delivery;
  return { subtotal, discountAmt, delivery, total };
}

// ─── RENDER MENU ──────────────────────────────────────────────────────────────
function renderMenu() {
  const grid  = document.getElementById('menu-grid');
  const items = currentCat === 'all' ? MENU : MENU.filter(i => i.cat === currentCat);

  grid.innerHTML = items.map(item => {
    const qty      = cart[item.id] || 0;
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

// ─── RENDER CART ──────────────────────────────────────────────────────────────
function renderCart() {
  const cartItems = document.getElementById('cart-items');
  const cartEmpty = document.getElementById('cart-empty');
  const cartFooter = document.getElementById('cart-footer');
  const entries   = Object.entries(cart).filter(([, q]) => q > 0);

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
  let totalQty = 0;
  entries.forEach(([idStr, qty]) => {
    const id   = Number(idStr);
    const item = MENU.find(m => m.id === id);
    totalQty  += qty;
    html += `
      <div class="cart-item">
        <div class="ci-emoji">${item.emoji}</div>
        <div class="ci-info">
          <div class="ci-name">${item.name}</div>
          <div class="ci-price">${item.price} ₽ × ${qty} = ${item.price * qty} ₽</div>
        </div>
        <div class="ci-controls">
          <button class="ci-btn remove" onclick="removeFromCart(${id}); renderCart();">−</button>
          <span class="ci-qty">${qty}</span>
          <button class="ci-btn" onclick="addToCart(${id}); renderCart();">+</button>
        </div>
      </div>`;
  });
  cartItems.innerHTML = html;

  const { subtotal, discountAmt, delivery, total } = calcTotals();
  document.getElementById('subtotal').textContent      = subtotal + ' ₽';
  document.getElementById('delivery-cost').textContent = delivery === 0 ? 'Бесплатно' : delivery + ' ₽';
  document.getElementById('total-price').textContent   = total + ' ₽';

  const discountRow = document.getElementById('discount-row');
  if (discountAmt > 0) {
    discountRow.style.display = 'flex';
    document.getElementById('discount-val').textContent = '−' + discountAmt + ' ₽';
  } else {
    discountRow.style.display = 'none';
  }
  updateCartBadge(totalQty);
}

// ─── CART ACTIONS ─────────────────────────────────────────────────────────────
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
  const item   = MENU.find(m => m.id === id);
  const qty    = cart[id] || 0;
  footer.innerHTML = `
    <div class="card-price">${item.price} ₽</div>
    ${qty === 0
      ? `<button class="add-btn" onclick="addToCart(${id})">+</button>`
      : `<div class="counter">
           <button class="counter-btn" onclick="removeFromCart(${id})">−</button>
           <span class="counter-qty">${qty}</span>
           <button class="counter-btn" onclick="addToCart(${id})">+</button>
         </div>`}`;
}

function updateCartBadge(qty) {
  const badge = document.getElementById('cart-badge');
  badge.textContent = qty;
  badge.classList.toggle('visible', qty > 0);
}

// ─── TOGGLE CART ──────────────────────────────────────────────────────────────
function toggleCart() {
  cartOpen = !cartOpen;
  document.getElementById('cart-panel').classList.toggle('open', cartOpen);
  document.getElementById('cart-overlay').classList.toggle('open', cartOpen);
  document.body.style.overflow = cartOpen ? 'hidden' : '';
  if (cartOpen) { haptic('medium'); renderCart(); }
}

// ─── FILTER CATEGORY ──────────────────────────────────────────────────────────
function filterCategory(cat, btn) {
  currentCat = cat;
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderMenu();
}

// ─── PROMO ────────────────────────────────────────────────────────────────────
function applyPromo() {
  const code = document.getElementById('promo-input').value.trim().toUpperCase();
  if (PROMOS[code]) {
    discount = PROMOS[code];
    haptic('success');
    renderCart();
    showToast(`Промокод применён! Скидка ${discount}%`);
  } else {
    haptic('error');
    showToast('Промокод не найден', true);
  }
}

// ─── CHECKOUT OPEN/CLOSE ──────────────────────────────────────────────────────
function openCheckout() {
  if (Object.keys(cart).length === 0) return;
  // Закрываем корзину
  cartOpen = false;
  document.getElementById('cart-panel').classList.remove('open');
  document.getElementById('cart-overlay').classList.remove('open');

  renderCheckoutSummary();

  document.getElementById('checkout-panel').classList.add('open');
  document.body.style.overflow = 'hidden';
  haptic('medium');
}

function closeCheckout() {
  document.getElementById('checkout-panel').classList.remove('open');
  document.body.style.overflow = '';
  // Возвращаем корзину
  cartOpen = true;
  document.getElementById('cart-panel').classList.add('open');
  document.getElementById('cart-overlay').classList.add('open');
  renderCart();
}

function renderCheckoutSummary() {
  const entries = Object.entries(cart).filter(([, q]) => q > 0);
  const { subtotal, discountAmt, delivery, total } = calcTotals();

  let html = entries.map(([id, qty]) => {
    const item = MENU.find(m => m.id === Number(id));
    return `
      <div class="co-sum-row">
        <div class="co-sum-emoji">${item.emoji}</div>
        <div class="co-sum-name">${item.name}</div>
        <div class="co-sum-qty">×${qty}</div>
        <div class="co-sum-price">${item.price * qty} ₽</div>
      </div>`;
  }).join('');

  if (discountAmt > 0) {
    html += `<div class="co-sum-row co-sum-row--discount">
      <div class="co-sum-emoji">🏷</div>
      <div class="co-sum-name">Скидка ${discount}%</div>
      <div class="co-sum-qty"></div>
      <div class="co-sum-price">−${discountAmt} ₽</div>
    </div>`;
  }
  html += `<div class="co-sum-row">
    <div class="co-sum-emoji">🚚</div>
    <div class="co-sum-name">Доставка</div>
    <div class="co-sum-qty"></div>
    <div class="co-sum-price">${delivery === 0 ? 'Бесплатно' : delivery + ' ₽'}</div>
  </div>`;

  document.getElementById('checkout-order-summary').innerHTML = html;
  document.getElementById('checkout-total').textContent = total + ' ₽';

  // Stars amount hint
  const starsAmt = Math.max(1, Math.round(total / 1.5));
  document.getElementById('stars-hint').textContent = `≈ ${starsAmt} ⭐`;
}

// ─── SUBMIT ORDER ─────────────────────────────────────────────────────────────
function submitOrder() {
  const street  = document.getElementById('address-street').value.trim();
  const apt     = document.getElementById('address-apt').value.trim();
  const comment = document.getElementById('address-comment').value.trim();

  if (!street) {
    haptic('error');
    document.getElementById('address-street').classList.add('input-error');
    document.getElementById('address-street').focus();
    showToast('Пожалуйста, укажите улицу и номер дома', true);
    return;
  }

  let address = street;
  if (apt)     address += `, кв./оф. ${apt}`;
  if (comment) address += ` (${comment})`;

  const selectedPayment = document.querySelector('input[name="payment"]:checked')?.value || 'cash';

  const entries   = Object.entries(cart).filter(([, q]) => q > 0);
  const orderData = entries.map(([idStr, qty]) => {
    const item = MENU.find(m => m.id === Number(idStr));
    return { name: item.name, qty, price: item.price, emoji: item.emoji };
  });

  const { total } = calcTotals();

  const payload = JSON.stringify({
    items:   orderData,
    total,
    discount,
    address,
    payment: selectedPayment,
  });

  haptic('success');

  if (tg) {
    tg.sendData(payload);
  }

  // Закрываем всё и показываем экран успеха
  document.getElementById('checkout-panel').classList.remove('open');
  document.body.style.overflow = '';
  document.getElementById('success-screen').style.display = 'flex';

  // Текст успеха зависит от метода оплаты
  const successText = document.getElementById('success-text');
  if (selectedPayment === 'stars') {
    successText.textContent = 'Счёт для оплаты Stars отправлен в чат бота. После оплаты заказ сразу поступит на кухню!';
  } else if (selectedPayment === 'cash') {
    successText.textContent = 'Ваш заказ уже готовится. Оплата наличными при получении. Ожидайте ~40 минут!';
  } else {
    successText.textContent = 'Заказ принят! Оператор свяжется с вами для подтверждения оплаты.';
  }
}

// ─── RESET ────────────────────────────────────────────────────────────────────
function resetOrder() {
  cart     = {};
  discount = 0;
  ['promo-input','address-street','address-apt','address-comment']
    .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  document.getElementById('success-screen').style.display = 'none';
  document.body.style.overflow = '';
  cartOpen = false;
  renderMenu();
  renderCart();
}

// ─── PAYMENT OPTION SELECTION ─────────────────────────────────────────────────
function initPaymentOptions() {
  document.querySelectorAll('.pay-item').forEach(item => {
    item.addEventListener('click', () => {
      const radio = item.querySelector('input[type="radio"]');
      if (!radio || radio.disabled) return;
      document.querySelectorAll('.pay-item').forEach(i => i.classList.remove('selected'));
      item.classList.add('selected');
      radio.checked = true;
      // Показываем/скрываем подсказку Stars
      const starsHintRow = document.getElementById('stars-hint-row');
      if (starsHintRow) {
        starsHintRow.style.display = radio.value === 'stars' ? 'flex' : 'none';
      }
    });
  });
  // Установить начальный стиль
  const checked = document.querySelector('.pay-item input:checked');
  if (checked) checked.closest('.pay-item').classList.add('selected');
}

// ─── TOAST NOTIFICATION ───────────────────────────────────────────────────────
function showToast(msg, isError = false) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.className   = 'toast' + (isError ? ' toast--error' : '');
  toast.classList.add('toast--visible');
  setTimeout(() => toast.classList.remove('toast--visible'), 2500);
}

// ─── HAPTIC ───────────────────────────────────────────────────────────────────
function haptic(type) {
  if (!tg?.HapticFeedback) return;
  if (type === 'light')   tg.HapticFeedback.impactOccurred('light');
  if (type === 'medium')  tg.HapticFeedback.impactOccurred('medium');
  if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
  if (type === 'error')   tg.HapticFeedback.notificationOccurred('error');
}

// ─── THEME ────────────────────────────────────────────────────────────────────
if (tg) {
  tg.onEvent('themeChanged', () => {
    document.body.style.setProperty('--bg',   tg.themeParams.bg_color           || '#0f0f0f');
    document.body.style.setProperty('--text', tg.themeParams.text_color         || '#ffffff');
    document.body.style.setProperty('--hint', tg.themeParams.hint_color         || '#888888');
    document.body.style.setProperty('--bg2',  tg.themeParams.secondary_bg_color || '#1a1a1a');
  });
}

// ─── ADDRESS INPUT: снять ошибку при вводе ────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const street = document.getElementById('address-street');
  if (street) {
    street.addEventListener('input', () => street.classList.remove('input-error'));
  }
});

// ─── INIT ─────────────────────────────────────────────────────────────────────
renderMenu();
renderCart();
initPaymentOptions();
