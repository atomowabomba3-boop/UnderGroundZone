// Minimal frontend helpers: API base, apiCall, loading/toast, current user loader
const API_BASE_URL = window.__API_BASE__ || '';

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
      // show admin tab if user is admin
      if (currentUser.is_admin) {
        const a = document.getElementById('nav-admin-tab');
        if (a) a.style.display = '';
      }
      if (typeof loadGiveawayStatus === 'function') loadGiveawayStatus();
      if (typeof loadEbooks === 'function') loadEbooks();
      if (typeof checkPayoutForUser === 'function') checkPayoutForUser();
    }
  } catch (err) {
    console.warn('getUser failed', err);
  }
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
    const payload = { admin_telegram_id: ADMIN_TELEGRAM_ID, target_telegram_id: ADMIN_TELEGRAM_ID, amount: 1 };
    const options = { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Admin-Telegram': String(ADMIN_TELEGRAM_ID) }, body: JSON.stringify(payload) };
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
