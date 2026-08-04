// ==================== CONFIGURATION ====================
const API_BASE_URL = window.location.origin;
const API_ENDPOINTS = {
    START: '/start',
    ME: '/me',
    REFERRAL: '/referral',
    RANKING: '/ranking',
    EBOOKS: '/ebooks',
    BUY_EBOOK: '/buy-ebook',
    GIVEAWAY_STATUS: '/giveaway/status',
    GIVEAWAY_JOIN: '/giveaway/join',
    GIVEAWAY_END: '/giveaway/end',
    GIVEAWAY_HISTORY: '/giveaway/history'
};

// ==================== TELEGRAM INTEGRATION ====================
let telegramUserId = null;
let currentUser = null;

function initTelegramWebApp() {
    const tg = window.Telegram?.WebApp;
    
    if (tg) {
        tg.ready();
        tg.expand();
        
        // Get user from Telegram
        if (tg.initDataUnsafe?.user?.id) {
            telegramUserId = tg.initDataUnsafe.user.id;
            console.log('Telegram User ID:', telegramUserId);
        }
    } else {
        // For development/testing
        telegramUserId = 123456789;
        console.warn('Telegram WebApp not available, using test ID');
    }
    
    return telegramUserId;
}

// ==================== API CALLS ====================
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API Error');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function startUser() {
    try {
        const data = await apiCall(API_ENDPOINTS.START, 'POST', {
            telegram_id: telegramUserId
        });
        currentUser = data.user;
        updateUserDisplay();
        return data.user;
    } catch (error) {
        showToast('Failed to start app', 'error');
        return null;
    }
}

async function getUser() {
    try {
        const data = await apiCall(`${API_ENDPOINTS.ME}?telegram_id=${telegramUserId}`);
        currentUser = data.user;
        updateUserDisplay();
        return data.user;
    } catch (error) {
        console.error('Failed to get user:', error);
        return null;
    }
}

// ==================== UI UPDATES ====================
function updateUserDisplay() {
    if (!currentUser) return;
    
    // Update header
    const ticketsBadge = document.getElementById('user-tickets');
    if (ticketsBadge) {
        ticketsBadge.textContent = `🎫 ${currentUser.tickets}`;
    }
    
    // Update home tab
    document.getElementById('home-tickets').textContent = currentUser.tickets;
    document.getElementById('home-referrals').textContent = currentUser.referrals_count;
    document.getElementById('home-ebooks').textContent = currentUser.ebooks_owned.length;
    
    // Update referral tab
    document.getElementById('referral-count').textContent = currentUser.referrals_count;
    document.getElementById('referral-bonus').textContent = calculateReferralBonus(currentUser.referrals_count);
}

function calculateReferralBonus(refCount) {
    const bonuses = {
        5: 5, 10: 15, 25: 40, 50: 100, 100: 300
    };
    
    let totalBonus = 0;
    Object.entries(bonuses).forEach(([count, bonus]) => {
        if (refCount >= parseInt(count)) {
            totalBonus += bonus;
        }
    });
    
    return totalBonus;
}

async function loadEBooks() {
    try {
        showLoading(true);
        const data = await apiCall(API_ENDPOINTS.EBOOKS);
        const ebooksList = document.getElementById('ebooks-list');
        
        if (data.ebooks.length === 0) {
            ebooksList.innerHTML = '<div class="loading">No ebooks available</div>';
            return;
        }
        
        ebooksList.innerHTML = data.ebooks.map(ebook => `
            <div class="ebook-card">
                <div class="ebook-cover ${currentUser?.ebooks_owned.includes(ebook.id) ? 'owned' : ''}">
                    📕
                </div>
                <div class="ebook-info">
                    <div class="ebook-name">${ebook.name}</div>
                    <div class="ebook-price">$${ebook.price}</div>
                    <div class="ebook-tickets">🎫 ${ebook.tickets_reward}</div>
                    ${!currentUser?.ebooks_owned.includes(ebook.id) ? 
                        `<button class="btn-buy" onclick="buyEbook(${ebook.id})">Buy</button>` : 
                        `<button class="btn-buy" disabled>Owned ✓</button>`
                    }
                </div>
            </div>
        `).join('');
        
        showLoading(false);
    } catch (error) {
        showToast('Failed to load ebooks', 'error');
        showLoading(false);
    }
}

async function buyEbook(ebookId) {
    try {
        showLoading(true);
        // In production, this would be handled by the crypto bot webhook
        showToast('Redirect to payment...');
        showLoading(false);
    } catch (error) {
        showToast('Failed to buy ebook', 'error');
        showLoading(false);
    }
}

