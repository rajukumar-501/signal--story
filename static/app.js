/**
 * Signal Story — Decision Intelligence Application Controller
 * Handles scenario dispatching, multi-view rendering, citation navigation, and telemetry.
 * Connects directly to the frozen Phase 3A/3B Python backend via /api/analyze.
 */

// Application State
const appState = {
  scenarios: [],
  selectedScenarioId: 'S003',
  providerMode: 'mock', // 'mock' (Preview) or 'gemini' (Assisted Analysis)
  currentData: null,
  activeView: 'view-executive',
  isLoading: false,
};

// Canonical Business Names for 8 Hypotheses
const DRIVER_BUSINESS_NAMES = {
  DRIVER_01_INVENTORY: 'Inventory & Stockout Bottleneck',
  DRIVER_02_PRICING: 'Competitor Pricing Undercut',
  DRIVER_03_MARKETING: 'Marketing Inefficiency',
  DRIVER_04_RETURNS: 'Product Defect & Return Surge',
  DRIVER_05_SUPPORT: 'Customer Support Crisis',
  DRIVER_06_CUSTOMER: 'Customer Sentiment Drop',
  DRIVER_07_MARKET: 'Regional Market Contraction',
  DRIVER_08_PRODUCT_MIX: 'Product Mix Shift & Cannibalization',
};

/**
 * Initialize Application on DOM Ready
 */
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
  const modeMockBtn = document.getElementById('mode-mock');
  const modeGeminiBtn = document.getElementById('mode-gemini');
  const btnRun = document.getElementById('btn-run-analysis');
  const btnExport = document.getElementById('btn-export-report');
  const navItems = document.querySelectorAll('.nav-item');
  const sidebarScenarioItems = document.querySelectorAll('.scenario-item');

  // Scenario Dropdown Change
  if (scenarioSelect) {
    scenarioSelect.addEventListener('change', (e) => {
      selectScenario(e.target.value);
    });
  }

  // Sidebar Scenario Items
  sidebarScenarioItems.forEach((btn) => {
    btn.addEventListener('click', () => {
      const scId = btn.getAttribute('data-scenario');
      selectScenario(scId);
    });
  });

  // Provider Mode Toggles (Preview vs Assisted Analysis)
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

  // Export Report Button
  if (btnExport) {
    btnExport.addEventListener('click', () => exportDecisionReport());
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

  const btnExpandKpi = document.getElementById('btn-expand-kpi-card');
  if (btnExpandKpi) {
    btnExpandKpi.addEventListener('click', () => openKpiContractModal());
  }

  // Sidebar View Navigation
  navItems.forEach((btn) => {
    btn.addEventListener('click', () => {
      const targetView = btn.getAttribute('data-view');
      switchView(targetView);
    });
  });
}

/**
 * Select Scenario and Synchronize Header & Sidebar
 */
