/**
 * Disaster Sentinel — Dashboard JavaScript
 * SPA Router, WebSocket Real-time Telemetry, Chart.js, & PyTorch GRU AI Visualization
 * SIH 2026 · Problem Statement SIH26178 · Qualcomm
 */

(function () {
    'use strict';

    // ═══════════════════════════════════════════════════════════
    // STATE & CONFIG
    // ═══════════════════════════════════════════════════════════

    const NODE_MAP = {
        'FLD1': { name: 'Flood', prefix: 'flood', color: '#00f2fe', layers: 3 },
        'SLD2': { name: 'Landslide', prefix: 'landslide', color: '#f6d365', layers: 3 },
        'FIR3': { name: 'Fire', prefix: 'fire', color: '#ff0844', layers: 3 },
        'POL4': { name: 'Pollution', prefix: 'pollution', color: '#b57bee', layers: 2 },
    };

    let ws = null;
    let currentView = 'overview';
    let charts = {};
    let latestData = {};
    let nodeHistory = { FLD1: [], SLD2: [], FIR3: [], POL4: [] };
    let alertLog = [];

    // ═══════════════════════════════════════════════════════════
    // SPA ROUTER
    // ═══════════════════════════════════════════════════════════

    function initRouter() {
        window.addEventListener('hashchange', handleRoute);
        handleRoute();
    }

    function handleRoute() {
        const hash = window.location.hash.replace('#', '') || 'overview';
        const validViews = ['overview', 'flood', 'landslide', 'fire', 'pollution', 'alerts'];
        currentView = validViews.includes(hash) ? hash : 'overview';

        // Update DOM view visibility
        document.querySelectorAll('.spa-view').forEach(view => {
            view.classList.remove('active-view');
        });
        const targetView = document.getElementById(`view-${currentView}`);
        if (targetView) {
            targetView.classList.add('active-view');
        }

        // Update Sidebar active state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        const activeNav = document.getElementById(`nav-${currentView}`);
        if (activeNav) {
            activeNav.classList.add('active');
        }

        // Update Header Titles
        updateHeaderTitle(currentView);

        // Fetch predictions and initialize charts for active view
        if (currentView === 'overview') {
            initOverviewChart();
        } else if (NODE_MAP[getNodeIdFromView(currentView)]) {
            const nodeId = getNodeIdFromView(currentView);
            initDetailChart(nodeId);
            fetchPredictions(nodeId);
        }
    }

    function getNodeIdFromView(view) {
        const mapping = { 'flood': 'FLD1', 'landslide': 'SLD2', 'fire': 'FIR3', 'pollution': 'POL4' };
        return mapping[view] || null;
    }

    function updateHeaderTitle(view) {
        const titles = {
            'overview': { title: 'Overview Command Center', sub: 'Real-time multi-hazard telemetry & PyTorch GRU AI predictive forecasting' },
            'flood': { title: '🌊 Flood Monitoring Command (FLD1)', sub: '3-Layer Validation · Water Level + Rain Rate + Barometric Pressure' },
            'landslide': { title: '⛰️ Landslide Monitoring Command (SLD2)', sub: '3-Layer Validation · Accelerometer Tilt + Soil Moisture + Pressure' },
            'fire': { title: '🔥 Fire Monitoring Command (FIR3)', sub: '3-Layer Validation · Flame IR + Smoke/Gas + Temperature' },
            'pollution': { title: '🏭 Air Pollution Command (POL4)', sub: '2-Layer Mode · MQ-135 Air Quality Index + PM2.5 Dust Concentration' },
            'alerts': { title: '🔔 System Alert Audit Log', sub: 'Historical and active multi-hazard alert audit feed' }
        };

        const t = titles[view] || titles['overview'];
        document.getElementById('page-title').textContent = t.title;
        document.getElementById('page-subtitle').textContent = t.sub;
    }

    // ═══════════════════════════════════════════════════════════
    // WEBSOCKET REAL-TIME TELEMETRY
    // ═══════════════════════════════════════════════════════════

    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('[WS] Connected to Disaster Sentinel Server');
            updateConnectionStatus(true);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleIncomingPacket(data);
            } catch (err) {
                console.error('[WS] Error parsing message:', err);
            }
        };

        ws.onclose = () => {
            console.warn('[WS] Disconnected — retrying in 3s...');
            updateConnectionStatus(false);
            setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (err) => {
            console.error('[WS] Socket error:', err);
            ws.close();
        };
    }

    function updateConnectionStatus(online) {
        const statusEl = document.getElementById('ws-status');
        if (!statusEl) return;
        const dot = statusEl.querySelector('.status-dot');
        const text = statusEl.querySelector('.status-text');

        if (online) {
            dot.className = 'status-dot';
            text.textContent = 'Live System Connected';
        } else {
            dot.className = 'status-dot offline';
            text.textContent = 'Disconnected (Reconnecting...)';
        }
    }

    function handleIncomingPacket(packet) {
        const nodeId = packet.node_id;
        if (!nodeId || !NODE_MAP[nodeId]) return;

        latestData[nodeId] = packet;

        // Add to local time-series history
        if (!nodeHistory[nodeId]) nodeHistory[nodeId] = [];
        nodeHistory[nodeId].push({
            timestamp: new Date().toLocaleTimeString(),
            score: packet.combined_score || 0,
            l1_raw: packet.l1_raw || 0,
            l2_raw: packet.l2_raw || 0,
            l3_raw: packet.l3_raw || 0,
            l1_anomaly: packet.l1_anomaly || 0,
            l2_anomaly: packet.l2_anomaly || 0,
            l3_anomaly: packet.l3_anomaly || 0,
        });

        if (nodeHistory[nodeId].length > 30) {
            nodeHistory[nodeId].shift();
        }

        // Update Overview Tile
        updateOverviewTile(nodeId, packet);

        // Update Active Detail View if currently viewing this node
        const activeNodeId = getNodeIdFromView(currentView);
        if (activeNodeId === nodeId) {
            updateDetailView(nodeId, packet);
        }

        // Update Overview Gauge & Timeline Chart if in Overview view
        if (currentView === 'overview') {
            updateOverallGauge();
            updateOverviewChart();
        }

        // Update Last Packet Timer
        document.getElementById('last-packet-timer').textContent = new Date().toLocaleTimeString();

        // Process Alerts if present
        if (packet.risk_level && packet.risk_level !== 'GREEN') {
            addAlertToFeed(packet);
        }
    }

    // ═══════════════════════════════════════════════════════════
    // UI UPDATERS
    // ═══════════════════════════════════════════════════════════

    function updateOverviewTile(nodeId, packet) {
        const info = NODE_MAP[nodeId];
        const prefix = info.prefix;

        // Combined Score
        const scoreEl = document.getElementById(`tile-${prefix}-score`);
        if (scoreEl) {
            scoreEl.textContent = (packet.combined_score || 0).toFixed(2);
        }

        // Status Badge
        const badgeEl = document.getElementById(`tile-${prefix}-badge`);
        if (badgeEl) {
            const risk = packet.risk_level || 'GREEN';
            badgeEl.className = `status-badge ${risk.toLowerCase()}`;
            badgeEl.textContent = risk;
        }

        // Mini Layer Progress Bars
        const l1Bar = document.getElementById(`tile-${prefix}-l1`);
        if (l1Bar) l1Bar.style.width = `${Math.max(5, (packet.l1_anomaly || 0) * 100)}%`;

        const l2Bar = document.getElementById(`tile-${prefix}-l2`);
        if (l2Bar) l2Bar.style.width = `${Math.max(5, (packet.l2_anomaly || 0) * 100)}%`;

        if (info.layers >= 3) {
            const l3Bar = document.getElementById(`tile-${prefix}-l3`);
            if (l3Bar) l3Bar.style.width = `${Math.max(5, (packet.l3_anomaly || 0) * 100)}%`;
        }
    }

    function updateOverallGauge() {
        let maxScore = 0;
        let activeCount = 0;

        Object.keys(NODE_MAP).forEach(nid => {
            if (latestData[nid]) {
                activeCount++;
                const s = latestData[nid].combined_score || 0;
                if (s > maxScore) maxScore = s;
            }
        });

        document.getElementById('nodes-online-count').textContent = activeCount;

        const gauge = document.getElementById('overall-risk-gauge');
        const percentEl = document.getElementById('overall-risk-percent');
        const labelEl = document.getElementById('overall-risk-label');
        const descEl = document.getElementById('overall-risk-desc');

        if (gauge && percentEl) {
            const pct = (maxScore * 100).toFixed(1);
            percentEl.textContent = `${pct}%`;
            gauge.style.setProperty('--score', Math.max(0.05, maxScore));

            let riskLabel = 'LOW';
            let color = 'var(--risk-green)';
            let desc = 'All 4 sensor nodes operating within safe thresholds';

            if (maxScore >= 0.75) {
                riskLabel = 'CRITICAL / RED';
                color = 'var(--risk-red)';
                desc = '⚠️ CRITICAL DISASTER ALERT: 3/3 confirmation threshold exceeded';
            } else if (maxScore >= 0.55) {
                riskLabel = 'HIGH / ORANGE';
                color = 'var(--risk-orange)';
                desc = '⚠️ HIGH RISK ALERT: Multi-layer corroborating anomalies detected';
            } else if (maxScore >= 0.40) {
                riskLabel = 'MEDIUM / YELLOW';
                color = 'var(--risk-yellow)';
                desc = '⚡ MODERATE ELEVATION: Sensor anomalies monitored';
            }

            labelEl.textContent = riskLabel;
            labelEl.style.color = color;
            descEl.textContent = desc;
        }
    }

    function updateDetailView(nodeId, packet) {
        const info = NODE_MAP[nodeId];
        const p = info.prefix;

        // Status Badge
        const statusEl = document.getElementById(`${p}-detail-status`);
        if (statusEl) {
            const r = packet.risk_level || 'GREEN';
            statusEl.className = `status-badge ${r.toLowerCase()} lg`;
            statusEl.textContent = r;
        }

        // Layer 1
        setLayerDetail(`${p}-dl1`, packet.l1_raw, packet.l1_anomaly);
        // Layer 2
        setLayerDetail(`${p}-dl2`, packet.l2_raw, packet.l2_anomaly);

        // Layer 3 (only if 3-layer node)
        if (info.layers >= 3) {
            setLayerDetail(`${p}-dl3`, packet.l3_raw, packet.l3_anomaly);
        }

        // Update Detail Chart
        updateDetailChart(nodeId);
    }

    function setLayerDetail(elemId, rawVal, anomalyVal) {
        const card = document.getElementById(elemId);
        if (!card) return;

        const rawEl = card.querySelector('.ld-val');
        const barEl = card.querySelector('.ld-bar');
        const scoreEl = card.querySelector('strong');
        const statusEl = card.querySelector('.ld-foot span:last-child');

        if (rawEl) rawEl.textContent = (rawVal !== undefined && rawVal !== null) ? rawVal.toFixed(1) : '—';
        if (scoreEl) scoreEl.textContent = (anomalyVal || 0).toFixed(2);
        if (barEl) barEl.style.width = `${Math.max(5, (anomalyVal || 0) * 100)}%`;

        if (statusEl) {
            if (anomalyVal >= 0.60) {
                statusEl.textContent = '🔴 Anomalous';
                statusEl.style.color = 'var(--risk-red)';
            } else if (anomalyVal >= 0.35) {
                statusEl.textContent = '🟡 Elevated';
                statusEl.style.color = 'var(--risk-yellow)';
            } else {
                statusEl.textContent = '🟢 Normal';
                statusEl.style.color = 'var(--risk-green)';
            }
        }
    }

    // ═══════════════════════════════════════════════════════════
    // AI PREDICTION RENDERER
    // ═══════════════════════════════════════════════════════════

    async function fetchPredictions(nodeId) {
        try {
            const res = await fetch(`/api/predictions/${nodeId}`);
            if (!res.ok) return;
            const data = await res.json();
            renderPredictions(nodeId, data.predictions);
        } catch (err) {
            console.error(`Failed to fetch predictions for ${nodeId}:`, err);
        }
    }

    function renderPredictions(nodeId, preds) {
        if (!preds) return;
        const info = NODE_MAP[nodeId];
        const p = info.prefix;

        const horizons = ['t15', 't30', 't60'];
        horizons.forEach(h => {
            const item = preds[h];
            if (!item) return;

            const probEl = document.getElementById(`${p}-${h}-prob`);
            const sevEl = document.getElementById(`${p}-${h}-sev`);
            const trajEl = document.getElementById(`${p}-${h}-traj`);
            const cardEl = document.getElementById(`${p}-ai-${h}`);

            if (probEl) {
                const pct = (item.probability * 100).toFixed(1);
                probEl.textContent = `${pct}%`;
            }

            if (sevEl) {
                sevEl.textContent = item.severity;
                sevEl.className = `ai-sev-tag ${item.severity.toLowerCase()}`;
                if (item.severity === 'CRITICAL') sevEl.style.backgroundColor = 'rgba(239, 68, 68, 0.3)';
                else if (item.severity === 'HIGH') sevEl.style.backgroundColor = 'rgba(249, 115, 22, 0.3)';
                else if (item.severity === 'MEDIUM') sevEl.style.backgroundColor = 'rgba(245, 158, 11, 0.3)';
                else sevEl.style.backgroundColor = 'rgba(16, 185, 129, 0.3)';
            }

            if (trajEl) {
                let symbol = '➔ Stable';
                if (preds.trajectory === 'escalating') symbol = '↗ Escalating';
                else if (preds.trajectory === 'declining') symbol = '↘ Declining';
                trajEl.textContent = symbol;
            }

            // Also update tile preview if T15
            if (h === 't15') {
                const tileAi = document.getElementById(`tile-${p}-ai`);
                if (tileAi) {
                    tileAi.textContent = `${item.severity} (${(item.probability * 100).toFixed(1)}%)`;
                }
            }
        });
    }

    // ═══════════════════════════════════════════════════════════
    // CHART.JS MANAGERS
    // ═══════════════════════════════════════════════════════════

    function initOverviewChart() {
        const ctx = document.getElementById('overview-timeline-chart');
        if (!ctx) return;

        if (charts['overview']) return; // already initialized

        charts['overview'] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Flood (FLD1)', data: [], borderColor: '#00f2fe', backgroundColor: 'rgba(0, 242, 254, 0.1)', tension: 0.3, fill: true },
                    { label: 'Landslide (SLD2)', data: [], borderColor: '#f6d365', backgroundColor: 'transparent', tension: 0.3 },
                    { label: 'Fire (FIR3)', data: [], borderColor: '#ff0844', backgroundColor: 'transparent', tension: 0.3 },
                    { label: 'Pollution (POL4)', data: [], borderColor: '#b57bee', backgroundColor: 'transparent', tension: 0.3 },
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                    y: { min: 0, max: 1, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } }
                }
            }
        });
    }

    function updateOverviewChart() {
        const chart = charts['overview'];
        if (!chart) return;

        const maxLen = Math.max(
            nodeHistory.FLD1.length, nodeHistory.SLD2.length,
            nodeHistory.FIR3.length, nodeHistory.POL4.length
        );

        if (maxLen === 0) return;

        const labels = nodeHistory.FLD1.map(h => h.timestamp);
        chart.data.labels = labels;

        chart.data.datasets[0].data = nodeHistory.FLD1.map(h => h.score);
        chart.data.datasets[1].data = nodeHistory.SLD2.map(h => h.score);
        chart.data.datasets[2].data = nodeHistory.FIR3.map(h => h.score);
        chart.data.datasets[3].data = nodeHistory.POL4.map(h => h.score);

        chart.update('quiet');
    }

    function initDetailChart(nodeId) {
        const info = NODE_MAP[nodeId];
        const p = info.prefix;
        const canvasId = `${p}-detail-chart`;
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (charts[nodeId]) return;

        const datasets = [
            { label: 'L1 Primary Anomaly', data: [], borderColor: info.color, tension: 0.3 },
            { label: 'L2 Corroborating Anomaly', data: [], borderColor: '#f59e0b', tension: 0.3 },
        ];

        if (info.layers >= 3) {
            datasets.push({ label: 'L3 Context Anomaly', data: [], borderColor: '#3b82f6', tension: 0.3 });
        }

        datasets.push({ label: 'Combined 3-Layer Score', data: [], borderColor: '#ef4444', borderDash: [4, 4], tension: 0.3 });

        charts[nodeId] = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#94a3b8' } } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                    y: { min: 0, max: 1, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } }
                }
            }
        });
    }

    function updateDetailChart(nodeId) {
        const chart = charts[nodeId];
        if (!chart) return;

        const hist = nodeHistory[nodeId] || [];
        chart.data.labels = hist.map(h => h.timestamp);
        chart.data.datasets[0].data = hist.map(h => h.l1_anomaly);
        chart.data.datasets[1].data = hist.map(h => h.l2_anomaly);

        if (NODE_MAP[nodeId].layers >= 3) {
            chart.data.datasets[2].data = hist.map(h => h.l3_anomaly);
            chart.data.datasets[3].data = hist.map(h => h.score);
        } else {
            chart.data.datasets[2].data = hist.map(h => h.score);
        }

        chart.update('quiet');
    }

    // ═══════════════════════════════════════════════════════════
    // ALERT FEED & CLOCK
    // ═══════════════════════════════════════════════════════════

    function addAlertToFeed(packet) {
        const feed = document.getElementById('alerts-page-feed');
        if (!feed) return;

        const row = document.createElement('div');
        const level = (packet.risk_level || 'INFO').toLowerCase();
        row.className = `alert-row ${level}`;
        row.innerHTML = `
            <div>
                <strong>[${packet.node_id}] ${packet.hazard_name} ALERT — ${packet.risk_level}</strong>
                <div style="font-size: 11px; color: var(--text-muted);">
                    Confirmation: ${packet.confirmation_level || 'HIGH'} | Combined Score: ${(packet.combined_score || 0).toFixed(2)}
                </div>
            </div>
            <div style="font-family: var(--font-mono); font-size: 11px;">${new Date().toLocaleTimeString()}</div>
        `;

        feed.insertBefore(row, feed.firstChild);
        const countEl = document.getElementById('nav-alert-count');
        if (countEl) countEl.textContent = feed.children.length;
    }

    function initClock() {
        const clockEl = document.getElementById('clock-display');
        if (!clockEl) return;
        setInterval(() => {
            clockEl.textContent = new Date().toLocaleTimeString();
        }, 1000);
    }

    // ═══════════════════════════════════════════════════════════
    // INIT
    // ═══════════════════════════════════════════════════════════

    document.addEventListener('DOMContentLoaded', () => {
        initRouter();
        connectWebSocket();
        initClock();
    });

})();
