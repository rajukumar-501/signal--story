import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dateutil.relativedelta import relativedelta

from .data_model import AnalyticalDataModel
from .kpi_engine import KPIEngine
from .driver_catalog import DriverCatalog

class DriverGenerator:
    """
    Generates candidate drivers based on deterministic evaluation of cross-source datasets.
    """
    def __init__(self, data_model: AnalyticalDataModel):
        self.dm = data_model

    def generate_candidates(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        candidates = []
        
        if event.get("baseline_status") != "VALID":
            return candidates

        # 6. Inventory
        inv_cand = self._generate_inventory_candidate(event)
        if inv_cand: candidates.append(inv_cand)

        # 7. Pricing
        px_cand = self._generate_pricing_candidate(event)
        if px_cand: candidates.append(px_cand)

        # 8. Marketing
        mkt_cand = self._generate_marketing_candidate(event)
        if mkt_cand: candidates.append(mkt_cand)

        # 9. Returns
        ret_cand = self._generate_returns_candidate(event)
        if ret_cand: candidates.append(ret_cand)

        # 10. Support
        sup_cand = self._generate_support_candidate(event)
        if sup_cand: candidates.append(sup_cand)

        # 11. Customer
        cust_cand = self._generate_customer_candidate(event)
        if cust_cand: candidates.append(cust_cand)

        # 12. Market
        mkt_shift_cand = self._generate_market_candidate(event)
        if mkt_shift_cand: candidates.append(mkt_shift_cand)

        # 13. Product Mix
        prod_cand = self._generate_product_mix_candidate(event)
        if prod_cand: candidates.append(prod_cand)

        return candidates

    def _get_target_date(self, event: Dict[str, Any]) -> pd.Timestamp:
        return pd.to_datetime(event['request']['date'])

    def _create_evidence(self, dataset: str, record_id: Optional[str], lineage: str,
                         date: pd.Timestamp, request: Dict[str, Any], metric: str,
                         value: Any, role: str) -> Dict[str, Any]:
        """
        Creates a structured evidence dictionary with all required metadata.
        """
        return {
            "source_dataset": dataset,
            "record_id": record_id if record_id else None,
            "lineage": lineage,
            "date": date.strftime("%Y-%m-%d") if isinstance(date, (pd.Timestamp, pd.DatetimeIndex)) else str(date),
            "market": request.get("market"),
            "product_code": request.get("product_code"),
            "category": request.get("category"),
            "channel": request.get("channel"),
            "metric": metric,
            "value": float(value) if isinstance(value, (int, float, np.number)) else value,
            "evidence_role": role
        }

    def _generate_inventory_candidate(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        df = self.dm.get_inventory()
        if df.empty: return None
        df = self.dm.apply_scope(df, event['request'])
        if df.empty: return None
        
        target_date = self._get_target_date(event)
        prev_1m = target_date - relativedelta(months=1)
        next_1m = target_date + relativedelta(months=1)
        
        df_before = df[df['date'] == prev_1m]
        df_during = df[df['date'] == target_date]
        df_after = df[df['date'] == next_1m]
        
        if df_during.empty: return None
        
        def is_inv_signal(df_slice, df_prev_slice=None):
            if df_slice.empty: return False
            if df_slice['stockout_flag'].max() > 0 or df_slice['stockout_hours'].sum() > 0:
                return True
            if df_prev_slice is not None and not df_prev_slice.empty:
                curr_stock = df_slice['closing_stock_units'].sum()
                prev_stock = df_prev_slice['closing_stock_units'].sum()
                if prev_stock > 0 and (curr_stock - prev_stock) / prev_stock < -0.15:
                    return True
            return False
            
        df_before_prev = df[df['date'] == prev_1m - relativedelta(months=1)]
        
        sig_before = is_inv_signal(df_before, df_before_prev)
        sig_during = is_inv_signal(df_during, df_before)
        sig_after = is_inv_signal(df_after, df_during)
        
        if sig_during:
            temp_align = "DURING"
        elif sig_before:
            temp_align = "BEFORE"
        elif sig_after:
            temp_align = "AFTER"
        else:
            temp_align = "NO_CLEAR_ALIGNMENT"
            
        evidence = []
        outcome_ev = self._create_evidence(
            dataset="fact_sales_monthly",
            record_id=None,
            lineage="AGGREGATED: market + product + date",
            date=target_date,
            request=event['request'],
            metric=event['kpi'],
            value=event['current_value'],
            role="OUTCOME"
        )
        evidence.append(outcome_ev)
        
        if sig_during or sig_before or sig_after:
            max_flag = int(df_during['stockout_flag'].max()) if not df_during.empty else 0
            sum_hours = float(df_during['stockout_hours'].sum()) if not df_during.empty else 0.0
            
            if max_flag > 0:
                evidence.append(self._create_evidence(
                    dataset="fact_inventory_monthly",
                    record_id=None,
                    lineage="AGGREGATED",
                    date=target_date,
                    request=event['request'],
                    metric="stockout_flag",
                    value=max_flag,
                    role="SUPPORTING"
                ))
            if sum_hours > 0:
                evidence.append(self._create_evidence(
                    dataset="fact_inventory_monthly",
                    record_id=None,
                    lineage="AGGREGATED",
                    date=target_date,
                    request=event['request'],
                    metric="stockout_hours",
                    value=sum_hours,
                    role="SUPPORTING"
                ))
                
        # Contradiction: Stable inventory, stockout_flag = 0 during event month
        if not df_during.empty and df_during['stockout_flag'].max() == 0:
            evidence.append(self._create_evidence(
                dataset="fact_inventory_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="stockout_flag",
                value=0,
                role="CONTRADICTORY"
            ))
            
        change_pct = 0.0
        if not df_during.empty and not df_before.empty:
            curr_stock = df_during['closing_stock_units'].sum()
            prev_stock = df_before['closing_stock_units'].sum()
            if prev_stock > 0:
                change_pct = max(0.0, (prev_stock - curr_stock) / prev_stock)
        if sig_during and df_during['stockout_flag'].max() > 0:
            change_pct = max(change_pct, 1.0)
            
        return {
            "driver": "DRIVER_01_INVENTORY",
            "status": "PLAUSIBLE" if sig_during or sig_before else "NOT_ESTABLISHED",
            "evidence": evidence,
            "temporal_alignment": temp_align,
            "driver_change_pct": change_pct,
            "metrics": {
                "stockout_hours": float(df_during['stockout_hours'].sum()) if not df_during.empty else 0.0,
                "closing_stock": float(df_during['closing_stock_units'].sum()) if not df_during.empty else 0.0
            },
            "driver_direction": "deterioration"
        }

    def _generate_pricing_candidate(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        df = self.dm.get_pricing()
        if df.empty: return None
        df = self.dm.apply_scope(df, event['request'])
        if df.empty: return None
        
        target_date = self._get_target_date(event)
        prev_1m = target_date - relativedelta(months=1)
        next_1m = target_date + relativedelta(months=1)
        
        df_before = df[df['date'] == prev_1m]
        df_during = df[df['date'] == target_date]
        df_after = df[df['date'] == next_1m]
        
        if df_during.empty: return None
        
        def is_pricing_signal(df_slice, df_prev_slice=None):
            if df_slice.empty: return False
            gap = df_slice['price_gap_percent'].mean()
            if pd.notna(gap) and gap > 0.05:
                return True
            if df_prev_slice is not None and not df_prev_slice.empty:
                prev_gap = df_prev_slice['price_gap_percent'].mean()
                if pd.notna(gap) and pd.notna(prev_gap) and (gap - prev_gap) > 0.03:
                    return True
            return False
            
        df_before_prev = df[df['date'] == prev_1m - relativedelta(months=1)]
        
        sig_before = is_pricing_signal(df_before, df_before_prev)
        sig_during = is_pricing_signal(df_during, df_before)
        sig_after = is_pricing_signal(df_after, df_during)
        
        if sig_during:
            temp_align = "DURING"
        elif sig_before:
            temp_align = "BEFORE"
        elif sig_after:
            temp_align = "AFTER"
        else:
            temp_align = "NO_CLEAR_ALIGNMENT"
            
        evidence = []
        outcome_ev = self._create_evidence(
            dataset="fact_sales_monthly",
            record_id=None,
            lineage="AGGREGATED: market + product + date",
            date=target_date,
            request=event['request'],
            metric=event['kpi'],
            value=event['current_value'],
            role="OUTCOME"
        )
        evidence.append(outcome_ev)
        
        curr_gap = df_during['price_gap_percent'].mean()
        prev_gap = df_before['price_gap_percent'].mean() if not df_before.empty else np.nan
        
        if sig_during or sig_before or sig_after:
            if pd.notna(curr_gap):
                evidence.append(self._create_evidence(
                    dataset="fact_competitor_pricing_monthly",
                    record_id=None,
                    lineage="AGGREGATED",
                    date=target_date,
                    request=event['request'],
                    metric="price_gap_percent",
                    value=curr_gap,
                    role="SUPPORTING"
                ))
                
        # Contradiction: price gap is negative or decreased significantly
        if pd.notna(curr_gap) and curr_gap < 0:
            evidence.append(self._create_evidence(
                dataset="fact_competitor_pricing_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="price_gap_percent",
                value=curr_gap,
                role="CONTRADICTORY"
            ))
            
        change_pct = 0.0
        if pd.notna(curr_gap) and pd.notna(prev_gap):
            change_pct = max(0.0, curr_gap - prev_gap)
        elif pd.notna(curr_gap):
            change_pct = max(0.0, curr_gap)
            
        return {
            "driver": "DRIVER_02_PRICING",
            "status": "PLAUSIBLE" if sig_during or sig_before else "NOT_ESTABLISHED",
            "evidence": evidence,
            "temporal_alignment": temp_align,
            "driver_change_pct": change_pct,
            "metrics": {
                "current_gap": float(curr_gap) if pd.notna(curr_gap) else 0.0,
                "previous_gap": float(prev_gap) if pd.notna(prev_gap) else 0.0
            },
            "driver_direction": "deterioration"
        }

    def _generate_marketing_candidate(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        df = self.dm.get_marketing()
        if df.empty: return None
        df = self.dm.apply_scope(df, event['request'])
        if df.empty: return None
        
        target_date = self._get_target_date(event)
        prev_1m = target_date - relativedelta(months=1)
        next_1m = target_date + relativedelta(months=1)
        
        df_before = df[df['date'] == prev_1m]
        df_during = df[df['date'] == target_date]
        df_after = df[df['date'] == next_1m]
        
        if df_during.empty: return None
        
        def is_marketing_signal(df_slice, df_prev_slice=None):
            if df_slice.empty or df_prev_slice is None or df_prev_slice.empty: return False
            curr_spend = df_slice['spend'].sum()
            prev_spend = df_prev_slice['spend'].sum()
            spend_change = KPIEngine.sales_growth(curr_spend, prev_spend)
            
            curr_cvr = KPIEngine.conversion_rate(df_slice)
            prev_cvr = KPIEngine.conversion_rate(df_prev_slice)
            cvr_change = KPIEngine.sales_growth(curr_cvr, prev_cvr)
            
            # spend increases but conversion rate/CTR drops, or CVR drops while sales drop
            if spend_change > 0.05 and cvr_change < -0.05:
                return True
            return False
            
        df_before_prev = df[df['date'] == prev_1m - relativedelta(months=1)]
        
        sig_before = is_marketing_signal(df_before, df_before_prev)
        sig_during = is_marketing_signal(df_during, df_before)
        sig_after = is_marketing_signal(df_after, df_during)
        
        if sig_during:
            temp_align = "DURING"
        elif sig_before:
            temp_align = "BEFORE"
        elif sig_after:
            temp_align = "AFTER"
        else:
            temp_align = "NO_CLEAR_ALIGNMENT"
            
        evidence = []
        outcome_ev = self._create_evidence(
            dataset="fact_sales_monthly",
            record_id=None,
            lineage="AGGREGATED: market + product + date",
            date=target_date,
            request=event['request'],
            metric=event['kpi'],
            value=event['current_value'],
            role="OUTCOME"
        )
        evidence.append(outcome_ev)
        
        curr_spend = df_during['spend'].sum()
        prev_spend = df_before['spend'].sum() if not df_before.empty else 0.0
        spend_change = KPIEngine.sales_growth(curr_spend, prev_spend)
        
        curr_cvr = KPIEngine.conversion_rate(df_during)
        prev_cvr = KPIEngine.conversion_rate(df_before) if not df_before.empty else 0.0
        cvr_change = KPIEngine.sales_growth(curr_cvr, prev_cvr)
        
        if sig_during or sig_before or sig_after:
            evidence.append(self._create_evidence(
                dataset="fact_marketing_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="spend",
                value=curr_spend,
                role="SUPPORTING"
            ))
            evidence.append(self._create_evidence(
                dataset="fact_marketing_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="conversion_rate",
                value=curr_cvr,
                role="SUPPORTING"
            ))
            
        # Contradiction: spend decreased or cvr improved
        if spend_change < 0 or cvr_change > 0:
            evidence.append(self._create_evidence(
                dataset="fact_marketing_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="conversion_rate_change",
                value=cvr_change,
                role="CONTRADICTORY"
            ))
            
        return {
            "driver": "DRIVER_03_MARKETING",
            "status": "PLAUSIBLE" if sig_during or sig_before else "NOT_ESTABLISHED",
            "evidence": evidence,
            "temporal_alignment": temp_align,
            "driver_change_pct": abs(cvr_change) if cvr_change < 0 else spend_change,
            "metrics": {
                "spend_change": float(spend_change),
                "cvr_change": float(cvr_change)
            },
            "driver_direction": "deterioration"
        }

    def _generate_returns_candidate(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        df = self.dm.get_joined_sales()
        if df.empty: return None
        df = self.dm.apply_scope(df, event['request'])
        if df.empty: return None
        
        target_date = self._get_target_date(event)
        prev_1m = target_date - relativedelta(months=1)
        next_1m = target_date + relativedelta(months=1)
        
        df_before = df[df['date'] == prev_1m]
        df_during = df[df['date'] == target_date]
        df_after = df[df['date'] == next_1m]
        
        if df_during.empty: return None
        
        def is_returns_signal(df_slice, df_prev_slice=None):
            if df_slice.empty or df_prev_slice is None or df_prev_slice.empty: return False
            curr_rate = KPIEngine.return_rate_value(df_slice)
            prev_rate = KPIEngine.return_rate_value(df_prev_slice)
            if pd.notna(curr_rate) and pd.notna(prev_rate) and (curr_rate - prev_rate) > 0.02:
                return True
            return False
            
        df_before_prev = df[df['date'] == prev_1m - relativedelta(months=1)]
        
        sig_before = is_returns_signal(df_before, df_before_prev)
        sig_during = is_returns_signal(df_during, df_before)
        sig_after = is_returns_signal(df_after, df_during)
        
        if sig_during:
            temp_align = "DURING"
        elif sig_before:
            temp_align = "BEFORE"
        elif sig_after:
            temp_align = "AFTER"
        else:
            temp_align = "NO_CLEAR_ALIGNMENT"
            
        evidence = []
        outcome_ev = self._create_evidence(
            dataset="fact_sales_monthly",
            record_id=None,
            lineage="AGGREGATED: market + product + date",
            date=target_date,
            request=event['request'],
            metric=event['kpi'],
            value=event['current_value'],
            role="OUTCOME"
        )
        evidence.append(outcome_ev)
        
        curr_rate = KPIEngine.return_rate_value(df_during)
        prev_rate = KPIEngine.return_rate_value(df_before) if not df_before.empty else 0.0
        
        if sig_during or sig_before or sig_after:
            evidence.append(self._create_evidence(
                dataset="fact_sales_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="return_rate",
                value=curr_rate,
                role="SUPPORTING"
            ))
            
        # Contradiction: return rate stable or decreased
        if curr_rate - prev_rate <= 0.01:
            evidence.append(self._create_evidence(
                dataset="fact_sales_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="return_rate_change",
                value=curr_rate - prev_rate,
                role="CONTRADICTORY"
            ))
            
        return {
            "driver": "DRIVER_04_RETURNS",
            "status": "PLAUSIBLE" if sig_during or sig_before else "NOT_ESTABLISHED",
            "evidence": evidence,
            "temporal_alignment": temp_align,
            "driver_change_pct": float(curr_rate - prev_rate),
            "metrics": {
                "current_return_rate": float(curr_rate),
                "previous_return_rate": float(prev_rate)
            },
            "driver_direction": "deterioration"
        }

    def _generate_support_candidate(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        sup_df = self.dm.get_support()
        crm_df = self.dm.get_crm()
        calls_df = self.dm.get_sales_calls()
        
        target_date = self._get_target_date(event)
        prev_1m = target_date - relativedelta(months=1)
        prev_2m = target_date - relativedelta(months=2)
        next_1m = target_date + relativedelta(months=1)
        
        # Apply scope filtering
        sup_df = self.dm.apply_scope(sup_df, event['request'])
        crm_df = self.dm.apply_scope(crm_df, event['request'])
        calls_df = self.dm.apply_scope(calls_df, event['request'])
        
        # 1. Evaluate support tickets
        sup_before_prev = sup_df[sup_df['date'] == prev_2m]
        sup_before = sup_df[sup_df['date'] == prev_1m]
        sup_during = sup_df[sup_df['date'] == target_date]
        sup_after = sup_df[sup_df['date'] == next_1m]
        
        def get_ticket_metrics(df_slice):
            if df_slice.empty: return 0, 0, 0.0
            total = len(df_slice)
            neg = len(df_slice[df_slice['sentiment'].str.lower() == 'negative'])
            rate = neg / total if total > 0 else 0.0
            return total, neg, rate
            
        tot_bp, neg_bp, rate_bp = get_ticket_metrics(sup_before_prev)
        tot_b, neg_b, rate_b = get_ticket_metrics(sup_before)
        tot_d, neg_d, rate_d = get_ticket_metrics(sup_during)
        tot_a, neg_a, rate_a = get_ticket_metrics(sup_after)
        
        ticket_sig_during = (tot_d > tot_b and tot_b > 0 and (tot_d - tot_b)/tot_b > 0.15) or (neg_d - neg_b >= 2) or (rate_d - rate_b > 0.10)
        ticket_sig_before = (tot_b > tot_bp and tot_bp > 0 and (tot_b - tot_bp)/tot_bp > 0.15) or (neg_b - neg_bp >= 2) or (rate_b - rate_bp > 0.10)
        ticket_sig_after = (tot_a > tot_d and tot_d > 0 and (tot_a - tot_d)/tot_d > 0.15) or (neg_a - neg_d >= 2) or (rate_a - rate_d > 0.10)
        
        # 2. Evaluate CRM notes for complaints
        crm_keywords = ['delay', 'slow', 'defect', 'broken', 'pricing', 'expensive', 'refund', 'support', 'issue', 'complaint']
        
        def count_crm_complaints(df_slice):
            if df_slice.empty: return 0, []
            matches = []
            for _, row in df_slice.iterrows():
                text = str(row.get('note_text', '')).lower()
                if any(kw in text for kw in crm_keywords):
                    matches.append(row)
            return len(matches), matches
            
        crm_cnt_bp, _ = count_crm_complaints(crm_df[crm_df['date'] == prev_2m])
        crm_cnt_b, crm_m_b = count_crm_complaints(crm_df[crm_df['date'] == prev_1m])
        crm_cnt_d, crm_m_d = count_crm_complaints(crm_df[crm_df['date'] == target_date])
        crm_cnt_a, crm_m_a = count_crm_complaints(crm_df[crm_df['date'] == next_1m])
        
        crm_sig_during = (crm_cnt_d > crm_cnt_b) and (crm_cnt_d >= 2)
        crm_sig_before = (crm_cnt_b > crm_cnt_bp) and (crm_cnt_b >= 2)
        crm_sig_after = (crm_cnt_a > crm_cnt_d) and (crm_cnt_a >= 2)
        
        # 3. Evaluate Sales Calls
        calls_keywords = ['delay', 'slow', 'defect', 'broken', 'pricing', 'expensive', 'refund', 'support', 'issue', 'complaint']
        
        def count_calls_complaints(df_slice):
            if df_slice.empty: return 0, []
            matches = []
            for _, row in df_slice.iterrows():
                text = str(row.get('transcript', '')).lower()
                if any(kw in text for kw in calls_keywords):
                    matches.append(row)
            return len(matches), matches
            
        calls_cnt_bp, _ = count_calls_complaints(calls_df[calls_df['date'] == prev_2m])
        calls_cnt_b, calls_m_b = count_calls_complaints(calls_df[calls_df['date'] == prev_1m])
        calls_cnt_d, calls_m_d = count_calls_complaints(calls_df[calls_df['date'] == target_date])
        calls_cnt_a, calls_m_a = count_calls_complaints(calls_df[calls_df['date'] == next_1m])
        
        calls_sig_during = (calls_cnt_d > calls_cnt_b) and (calls_cnt_d >= 1)
        calls_sig_before = (calls_cnt_b > calls_cnt_bp) and (calls_cnt_b >= 1)
        calls_sig_after = (calls_cnt_a > calls_cnt_d) and (calls_cnt_a >= 1)
        
        # Combine signals for temporal alignment
        sig_before = ticket_sig_before or crm_sig_before or calls_sig_before
        sig_during = ticket_sig_during or crm_sig_during or calls_sig_during
        sig_after = ticket_sig_after or crm_sig_after or calls_sig_after
        
        if sig_during:
            temp_align = "DURING"
        elif sig_before:
            temp_align = "BEFORE"
        elif sig_after:
            temp_align = "AFTER"
        else:
            temp_align = "NO_CLEAR_ALIGNMENT"
            
        evidence = []
        evidence.append(self._create_evidence(
            dataset="fact_sales_monthly",
            record_id=None,
            lineage="AGGREGATED: market + product + date",
            date=target_date,
            request=event['request'],
            metric=event['kpi'],
            value=event['current_value'],
            role="OUTCOME"
        ))
        
        # Only append detailed tickets if they grew/exceeded threshold during the event month
        if sig_during:
            if not sup_during.empty:
                neg_tickets = sup_during[sup_during['sentiment'].str.lower() == 'negative']
                for _, row in neg_tickets.head(3).iterrows():
                    evidence.append({
                        "source_dataset": "fact_support_tickets",
                        "record_id": row.get('ticket_id'),
                        "lineage": "RECORD",
                        "date": target_date.strftime("%Y-%m-%d"),
                        "market": row.get('market'),
                        "product_code": row.get('product_code'),
                        "category": None,
                        "channel": None,
                        "metric": "sentiment_negative",
                        "value": 1.0,
                        "evidence_role": "SUPPORTING"
                    })
                evidence.append(self._create_evidence(
                    dataset="fact_support_tickets",
                    record_id=None,
                    lineage="AGGREGATED",
                    date=target_date,
                    request=event['request'],
                    metric="ticket_volume",
                    value=tot_d,
                    role="SUPPORTING"
                ))
                
            # Append detailed CRM complaints
            for row in crm_m_d[:2]:
                evidence.append({
                    "source_dataset": "fact_crm_notes",
                    "record_id": row.get('note_id'),
                    "lineage": "RECORD",
                    "date": target_date.strftime("%Y-%m-%d"),
                    "market": row.get('market'),
                    "product_code": row.get('product_code'),
                    "category": None,
                    "channel": None,
                    "metric": "crm_note_complaint",
                    "value": 1.0,
                    "evidence_role": "SUPPORTING"
                })
                
            # Append detailed Sales Call complaints
            for row in calls_m_d[:2]:
                evidence.append({
                    "source_dataset": "fact_sales_calls",
                    "record_id": row.get('call_id'),
                    "lineage": "RECORD",
                    "date": target_date.strftime("%Y-%m-%d"),
                    "market": row.get('market'),
                    "product_code": row.get('product_code'),
                    "category": None,
                    "channel": None,
                    "metric": "sales_call_complaint",
                    "value": 1.0,
                    "evidence_role": "SUPPORTING"
                })
            
        # Contradiction: If tickets and complaints are zero or decreased significantly
        if tot_d <= tot_b and crm_cnt_d <= crm_cnt_b and calls_cnt_d <= calls_cnt_b:
            evidence.append(self._create_evidence(
                dataset="fact_support_tickets",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="ticket_volume_stable_or_down",
                value=0.0,
                role="CONTRADICTORY"
            ))
            
        change_pct = 0.0
        if tot_b > 0 and tot_d > tot_b:
            change_pct = max(change_pct, (tot_d - tot_b)/tot_b)
        if rate_d > rate_b and rate_d - rate_b > 0:
            change_pct = max(change_pct, rate_d - rate_b)
        if crm_cnt_d > crm_cnt_b:
            change_pct = max(change_pct, float(crm_cnt_d - crm_cnt_b) / 5.0)
        if calls_cnt_d > calls_cnt_b:
            change_pct = max(change_pct, float(calls_cnt_d - calls_cnt_b) / 3.0)
            
        if not sig_during and not sig_before:
            return None
            
        return {
            "driver": "DRIVER_05_SUPPORT",
            "status": "PLAUSIBLE" if sig_during or sig_before else "NOT_ESTABLISHED",
            "evidence": evidence,
            "temporal_alignment": temp_align,
            "driver_change_pct": change_pct,
            "metrics": {
                "ticket_volume_growth": float((tot_d - tot_b)/tot_b) if tot_b > 0 else 0.0,
                "negative_sentiment_rate": float(rate_d)
            },
            "driver_direction": "deterioration"
        }

    def _generate_customer_candidate(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        df = self.dm.get_joined_sales()
        if df.empty or 'channel' not in df.columns: return None
        
        market_req = {"market": event['request'].get("market")} if event['request'].get("market") else {}
        df = self.dm.apply_scope(df, market_req)
        if df.empty: return None
        
        target_date = self._get_target_date(event)
        prev_1m = target_date - relativedelta(months=1)
        next_1m = target_date + relativedelta(months=1)
        
        def calculate_max_channel_shift(df_curr, df_prev):
            if df_curr.empty or df_prev.empty: return 0.0, None
            curr_total = df_curr['signed_sales_amount'].sum()
            prev_total = df_prev['signed_sales_amount'].sum()
            if curr_total == 0 or prev_total == 0: return 0.0, None
            
            curr_chan = df_curr.groupby('channel')['signed_sales_amount'].sum()
            prev_chan = df_prev.groupby('channel')['signed_sales_amount'].sum()
            
            max_shift = 0.0
            worst_chan = None
            for chan in curr_chan.index:
                if chan in prev_chan:
                    curr_share = curr_chan[chan] / curr_total
                    prev_share = prev_chan[chan] / prev_total
                    shift = prev_share - curr_share
                    if shift > max_shift:
                        max_shift = shift
                        worst_chan = chan
            return max_shift, worst_chan
            
        shift_during, chan_during = calculate_max_channel_shift(df[df['date'] == target_date], df[df['date'] == prev_1m])
        shift_before, chan_before = calculate_max_channel_shift(df[df['date'] == prev_1m], df[df['date'] == prev_1m - relativedelta(months=1)])
        shift_after, chan_after = calculate_max_channel_shift(df[df['date'] == next_1m], df[df['date'] == target_date])
        
        sig_before = shift_before > 0.03
        sig_during = shift_during > 0.03
        sig_after = shift_after > 0.03
        
        if sig_during:
            temp_align = "DURING"
        elif sig_before:
            temp_align = "BEFORE"
        elif sig_after:
            temp_align = "AFTER"
        else:
            temp_align = "NO_CLEAR_ALIGNMENT"
            
        evidence = []
        evidence.append(self._create_evidence(
            dataset="fact_sales_monthly",
            record_id=None,
            lineage="AGGREGATED: market + product + date",
            date=target_date,
            request=event['request'],
            metric=event['kpi'],
            value=event['current_value'],
            role="OUTCOME"
        ))
        
        if sig_during or sig_before or sig_after:
            if chan_during:
                evidence.append(self._create_evidence(
                    dataset="fact_sales_monthly",
                    record_id=None,
                    lineage="AGGREGATED: market + channel + date",
                    date=target_date,
                    request=event['request'],
                    metric=f"channel_share_decline_{chan_during}",
                    value=shift_during,
                    role="SUPPORTING"
                ))
                
        # Contradiction: shifts are very small
        if shift_during <= 0.02:
            evidence.append(self._create_evidence(
                dataset="fact_sales_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="max_channel_shift",
                value=shift_during,
                role="CONTRADICTORY"
            ))
            
        return {
            "driver": "DRIVER_06_CUSTOMER",
            "status": "PLAUSIBLE" if sig_during or sig_before else "NOT_ESTABLISHED",
            "evidence": evidence,
            "temporal_alignment": temp_align,
            "driver_change_pct": shift_during,
            "metrics": {
                "worst_channel": chan_during if chan_during else "None"
            },
            "driver_direction": "deterioration"
        }

    def _generate_market_candidate(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        df = self.dm.get_joined_sales()
        if df.empty: return None
        
        target_date = self._get_target_date(event)
        prev_1m = target_date - relativedelta(months=1)
        next_1m = target_date + relativedelta(months=1)
        
        target_market = event['request'].get('market')
        if not target_market:
            return None
            
        df_target = df[df['market'] == target_market]
        df_rest = df[df['market'] != target_market]
        
        def calculate_market_performance(df_t, df_r, t_date, p_date):
            t_curr = df_t[df_t['date'] == t_date]['signed_sales_amount'].sum()
            t_prev = df_t[df_t['date'] == p_date]['signed_sales_amount'].sum()
            t_growth = KPIEngine.sales_growth(t_curr, t_prev)
            
            r_curr = df_r[df_r['date'] == t_date]['signed_sales_amount'].sum()
            r_prev = df_r[df_r['date'] == p_date]['signed_sales_amount'].sum()
            r_growth = KPIEngine.sales_growth(r_curr, r_prev)
            
            return t_growth, r_growth
            
        g_target_during, g_rest_during = calculate_market_performance(df_target, df_rest, target_date, prev_1m)
        g_target_before, g_rest_before = calculate_market_performance(df_target, df_rest, prev_1m, prev_1m - relativedelta(months=1))
        g_target_after, g_rest_after = calculate_market_performance(df_target, df_rest, next_1m, target_date)
        
        # Target declines and target underperforms rest-of-company by > 10%
        def check_signal(target_g, rest_g):
            return target_g < -0.10 and (target_g - rest_g) < -0.10
            
        sig_before = check_signal(g_target_before, g_rest_before)
        sig_during = check_signal(g_target_during, g_rest_during)
        sig_after = check_signal(g_target_after, g_rest_after)
        
        if sig_during:
            temp_align = "DURING"
        elif sig_before:
            temp_align = "BEFORE"
        elif sig_after:
            temp_align = "AFTER"
        else:
            temp_align = "NO_CLEAR_ALIGNMENT"
            
        evidence = []
        evidence.append(self._create_evidence(
            dataset="fact_sales_monthly",
            record_id=None,
            lineage="AGGREGATED: market + product + date",
            date=target_date,
            request=event['request'],
            metric=event['kpi'],
            value=event['current_value'],
            role="OUTCOME"
        ))
        
        if sig_during or sig_before or sig_after:
            evidence.append(self._create_evidence(
                dataset="fact_sales_monthly",
                record_id=None,
                lineage="AGGREGATED: market + date",
                date=target_date,
                request=event['request'],
                metric="market_specific_underperformance",
                value=g_target_during - g_rest_during,
                role="SUPPORTING"
            ))
            
        # Contradiction: target performs similarly or better, or rest of company declines similarly
        if (g_target_during - g_rest_during) >= -0.05 or g_rest_during < -0.15:
            evidence.append(self._create_evidence(
                dataset="fact_sales_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="rest_of_company_decline",
                value=g_rest_during,
                role="CONTRADICTORY"
            ))
            
        return {
            "driver": "DRIVER_07_MARKET",
            "status": "PLAUSIBLE" if sig_during or sig_before else "NOT_ESTABLISHED",
            "evidence": evidence,
            "temporal_alignment": temp_align,
            "driver_change_pct": abs(g_target_during - g_rest_during),
            "metrics": {
                "target_growth": float(g_target_during),
                "rest_growth": float(g_rest_during)
            },
            "driver_direction": "deterioration"
        }

    def _generate_product_mix_candidate(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        df = self.dm.get_joined_sales()
        if df.empty or 'category' not in df.columns: return None
        
        market_req = {"market": event['request'].get("market")} if event['request'].get("market") else {}
        df = self.dm.apply_scope(df, market_req)
        if df.empty: return None
        
        target_date = self._get_target_date(event)
        prev_1m = target_date - relativedelta(months=1)
        next_1m = target_date + relativedelta(months=1)
        
        def calculate_max_category_shift(df_curr, df_prev):
            if df_curr.empty or df_prev.empty: return 0.0, None
            curr_total = df_curr['signed_sales_amount'].sum()
            prev_total = df_prev['signed_sales_amount'].sum()
            if curr_total == 0 or prev_total == 0: return 0.0, None
            
            curr_cat = df_curr.groupby('category')['signed_sales_amount'].sum()
            prev_cat = df_prev.groupby('category')['signed_sales_amount'].sum()
            
            max_shift = 0.0
            worst_cat = None
            for cat in curr_cat.index:
                if cat in prev_cat:
                    curr_share = curr_cat[cat] / curr_total
                    prev_share = prev_cat[cat] / prev_total
                    shift = prev_share - curr_share
                    if shift > max_shift:
                        max_shift = shift
                        worst_cat = cat
            return max_shift, worst_cat
            
        shift_during, cat_during = calculate_max_category_shift(df[df['date'] == target_date], df[df['date'] == prev_1m])
        shift_before, cat_before = calculate_max_category_shift(df[df['date'] == prev_1m], df[df['date'] == prev_1m - relativedelta(months=1)])
        shift_after, cat_after = calculate_max_category_shift(df[df['date'] == next_1m], df[df['date'] == target_date])
        
        sig_before = shift_before > 0.03
        sig_during = shift_during > 0.03
        sig_after = shift_after > 0.03
        
        if sig_during:
            temp_align = "DURING"
        elif sig_before:
            temp_align = "BEFORE"
        elif sig_after:
            temp_align = "AFTER"
        else:
            temp_align = "NO_CLEAR_ALIGNMENT"
            
        evidence = []
        evidence.append(self._create_evidence(
            dataset="fact_sales_monthly",
            record_id=None,
            lineage="AGGREGATED: market + product + date",
            date=target_date,
            request=event['request'],
            metric=event['kpi'],
            value=event['current_value'],
            role="OUTCOME"
        ))
        
        if sig_during or sig_before or sig_after:
            if cat_during:
                evidence.append(self._create_evidence(
                    dataset="fact_sales_monthly",
                    record_id=None,
                    lineage="AGGREGATED: market + category + date",
                    date=target_date,
                    request=event['request'],
                    metric=f"category_share_decline_{cat_during}",
                    value=shift_during,
                    role="SUPPORTING"
                ))
                
        # Contradiction: shifts are very small
        if shift_during <= 0.02:
            evidence.append(self._create_evidence(
                dataset="fact_sales_monthly",
                record_id=None,
                lineage="AGGREGATED",
                date=target_date,
                request=event['request'],
                metric="max_category_shift",
                value=shift_during,
                role="CONTRADICTORY"
            ))
            
        return {
            "driver": "DRIVER_08_PRODUCT_MIX",
            "status": "PLAUSIBLE" if sig_during or sig_before else "NOT_ESTABLISHED",
            "evidence": evidence,
            "temporal_alignment": temp_align,
            "driver_change_pct": shift_during,
            "metrics": {
                "worst_category": cat_during if cat_during else "None"
            },
            "driver_direction": "deterioration"
        }