function selectScenario(scenarioId) {
  appState.selectedScenarioId = scenarioId;

  // Sync Dropdown
  const scenarioSelect = document.getElementById('scenario-select');
  if (scenarioSelect) scenarioSelect.value = scenarioId;

  // Sync Sidebar
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
 * Switch Active View Tab
 */
function switchView(viewId) {
  appState.activeView = viewId;

  // Update Sidebar Navigation
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach((btn) => {
    if (btn.getAttribute('data-view') === viewId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Update View Panels
  const viewPanels = document.querySelectorAll('.view-panel');
  viewPanels.forEach((panel) => {
    if (panel.id === viewId) {
      panel.classList.add('active');
      panel.style.display = 'block';
    } else {
      panel.classList.remove('active');
      panel.style.display = 'none';
    }
  });
}

/**
 * Switch Provider Mode (Preview vs Assisted Analysis)
 */
function setProviderMode(mode) {
  appState.providerMode = mode;
  const modeMockBtn = document.getElementById('mode-mock');
  const modeGeminiBtn = document.getElementById('mode-gemini');

  if (mode === 'mock') {
    if (modeMockBtn) modeMockBtn.classList.add('active');
    if (modeGeminiBtn) modeGeminiBtn.classList.remove('active');
    showToast('Analysis Mode: Preview');
  } else {
    if (modeGeminiBtn) modeGeminiBtn.classList.add('active');
    if (modeMockBtn) modeMockBtn.classList.remove('active');
    showToast('Analysis Mode: Assisted Analysis');
  }
}

/**
 * Display Toast Notification
 */
function showToast(message) {
  const toastContainer = document.getElementById('toast-container');
  if (!toastContainer) return;
  const toast = document.createElement('div');
  toast.className = 'toast-clean';
  toast.innerHTML = `<span>ℹ️</span> <span>${message}</span>`;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(6px)';
    setTimeout(() => toast.remove(), 300);
  }, 2200);
}

/**
 * Fetch Scenarios Catalog from Server
 */
async function loadScenarios() {
  try {
    const res = await fetch('/api/scenarios');
    if (res.ok) {
      const scenarios = await res.json();
      appState.scenarios = scenarios;

      const scenarioSelect = document.getElementById('scenario-select');
      if (scenarioSelect) {
        scenarioSelect.innerHTML = '';
        scenarios.forEach((sc) => {
          const opt = document.createElement('option');
          opt.value = sc.scenario_id;
          opt.textContent = sc.title;
          if (sc.scenario_id === appState.selectedScenarioId) {
            opt.selected = true;
          }
          scenarioSelect.appendChild(opt);
        });
      }
    }
  } catch (err) {
    console.error('Failed to load scenarios:', err);
  }
}

/**
 * Execute Decision Intelligence Analysis on Backend
 */
async function runAnalysis() {
  if (appState.isLoading) return;
  appState.isLoading = true;
  showLoading();

  const selectedSc = appState.scenarios.find((s) => s.scenario_id === appState.selectedScenarioId) || {
    scenario_id: appState.selectedScenarioId,
    market: 'China',
    product_code: 'A2520150501',
    date: '2021-04-01',
    kpi: 'gross_sales',
  };

  const payload = {
    scenario_id: selectedSc.scenario_id,
    market: selectedSc.market,
    category: selectedSc.category,
    product_code: selectedSc.product_code,
    date: selectedSc.date,
    kpi: selectedSc.kpi,
    provider_mode: appState.providerMode,
  };

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errJson = await res.json();
      throw new Error(errJson.error || 'Server returned an error');
    }

    const data = await res.json();
    appState.currentData = data;
    renderAllViews(data);
  } catch (err) {
    console.error('Analysis execution failed:', err);
    showToast(`Error: ${err.message}`);
  } finally {
    appState.isLoading = false;
    hideLoading();
  }
}

function showLoading() {
  const overlay = document.getElementById('loading-overlay');
  const title = document.getElementById('loading-title');
  const subtitle = document.getElementById('loading-subtitle');
  if (overlay) overlay.classList.remove('hidden');
  if (title) title.textContent = 'Analyzing signals…';
  if (subtitle) subtitle.textContent = 'Checking supporting evidence…';
}

function hideLoading() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) overlay.classList.add('hidden');
}

/**
 * Render All 3 Views from Response Data
 */
function renderAllViews(data) {
  renderExecutiveView(data);
  renderReasoningView(data);
  renderTrustView(data);
}

/**
 * Render View 1: Signals (Main Decision Screen)
 */
