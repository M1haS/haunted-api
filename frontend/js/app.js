/* ─────────────────────────────────────────────────
   HAUNTED — Paranormal Registry UI
   app.js — all client-side logic
───────────────────────────────────────────────── */

const API = 'http://localhost:8000';

/* ── State ── */
const scores = { kinetic: 0, visual: 0, thermal: 0, electronic: 0 };

/* ── Clock ── */
function tick() {
  document.getElementById('sidebar-clock').textContent =
    new Date().toLocaleTimeString('en-GB');
}
tick();
setInterval(tick, 1000);

/* ── API helper ── */
async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
  return data;
}

/* ── Toast ── */
function toast(msg, type = 'ok') {
  const dock = document.getElementById('toast-dock');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  dock.appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

/* ── Tab navigation ── */
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-section').forEach(s => s.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${tab}`).classList.add('active');
    if (tab === 'events') loadEvents();
    if (tab === 'locations') loadLocations();
  });
});

/* ── Score sliders ── */
function updateScore(axis, val) {
  scores[axis] = parseFloat(val);
  document.getElementById(`val-${axis}`).textContent = parseFloat(val).toFixed(2);
  // Update preview bar
  const prevId = axis === 'kinetic' ? 'prev-kinetic'
    : axis === 'visual' ? 'prev-visual'
    : axis === 'thermal' ? 'prev-thermal'
    : 'prev-electronic';
  document.getElementById(prevId).style.setProperty('--w', `${Math.round(parseFloat(val) * 100)}%`);
  // Tint value text
  const valEl = document.getElementById(`val-${axis}`);
  const v = parseFloat(val);
  valEl.style.color = v >= 0.7 ? '#c0392b' : v >= 0.4 ? '#e67e22' : '';
}

/* ── Summary stats ── */
async function loadSummary() {
  try {
    const d = await apiFetch('/stats/summary');
    document.getElementById('st-loc').textContent  = d.total_locations  ?? 0;
    document.getElementById('st-ev').textContent   = d.total_events     ?? 0;
    document.getElementById('st-ver').textContent  = d.verified_events  ?? 0;
    document.getElementById('st-ext').textContent  = d.extreme_threat_locations ?? 0;
    document.getElementById('status-dot').className  = 'status-indicator online';
    document.getElementById('status-text').textContent = 'Connected';
  } catch {
    document.getElementById('status-dot').className  = 'status-indicator offline';
    document.getElementById('status-text').textContent = 'API offline';
  }
}

/* ── Recent events (overview) ── */
async function loadRecentEvents() {
  const body = document.getElementById('recent-events-body');
  try {
    const events = await apiFetch('/events?limit=5');
    if (!events.length) {
      body.innerHTML = '<div class="empty-state">No incidents on file.</div>';
      return;
    }
    body.innerHTML = events.map(e => `
      <div class="recent-event-item">
        <span class="event-id">#${e.id}</span>
        <div>
          <div class="rev-title">${escHtml(e.title)}</div>
          <div class="rev-meta">${badgeHtml(e.classification)} · ${e.moon_phase ?? '—'}</div>
        </div>
        <span class="verified-tag ${e.verified ? 'yes' : 'no'}">${e.verified ? 'verified' : 'pending'}</span>
      </div>`).join('');
  } catch (err) {
    body.innerHTML = `<div class="empty-state" style="color:var(--red);">${err.message}</div>`;
  }
}

/* ── Submit event ── */
async function submitEvent() {
  const btn = document.getElementById('ev-submit-btn');
  const locId   = parseInt(document.getElementById('ev-locid').value) || 1;
  const title   = document.getElementById('ev-title').value.trim() || 'Unnamed incident';
  const desc    = document.getElementById('ev-desc').value.trim() || null;
  const dateVal = document.getElementById('ev-date').value;
  const witnesses = parseInt(document.getElementById('ev-witnesses').value) || 0;

  const payload = {
    location_id: locId,
    title,
    description: desc,
    occurred_at: dateVal || new Date().toISOString().slice(0, 16),
    witness_count: witnesses,
    kinetic_score: scores.kinetic,
    visual_score: scores.visual,
    thermal_score: scores.thermal,
    electronic_score: scores.electronic,
    evidence: [],
  };

  btn.disabled = true;
  btn.querySelector('.btn-text').textContent = 'FILING…';

  try {
    const ev  = await apiFetch('/events', { method: 'POST', body: JSON.stringify(payload) });
    const clf = await apiFetch(`/events/${ev.id}/classify`);
    toast(`Event #${ev.id} filed — ${clf.classification.toUpperCase()}`, 'ok');

    showClassificationResult(ev, clf);
    loadSummary();
  } catch (err) {
    toast(`Error: ${err.message}`, 'err');
  } finally {
    btn.disabled = false;
    btn.querySelector('.btn-text').textContent = 'FILE REPORT';
  }
}

function showClassificationResult(ev, clf) {
  const panel = document.getElementById('clf-result');
  const threatLevel = clf.threat_level?.toUpperCase() ?? 'LOW';
  const lvlMap = { BENIGN: 1, LOW: 2, MODERATE: 3, HIGH: 4, EXTREME: 5 };
  const lvl = lvlMap[threatLevel] ?? 1;
  const skulls = Array.from({ length: 5 }, (_, i) =>
    `<span class="skull ${i < lvl ? 'lit' : ''}">☠</span>`).join('');

  panel.style.display = 'block';
  panel.innerHTML = `
    <div class="clf-header">Classification result — Event #${ev.id} · ${ev.moon_phase}</div>
    <div class="clf-class">${clf.classification.toUpperCase()}</div>
    <div class="clf-skulls">${skulls}</div>
    <div class="clf-details">
      <div class="clf-detail-row">
        <strong>Threat level:</strong> ${clf.threat_level}<br>
        <strong>Confidence:</strong> ${(clf.confidence * 100).toFixed(1)}%<br>
        <strong>Dominant axis:</strong> ${clf.dominant_axis}
      </div>
      <div class="clf-detail-row">${escHtml(clf.reasoning)}</div>
    </div>`;
}

