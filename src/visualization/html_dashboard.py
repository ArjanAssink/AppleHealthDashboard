#!/usr/bin/env python3
"""
HTML Dashboard Generator

Writes a self-contained index.html to the output directory.
The page loads data lazily from the JSON files produced by HealthDataExporter.
No build step, no server required – open the file directly in a browser.

Charts are rendered with Apache ECharts (CDN), which provides:
  - Built-in time axis (no adapter needed)
  - dataZoom for pan/scroll on time-series views
  - Calendar heatmap for workout frequency
  - Min/max confidence band for averaged metrics (heart rate, weight, etc.)
"""

from pathlib import Path


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Apple Health Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
<style>
  :root {
    --bg:        #f2f2f7;
    --surface:   #ffffff;
    --accent:    #007aff;
    --text:      #1c1c1e;
    --subtext:   #8e8e93;
    --border:    #e5e5ea;
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

  /* ── Sidebar ──────────────────────────────────────────────────── */
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
  #sidebar-header { padding: 20px 16px 12px; border-bottom: 1px solid var(--border); }
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
    font-size: 10px; font-weight: 700; color: var(--subtext);
    text-transform: uppercase; letter-spacing: .7px;
    padding: 8px 16px 4px;
  }
  .nav-item {
    display: flex; align-items: center; gap: 8px;
    padding: 7px 16px; font-size: 13px; cursor: pointer;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    transition: background .1s;
  }
  .nav-item:hover  { background: var(--bg); }
  .nav-item.active { background: #e5f0ff; color: var(--accent); font-weight: 600; }
  .nav-item .dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    background: var(--accent);
  }
  .nav-item .dot.vitals      { background: #ff3b30; }
  .nav-item .dot.activity    { background: #34c759; }
  .nav-item .dot.body        { background: #ff9500; }
  .nav-item .dot.nutrition   { background: #af52de; }
  .nav-item .dot.sleep       { background: #5856d6; }
  .nav-item .dot.mindfulness { background: #30b0c7; }
  .nav-item .dot.workouts    { background: #ff6b35; }
  .nav-item .dot.other       { background: var(--subtext); }

  /* ── Main content ─────────────────────────────────────────────── */
  #main { margin-left: var(--sidebar-w); flex: 1; padding: 24px; min-width: 0; }

  /* ── Page header ──────────────────────────────────────────────── */
  .page-header {
    display: flex; align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 20px; flex-wrap: wrap; gap: 12px;
  }
  .page-header h2 { font-size: 22px; font-weight: 700; }
  .page-header p  { font-size: 13px; color: var(--subtext); margin-top: 3px; }

  .gran-tabs {
    display: flex; gap: 4px;
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 8px; padding: 3px;
  }
  .gran-tabs button {
    border: none; background: transparent;
    padding: 5px 14px; font-size: 13px; border-radius: 6px;
    cursor: pointer; color: var(--subtext); font-family: inherit;
    transition: background .15s, color .15s;
  }
  .gran-tabs button.active {
    background: var(--surface); color: var(--text);
    font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,.12);
  }

  .filter-select {
    padding: 5px 28px 5px 12px;
    font-size: 13px;
    font-family: inherit;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg);
    color: var(--text);
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%238e8e93'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
  }
  .filter-select:focus { outline: none; border-color: var(--accent); }

  /* ── Stat cards ───────────────────────────────────────────────── */
  .stat-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 12px; margin-bottom: 20px;
  }
  .stat-card {
    background: var(--surface); border-radius: 14px;
    padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.06);
  }
  .stat-card .label { font-size: 11px; color: var(--subtext); font-weight: 600; text-transform: uppercase; letter-spacing: .5px; }
  .stat-card .value { font-size: 26px; font-weight: 700; margin-top: 4px; line-height: 1; }
  .stat-card .unit  { font-size: 12px; color: var(--subtext); margin-top: 2px; }

  /* ── Chart card ───────────────────────────────────────────────── */
  .chart-card {
    background: var(--surface); border-radius: 14px;
    padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,.06);
    margin-bottom: 20px;
  }
  .chart-card h3 { font-size: 14px; font-weight: 700; margin-bottom: 14px; }

  /* ── Overview grid ────────────────────────────────────────────── */
  .overview-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }
  .overview-card {
    background: var(--surface); border-radius: 14px;
    padding: 16px 20px; box-shadow: 0 1px 3px rgba(0,0,0,.06);
    cursor: pointer; transition: box-shadow .15s;
  }
  .overview-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.1); }
  .overview-card h3   { font-size: 13px; font-weight: 600; color: var(--subtext); margin-bottom: 6px; }
  .overview-card .big { font-size: 28px; font-weight: 700; }
  .overview-card small { font-size: 12px; color: var(--subtext); }
  .overview-card .spark { margin-top: 12px; height: 70px; }

  /* ── Workout summary ──────────────────────────────────────────── */
  .wk-summary-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px; margin-bottom: 20px;
  }

  /* ── Table ────────────────────────────────────────────────────── */
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  thead th {
    text-align: left; padding: 8px 12px;
    font-size: 11px; font-weight: 700; color: var(--subtext);
    text-transform: uppercase; letter-spacing: .5px;
    border-bottom: 1px solid var(--border);
  }
  tbody tr { border-bottom: 1px solid var(--border); }
  tbody tr:last-child { border-bottom: none; }
  tbody td { padding: 9px 12px; }

  /* ── Loading / error ──────────────────────────────────────────── */
  #loading {
    position: fixed; inset: 0; background: rgba(255,255,255,.85);
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; color: var(--subtext); z-index: 9999;
  }
  .spinner {
    width: 24px; height: 24px;
    border: 3px solid var(--border); border-top-color: var(--accent);
    border-radius: 50%; animation: spin .7s linear infinite; margin-right: 10px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  #error-banner {
    display: none; background: #fff3f2; border: 1px solid #ffcdd2;
    border-radius: 10px; padding: 16px; color: #b71c1c;
    margin-bottom: 20px; font-size: 13px;
  }

  @media (max-width: 640px) {
    #sidebar { width: 100%; min-height: auto; position: relative; }
    #main    { margin-left: 0; padding: 16px; }
    body     { flex-direction: column; }
  }
