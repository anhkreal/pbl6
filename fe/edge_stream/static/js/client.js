const statusEl = document.getElementById('status');
setInterval(async () => {
  try {
    const r = await fetch('/stats');
    const j = await r.json();
    statusEl.textContent = `Last: ${j.staffName||'Unknown'} ${j.emotion||''}`;
  } catch(e){ statusEl.textContent = 'No stats'; }
}, 2000);
