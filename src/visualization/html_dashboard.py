#!/usr/bin/env python3
"""
HTML Dashboard Generator

Writes a self-contained index.html to the output directory.
The page loads data lazily from the JSON files produced by HealthDataExporter.
No build step, no server required – open the file directly in a browser.
"""

from pathlib import Path


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Apple Health Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<style>
  :root {
    --bg:       #f2f2f7;
    --surface:  #ffffff;
    --accent:   #007aff;
    --accent2:  #34c759;
    --text:     #1c1c1e;
    --subtext:  #8e8e93;
    --border:   #e5e5ea;
    --sidebar-w: 260px;
  }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    min-height: 100vh;
  }

  /* ── Sidebar ─────────────────────────────────────────────────── */
  #sidebar {
    width: var(--sidebar-w);
    min-height: 100vh;
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    position: fixed;
    top: 0; left: 0; bottom: 0;
    overflow-y: auto;
    z-index: 100;
  }
  #sidebar-header {
    padding: 20px 16px 12px;
    border-bottom: 1px solid var(--border);
  }
  #sidebar-header h1 { font-size: 15px; font-weight: 700; }
  #sidebar-header p  { font-size: 12px; color: var(--subtext); margin-top: 2px; }

  #sidebar-search {
    margin: 10px 12px;
    padding: 7px 10px;
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 13px;
    width: calc(100% - 24px);
    background: var(--bg);
    color: var(--text);
  }
  #sidebar-search:focus { outline: none; border-color: var(--accent); }

  .nav-group { padding: 4px 0; }
  .nav-group-label {
    font-size: 10px;
    font-weight: 700;
    color: var(--subtext);
    text-transform: uppercase;
    letter-spacing: .7px;
    padding: 8px 16px 4px;
  }
  .nav-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 16px;
    font-size: 13px;
    cursor: pointer;
    border-radius: 0;
    transition: background .1s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .nav-item:hover   { background: var(--bg); }
  .nav-item.active  { background: #e5f0ff; color: var(--accent); font-weight: 600; }
  .nav-item .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    background: var(--accent);
  }
  .nav-item .dot.vitals    { background: #ff3b30; }
  .nav-item .dot.activity  { background: #34c759; }
  .nav-item .dot.body      { background: #ff9500; }
  .nav-item .dot.nutrition { background: #af52de; }
  .nav-item .dot.sleep     { background: #5856d6; }
  .nav-item .dot.mindfulness { background: #30b0c7; }
  .nav-item .dot.workouts  { background: #ff6b35; }
  .nav-item .dot.other     { background: var(--subtext); }

  /* ── Main content ────────────────────────────────────────────── */
  #main {
    margin-left: var(--sidebar-w);
    flex: 1;
    padding: 24px;
    min-width: 0;
  }

  /* ── Page header ─────────────────────────────────────────────── */
  .page-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 12px;
  }
  .page-header h2 { font-size: 22px; font-weight: 700; }
  .page-header p  { font-size: 13px; color: var(--subtext); margin-top: 3px; }

  .granularity-tabs {
    display: flex;
    gap: 4px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 3px;
  }
  .granularity-tabs button {
    border: none;
    background: transparent;
    padding: 5px 14px;
    font-size: 13px;
    border-radius: 6px;
    cursor: pointer;
    color: var(--subtext);
    font-family: inherit;
    transition: background .15s, color .15s;
  }
  .granularity-tabs button.active {
    background: var(--surface);
    color: var(--text);
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(0,0,0,.12);
  }

  /* ── Stat cards ──────────────────────────────────────────────── */
  .stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
  }
  .stat-card {
    background: var(--surface);
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }
  .stat-card .label  { font-size: 11px; color: var(--subtext); font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }
  .stat-card .value  { font-size: 26px; font-weight: 700; margin-top: 4px; line-height: 1; }
  .stat-card .unit   { font-size: 12px; color: var(--subtext); margin-top: 2px; }

  /* ── Chart card ──────────────────────────────────────────────── */
  .chart-card {
    background: var(--surface);
    border-radius: 14px;
    padding: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    margin-bottom: 20px;
  }
  .chart-card canvas { max-height: 300px; }

  /* ── Overview grid ───────────────────────────────────────────── */
  .overview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }
  .overview-card {
    background: var(--surface);
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    cursor: pointer;
    transition: box-shadow .15s;
  }
  .overview-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.1); }
  .overview-card h3  { font-size: 13px; font-weight: 600; color: var(--subtext); margin-bottom: 6px; }
  .overview-card .big { font-size: 28px; font-weight: 700; }
  .overview-card small { font-size: 12px; color: var(--subtext); }
  .overview-card canvas { margin-top: 12px; max-height: 70px; }

  /* ── Workout table ───────────────────────────────────────────── */
  .workout-summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
  }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th {
    text-align: left;
    padding: 8px 12px;
    font-size: 11px;
    font-weight: 700;
    color: var(--subtext);
    text-transform: uppercase;
    letter-spacing: .5px;
    border-bottom: 1px solid var(--border);
  }
  tbody tr { border-bottom: 1px solid var(--border); }
  tbody tr:last-child { border-bottom: none; }
  tbody td { padding: 9px 12px; }

  /* ── Loading / error ─────────────────────────────────────────── */
  #loading {
    position: fixed; inset: 0;
    background: rgba(255,255,255,.85);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    color: var(--subtext);
    z-index: 9999;
  }
  .spinner {
    width: 24px; height: 24px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin .7s linear infinite;
    margin-right: 10px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  #error-banner {
    display: none;
    background: #fff3f2;
    border: 1px solid #ffcdd2;
    border-radius: 10px;
    padding: 16px;
    color: #b71c1c;
    margin-bottom: 20px;
    font-size: 13px;
  }

  @media (max-width: 640px) {
    #sidebar { width: 100%; min-height: auto; position: relative; }
    #main { margin-left: 0; padding: 16px; }
    body { flex-direction: column; }
  }