/* ── Load events ── */
async function loadEvents() {
  const container = document.getElementById('events-container');
  container.innerHTML = `<div class="loading-state"><span class="spinner"></span> Loading dossiers…</div>`;
  try {
    const events = await apiFetch('/events?limit=50');
    if (!events.length) {
      container.innerHTML = '<div class="empty-state">No incidents on file.</div>';
      return;
    }
    const rows = events.map(e => `
      <tr>
        <td class="event-id">#${e.id}</td>
        <td class="event-title">${escHtml(e.title)}</td>
        <td>${badgeHtml(e.classification)}</td>
        <td class="moon-pill">${e.moon_phase ?? '—'}</td>
        <td style="text-align:center;">${e.witness_count}</td>
        <td><span class="verified-tag ${e.verified ? 'yes' : 'no'}">${e.verified ? 'verified' : 'pending'}</span></td>
        <td style="font-size:0.7rem;color:var(--text-dim);">${fmtDate(e.occurred_at)}</td>
        <td>${!e.verified
          ? `<button class="btn-small" onclick="verifyEvent(${e.id},this)">Verify</button>`
          : ''}</td>
      </tr>`).join('');
    container.innerHTML = `
      <div class="events-table-wrap">
        <table class="events-table">
          <thead><tr>
            <th>#</th><th>Title</th><th>Class</th><th>Moon</th>
            <th>Witnesses</th><th>Status</th><th>Date</th><th></th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  } catch (err) {
    container.innerHTML = `<div class="empty-state" style="color:var(--red);">${err.message}</div>`;
  }
}

async function verifyEvent(id, btn) {
  btn.textContent = '…';
  btn.disabled = true;
  try {
    await apiFetch(`/events/${id}/verify`, { method: 'PATCH' });
    toast(`Event #${id} verified`, 'ok');
    loadEvents();
    loadSummary();
  } catch (err) {
    toast(err.message, 'err');
    btn.textContent = 'Verify';
    btn.disabled = false;
  }
}

/* ── Load locations ── */
async function loadLocations() {
  const container = document.getElementById('locations-container');
  container.innerHTML = `<div class="loading-state"><span class="spinner"></span> Loading files…</div>`;
  try {
    const locs = await apiFetch('/locations?limit=50');
    if (!locs.length) {
      container.innerHTML = '<div class="empty-state">No locations registered.</div>';
      return;
    }
    const threatPct = { BENIGN: 10, LOW: 25, MODERATE: 50, HIGH: 75, EXTREME: 100 };
    const threatClass = { EXTREME: 'extreme', HIGH: 'high', MODERATE: 'moderate' };

    const cards = locs.map((l, i) => `
      <div class="loc-card" style="animation:fade-up 0.3s ease ${i * 0.04}s both;">
        <div class="loc-card-top">
          <span class="loc-id">${String(l.id).padStart(3, '0')}</span>
          <span class="loc-threat-badge ${threatClass[l.threat_level] ?? ''}">${l.threat_level}</span>
        </div>
        <div class="loc-name">${escHtml(l.name)}</div>
        <div class="loc-meta">
          <span>⚡ ${l.event_count} events</span>
          <span>${l.country_code ?? '—'}</span>
          <span>${l.latitude.toFixed(3)}, ${l.longitude.toFixed(3)}</span>
        </div>
        <div class="loc-threat-bar">
          <div class="loc-threat-fill" style="width:${threatPct[l.threat_level] ?? 10}%"></div>
        </div>
      </div>`).join('');

    container.innerHTML = `<div class="locations-grid">${cards}</div>`;
  } catch (err) {
    container.innerHTML = `<div class="empty-state" style="color:var(--red);">${err.message}</div>`;
  }
}

/* ── Submit location ── */
async function submitLocation() {
  const name = document.getElementById('loc-name').value.trim();
  const lat  = parseFloat(document.getElementById('loc-lat').value);
  const lon  = parseFloat(document.getElementById('loc-lon').value);

  if (!name || isNaN(lat) || isNaN(lon)) {
    toast('Name, latitude and longitude are required.', 'err');
    return;
  }

  const payload = {
    name,
    latitude: lat,
    longitude: lon,
    country_code: document.getElementById('loc-cc').value.trim().toUpperCase() || null,
    address: document.getElementById('loc-addr').value.trim() || null,
    notes: document.getElementById('loc-notes').value.trim() || null,
    tags: [],
  };

  try {
    const loc = await apiFetch('/locations', { method: 'POST', body: JSON.stringify(payload) });
    toast(`Location #${loc.id} registered: ${loc.name}`, 'ok');
    loadSummary();
    // Clear form
    ['loc-name','loc-lat','loc-lon','loc-cc','loc-addr','loc-notes'].forEach(id => {
      document.getElementById(id).value = '';
    });
  } catch (err) {
    toast(`Error: ${err.message}`, 'err');
  }
}

/* ── Helpers ── */
function escHtml(s = '') {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' });
}

function badgeHtml(cls = 'unknown') {
  return `<span class="badge badge-${cls.toLowerCase()}">${cls.toUpperCase()}</span>`;
}

/* ── Set default datetime ── */
document.getElementById('ev-date').value = new Date().toISOString().slice(0, 16);

/* ── Boot ── */
loadSummary();
loadRecentEvents();