</style>
</head>
<body>

<div id="loading"><div class="spinner"></div>Loading health data…</div>

<nav id="sidebar">
  <div id="sidebar-header">
    <h1>Health Dashboard</h1>
    <p id="sidebar-date-range">Loading…</p>
  </div>
  <input id="sidebar-search" type="search" placeholder="Search metrics…">
  <div id="sidebar-nav"></div>
</nav>

<main id="main">
  <div id="error-banner"></div>
  <div id="content"></div>
</main>

<script>
'use strict';

// ══════════════════════════════════════════════════════════════════════════
// State & chart registry
// ══════════════════════════════════════════════════════════════════════════
const state = {
  manifest:    null,
  metricCache: {},
  workouts:    null,
  currentView:   'overview',
  granularity:   'daily',
  workoutFilter: 'all',
};

// All active ECharts instances – disposed on every view transition
const chartInstances = [];

function initChart(domId) {
  const el = document.getElementById(domId);
  if (!el) return null;
  const instance = echarts.init(el, null, { renderer: 'canvas' });
  chartInstances.push(instance);
  return instance;
}

function disposeAllCharts() {
  chartInstances.forEach(c => { try { c.dispose(); } catch(_) {} });
  chartInstances.length = 0;
}

window.addEventListener('resize', () => {
  chartInstances.forEach(c => { try { c.resize(); } catch(_) {} });
});

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
      '<br>Run <code>python main.py</code> first, then open this file from the output/ directory.');
  } finally {
    document.getElementById('loading').style.display = 'none';
  }
}

