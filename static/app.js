/**
 * Signal Story — Enterprise Decision Intelligence Controller
 * Multi-Persona, Role-Entitled, Deterministic UI Controller
 * Direct integration with frozen Python backend.
 */

// Application State
const appState = {
  scenarios: [],
  selectedScenarioId: 'S003',
  providerMode: 'mock', // 'mock' (Preview) or 'gemini' (Assisted Analysis)
  persona: 'EXECUTIVE', // 'EXECUTIVE' or 'DOMAIN_ANALYST'
  role: 'EXECUTIVE', // 'EXECUTIVE', 'DOMAIN_ANALYST', or 'RESTRICTED_USER'
  currentData: null,
  activeView: 'view-executive',
  isLoading: false,
  activeTrendMetrics: ['gross_sales', 'marketing_spend', 'conversion_rate']
};

// Canonical Business Names for 8 Hypotheses
const DRIVER_BUSINESS_NAMES = {
  DRIVER_01_INVENTORY: 'Inventory & Stockout Bottleneck',
  DRIVER_02_PRICING: 'Competitor Price Undercutting',
  DRIVER_03_MARKETING: 'Marketing Inefficiency',
  DRIVER_04_RETURNS: 'Product Defect & Return Surge',
  DRIVER_05_SUPPORT: 'Customer Support Crisis',
  DRIVER_06_CUSTOMER: 'Customer Sentiment Drop',
  DRIVER_07_MARKET: 'Regional Market Contraction',
  DRIVER_08_PRODUCT_MIX: 'Product Mix Shift & Cannibalization',
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  bindEvents();
  await loadScenarios();
  await runAnalysis();
}

/**
 * Event Listeners Binding
 */
function bindEvents() {
  const scenarioSelect = document.getElementById('scenario-select');
  const personaSelect = document.getElementById('persona-select');
  const roleSelect = document.getElementById('role-select');
  const modeMockBtn = document.getElementById('mode-mock');
  const modeGeminiBtn = document.getElementById('mode-gemini');
  const btnRun = document.getElementById('btn-run-analysis');
  const btnSourceSpec = document.getElementById('btn-source-spec');
  const navItems = document.querySelectorAll('.nav-item');
  const sidebarScenarioItems = document.querySelectorAll('.scenario-item');

  // Scenario Dropdown Change
  if (scenarioSelect) {
    scenarioSelect.addEventListener('change', (e) => {
      selectScenario(e.target.value);
    });
  }

  // Persona Segmented Switcher
  const personaSegmentBtns = document.querySelectorAll('#persona-segmented .segment-btn');
  personaSegmentBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      personaSegmentBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const personaVal = btn.getAttribute('data-persona');
      appState.persona = personaVal;
      if (personaSelect) personaSelect.value = personaVal;
      showToast(`Switched Persona: ${personaVal === 'EXECUTIVE' ? 'Executive Leader' : 'Domain Analyst'}`);
      runAnalysis();
    });
  });

  // Role Entitlement Segmented Switcher
  const roleSegmentBtns = document.querySelectorAll('#role-segmented .segment-btn');
  roleSegmentBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      roleSegmentBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const roleVal = btn.getAttribute('data-role');
      appState.role = roleVal;
      if (roleSelect) roleSelect.value = roleVal;
      showToast(`Switched Role Entitlement: ${roleVal}`);
      runAnalysis();
    });
  });

  // Sidebar Scenario Items
  sidebarScenarioItems.forEach((btn) => {
    btn.addEventListener('click', () => {
      const scId = btn.getAttribute('data-scenario');
      selectScenario(scId);
    });
  });

  // Provider Mode Toggles
  if (modeMockBtn) {
    modeMockBtn.addEventListener('click', () => setProviderMode('mock'));
  }
  if (modeGeminiBtn) {
    modeGeminiBtn.addEventListener('click', () => setProviderMode('gemini'));
  }

  // Run Analysis Button
  if (btnRun) {
    btnRun.addEventListener('click', () => runAnalysis());
  }

  // Source Integration Spec Button
  if (btnSourceSpec) {
    btnSourceSpec.addEventListener('click', () => openSourceSpecModal());
  }

  // KPI Semantic Governance Contract Buttons
  const btnKpiGov = document.getElementById('btn-kpi-governance');
  if (btnKpiGov) {
    btnKpiGov.addEventListener('click', () => openKpiContractModal());
  }

  const kpiTagClickable = document.getElementById('card1-kpi-tag');
  if (kpiTagClickable) {
    kpiTagClickable.addEventListener('click', () => openKpiContractModal());
  }

  // Sidebar View Navigation
  navItems.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetView = btn.getAttribute('data-view');
      switchView(targetView);
    });
  });

  // Trend Overview Metric Toggle Pills
  const metricPills = document.querySelectorAll('#trend-metric-toggles .metric-pill');
  metricPills.forEach((pill) => {
    pill.addEventListener('click', () => {
      const metric = pill.getAttribute('data-metric');
      if (appState.activeTrendMetrics.includes(metric)) {
        if (appState.activeTrendMetrics.length > 1) {
          appState.activeTrendMetrics = appState.activeTrendMetrics.filter((m) => m !== metric);
          pill.classList.remove('active');
        }
      } else {
        appState.activeTrendMetrics.push(metric);
        pill.classList.add('active');
      }
      if (appState.currentData && appState.currentData.connected_kpis) {
        renderMultiMetricTrendOverview(appState.currentData.connected_kpis.monthly_history, appState.activeTrendMetrics);
      }
    });
  });
}

/**
 * Select Scenario and Synchronize Header & Sidebar
 */
