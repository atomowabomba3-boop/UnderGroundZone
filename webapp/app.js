// Web App frontend: integrate with Telegram WebApp API when available
console.log('UnderGroundZone webapp loaded');

const envEl = document.getElementById('env');
const mainEl = document.querySelector('main');
let currentUser = null;

function showMessage(msg) {
  envEl.textContent = msg;
}

function createButton(text, onClick) {
  const btn = document.createElement('button');
  btn.textContent = text;
  btn.style.marginRight = '0.5rem';
  btn.addEventListener('click', onClick);
  return btn;
}

async function apiPost(path, body) {
  try {
    const res = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

async function apiGet(path) {
  try {
    const res = await fetch(path);
    return await res.json();
  } catch (e) {
    return { error: e.message };
  }
}

async function callStart(telegramId, referrer) {
  showMessage('Rejestruję użytkownika...');
  const body = { telegram_id: telegramId };
  if (referrer) body.referrer_telegram_id = referrer;
  const j = await apiPost('/start', body);
  if (j && j.status === 'success') {
    currentUser = j.user;
    renderUser();
    showMessage('Zarejestrowano: ' + (currentUser && currentUser.telegram_id));
  } else {
    showMessage('Błąd rejestracji: ' + (j && j.error ? j.error : JSON.stringify(j)));
  }
}

function renderUser() {
  // remove any existing user box
  const existing = document.getElementById('user-box');
  if (existing) existing.remove();

  const box = document.createElement('div');
  box.id = 'user-box';
  box.style.marginTop = '1rem';
  box.style.padding = '1rem';
  box.style.background = 'rgba(255,255,255,0.03)';
  box.style.borderRadius = '8px';

  const title = document.createElement('h2');
  title.textContent = 'Moje konto';
  title.style.marginTop = '0';
  box.appendChild(title);

  const info = document.createElement('div');
  info.innerHTML = `ID: ${currentUser.id} — Telegram: ${currentUser.telegram_id} — Tickets: ${currentUser.tickets}`;
  box.appendChild(info);

  // Buttons: Get referral link, Buy sample ebook, Join giveaway
  const btnRow = document.createElement('div');
  btnRow.style.marginTop = '0.75rem';

  const refBtn = createButton('Pobierz referral link', () => {
    if (currentUser && currentUser.referral_link) {
      navigator.clipboard && navigator.clipboard.writeText(currentUser.referral_link);
      showMessage('Skopiowano referral link do schowka');
    } else showMessage('Brak referral link');
  });

  const buyBtn = createButton('Kup ebook (symulacja $2)', async () => {
    if (!currentUser) return showMessage('Brak użytkownika');
    showMessage('Przetwarzanie zakupu...');
    const res = await apiPost('/buy-ebook', { telegram_id: currentUser.telegram_id, ebook_id: 1, amount_usd: 2 });
    if (res && res.status === 'success') {
      showMessage('Zakup udany');
      currentUser = res.user;
      renderUser();
    } else {
      showMessage('Błąd zakupu: ' + (res && res.error ? res.error : JSON.stringify(res)));
    }
  });

  const joinBtn = createButton('Dołącz do giveaway (wydaj wszystkie bilety)', async () => {
    if (!currentUser) return showMessage('Brak użytkownika');
    showMessage('Łączenie z giveaway...');
    const res = await apiPost('/giveaway/join', { telegram_id: currentUser.telegram_id });
    if (res && res.status === 'success') {
      showMessage('Dołączono do giveaway');
      currentUser = res.user;
      renderUser();
    } else {
      showMessage('Błąd dołączania: ' + (res && res.error ? res.error : JSON.stringify(res)));
    }
  });

  btnRow.appendChild(refBtn);
  btnRow.appendChild(buyBtn);
  btnRow.appendChild(joinBtn);
  box.appendChild(btnRow);

  mainEl.appendChild(box);
}

async function init() {
  // If inside Telegram WebApp, use initDataUnsafe to get user and start_param
  try {
    if (window.Telegram && window.Telegram.WebApp) {
      const webapp = window.Telegram.WebApp;
      const unsafe = webapp.initDataUnsafe || {};
      const user = unsafe.user;
      const startParam = unsafe.start_param || unsafe.start_param || undefined;
      if (user && user.id) {
        showMessage('Wykryto Telegram Web App. Logowanie...');
        await callStart(user.id, startParam);
        return;
      }
      // Not enough webapp data -> fall through to API check
    }
  } catch (e) {
    console.warn('Telegram WebApp init failed', e);
  }

  // Not in Telegram or no user info available — just check backend status
  showMessage('Sprawdzam backend...');
  const status = await apiGet('/me');
  if (status && status.status === 'success') {
    showMessage('API reachable — backend OK');
  } else if (status && status.error) {
    showMessage('Backend error: ' + status.error);
  } else {
    showMessage('Backend unreachable');
  }
}

init();