// ══════════════════════════════════════════════════════════════════════════
// Data fetching
// ══════════════════════════════════════════════════════════════════════════
async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status} fetching ${url}`);
  return r.json();
}

async function loadMetric(id) {
  if (!state.metricCache[id])
    state.metricCache[id] = await fetchJSON(`data/metrics/${id}.json`);
  return state.metricCache[id];
}

async function loadWorkouts() {
  if (!state.workouts)
    state.workouts = await fetchJSON('data/workouts.json');
  return state.workouts;
}

// ══════════════════════════════════════════════════════════════════════════
// Sidebar
// ══════════════════════════════════════════════════════════════════════════
function renderSidebar() {
  const m  = state.manifest;
  const dr = m.date_range;
  document.getElementById('sidebar-date-range').textContent =
    dr.start ? `${fmtDate(dr.start)} – ${fmtDate(dr.end)}` : 'No data';

  const ORDER  = ['activity','vitals','body','sleep','nutrition','mindfulness','other'];
  const LABELS = { activity:'Activity', vitals:'Vitals', body:'Body Measurements',
                   sleep:'Sleep', nutrition:'Nutrition', mindfulness:'Mindfulness', other:'Other' };

  const groups = {};
  for (const metric of m.metrics) {
    const cat = metric.category || 'other';
    (groups[cat] = groups[cat] || []).push(metric);
  }

  const nav = document.getElementById('sidebar-nav');
  nav.innerHTML = '';
  nav.appendChild(navItem('overview',  'other',    'Overview'));
  if (m.workouts && m.workouts.total > 0)
    nav.appendChild(navItem('workouts', 'workouts', `Workouts (${m.workouts.total})`));

  for (const cat of ORDER) {
    if (!groups[cat]) continue;
    const g = document.createElement('div');
    g.className = 'nav-group';
    g.dataset.cat = cat;
    const lbl = document.createElement('div');
    lbl.className = 'nav-group-label';
    lbl.textContent = LABELS[cat] || cat;
    g.appendChild(lbl);
    for (const metric of groups[cat])
      g.appendChild(navItem('metric:' + metric.id, cat, metric.display_name));
    nav.appendChild(g);
  }

  document.getElementById('sidebar-search').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    nav.querySelectorAll('.nav-item').forEach(el => {
      el.style.display = (!q || el.textContent.toLowerCase().includes(q)) ? '' : 'none';
    });
    nav.querySelectorAll('.nav-group').forEach(g => {
      g.style.display = [...g.querySelectorAll('.nav-item')].some(i => i.style.display !== 'none') ? '' : 'none';
    });
  });
}

function navItem(viewId, cat, label) {
  const el = document.createElement('div');
  el.className = 'nav-item';
  el.dataset.view = viewId;
  el.innerHTML = `<span class="dot ${cat}"></span><span>${label}</span>`;
  el.addEventListener('click', () => showView(viewId));
  return el;
}

function setActiveNav(viewId) {
  document.querySelectorAll('.nav-item').forEach(el =>
    el.classList.toggle('active', el.dataset.view === viewId));
}

// ══════════════════════════════════════════════════════════════════════════
// View routing
// ══════════════════════════════════════════════════════════════════════════
async function showView(viewId) {
  state.currentView = viewId;
  setActiveNav(viewId);
  disposeAllCharts();
  document.getElementById('error-banner').style.display = 'none';
  showLoading(true);
  try {
    if (viewId === 'overview')            await renderOverview();
    else if (viewId === 'workouts')       await renderWorkouts();
    else if (viewId.startsWith('metric:')) await renderMetric(viewId.slice(7));
  } catch(e) {
    showError(e.message);
  } finally {
    showLoading(false);
  }
}

// ══════════════════════════════════════════════════════════════════════════
// Overview
// ══════════════════════════════════════════════════════════════════════════
async function renderOverview() {
  const m    = state.manifest;
  const topN = m.metrics.slice(0, 8);
  const loaded = await Promise.all(topN.map(metric => loadMetric(metric.id).catch(() => null)));

  document.getElementById('content').innerHTML = `
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
    card.onclick   = () => showView('metric:' + metric.id);

    let latestVal = '—', latestDate = '';
    if (data && data.daily && data.daily.length > 0) {
      const last = data.daily[data.daily.length - 1];
      latestVal  = fmtVal(last.value);
      latestDate = 'Last: ' + fmtDate(last.date);
    }

    card.innerHTML = `
      <h3>${metric.display_name}</h3>
      <div class="big">${latestVal} <small style="font-size:14px;font-weight:400;color:var(--subtext)">${metric.unit}</small></div>
      <small>${latestDate}</small>
      <div class="spark" id="spark-${metric.id}"></div>
    `;
    grid.appendChild(card);

    if (data && data.daily && data.daily.length > 0) {
      renderSparkline('spark-' + metric.id, data.daily.slice(-30), catColor(metric.category));
    }
  });
}

