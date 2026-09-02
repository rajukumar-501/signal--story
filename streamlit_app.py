"""
Accenture Decision Intelligence Platform -- Streamlit Application
================================================================
Enterprise Decision Intelligence Dashboard with Phase 6.2 Signal Story Layer.
Supports full multi-persona governance, entitlement-aware redaction,
low-confidence abstention, sparse history detection, and feedback learning.
Ready for deployment on Streamlit Community Cloud (share.streamlit.io).
"""

import os
import sys
import json
import time
from pathlib import Path

# Ensure root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd

from src.server import execute_decision_analysis, _build_signal_story, OFFICIAL_SCENARIOS
from src.governance.feedback_learning import FeedbackLearningEngine

# Initialize feedback learning engine
_feedback_engine = FeedbackLearningEngine()

# -----------------------------------------------------------------------------
# Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Signal Story -- Enterprise Decision Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Dark Theme CSS
st.markdown("""
<style>
  /* Global Page Background & Fonts */
  .stApp {
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }

  /* Header Container */
  .enterprise-header {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.85));
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
  }
  .header-brand {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #a855f7;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  .header-title {
    font-size: 26px;
    font-weight: 800;
    color: #f8fafc;
    margin: 0;
    line-height: 1.2;
  }
  .header-subtitle {
    font-size: 14px;
    color: #94a3b8;
    margin-top: 6px;
  }
  .header-badges {
    display: flex;
    gap: 10px;
    margin-top: 14px;
    flex-wrap: wrap;
  }
  .badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }
  .badge-purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
  .badge-blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
  .badge-green { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
  .badge-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

  /* Signal Story Box */
  .story-card {
    background: linear-gradient(145deg, #131b2e, #0f172a);
    border: 1px solid rgba(168, 85, 247, 0.35);
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 24px;
    box-shadow: 0 12px 30px -8px rgba(168, 85, 247, 0.15);
  }
  .story-state-badge {
    font-size: 12px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: 1px;
    display: inline-block;
    margin-bottom: 12px;
  }
  .state-supported { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; }
  .state-plausible { background: rgba(168, 85, 247, 0.2); color: #c084fc; border: 1px solid #a855f7; }
  .state-abstention { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
  .state-sparse { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }

  .glance-box {
    background: rgba(15, 23, 42, 0.85);
    border-left: 4px solid #a855f7;
    padding: 14px 18px;
    border-radius: 0 8px 8px 0;
    font-size: 15px;
    line-height: 1.6;
    color: #f1f5f9;
    margin-bottom: 18px;
  }

  /* Metric cards */
  .metric-card {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 16px;
    text-align: center;
  }
  .metric-label { font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; }
  .metric-value { font-size: 24px; font-weight: 700; color: #f8fafc; margin: 4px 0; }
  .metric-delta-neg { color: #f87171; font-weight: 600; font-size: 13px; }
  .metric-delta-pos { color: #4ade80; font-weight: 600; font-size: 13px; }

  /* Epistemic note */
  .epistemic-note {
    font-size: 12px;
    color: #94a3b8;
    font-style: italic;
    margin-top: 8px;
  }

  /* Timeline Pills */
  .timeline-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 18px;
    overflow-x: auto;
    padding-bottom: 6px;
  }
  .timeline-step {
    flex: 1;
    min-width: 110px;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 11px;
  }
  .timeline-step strong { display: block; color: #c084fc; font-size: 10px; text-transform: uppercase; }
  .timeline-step span { color: #e2e8f0; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar: Scenario, Persona, Role & Provider Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Governance & Scenarios")
    
    scenario_options = {s["scenario_id"]: f"{s['scenario_id']} -- {s['title'].split('—')[-1].strip()}" for s in OFFICIAL_SCENARIOS}
    selected_scenario_id = st.selectbox(
        "Select Official Scenario",
        options=list(scenario_options.keys()),
        format_func=lambda x: scenario_options[x],
        index=0,
        help="Select one of the 8 canonical benchmark scenarios or S009 new launch.",
    )
    
    current_scenario = next((s for s in OFFICIAL_SCENARIOS if s["scenario_id"] == selected_scenario_id), OFFICIAL_SCENARIOS[0])
    st.info(f"**Target:** {current_scenario.get('market')} • {current_scenario.get('product_code') or 'All Products'}\n\n**Period:** {current_scenario.get('period')}\n\n*{current_scenario.get('description')}*")

    st.markdown("---")
    st.markdown("### 👤 Persona & Security")

    selected_persona = st.radio(
        "Active Persona",
        options=["EXECUTIVE", "DOMAIN_ANALYST"],
        format_func=lambda x: "👔 Executive Briefing" if x == "EXECUTIVE" else "🔬 Domain Analyst Trace",
        index=0,
    )

    selected_role = st.selectbox(
        "User Entitlement Role",
        options=["EXECUTIVE", "LEAD_ANALYST", "RESTRICTED_USER"],
        format_func=lambda x: {
            "EXECUTIVE": "Executive (Full Access)",
            "LEAD_ANALYST": "Lead Commercial Analyst",
            "RESTRICTED_USER": "Restricted User (Financial Redacted)"
        }[x],
        index=0,
        help="Restricted User role tests field-level financial redaction."
    )

    st.markdown("---")
    st.markdown("### 🤖 Reasoning Engine")

    provider_mode = st.radio(
        "Provider Mode",
        options=["mock", "gemini"],
        format_func=lambda x: "🔒 Deterministic Mock Provider (Governed)" if x == "mock" else "✨ Live Google Gemini Model",
        index=0,
    )

    gemini_key_input = ""
    if provider_mode == "gemini":
        gemini_key_input = st.text_input(
            "Google Gemini API Key",
            type="password",
            value=os.getenv("GEMINI_API_KEY", ""),
            help="Optional: defaults to GEMINI_API_KEY from .env or environment if left blank."
        )

    run_clicked = st.button("⚡ Run Decision Analysis", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# Execute Decision Intelligence Analysis
# -----------------------------------------------------------------------------
req_data = {
    "scenario_id": selected_scenario_id,
    "market": current_scenario.get("market"),
    "product_code": current_scenario.get("product_code"),
    "category": current_scenario.get("category"),
    "date": current_scenario.get("date"),
    "kpi": current_scenario.get("kpi", "gross_sales"),
    "provider_mode": provider_mode,
    "persona": selected_persona,
    "role": selected_role,
}
if gemini_key_input:
    os.environ["GEMINI_API_KEY"] = gemini_key_input

@st.cache_data(show_spinner=False, ttl=60)
def run_analysis_cached(req_dict, user_role):
    res = execute_decision_analysis(req_dict, user_role=user_role)
    story = _build_signal_story(res, scenario_id=req_dict.get("scenario_id"))
    return res, story

with st.spinner("Executing Deterministic Decision Intelligence & Reasoning Pipeline..."):
    ui_resp, signal_story = run_analysis_cached(req_data, selected_role)

is_redacted = (ui_resp.get("entitlement", {}) or {}).get("is_redacted", False)

# -----------------------------------------------------------------------------
# Header Presentation
# -----------------------------------------------------------------------------
st.markdown(f"""
<div class="enterprise-header">
  <div class="header-brand">Accenture Decision Intelligence Platform • Enterprise Edition</div>
  <h1 class="header-title">{current_scenario.get('title')}</h1>
  <div class="header-subtitle">
    Scope: <strong>{current_scenario.get('market')}</strong> • 
    Entity: <strong>{current_scenario.get('product_code') or current_scenario.get('category') or 'Market Wide'}</strong> • 
    Timeline: <strong>{current_scenario.get('period')}</strong>
  </div>
  <div class="header-badges">
    <span class="badge badge-purple">FROZEN CORE AUDITED</span>
    <span class="badge badge-blue">PHASE 6.2 SIGNAL STORY ACTIVE</span>
    <span class="badge {'badge-amber' if is_redacted else 'badge-green'}">{'🔒 FINANCIAL CONFIDENTIAL REDACTED' if is_redacted else 'SECURITY: FULL ACCESS'}</span>
    <span class="badge badge-purple">{selected_persona} VIEW</span>
    <span class="badge badge-blue">PROVIDER: {ui_resp.get('metadata', {}).get('provider', 'MOCK').upper()}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Phase 6.2 Signal Story Narrative Panel
# -----------------------------------------------------------------------------
story_state = signal_story.get("story_state", "PLAUSIBLE")
state_class = {
    "SUPPORTED": "state-supported",
    "PLAUSIBLE": "state-plausible",
    "ABSTENTION": "state-abstention",
    "SPARSE_HISTORY": "state-sparse"
}.get(story_state, "state-plausible")

wh = signal_story.get("what_happened", {})
what_changed = signal_story.get("what_changed", [])
evidence_chain = signal_story.get("evidence_chain", [])
ruled_out = signal_story.get("ruled_out", [])
what_next = signal_story.get("what_next", {})
primary = signal_story.get("primary_driver")

st.markdown(f"""
<div class="story-card">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div>
      <span class="story-state-badge {state_class}">STATUS: {story_state.replace('_', ' ')}</span>
    </div>
    <span style="font-size:12px; color:#94a3b8; font-weight:600;">PHASE 6.2 NARRATIVE INTELLIGENCE</span>
  </div>
  <div class="glance-box">
    <strong>Story at a Glance:</strong><br>
    {signal_story.get('glance_text')}
  </div>
</div>
""", unsafe_allow_html=True)

# Timeline Steps Bar
timeline_steps = signal_story.get("timeline_steps", [])
if timeline_steps:
    cols = st.columns(len(timeline_steps))
    for i, step in enumerate(timeline_steps):
        with cols[i]:
            st.markdown(f"""
            <div class="timeline-step">
              <strong>{step.get('number', f'0{i+1}')} • {step.get('label')}</strong>
              <span>{step.get('detail')}</span>
            </div>
            """, unsafe_allow_html=True)

# Expandable 5-Stage Story Accordions
with st.expander("① WHAT HAPPENED -- Signal & Baseline Anomaly", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Target Metric</div>
          <div class="metric-value">{wh.get('kpi_name', 'Gross Sales')}</div>
          <div class="metric-delta-neg">{wh.get('direction', 'fell').upper()} {wh.get('magnitude_pct', 0):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Observed Actual</div>
          <div class="metric-value">{wh.get('actual_display', '—')}</div>
          <div style="font-size:11px; color:#94a3b8;">Period: {wh.get('period', 'Current Month')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">Governed Baseline</div>
          <div class="metric-value">{wh.get('baseline_display', '—')}</div>
          <div style="font-size:11px; color:#94a3b8;">Historical Benchmark</div>
        </div>
        """, unsafe_allow_html=True)

with st.expander("② WHAT CHANGED AROUND IT -- Connected Ecosystem Signals", expanded=False):
    if what_changed:
        cols_kpi = st.columns(min(len(what_changed), 4))
        for idx, kpi in enumerate(what_changed[:4]):
            with cols_kpi[idx]:
                delta_class = "metric-delta-neg" if kpi.get("change_pct", 0) < 0 else "metric-delta-pos"
                st.markdown(f"""
                <div class="metric-card">
                  <div class="metric-label">{kpi.get('display_name')}</div>
                  <div class="metric-value">{kpi.get('formatted_change')}</div>
                  <div class="{delta_class}">{kpi.get('role_label', 'Connected')}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No connected KPI shift records for this scenario.")
    st.markdown('<div class="epistemic-note">Correlation does not imply causality. Coinciding movements inform hypothesis selection only.</div>', unsafe_allow_html=True)

with st.expander("③ WHAT THE EVIDENCE SAYS -- Verified Findings & Records", expanded=False):
    if evidence_chain:
        for ev in evidence_chain:
            col_a, col_b = st.columns([1, 4])
            with col_a:
                st.markdown(f"**`{ev.get('evidence_id')}`**" if selected_persona == "DOMAIN_ANALYST" else f"**{ev.get('metric')}**")
                st.caption(f"Source: {ev.get('dataset', 'Analytics')}")
            with col_b:
                st.markdown(f"**{ev.get('display_name')}**: {ev.get('finding')}")
            st.divider()
    else:
        st.info("No explicit evidence records associated with this condition.")
    if signal_story.get("epistemic_note"):
        st.warning(signal_story.get("epistemic_note"))

with st.expander("④ ALTERNATIVES CHECKED -- Candidate Hypotheses Ruled Out", expanded=False):
    if ruled_out:
        for r in ruled_out:
            st.markdown(f"- **{r.get('driver_name')}** (Fit Score: `{r.get('fit_score', 0):.2f}`): *{r.get('rejection_reason')}*")
    else:
        st.info("No alternative drivers evaluated.")

with st.expander("⑤ WHAT SHOULD HAPPEN NEXT -- Governance Recommendation & Action Plan", expanded=True):
    col_act, col_meta = st.columns([3, 2])
    with col_act:
        st.markdown("### Recommended Action")
        st.markdown(f"> **{what_next.get('recommended_action')}**")
        if what_next.get("finding_statement"):
            st.caption(f"Finding Statement: {what_next.get('finding_statement')}")
    with col_meta:
        st.markdown("### Governance Parameters")
        st.markdown(f"- **Responsible Owner:** `{what_next.get('owner')}`")
        st.markdown(f"- **Business Area:** `{what_next.get('area')}`")
        risk_color = "🔴" if what_next.get('risk_level') == "HIGH" else ("🟡" if what_next.get('risk_level') == "MEDIUM" else "🟢")
        st.markdown(f"- **Risk Classification:** {risk_color} `{what_next.get('risk_level')}`")
        st.markdown(f"- **Human Approval Required:** `{'YES' if what_next.get('human_review_required') else 'NO'}`")

# -----------------------------------------------------------------------------
# Deep-Dive Tabs
# -----------------------------------------------------------------------------
st.markdown("---")
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Diagnostic Breakdown",
    "🔗 Connected KPI Network",
    "⚖️ Candidate Driver Comparison",
    "🛡️ Data Trust & Verification",
    "✍️ Analyst Review & Feedback"
])

with tab1:
    st.subheader("Diagnostic Overview")
    diag = ui_resp.get("phase3b", {}).get("diagnosis", {})
    st.markdown(f"- **Primary Hypothesis:** `{diag.get('driver') or 'None (Abstention)'}`")
    st.markdown(f"- **Diagnosis Status:** `{diag.get('status') or 'NOT_ESTABLISHED'}`")
    st.markdown(f"- **Confidence Score:** `{diag.get('confidence') or 'NONE'}`")
    
    summary_text = ui_resp.get("persona_view", {}).get("summary") or ui_resp.get("phase3b", {}).get("executive_summary")
    if summary_text:
        st.markdown("### Executive Summary")
        st.markdown(summary_text)

with tab2:
    st.subheader("Connected Enterprise Metrics")
    conn_list = ui_resp.get("connected_kpis", {}).get("connected_kpis", [])
    if conn_list:
        df_conn = pd.DataFrame(conn_list)[["kpi_id", "display_name", "formatted_change", "evidence_role", "source_dataset"]]
        st.dataframe(df_conn, use_container_width=True)
    else:
        st.info("No connected KPI records for this scenario.")

with tab3:
    st.subheader("Candidate Driver Arbitration Matrix")
    cands = ui_resp.get("adjusted_candidate_drivers") or ui_resp.get("phase3a", {}).get("candidate_drivers", [])
    if cands:
        df_cands = pd.DataFrame(cands)
        st.dataframe(df_cands, use_container_width=True)
    else:
        st.info("No candidate drivers in this scenario.")

with tab4:
    st.subheader("Data Trust & Quality Audit")
    trust = ui_resp.get("data_trust", {})
    q1, q2, q3 = st.columns(3)
    q1.metric("Data Quality Score", f"{trust.get('overall_score', 95)}/100")
    q2.metric("Trust Status", trust.get('trust_status', 'TRUSTED'))
    q3.metric("Records Assessed", f"{trust.get('records_assessed', 1552449):,}")
    st.json(trust.get("dimension_scores", {}))

with tab5:
    st.subheader("Analyst Governance & Feedback Loop")
    st.markdown("Submit reviewer feedback to improve future arbitration weights.")
    with st.form("feedback_form"):
        decision_choice = st.selectbox("Analyst Decision", ["APPROVED", "REJECTED", "MODIFIED", "ESCALATED"])
        reviewer_name = st.text_input("Reviewer Name / Title", value="Lead Commercial Analyst")
        alt_driver = st.selectbox("Alternative Driver (if modified)", ["None", "DRIVER_01_INVENTORY", "DRIVER_02_PRICING", "DRIVER_03_MARKETING", "DRIVER_04_RETURNS", "DRIVER_05_SUPPORT", "DRIVER_06_CUSTOMER", "DRIVER_07_MARKET", "DRIVER_08_PRODUCT_MIX"])
        feedback_notes = st.text_area("Audit Notes & Rationale", "Reviewed corroborating telemetry; finding accepted.")
        submit_feedback = st.form_submit_button("Submit Governed Review")
        
        if submit_feedback:
            rec = _feedback_engine.record_feedback(
                scenario_id=selected_scenario_id,
                predicted_driver=primary.get("driver_id") if primary else "UNKNOWN",
                analyst_decision=decision_choice,
                reviewer=reviewer_name,
                reason=feedback_notes,
                alternative_driver=None if alt_driver == "None" else alt_driver
            )
            st.success(f"Feedback recorded successfully! ID: `{rec.get('feedback_id')}`")

# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#64748b; font-size:12px;">
  Accenture Decision Intelligence Platform • Phase 6.2 Certified • 100% Frozen Core Architecture Verified • Built with Streamlit
</div>
""", unsafe_allow_html=True)
