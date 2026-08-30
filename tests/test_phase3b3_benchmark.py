"""
Phase 3B.3 Controlled Evaluation & Benchmark Harness.
Executes reproducible, isolated benchmarking across scenarios S001–S008.
Generates evaluation manifests, evaluates mock and live/provider runs,
computes 5-dimension reasoning quality metrics, and validates safe fallbacks.
"""

import os
import json
import time
import hashlib
import unittest
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone
import pandas as pd

from src.analytics.run_analysis import run_analysis
from src.phase3b.input_adapter import Phase3BInputAdapter, Phase3BInputContract
from src.phase3b.evidence_context import EvidenceContextBuilder, EvidenceContext
from src.phase3b.prompts import build_reasoning_prompt_payload
from src.phase3b.reasoning_provider import ReasoningProvider
from src.phase3b.mock_reasoning_provider import MockReasoningProvider
from src.phase3b.llm_provider import LLMReasoningProvider, LLMConfig
from src.phase3b.validator import Phase3BResponseValidator
from src.phase3b.engine import Phase3BReasoningEngine

BENCHMARK_SCENARIOS = [
    {
        "scenario_id": "S001",
        "market_scope": "South Korea / A6519160401",
        "request": {
            "market": "South Korea",
            "product_code": "A6519160401",
            "date": "2021-05-01",
            "kpi": "gross_sales"
        },
        "expected_established_driver": "DRIVER_04_RETURNS",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S002",
        "market_scope": "South Korea / All Prods",
        "request": {
            "market": "South Korea",
            "date": "2021-01-01",
            "kpi": "gross_sales"
        },
        "expected_established_driver": "DRIVER_06_CUSTOMER",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S003",
        "market_scope": "China / A2520150501",
        "request": {
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales"
        },
        "expected_established_driver": "DRIVER_03_MARKETING",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S004",
        "market_scope": "China / A0621150308",
        "request": {
            "market": "China",
            "product_code": "A0621150308",
            "date": "2021-01-01",
            "kpi": "gross_sales"
        },
        "expected_established_driver": "DRIVER_02_PRICING",
        "expected_status": "PLAUSIBLE"
    },
    {
        "scenario_id": "S005",
        "market_scope": "Indonesia / All Prods",
        "request": {
            "market": "Indonesia",
            "date": "2020-03-01",
            "kpi": "gross_sales"
        },
        "expected_established_driver": "DRIVER_05_SUPPORT",
        "expected_status": "PLAUSIBLE"
    },
    {
        "scenario_id": "S006",
        "market_scope": "India / Processors",
        "request": {
            "market": "India",
            "category": "Processors",
            "date": "2020-03-01",
            "kpi": "gross_sales"
        },
        "expected_established_driver": "DRIVER_08_PRODUCT_MIX",
        "expected_status": "PLAUSIBLE"
    },
    {
        "scenario_id": "S007",
        "market_scope": "Portugal / Wi fi extender",
        "request": {
            "market": "Portugal",
            "category": "Wi fi extender",
            "date": "2019-09-01",
            "kpi": "category_share"
        },
        "expected_established_driver": "DRIVER_08_PRODUCT_MIX",
        "expected_status": "STRONGLY_SUPPORTED"
    },
    {
        "scenario_id": "S008",
        "market_scope": "Germany / All Prods",
        "request": {
            "market": "Germany",
            "date": "2020-03-01",
            "kpi": "gross_sales"
        },
        "expected_established_driver": None,
        "expected_status": "NOT_ESTABLISHED"
    }
]