</style>
</head>
<body>

<div id="loading"><div class="spinner"></div>Loading health data…</div>

<!-- ─── Sidebar ──────────────────────────────────────────────────────────── -->
<nav id="sidebar">
  <div id="sidebar-header">
    <h1>Health Dashboard</h1>
    <p id="sidebar-date-range">Loading…</p>
  </div>
  <input id="sidebar-search" type="search" placeholder="Search metrics…">
  <div id="sidebar-nav">
    <!-- populated by JS -->
  </div>
</nav>

<!-- ─── Main ─────────────────────────────────────────────────────────────── -->
<main id="main">
  <div id="error-banner"></div>
  <div id="content">
    <!-- populated by JS -->
  </div>
</main>

<script>
// ══════════════════════════════════════════════════════════════════════════
// State
// ══════════════════════════════════════════════════════════════════════════
const state = {
  manifest: null,
  metricCache: {},
  workouts: null,
  currentView: 'overview',
  granularity: 'daily',
  activeChart: null,
};

// ══════════════════════════════════════════════════════════════════════════
// Boot
// ══════════════════════════════════════════════════════════════════════════
async function boot() {
  try {
    state.manifest = await fetchJSON('data/manifest.json');
    renderSidebar();
    showView('overview');
  } catch(e) {
    showError('Could not load manifest.json. ' + e.message +
      '<br>Make sure you run <code>python main.py</code> first and open this file from the output/ directory.');
  } finally {
    document.getElementById('loading').style.display = 'none';
  }
}

