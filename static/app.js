async function act(action) {
  try {
    const r = await fetch('/' + action, { method: 'POST' });
    const data = await r.json();
    if (data.ok) {
      document.getElementById('state').textContent = data.state;
      document.getElementById('state').className = 'badge ' + data.state;
    }
  } catch(e) { alert('خطأ: ' + e); }
}

async function loadData() {
  if (!confirm('سيتم تحميل الفتاوى من data.json (بدون تكرار)')) return;
  try {
    const r = await fetch('/load-data', { method: 'POST' });
    const data = await r.json();
    if (data.ok) alert('✅ أُضيفت ' + data.inserted + ' فتوى');
    else alert('❌ ' + data.error);
    location.reload();
  } catch(e) { alert('خطأ: ' + e); }
}

async function refresh() {
  try {
    const r = await fetch('/stats');
    const data = await r.json();
    const s = data.stats;
    const st = document.getElementById('state');
    if (st) {
      st.textContent = data.state;
      st.className = 'badge ' + data.state;
    }
    const nums = document.querySelectorAll('.stat-num');
    if (nums.length >= 4) {
      nums[0].textContent = s.total;
      nums[1].textContent = s.sent;
      nums[2].textContent = s.pending;
      nums[3].textContent = s.failed;
    }
    const pct = s.total ? Math.round((s.sent / s.total) * 100) : 0;
    const fill = document.getElementById('progress-fill');
    const txt = document.getElementById('progress-text');
    if (fill) fill.style.width = pct + '%';
    if (txt) txt.textContent = pct + '%';
  } catch(e) {}
}

if (document.getElementById('state')) {
  setInterval(refresh, 5000);
  refresh();
}