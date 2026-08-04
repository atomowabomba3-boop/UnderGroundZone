const API_BASE = '';

let currentUserId = null;

// Initialize Telegram WebApp
if (window.Telegram?.WebApp) {
    console.log('✅ Telegram WebApp detected');
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();
}

// Get Telegram ID
function getTelegramId() {
    try {
        const W = window.Telegram?.WebApp;
        if (W?.initDataUnsafe?.user?.id) {
            console.log('✅ Telegram ID:', W.initDataUnsafe.user.id);
            return W.initDataUnsafe.user.id;
        }
    } catch(e) {
        console.warn('Could not get Telegram ID:', e);
    }
    
    // Fallback: from URL params
    const params = new URLSearchParams(window.location.search);
    return params.get('telegram_id') || null;
}

async function startApp() {
    const telegramId = getTelegramId();
    
    if (!telegramId) {
        document.body.innerHTML = '<div style="padding:20px;text-align:center;">⚠️ Open this from Telegram bot!<br/>Or add ?telegram_id=YOUR_ID to URL</div>';
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/api/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ telegram_id: telegramId })
        });
        
        const user = await res.json();
        console.log('✅ User registered/fetched:', user);
        
        currentUserId = telegramId;
        updateUI(user);
        loadRanking();
        
        // Setup event listeners
        document.getElementById('ref-btn').addEventListener('click', handleAddReferral);
        document.getElementById('refresh-btn').addEventListener('click', () => refreshUser());
        
    } catch(err) {
        console.error('Error starting app:', err);
        document.body.innerHTML += '<p style="color:red;">Error: ' + err + '</p>';
    }
}

function updateUI(user) {
    document.getElementById('user-id').textContent = user.telegram_id;
    document.getElementById('user-tickets').textContent = user.tickets;
    document.getElementById('user-refs').textContent = user.referrals;
}

async function handleAddReferral() {
    const refInput = document.getElementById('ref-input');
    const referredId = refInput.value.trim();
    const refMsg = document.getElementById('ref-msg');
    
    if (!referredId) {
        refMsg.textContent = '❌ Enter a Telegram ID';
        refMsg.className = 'error';
        return;
    }
    
    try {
        await fetch(`${API_BASE}/api/referral`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                referrer_id: currentUserId,
                referred_id: referredId
            })
        });
        
        refMsg.textContent = '✅ Referral added! +5 tickets';
        refMsg.className = 'success';
        refInput.value = '';
        
        await refreshUser();
        await loadRanking();
        
    } catch(err) {
        refMsg.textContent = '❌ Error: ' + err;
        refMsg.className = 'error';
    }
}

async function refreshUser() {
    try {
        const res = await fetch(`${API_BASE}/api/user/${currentUserId}`);
        const user = await res.json();
        updateUI(user);
        console.log('✅ User refreshed');
    } catch(err) {
        console.error('Error refreshing user:', err);
    }
}

async function loadRanking() {
    try {
        const res = await fetch(`${API_BASE}/api/ranking`);
        const data = await res.json();
        
        const rankingList = document.getElementById('ranking-list');
        rankingList.innerHTML = '';
        
        data.ranking.forEach(user => {
            const li = document.createElement('li');
            li.textContent = `#${user.rank} ${user.telegram_id} — 📣 ${user.referrals} — 🎟️ ${user.tickets}`;
            rankingList.appendChild(li);
        });
        
    } catch(err) {
        console.error('Error loading ranking:', err);
    }
}

// Start on load
window.addEventListener('load', startApp);
