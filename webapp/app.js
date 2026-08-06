// Minimal frontend for UnderGroundZone — placeholder only
console.log('UnderGroundZone webapp loaded');

// Try to show a helpful message fetched from backend
fetch('/me')
  .then(r => r.json())
  .then(j => {
    const el = document.getElementById('env');
    if (j && j.status === 'success') {
      el.textContent = 'API reachable — backend OK';
    } else {
      el.textContent = 'API reachable — but /me returned: ' + (j && j.error ? j.error : JSON.stringify(j));
    }
  }).catch(e => {
    const el = document.getElementById('env');
    el.textContent = 'Nie można połączyć się z backendem: ' + e.message;
  });