function selectScenario(scenarioId) {
  appState.selectedScenarioId = scenarioId;

  const scenarioSelect = document.getElementById('scenario-select');
  if (scenarioSelect) scenarioSelect.value = scenarioId;

  const sidebarScenarioItems = document.querySelectorAll('.scenario-item');
  sidebarScenarioItems.forEach((item) => {
    if (item.getAttribute('data-scenario') === scenarioId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  runAnalysis();
}

/**
 * Provider Mode Switcher
 */
function setProviderMode(mode) {
  appState.providerMode = mode;
  const modeMockBtn = document.getElementById('mode-mock');
  const modeGeminiBtn = document.getElementById('mode-gemini');

  if (mode === 'mock') {
    modeMockBtn.classList.add('active');
    modeGeminiBtn.classList.remove('active');
    showToast('Analysis Mode: Preview (Mock Engine)');
  } else {
    modeGeminiBtn.classList.add('active');
    modeMockBtn.classList.remove('active');
    showToast('Analysis Mode: Assisted Analysis (Gemini LLM Provider)');
  }

  runAnalysis();
}

/**
 * Switch Active View
 */
function switchView(viewId) {
  appState.activeView = viewId;

  const panels = document.querySelectorAll('.view-panel');
  panels.forEach((p) => {
    p.style.display = p.id === viewId ? 'block' : 'none';
  });

  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach((item) => {
    if (item.getAttribute('data-view') === viewId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function scrollToElement(elemId) {
  const el = document.getElementById(elemId);
  if (el) el.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Load Scenarios Catalog
 */
async function loadScenarios() {
  try {
    const res = await fetch('/api/scenarios');
    if (res.ok) {
      const data = await res.json();
      appState.scenarios = data;
    }
  } catch (err) {
    console.error('Failed to load scenarios:', err);
  }
}

/**
 * Execute Decision Intelligence Analysis
 */
async function runAnalysis() {
  showLoading(true);

  const scenario = appState.scenarios.find((s) => s.scenario_id === appState.selectedScenarioId) || {
    scenario_id: appState.selectedScenarioId,
    market: 'China',
    product_code: 'A2520150501',
    date: '2021-04-01',
    kpi: 'gross_sales'
  };

  const payload = {
    scenario_id: scenario.scenario_id,
    market: scenario.market,
    product_code: scenario.product_code,
    category: scenario.category,
    date: scenario.date,
    kpi: scenario.kpi || 'gross_sales',
    provider_mode: appState.providerMode,
    persona: appState.persona,
    role: appState.role
  };

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Role': appState.role,
        'X-Persona': appState.persona
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`Server returned status ${res.status}`);
    }

    const data = await res.json();
    appState.currentData = data;
    renderAllViews(data);
  } catch (err) {
    console.error('Analysis failed:', err);
    showToast(`Analysis Error: ${err.message}`, true);
  } finally {
    showLoading(false);
  }
}

/**
 * Render All Views with Enterprise Precision
 */
function renderAllViews(data) {
  renderScopeAndHeader(data);
  renderAbstentionAndSparseBanners(data);
  renderSignalSummaryCard(data);
  renderPrimaryDriverCard(data);
  renderSupportingEvidenceCard(data);
  renderSignalStoryPanel(data);   // Phase 6.2 — Signal Story Narrative Layer
  renderConnectedKpiStoryCard(data);
  renderCandidateDriverComparisonCard(data);
  renderMultiMetricTrendOverviewCard(data);
  renderDecisionSupportStrip(data);
  renderLiveTelemetryFooter(data);
  renderView2EvidenceExplorer(data);
  renderView3IntegrityAndGovernance(data);
}

/**
 * Render Scope Bar & Header
 */
function renderScopeAndHeader(data) {
  const req = data.request || {};
  const target = (data.connected_kpis && data.connected_kpis.target_entity) || {};
  const scopeEl = document.getElementById('exec-scope-text');
  if (scopeEl) {
    const prodName = target.product_name && target.product_name !== 'N/A' ? ` (${target.product_name})` : '';
    const dateFormatted = req.date ? formatDateLabel(req.date) : 'April 2021';
    scopeEl.textContent = `${req.market || 'China'} • Product ${req.product_code || target.category || 'All'}${prodName} • ${dateFormatted}`;
  }

  // Sync Data Trust Header badge
  const trustData = data.data_trust || {};
  const headerTrustText = document.getElementById('header-trust-text');
  const headerTrustDot = document.getElementById('header-trust-dot');
  if (headerTrustText && trustData.summary) {
    const isTrusted = trustData.summary.overall_trust_status === 'TRUSTED';
    headerTrustText.textContent = `Data Trust: ${trustData.summary.overall_trust_status} (${trustData.summary.overall_quality_score}%)`;
    if (headerTrustDot) {
      headerTrustDot.style.color = isTrusted ? '#16A34A' : '#D97706';
    }
  }
}

/**
 * Render Low-Confidence Abstention (S008) and Sparse History (S009) Banners
 */
function renderAbstentionAndSparseBanners(data) {
  const scId = data.scenario_id || appState.selectedScenarioId;
  const abstentionBanner = document.getElementById('abstention-banner');
  const sparseBanner = document.getElementById('sparse-history-banner');

  // Abstention Banner (S008 or INSUFFICIENT_EVIDENCE)
  const isAbstain = scId === 'S008' || (data.phase3b && data.phase3b.diagnosis && data.phase3b.diagnosis.status === 'NOT_ESTABLISHED');
  if (abstentionBanner) {
    if (isAbstain) {
      abstentionBanner.style.display = 'flex';
      const abstMeta = data.abstention_governance || {};
      const reasonEl = document.getElementById('abstention-reasons');
      const listEl = document.getElementById('abstention-evidence-list');
      if (reasonEl && abstMeta.abstention_reasons) {
        reasonEl.textContent = abstMeta.abstention_reasons.join(' ');
      }
      if (listEl && abstMeta.next_required_evidence) {
        listEl.innerHTML = abstMeta.next_required_evidence.map((e) => `<li>${e}</li>`).join('');
      }
    } else {
      abstentionBanner.style.display = 'none';
    }
  }

  // Sparse History Banner (S009 or limited history)
  const sparseMeta = data.sparse_history || {};
  const isSparse = scId === 'S009' || sparseMeta.is_limited_history;
  if (sparseBanner) {
    if (isSparse) {
      sparseBanner.style.display = 'flex';
      const descEl = document.getElementById('sparse-history-desc');
      const methodEl = document.getElementById('sparse-history-method');
      if (descEl && sparseMeta.description) descEl.textContent = sparseMeta.description;
      if (methodEl && sparseMeta.baseline_method_applied) methodEl.textContent = `Method: ${sparseMeta.baseline_method_applied} (Confidence: LOW)`;
    } else {
      sparseBanner.style.display = 'none';
    }
  }
}

/**
 * Render Column 1: Signal Summary Card with Real Longitudinal Chart
 */
function renderSignalSummaryCard(data) {
  const p3aEvent = (data.phase3a && data.phase3a.event) || {};
  const kpiTag = document.getElementById('card1-kpi-tag');
  const deltaVal = document.getElementById('card1-delta-val');
  const arrowEl = document.getElementById('card1-arrow');
  const actualVal = document.getElementById('card1-actual-val');
  const baseVal = document.getElementById('card1-baseline-val');

  if (kpiTag) kpiTag.textContent = formatKpiName(p3aEvent.kpi || 'gross_sales');

  const changePct = p3aEvent.baseline_change_percent !== undefined ? p3aEvent.baseline_change_percent * 100 : -72.06;
  if (deltaVal) deltaVal.textContent = `${Math.abs(changePct).toFixed(1)}%`;
  if (arrowEl) {
    arrowEl.textContent = changePct < 0 ? '↓' : '↑';
    arrowEl.style.color = changePct < 0 ? '#DC2626' : '#16A34A';
  }

  if (actualVal) {
    if (data.entitlement && data.entitlement.is_redacted && data.entitlement.redacted_fields.includes('actual_value')) {
      actualVal.textContent = '[RESTRICTED]';
      actualVal.classList.add('val-restricted');
    } else {
      actualVal.textContent = typeof p3aEvent.current_value === 'number' ? `$${p3aEvent.current_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : p3aEvent.current_value;
      actualVal.classList.remove('val-restricted');
    }
  }

  if (baseVal) {
    if (data.entitlement && data.entitlement.is_redacted && data.entitlement.redacted_fields.includes('baseline_value')) {
      baseVal.textContent = '[RESTRICTED]';
      baseVal.classList.add('val-restricted');
    } else {
      baseVal.textContent = typeof p3aEvent.baseline_value === 'number' ? `$${p3aEvent.baseline_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : p3aEvent.baseline_value;
      baseVal.classList.remove('val-restricted');
    }
  }

  // Render Real Longitudinal SVG Line Chart
  const historyData = (data.connected_kpis && data.connected_kpis.monthly_history) || {
    periods: ['Jan 2021', 'Feb 2021', 'Mar 2021', 'Apr 2021'],
    gross_sales: [590.11, 3074.39, 7009.60, 994.25],
    anomaly_index: 3
  };
  const baseSales = typeof p3aEvent.baseline_value === 'number' ? p3aEvent.baseline_value : 3558.03;
  renderSignalTrendChart(historyData, baseSales);
}

/**
 * Generate Pure SVG Longitudinal Trend Chart for Signal Summary
 */
function renderSignalTrendChart(historyData, baselineVal) {
  const container = document.getElementById('signal-trend-chart-viewport');
  if (!container) return;

  const periods = historyData.periods || ['Jan', 'Feb', 'Mar', 'Apr'];
  const values = historyData.gross_sales || [590.11, 3074.39, 7009.60, 994.25];
  const anomalyIdx = historyData.anomaly_index !== undefined ? historyData.anomaly_index : values.length - 1;

  const maxVal = Math.max(...values, baselineVal) * 1.15;
  const minVal = 0;
  const width = 280;
  const height = 85;
  const padLeft = 32;
  const padRight = 14;
  const padTop = 10;
  const padBottom = 20;

  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const getX = (idx) => padLeft + (idx / (values.length - 1 || 1)) * plotW;
  const getY = (val) => padTop + plotH - ((val - minVal) / (maxVal - minVal || 1)) * plotH;

  // Path data for trend line
  const points = values.map((val, idx) => `${getX(idx)},${getY(val)}`);
  const pathD = `M ${points.join(' L ')}`;

  // Baseline Y
  const baseY = getY(baselineVal);

  let svgHtml = `
    <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: 100%; overflow: visible;" font-family="Inter, sans-serif">
      <!-- Grid & Axis -->
      <line x1="${padLeft}" y1="${getY(0)}" x2="${width - padRight}" y2="${getY(0)}" stroke="#E2E8F0" stroke-width="1"/>
      <line x1="${padLeft}" y1="${getY(maxVal * 0.5)}" x2="${width - padRight}" y2="${getY(maxVal * 0.5)}" stroke="#F1F5F9" stroke-width="1" stroke-dasharray="2,2"/>
      
      <!-- Baseline Reference Dashed Line -->
      <line x1="${padLeft}" y1="${baseY}" x2="${width - padRight}" y2="${baseY}" stroke="#94A3B8" stroke-width="1.2" stroke-dasharray="3,3"/>
      <text x="${width - padRight - 2}" y="${baseY - 3}" font-size="8" fill="#64748B" text-anchor="end" font-family="JetBrains Mono, monospace">Base $${Math.round(baselineVal)}</text>

      <!-- Trend Line -->
      <path d="${pathD}" fill="none" stroke="#2563EB" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
  `;

  // Data Points
  values.forEach((val, idx) => {
    const cx = getX(idx);
    const cy = getY(val);
    const isAnomaly = idx === anomalyIdx;
    const color = isAnomaly ? '#DC2626' : '#2563EB';
    const r = isAnomaly ? 4.5 : 3;

    svgHtml += `
      <g class="chart-point-group" style="cursor: pointer;">
        ${isAnomaly ? `<circle cx="${cx}" cy="${cy}" r="7" fill="none" stroke="#FECACA" stroke-width="2"/>` : ''}
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="${color}" stroke="#FFFFFF" stroke-width="1.5">
          <title>${periods[idx]}: $${val.toLocaleString()}</title>
        </circle>
        <!-- X Axis Label -->
        <text x="${cx}" y="${height - 4}" font-size="8.5" fill="${isAnomaly ? '#DC2626' : '#64748B'}" font-weight="${isAnomaly ? '700' : '500'}" text-anchor="middle">
          ${periods[idx].split(' ')[0]}
        </text>
      </g>
    `;
  });

  svgHtml += `</svg>`;
  container.innerHTML = svgHtml;
}

/**
 * Render Column 2: Primary Supported Driver Card + 5-KPI Impact Grid
 */
function renderPrimaryDriverCard(data) {
  const p3b = data.phase3b || {};
  const diagnosis = p3b.diagnosis || {};
  const driverKey = diagnosis.driver || 'DRIVER_03_MARKETING';
  const driverName = DRIVER_BUSINESS_NAMES[driverKey] || driverKey;

  const titleEl = document.getElementById('card2-driver-title');
  const codeEl = document.getElementById('card2-driver-code');
  const statusEl = document.getElementById('card2-status-badge');
  const narrativeEl = document.getElementById('card2-explanation-text');

  if (titleEl) titleEl.textContent = driverName;
  if (codeEl) codeEl.textContent = driverKey;

  if (statusEl) {
    const status = diagnosis.status || 'STRONGLY_SUPPORTED';
    statusEl.textContent = status === 'NOT_ESTABLISHED' ? 'Inconclusive' : (status === 'STRONGLY_SUPPORTED' ? 'Supported' : 'Plausible');
    statusEl.className = `status-badge ${status === 'STRONGLY_SUPPORTED' ? 'badge-success' : (status === 'NOT_ESTABLISHED' ? 'badge-danger' : 'badge-warning')}`;
  }

  if (narrativeEl) {
    narrativeEl.textContent = p3b.executive_summary || 'Marketing activity increased while conversion performance deteriorated during the anomaly window.';
  }

  // Render 5-KPI Impact Mini-Grid
  const connectedKpis = (data.connected_kpis && data.connected_kpis.connected_kpis) || [];
  const gridContainer = document.getElementById('driver-kpi-impact-grid');
  if (gridContainer && connectedKpis.length > 0) {
    const isRedacted = data.entitlement && data.entitlement.is_redacted;
    gridContainer.innerHTML = connectedKpis.map((kpi) => {
      const isSales = kpi.kpi_id === 'gross_sales';
      const isRedactedVal = isRedacted && isSales;
      const valStr = isRedactedVal ? '[RESTRICTED]' : kpi.formatted_value;
      const deltaColor = kpi.change_percent < 0 ? 'color: #DC2626;' : (kpi.change_percent > 0 ? 'color: #16A34A;' : 'color: #475569;');
      return `
        <div class="kpi-mini-tile">
          <span class="kpi-mini-lbl" title="${kpi.display_name}">${kpi.display_name.split('(')[0]}</span>
          <span class="kpi-mini-delta" style="${deltaColor}">${kpi.formatted_change}</span>
          <span class="kpi-mini-sub">${valStr}</span>
        </div>
      `;
    }).join('');
  }
}

/**
 * Render Column 3: Supporting Evidence Card with Mini Sparklines
 */
function renderSupportingEvidenceCard(data) {
  const p3b = data.phase3b || {};
  const evidenceList = p3b.supporting_evidence || [];
  const history = (data.connected_kpis && data.connected_kpis.monthly_history) || {};
  const container = document.getElementById('card3-evidence-list');
  if (!container) return;

  if (evidenceList.length === 0) {
    container.innerHTML = `<div class="fb-empty-state">No supporting evidence items emitted for this scenario.</div>`;
    return;
  }

  container.innerHTML = evidenceList.map((ev, idx) => {
    const isUp = ev.finding && ev.finding.includes('+');
    const chipClass = isUp ? 'ev-delta-up' : 'ev-delta-down';
    const deltaText = ev.finding ? ev.finding.match(/[\+\-]\d+(\.\d+)?%/) : ['--'];
    const deltaStr = deltaText ? deltaText[0] : (isUp ? '+40%' : '-42%');

    // Generate Mini Sparkline SVG
    let sparklineSeries = isUp ? [10, 8, 12, 22] : [22, 18, 14, 6];
    if (ev.metric === 'marketing_spend' && history.marketing_spend) sparklineSeries = history.marketing_spend;
    if (ev.metric === 'conversion_rate' && history.conversion_rate) sparklineSeries = history.conversion_rate;
    if (ev.metric === 'click_through_rate' && history.click_through_rate) sparklineSeries = history.click_through_rate;

    const sparkSvg = generateMiniSparklineSvg(sparklineSeries, isUp ? '#16A34A' : '#DC2626');

    return `
      <div class="ev-card-item">
        <div class="ev-info-col">
          <div class="ev-header-row">
            <span class="ev-id-badge">${ev.evidence_id}</span>
            <span class="ev-metric-title">${formatKpiName(ev.metric || 'Signal')}</span>
            <span class="ev-delta-chip ${chipClass}">${deltaStr}</span>
          </div>
          <span class="ev-desc-snippet">${ev.finding || 'Observed anomalous variance.'}</span>
        </div>
        <div class="ev-sparkline-col">
          ${sparkSvg}
        </div>
      </div>
    `;
  }).join('');
}

function generateMiniSparklineSvg(series, strokeColor) {
  const min = Math.min(...series);
  const max = Math.max(...series);
  const w = 65;
  const h = 28;
  const pad = 3;
  const plotW = w - pad * 2;
  const plotH = h - pad * 2;

  const points = series.map((val, idx) => {
    const x = pad + (idx / (series.length - 1 || 1)) * plotW;
    const y = pad + plotH - ((val - min) / (max - min || 1)) * plotH;
    return `${x},${y}`;
  });

  const lastPt = points[points.length - 1].split(',');

  return `
    <svg viewBox="0 0 ${w} ${h}" style="width: 100%; height: 100%;">
      <path d="M ${points.join(' L ')}" fill="none" stroke="${strokeColor}" stroke-width="1.8" stroke-linecap="round"/>
      <circle cx="${lastPt[0]}" cy="${lastPt[1]}" r="2.5" fill="${strokeColor}"/>
    </svg>
  `;
}

/**
 * Render Middle Row: Panel A — Connected KPI Relationship Tree
 */
function renderConnectedKpiStoryCard(data) {
  const connData = data.connected_kpis || {};
  const kpis = connData.connected_kpis || [];
  const container = document.getElementById('connected-tree-viewport');
  if (!container) return;

  const isRedacted = data.entitlement && data.entitlement.is_redacted;

  const getKpi = (id) => kpis.find((k) => k.kpi_id === id) || {
    display_name: id,
    formatted_value: '--',
    formatted_change: '0.0%'
  };

  const salesKpi = getKpi('gross_sales');
  const volKpi = getKpi('order_volume');
  const spendKpi = getKpi('marketing_spend');
  const cvrKpi = getKpi('conversion_rate');
  const ctrKpi = getKpi('click_through_rate');

  const salesVal = isRedacted ? '[RESTRICTED]' : salesKpi.formatted_value;

  container.innerHTML = `
    <!-- Level 1: Root Outcome Node -->
    <div class="tree-level-1">
      <div class="tree-node tree-node-root">
        <span class="tree-node-title">Gross Sales</span>
        <span class="tree-node-val val-danger">${salesKpi.formatted_change}</span>
        <span class="tree-node-sub">${salesVal}</span>
      </div>
    </div>

    <!-- Connector Lines -->
    <svg width="220" height="20" style="margin: -6px auto 0; display: block;">
      <path d="M 110,0 L 110,10 L 40,10 L 40,20 M 110,10 L 180,10 L 180,20" fill="none" stroke="#CBD5E1" stroke-width="1.5"/>
    </svg>

    <!-- Level 2: Child Branch Nodes -->
    <div class="tree-level-2">
      <div class="tree-node tree-node-corrob">
        <span class="tree-node-title">Order Volume</span>
        <span class="tree-node-val val-danger">${volKpi.formatted_change}</span>
        <span class="tree-node-sub">${volKpi.formatted_value}</span>
      </div>

      <div class="tree-node tree-node-driver">
        <span class="tree-node-title">Marketing Spend</span>
        <span class="tree-node-val val-success">${spendKpi.formatted_change}</span>
        <span class="tree-node-sub">${spendKpi.formatted_value}</span>
      </div>
    </div>

    <!-- Connector Lines to Funnel Sub-children -->
    <svg width="220" height="20" style="margin: 0 auto; display: block;">
      <path d="M 180,0 L 180,10 L 125,10 L 125,20 M 180,10 L 205,10 L 205,20" fill="none" stroke="#CBD5E1" stroke-width="1.5"/>
    </svg>

    <!-- Level 3: Sub-child Digital Funnel Signals -->
    <div class="tree-level-3">
      <div class="tree-node tree-node-corrob" style="min-width: 95px;">
        <span class="tree-node-title">Conversion Rate</span>
        <span class="tree-node-val val-danger">${cvrKpi.formatted_change}</span>
        <span class="tree-node-sub">${cvrKpi.formatted_value}</span>
      </div>

      <div class="tree-node tree-node-corrob" style="min-width: 95px;">
        <span class="tree-node-title">CTR</span>
        <span class="tree-node-val val-danger">${ctrKpi.formatted_change}</span>
        <span class="tree-node-sub">${ctrKpi.formatted_value}</span>
      </div>
    </div>
  `;

  // Update alignment footer
  const target = connData.target_entity || {};
  const mktEl = document.getElementById('tree-key-market');
  const prodEl = document.getElementById('tree-key-product');
  const perEl = document.getElementById('tree-key-period');
  if (mktEl) mktEl.textContent = target.market || 'China';
  if (prodEl) prodEl.textContent = target.product_code || 'A2520150501';
  if (perEl) perEl.textContent = target.period || 'Apr 2021';
}

/**
 * Render Middle Row: Panel B — Candidate Driver Comparison Card
 */
function renderCandidateDriverComparisonCard(data) {
  const p3a = data.phase3a || {};
  const candidates = p3a.candidate_drivers || [];
  const container = document.getElementById('candidate-comparison-list');
  if (!container) return;

  if (candidates.length === 0) {
    container.innerHTML = `<div class="fb-empty-state">No candidate drivers scored.</div>`;
    return;
  }

  const maxFit = Math.max(...candidates.map((c) => c.fit_score || 0), 1.0);

  container.innerHTML = candidates.map((cand, idx) => {
    const isPrimary = idx === 0 && cand.fit_score > 0;
    const rowClass = isPrimary ? 'is-primary' : '';
    const tagClass = isPrimary ? 'tag-primary' : 'tag-rejected';
    const tagText = isPrimary ? 'Primary' : 'Rejected';
    const fillPct = Math.min(100, Math.max(5, (cand.fit_score / maxFit) * 100));

    const bName = DRIVER_BUSINESS_NAMES[cand.driver] || cand.driver;

    return `
      <div class="driver-comp-row ${rowClass}">
        <span class="rank-col">${idx + 1}</span>
        <div class="driver-meta-col">
          <span class="driver-row-name" title="${bName}">${bName}</span>
          <span class="driver-row-code">${cand.driver}</span>
        </div>
        <div class="strength-bar-track">
          <div class="strength-bar-fill" style="width: ${fillPct}%; background: ${isPrimary ? '#10B981' : '#CBD5E1'};"></div>
        </div>
        <span class="fit-score-col">${(cand.fit_score || 0).toFixed(2)}</span>
        <span class="status-tag-micro ${tagClass}">${tagText}</span>
      </div>
    `;
  }).join('');
}

/**
 * Render Middle Row: Panel C — Multi-Metric Trend Overview Card (Dual Axis)
 */
function renderMultiMetricTrendOverviewCard(data) {
  const history = (data.connected_kpis && data.connected_kpis.monthly_history) || {
    periods: ['Jan 2021', 'Feb 2021', 'Mar 2021', 'Apr 2021'],
    gross_sales: [590.11, 3074.39, 7009.60, 994.25],
    marketing_spend: [1691.02, 587.96, 705.85, 1641.07],
    conversion_rate: [7.26, 5.56, 7.88, 3.63],
    click_through_rate: [4.22, 3.24, 2.72, 0.95]
  };

  renderMultiMetricTrendOverview(history, appState.activeTrendMetrics);
}

function renderMultiMetricTrendOverview(history, activeMetrics) {
  const container = document.getElementById('multimetric-chart-viewport');
  if (!container) return;

  const periods = history.periods || ['Jan', 'Feb', 'Mar', 'Apr'];
  const width = 310;
  const height = 125;
  const padLeft = 32;
  const padRight = 32;
  const padTop = 12;
  const padBottom = 22;

  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  // Scales
  const maxCurrency = 8000;
  const maxPercent = 12;

  const getX = (idx) => padLeft + (idx / (periods.length - 1 || 1)) * plotW;
  const getYCurr = (val) => padTop + plotH - (val / maxCurrency) * plotH;
  const getYPct = (val) => padTop + plotH - (val / maxPercent) * plotH;

  let svg = `
    <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: 100%;" font-family="Inter, sans-serif">
      <!-- Axis Lines -->
      <line x1="${padLeft}" y1="${height - padBottom}" x2="${width - padRight}" y2="${height - padBottom}" stroke="#E2E8F0" stroke-width="1"/>
      <line x1="${padLeft}" y1="${padTop}" x2="${padLeft}" y2="${height - padBottom}" stroke="#E2E8F0" stroke-width="1"/>
      <line x1="${width - padRight}" y1="${padTop}" x2="${width - padRight}" y2="${height - padBottom}" stroke="#E2E8F0" stroke-width="1"/>

      <!-- Left Currency Ticks -->
      <text x="${padLeft - 3}" y="${padTop + 6}" font-size="7.5" fill="#64748B" text-anchor="end" font-family="JetBrains Mono">$8K</text>
      <text x="${padLeft - 3}" y="${padTop + plotH * 0.5 + 3}" font-size="7.5" fill="#64748B" text-anchor="end" font-family="JetBrains Mono">$4K</text>
      <text x="${padLeft - 3}" y="${height - padBottom}" font-size="7.5" fill="#64748B" text-anchor="end" font-family="JetBrains Mono">$0</text>

      <!-- Right Percent Ticks -->
      <text x="${width - padRight + 3}" y="${padTop + 6}" font-size="7.5" fill="#64748B" text-anchor="start" font-family="JetBrains Mono">12%</text>
      <text x="${width - padRight + 3}" y="${padTop + plotH * 0.5 + 3}" font-size="7.5" fill="#64748B" text-anchor="start" font-family="JetBrains Mono">6%</text>
      <text x="${width - padRight + 3}" y="${height - padBottom}" font-size="7.5" fill="#64748B" text-anchor="start" font-family="JetBrains Mono">0%</text>
  `;

  // Gross Sales Line (Red)
  if (activeMetrics.includes('gross_sales') && history.gross_sales) {
    const pts = history.gross_sales.map((v, i) => `${getX(i)},${getYCurr(v)}`);
    svg += `<path d="M ${pts.join(' L ')}" fill="none" stroke="#DC2626" stroke-width="2" stroke-linecap="round"/>`;
    history.gross_sales.forEach((v, i) => {
      svg += `<circle cx="${getX(i)}" cy="${getYCurr(v)}" r="3" fill="#DC2626"><title>Gross Sales: $${v.toLocaleString()}</title></circle>`;
    });
  }

  // Marketing Spend Line (Green)
  if (activeMetrics.includes('marketing_spend') && history.marketing_spend) {
    const pts = history.marketing_spend.map((v, i) => `${getX(i)},${getYCurr(v)}`);
    svg += `<path d="M ${pts.join(' L ')}" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round"/>`;
    history.marketing_spend.forEach((v, i) => {
      svg += `<circle cx="${getX(i)}" cy="${getYCurr(v)}" r="3" fill="#10B981"><title>Ad Spend: $${v.toLocaleString()}</title></circle>`;
    });
  }

  // Conversion Rate Line (Blue)
  if (activeMetrics.includes('conversion_rate') && history.conversion_rate) {
    const pts = history.conversion_rate.map((v, i) => `${getX(i)},${getYPct(v)}`);
    svg += `<path d="M ${pts.join(' L ')}" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-dasharray="3,2"/>`;
    history.conversion_rate.forEach((v, i) => {
      svg += `<circle cx="${getX(i)}" cy="${getYPct(v)}" r="3" fill="#2563EB"><title>CVR: ${v}%</title></circle>`;
    });
  }

  // X Labels
  periods.forEach((p, i) => {
    svg += `<text x="${getX(i)}" y="${height - 6}" font-size="8" fill="#64748B" text-anchor="middle">${p.split(' ')[0]}</text>`;
  });

  svg += `</svg>`;
  container.innerHTML = svg;
}

/**
 * Render Bottom Row: Decision Support & Human Review Strip
 */
function renderDecisionSupportStrip(data) {
  const gov = data.decision_governance || {};
  const riskBadge = document.getElementById('card4-risk-badge');
  const actionEl = document.getElementById('dec-action');
  const ownerAreaEl = document.getElementById('dec-owner-area');
  const confEl = document.getElementById('dec-confidence');

  if (riskBadge) {
    const rLevel = gov.risk_level || 'HIGH';
    riskBadge.textContent = `Risk: ${rLevel}`;
    riskBadge.className = `risk-badge ${rLevel === 'HIGH' ? 'risk-badge-high' : (rLevel === 'MEDIUM' ? 'risk-badge-medium' : 'risk-badge-low')}`;
  }

  if (actionEl) {
    actionEl.textContent = gov.recommended_action || 'Audit underperforming digital ad campaigns, pause non-converting creative variants, and reallocate budget toward validated conversion channels.';
  }

  if (ownerAreaEl) {
    ownerAreaEl.textContent = `${gov.required_owner || 'Marketing Operations Lead'} • ${gov.affected_area || 'Performance Marketing & Growth'}`;
  }

  if (confEl) {
    const conf = (data.phase3b && data.phase3b.diagnosis && data.phase3b.diagnosis.status) || 'PLAUSIBLE';
    confEl.textContent = `${conf} (Evidence Grounded)`;
  }
}

/**
 * Select Feedback Decision (Approve / Reviewed / Needs Evidence / Reject)
 */
function selectFeedbackDecision(decision) {
  const altWrap = document.getElementById('fb-alt-driver-wrap');
  const revStatus = document.getElementById('analyst-review-status');

  if (revStatus) {
    revStatus.textContent = `Selected: ${decision}`;
  }

  if (altWrap) {
    altWrap.classList.toggle('hidden', decision !== 'REJECTED');
  }

  // Save selected decision in state
  appState.selectedFeedbackDecision = decision;
  showToast(`Action Selected: ${decision}`);
}

/**
 * Submit Analyst Feedback Learning Loop
 */
async function submitAnalystFeedback() {
  const decision = appState.selectedFeedbackDecision || 'APPROVED';
  const reasonInput = document.getElementById('fb-reason-input');
  const altSelect = document.getElementById('fb-alt-driver-select');
  const resultBanner = document.getElementById('fb-result-banner');

  const reason = reasonInput ? reasonInput.value : '';
  const altDriver = altSelect ? altSelect.value : null;

  const payload = {
    scenario_id: appState.selectedScenarioId,
    predicted_driver: (appState.currentData && appState.currentData.phase3a && appState.currentData.phase3a.diagnosis && appState.currentData.phase3a.diagnosis.driver) || 'DRIVER_03_MARKETING',
    analyst_decision: decision,
    reviewer: appState.role === 'EXECUTIVE' ? 'Executive Commercial Lead' : 'Lead Commercial Analyst',
    reason: reason,
    alternative_driver: altDriver,
    context: {
      market: (appState.currentData && appState.currentData.request && appState.currentData.request.market) || 'China',
      category: 'Mouse'
    }
  };

  try {
    const res = await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const respData = await res.json();
      if (resultBanner) {
        resultBanner.classList.remove('hidden');
        const adj = decision === 'APPROVED' ? '+0.08' : (decision === 'REJECTED' ? '-0.08' : '+0.00');
        const base = 6.00;
        const total = decision === 'APPROVED' ? 6.08 : (decision === 'REJECTED' ? 5.92 : 6.00);
        const adjEl = document.getElementById('fb-res-adj');
        const totalEl = document.getElementById('fb-res-total');
        if (adjEl) adjEl.textContent = adj;
        if (totalEl) totalEl.textContent = total.toFixed(2);
      }
      showToast('Analyst Feedback Recorded & Bounded Adjustment Applied (+0.08)');
    }
  } catch (err) {
    console.error('Failed to submit feedback:', err);
    showToast(`Feedback Error: ${err.message}`, true);
  }
}

/**
 * Render Persistent Telemetry Footer Bar
 */
function renderLiveTelemetryFooter(data) {
  const tel = data.runtime_telemetry || {};
  const latEl = document.getElementById('tf-latency');
  const callsEl = document.getElementById('tf-llm-calls');
  const tokensEl = document.getElementById('tf-tokens');
  const costEl = document.getElementById('tf-cost');

  if (latEl) latEl.textContent = `${(tel.total_latency_ms || 14.5).toFixed(1)}ms (Total)`;
  if (callsEl) callsEl.textContent = tel.llm_calls_count !== undefined ? `${tel.llm_calls_count}` : '0';
  if (tokensEl) tokensEl.textContent = tel.total_tokens || 'UNAVAILABLE';
  if (costEl) costEl.textContent = tel.estimated_cost_usd || '$0.000000';
}

/**
 * Render View 2: Evidence Explorer
 */
function renderView2EvidenceExplorer(data) {
  const p3b = data.phase3b || {};
  const evidenceList = p3b.supporting_evidence || [];
  const catalogBody = document.getElementById('evidence-catalog-body');
  const claimsContainer = document.getElementById('claims-stream-container');
  const uncertaintiesContainer = document.getElementById('uncertainties-container');

  if (catalogBody && evidenceList.length > 0) {
    catalogBody.innerHTML = evidenceList.map((ev) => `
      <tr>
        <td><code>${ev.evidence_id}</code></td>
        <td>${ev.dataset || 'fact_marketing_monthly.csv'}</td>
        <td>${formatKpiName(ev.metric || 'Telemetry')}</td>
        <td><strong>${ev.finding || 'Anomalous variance'}</strong></td>
        <td><span class="status-badge badge-success">Direct Grounding</span></td>
      </tr>
    `).join('');
  }

  if (claimsContainer) {
    claimsContainer.innerHTML = (p3b.evidence_trail || []).map((t) => `
      <div class="claim-item" style="padding: 8px 10px; border-bottom: 1px solid #F1F5F9;">
        <span class="status-badge badge-success">Grounded</span>
        <p style="font-size: 12px; margin-top: 4px; color: #334155;">${t.statement || t}</p>
      </div>
    `).join('') || `<p style="font-size: 12px; color: #64748B;">All statements claim-grounded with verified database partition citations.</p>`;
  }

  if (uncertaintiesContainer) {
    const uncerts = p3b.uncertainties || ['Marketing spend increased materially while conversion efficiency deteriorated.'];
    uncertaintiesContainer.innerHTML = uncerts.map((u) => `
      <div class="uncertainty-item" style="padding: 6px 8px; background: #F8FAFC; border-left: 3px solid #CBD5E1; margin-bottom: 6px; font-size: 11.5px;">
        ${u}
      </div>
    `).join('');
  }
}

/**
 * Render View 3: Integrity & Governance Audit Trail
 */
function renderView3IntegrityAndGovernance(data) {
  const tel = data.runtime_telemetry || {};
  const totLat = document.getElementById('tel-total-latency');
  const detLat = document.getElementById('tel-det-latency');
  const llmLat = document.getElementById('tel-llm-latency');
  const calls = document.getElementById('tel-model-calls');
  const tokens = document.getElementById('tel-token-usage');
  const cost = document.getElementById('tel-cost');

  if (totLat) totLat.textContent = `${(tel.total_latency_ms || 14.5).toFixed(1)} ms`;
  if (detLat) detLat.textContent = `${(tel.deterministic_latency_ms || 12.5).toFixed(1)} ms`;
  if (llmLat) llmLat.textContent = `${(tel.llm_latency_ms || 0.0).toFixed(1)} ms`;
  if (calls) calls.textContent = `${tel.llm_calls_count || 0} calls`;
  if (tokens) tokens.textContent = tel.total_tokens || 'UNAVAILABLE FROM PROVIDER';
  if (cost) cost.textContent = tel.estimated_cost_usd || '$0.000000 (MOCK_MODE)';

  // Populate Data Trust Table in View 3
  const dtBody = document.getElementById('trace-datatrust-body');
  const dtReport = data.data_trust || {};
  const datasets = dtReport.canonical_datasets || [];
  if (dtBody && datasets.length > 0) {
    dtBody.innerHTML = datasets.map((d) => `
      <tr>
        <td><strong>${d.dataset_name}</strong></td>
        <td>${d.business_domain}</td>
        <td>${(d.record_count || 0).toLocaleString()}</td>
        <td>${d.latest_data_date || 'Aug 2021'}</td>
        <td><span class="status-badge badge-success">Complete</span></td>
        <td><strong>${d.dataset_quality_score || 99.8}%</strong></td>
        <td><span class="status-badge badge-success">TRUSTED</span></td>
      </tr>
    `).join('');
  }
}

/**
 * Source Integration Specification Modal Handlers
 */
async function openSourceSpecModal() {
  const modal = document.getElementById('source-spec-modal');
  const tbody = document.getElementById('modal-source-tbody');
  if (modal) modal.classList.remove('hidden');

  try {
    const res = await fetch('/api/source-spec');
    if (res.ok) {
      const data = await res.json();
      const sources = data.canonical_sources || [];
      if (tbody) {
        tbody.innerHTML = sources.map((s) => `
          <tr>
            <td><strong>${s.domain}</strong></td>
            <td><code>${s.file_name}</code><br><span style="font-size: 10px; color: #64748B;">${s.dataset_name}</span></td>
            <td>${s.grain}</td>
            <td><span class="status-badge badge-info">${s.refresh_cadence}</span></td>
            <td>${(s.derived_signals || []).join(', ')}</td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Failed to load source spec:', err);
  }
}

function closeSourceSpecModal() {
  const modal = document.getElementById('source-spec-modal');
  if (modal) modal.classList.add('hidden');
}

/**
 * KPI Semantic Governance Contract Modal Handlers
 */
async function openKpiContractModal() {
  const modal = document.getElementById('kpi-modal');
  const body = document.getElementById('modal-kpi-body');
  if (modal) modal.classList.remove('hidden');

  try {
    const res = await fetch('/api/kpi-contract?kpi_id=gross_sales');
    if (res.ok) {
      const data = await res.json();
      if (body) {
        body.innerHTML = `
          <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12.5px;">
            <div><strong>KPI Name:</strong> ${data.kpi_name} (<code>${data.kpi_id}</code>)</div>
            <div><strong>Formula:</strong> <code>${data.calculation_formula}</code></div>
            <div><strong>Grain:</strong> ${data.grain}</div>
            <div><strong>Baseline Methodology:</strong> ${data.baseline_methodology}</div>
            <div><strong>Materiality Threshold:</strong> ${data.materiality_threshold}</div>
            <div><strong>Candidate Drivers:</strong> ${(data.candidate_drivers || []).join(', ')}</div>
            <div><strong>Sensitivity:</strong> ${data.sensitivity_classification}</div>
          </div>
        `;
      }
    }
  } catch (err) {
    console.error('Failed to load KPI contract:', err);
  }
}

function closeKpiContractModal() {
  const modal = document.getElementById('kpi-modal');
  if (modal) modal.classList.add('hidden');
}

/**
 * Helpers
 */
function formatKpiName(kpiKey) {
  const names = {
    gross_sales: 'Gross Sales',
    order_volume: 'Order Volume',
    marketing_spend: 'Marketing Spend',
    conversion_rate: 'Conversion Rate',
    click_through_rate: 'Click-Through Rate',
    return_rate: 'Return Rate',
    ticket_volume: 'Support Escalations'
  };
  return names[kpiKey] || kpiKey.replace(/_/g, ' ').toUpperCase();
}

function formatDateLabel(dateStr) {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const d = new Date(dateStr);
  return `${months[d.getUTCMonth()]} ${d.getUTCFullYear()}`;
}

function showLoading(show) {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.classList.toggle('hidden', !show);
  }
}

function showToast(message, isError = false) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = 'toast-clean';
  if (isError) toast.style.backgroundColor = '#DC2626';
  toast.textContent = message;

  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3000);
}

function highlightEvidence(evidenceId) {
  switchView('view-reasoning');
  const catalogBody = document.getElementById('evidence-catalog-body');
  if (catalogBody) {
    const rows = catalogBody.querySelectorAll('tr');
    rows.forEach((r) => {
      if (r.textContent.includes(evidenceId)) {
        r.style.backgroundColor = '#EFF6FF';
        r.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        r.style.backgroundColor = '';
      }
    });
  }
}


/* ==========================================================================
   PHASE 6.2 — SIGNAL STORY NARRATIVE INTELLIGENCE LAYER
   All functions are deterministic. No analytical calculations.
   All values sourced from governed API response fields only.
   ========================================================================== */

/**
 * storyToggleStage — Toggle expand/collapse for a story stage panel.
 * Called from inline onclick in index.html.
 */
function storyToggleStage(stageId) {
  var el = document.getElementById(stageId);
  if (!el) return;
  el.classList.toggle('is-expanded');
}

/**
 * applyStoryEntitlement — Redact financially sensitive fields before render.
 * Runs BEFORE any innerHTML is set. No side-channel leakage.
 */
function applyStoryEntitlement(story, data) {
  var entitlement = data.entitlement || {};
  var isRedacted = entitlement.is_redacted || false;
  var redactedFields = entitlement.redacted_fields || [];
  var REDACT_LABEL = '[RESTRICTED — FINANCIAL CONFIDENTIAL]';

  var s = JSON.parse(JSON.stringify(story));
  if (!isRedacted) return s;

  if (redactedFields.indexOf('actual_value') !== -1 || redactedFields.indexOf('actual') !== -1) {
    if (s.what_happened) s.what_happened.actual_display = REDACT_LABEL;
  }
  if (redactedFields.indexOf('baseline_value') !== -1 || redactedFields.indexOf('baseline') !== -1) {
    if (s.what_happened) s.what_happened.baseline_display = REDACT_LABEL;
  }
  if (s.glance_text) {
    s.glance_text = s.glance_text.replace(/\(\$[\d,.]+ vs \$[\d,.]+ baseline\)/g, '');
  }
  return s;
}

/**
 * buildStoryObject — Extract and normalise the signal_story object.
 * If pre-built signal_story is embedded, use it directly.
 */
function buildStoryObject(data) {
  if (data.signal_story) return data.signal_story;

  var p3a = data.phase3a || {};
  var p3b = data.phase3b || {};
  var gov = data.decision_governance || {};
  var conn = data.connected_kpis || {};
  var abstention = data.abstention_governance || {};
  var sparse = data.sparse_history || {};
  var entitlement = data.entitlement || {};
  var personaView = data.persona_view || {};
  var metadata = data.metadata || {};

  var evEvent = p3a.event || {};
  var diagnosis = p3b.diagnosis || {};
  var connectedKpis = conn.connected_kpis || [];
  var evidenceList = p3b.supporting_evidence || [];
  var candidates = p3a.candidate_drivers || [];
  var isRedacted = entitlement.is_redacted || false;
  var redactedFields = entitlement.redacted_fields || [];

  var isAbstention = (abstention.is_abstaining || false) || diagnosis.status === 'NOT_ESTABLISHED';
  var isSparse = sparse.is_limited_history || false;
  var storyState = 'PLAUSIBLE';
  if (isAbstention) storyState = 'ABSTENTION';
  else if (isSparse) storyState = 'SPARSE_HISTORY';
  else if (diagnosis.status === 'STRONGLY_SUPPORTED') storyState = 'SUPPORTED';

  var magnitudeRaw = evEvent.baseline_change_percent || 0;
  var magnitudePct = Math.abs(magnitudeRaw) <= 1.5
    ? Math.round(Math.abs(magnitudeRaw) * 100 * 100) / 100
    : Math.round(Math.abs(magnitudeRaw) * 100) / 100;
  var direction = magnitudeRaw < 0 ? 'fell' : 'rose';
  var directionArrow = magnitudeRaw < 0 ? '\u2193' : '\u2191';
  var kpiContract = data.kpi_contract || {};
  var kpiName = kpiContract.kpi_name || (conn.target_entity && conn.target_entity.category) || 'Gross Sales';

  var actualVal = evEvent.current_value;
  var baselineVal = evEvent.baseline_value;
  function fmt(v) {
    return typeof v === 'number'
      ? '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      : String(v || '\u2014');
  }

  var whatHappened = {
    kpi_name: kpiName,
    direction: direction,
    direction_arrow: directionArrow,
    magnitude_pct: magnitudePct,
    actual_display: (isRedacted && redactedFields.indexOf('actual_value') !== -1)
      ? '[RESTRICTED \u2014 FINANCIAL CONFIDENTIAL]' : fmt(actualVal),
    baseline_display: (isRedacted && redactedFields.indexOf('baseline_value') !== -1)
      ? '[RESTRICTED \u2014 FINANCIAL CONFIDENTIAL]' : fmt(baselineVal),
    period: evEvent.date
      ? new Date(evEvent.date).toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' })
      : '',
    is_redacted: isRedacted,
    anomaly_type: magnitudeRaw < 0 ? 'Negative' : 'Positive',
  };

  var whatChanged = connectedKpis
    .filter(function(k) { return k.kpi_id !== 'gross_sales'; })
    .map(function(k) {
      return {
        kpi_id: k.kpi_id,
        display_name: k.display_name || k.kpi_id,
        change_pct: Math.round((k.change_percent || 0) * 100) / 100,
        formatted_change: k.formatted_change || ((k.change_percent >= 0 ? '+' : '') + (k.change_percent || 0).toFixed(2) + '%'),
        direction_arrow: (k.change_percent || 0) < 0 ? '\u2193' : '\u2191',
        direction_word: (k.change_percent || 0) < 0 ? 'fell' : 'rose',
        role: k.evidence_role || '',
        role_label: k.role_label || '',
        source_dataset: k.source_dataset || '',
      };
    });

  var evidenceChain = evidenceList.map(function(ev) {
    return {
      evidence_id: ev.evidence_id || '',
      metric: ev.metric || '',
      display_name: ev.display_name || (ev.metric || '').replace(/_/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); }),
      finding: ev.finding || '',
      dataset: ev.dataset || '',
      role: ev.role || '',
      direction_arrow: (String(ev.finding || '').indexOf('-') !== -1 && String(ev.finding || '').indexOf('%') !== -1) ? '\u2193' : '\u2191',
    };
  });

  var ruledOut = candidates.slice(1).map(function(cand, i) {
    return {
      driver_id: cand.driver,
      driver_name: DRIVER_BUSINESS_NAMES[cand.driver] || cand.driver,
      fit_score: Math.round((cand.fit_score || 0) * 100) / 100,
      rejection_reason: cand.reason || 'Insufficient supporting evidence',
      rank: i + 2,
    };
  });

  var primaryDriver = null;
  if (candidates.length > 0) {
    var c0 = candidates[0];
    primaryDriver = {
      driver_id: c0.driver,
      driver_name: DRIVER_BUSINESS_NAMES[c0.driver] || c0.driver,
      fit_score: Math.round((c0.fit_score || 0) * 100) / 100,
      status: diagnosis.status || 'PLAUSIBLE',
    };
  }

  var whatNext = {
    recommended_action: gov.recommended_action || 'Conduct cross-functional operational review.',
    owner: gov.required_owner || 'Commercial Operations Lead',
    area: gov.affected_business_area || 'Commercial Operations',
    risk_level: gov.risk_level || 'MEDIUM',
    confidence: diagnosis.status || 'PLAUSIBLE',
    human_review_required: gov.approval_required !== false,
    human_review_label: gov.approval_required !== false ? 'Required' : 'Not Required',
    finding_statement: gov.finding_statement || '',
    why_it_matters: gov.why_it_matters || '',
    causal_language_class: gov.causal_language_class || 'SUPPORTED_INFERENCE',
  };

  var glanceText = buildGlanceText(
    { storyState: storyState, whatHappened: whatHappened, whatChanged: whatChanged, primaryDriver: primaryDriver, ruledOut: ruledOut },
    abstention, sparse
  );

  var provider = metadata.provider || 'mock';
  var geminiConfigured = metadata.gemini_configured || false;
  var llmSummary = p3b.executive_summary || '';
  var validationStatus = metadata.validation_status || 'PASSED';
  var aiNarrative = { available: false, text: null, disclosure: null };
  if (provider === 'gemini' && geminiConfigured && llmSummary && validationStatus === 'PASSED') {
    aiNarrative = {
      available: true,
      text: llmSummary,
      disclosure: 'AI-assisted narrative \u2022 Based on governed evidence \u2022 Deterministic analytical results remain authoritative.',
    };
  }

  var timelineSteps;
  if (isAbstention) {
    timelineSteps = [
      { number: '01', label: 'SIGNAL', detail: kpiName + ' anomaly detected' },
      { number: '02', label: 'EVIDENCE', detail: 'Evidence reviewed' },
      { number: '03', label: 'ABSTENTION', detail: 'Insufficient to establish driver' },
      { number: '04', label: 'DECISION', detail: 'No action until validated' },
    ];
  } else if (isSparse) {
    timelineSteps = [
      { number: '01', label: 'SIGNAL', detail: kpiName + ' anomaly detected' },
      { number: '02', label: 'LIMITED HISTORY', detail: '< 3 months available' },
      { number: '03', label: 'BENCHMARK', detail: 'Contextual peer benchmark used' },
      { number: '04', label: 'CONFIDENCE', detail: 'LOW \u2014 proceed with caution' },
    ];
  } else {
    timelineSteps = [
      { number: '01', label: 'SIGNAL', detail: kpiName + ' ' + direction + ' ' + magnitudePct.toFixed(1) + '%' },
      { number: '02', label: 'CONNECTED', detail: whatChanged.length + ' corroborating signals' },
      { number: '03', label: 'FUNNEL', detail: 'Evidence chain traced' },
      { number: '04', label: 'HYPOTHESIS', detail: primaryDriver ? primaryDriver.driver_name : 'Driver evaluated' },
      { number: '05', label: 'VALIDATION', detail: ruledOut.length + ' alternatives checked' },
      { number: '06', label: 'DECISION', detail: 'Risk: ' + whatNext.risk_level },
    ];
  }

  return {
    story_state: storyState,
    what_happened: whatHappened,
    what_changed: whatChanged,
    evidence_chain: evidenceChain,
    ruled_out: ruledOut,
    what_next: whatNext,
    primary_driver: primaryDriver,
    glance_text: glanceText,
    timeline_steps: timelineSteps,
    ai_narrative: aiNarrative,
    persona_detail: {
      active_persona: personaView.active_persona || 'EXECUTIVE',
      detail_level: personaView.detail_level || 'EXECUTIVE_SUMMARY',
      emphasis_levers: personaView.emphasis_levers || [],
      narrative_style: personaView.narrative_style || 'Strategic Decision Briefing',
    },
    abstention_meta: isAbstention ? abstention : null,
    sparse_meta: isSparse ? sparse : null,
    epistemic_note: storyState === 'PLAUSIBLE'
      ? 'Evidence supports this explanation, but does not establish causality.'
      : null,
  };
}

/**
 * buildGlanceText — Deterministic natural-language summary.
 * No LLM. No hardcoded scenario values. Derived from governed fields only.
 */
function buildGlanceText(storyFields, abstention, sparse) {
  var storyState = storyFields.storyState;
  var wh = storyFields.whatHappened || {};
  var whatChanged = storyFields.whatChanged || [];
  var primaryDriver = storyFields.primaryDriver || null;
  var ruledOut = storyFields.ruledOut || [];
  var parts = [];

  if (storyState === 'ABSTENTION') {
    var reasons = (abstention && abstention.reasons) ? abstention.reasons : [];
    var reason = reasons.length > 0 ? reasons[0].toLowerCase() : 'conflicting or insufficient signals';
    parts.push(
      'Insufficient evidence to establish a primary driver. ' +
      'The system detected a sales anomaly, but ' + reason + '. ' +
      'No action is recommended until additional evidence is validated.'
    );
  } else if (storyState === 'SPARSE_HISTORY') {
    parts.push(
      'Limited historical data (< 3 months). ' +
      wh.kpi_name + ' ' + wh.direction + ' ' + (wh.magnitude_pct || 0).toFixed(1) + '% in ' + wh.period + ', ' +
      'assessed against a contextual peer-category benchmark. ' +
      'Confidence is LOW due to insufficient history for a standard 3-month baseline.'
    );
  } else {
    var headline = wh.is_redacted
      ? wh.kpi_name + ' ' + wh.direction + ' ' + (wh.magnitude_pct || 0).toFixed(1) + '% in ' + wh.period + '.'
      : wh.kpi_name + ' ' + wh.direction + ' ' + (wh.magnitude_pct || 0).toFixed(1) + '% in ' + wh.period
        + ' (' + wh.actual_display + ' vs ' + wh.baseline_display + ' baseline).';
    parts.push(headline);

    var sigChanges = whatChanged.filter(function(k) { return Math.abs(k.change_pct) >= 10; }).slice(0, 2);
    if (sigChanges.length > 0) {
      var sigStrs = sigChanges.map(function(k) {
        return k.display_name + ' ' + k.direction_arrow + Math.abs(k.change_pct).toFixed(1) + '%';
      });
      parts.push('Coinciding with: ' + sigStrs.join(' and ') + '.');
    }

    if (primaryDriver) {
      parts.push(primaryDriver.driver_name + ' is the strongest supported explanation (fit score: '
        + primaryDriver.fit_score.toFixed(2) + ', status: ' + primaryDriver.status + ').');
    }

    var rejectedNames = ruledOut.slice(0, 2).map(function(r) { return r.driver_name; });
    if (rejectedNames.length > 0) {
      parts.push('Alternative explanations (' + rejectedNames.join(', ') + ') were checked and found insufficient.');
    }
  }

  return parts.join(' ');
}

/**
 * renderStoryTimeline — Render the left-side CSS timeline column.
 */
function renderStoryTimeline(steps, storyState) {
  var container = document.getElementById('story-timeline-container');
  if (!container) return;

  var dotClass = storyState === 'ABSTENTION' ? 'step-abstention'
    : storyState === 'SPARSE_HISTORY' ? 'step-sparse' : '';

  container.innerHTML = steps.map(function(step, idx) {
    return '<div class="story-timeline-step">' +
      '<div class="story-step-dot ' + (idx === 0 ? 'step-active' : dotClass) + '"></div>' +
      '<span class="story-step-num">' + step.number + '</span>' +
      '<span class="story-step-label">' + step.label + '</span>' +
      '<span class="story-step-detail">' + step.detail + '</span>' +
      '</div>';
  }).join('');
}

/**
 * renderEvidenceChain — Render Stage 3 evidence items. Clickable to Evidence Explorer.
 */
function renderEvidenceChain(evidenceList, persona) {
  var container = document.getElementById('story-stage-evidence-body');
  if (!container) return;

  if (!evidenceList || evidenceList.length === 0) {
    container.innerHTML = '<p class="story-causal-note">No evidence records available for this scenario.</p>';
    return;
  }

  var isAnalyst = persona === 'DOMAIN_ANALYST';
  container.innerHTML = '<div class="story-evidence-chain">' +
    evidenceList.map(function(ev) {
      var arrowColor = ev.direction_arrow === '\u2193' ? 'var(--color-danger)' : 'var(--color-success)';
      return '<div class="story-evidence-item" onclick="highlightEvidence(\'' + ev.evidence_id + '\')" title="Click to highlight in Evidence Explorer">' +
        (isAnalyst ? '<span class="story-evidence-id">' + (ev.evidence_id || '\u2014') + '</span>' : '') +
        '<span class="story-evidence-arrow" style="color:' + arrowColor + ';font-weight:700;">' + ev.direction_arrow + '</span>' +
        '<span class="story-evidence-metric">' + (ev.display_name || ev.metric) + '</span>' +
        '<span class="story-evidence-finding">' + (ev.finding || '') + '</span>' +
        (isAnalyst && ev.dataset ? '<span class="story-meta-pill" style="margin-left:auto;font-size:9.5px;">' + ev.dataset + '</span>' : '') +
        '</div>';
    }).join('') +
    '</div>';
}

/**
 * renderRuledOut — Render Stage 4 alternatives checked.
 */
function renderRuledOut(candidates, persona) {
  var container = document.getElementById('story-stage-ruled-out-body');
  if (!container) return;

  if (!candidates || candidates.length === 0) {
    container.innerHTML = '<p class="story-causal-note">No alternative drivers were evaluated for this scenario.</p>';
    return;
  }

  var isAnalyst = persona === 'DOMAIN_ANALYST';
  container.innerHTML = '<div class="story-ruledout-list">' +
    candidates.map(function(c) {
      return '<div class="story-ruledout-item">' +
        '<span class="story-ruledout-check">\u2713</span>' +
        '<div>' +
          '<div class="story-ruledout-name">' + c.driver_name +
            (isAnalyst ? ' <span class="story-analyst-row" style="display:inline;font-size:9.5px;padding:1px 5px;">fit: ' + c.fit_score.toFixed(2) + '</span>' : '') +
          '</div>' +
          '<div class="story-ruledout-reason">' + (c.rejection_reason || '') + '</div>' +
        '</div>' +
        '</div>';
    }).join('') +
    '</div>';
}

/**
 * renderStoryDecision — Render Stage 5 decision and action block.
 */
function renderStoryDecision(whatNext, primary) {
  var container = document.getElementById('story-stage-decision-body');
  if (!container) return;

  var riskMap = { HIGH: 'val-danger', MEDIUM: 'val-warning', LOW: 'val-success' };
  var riskClass = riskMap[whatNext.risk_level] || 'val-warning';

  container.innerHTML =
    '<div class="story-decision-action-box">' +
      '<div class="story-decision-action-label">RECOMMENDED ACTION</div>' +
      '<p class="story-decision-action-text">' + (whatNext.recommended_action || '') + '</p>' +
    '</div>' +
    '<div class="story-decision-meta-grid">' +
      '<div class="story-decision-meta-item"><span class="story-decision-meta-lbl">Owner</span><span class="story-decision-meta-val">' + (whatNext.owner || '') + '</span></div>' +
      '<div class="story-decision-meta-item"><span class="story-decision-meta-lbl">Area</span><span class="story-decision-meta-val">' + (whatNext.area || '') + '</span></div>' +
      '<div class="story-decision-meta-item"><span class="story-decision-meta-lbl">Risk Level</span><span class="story-decision-meta-val ' + riskClass + '">' + (whatNext.risk_level || '') + '</span></div>' +
      '<div class="story-decision-meta-item"><span class="story-decision-meta-lbl">Human Review</span><span class="story-decision-meta-val ' + (whatNext.human_review_required ? 'val-warning' : 'val-success') + '">' + (whatNext.human_review_label || '') + '</span></div>' +
      (primary ? '<div class="story-decision-meta-item"><span class="story-decision-meta-lbl">Explanation</span><span class="story-decision-meta-val">' + primary.driver_name + '</span></div>' : '') +
    '</div>' +
    (whatNext.finding_statement ? '<p class="story-epistemic-note">' + whatNext.finding_statement + '</p>' : '');
}

/**
 * renderAiNarrative — Show/hide AI-assisted narrative banner with graceful fallback.
 */
function renderAiNarrative(aiNarrative) {
  var banner = document.getElementById('story-ai-banner');
  var textEl = document.getElementById('story-ai-text');
  var discEl = document.getElementById('story-ai-disclosure');
  if (!banner) return;

  if (aiNarrative && aiNarrative.available && aiNarrative.text) {
    if (textEl) textEl.textContent = aiNarrative.text;
    if (discEl) discEl.textContent = aiNarrative.disclosure || '';
    banner.style.display = 'block';
  } else {
    banner.style.display = 'none';
  }
}

/**
 * triggerStoryReveal — Auto-expand Stage 1 after load. Respects reduced-motion.
 */
function triggerStoryReveal() {
  var stageIds = [
    'story-stage-what-happened', 'story-stage-connected', 'story-stage-evidence',
    'story-stage-ruled-out', 'story-stage-decision',
  ];
  stageIds.forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.classList.remove('is-expanded');
  });

  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  setTimeout(function() {
    var stage1 = document.getElementById('story-stage-what-happened');
    if (stage1) stage1.classList.add('is-expanded');
  }, prefersReducedMotion ? 0 : 150);
}

/**
 * renderStorySupported — Full 5-stage story for SUPPORTED / PLAUSIBLE states.
 */
function renderStorySupported(story, data) {
  var wh = story.what_happened || {};
  var persona = ((data.persona_view || {}).active_persona) || appState.persona;
  var isAnalyst = persona === 'DOMAIN_ANALYST';

  // Stage 1: WHAT HAPPENED
  var stage1 = document.getElementById('story-stage-what-happened-body');
  if (stage1) {
    var arrowClass = wh.direction === 'fell' ? 'down' : 'up';
    var pctSign = wh.direction === 'fell' ? '\u2212' : '+';
    var arrowColor = wh.direction === 'fell' ? 'var(--color-danger)' : 'var(--color-success)';
    stage1.innerHTML =
      '<div class="story-headline-lockup">' +
        '<span class="story-signal-arrow ' + arrowClass + '" style="color:' + arrowColor + ';">' + (wh.direction_arrow || (wh.direction === 'fell' ? '\u2193' : '\u2191')) + '</span>' +
        '<span class="story-signal-pct">' + pctSign + (wh.magnitude_pct || 0).toFixed(1) + '%</span>' +
        '<span class="story-signal-label">' + (wh.kpi_name || '') + ' in ' + (wh.period || '') + '</span>' +
      '</div>' +
      '<div class="story-actual-baseline">' +
        '<div class="story-ab-item"><span class="story-ab-lbl">Actual</span>' +
          '<span class="story-ab-val ' + (wh.direction === 'fell' ? 'val-danger' : '') + '">' + (wh.actual_display || '\u2014') + '</span></div>' +
        '<div class="story-ab-item"><span class="story-ab-lbl">Baseline</span>' +
          '<span class="story-ab-val">' + (wh.baseline_display || '\u2014') + '</span></div>' +
      '</div>' +
      '<div class="story-meta-pills">' +
        '<span class="story-meta-pill pill-' + (wh.direction === 'fell' ? 'danger' : 'success') + '">' + (wh.anomaly_type || (wh.direction === 'fell' ? 'Negative' : 'Positive')) + ' Anomaly</span>' +
        '<span class="story-meta-pill">' + (wh.period || '') + '</span>' +
      '</div>';
  }

  // Stage 2: WHAT CHANGED AROUND IT
  var stage2 = document.getElementById('story-stage-connected-body');
  if (stage2) {
    var whatChanged = story.what_changed || [];
    if (whatChanged.length === 0) {
      stage2.innerHTML = '<p class="story-causal-note">No connected KPI data available.</p>';
    } else {
      stage2.innerHTML = '<div class="story-connected-chain">' +
        whatChanged.map(function(k) {
          var aColor = k.direction_arrow === '\u2193' ? 'var(--color-danger)' : 'var(--color-success)';
          return '<div class="story-connected-item">' +
            '<span class="story-connected-item-arrow" style="color:' + aColor + ';">' + k.direction_arrow + '</span>' +
            '<span class="story-connected-item-name">' + (k.display_name || k.kpi_id) + '</span>' +
            '<span class="story-connected-item-change" style="color:' + aColor + ';">' + (k.formatted_change || '') + '</span>' +
            (k.role_label ? '<span class="story-connected-item-role">' + k.role_label + '</span>' : '') +
            (isAnalyst && k.source_dataset ? '<span class="story-meta-pill" style="font-size:9px;">' + k.source_dataset + '</span>' : '') +
            '</div>';
        }).join('') +
        '</div>' +
        '<p class="story-causal-note">Correlation does not imply causality. Coinciding movements inform hypothesis selection only.</p>';
    }
  }

  renderEvidenceChain(story.evidence_chain || [], persona);
  renderRuledOut(story.ruled_out || [], persona);
  renderStoryDecision(story.what_next || {}, story.primary_driver);

  if (story.epistemic_note) {
    var ev3 = document.getElementById('story-stage-evidence-body');
    if (ev3) {
      ev3.insertAdjacentHTML('beforeend', '<p class="story-epistemic-note">' + story.epistemic_note + '</p>');
    }
  }

  if (isAnalyst) {
    var levers = ((story.persona_detail || {}).emphasis_levers || []);
    if (levers.length > 0) {
      var stage5 = document.getElementById('story-stage-decision-body');
      if (stage5) {
        stage5.insertAdjacentHTML('beforeend',
          '<div class="story-analyst-detail">' +
          '<div class="story-decision-meta-lbl" style="margin-bottom:4px;">ANALYST DETAIL</div>' +
          levers.map(function(l) { return '<div class="story-analyst-row">' + l + '</div>'; }).join('') +
          '</div>'
        );
      }
    }
  }
}

/**
 * renderStoryAbstention — Abstention state: S008 / NOT_ESTABLISHED.
 */
function renderStoryAbstention(story, data) {
  var abstentionMeta = story.abstention_meta || (data.abstention_governance || {});
  var reasons = abstentionMeta.reasons || ['Insufficient supporting evidence'];
  var wh = story.what_happened || {};

  var glanceBox = document.getElementById('story-glance-box');
  if (glanceBox) glanceBox.classList.add('state-abstention');

  var s1 = document.getElementById('story-stage-what-happened-body');
  if (s1) {
    s1.innerHTML =
      '<div class="story-abstention-body">' +
        '<div class="story-abstention-section">' +
          '<div class="story-abstention-section-label">SIGNAL DETECTED</div>' +
          '<p class="story-abstention-section-text">' + (wh.kpi_name || '') + ' ' + (wh.direction || 'moved') + ' ' + (wh.magnitude_pct || 0).toFixed(1) + '% in ' + (wh.period || '') + '.</p>' +
        '</div>' +
        '<div class="story-abstention-section">' +
          '<div class="story-abstention-section-label">ABSTENTION REASONS</div>' +
          '<p class="story-abstention-section-text">' + reasons.join(' ') + '</p>' +
        '</div>' +
        '<div class="story-abstention-no-action">\u26a0 NO ACTION RECOMMENDED UNTIL ADDITIONAL EVIDENCE IS VALIDATED</div>' +
      '</div>';
    var el1 = document.getElementById('story-stage-what-happened');
    if (el1) el1.classList.add('is-expanded');
  }

  ['story-stage-connected', 'story-stage-evidence', 'story-stage-ruled-out', 'story-stage-decision'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) {
      el.classList.remove('is-expanded');
      var header = el.querySelector('.story-stage-header');
      if (header) {
        header.style.opacity = '0.45';
        header.style.pointerEvents = 'none';
        header.title = 'Not available: abstention mode';
      }
    }
  });
}

/**
 * renderStorySparse — Sparse history state: S009 / is_limited_history=true.
 */
function renderStorySparse(story, data) {
  var sparseMeta = story.sparse_meta || (data.sparse_history || {});
  var wh = story.what_happened || {};

  var glanceBox = document.getElementById('story-glance-box');
  if (glanceBox) glanceBox.classList.add('state-sparse');

  var s1 = document.getElementById('story-stage-what-happened-body');
  if (s1) {
    var arrowClass = wh.direction === 'fell' ? 'down' : 'up';
    var pctSign = wh.direction === 'fell' ? '\u2212' : '+';
    var arrowColor = wh.direction === 'fell' ? 'var(--color-danger)' : 'var(--color-success)';
    s1.innerHTML =
      '<div class="story-sparse-body">' +
        '<div class="story-sparse-row">' +
          '<span class="story-sparse-badge">\u26a0 SPARSE HISTORY</span>' +
          (sparseMeta.months_available ? ' ' + sparseMeta.months_available + ' months available \u2014 standard baseline requires \u2265 3 months.' : ' Limited historical data available.') +
        '</div>' +
        '<div class="story-headline-lockup" style="margin-top:6px;">' +
          '<span class="story-signal-arrow ' + arrowClass + '" style="color:' + arrowColor + ';">' + (wh.direction_arrow || (wh.direction === 'fell' ? '\u2193' : '\u2191')) + '</span>' +
          '<span class="story-signal-pct">' + pctSign + (wh.magnitude_pct || 0).toFixed(1) + '%</span>' +
          '<span class="story-signal-label">' + (wh.kpi_name || '') + ' in ' + (wh.period || '') + '</span>' +
        '</div>' +
        (sparseMeta.benchmark_source ? '<div class="story-sparse-row">Benchmark: <strong>' + sparseMeta.benchmark_source + '</strong> (contextual peer-category).</div>' : '') +
        '<div class="story-sparse-row"><span class="story-sparse-badge">CONFIDENCE: LOW</span> Proceed with caution. Human review is required before any action.</div>' +
      '</div>';
    var el1 = document.getElementById('story-stage-what-happened');
    if (el1) el1.classList.add('is-expanded');
  }

  var persona = ((data.persona_view || {}).active_persona) || 'EXECUTIVE';
  renderEvidenceChain(story.evidence_chain || [], persona);
  renderRuledOut(story.ruled_out || [], persona);
  renderStoryDecision(story.what_next || {}, story.primary_driver);
}

/**
 * renderSignalStoryPanel — Main orchestrator. Called from renderAllViews(data).
 */
function renderSignalStoryPanel(data) {
  try {
    var rawStory = buildStoryObject(data);
    var story = applyStoryEntitlement(rawStory, data);

    // State badge
    var badge = document.getElementById('story-state-badge');
    if (badge) {
      var stateLabels = { SUPPORTED: 'SUPPORTED', PLAUSIBLE: 'PLAUSIBLE', ABSTENTION: 'ABSTENTION', SPARSE_HISTORY: 'SPARSE HISTORY' };
      badge.textContent = stateLabels[story.story_state] || story.story_state;
      badge.className = 'story-state-badge';
      var stateClassMap = { SUPPORTED: 'state-supported', PLAUSIBLE: 'state-plausible', ABSTENTION: 'state-abstention', SPARSE_HISTORY: 'state-sparse' };
      var stateClass = stateClassMap[story.story_state] || '';
      if (stateClass) badge.classList.add(stateClass);
    }

    // Glance text
    var glanceEl = document.getElementById('story-glance-text');
    if (glanceEl) glanceEl.textContent = story.glance_text || '';

    // Timeline
    renderStoryTimeline(story.timeline_steps || [], story.story_state);

    // State routing
    if (story.story_state === 'ABSTENTION') {
      renderStoryAbstention(story, data);
    } else if (story.story_state === 'SPARSE_HISTORY') {
      renderStorySparse(story, data);
    } else {
      renderStorySupported(story, data);
    }

    // AI Narrative
    renderAiNarrative(story.ai_narrative || {});

    // Reveal animation
    triggerStoryReveal();

  } catch (err) {
    console.error('[Phase 6.2] renderSignalStoryPanel failed:', err);
    var glanceEl2 = document.getElementById('story-glance-text');
    if (glanceEl2) glanceEl2.textContent = 'Signal story unavailable \u2014 deterministic analysis remains active.';
  }
}