async function loadRanking() {
    try {
        showLoading(true);
        const data = await apiCall(API_ENDPOINTS.RANKING);
        const rankingList = document.getElementById('ranking-list');
        
        if (data.ranking.length === 0) {
            rankingList.innerHTML = '<div class="loading">No users yet</div>';
            return;
        }
        
        rankingList.innerHTML = data.ranking.map((user, index) => {
            let positionClass = '';
            if (index === 0) positionClass = 'gold';
            else if (index === 1) positionClass = 'silver';
            else if (index === 2) positionClass = 'bronze';
            
            return `
                <div class="ranking-item">
                    <div class="ranking-position ${positionClass}">${index + 1}</div>
                    <div class="ranking-info">
                        <div class="ranking-name">User ${user.telegram_id}</div>
                        <div class="ranking-refs">${user.referrals} referrals</div>
                    </div>
                    <div class="ranking-tickets">
                        <div class="ranking-tickets-value">${user.tickets}</div>
                        <div class="ranking-tickets-label">tickets</div>
                    </div>
                </div>
            `;
        }).join('');
        
        showLoading(false);
    } catch (error) {
        showToast('Failed to load ranking', 'error');
        showLoading(false);
    }
}

async function loadGiveawayStatus() {
    try {
        const data = await apiCall(API_ENDPOINTS.GIVEAWAY_STATUS);
        const giveawayContent = document.getElementById('giveaway-content');
        
        if (!data.giveaway) {
            giveawayContent.innerHTML = `
                <div class="giveaway-pool">
                    <div class="pool-label">No active giveaway</div>
                    <div class="pool-amount">$0.00</div>
                    <div class="pool-label">Waiting for $15 pool</div>
                </div>
                <button class="btn btn-primary" onclick="location.reload()">Refresh</button>
            `;
            return;
        }
        
        const giveaway = data.giveaway;
        giveawayContent.innerHTML = `
            <div class="giveaway-pool">
                <div class="pool-label">Prize Pool</div>
                <div class="pool-amount">$${giveaway.pool_amount.toFixed(2)}</div>
            </div>
            
            <div class="giveaway-status">
                🎁 Active Giveaway - ${giveaway.participants} participants
            </div>
            
            <div class="giveaway-stats">
                <div class="giveaway-stat">
                    <div class="giveaway-stat-label">Your Tickets</div>
                    <div class="giveaway-stat-value">${currentUser?.tickets || 0}</div>
                </div>
                <div class="giveaway-stat">
                    <div class="giveaway-stat-label">Participants</div>
                    <div class="giveaway-stat-value">${giveaway.participants}</div>
                </div>
            </div>
            
            <input type="number" id="tickets-input" min="1" max="${currentUser?.tickets || 0}" 
                   value="1" class="referral-input" placeholder="Tickets to spend">
            <button class="btn btn-primary" style="width: 100%; margin-top: 12px;" 
                    onclick="joinGiveaway(${giveaway.id})">Join Giveaway</button>
        `;
    } catch (error) {
        console.error('Failed to load giveaway status:', error);
    }
}

async function joinGiveaway(giveawayId) {
    try {
        const ticketsInput = document.getElementById('tickets-input');
        const tickets = parseInt(ticketsInput?.value || 1);
        
        if (tickets > currentUser.tickets) {
            showToast('Not enough tickets', 'error');
            return;
        }
        
        showLoading(true);
        await apiCall(API_ENDPOINTS.GIVEAWAY_JOIN, 'POST', {
            telegram_id: telegramUserId,
            tickets: tickets
        });
        
        showToast(`Successfully joined with ${tickets} tickets!`, 'success');
        await getUser();
        await loadGiveawayStatus();
        showLoading(false);
    } catch (error) {
        showToast('Failed to join giveaway', 'error');
        showLoading(false);
    }
}

// ==================== REFERRAL ====================
function copyReferralLink() {
    const link = document.getElementById('referral-link');
    link.select();
    document.execCommand('copy');
    showToast('Link copied!', 'success');
}

// ==================== NAVIGATION ====================
function setupNavigation() {
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    
    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            
            // Update active tab button
            navTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update active content
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Load tab data
            if (tabName === 'ebooks') {
                loadEBooks();
            } else if (tabName === 'ranking') {
                loadRanking();
            } else if (tabName === 'giveaway') {
                loadGiveawayStatus();
            }
        });
    });
    
    // Set first tab as active
    navTabs[0].classList.add('active');
}

// ==================== UTILITIES ====================
function showLoading(show = true) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize Telegram
    initTelegramWebApp();
    
    // Setup navigation
    setupNavigation();
    
    // Setup copy button
    document.getElementById('copy-referral-btn').addEventListener('click', copyReferralLink);
    
    // Load initial data
    showLoading(true);
    await startUser();
    await loadRanking();
    showLoading(false);
    
    // Refresh user data every 30 seconds
    setInterval(() => {
        getUser();
    }, 30000);
});

// Refresh on visibility change
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        getUser();
    }
});
