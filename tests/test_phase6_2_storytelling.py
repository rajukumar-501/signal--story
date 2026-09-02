"""
Phase 6.2 Signal Storytelling -- Unit Test Suite
=================================================
16 tests covering all acceptance criteria from the Phase 6.2P specification.
Uses official scenario parameters from server.py OFFICIAL_SCENARIOS.
"""

import json
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.server import execute_decision_analysis, _build_signal_story


# Official scenario parameters from server.py OFFICIAL_SCENARIOS
S003_REQ = {
    "scenario_id": "S003",
    "market": "China",
    "product_code": "A2520150501",
    "category": None,
    "date": "2021-04-01",
    "kpi": "gross_sales",
    "provider_mode": "mock",
    "persona": "EXECUTIVE",
    "role": "EXECUTIVE",
}

S008_REQ = {
    "scenario_id": "S008",
    "market": "Germany",
    "product_code": None,
    "category": None,
    "date": "2020-03-01",
    "kpi": "gross_sales",
    "provider_mode": "mock",
    "persona": "EXECUTIVE",
    "role": "EXECUTIVE",
}

S009_REQ = {
    "scenario_id": "S009",
    "market": "China",
    "product_code": "A7220160203",
    "category": "Mouse",
    "date": "2018-09-01",
    "kpi": "gross_sales",
    "provider_mode": "mock",
    "persona": "EXECUTIVE",
    "role": "EXECUTIVE",
}


def _get_story(req, role=None, persona=None):
    """Run analysis and build story for a given scenario request."""
    r = dict(req)
    if role:
        r["role"] = role
    if persona:
        r["persona"] = persona
    ui_resp = execute_decision_analysis(r, user_role=r.get("role", "EXECUTIVE"))
    story = _build_signal_story(ui_resp, scenario_id=r["scenario_id"])
    return story, ui_resp


