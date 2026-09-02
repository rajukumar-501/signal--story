"""
Role-Based Access Control & Entitlement Engine (Phase 6F).
Enforces prototype role-based data access, sensitive field redaction,
and permission gating for Executive, Domain Analyst, and Restricted User personas.
"""

import json
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENTITLEMENT_CONTRACT_PATH = PROJECT_ROOT / "Data" / "semantic" / "entitlement_contract.json"


class EntitlementEngine:
    """Enforces prototype role-based access control and data redaction."""

    def __init__(self, contract_path: Path = ENTITLEMENT_CONTRACT_PATH):
        self.contract_path = contract_path
        self.contract = self._load_contract()

    def _load_contract(self) -> Dict[str, Any]:
        if self.contract_path.exists():
            with open(self.contract_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "roles": {
                "EXECUTIVE": {"display_name": "Executive / Leadership"},
                "DOMAIN_ANALYST": {"display_name": "Domain Analyst / RevOps"},
                "RESTRICTED_USER": {"display_name": "Restricted User / External Auditor"}
            }
        }

    def apply_entitlements_to_payload(self, payload: Dict[str, Any], role: str = "EXECUTIVE") -> Dict[str, Any]:
        """
        Apply role-based entitlements, data redaction, and permission gates to the analysis payload.
        """
        normalized_role = (role or "EXECUTIVE").upper().strip()
        if normalized_role not in ["EXECUTIVE", "DOMAIN_ANALYST", "RESTRICTED_USER"]:
            normalized_role = "EXECUTIVE"

        role_meta = self.contract.get("roles", {}).get(normalized_role, {})
        allowed_views = role_meta.get("allowed_views", ["view-executive", "view-reasoning", "view-trace"])

        entitlement_meta = {
            "active_role": normalized_role,
            "display_name": role_meta.get("display_name", normalized_role),
            "allowed_views": allowed_views,
            "data_access": role_meta.get("data_access", {}),
            "is_redacted": normalized_role == "RESTRICTED_USER",
            "approval_authorized": normalized_role in ["EXECUTIVE"]
        }
        payload["entitlement"] = entitlement_meta

        # If RESTRICTED_USER, apply sensitive data redactions
        if normalized_role == "RESTRICTED_USER":
            # Redact Event gross numbers
            if "phase3a" in payload and "event" in payload["phase3a"]:
                payload["phase3a"]["event"]["actual_value"] = "[RESTRICTED - FINANCIAL CONFIDENTIAL]"
                payload["phase3a"]["event"]["baseline_value"] = "[RESTRICTED - FINANCIAL CONFIDENTIAL]"
                payload["phase3a"]["event"]["current_value"] = "[RESTRICTED - FINANCIAL CONFIDENTIAL]"

            # Redact Connected KPIs values
            if "connected_kpis" in payload and "connected_kpis" in payload["connected_kpis"]:
                for kpi in payload["connected_kpis"]["connected_kpis"]:
                    if kpi.get("kpi_id") in ["gross_sales", "marketing_spend"]:
                        kpi["formatted_value"] = "[RESTRICTED]"
                        kpi["formatted_change"] = "[RESTRICTED]"
                        kpi["current_value"] = None
                        kpi["baseline_value"] = None

            # Redact Decision Action
            if "decision_governance" in payload:
                payload["decision_governance"]["recommended_action"] = "[RESTRICTED - EXECUTIVE PERMISSION REQUIRED]"
                payload["decision_governance"]["finding_statement"] = "[RESTRICTED - SENSITIVE COMMERCIAL TELEMETRY]"
                payload["decision_governance"]["why_it_matters"] = "[RESTRICTED]"

            # Redact Persona Summary if present
            if "persona_view" in payload:
                payload["persona_view"]["summary"] = "Financial telemetry and executive remediation actions are restricted for this role."
                payload["persona_view"]["recommended_action"] = "[RESTRICTED - INSUFFICIENT PERMISSIONS]"

        return payload
