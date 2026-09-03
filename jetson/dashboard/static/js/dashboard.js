/**
 * ═══════════════════════════════════════════════════
 * DISASTER SENTINEL — Dashboard JavaScript
 * Real-time WebSocket updates + Chart.js visualization
 * ═══════════════════════════════════════════════════
 */

// ── Configuration ──
const WS_URL = `ws://${window.location.host}/ws`;
const API_BASE = '/api';
const MAX_CHART_POINTS = 60;
const MAX_ALERT_ITEMS = 30;

// ── State ──
let ws = null;
let charts = {};
let chartData = {
    flood: [], fire: [], landslide: []
};

// ── Hazard Mapping ──
const HAZARD_MAP = {
    'FLD1': { key: 'flood', name: 'FLOOD', color: '#3b82f6' },
    'FIR2': { key: 'fire', name: 'FIRE', color: '#f97316' },
    'SLD2': { key: 'landslide', name: 'LANDSLIDE', color: '#a78bfa' },
};

const RISK_COLORS = {
    GREEN: { bg: 'rgba(16,185,129,0.12)', text: '#10b981', class: '' },
    YELLOW: { bg: 'rgba(245,158,11,0.12)', text: '#f59e0b', class: 'yellow' },
    ORANGE: { bg: 'rgba(249,115,22,0.15)', text: '#f97316', class: 'orange' },
    RED: { bg: 'rgba(239,68,68,0.15)', text: '#ef4444', class: 'red' },
};

// ── Initialize on Load ──
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    connectWebSocket();
    startClock();
    fetchInitialData();
});

// ── Clock ──
function startClock() {
    const clockEl = document.getElementById('clock');
    function update() {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString('en-IN', { 
            hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
        }) + '  ' + now.toLocaleDateString('en-IN', { 
            day: '2-digit', month: 'short', year: 'numeric'
        });
    }
    update();
    setInterval(update, 1000);
}

// ── WebSocket Connection ──
function connectWebSocket() {
    const statusEl = document.getElementById('connection-status');
    const dotEl = statusEl.querySelector('.status-dot');
    const textEl = statusEl.querySelector('.status-text');

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        dotEl.className = 'status-dot connected';
        textEl.textContent = 'Connected';
        addAlertItem('info', 'WebSocket connected to Jetson');
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleUpdate(data);
        } catch (e) {
            console.error('WS parse error:', e);
        }
    };

    ws.onclose = () => {
        dotEl.className = 'status-dot disconnected';
        textEl.textContent = 'Disconnected';
        addAlertItem('warning', 'WebSocket disconnected — reconnecting in 3s...');
        setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => {
        dotEl.className = 'status-dot disconnected';
        textEl.textContent = 'Error';
    };
}

// ── Fetch Initial Data ──
async function fetchInitialData() {
    try {
        const [statusRes, readingsRes] = await Promise.all([
            fetch(`${API_BASE}/status`),
            fetch(`${API_BASE}/readings/latest`),
        ]);

        if (statusRes.ok) {
            const status = await statusRes.json();
            document.getElementById('nodes-online').textContent = status.nodes_online;
            document.getElementById('nodes-total').textContent = status.nodes_total;
        }

        if (readingsRes.ok) {
            const readings = await readingsRes.json();
            readings.readings.forEach(r => updateHazardCard(r));
        }
    } catch (e) {
        console.log('Initial data fetch skipped (server may not be running)');
    }
}

// ── Handle WebSocket Updates ──
function handleUpdate(data) {
    // Update node card
    if (data.node_id) {
        updateHazardCard(data);
    }

    // Update risk states
    if (data.risk_level) {
        updateRiskState(data);
    }

    // Update last packet time
    document.getElementById('last-packet-time').querySelector('span').textContent = 
        new Date().toLocaleTimeString('en-IN', { hour12: false });
}