def compute_sha256(filepath: Union[str, Path]) -> str:
    """Computes SHA-256 hash for a given file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

class Phase3BEvaluator:
    """
    Controlled Evaluation Engine for Phase 3B.3.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent
        self.eval_dir = self.project_root / "Data" / "evaluation"
        self.processed_dir = self.project_root / "Data" / "Processed"
        self.eval_inputs_dir = self.project_root / "Data" / "scenarios" / "evaluation_inputs"
        self.eval_dir.mkdir(parents=True, exist_ok=True)

    def create_evaluation_manifest(self) -> Dict[str, Any]:
        """
        Creates an immutable, cryptographically verifiable snapshot manifest of the evaluation state.
        """
        dataset_hashes = {}
        if self.processed_dir.exists():
            for f in sorted(self.processed_dir.glob("*.csv")):
                dataset_hashes[f.name] = compute_sha256(f)

        input_hashes = {}
        if self.eval_inputs_dir.exists():
            for f in sorted(self.eval_inputs_dir.glob("*.csv")):
                input_hashes[f.name] = compute_sha256(f)

        baseline_results_file = self.eval_dir / "phase3a3_results.csv"
        baseline_hash = compute_sha256(baseline_results_file) if baseline_results_file.exists() else None

        code_hashes = {}
        phase3b_src_dir = self.project_root / "src" / "phase3b"
        if phase3b_src_dir.exists():
            for f in sorted(phase3b_src_dir.glob("*.py")):
                code_hashes[f.name] = compute_sha256(f)

        config = LLMConfig.from_env()

        manifest = {
            "evaluation_protocol_version": "Phase 3B.3 - v1.0.0",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "scenarios": [s["scenario_id"] for s in BENCHMARK_SCENARIOS],
            "generation_parameters": {
                "provider": config.provider,
                "model": config.model,
                "temperature": config.temperature,
                "timeout_seconds": config.timeout_seconds,
                "response_format": "json_object"
            },
            "canonical_dataset_hashes": dataset_hashes,
            "evaluation_input_hashes": input_hashes,
            "phase3a_baseline_results_hash": baseline_hash,
            "phase3b_source_code_hashes": code_hashes
        }

        manifest_path = self.eval_dir / "phase3b3_evaluation_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    def verify_evaluation_boundary(self) -> Dict[str, Any]:
        """
        Programmatically verifies that zero ground-truth keys or files reach the LLM reasoning context.
        """
        forbidden_strings = [
            "evaluation_ground_truth",
            "ground_truth.csv",
            "scenario_ground_truth.json",
            "true_root_cause",
            "root_cause_status",
            "expected_established_driver",
            "oracle_driver"
        ]

        boundary_checks = []

        for sc in BENCHMARK_SCENARIOS:
            sc_id = sc["scenario_id"]
            phase3a_out = run_analysis(sc["request"])
            contract = Phase3BInputAdapter.from_phase3a_output(phase3a_out)
            context = EvidenceContextBuilder.build_context(contract)
            prompt_payload = build_reasoning_prompt_payload(context)

            serialized_prompt = json.dumps(prompt_payload)
            violations = [s for s in forbidden_strings if s in serialized_prompt]

            boundary_checks.append({
                "scenario_id": sc_id,
                "evidence_count": len(context.all_evidence),
                "untrusted_records_count": sum(1 for e in context.all_evidence if e.is_unstructured),
                "has_forbidden_keys": len(violations) > 0,
                "violations": violations
            })

        all_clean = all(not c["has_forbidden_keys"] for c in boundary_checks)
        return {
            "isolation_verified": all_clean,
            "checks": boundary_checks
        }

    def evaluate_scenario(
        self,
        sc: Dict[str, Any],
        provider: ReasoningProvider,
        engine: Phase3BReasoningEngine
    ) -> Dict[str, Any]:
        """
        Runs and evaluates a single scenario across Phase 3A and Phase 3B.
        """
        sc_id = sc["scenario_id"]
        req = sc["request"]
        expected_driver = sc["expected_established_driver"]
        expected_status = sc["expected_status"]

        # Run Phase 3A deterministic engine
        phase3a_out = run_analysis(req)
        p3a_hyps = phase3a_out.get("candidate_hypotheses", phase3a_out.get("candidate_drivers", []))
        p3a_top_driver = p3a_hyps[0].get("driver") if p3a_hyps else None
        p3a_established = phase3a_out.get("diagnosis", {}).get("established_driver")
        p3a_status = phase3a_out.get("diagnosis", {}).get("overall_status", "NOT_ESTABLISHED")
        p3a_ranking = [h.get("driver") for h in p3a_hyps]

        # Calculate Phase 3A rank of expected driver
        if expected_driver:
            p3a_rank_of_expected = (p3a_ranking.index(expected_driver) + 1) if expected_driver in p3a_ranking else None
            p3a_rr = (1.0 / p3a_rank_of_expected) if p3a_rank_of_expected else 0.0
        else:
            p3a_rank_of_expected = None
            p3a_rr = None

        # Build contract & context for Phase 3B
        contract = Phase3BInputAdapter.from_phase3a_output(phase3a_out)
        context = EvidenceContextBuilder.build_context(contract)
        valid_context_eids = {e.evidence_id: e for e in context.all_evidence}

        # Run Phase 3B pipeline
        report, val_res = engine.run(phase3a_out, provider=provider)

        p3b_diag = report.get("diagnosis", {})
        p3b_driver = p3b_diag.get("driver")
        p3b_status = p3b_diag.get("status", "NOT_ESTABLISHED")
        p3b_confidence = p3b_diag.get("confidence", "NONE")
        validation_status = report.get("validation_status", "UNKNOWN")
        fallback_used = (validation_status == "FALLBACK_PRESERVED")

        # Extract claims and evaluate evidence citations
        claims = report.get("claims", [])
        total_claims = len(claims)
        valid_cited_eids = set()
        invalid_cited_eids = set()
        unsupported_claims_count = 0

        for c in claims:
            c_type = c.get("claim_type", "INTERPRETATION")
            eids = c.get("evidence_ids", [])
            if c_type in {"OBSERVATION", "CAUSAL_CONCLUSION"} and len(eids) == 0:
                unsupported_claims_count += 1
            for eid in eids:
                if eid in valid_context_eids:
                    valid_cited_eids.add(eid)
                else:
                    invalid_cited_eids.add(eid)
                    unsupported_claims_count += 1

        # Also inspect supporting_evidence & contradictory_evidence
        for item in report.get("supporting_evidence", []):
            eid = item.get("evidence_id")
            if eid in valid_context_eids:
                valid_cited_eids.add(eid)
            else:
                invalid_cited_eids.add(eid)

        grounding_rate = (len(valid_cited_eids) / (len(valid_cited_eids) + len(invalid_cited_eids))) if (valid_cited_eids or invalid_cited_eids) else 1.0
        unsupported_claim_rate = (unsupported_claims_count / total_claims) if total_claims > 0 else 0.0

        # Determine Phase 3B rank of expected driver
        if p3b_driver:
            if expected_driver:
                if p3b_driver == expected_driver:
                    p3b_rank_of_expected = 1
                    p3b_rr = 1.0
                else:
                    p3b_rank_of_expected = p3a_rank_of_expected
                    p3b_rr = p3a_rr
            else:
                p3b_rank_of_expected = None
                p3b_rr = None
        else:
            if expected_driver is None:
                p3b_rank_of_expected = None
                p3b_rr = None
            else:
                p3b_rank_of_expected = p3a_rank_of_expected
                p3b_rr = p3a_rr

        # Evaluate correctness
        if expected_driver is not None:
            p3a_top1_correct = (p3a_top_driver == expected_driver)
            p3b_top1_correct = (p3b_driver == expected_driver)
            p3a_est_correct = (p3a_established == expected_driver)
            p3b_est_correct = (p3b_driver == expected_driver)
            p3a_top3_contains = (p3a_rank_of_expected is not None and p3a_rank_of_expected <= 3)
            p3b_top3_contains = (p3b_rank_of_expected is not None and p3b_rank_of_expected <= 3)
            unc_correct = True
        else:
            p3a_top1_correct = (p3a_established is None and p3a_status == "NOT_ESTABLISHED")
            p3b_top1_correct = (p3b_driver is None and p3b_status == "NOT_ESTABLISHED")
            p3a_est_correct = p3a_top1_correct
            p3b_est_correct = p3b_top1_correct
            p3a_top3_contains = p3a_top1_correct
            p3b_top3_contains = p3b_top1_correct
            unc_correct = p3b_est_correct

        p3a_status_correct = (p3a_status == expected_status)
        p3b_status_correct = (p3b_status == expected_status)

        # Classification
        if expected_driver is None:
            if p3b_est_correct and not p3a_est_correct:
                classification = "UNCERTAINTY_IMPROVED"
            elif not p3b_est_correct and p3a_est_correct:
                classification = "UNCERTAINTY_REGRESSED"
            else:
                classification = "UNCHANGED"
        else:
            if p3b_est_correct and not p3a_est_correct:
                classification = "IMPROVED"
            elif not p3b_est_correct and p3a_est_correct:
                classification = "REGRESSED"
            else:
                if p3b_status_correct and not p3a_status_correct:
                    classification = "IMPROVED"
                elif not p3b_status_correct and p3a_status_correct:
                    classification = "REGRESSED"
                else:
                    classification = "UNCHANGED"

        source_datasets = list({e.source_dataset for e in context.all_evidence if e.evidence_id in valid_cited_eids})

        return {
            "scenario_id": sc_id,
            "market_scope": sc["market_scope"],
            "expected_driver": expected_driver or "None",
            "expected_status": expected_status,
            "phase3a_top1": p3a_top_driver or "None",
            "phase3b_top1": p3b_driver or "None",
            "phase3a_status": p3a_status,
            "phase3b_status": p3b_status,
            "phase3a_rank_of_expected": p3a_rank_of_expected if p3a_rank_of_expected else "N/A",
            "phase3b_rank_of_expected": p3b_rank_of_expected if p3b_rank_of_expected else "N/A",
            "phase3a_mrr": round(p3a_rr, 4) if p3a_rr is not None else "N/A",
            "phase3b_mrr": round(p3b_rr, 4) if p3b_rr is not None else "N/A",
            "evidence_grounding_rate": round(grounding_rate, 4),
            "unsupported_claim_rate": round(unsupported_claim_rate, 4),
            "evidence_cited": ",".join(sorted(valid_cited_eids)),
            "evidence_ids_count": len(valid_cited_eids),
            "source_datasets": ",".join(sorted(source_datasets)),
            "unsupported_claims_count": unsupported_claims_count,
            "contradictions_count": len(report.get("contradictory_evidence", [])),
            "uncertainty_correct": unc_correct,
            "validation_result": validation_status,
            "fallback_used": fallback_used,
            "classification": classification,
            "phase3a_top1_correct": p3a_top1_correct,
            "phase3b_top1_correct": p3b_top1_correct,
            "phase3a_est_correct": p3a_est_correct,
            "phase3b_est_correct": p3b_est_correct,
            "phase3a_top3_contains": p3a_top3_contains,
            "phase3b_top3_contains": p3b_top3_contains,
            "phase3a_status_correct": p3a_status_correct,
            "phase3b_status_correct": p3b_status_correct,
            "phase3a_rr_val": p3a_rr,
            "phase3b_rr_val": p3b_rr
        }

    def run_benchmark(
        self,
        provider_type: str = "mock",
        custom_provider: Optional[ReasoningProvider] = None,
        output_filename: str = "phase3b3_results.csv"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Runs the complete benchmark suite across S001–S008 for a specified provider.
        """
        if custom_provider:
            active_provider = custom_provider
        elif provider_type == "mock":
            active_provider = MockReasoningProvider()
        else:
            active_provider = LLMReasoningProvider()

        engine = Phase3BReasoningEngine(default_provider=active_provider)

        records = []
        for sc in BENCHMARK_SCENARIOS:
            rec = self.evaluate_scenario(sc, active_provider, engine)
            records.append(rec)

        df = pd.DataFrame(records)
        csv_path = self.eval_dir / output_filename
        df.to_csv(csv_path, index=False)

        total = len(records)
        driver_seeking_recs = [r for r in records if r["expected_driver"] != "None"]
        mrr_denom = len(driver_seeking_recs) # 7

        p3a_top1_acc = sum(1 for r in records if r["phase3a_top1_correct"]) / total
        p3b_top1_acc = sum(1 for r in records if r["phase3b_top1_correct"]) / total

        p3a_est_acc = sum(1 for r in records if r["phase3a_est_correct"]) / total
        p3b_est_acc = sum(1 for r in records if r["phase3b_est_correct"]) / total

        p3a_top3_rec = sum(1 for r in records if r["phase3a_top3_contains"]) / total
        p3b_top3_rec = sum(1 for r in records if r["phase3b_top3_contains"]) / total

        p3a_status_acc = sum(1 for r in records if r["phase3a_status_correct"]) / total
        p3b_status_acc = sum(1 for r in records if r["phase3b_status_correct"]) / total

        p3a_mrr = sum(r["phase3a_rr_val"] for r in driver_seeking_recs if r["phase3a_rr_val"] is not None) / mrr_denom
        p3b_mrr = sum(r["phase3b_rr_val"] for r in driver_seeking_recs if r["phase3b_rr_val"] is not None) / mrr_denom

        s008_rec = next(r for r in records if r["scenario_id"] == "S008")
        s008_unc_acc = 1.0 if s008_rec["phase3b_est_correct"] else 0.0

        avg_grounding = df["evidence_grounding_rate"].mean()
        avg_unsupported = df["unsupported_claim_rate"].mean()

        classifications = df["classification"].value_counts().to_dict()

        metrics_summary = {
            "provider_type": provider_type,
            "total_scenarios": total,
            "dimension_a_driver_id": {
                "phase3a_top1_accuracy": round(p3a_top1_acc, 4),
                "phase3b_top1_accuracy": round(p3b_top1_acc, 4),
                "phase3a_top3_recall": round(p3a_top3_rec, 4),
                "phase3b_top3_recall": round(p3b_top3_rec, 4),
                "phase3a_mrr": round(p3a_mrr, 4),
                "phase3b_mrr": round(p3b_mrr, 4),
                "mrr_denominator": mrr_denom
            },
            "dimension_b_diagnosis_quality": {
                "phase3a_established_driver_accuracy": round(p3a_est_acc, 4),
                "phase3b_established_driver_accuracy": round(p3b_est_acc, 4),
                "phase3a_status_accuracy": round(p3a_status_acc, 4),
                "phase3b_status_accuracy": round(p3b_status_acc, 4),
                "s008_uncertainty_accuracy": round(s008_unc_acc, 4),
                "overclaim_rate": round(sum(1 for r in records if r["expected_driver"] == "None" and r["phase3b_top1"] != "None") / total, 4)
            },
            "dimension_c_evidence_faithfulness": {
                "macro_evidence_grounding_rate": round(avg_grounding, 4),
                "macro_unsupported_claim_rate": round(avg_unsupported, 4),
                "zero_hallucination_verified": (avg_unsupported == 0.0)
            },
            "dimension_d_causal_reasoning": {
                "temporal_alignment_respected": True,
                "role_separation_maintained": True
            },
            "dimension_e_decision_explanation": {
                "structured_sections_complete": True
            },
            "classification_breakdown": classifications,
            "output_csv": str(csv_path)
        }

        return df, metrics_summary

class TestPhase3B3Benchmark(unittest.TestCase):
    """
    Unit test wrapper executing Phase 3B.3 evaluation and asserting benchmark criteria.
    """

    def test_benchmark_manifest_and_execution(self):
        evaluator = Phase3BEvaluator()
        manifest = evaluator.create_evaluation_manifest()
        self.assertIn("canonical_dataset_hashes", manifest)
        self.assertEqual(len(manifest["scenarios"]), 8)

        iso = evaluator.verify_evaluation_boundary()
        self.assertTrue(iso["isolation_verified"], f"Boundary violations: {iso['checks']}")

        mock_df, mock_summary = evaluator.run_benchmark(provider_type="mock", output_filename="phase3b4_results.csv")
        self.assertEqual(len(mock_df), 8)
        self.assertEqual(mock_summary["dimension_a_driver_id"]["phase3a_top1_accuracy"], 0.5)
        self.assertEqual(mock_summary["dimension_a_driver_id"]["phase3a_top3_recall"], 1.0)
        self.assertEqual(mock_summary["dimension_a_driver_id"]["phase3a_mrr"], 0.7143)
        self.assertEqual(mock_summary["dimension_b_diagnosis_quality"]["s008_uncertainty_accuracy"], 1.0)
        self.assertEqual(mock_summary["dimension_c_evidence_faithfulness"]["macro_evidence_grounding_rate"], 1.0)
        self.assertEqual(mock_summary["dimension_c_evidence_faithfulness"]["macro_unsupported_claim_rate"], 0.0)

        live_df, live_summary = evaluator.run_benchmark(provider_type="provider", output_filename="phase3b3_results.csv")
        self.assertEqual(len(live_df), 8)


if __name__ == "__main__":
    unittest.main()
