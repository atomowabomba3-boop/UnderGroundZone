// Frontend logic for UnderGroundZone
const API = window.location.origin;

function qs(id){return document.getElementById(id)}

async function loadEbooks(telegram_id){
  const res = await fetch('/ebooks');
  const data = await res.json();
  const container = qs('ebooks');
  container.innerHTML='';
  data.ebooks.forEach(e=>{
    const el = document.createElement('div'); el.className='ebook';
    el.innerHTML = `<h4>${e.title}</h4><p>Price: $${e.price_usd}</p><button data-id="${e.id}">Buy (simulate)</button>`;
    const btn = el.querySelector('button');
    btn.addEventListener('click', async ()=>{
      // Simulate payment webhook by calling /buy-ebook directly (for demo)
      const amount = e.price_usd;
      const body = { telegram_id, ebook_id: e.id, amount_usd: amount };
      const r = await fetch('/buy-ebook', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
      const j = await r.json();
      alert(JSON.stringify(j));
      refresh(telegram_id);
    });
    container.appendChild(el);
  })
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
  const res = await fetch(`/me?telegram_id=${telegram_id}`);
  if(res.status===200){
    const data = await res.json();
    qs('telegram-id').textContent = telegram_id;
    qs('tickets').textContent = data.user.tickets;
    qs('refs').textContent = data.user.referrals;
  }
  await loadEbooks(telegram_id);
  await loadRanking();
}

// Telegram Mini App detection - try initDataUnsafe or query param
function detectTelegramId(){
  try{
    if(window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initDataUnsafe){
      return window.Telegram.WebApp.initDataUnsafe.user.id;
    }
  }catch(e){}
  const url = new URL(window.location.href);
  return url.searchParams.get('telegram_id') || url.searchParams.get('id');
}

window.addEventListener('load', async ()=>{
  const tid = detectTelegramId();
  if(!tid){
    const manual = prompt('Podaj telegram_id do testów:');
    if(!manual) return;
    telegram_id = manual;
  } else {
    telegram_id = tid;
  }
  // call /start to register (idempotent)
  await fetch('/start',{ method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({telegram_id}) });
  await refresh(telegram_id);
  qs('refresh').addEventListener('click', ()=>refresh(telegram_id));
});