// ── Update Hazard Card ──
function updateHazardCard(data) {
    const mapping = HAZARD_MAP[data.node_id];
    if (!mapping) return;

    const key = mapping.key;
    const prefix = key;

    // Update layer rows
    updateLayerRow(`${prefix}-l1`, data.l1_raw, data.l1_anomaly);
    updateLayerRow(`${prefix}-l2`, data.l2_raw, data.l2_anomaly);
    updateLayerRow(`${prefix}-l3`, data.l3_raw, data.l3_anomaly);

    // Update metrics
    const combinedEl = document.getElementById(`${prefix}-combined`);
    if (combinedEl) combinedEl.textContent = (data.combined_score || 0).toFixed(2);

    // Update chart
    updateChart(key, data.combined_score || 0);
}

// ── Update Risk State ──
function updateRiskState(data) {
    const mapping = HAZARD_MAP[data.node_id];
    if (!mapping) return;

    const key = mapping.key;
    const riskLevel = data.risk_level || 'GREEN';
    const riskInfo = RISK_COLORS[riskLevel] || RISK_COLORS.GREEN;

    // Update risk badge
    const badge = document.getElementById(`${key}-risk-badge`);
    if (badge) {
        badge.textContent = riskLevel;
        badge.className = `risk-badge ${riskInfo.class}`;
    }

    // Update card border
    const card = document.getElementById(`card-${key}`);
    if (card) {
        card.className = `hazard-card risk-${riskLevel.toLowerCase()}`;
        card.dataset.hazard = mapping.name;
    }

    // Update metrics
    setMetric(`${key}-confirm`, data.confirmation_level || 'NONE');
    setMetric(`${key}-prob`, `${data.probability_percent || 0}%`);
    setMetric(`${key}-severity`, data.severity || '—');
    setMetric(`${key}-eta`, data.eta_minutes ? `~${data.eta_minutes}min` : '—');
    
    const trend = data.trend || {};
    setMetric(`${key}-trend`, trend.direction === 'rising' ? '↑ Rising' : 
              trend.direction === 'falling' ? '↓ Falling' : '→ Stable');

    // Update alert channels
    if (riskLevel === 'RED') {
        updateAlertChannel('alert-sms', 'triggered', 'SENT');
        updateAlertChannel('alert-buzzer', 'triggered', 'ON');
        updateAlertChannel('alert-strobe', 'triggered', 'ON');
        addAlertItem('danger', 
            `🚨 RED ALERT: ${mapping.name} — Probability ${data.probability_percent}% — ` +
            `All 3 layers confirmed — SMS sent`);
    } else if (riskLevel === 'ORANGE') {
        updateAlertChannel('alert-buzzer', 'triggered', 'BEEP');
        addAlertItem('warning', 
            `⚠️ ORANGE: ${mapping.name} — Probability ${data.probability_percent}% — ` +
            `${data.layers_anomalous}/3 layers anomalous`);
    } else if (riskLevel === 'YELLOW') {
        addAlertItem('warning', 
            `🟡 YELLOW: ${mapping.name} — Score ${(data.combined_score||0).toFixed(2)}`);
    } else {
        // Check if all nodes are green
        updateAlertChannel('alert-buzzer', 'off', 'OFF');
        updateAlertChannel('alert-strobe', 'off', 'OFF');
    }

    // Update node count
    const onlineEl = document.getElementById('nodes-online');
    if (onlineEl) {
        // Simple: count nodes we've received data from
        const seenNodes = new Set(Object.keys(HAZARD_MAP));
        onlineEl.textContent = seenNodes.size;
        document.getElementById('nodes-total').textContent = seenNodes.size;
    }
}