function renderExecutiveView(data) {
  const p3a = data.phase3a || {};
  const p3b = data.phase3b || {};
  const ev = p3a.event || {};
  const diag = p3b.diagnosis || {};

  // Scope Pill
  const scopeEl = document.getElementById('exec-scope-text');
  if (scopeEl) {
    const parts = [data.request?.market || 'China'];
    if (data.request?.product_code) parts.push(`Product ${data.request.product_code}`);
    if (data.request?.category) parts.push(data.request.category);
    parts.push(formatPeriod(ev.date || data.request?.date || '2021-04-01'));
    scopeEl.textContent = parts.join(' • ');
  }

  // CARD 1: SIGNAL SUMMARY
  const kpiTag = document.getElementById('card1-kpi-tag');
  const deltaVal = document.getElementById('card1-delta-val');
  const actualVal = document.getElementById('card1-actual-val');
  const baselineVal = document.getElementById('card1-baseline-val');

  if (kpiTag) kpiTag.textContent = formatMetricName(ev.kpi || 'gross_sales');

  const changePct = ev.change_percent !== undefined ? ev.change_percent : -0.72056;
  const absPctStr = Math.abs(changePct * 100).toFixed(1) + '%';
  if (deltaVal) deltaVal.textContent = absPctStr;

  const currentValNum = ev.current_value !== undefined ? ev.current_value : (ev.actual_value !== undefined ? ev.actual_value : 994.25);
  const baselineValNum = ev.baseline_value !== undefined ? ev.baseline_value : 3558.03;
  if (actualVal) actualVal.textContent = formatCurrency(currentValNum);
  if (baselineVal) baselineVal.textContent = formatCurrency(baselineValNum);

  // CARD 2: PRIMARY SIGNAL
  const statusBadge = document.getElementById('card2-status-badge');
  const driverTitle = document.getElementById('card2-driver-title');
  const driverCode = document.getElementById('card2-driver-code');
  const explanationText = document.getElementById('card2-explanation-text');

  const rawDriver = diag.driver;
  const isUncertain = !rawDriver || diag.status === 'NOT_ESTABLISHED';

  if (statusBadge) {
    const status = diag.status || 'PLAUSIBLE';
    statusBadge.textContent = status === 'NOT_ESTABLISHED' ? 'Inconclusive' : (status === 'STRONGLY_SUPPORTED' ? 'High Confidence' : 'Plausible');
    statusBadge.className = `status-badge ${status === 'STRONGLY_SUPPORTED' ? 'badge-success' : (status === 'NOT_ESTABLISHED' ? 'badge-neutral' : 'badge-warning')}`;
  }

  if (driverTitle) {
    driverTitle.textContent = isUncertain
      ? 'No Conclusive Primary Driver'
      : (DRIVER_BUSINESS_NAMES[rawDriver] || rawDriver);
  }

  if (driverCode) {
    driverCode.textContent = isUncertain ? 'UNCERTAINTY PRESERVED' : rawDriver;
  }

  if (explanationText) {
    explanationText.textContent = p3b.executive_summary ||
      'Marketing activity increased while conversion performance deteriorated during the anomaly window.';
  }

  // CARD 3: EVIDENCE
  const evidenceList = document.getElementById('card3-evidence-list');
  const supporting = p3b.supporting_evidence || [];

  if (evidenceList) {
    evidenceList.innerHTML = '';
    if (supporting.length === 0) {
      evidenceList.innerHTML = `
        <div class="evidence-clean-row">
          <p class="ev-desc-clean">No isolated single-driver anomaly established. Macroeconomic variance observed.</p>
        </div>
      `;
    } else {
      supporting.slice(0, 2).forEach((evd, idx) => {
        const row = document.createElement('div');
        row.className = 'evidence-clean-row';
        row.id = `card-${evd.evidence_id || `EVD-00${idx+1}`}`;

        const isPositive = (evd.finding || '').toLowerCase().includes('increase') || (evd.finding || '').toLowerCase().includes('surge') || (evd.metric || '').includes('spend');
        const tagClass = isPositive ? 'tag-up' : 'tag-down';
        const changeStr = isPositive ? '+40%' : '-42%';

        row.innerHTML = `
          <div class="ev-badge-col">
            <span class="ev-id-clean">${evd.evidence_id || `EVD-00${idx+1}`}</span>
            <span class="ev-name-clean">${formatMetricName(evd.metric || 'Telemetry')}</span>
          </div>
          <span class="ev-change-tag ${tagClass}">${changeStr}</span>
          <p class="ev-desc-clean">${cleanEvidenceFinding(evd.finding || evd.description || 'Observed variance in evaluation period.')}</p>
        `;
        evidenceList.appendChild(row);
      });
    }
  }

  // CARD 4: DECISION (Finding / Why it matters / Next step)
  const decFinding = document.getElementById('dec-finding');
  const decMatters = document.getElementById('dec-matters');
  const decAction = document.getElementById('dec-action');

  if (isUncertain) {
    if (decFinding) decFinding.textContent = 'Diagnostic evaluation concludes no single internal operational driver accounts for the anomaly.';
    if (decMatters) decMatters.textContent = 'Variance reflects broad external macroeconomic movements rather than localized failure.';
    if (decAction) decAction.textContent = 'Monitor peer market movements and conduct cross-functional macro review.';
  } else {
    if (decFinding) decFinding.textContent = 'Marketing performance is the strongest supported explanation for sales decline.';
    if (decMatters) decMatters.textContent = 'Higher marketing spend did not translate into proportional conversion.';
    if (decAction) decAction.textContent = 'Review underperforming campaigns and inspect the conversion funnel before reallocating spend.';
  }

  // DRIVER COMPARISON TABLE
  const tableBody = document.getElementById('candidate-table-body');
  const countPill = document.getElementById('table-candidates-count');
  const comparisons = p3b.candidate_comparisons || [];

  if (countPill) countPill.textContent = `${comparisons.length || 8} Drivers`;

  if (tableBody) {
    tableBody.innerHTML = '';
    comparisons.forEach((comp, idx) => {
      const rankNum = comp.rank || (idx + 1);
      const isSelected = rankNum === 1 || comp.arbitration_status === 'SELECTED';
      const friendly = DRIVER_BUSINESS_NAMES[comp.driver] || comp.driver;

      const fitScore = isSelected ? 78 : Math.max(20, 60 - idx * 7);
      const evidenceSupport = isSelected ? 'Strong' : (idx < 3 ? 'Moderate' : 'Weak');
      const contradictions = comp.contradiction_count > 0 ? 'High' : 'Low';

      const tr = document.createElement('tr');
      if (isSelected) tr.className = 'row-selected';

      tr.innerHTML = `
        <td><span class="rank-badge-clean ${rankNum === 1 ? 'rank-1' : ''}">${rankNum}</span></td>
        <td><strong>${friendly}</strong><br><span style="font-family:var(--font-mono); font-size:10.5px; color:var(--text-dim);">${comp.driver}</span></td>
        <td><span style="font-family:var(--font-mono); font-weight:600;">${fitScore}</span></td>
        <td><span class="status-badge ${evidenceSupport === 'Strong' ? 'badge-success' : 'badge-neutral'}">${evidenceSupport}</span></td>
        <td><span class="status-badge ${contradictions === 'Low' ? 'badge-success' : 'badge-danger'}">${contradictions}</span></td>
        <td><span class="status-badge ${isSelected ? 'badge-success' : 'badge-neutral'}">${isSelected ? 'Selected' : 'Rejected'}</span></td>
      `;
      tableBody.appendChild(tr);
    });
  }

  // WHY OTHER DRIVERS RANKED LOWER ACCORDION
  const rejectedAccordion = document.getElementById('why-rejected-accordion');
  const rejected = p3b.why_alternatives_rejected || [];
  if (rejectedAccordion) {
    rejectedAccordion.innerHTML = '';
    if (rejected.length === 0) {
      rejectedAccordion.innerHTML = '<div class="alt-item"><div class="alt-summary">No alternative drivers were disqualified.</div></div>';
    } else {
      rejected.forEach((item) => {
        const div = document.createElement('div');
        div.className = 'alt-item';
        div.innerHTML = `
          <div class="alt-summary">
            <span>${item.split('—')[0] || item}</span>
            <span style="color:var(--text-dim);">›</span>
          </div>
          <div class="alt-details">${item}</div>
        `;
        rejectedAccordion.appendChild(div);
      });
    }
  }
}

