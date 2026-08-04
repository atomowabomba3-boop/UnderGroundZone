// Simple frontend client for UnderGroundZone with referral and webhook simulation
const API = "/";
function $q(sel){ return document.querySelector(sel); }

let telegram_id = null;

function getQueryParam(name) {
  const url = new URL(window.location.href);
  return url.searchParams.get(name);
}

async function api(path, opts){
  opts = opts || {};
  opts.headers = Object.assign({"Content-Type":"application/json"}, opts.headers||{});
  if(opts.body && typeof opts.body !== "string") opts.body = JSON.stringify(opts.body);
  const res = await fetch(API + path, opts);
  return res.json();
}

async function loadUser() {
  const tid = telegram_id || getQueryParam("telegram_id");
  if(!tid){
    document.getElementById("user-info").textContent = "Brak telegram_id. Otwórz przez Telegram Mini App lub dodaj ?telegram_id=...";
    return;
  }
  telegram_id = tid;
  document.getElementById("ref-link").value = `${location.origin}${location.pathname}?ref=${telegram_id}`;
  await api("start", {method:"POST", body:{telegram_id}});
  const me = await api(`me?telegram_id=${telegram_id}`);
  if(me.error){
    document.getElementById("user-info").textContent = "Błąd ładowania użytkownika";
    return;
  }
  const user = me.user;
  document.getElementById("user-info").textContent = `Zalogowany: ${telegram_id}`;
  document.getElementById("tickets").textContent = user.tickets;
  document.getElementById("refs").textContent = user.referrals;
  const owned = user.ebooks_owned || [];
  const ownedList = document.getElementById("ebooks-owned");
  ownedList.innerHTML = "";
  owned.forEach(e => { const li = document.createElement("li"); li.textContent = e; ownedList.appendChild(li); });
}

async function loadEbooks(){
  const res = await api("ebooks");
  const container = document.getElementById("ebooks-list");
  container.innerHTML = "";
  if(res.ok){
    res.ebooks.forEach(ebook=>{
      const d = document.createElement("div"); d.className="ebook";
      d.innerHTML = `
        <img src="/images/placeholder.png" alt="cover" />
        <h3>${ebook.title}</h3>
        <div>Price: $${ebook.price_usd} → ${ebook.tickets_awarded} tickets</div>
        <button data-id="${ebook.id}" data-price="${ebook.price_usd}">Buy (simulate)</button>
        <a href="/ebooks/${ebook.filename}" target="_blank">Pobierz (backend)</a>
      `;
      const btn = d.querySelector("button");
      btn.addEventListener("click", ()=> {
        const secret = prompt("Wpisz webhook secret do symulacji (leave blank to cancel)");
        if(!secret) return;
        const body = { telegram_id: telegram_id || prompt('telegram_id?'), ebook_id: ebook.id, amount_usd: ebook.price_usd };
        fetch('/buy-ebook', { method: 'POST', headers: { 'Content-Type':'application/json', 'X-WEBHOOK-SECRET': secret }, body: JSON.stringify(body) })
          .then(r=>r.json()).then(j=>{ alert(JSON.stringify(j)); loadUser(); });
      });
      container.appendChild(d);
    });
  }
}

async function loadRanking(){
  const res = await api("ranking");
  const ol = document.getElementById("ranking-list");
  ol.innerHTML = "";
  if(res.ok){
    res.ranking.forEach(r=>{
      const li = document.createElement("li");
      li.textContent = `${r.telegram_id} — ${r.referrals} refów`;
      ol.appendChild(li);
    });
  }
}

document.getElementById("refresh-ranking").addEventListener("click", loadRanking);

// referral send
document.getElementById("send-ref").addEventListener("click", async ()=>{
  const referrer = document.getElementById("referrer").value;
  const referred = document.getElementById("referred").value;
  if(!referrer || !referred){ alert('wypełnij pola'); return; }
  const res = await api('referral', { method:'POST', body:{ referrer_id: referrer, referred_id: referred } });
  alert(JSON.stringify(res));
  loadUser();
});

// simulation form
document.getElementById("send-sim").addEventListener("click", async ()=>{
  const secret = document.getElementById("webhook-secret").value;
  const tid = document.getElementById("sim-telegram-id").value;
  const ebook_id = document.getElementById("sim-ebook-id").value;
  const amount = document.getElementById("sim-amount").value;
  if(!tid || !ebook_id || !amount){ alert('Wypełnij wszystkie pola symulacji'); return; }
  const body = { telegram_id: tid, ebook_id: ebook_id, amount_usd: parseFloat(amount) };
  const headers = { 'Content-Type':'application/json' };
  if(secret) headers['X-WEBHOOK-SECRET'] = secret;
  const res = await fetch('/buy-ebook', { method:'POST', headers, body: JSON.stringify(body) });
  const j = await res.json();
  alert(JSON.stringify(j));
  loadUser();
});

// DEBUG / fallback for Telegram WebApp
function isTelegramWebApp(){
  try{
    return !!(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe);
  }catch(e){ return false; }
}

function showTelegramMissingBanner(){
  const container = document.createElement('div');
  container.style.background = '#ffefc8';
  container.style.color = '#000';
  container.style.padding = '8px';
  container.style.borderRadius = '6px';
  container.style.margin = '8px 0';
  container.style.fontSize = '14px';
  container.innerHTML = `
    <strong>Uwaga:</strong> Wygląda na to, że aplikacja nie została otwarta z poziomu Telegrama.<br/>
    Otwórz ją przez przycisk Web App wysłany przez bota w Telegramie, lub wpisz ręcznie telegram_id poniżej do testów.<br/>
    <input id="manual-tid" placeholder="telegram_id (np. 1001)" style="margin-top:6px;padding:6px;border-radius:6px;border:1px solid #ccc;" />
    <button id="apply-tid" style="margin-left:6px;padding:6px 8px;border-radius:6px;background:#ff6b6b;color:#fff;border:none;">Zastosuj</button>
  `;
  document.body.prepend(container);
  document.getElementById('apply-tid').addEventListener('click', ()=>{
    const val = document.getElementById('manual-tid').value.trim();
    if(val){
      telegram_id = val;
      loadUser();
    }
  });
}

async function sendDebugOpen(payload){
  try{
    await fetch('/debug-open', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    console.log('sent debug-open');
  }catch(e){
    console.warn('debug-open failed', e);
  }
}

(async function init(){
  try{ if(isTelegramWebApp()){
      const initData = window.Telegram.WebApp.initDataUnsafe || {};
      const u = initData.user; if(u && u.id) telegram_id = String(u.id);
      // send debug payload to server so we can inspect what Telegram actually sent
      sendDebugOpen({ initData });
    } else {
      showTelegramMissingBanner();
      const qtid = getQueryParam('telegram_id') || getQueryParam('ref') || null;
      if(qtid) telegram_id = qtid;
    }
  }catch(e){}
  await loadUser();
  await loadEbooks();
  await loadRanking();
})();