// ══════════════════════════════════════════════════════════════════════════
// Data helpers
// ══════════════════════════════════════════════════════════════════════════
async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status} fetching ${url}`);
  return r.json();
}

async function loadMetric(id) {
  if (state.metricCache[id]) return state.metricCache[id];
  const data = await fetchJSON(`data/metrics/${id}.json`);
  state.metricCache[id] = data;
  return data;
}

async function loadWorkouts() {
  if (state.workouts) return state.workouts;
  state.workouts = await fetchJSON('data/workouts.json');
  return state.workouts;
}

// ══════════════════════════════════════════════════════════════════════════
// Sidebar
// ══════════════════════════════════════════════════════════════════════════
function renderSidebar() {
  const m = state.manifest;

  // Date range
  const dr = m.date_range;
  document.getElementById('sidebar-date-range').textContent =
    dr.start ? `${fmt(dr.start)} – ${fmt(dr.end)}` : 'No date range';

  // Group metrics by category
  const groups = {};
  for (const metric of m.metrics) {
    const cat = metric.category || 'other';
    (groups[cat] = groups[cat] || []).push(metric);
  }

  // Category ordering
  const ORDER = ['activity','vitals','body','sleep','nutrition','mindfulness','other'];
  const LABELS = {
    activity: 'Activity', vitals: 'Vitals', body: 'Body Measurements',
    sleep: 'Sleep', nutrition: 'Nutrition', mindfulness: 'Mindfulness', other: 'Other',
  };

  const nav = document.getElementById('sidebar-nav');
  nav.innerHTML = '';

  // Overview
  nav.appendChild(navItem('overview', 'other', 'Overview', false));

  // Workouts
  if (m.workouts && m.workouts.total > 0) {
    nav.appendChild(navItem('workouts', 'workouts', `Workouts (${m.workouts.total})`, false));
  }

  // Metrics grouped by category
  for (const cat of ORDER) {
    if (!groups[cat]) continue;
    const groupEl = document.createElement('div');
    groupEl.className = 'nav-group';
    groupEl.dataset.cat = cat;

    const label = document.createElement('div');
    label.className = 'nav-group-label';
    label.textContent = LABELS[cat] || cat;
    groupEl.appendChild(label);

    for (const metric of groups[cat]) {
      groupEl.appendChild(navItem('metric:' + metric.id, cat, metric.display_name, false));
    }
    nav.appendChild(groupEl);
  }

  // Search filtering
  document.getElementById('sidebar-search').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    nav.querySelectorAll('.nav-item').forEach(el => {
      el.style.display = !q || el.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
    nav.querySelectorAll('.nav-group').forEach(g => {
      const visible = [...g.querySelectorAll('.nav-item')].some(i => i.style.display !== 'none');
      g.style.display = visible ? '' : 'none';
    });
  });
}

function navItem(viewId, cat, label, isActive) {
  const el = document.createElement('div');
  el.className = 'nav-item' + (isActive ? ' active' : '');
  el.dataset.view = viewId;
  el.innerHTML = `<span class="dot ${cat}"></span><span>${label}</span>`;
  el.addEventListener('click', () => showView(viewId));
  return el;
}

function setActiveNav(viewId) {
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === viewId);
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Views
// ══════════════════════════════════════════════════════════════════════════
async function showView(viewId) {
  state.currentView = viewId;
  setActiveNav(viewId);
  destroyChart();
  showLoading(true);

  try {
    if (viewId === 'overview')   await renderOverview();
    else if (viewId === 'workouts') await renderWorkouts();
    else if (viewId.startsWith('metric:')) {
      const id = viewId.replace('metric:', '');
      await renderMetric(id);
    }
  } catch(e) {
    showError(e.message);
  } finally {
    showLoading(false);
  }
}

// ── Overview ──────────────────────────────────────────────────────────────
async function renderOverview() {
  const m = state.manifest;
  const topN = m.metrics.slice(0, 8);

  // Fetch sparkline data for top metrics in parallel
  const loaded = await Promise.all(topN.map(metric => loadMetric(metric.id).catch(() => null)));

  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2>Overview</h2>
        <p>${m.total_records.toLocaleString()} records · ${m.metrics.length} metric types · ${m.sources.length} source(s)</p>
      </div>
    </div>
    <div class="overview-grid" id="overview-grid"></div>
  `;

  const grid = document.getElementById('overview-grid');

  topN.forEach((metric, i) => {
    const data = loaded[i];
    const card = document.createElement('div');
    card.className = 'overview-card';
    card.onclick = () => showView('metric:' + metric.id);

    let latestVal = '—', latestDate = '';
    if (data && data.daily && data.daily.length > 0) {
      const last = data.daily[data.daily.length - 1];
      latestVal  = fmtVal(last.value);
      latestDate = 'Last: ' + fmt(last.date);
    }

    card.innerHTML = `
      <h3>${metric.display_name}</h3>
      <div class="big">${latestVal} <small>${metric.unit}</small></div>
      <small>${latestDate}</small>
      <canvas id="spark-${metric.id}" height="70"></canvas>
    `;
    grid.appendChild(card);

    // Sparkline
    if (data && data.daily && data.daily.length > 0) {
      const last30 = data.daily.slice(-30);
      new Chart(document.getElementById('spark-' + metric.id), {
        type: 'line',
        data: {
          labels: last30.map(d => d.date),
          datasets: [{
            data: last30.map(d => d.value),
            borderColor: catColor(metric.category),
            borderWidth: 1.5,
            pointRadius: 0,
            fill: true,
            backgroundColor: catColor(metric.category, .12),
            tension: .3,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false }, tooltip: { enabled: false } },
          scales: { x: { display: false }, y: { display: false } },
          animation: false,
        },
      });
    }
  });
}