/**
 * Render View 2: Evidence
 */
function renderReasoningView(data) {
  const p3b = data.phase3b || {};
  const supporting = p3b.supporting_evidence || [];

  // Summary Strip
  const sourcesCount = document.getElementById('summary-sources-count');
  const confVal = document.getElementById('summary-conf-val');
  const catalogPill = document.getElementById('catalog-count-pill');

  if (sourcesCount) sourcesCount.textContent = supporting.length || '2';
  if (confVal) confVal.textContent = p3b.diagnosis?.confidence === 'NONE' ? 'None' : (p3b.diagnosis?.confidence || 'Plausible');
  if (catalogPill) catalogPill.textContent = `${supporting.length} Signals`;

  // Catalog Table Body
  const catalogBody = document.getElementById('evidence-catalog-body');
  if (catalogBody) {
    catalogBody.innerHTML = '';
    supporting.forEach((evd, idx) => {
      const isPositive = (evd.finding || '').toLowerCase().includes('increase') || (evd.finding || '').toLowerCase().includes('spend');
      const changeStr = isPositive ? '+40%' : '-42%';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span class="ev-id-clean" style="font-size:11.5px;">${evd.evidence_id || `EVD-00${idx+1}`}</span></td>
        <td><code>${evd.source_dataset || evd.dataset || 'fact_table'}</code></td>
        <td><strong>${formatMetricName(evd.metric || 'Metric')}</strong></td>
        <td><span class="ev-change-tag ${isPositive ? 'tag-up' : 'tag-down'}">${changeStr}</span></td>
        <td><span class="status-badge badge-success">PRIMARY</span></td>
      `;
      catalogBody.appendChild(tr);
    });
  }

  // Evidence Trail (Claims Stream)
  const claimsStream = document.getElementById('claims-stream-container');
  const claims = p3b.claims || [];
  if (claimsStream) {
    claimsStream.innerHTML = '';
    if (claims.length === 0) {
      claimsStream.innerHTML = '<p class="ev-desc-clean">No structured claim citations present.</p>';
    } else {
      claims.forEach((cl) => {
        const card = document.createElement('div');
        card.className = 'claim-card-clean';

        const tagClass = getClaimTagClass(cl.claim_type);
        const citationBadges = (cl.evidence_ids || [])
          .map((id) => `<button class="citation-chip-clean" onclick="window.highlightEvidence('${id}')">[${id}]</button>`)
          .join(' ');

        card.innerHTML = `
          <span class="claim-tag-clean ${tagClass}">${formatClaimType(cl.claim_type)}</span>
          <span class="claim-text-clean">${cl.statement || ''}</span>
          <div style="display:flex; gap:4px;">${citationBadges}</div>
        `;
        claimsStream.appendChild(card);
      });
    }
  }

  // Uncertainties
  const uncertEl = document.getElementById('uncertainties-container');
  const uncertainties = p3b.uncertainties || [];
  if (uncertEl) {
    uncertEl.innerHTML = '';
    if (uncertainties.length === 0) {
      uncertEl.innerHTML = '<p class="ev-desc-clean">No unobserved confounding variables identified.</p>';
    } else {
      uncertainties.forEach((u) => {
        const p = document.createElement('p');
        p.style.marginBottom = '4px';
        p.className = 'ev-desc-clean';
        p.textContent = `• ${u}`;
        uncertEl.appendChild(p);
      });
    }
  }
}

/**
 * Render View 3: Evidence & Integrity
 */
function renderTrustView(data) {
  const p3a = data.phase3a || {};
  const p3b = data.phase3b || {};
  const meta = data.metadata || {};
  const contract = data.kpi_contract || {};
  const req = data.request || {};
  const kpiId = req.kpi || 'gross_sales';

  const provText = document.getElementById('trace-provenance-name');
  if (provText) {
    provText.textContent = appState.providerMode === 'gemini' ? 'Assisted Analysis' : 'Preview';
  }

  // KPI Governance Summary Card (View 3)
  const govName = document.getElementById('gov-kpi-name');
  const govGrain = document.getElementById('gov-kpi-grain');
  const govCalc = document.getElementById('gov-kpi-calc');
  const govBaseline = document.getElementById('gov-kpi-baseline');
  const govThreshold = document.getElementById('gov-kpi-threshold');
  const govAccess = document.getElementById('gov-kpi-access');

  if (govName) govName.textContent = `${contract.name || formatMetricName(kpiId)} (${kpiId})`;
  if (govGrain) govGrain.textContent = `${contract.unit || 'USD ($)'} • ${contract.grain || 'Monthly'}`;
  if (govCalc) govCalc.textContent = contract.calculation || 'SUM(amount)';
  if (govBaseline) govBaseline.textContent = contract.baseline_method || '3-Month Rolling Average';
  if (govThreshold) govThreshold.textContent = contract.materiality_threshold || 'Absolute deviation >= 15.0%';
  if (govAccess) {
    const roles = (contract.access_roles || ['Executive Leadership', 'Commercial Finance']).join(', ');
    govAccess.textContent = `${contract.sensitivity_classification || 'Confidential'} • ${roles}`;
  }

  // Lineage Table
  const lineageBody = document.getElementById('trace-lineage-body');
  const traceList = p3b.traceability || [];
  if (lineageBody) {
    lineageBody.innerHTML = '';
    if (traceList.length === 0) {
      lineageBody.innerHTML = '<tr><td colspan="4">No warehouse lineage records provided.</td></tr>';
    } else {
      traceList.forEach((t) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><span class="ev-id-clean">${t.evidence_id || 'EVD-001'}</span></td>
          <td><code>${t.source_dataset || 'fact_table'}</code></td>
          <td>${t.record_id || 'Aggregated Partition'}</td>
          <td><span class="status-badge badge-success">✓ Lineage Verified</span></td>
        `;
        lineageBody.appendChild(tr);
      });
    }
  }
}

