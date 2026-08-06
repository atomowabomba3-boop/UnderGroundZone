// Minimal frontend helpers: API base, apiCall, loading/toast, current user loader
const API_BASE_URL = window.__API_BASE__ || '';
const FRONTEND_ADMIN_TELEGRAM_ID = 8998575936; // matches backend constant

async function apiCall(path, method='GET', body=null) {
  const url = (path.startsWith('http') ? path : `${API_BASE_URL}${path}`);
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body != null) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  if (!res.ok) {
    let err;
    try { err = await res.json(); } catch(e) { err = { error: res.statusText }; }
    throw err;
  }
  try { return await res.json(); } catch(e) { return null; }
}

function showToast(msg, type='info') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = `toast show ${type}`;
  setTimeout(()=>{ el.classList.remove('show'); }, 3000);
}
function showLoading(on=true) {
  const l = document.getElementById('loading-overlay');
  if (l) l.style.display = on ? 'flex' : 'none';
}

let currentUser = null;

async function getUser() {
  try {
    const res = await apiCall('/me');
    if (res && res.user) {
      currentUser = res.user;
      const t = document.getElementById('user-tickets');
      if (t) t.textContent = `🎫 ${currentUser.tickets || 0}`;
      // update home stats
      const ht = document.getElementById('home-tickets'); if(ht) ht.textContent = currentUser.tickets || 0;
      const hr = document.getElementById('home-referrals'); if(hr) hr.textContent = currentUser.referrals_count || 0;
      const he = document.getElementById('home-ebooks'); if(he) he.textContent = (currentUser.ebooks_owned || []).length || 0;

      // show admin tab if user is admin (backend may not include is_admin)
      if (currentUser.is_admin || Number(currentUser.telegram_id) === FRONTEND_ADMIN_TELEGRAM_ID) {
        const a = document.getElementById('nav-admin-tab');
        if (a) a.style.display = '';
      }

      // referral link
      try { setupReferralLink(); } catch(e) { console.debug('referral setup failed', e); }

      // load other content
      if (typeof loadGiveawayStatus === 'function') loadGiveawayStatus();
      if (typeof loadEbooks === 'function') loadEbooks();
      if (typeof loadRanking === 'function') loadRanking();
      if (typeof checkPayoutForUser === 'function') checkPayoutForUser();
    }
  } catch (err) {
    console.warn('getUser failed', err);
  }

  // ensure public tabs still load when not logged in
  try {
    if (typeof loadGiveawayStatus === 'function') loadGiveawayStatus();
    if (typeof loadEbooks === 'function') loadEbooks();
    if (typeof loadRanking === 'function') loadRanking();
  } catch(e) { console.debug('initial content load failed', e); }
}

document.addEventListener('DOMContentLoaded', () => {
  // kick off initial data load
  getUser().catch(()=>{});
});

// Payout & admin helpers
async function checkPayoutForUser(){
  if(!currentUser) return;
  try{
    const res = await apiCall('/giveaway/payout');
    if(res && res.payout){
      const sel = document.getElementById('payout-currency'); sel.innerHTML='';
      (res.currencies||[]).forEach(c=>{ const o=document.createElement('option'); o.value=c; o.textContent=c; sel.appendChild(o); });
      const addrEl = document.getElementById('payout-address'); if (addrEl) addrEl.value = res.payout.address || '';
      showPayoutModal();
    }
  }catch(e){
    console.debug('No payout or fetch error', e);
  }
}
function showPayoutModal(){ const el = document.getElementById('payout-modal'); if(el) el.style.display='flex'; }
function closePayoutModal(){ const el = document.getElementById('payout-modal'); if(el) el.style.display='none'; }

async function confirmPayout(){
  const currency = document.getElementById('payout-currency').value;
  const address = (document.getElementById('payout-address').value || '').trim();
  const msg = document.getElementById('payout-msg');
  if(!address){ if(msg) msg.textContent='Wpisz adres'; return; }
  try{
    const res = await apiCall('/giveaway/payout/confirm','POST',{currency,address});
    if(res && res.status==='success'){ if(msg) msg.textContent='Potwierdzono'; setTimeout(()=>closePayoutModal(),900); await getUser(); await loadGiveawayStatus(); }
    else if(msg) msg.textContent = (res && res.error) || 'Błąd';
  }catch(e){ if(msg) msg.textContent='Błąd sieci'; }
}