function renderSparkline(domId, rows, color) {
  const chart = initChart(domId);
  if (!chart) return;
  chart.setOption({
    animation: false,
    grid: { top: 2, bottom: 2, left: 2, right: 2 },
    xAxis: { type: 'category', show: false, data: rows.map(r => r.date) },
    yAxis: { type: 'value',    show: false, scale: true },
    series: [{
      type: 'line',
      data: rows.map(r => r.value),
      smooth: 0.4,
      symbol: 'none',
      lineStyle: { color, width: 1.5 },
      areaStyle: { color: hexAlpha(color, 0.15) },
    }],
    tooltip: { show: false },
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Metric detail
// ══════════════════════════════════════════════════════════════════════════
async function renderMetric(id) {
  const metric = state.manifest.metrics.find(m => m.id === id);
  const data   = await loadMetric(id);

  document.getElementById('content').innerHTML = `
    <div class="page-header">
      <div>
        <h2>${data.display_name}</h2>
        <p>${metric.record_count.toLocaleString()} records · ${data.unit} · ${data.agg_method === 'sum' ? 'daily total' : 'daily average'}</p>
      </div>
      <div class="gran-tabs">
        <button id="btn-daily"   class="active" onclick="setGranularity('daily','${id}')">Daily</button>
        <button id="btn-weekly"           onclick="setGranularity('weekly','${id}')">Weekly</button>
        <button id="btn-monthly"          onclick="setGranularity('monthly','${id}')">Monthly</button>
      </div>
    </div>
    <div class="stat-grid" id="stat-grid"></div>
    <div class="chart-card">
      <div id="main-chart" style="height:340px"></div>
    </div>
  `;

  renderStatCards(data);
  renderMainChart(data, 'daily');
}

function setGranularity(gran, metricId) {
  state.granularity = gran;
  ['daily','weekly','monthly'].forEach(g =>
    document.getElementById('btn-' + g)?.classList.toggle('active', g === gran));
  const data = state.metricCache[metricId];
  if (data) renderMainChart(data, gran);
}

function renderStatCards(data) {
  const daily = data.daily || [];
  if (!daily.length) return;
  const vals   = daily.map(d => d.value);
  const last30 = daily.slice(-30).map(d => d.value);
  const stats  = [
    { label: 'Latest',       value: fmtVal(vals[vals.length - 1]),         unit: data.unit },
    { label: 'Avg (30 days)',value: fmtVal(avg(last30)),                   unit: data.unit },
    { label: 'All-time max', value: fmtVal(Math.max(...vals)),             unit: data.unit },
    { label: 'Total records',value: daily.reduce((a,d) => a + d.count,0).toLocaleString(), unit: '' },
  ];
  document.getElementById('stat-grid').innerHTML = stats.map(s => `
    <div class="stat-card">
      <div class="label">${s.label}</div>
      <div class="value">${s.value}</div>
      <div class="unit">${s.unit}</div>
    </div>
  `).join('');
}

function renderMainChart(data, gran) {
  // Dispose only the main chart (sparklines may already be gone from a prior view)
  disposeAllCharts();

  const chart = initChart('main-chart');
  if (!chart) return;

  const rows = data[gran] || [];
  if (!rows.length) return;

  const color   = catColor(data.category || 'other');
  const dateKey = gran === 'daily' ? 'date' : 'start_date';
  const series  = [];

  // Min/max confidence band for averaged metrics (e.g. heart rate, weight)
  if (gran === 'daily' && data.agg_method === 'mean' && rows[0].min !== undefined) {
    // Stacked band: lower series is the baseline, upper adds the delta
    series.push({
      type: 'line', name: 'min',
      data: rows.map(r => [r[dateKey], r.min]),
      symbol: 'none', lineStyle: { opacity: 0 },
      areaStyle: { color: 'transparent' },
      stack: 'band', stackStrategy: 'all',
      tooltip: { show: false },
    });
    series.push({
      type: 'line', name: 'range',
      data: rows.map(r => [r[dateKey], r.max - r.min]),
      symbol: 'none', lineStyle: { opacity: 0 },
      areaStyle: { color: hexAlpha(color, 0.15) },
      stack: 'band', stackStrategy: 'all',
      tooltip: { show: false },
    });
  }

  // Main value line
  series.push({
    type: 'line', name: data.display_name,
    data: rows.map(r => [r[dateKey], r.value]),
    smooth: 0.3,
    symbol: rows.length <= 60 ? 'circle' : 'none',
    symbolSize: 4,
    lineStyle: { color, width: 2 },
    itemStyle: { color },
    areaStyle: gran === 'monthly' ? null : { color: hexAlpha(color, 0.08) },
    z: 3,
  });

  chart.setOption({
    animation: false,
    grid: { top: 16, bottom: gran === 'monthly' ? 36 : 72, left: 64, right: 16 },
    xAxis: {
      type: 'time',
      axisLine:  { lineStyle: { color: '#e5e5ea' } },
      axisTick:  { show: false },
      axisLabel: { color: '#8e8e93', hideOverlap: true },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8e8e93', formatter: v => fmtVal(v) },
      splitLine:  { lineStyle: { color: '#f2f2f7' } },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', crossStyle: { color: '#c0c0c0' }, lineStyle: { type: 'dashed' } },
      formatter(params) {
        const main = params.find(p => p.seriesName === data.display_name);
        if (!main) return '';
        const row = rows[main.dataIndex] || {};
        let html = `<div style="font-size:12px;color:#8e8e93;margin-bottom:4px">${fmtDateLong(main.value[0])}</div>`;
        html += `<b>${fmtVal(main.value[1])} ${data.unit}</b>`;
        if (row.min !== undefined && row.min !== row.max)
          html += `<div style="font-size:11px;color:#8e8e93;margin-top:2px">Range: ${fmtVal(row.min)} – ${fmtVal(row.max)}</div>`;
        return html;
      },
    },
    // dataZoom: inside (mouse wheel / touch) + slider bar below the chart
    dataZoom: gran === 'monthly' ? [] : [
      { type: 'inside', start: 0, end: 100, zoomOnMouseWheel: true, moveOnMouseMove: true },
      {
        type: 'slider', bottom: 8, height: 24,
        borderColor: '#e5e5ea',
        fillerColor: hexAlpha(color, 0.12),
        handleStyle: { color, borderColor: color },
        moveHandleStyle: { color },
        textStyle: { color: '#8e8e93', fontSize: 10 },
      },
    ],
    series,
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Workouts
// ══════════════════════════════════════════════════════════════════════════
async function renderWorkouts() {
  const wk = await loadWorkouts();
  state.workoutFilter = 'all';

  const typeOptions = wk.types.slice().sort().map(t =>
    `<option value="${t}">${t}</option>`
  ).join('');

  document.getElementById('content').innerHTML = `
    <div class="page-header">
      <div>
        <h2>Workouts</h2>
        <p id="wk-subtitle">${wk.total.toLocaleString()} workouts · ${wk.types.length} type(s)</p>
      </div>
      <select class="filter-select" id="wk-type-filter">
        <option value="all">All Types</option>
        ${typeOptions}
      </select>
    </div>
    <div class="wk-summary-grid" id="wk-summary-grid"></div>
    <div class="chart-card">
      <h3>Workout Calendar</h3>
      <div id="wk-calendar"></div>
    </div>
    <div class="chart-card">
      <h3>Weekly Frequency</h3>
      <div id="wk-freq" style="height:200px"></div>
    </div>
    <div class="chart-card">
      <h3>Recent Workouts</h3>
      <table>
        <thead><tr>
          <th>Date</th><th>Type</th><th>Duration</th><th>Calories</th><th>Source</th>
        </tr></thead>
        <tbody id="wk-tbody"></tbody>
      </table>
    </div>
  `;

  document.getElementById('wk-type-filter').addEventListener('change', e => {
    state.workoutFilter = e.target.value;
    applyWorkoutFilter();
  });

  applyWorkoutFilter();
}

function applyWorkoutFilter() {
  const wk     = state.workouts;
  const filter = state.workoutFilter;
  const records = filter === 'all'
    ? wk.records
    : wk.records.filter(r => r.type === filter);
  const byType = filter === 'all'
    ? wk.by_type || {}
    : { [filter]: (wk.by_type || {})[filter] };

  // Update subtitle
  const subtitle = document.getElementById('wk-subtitle');
  if (subtitle) {
    const typeCount = filter === 'all' ? wk.types.length : 1;
    subtitle.textContent = `${records.length.toLocaleString()} workouts · ${typeCount} type(s)`;
  }

  // Summary cards
  const grid = document.getElementById('wk-summary-grid');
  grid.innerHTML = '';
  for (const [type, s] of Object.entries(byType)) {
    if (!s) continue;
    grid.innerHTML += `
      <div class="stat-card">
        <div class="label">${type}</div>
        <div class="value">${s.count}</div>
        <div class="unit">${s.avg_duration_minutes} min avg · ${Math.round(s.total_duration_minutes / 60)}h total</div>
      </div>`;
  }

  // Calendar
  disposeAllCharts();
  const years = [...new Set(records.map(r => r.date.slice(0,4)))].sort();
  const calH  = Math.max(200, years.length * 160 + 80);
  document.getElementById('wk-calendar').style.height = calH + 'px';
  renderWorkoutCalendar(records, years, calH);

  // Frequency
  renderWorkoutFrequency(records);

  // Recent table
  const recent = records.slice(-20).reverse();
  document.getElementById('wk-tbody').innerHTML = recent.map(r => `
    <tr>
      <td>${fmtDate(r.date)}</td>
      <td>${r.type}</td>
      <td>${r.duration_minutes} min</td>
      <td>${r.calories ? r.calories + ' kcal' : '—'}</td>
      <td>${r.source}</td>
    </tr>
  `).join('');
}

function renderWorkoutCalendar(records, years, containerH) {
  const chart = initChart('wk-calendar');
  if (!chart) return;

  // Build [date, count] from workout records
  const dayMap = {};
  for (const r of records) dayMap[r.date] = (dayMap[r.date] || 0) + 1;
  const calData = Object.entries(dayMap);

  // One calendar component per year, stacked vertically
  const PER_YEAR_H  = 150;
  const TOP_PADDING = 30;

  const calendarDefs = years.map((year, i) => ({
    top:      TOP_PADDING + i * PER_YEAR_H,
    left:     60, right: 20,
    range:    year,
    cellSize: ['auto', 14],
    dayLabel: {
      show: true, firstDay: 1,
      nameMap: ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
      color: '#8e8e93', fontSize: 10,
    },
    monthLabel: { color: '#8e8e93', fontSize: 11 },
    yearLabel:  { show: true, color: '#1c1c1e', fontSize: 13, fontWeight: 700, position: 'left' },
    splitLine:  { show: false },
    itemStyle:  { borderWidth: 3, borderColor: '#fff' },
  }));

  const seriesDefs = years.map((year, i) => ({
    type: 'heatmap',
    coordinateSystem: 'calendar',
    calendarIndex: i,
    data: calData.filter(([d]) => d.startsWith(year)),
  }));

  chart.setOption({
    animation: false,
    tooltip: {
      formatter: p => {
        const count = p.value[1];
        return `${fmtDate(p.value[0])}: <b>${count} workout${count > 1 ? 's' : ''}</b>`;
      },
    },
    visualMap: {
      type: 'piecewise',
      orient: 'horizontal',
      left: 'center', bottom: 0,
      pieces: [
        { value: 0, color: '#ebedf0', label: '0'  },
        { value: 1, color: '#9be9a8', label: '1'  },
        { value: 2, color: '#40c463', label: '2'  },
        { gte: 3,  color: '#216e39', label: '3+' },
      ],
      itemWidth: 12, itemHeight: 12,
      textStyle: { color: '#8e8e93', fontSize: 11 },
    },
    calendar: calendarDefs,
    series:   seriesDefs,
  });
}

function renderWorkoutFrequency(records) {
  const chart = initChart('wk-freq');
  if (!chart) return;

  // Group by ISO week start (Monday)
  const weekMap = {};
  for (const r of records) {
    const monday = mondayOf(new Date(r.date + 'T00:00:00'));
    weekMap[monday] = (weekMap[monday] || 0) + 1;
  }
  const weeks = Object.keys(weekMap).sort();

  chart.setOption({
    animation: false,
    grid: { top: 8, bottom: 36, left: 36, right: 16 },
    xAxis: {
      type: 'time',
      axisLine:  { lineStyle: { color: '#e5e5ea' } },
      axisTick:  { show: false },
      axisLabel: { color: '#8e8e93', hideOverlap: true },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value', minInterval: 1,
      axisLabel: { color: '#8e8e93' },
      splitLine:  { lineStyle: { color: '#f2f2f7' } },
    },
    tooltip: {
      trigger: 'axis',
      formatter: params => {
        const p = params[0];
        return `Week of ${fmtDate(p.value[0])}: <b>${p.value[1]} workout${p.value[1]>1?'s':''}</b>`;
      },
    },
    dataZoom: [
      { type: 'inside', start: 0, end: 100 },
      { type: 'slider', bottom: 0, height: 20, borderColor: '#e5e5ea',
        fillerColor: hexAlpha('#ff6b35', 0.12),
        handleStyle: { color: '#ff6b35', borderColor: '#ff6b35' } },
    ],
    series: [{
      type: 'bar',
      name: 'Workouts',
      data: weeks.map(w => [w, weekMap[w]]),
      itemStyle: { color: hexAlpha('#ff6b35', 0.85), borderRadius: [3,3,0,0] },
      barMaxWidth: 16,
    }],
  });
}

// ══════════════════════════════════════════════════════════════════════════
// Utilities
// ══════════════════════════════════════════════════════════════════════════
function fmtDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(String(dateStr).slice(0,10) + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function fmtDateLong(ts) {
  const d = new Date(typeof ts === 'number' ? ts : String(ts).slice(0,10) + 'T00:00:00');
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
}

function fmtVal(v) {
  if (v === null || v === undefined || isNaN(v)) return '—';
  if (Math.abs(v) >= 10000) return Math.round(v).toLocaleString();
  if (Math.abs(v) >= 1000)  return Math.round(v).toLocaleString();
  if (Math.abs(v) < 10)     return parseFloat(v.toFixed(1)).toString();
  return Math.round(v).toString();
}

function avg(arr) {
  return arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
}

function mondayOf(d) {
  const day = d.getDay();
  const diff = (day === 0) ? -6 : 1 - day; // Monday = 1
  const m = new Date(d);
  m.setDate(d.getDate() + diff);
  return m.toISOString().slice(0, 10);
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

function catColor(cat) {
  return CAT_COLORS[cat] || '#007aff';
}

function hexAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function showLoading(on) {
  document.getElementById('loading').style.display = on ? 'flex' : 'none';
}

function showError(msg) {
  const el = document.getElementById('error-banner');
  el.innerHTML = msg;
  el.style.display = 'block';
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
