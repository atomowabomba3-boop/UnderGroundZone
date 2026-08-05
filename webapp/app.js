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