// Robust admin add tickets
async function adminAddTickets(){
  try{
    showLoading(true);
    const payload = { admin_telegram_id: FRONTEND_ADMIN_TELEGRAM_ID, target_telegram_id: FRONTEND_ADMIN_TELEGRAM_ID, amount: 1 };
    const options = { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Admin-Telegram': String(FRONTEND_ADMIN_TELEGRAM_ID) }, body: JSON.stringify(payload) };
    const resp = await fetch(`${API_BASE_URL}/admin/add-tickets`, options);
    const data = await resp.json();
    if(!resp.ok){ console.error('Admin add-tickets failed', data); showToast(data.error || data.message || 'Failed to add ticket','error'); return; }
    showToast(data.message || 'Added','success');
    await getUser();
  }catch(e){ console.error('adminAddTickets error', e); showToast('Failed to add ticket','error'); }finally{ showLoading(false); }
}

// --- TAB SWITCHING: add missing navigation handlers ---
(function setupTabs(){
  try {
    const tabs = Array.from(document.querySelectorAll('.nav-tab'));
    const contents = Array.from(document.querySelectorAll('.tab-content'));

    function showTab(tabName){
      tabs.forEach(t => t.classList.remove('active'));
      contents.forEach(c => c.classList.remove('active'));

      const btn = tabs.find(t => t.dataset && t.dataset.tab === tabName);
      if(btn) btn.classList.add('active');

      const section = document.getElementById(`${tabName}-tab`);
      if(section) section.classList.add('active');
    }

    tabs.forEach(t => {
      t.addEventListener('click', (e) => {
        const name = t.dataset && t.dataset.tab;
        if(name) {
          showTab(name);
        }
      });
    });

    const params = new URLSearchParams(window.location.search);
    const initial = params.get('tab') || (tabs[0] && tabs[0].dataset.tab) || 'home';
    showTab(initial);
  } catch (err) {
    console.error('setupTabs error', err);
  }
})();

// ==================== CONTENT LOADERS ====================
// Load eBooks from API and render
async function loadEbooks(){
  const el = document.getElementById('ebooks-list');
  if(!el) return;
  el.innerHTML = '<div class="loading">Loading eBooks...</div>';
  try{
    const res = await apiCall('/ebooks');
    if(!res || !res.ebooks) { el.innerHTML = '<div class="loading">No eBooks found</div>'; return; }
    const books = res.ebooks;
    if(books.length === 0){ el.innerHTML = '<div class="loading">No eBooks available</div>'; return; }
    el.innerHTML = '';
    books.forEach(b => {
      const card = document.createElement('div'); card.className = 'ebook-card';
      const cover = document.createElement('div'); cover.className = 'ebook-cover';
      if(b.cover_image){
        const img = document.createElement('img'); img.src = b.cover_image; img.alt = b.name; img.style.width='100%'; img.style.borderRadius='8px'; cover.appendChild(img);
      } else { cover.textContent = '📘'; }
      const title = document.createElement('div'); title.className = 'ebook-title'; title.textContent = b.name || 'Untitled';
      const price = document.createElement('div'); price.className = 'ebook-price'; price.textContent = `$${b.price || '0.00'}`;
      const tickets = document.createElement('div'); tickets.className = 'ebook-tickets'; tickets.textContent = `${b.tickets_reward || 0} tickets`;
      const btn = document.createElement('a'); btn.className = 'btn-buy'; btn.textContent = 'Download';
      btn.href = b.file_path ? `${API_BASE_URL}/download/${encodeURIComponent(b.file_path)}` : '#';
      btn.target = '_blank';
      card.appendChild(cover); card.appendChild(title); card.appendChild(price); card.appendChild(tickets); card.appendChild(btn);
      el.appendChild(card);
    });
  }catch(e){ console.error('loadEbooks error', e); el.innerHTML = '<div class="loading">Failed to load eBooks</div>'; }
}

// Setup referral link copy and values
function setupReferralLink(){
  const input = document.getElementById('referral-link');
  const btn = document.getElementById('copy-referral-btn');
  if(!input || !btn) return;
  // prefer backend-provided referral_link
  let link = (currentUser && currentUser.referral_link) || input.value || '';
  // normalize: if link contains '/?ref=' or 'ref:' keep it; otherwise just use as-is
  input.value = link;
  btn.addEventListener('click', async () => {
    try{
      await navigator.clipboard.writeText(input.value);
      showToast('Referral link copied');
    }catch(e){
      console.error('Clipboard copy failed', e);
      // fallback select
      input.select(); document.execCommand('copy'); showToast('Referral link copied (fallback)');
    }
  });
}

// Load giveaway status
async function loadGiveawayStatus(){
  const el = document.getElementById('giveaway-content');
  if(!el) return;
  el.innerHTML = '<div class="loading">Loading giveaway status...</div>';
  try{
    const res = await apiCall('/giveaway/status');
    if(!res || !res.giveaway){ el.innerHTML = '<div class="loading">No active giveaway</div>'; return; }
    const g = res.giveaway;
    // render basic info
    el.innerHTML = '';
    const pool = document.createElement('div'); pool.className = 'giveaway-pool'; pool.innerHTML = `<h3>Pool: $${g.pool_amount || 0}</h3>`;
    const status = document.createElement('div'); status.className='giveaway-status'; status.textContent = `Status: ${g.status || 'unknown'}`;
    const ends = document.createElement('div'); ends.className='giveaway-ends'; ends.textContent = `Ends at: ${g.ends_at || 'N/A'}`;
    el.appendChild(pool); el.appendChild(status); el.appendChild(ends);
  }catch(e){ console.error('loadGiveawayStatus error', e); el.innerHTML = '<div class="loading">Failed to load giveaway</div>'; }
}

// Load ranking
async function loadRanking(){
  const el = document.getElementById('ranking-list');
  if(!el) return;
  el.innerHTML = '<div class="loading">Loading ranking...</div>';
  try{
    const res = await apiCall('/ranking');
    if(!res || !res.ranking || res.ranking.length === 0){ el.innerHTML = '<div class="loading">No ranking data</div>'; return; }
    el.innerHTML = '';
    res.ranking.forEach(r => {
      const row = document.createElement('div'); row.className = 'ranking-row';
      row.innerHTML = `<div class="rank-pos">${r.position}</div><div class="rank-id">${r.telegram_id}</div><div class="rank-ref">${r.referrals} refs</div><div class="rank-tickets">${r.tickets} tix</div>`;
      el.appendChild(row);
    });
  }catch(e){ console.error('loadRanking error', e); el.innerHTML = '<div class="loading">Failed to load ranking</div>'; }
}