// ── Helper: Update Layer Row ──
function updateLayerRow(rowId, rawValue, anomalyScore) {
    const row = document.getElementById(rowId);
    if (!row) return;

    const bar = row.querySelector('.layer-bar');
    const valueEl = row.querySelector('.layer-value');
    const scoreEl = row.querySelector('.layer-score');
    const statusEl = row.querySelector('.layer-status');

    const score = anomalyScore || 0;
    const pct = Math.min(100, Math.max(2, score * 100));

    // Update bar width and color
    bar.style.width = `${pct}%`;
    bar.className = 'layer-bar' + 
        (score > 0.75 ? ' red' : score > 0.5 ? ' orange' : score > 0.3 ? ' yellow' : '');

    // Update value display
    if (rawValue !== undefined && rawValue !== null) {
        valueEl.textContent = typeof rawValue === 'number' ? rawValue.toFixed(1) : rawValue;
    }

    // Update score
    scoreEl.textContent = score.toFixed(2);

    // Update status icon
    statusEl.textContent = score > 0.5 ? '🔴' : score > 0.3 ? '🟡' : '🟢';

    // Highlight anomalous rows
    row.className = 'layer-row' + (score > 0.5 ? ' anomalous' : '');
}

// ── Helper: Set Metric Value ──
function setMetric(id, value) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
        // Add color class for high values
        if (typeof value === 'string' && value.includes('%')) {
            const pct = parseInt(value);
            el.className = 'metric-value' + (pct > 75 ? ' high' : '');
        }
    }
}

// ── Helper: Update Alert Channel ──
function updateAlertChannel(channelId, statusClass, statusText) {
    const channel = document.getElementById(channelId);
    if (!channel) return;
    const status = channel.querySelector('.channel-status');
    if (status) {
        status.className = `channel-status ${statusClass}`;
        status.textContent = statusText;
    }
}

// ── Helper: Add Alert Feed Item ──
function addAlertItem(type, message) {
    const feed = document.getElementById('alert-feed');
    if (!feed) return;

    const time = new Date().toLocaleTimeString('en-IN', { hour12: false });
    const item = document.createElement('div');
    item.className = `alert-item ${type}`;
    item.textContent = `[${time}] ${message}`;

    // Prepend (newest on top)
    feed.insertBefore(item, feed.firstChild);

    // Limit items
    while (feed.children.length > MAX_ALERT_ITEMS) {
        feed.removeChild(feed.lastChild);
    }
}

// ══════════════════════════════════════════
// CHARTS
// ══════════════════════════════════════════

function initCharts() {
    const chartConfig = (label, color) => ({
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: color,
                backgroundColor: color + '20',
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 300 },
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    display: false,
                },
                y: {
                    min: 0,
                    max: 1,
                    ticks: {
                        color: '#64748b',
                        font: { size: 9, family: "'JetBrains Mono'" },
                        stepSize: 0.25,
                        callback: v => v.toFixed(2),
                    },
                    grid: {
                        color: 'rgba(255,255,255,0.04)',
                    },
                },
            },
        },
    });

    charts.flood = new Chart(
        document.getElementById('flood-chart'), 
        chartConfig('3-Layer Score', '#3b82f6')
    );
    charts.fire = new Chart(
        document.getElementById('fire-chart'), 
        chartConfig('3-Layer Score', '#f97316')
    );
    charts.landslide = new Chart(
        document.getElementById('landslide-chart'), 
        chartConfig('3-Layer Score', '#a78bfa')
    );
}

function updateChart(hazardKey, score) {
    const chart = charts[hazardKey];
    if (!chart) return;

    const now = new Date().toLocaleTimeString('en-IN', { hour12: false, second: '2-digit' });
    
    chart.data.labels.push(now);
    chart.data.datasets[0].data.push(score);

    // Limit data points
    if (chart.data.labels.length > MAX_CHART_POINTS) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }

    // Change color based on score
    const color = score > 0.75 ? '#ef4444' : score > 0.5 ? '#f97316' : 
                  score > 0.3 ? '#f59e0b' : HAZARD_MAP[Object.keys(HAZARD_MAP).find(
                      k => HAZARD_MAP[k].key === hazardKey)]?.color || '#6366f1';

    chart.data.datasets[0].borderColor = color;
    chart.data.datasets[0].backgroundColor = color + '20';

    chart.update('none'); // No animation for performance
}