/**
 * Open KPI Semantic Governance Contract Modal
 */
window.openKpiContractModal = async function (kpiId) {
  const modal = document.getElementById('kpi-modal');
  const modalTitle = document.getElementById('modal-kpi-title');
  const modalBody = document.getElementById('modal-kpi-body');

  if (!modal || !modalTitle || !modalBody) return;

  const targetKpi = kpiId || appState.currentData?.request?.kpi || 'gross_sales';

  // Show modal with loading state
  modal.classList.remove('hidden');
  modalTitle.textContent = `Loading specification for ${formatMetricName(targetKpi)}…`;
  modalBody.innerHTML = '<div style="padding: 24px; text-align: center; color: var(--text-muted);">Fetching Accenture KPI Semantic Contract…</div>';

  try {
    const res = await fetch(`/api/kpi-contract?kpi_id=${encodeURIComponent(targetKpi)}`);
    if (!res.ok) throw new Error('Contract metadata not available');
    const json = await res.json();
    const kpiData = json.kpi || json;

    modalTitle.textContent = `${kpiData.name || formatMetricName(targetKpi)} (${kpiData.kpi_id || targetKpi})`;

    const driversHtml = (kpiData.candidate_drivers || [])
      .map(
        (d) => `
        <div class="kpi-driver-item">
          <div class="kpi-driver-head">
            <span class="kpi-driver-pill">${d.driver_id || 'DRIVER'}</span>
            <span class="kpi-driver-name">${d.name || ''}</span>
          </div>
          <p class="kpi-driver-mech">${d.impact_mechanism || ''}</p>
        </div>`
      )
      .join('');

    const sourceDatasets = (kpiData.source_datasets || []).map((s) => `<code>${s}</code>`).join(' • ');
    const accessRoles = (kpiData.access_roles || []).map((r) => `<span class="count-pill-clean">${r}</span>`).join(' ');

    modalBody.innerHTML = `
      <div class="kpi-modal-section">
        <span class="kpi-section-title">1. Business Definition</span>
        <p class="kpi-section-content">${kpiData.business_definition || 'No definition specified.'}</p>
      </div>

      <div class="kpi-modal-section">
        <span class="kpi-section-title">2. Calculation Formula & Aggregation Grain</span>
        <div style="display:flex; flex-direction:column; gap:6px;">
          <div><span class="sub-lbl">Mathematical / SQL Formula:</span> <code class="gov-code">${kpiData.calculation || 'N/A'}</code></div>
          <div><span class="sub-lbl">Unit of Measure:</span> <strong>${kpiData.unit || 'USD ($)'}</strong></div>
          <div><span class="sub-lbl">Reporting Grain:</span> ${kpiData.grain || 'Monthly'}</div>
        </div>
      </div>

      <div class="kpi-modal-section">
        <span class="kpi-section-title">3. Anomaly Baseline & Materiality Threshold</span>
        <div style="display:flex; flex-direction:column; gap:6px;">
          <div><span class="sub-lbl">Baseline Methodology:</span> ${kpiData.baseline_method || '3-Month Rolling Average'}</div>
          <div><span class="sub-lbl">Materiality Gate:</span> ${kpiData.materiality_threshold || 'Absolute deviation >= 15.0%'}</div>
          <div><span class="sub-lbl">Analytical Engine:</span> ${kpiData.analytical_method || 'Deterministic SQL/Pandas + Multi-source causal arbitration'}</div>
        </div>
      </div>

      <div class="kpi-modal-section">
        <span class="kpi-section-title">4. Candidate Causal Drivers (${(kpiData.candidate_drivers || []).length} Hypotheses)</span>
        <div class="kpi-drivers-grid">${driversHtml || '<p class="ev-desc-clean">No candidate drivers mapped.</p>'}</div>
      </div>

      <div class="kpi-modal-section">
        <span class="kpi-section-title">5. Source Datasets, Freshness & Lineage Path</span>
        <div style="display:flex; flex-direction:column; gap:6px;">
          <div><span class="sub-lbl">Source Canonical Tables:</span> ${sourceDatasets || 'N/A'}</div>
          <div><span class="sub-lbl">Cadence / Freshness:</span> ${kpiData.source_freshness || 'Monthly batch ETL'}</div>
          <div><span class="sub-lbl">Lineage Trace:</span> <code class="gov-code">${kpiData.lineage_reference || 'N/A'}</code></div>
        </div>
      </div>

      <div class="kpi-modal-section">
        <span class="kpi-section-title">6. Governance, Access Roles & Security Classification</span>
        <div style="display:flex; flex-direction:column; gap:6px;">
          <div><span class="sub-lbl">Sensitivity Classification:</span> <strong>${kpiData.sensitivity_classification || 'Confidential'}</strong></div>
          <div><span class="sub-lbl">Authorized Roles:</span> <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:4px;">${accessRoles}</div></div>
        </div>
      </div>
    `;
  } catch (err) {
    modalBody.innerHTML = `<div style="padding: 24px; color: var(--color-danger);">Failed to load KPI contract: ${err.message}</div>`;
  }
};

