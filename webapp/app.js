// Frontend logic with i18n and auto-detect Telegram ID
const API = window.location.origin;

const TRANSLATIONS = {
  en: {
    title: 'UnderGroundZone',
    header: '✨ UnderGroundZone',
    user: '👤 Telegram ID:',
    tickets: '🎟️ Tickets:',
    refs: '📣 Referrals:',
    ebooks: '📚 Ebooks',
    ranking: '🏆 Ranking',
    adminPanel: '🔒 Admin Panel',
    buy: '✨ Buy',
    grantFree: '🎁 Grant free',
    refresh: 'Refresh 🔄',
    buyModalTitle: '🛒 Buy ebook',
    buyModalPrompt: 'Select payment mode:',
    paySim: 'Pay (simulation)',
    payReal: 'Pay (real)'
  },
  pl: {
    title: 'UnderGroundZone',
    header: '✨ UnderGroundZone',
    user: '👤 Telegram ID:',
    tickets: '🎟️ Bilety:',
    refs: '📣 Polecenia:',
    ebooks: '📚 Ebooki',
    ranking: '🏆 Ranking',
    adminPanel: '🔒 Panel Admina',
    buy: '✨ Kup',
    grantFree: '🎁 Przyznaj za darmo',
    refresh: 'Odśwież 🔄',
    buyModalTitle: '🛒 Kup ebook',
    buyModalPrompt: 'Wybierz sposób płatności:',
    paySim: 'Płatność (symulacja)',
    payReal: 'Płatność (na żywo)'
  }
};

function qs(id){return document.getElementById(id)}
function el(tag, cls){ const e = document.createElement(tag); if(cls) e.className = cls; return e }

function t(key){
  const lang = localStorage.getItem('ugz_lang') || 'en';
  return (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) || TRANSLATIONS['en'][key] || key;
}

function applyTranslations(){
  qs('site-title').textContent = t('title');
  qs('header-title').textContent = t('header');
  qs('label-user').textContent = t('user');
  qs('label-tickets').textContent = t('tickets');
  qs('label-refs').textContent = t('refs');
  qs('label-ebooks').textContent = t('ebooks');
  qs('label-ranking').textContent = t('ranking');
  qs('admin-title').textContent = t('adminPanel');
  qs('modal-title').textContent = t('buyModalTitle');
  qs('modal-prompt').textContent = t('buyModalPrompt');
  qs('modal-buy-sim').textContent = t('paySim');
  qs('modal-buy-real').textContent = t('payReal');
  qs('refresh').textContent = t('refresh');
}

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
        <button class="buy" data-id="${e.id}">${t('buy')}</button>
        ${isAdmin?`<button class="buy-free" data-id="${e.id}">${t('grantFree')}</button>`:''}
      </div>
    `;
    container.appendChild(card);
  });
  // listeners
  document.querySelectorAll('.buy').forEach(b=>b.addEventListener('click', async (evt)=>{
    const id = evt.currentTarget.dataset.id;
    openBuyModal(id, telegram_id);
  }));
  document.querySelectorAll('.buy-free').forEach(b=>b.addEventListener('click', async (evt)=>{
    const id = evt.currentTarget.dataset.id;
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
    if(j.order_token && j.payment_link){ window.open(j.payment_link, '_blank'); }
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
    const isAdmin = !!data.user.is_admin;
    await loadEbooks(telegram_id, isAdmin);
    await loadRanking();
    if(isAdmin){ qs('admin-panel').style.display='block'; loadAdminPanel(telegram_id); } else { qs('admin-panel').style.display='none'; }
  }
}

async function loadAdminPanel(telegram_id){
  const r = await fetch('/admin/users', { headers: { 'X-ADMIN-ID': telegram_id } });
  const j = await r.json();
  const list = qs('admin-users');
  list.innerHTML='';
  j.users.forEach(u=>{
    const row = document.createElement('div'); row.className='admin-user';
    row.innerHTML = `<strong>${u.telegram_id}</strong> — 🎟️ ${u.tickets} — 📚 ${u.ebooks_owned.length} — refs: ${u.referrals} <button data-id="${u.telegram_id}" class="grant">+10🎟[...]
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

// Detect Telegram ID automatically
function detectTelegramId(){
  try{
    const W = window.Telegram?.WebApp;
    if(W){
      console.log('✅ Telegram WebApp detected');
      const initUnsafe = W.initDataUnsafe;
      if(initUnsafe && initUnsafe.user && initUnsafe.user.id) {
        console.log('✅ Telegram ID found from initDataUnsafe:', initUnsafe.user.id);
        return String(initUnsafe.user.id);
      }
      const raw = W.initData;
      if(raw){
        try{
          const params = new URLSearchParams(raw);
          if(params.has('user')){
            try{ const u = JSON.parse(params.get('user')); if(u && u.id) return String(u.id); }catch(e){}
          }
          if(params.has('id')) return params.get('id');
        }catch(e){}
      }
    } else {
      console.warn('⚠️ Telegram WebApp not detected');
    }
  }catch(e){
    console.error('Error detecting Telegram:', e);
  }
  const url = new URL(window.location.href);
  return url.searchParams.get('telegram_id') || null;
}

// Language selector
function initLanguage(){
  const sel = qs('lang-select');
  const saved = localStorage.getItem('ugz_lang') || 'en';
  sel.value = saved;
  applyTranslations();
  sel.addEventListener('change', ()=>{
    localStorage.setItem('ugz_lang', sel.value);
    applyTranslations();
    // re-render ebooks (they use t() when rendering)
    const telegram_id = qs('telegram-id').textContent || null;
    if(telegram_id && telegram_id !== '-') refresh(telegram_id);
  });
}

window.addEventListener('load', async ()=>{
  console.log('🚀 Page loaded, initializing...');
  
  // Initialize Telegram WebApp
  if(window.Telegram?.WebApp){
    console.log('📱 Initializing Telegram WebApp...');
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();
  }
  
  initLanguage();
  let telegram_id = detectTelegramId();
  
  console.log('🔍 Detected telegram_id:', telegram_id);
  
  if(!telegram_id){
    console.error('❌ No telegram_id found');
    document.body.innerHTML = `<div style="padding:20px;font-family:sans-serif;">${t('header')}<br/><br/>Open this page from the Telegram bot (Web App) or add ?telegram_id=YOUR_ID to the URL for testing. Debug: Check console for details.`;
    return;
  }
  
  const initData = window.Telegram?.WebApp?.initData || null;
  try{ await fetch('/start',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({telegram_id, init_data: initData}) }); }catch(e){console.warn('start failed', e)}
  try{ const resp = await fetch('/_config'); if(resp.ok){ const cfg = await resp.json(); if(cfg.ADMIN_TELEGRAM_ID) qs('admin-id').value = String(cfg.ADMIN_TELEGRAM_ID); } }catch(e){console.warn('config failed', e)}
  
  applyTranslations();
  await refresh(telegram_id);
  qs('refresh').addEventListener('click', ()=>refresh(telegram_id));
  qs('modal-close').addEventListener('click', ()=>{ qs('modal').style.display='none'; });
});
