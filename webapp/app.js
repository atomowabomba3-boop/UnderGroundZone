// Frontend logic for UnderGroundZone (updated: modal, admin panel, emojis)
const API = window.location.origin;

function qs(id){return document.getElementById(id)}

function el(tag, cls){ const e = document.createElement(tag); if(cls) e.className = cls; return e }

async function loadEbooks(telegram_id, isAdmin=false){
  const res = await fetch('/ebooks');
  const data = await res.json();
  const container = qs('ebooks');
  container.innerHTML='';
  data.ebooks.forEach(e=>{
    const card = el('div','ebook');
    card.innerHTML = `
      <img src="${e.image || '/images/sample1.jpg'}" alt="${e.title}"/>
      <h4>${e.title}</h4>
      <p>💲 ${e.price_usd} — 🎟️ ${priceToTickets(e.price_usd)} tickets</p>
      <div class="ebook-actions">
        <button class="buy" data-id="${e.id}">✨ Buy</button>
        ${isAdmin?'<button class="buy-free" data-id="'+e.id+'">🎁 Grant free</button>':''}
      </div>
    `;
    container.appendChild(card);
  });
  // attach listeners
  document.querySelectorAll('.buy').forEach(b=>b.addEventListener('click', async (evt)=>{
    const id = evt.currentTarget.dataset.id;
    openBuyModal(id, telegram_id);
  }));
  document.querySelectorAll('.buy-free').forEach(b=>b.addEventListener('click', async (evt)=>{
    const id = evt.currentTarget.dataset.id;
    // admin free award
    const r = await fetch('/admin/award-free', {method:'POST', headers:{'Content-Type':'application/json','X-ADMIN-ID':telegram_id}, body: JSON.stringify({telegram_id, ebook_id: id})});
    const j = await r.json();
    alert(JSON.stringify(j));
    refresh(telegram_id);
  }));
}

function priceToTickets(price){
  if(price==2) return 50;
  if(price==5) return 150;
  if(price==10) return 500;
  return Math.round(price*25);
}

// modal
function openBuyModal(ebook_id, telegram_id){
  const modal = qs('modal');
  modal.style.display='block';
  modal.dataset.eid = ebook_id;
  qs('modal-buy-sim').onclick = async ()=>{
    modal.style.display='none';
    const body = { telegram_id, ebook_id: parseInt(ebook_id), mode: 'simulate' };
    const r = await fetch('/checkout', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
    const j = await r.json();
    alert(JSON.stringify(j));
    refresh(telegram_id);
  };
  qs('modal-buy-real').onclick = async ()=>{
    modal.style.display='none';
    const body = { telegram_id, ebook_id: parseInt(ebook_id), mode: 'real' };
    const r = await fetch('/checkout', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
    const j = await r.json();
    if(j.order_token && j.payment_link){
      // open payment link (stub)
      window.open(j.payment_link, '_blank');
    }
    alert(JSON.stringify(j));
    refresh(telegram_id);
  };
}

async function loadRanking(){
  const res = await fetch('/ranking');
  const data = await res.json();
  const ol = qs('ranking');
  ol.innerHTML='';
  data.ranking.forEach(u=>{
    const li = document.createElement('li');
    li.textContent = `${u.telegram_id} — refs: ${u.referrals} — tickets: ${u.tickets}`;
    ol.appendChild(li);
  })
}

async function refresh(telegram_id){
  if(!telegram_id) return;
  const res = await fetch(`/me?telegram_id=${encodeURIComponent(telegram_id)}`);
  if(res.status===200){
    const data = await res.json();
    qs('telegram-id').textContent = telegram_id;
    qs('tickets').textContent = data.user.tickets;
    qs('refs').textContent = data.user.referrals;
    const isAdmin = (String(telegram_id) === (qs('admin-id')?.value || '')) || false;
    await loadEbooks(telegram_id, isAdmin);
    await loadRanking();
    // show admin panel if admin
    if(String(telegram_id) === qs('admin-id').value){
      qs('admin-panel').style.display='block';
      loadAdminPanel(telegram_id);
    } else {
      qs('admin-panel').style.display='none';
    }
  }
}

async function loadAdminPanel(telegram_id){
  const r = await fetch('/admin/users', { headers: { 'X-ADMIN-ID': telegram_id } });
  const j = await r.json();
  const list = qs('admin-users');
  list.innerHTML='';
  j.users.forEach(u=>{
    const row = document.createElement('div'); row.className='admin-user';
    row.innerHTML = `<strong>${u.telegram_id}</strong> — 🎟️ ${u.tickets} — 📚 ${u.ebooks_owned.length} — refs: ${u.referrals} <button data-id="${u.telegram_id}" class="grant">+10🎟️</button>`;
    list.appendChild(row);
  });
  document.querySelectorAll('.grant').forEach(btn=>btn.addEventListener('click', async (e)=>{
    const tid = e.currentTarget.dataset.id;
    const rr = await fetch('/admin/grant-tickets', { method:'POST', headers:{'Content-Type':'application/json','X-ADMIN-ID':telegram_id}, body: JSON.stringify({telegram_id: tid, amount: 10}) });
    alert(JSON.stringify(await rr.json()));
    loadAdminPanel(telegram_id);
    refresh(telegram_id);
  }));
}

// Telegram Web App detection - handle safely and avoid throwing when opened outside Telegram
function detectTelegramId(){
  try{
    if(window.Telegram && window.Telegram.WebApp){
      try{
        // when opened inside Telegram WebApp, initDataUnsafe should be available
        const init = window.Telegram.WebApp.initDataUnsafe;
        if(init && init.user && init.user.id) return String(init.user.id);
        // sometimes only user object available via initData
        if(window.Telegram.WebApp?.initData) return null;
      }catch(e){
        console.warn('Telegram WebApp exists but could not read initDataUnsafe', e);
      }
    }
  }catch(e){/* ignore */}
  // fallback to URL param
  const url = new URL(window.location.href);
  return url.searchParams.get('telegram_id') || url.searchParams.get('id');
}

window.addEventListener('load', async ()=>{
  let telegram_id = detectTelegramId();
  if(!telegram_id){
    const manual = prompt('Enter your telegram_id for testing:');
    if(!manual) return;
    telegram_id = manual;
  }
  // call /start to register (idempotent)
  try{ await fetch('/start',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({telegram_id}) }); }catch(e){console.warn('start failed', e)}
  // store admin id field from server-side env (injected by template)
  try{ const resp = await fetch('/_config'); if(resp.ok){ const cfg = await resp.json(); if(cfg.ADMIN_TELEGRAM_ID) qs('admin-id').value = String(cfg.ADMIN_TELEGRAM_ID); } }catch(e){console.warn('config fetch failed', e)}
  await refresh(telegram_id);
  qs('refresh').addEventListener('click', ()=>refresh(telegram_id));
  // modal close
  qs('modal-close').addEventListener('click', ()=>{ qs('modal').style.display='none'; });
});
