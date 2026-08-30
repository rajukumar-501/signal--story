"""
Output Formatter for Phase 3B Reasoning Engine.
Formats validated reasoning results into structured JSON and presentation markdown.
"""

from typing import Dict, Any, Optional

class OutputFormatter:
    """
    Formats validated diagnostic and reasoning results for API consumers and report generators.
    """

    @classmethod
    def format_json(cls, validated_data: Dict[str, Any], validation_warnings: Optional[list] = None) -> Dict[str, Any]:
        output = dict(validated_data)
        output["validation_status"] = "PASSED"
        if validation_warnings:
            output["validation_warnings"] = validation_warnings
        return output

    @classmethod
    def format_markdown(cls, validated_data: Dict[str, Any]) -> str:
        summary = validated_data.get("executive_summary", "")
        what = validated_data.get("what_happened", "")
        diag = validated_data.get("diagnosis", {})
        reasoning = validated_data.get("reasoning", [])
        sup_ev = validated_data.get("supporting_evidence", [])
        con_ev = validated_data.get("contradictory_evidence", [])
        uncertainties = validated_data.get("uncertainties", [])
        next_steps = validated_data.get("recommended_next_steps", [])

        md = []
        md.append("# Decision Intelligence Diagnostic Report\n")
        md.append(f"## Executive Summary\n{summary}\n")
        md.append(f"## What Happened\n{what}\n")
        md.append(f"## Diagnosis Verdict\n- **Driver**: `{diag.get('driver')}`\n- **Status**: `{diag.get('status')}`\n- **Confidence**: `{diag.get('confidence')}`\n")

        md.append("## Evidence-Grounded Reasoning")
        for idx, r in enumerate(reasoning, 1):
            cites = ", ".join(r.get("evidence_ids", []))
            md.append(f"### Claim {idx}: {r.get('claim')}")
            md.append(f"- **Cited Evidence**: `{cites}`")
            md.append(f"- **Explanation**: {r.get('explanation')}\n")

        if sup_ev:
            md.append("## Supporting Evidence")
            for ev in sup_ev:
                md.append(f"- **[{ev.get('evidence_id')}]** `{ev.get('source_dataset')}` (`{ev.get('metric')}`): {ev.get('finding')}")
            md.append("")

        if con_ev:
            md.append("## Contradictory Evidence")
            for ev in con_ev:
                md.append(f"- **[{ev.get('evidence_id')}]** `{ev.get('source_dataset')}` (`{ev.get('metric')}`): {ev.get('finding')}")
            md.append("")

        if uncertainties:
            md.append("## Uncertainties & Causal Bounds")
            for u in uncertainties:
                md.append(f"- {u}")
            md.append("")

        if next_steps:
            md.append("## Recommended Next Steps")
            for step in next_steps:
                md.append(f"1. {step}")
            md.append("")

        return "\n".join(md)
