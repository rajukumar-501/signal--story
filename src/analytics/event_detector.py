import pandas as pd
from typing import Dict, Any
from dateutil.relativedelta import relativedelta

from .data_model import AnalyticalDataModel
from .kpi_engine import KPIEngine

class EventDetector:
    """
    Detects business events deterministically by analyzing specific KPIs for a given entity and date.
    Calculates previous month values and 3-month rolling baselines.
    """
    def __init__(self, data_model: AnalyticalDataModel):
        self.dm = data_model

    def detect_event(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input:
        {
            "market": "China",
            "product_code": "A2520150501",
            "date": "2021-04-01",
            "kpi": "gross_sales",
            "channel": "Retail" # optional
        }
        """
        target_date = pd.to_datetime(request['date'])
        kpi_name = request['kpi']
        
        sales = self.dm.get_joined_sales()

        # Filter by request scope using reusable apply_scope
        entity_sales = self.dm.apply_scope(sales, request)
        
        # Filter market sales scoped only by market (for share baseline calculations)
        market_request = {"market": request.get("market")} if request.get("market") else {}
        market_sales = self.dm.apply_scope(sales, market_request)

        if entity_sales.empty:
            return self._empty_result(request)

        # Time periods
        prev_1m = target_date - relativedelta(months=1)
        prev_2m = target_date - relativedelta(months=2)
        prev_3m = target_date - relativedelta(months=3)

        df_current = entity_sales[entity_sales['date'] == target_date]
        df_prev_1m = entity_sales[entity_sales['date'] == prev_1m]
        df_prev_2m = entity_sales[entity_sales['date'] == prev_2m]
        df_prev_3m = entity_sales[entity_sales['date'] == prev_3m]

        if kpi_name == "category_share":
            def calc_share(df_ent, df_mkt, d):
                ent_d = df_ent[df_ent['date'] == d]
                mkt_d = df_mkt[df_mkt['date'] == d]
                return KPIEngine.share_percentage(KPIEngine.gross_sales(ent_d), KPIEngine.gross_sales(mkt_d))
                
            val_current = calc_share(entity_sales, market_sales, target_date)
            val_prev_1m = calc_share(entity_sales, market_sales, prev_1m)
            val_prev_2m = calc_share(entity_sales, market_sales, prev_2m)
            val_prev_3m = calc_share(entity_sales, market_sales, prev_3m)
        else:
            kpi_func = getattr(KPIEngine, kpi_name, None)
            if not kpi_func:
                raise ValueError(f"Unknown KPI: {kpi_name}")

            val_current = kpi_func(df_current)
            val_prev_1m = kpi_func(df_prev_1m)
            val_prev_2m = kpi_func(df_prev_2m)
            val_prev_3m = kpi_func(df_prev_3m)

        # Baseline calculation
        if df_prev_1m.empty:
            baseline_status = "INSUFFICIENT_HISTORY"
            baseline_value = 0.0
        else:
            baseline_status = "VALID"
            hist_vals = []
            if not df_prev_1m.empty: hist_vals.append(val_prev_1m)
            if not df_prev_2m.empty: hist_vals.append(val_prev_2m)
            if not df_prev_3m.empty: hist_vals.append(val_prev_3m)
            
            baseline_value = sum(hist_vals) / len(hist_vals) if hist_vals else 0.0

        abs_change = val_current - baseline_value
        pct_change = KPIEngine.sales_growth(val_current, baseline_value)
        mom_pct = KPIEngine.sales_growth(val_current, val_prev_1m)

        # Calculate detailed relative category metrics if applicable
        relative_metrics = {}
        if request.get("category") or kpi_name == "category_share":
            target_curr_sales = KPIEngine.gross_sales(df_current)
            target_prev_sales = KPIEngine.gross_sales(df_prev_1m)
            target_abs_change = target_curr_sales - target_prev_sales
            
            mkt_curr_sales = KPIEngine.gross_sales(market_sales[market_sales['date'] == target_date])
            mkt_prev_sales = KPIEngine.gross_sales(market_sales[market_sales['date'] == prev_1m])
            
            target_curr_share = target_curr_sales / mkt_curr_sales if mkt_curr_sales > 0 else 0.0
            target_prev_share = target_prev_sales / mkt_prev_sales if mkt_prev_sales > 0 else 0.0
            share_change = target_curr_share - target_prev_share
            
            # Comparison-category performance
            other_cats = [c for c in market_sales['category'].dropna().unique() if c != request.get('category')]
            comp_perf = {}
            for cat in other_cats:
                cat_df = market_sales[market_sales['category'] == cat]
                c_sales_curr = KPIEngine.gross_sales(cat_df[cat_df['date'] == target_date])
                c_sales_prev = KPIEngine.gross_sales(cat_df[cat_df['date'] == prev_1m])
                c_growth = KPIEngine.sales_growth(c_sales_curr, c_sales_prev)
                comp_perf[cat] = {
                    "current_sales": c_sales_curr,
                    "previous_sales": c_sales_prev,
                    "growth": c_growth
                }
                
            relative_metrics = {
                "target_category_current_share": target_curr_share,
                "target_category_previous_share": target_prev_share,
                "share_change": share_change,
                "target_category_absolute_sales_change": target_abs_change,
                "comparison_category_performance": comp_perf
            }

        return {
            "request": request,
            "kpi": kpi_name,
            "current_value": val_current,
            "previous_month_value": val_prev_1m,
            "rolling_3m_baseline": baseline_value,
            "mom_change_percent": mom_pct,
            "baseline_change_percent": pct_change,
            "absolute_change": abs_change,
            "percentage_change": pct_change,
            "baseline_status": baseline_status,
            "anomaly_magnitude": abs(pct_change) if baseline_status == "VALID" else 0.0,
            "relative_metrics": relative_metrics
        }

    def _empty_result(self, request: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "request": request,
            "kpi": request.get('kpi', 'unknown'),
            "current_value": 0.0,
            "previous_month_value": 0.0,
            "rolling_3m_baseline": 0.0,
            "mom_change_percent": 0.0,
            "baseline_change_percent": 0.0,
            "absolute_change": 0.0,
            "percentage_change": 0.0,
            "baseline_status": "INSUFFICIENT_HISTORY",
            "anomaly_magnitude": 0.0,
            "relative_metrics": {}
        }