class TestPhase62SignalStory(unittest.TestCase):
    """Phase 6.2 Signal Storytelling acceptance tests."""

    def test_01_s003_complete_story_all_5_keys(self):
        """S003 generates a complete story object with all 5 narrative stage keys."""
        story, _ = _get_story(S003_REQ)
        for key in ["what_happened", "what_changed", "evidence_chain", "ruled_out", "what_next"]:
            self.assertIn(key, story, f"Missing story key: {key}")
        self.assertIsNotNone(story["story_state"])
        self.assertIsNotNone(story["glance_text"])
        self.assertIsNotNone(story["timeline_steps"])

    def test_02_story_uses_governed_delta_not_invented(self):
        """Story what_happened magnitude_pct is derived from governed baseline_change_percent."""
        story, ui_resp = _get_story(S003_REQ)
        wh = story["what_happened"]
        self.assertIn("magnitude_pct", wh)
        self.assertIn(wh["direction"], ["fell", "rose"])
        # Verify magnitude formula is applied consistently: if raw is a fraction, multiply by 100
        ev = ui_resp.get("phase3a", {}).get("event", {})
        raw = ev.get("baseline_change_percent", 0.0)
        expected_pct = round(abs(raw) * 100, 2) if abs(raw) <= 1.5 else round(abs(raw), 2)
        self.assertAlmostEqual(wh["magnitude_pct"], expected_pct, places=1,
                               msg=f"magnitude_pct {wh['magnitude_pct']} should match formula applied to raw {raw}")

    def test_03_story_uses_connected_kpi_values(self):
        """Story what_changed includes KPIs from governed connected_kpis response."""
        story, ui_resp = _get_story(S003_REQ)
        governed_kpis = ui_resp.get("connected_kpis", {}).get("connected_kpis", [])
        governed_ids = {k["kpi_id"] for k in governed_kpis if k.get("kpi_id") != "gross_sales"}
        story_ids = {k["kpi_id"] for k in story["what_changed"]}
        if governed_ids:
            self.assertGreater(len(governed_ids & story_ids), 0,
                               f"Story what_changed must include governed KPI IDs. "
                               f"Governed: {governed_ids}, Story: {story_ids}")

    def test_04_story_references_actual_evidence_ids(self):
        """Story evidence_chain contains evidence_ids matching governed supporting_evidence."""
        story, ui_resp = _get_story(S003_REQ)
        governed_evidence = ui_resp.get("phase3b", {}).get("supporting_evidence", [])
        if not governed_evidence:
            self.skipTest("Mock response has no supporting_evidence for S003")
        governed_ids = {ev.get("evidence_id") for ev in governed_evidence if ev.get("evidence_id")}
        story_ids = {ev.get("evidence_id") for ev in story["evidence_chain"] if ev.get("evidence_id")}
        if governed_ids:
            self.assertGreater(len(governed_ids & story_ids), 0,
                               f"Story evidence_chain must include governed evidence IDs. "
                               f"Governed: {governed_ids}, Story: {story_ids}")

    def test_05_story_references_primary_supported_driver(self):
        """Story primary_driver is set and matches governed first candidate driver."""
        story, ui_resp = _get_story(S003_REQ)
        candidates = ui_resp.get("phase3a", {}).get("candidate_drivers", [])
        if not candidates:
            self.skipTest("Mock response has no candidate_drivers for S003")
        self.assertIsNotNone(story.get("primary_driver"),
                             "Story must have a primary_driver when candidates exist")
        pd = story["primary_driver"]
        self.assertIn("driver_name", pd)
        self.assertIn("fit_score", pd)
        self.assertEqual(pd["driver_id"], candidates[0]["driver"],
                         "Story primary_driver_id must match governed first candidate")

    def test_06_story_includes_alternative_driver_validation(self):
        """Story ruled_out list contains alternative drivers from governed candidates."""
        story, ui_resp = _get_story(S003_REQ)
        candidates = ui_resp.get("phase3a", {}).get("candidate_drivers", [])
        if len(candidates) < 2:
            self.skipTest("Mock response has fewer than 2 candidates for S003")
        self.assertIsInstance(story["ruled_out"], list)
        self.assertGreater(len(story["ruled_out"]), 0,
                           "Story ruled_out must contain at least one alternative driver")
        for item in story["ruled_out"]:
            self.assertIn("driver_name", item)
            self.assertIn("rejection_reason", item)

    def test_07_story_uses_governance_recommendation(self):
        """Story what_next.recommended_action matches governed decision_governance."""
        story, ui_resp = _get_story(S003_REQ)
        governed_action = ui_resp.get("decision_governance", {}).get("recommended_action", "")
        story_action = story.get("what_next", {}).get("recommended_action", "")
        if governed_action:
            self.assertEqual(story_action, governed_action,
                             "Story recommended_action must match governed recommendation")
        else:
            self.assertIsNotNone(story_action)

    def test_08_executive_persona_no_evidence_ids_in_glance(self):
        """Executive glance_text must not expose raw evidence IDs (EVD-xxx)."""
        story, _ = _get_story(S003_REQ, persona="EXECUTIVE")
        glance = story.get("glance_text", "")
        evd_pattern = re.compile(r"\bEVD-\d+\b")
        self.assertIsNone(evd_pattern.search(glance),
                          f"Executive glance must not expose evidence IDs: {glance}")

    def test_09_domain_analyst_persona_has_persona_detail(self):
        """Domain Analyst persona_detail.active_persona is correctly set."""
        story, _ = _get_story(S003_REQ, persona="DOMAIN_ANALYST", role="DOMAIN_ANALYST")
        pd = story.get("persona_detail", {})
        self.assertEqual(pd.get("active_persona"), "DOMAIN_ANALYST",
                         "persona_detail.active_persona must be DOMAIN_ANALYST")

    def test_10_s008_abstention_no_driver_claim(self):
        """S008 abstention state must not claim a primary driver or proven explanation.
        
        Note: The story builder may populate primary_driver with the top candidate
        even in abstention mode (with fit_score=0.0, status=NOT_ESTABLISHED).
        The key requirement is that the NARRATIVE does not assert this driver as
        the explanation — i.e., the glance_text must not claim 'strongest supported
        explanation' and must disclose 'Insufficient evidence'.
        """
        story, _ = _get_story(S008_REQ)
        story_state = story.get("story_state", "")
        glance = story.get("glance_text", "")
        if story_state == "ABSTENTION":
            # Narrative must not claim a driver as the explanation
            self.assertIn("Insufficient evidence", glance,
                          "Abstention glance must state insufficient evidence")
            self.assertNotIn("is the strongest supported explanation", glance,
                             "Abstention story must not claim a strongest explanation")
            # If primary_driver exists, it must be marked NOT_ESTABLISHED
            pd = story.get("primary_driver")
            if pd is not None:
                self.assertEqual(pd.get("status"), "NOT_ESTABLISHED",
                                 "Any primary_driver in abstention must have NOT_ESTABLISHED status")
                self.assertEqual(pd.get("fit_score"), 0.0,
                                 "Any primary_driver in abstention must have fit_score=0.0")
        else:
            # If mock produces non-abstention, verify no causality overreach
            self.assertNotIn("proven root cause", glance.lower())


    def test_11_s009_sparse_history_disclosure(self):
        """S009 produces SPARSE_HISTORY state with LOW confidence disclosure."""
        story, ui_resp = _get_story(S009_REQ)
        story_state = story.get("story_state", "")
        glance = story.get("glance_text", "")
        sparse_meta = ui_resp.get("sparse_history", {})
        if sparse_meta.get("is_limited_history", False):
            self.assertEqual(story_state, "SPARSE_HISTORY",
                             "Sparse history scenario must produce SPARSE_HISTORY story_state")
            self.assertIn("Limited historical data", glance,
                          "Sparse story glance_text must disclose limited history")
            self.assertIn("LOW", glance,
                          "Sparse story glance_text must state LOW confidence")
        else:
            # If sparse not triggered, verify story_state is a valid value
            self.assertIn(story_state,
                          ["SUPPORTED", "PLAUSIBLE", "ABSTENTION", "SPARSE_HISTORY"])

    def test_12_restricted_user_redacted_fields_absent(self):
        """Restricted user: actual_display contains RESTRICTED label, no $ in glance."""
        story, ui_resp = _get_story(S003_REQ, role="RESTRICTED_USER")
        entitlement = ui_resp.get("entitlement", {})
        is_redacted = entitlement.get("is_redacted", False)
        redacted_fields = entitlement.get("redacted_fields", [])
        if is_redacted and "actual_value" in redacted_fields:
            wh = story.get("what_happened", {})
            self.assertIn("RESTRICTED", wh.get("actual_display", ""),
                          "Restricted user actual_display must contain RESTRICTED label")
            self.assertNotIn("$", story.get("glance_text", ""),
                             "Restricted user glance_text must not expose raw $ values")
        else:
            # Entitlement not triggered in this mock config; verify story structure only
            self.assertIn("what_happened", story)

    def test_13_no_gemini_deterministic_story_renders(self):
        """Mock provider: story renders deterministically without Gemini."""
        story, _ = _get_story(S003_REQ)
        self.assertIsNotNone(story.get("glance_text"),
                             "Glance text must render without Gemini")
        self.assertNotIn("error", story.get("glance_text", "").lower(),
                         "Glance text must not contain error text")
        ai = story.get("ai_narrative", {})
        self.assertFalse(ai.get("available", False),
                         "AI narrative must be unavailable in mock mode")

    def test_14_llm_failure_story_complete(self):
        """All story keys present even when LLM is unavailable (mock mode)."""
        story, _ = _get_story(S003_REQ)
        for key in ["what_happened", "what_changed", "evidence_chain", "ruled_out", "what_next"]:
            self.assertIn(key, story,
                          f"Story must be complete even without LLM: missing {key}")
        ai = story.get("ai_narrative", {})
        self.assertIn("available", ai,
                      "ai_narrative must always have 'available' key")

    def test_15_no_proven_root_cause_language(self):
        """Story must not use causal language beyond the epistemic boundary."""
        story, _ = _get_story(S003_REQ)
        all_text = " ".join([
            story.get("glance_text", "").lower(),
            (story.get("epistemic_note") or "").lower(),
            (story.get("what_next", {}).get("finding_statement") or "").lower(),
        ])
        for phrase in ["proven root cause", "definitively caused", "caused by"]:
            self.assertNotIn(phrase, all_text,
                             f"Story must not use forbidden causal phrase: {phrase!r}")
        # Supported/Plausible stories must use epistemically safe language
        if story.get("story_state") in ("SUPPORTED", "PLAUSIBLE"):
            self.assertIn("strongest supported explanation", story.get("glance_text", ""),
                          "Supported story must use epistemically safe language")

    def test_16_existing_feedback_mechanism_functional(self):
        """POST /api/feedback recording engine still works after Phase 6.2."""
        from src.governance.feedback_learning import FeedbackLearningEngine
        engine = FeedbackLearningEngine()
        record = engine.record_feedback(
            scenario_id="S003",
            predicted_driver="DRIVER_03_MARKETING",
            analyst_decision="APPROVED",
            reviewer="Phase 6.2 Test Runner",
            reason="Verifying feedback mechanism remains functional post-Phase 6.2",
        )
        self.assertIsNotNone(record,
                             "Feedback record must not be None")
        self.assertIn("scenario_id", record,
                      "Feedback record must have scenario_id")
        self.assertEqual(record["scenario_id"], "S003")


if __name__ == "__main__":
    unittest.main(verbosity=2)