// ── Metric detail ─────────────────────────────────────────────────────────
async function renderMetric(id) {
  showLoading(true);
  const metric = state.manifest.metrics.find(m => m.id === id);
  const data   = await loadMetric(id);

  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2>${data.display_name}</h2>
        <p>${metric.record_count.toLocaleString()} records · ${data.unit} · ${data.agg_method === 'sum' ? 'daily total' : 'daily average'}</p>
      </div>
      <div class="granularity-tabs">
        <button onclick="setGranularity('daily',   '${id}')" id="btn-daily"   class="active">Daily</button>
        <button onclick="setGranularity('weekly',  '${id}')" id="btn-weekly"  >Weekly</button>
        <button onclick="setGranularity('monthly', '${id}')" id="btn-monthly" >Monthly</button>
      </div>
    </div>
    <div class="stat-grid" id="stat-grid"></div>
    <div class="chart-card"><canvas id="main-chart"></canvas></div>
  `;

  renderStatCards(data);
  renderMainChart(data, 'daily');
}

function setGranularity(gran, metricId) {
  state.granularity = gran;
  ['daily','weekly','monthly'].forEach(g => {
    document.getElementById('btn-' + g)?.classList.toggle('active', g === gran);
  });
  const data = state.metricCache[metricId];
  if (data) renderMainChart(data, gran);
}

function renderStatCards(data) {
  const daily = data.daily || [];
  if (!daily.length) return;

  const vals = daily.map(d => d.value);
  const last30 = daily.slice(-30).map(d => d.value);

  const stats = [
    { label: 'Latest',  value: fmtVal(vals[vals.length - 1]),         unit: data.unit },
    { label: 'Avg (30d)', value: fmtVal(avg(last30)),                 unit: data.unit },
    { label: 'Max',     value: fmtVal(Math.max(...vals)),             unit: data.unit },
    { label: 'Total records', value: daily.reduce((a,d) => a + d.count, 0).toLocaleString(), unit: '' },
  ];

  const grid = document.getElementById('stat-grid');
  grid.innerHTML = stats.map(s => `
    <div class="stat-card">
      <div class="label">${s.label}</div>
      <div class="value">${s.value}</div>
      <div class="unit">${s.unit}</div>
    </div>
  `).join('');
}

function renderMainChart(data, gran) {
  destroyChart();
  const rows = data[gran] || [];
  if (!rows.length) return;

  const labelKey = gran === 'daily' ? 'date' : gran === 'weekly' ? 'start_date' : 'start_date';
  const color = catColor(data.category ?? 'other');

  const datasets = [{
    label: data.display_name,
    data: rows.map(r => ({ x: r[labelKey], y: r.value })),
    borderColor: color,
    backgroundColor: catColor(data.category ?? 'other', .15),
    borderWidth: 2,
    pointRadius: gran === 'daily' && rows.length > 90 ? 0 : 3,
    fill: true,
    tension: .3,
  }];

  // Add min/max band for daily avg metrics
  if (gran === 'daily' && data.agg_method === 'mean' && rows[0].min !== undefined) {
    datasets.unshift({
      label: 'Range',
      data: rows.map(r => ({ x: r.date, y: r.max })),
      borderColor: 'transparent',
      backgroundColor: catColor(data.category ?? 'other', .08),
      fill: '+1',
      pointRadius: 0,
      tension: .3,
    });
    datasets.push({
      label: '_min',
      data: rows.map(r => ({ x: r.date, y: r.min })),
      borderColor: 'transparent',
      backgroundColor: 'transparent',
      pointRadius: 0,
      tension: .3,
    });
  }

  state.activeChart = new Chart(document.getElementById('main-chart'), {
    type: 'line',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              if (ctx.dataset.label.startsWith('_')) return null;
              return `${ctx.dataset.label}: ${fmtVal(ctx.parsed.y)} ${data.unit}`;
            },
          },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: {
            unit: gran === 'daily' ? 'month' : gran === 'weekly' ? 'month' : 'year',
            tooltipFormat: gran === 'daily' ? 'MMM d, yyyy' : gran === 'weekly' ? "'Week of' MMM d" : 'MMMM yyyy',
          },
          grid: { color: '#f2f2f7' },
          ticks: { color: '#8e8e93', maxRotation: 0 },
        },
        y: {
          grid: { color: '#f2f2f7' },
          ticks: { color: '#8e8e93', callback: v => fmtVal(v) },
        },
      },
    },
  });
}

// ── Workouts ──────────────────────────────────────────────────────────────
async function renderWorkouts() {
  const wk = await loadWorkouts();
  const m  = state.manifest;

  const content = document.getElementById('content');
  content.innerHTML = `
    <div class="page-header">
      <div>
        <h2>Workouts</h2>
        <p>${wk.total.toLocaleString()} workouts · ${wk.types.length} type(s)</p>
      </div>
    </div>
    <div class="workout-summary-grid" id="wk-summary-grid"></div>
    <div class="chart-card" style="margin-bottom:20px">
      <canvas id="wk-chart" height="250"></canvas>
    </div>
    <div class="chart-card">
      <h3 style="font-size:14px;font-weight:700;margin-bottom:14px;">Recent Workouts</h3>
      <table>
        <thead><tr>
          <th>Date</th><th>Type</th><th>Duration</th><th>Calories</th><th>Source</th>
        </tr></thead>
        <tbody id="wk-table-body"></tbody>
      </table>
    </div>
  `;

  // Summary cards
  const grid = document.getElementById('wk-summary-grid');
  const byType = wk.by_type || {};
  for (const [type, stats] of Object.entries(byType)) {
    grid.innerHTML += `
      <div class="stat-card">
        <div class="label">${type}</div>
        <div class="value">${stats.count}</div>
        <div class="unit">sessions · avg ${stats.avg_duration_minutes} min</div>
      </div>`;
  }

  // Weekly frequency bar chart
  const weeklyMap = {};
  for (const rec of wk.records) {
    const d = new Date(rec.date);
    const iso = isoWeekKey(d);
    weeklyMap[iso] = (weeklyMap[iso] || 0) + 1;
  }
  const weeks = Object.keys(weeklyMap).sort();
  state.activeChart = new Chart(document.getElementById('wk-chart'), {
    type: 'bar',
    data: {
      labels: weeks,
      datasets: [{
        label: 'Workouts per week',
        data: weeks.map(w => weeklyMap[w]),
        backgroundColor: '#ff6b35cc',
        borderRadius: 3,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          type: 'time',
          time: { unit: 'month', tooltipFormat: "'Week of' MMM d, yyyy" },
          grid: { display: false },
          ticks: { color: '#8e8e93', maxRotation: 0 },
        },
        y: { grid: { color: '#f2f2f7' }, ticks: { stepSize: 1, color: '#8e8e93' } },
      },
    },
  });

  // Recent workouts table (last 20)
  const tbody = document.getElementById('wk-table-body');
  const recent = wk.records.slice(-20).reverse();
  tbody.innerHTML = recent.map(r => `
    <tr>
      <td>${fmt(r.date)}</td>
      <td>${r.type}</td>
      <td>${r.duration_minutes} min</td>
      <td>${r.calories ? r.calories + ' kcal' : '—'}</td>
      <td>${r.source}</td>
    </tr>
  `).join('');
}

// ══════════════════════════════════════════════════════════════════════════
// Utility
// ══════════════════════════════════════════════════════════════════════════
function fmt(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function fmtVal(v) {
  if (v === null || v === undefined || isNaN(v)) return '—';
  if (Math.abs(v) >= 1000) return Math.round(v).toLocaleString();
  if (Math.abs(v) < 10)    return (+v.toFixed(2)).toString();
  return Math.round(v).toLocaleString();
}

function avg(arr) {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}

function destroyChart() {
  if (state.activeChart) { state.activeChart.destroy(); state.activeChart = null; }
}

function showLoading(on) {
  document.getElementById('loading').style.display = on ? 'flex' : 'none';
}

function showError(msg) {
  const el = document.getElementById('error-banner');
  el.innerHTML = msg;
  el.style.display = 'block';
}

function isoWeekKey(d) {
  const jan4 = new Date(d.getFullYear(), 0, 4);
  const startOfWeek1 = new Date(jan4);
  startOfWeek1.setDate(jan4.getDate() - (jan4.getDay() || 7) + 1);
  const weekNo = Math.ceil(((d - startOfWeek1) / 86400000 + 1) / 7);
  return `${d.getFullYear()}-${String(weekNo).padStart(2,'0')}-01`;
}

const CAT_COLORS = {
  activity:    '#34c759',
  vitals:      '#ff3b30',
  body:        '#ff9500',
  nutrition:   '#af52de',
  sleep:       '#5856d6',
  mindfulness: '#30b0c7',
  workouts:    '#ff6b35',
  other:       '#007aff',
};
function catColor(cat, alpha) {
  const hex = CAT_COLORS[cat] || '#007aff';
  if (!alpha) return hex;
  const r = parseInt(hex.slice(1,3),16);
  const g = parseInt(hex.slice(3,5),16);
  const b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ══════════════════════════════════════════════════════════════════════════
// Start
// ══════════════════════════════════════════════════════════════════════════
boot();
</script>
</body>
</html>
"""


def generate_html_dashboard(output_dir: Path) -> Path:
    """
    Write index.html to output_dir.
    Returns the path to the generated file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "index.html"
    out_path.write_text(HTML_TEMPLATE, encoding="utf-8")
    return out_path