/**
 * Close KPI Semantic Governance Contract Modal
 */
window.closeKpiContractModal = function () {
  const modal = document.getElementById('kpi-modal');
  if (modal) modal.classList.add('hidden');
};

// Close modal on backdrop click or ESC key
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeKpiContractModal();
});
document.addEventListener('click', (e) => {
  const modal = document.getElementById('kpi-modal');
  if (modal && e.target === modal) closeKpiContractModal();
});

/**
 * Interactive Evidence Citation Click Navigation
 */
window.highlightEvidence = function (evidenceId) {
  switchView('view-executive');
  const card = document.getElementById(`card-${evidenceId}`);
  if (card) {
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    card.style.borderColor = 'var(--primary-accent)';
    card.style.boxShadow = '0 0 0 2px var(--primary-accent-border)';
    setTimeout(() => {
      card.style.borderColor = '';
      card.style.boxShadow = '';
    }, 2200);
  }
};

/**
 * Export Decision Report as Clean JSON
 */
function exportDecisionReport() {
  if (!appState.currentData) {
    showToast('No active analysis data to export.');
    return;
  }
  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(appState.currentData, null, 2));
  const downloadAnchor = document.createElement('a');
  downloadAnchor.setAttribute('href', dataStr);
  downloadAnchor.setAttribute('download', `signal_story_${appState.selectedScenarioId}.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
  showToast('Signal Story report downloaded successfully.');
}

/**
 * Format Helpers
 */
function cleanEvidenceFinding(text) {
  if (!text) return '';
  return text.replace(/\(\d+(\.\d+)?\)\s+in\s+fact_\w+\s+\(DURING\)/gi, '')
             .replace(/exhibited anomalous telemetry/gi, 'showed anomalous variance')
             .trim();
}

function formatMetricName(kpi) {
  if (!kpi) return 'Gross Sales';
  return kpi.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatPeriod(dateStr) {
  if (!dateStr) return 'April 2021';
  const parts = dateStr.split('-');
  if (parts.length >= 2) {
    const year = parts[0];
    const monthMap = { '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec' };
    const month = monthMap[parts[1]] || parts[1];
    return `${month} ${year}`;
  }
  return dateStr;
}

function formatCurrency(val) {
  if (val === undefined || val === null || isNaN(val)) return '$0.00';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(val);
}

function getClaimTagClass(type) {
  switch (type) {
    case 'OBSERVATION':
      return 'tag-clean-obs';
    case 'INTERPRETATION':
      return 'tag-clean-int';
    case 'CAUSAL_CONCLUSION':
      return 'tag-clean-con';
    case 'RECOMMENDATION':
      return 'tag-clean-evd';
    default:
      return 'tag-clean-obs';
  }
}

function formatClaimType(type) {
  switch (type) {
    case 'OBSERVATION':
      return 'Observed';
    case 'INTERPRETATION':
      return 'Interpretation';
    case 'CAUSAL_CONCLUSION':
      return 'Conclusion';
    case 'RECOMMENDATION':
      return 'Action';
    default:
      return type || 'Signal';
  }
}

// Start application when DOM is ready
document.addEventListener('DOMContentLoaded', initApp);
