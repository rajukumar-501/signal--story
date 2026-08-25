import pandas as pd
import numpy as np

class KPIEngine:
    """
    Calculates standard KPIs deterministically from analytical dataframes.
    """
    @staticmethod
    def gross_sales(df: pd.DataFrame) -> float:
        if df.empty or 'gross_sales_amount' not in df.columns:
            return 0.0
        return float(df['gross_sales_amount'].sum())

    @staticmethod
    def return_value(df: pd.DataFrame) -> float:
        if df.empty or 'return_sales_amount' not in df.columns:
            return 0.0
        return float(df['return_sales_amount'].sum())

    @staticmethod
    def signed_net_revenue(df: pd.DataFrame) -> float:
        """
        True net revenue MUST use SUM(signed_sales_amount).
        NEVER SUM(net_sales_amount).
        """
        if df.empty or 'signed_sales_amount' not in df.columns:
            return 0.0
        return float(df['signed_sales_amount'].sum())

    @staticmethod
    def gross_units(df: pd.DataFrame) -> float:
        if df.empty or 'gross_qty' not in df.columns:
            return 0.0
        return float(df['gross_qty'].sum())

    @staticmethod
    def return_units(df: pd.DataFrame) -> float:
        if df.empty or 'return_qty' not in df.columns:
            return 0.0
        return float(df['return_qty'].sum())

    @staticmethod
    def net_units(df: pd.DataFrame) -> float:
        if df.empty or 'Qty' not in df.columns:
            return 0.0
        return float(df['Qty'].sum())

    @staticmethod
    def return_rate(df: pd.DataFrame) -> float:
        """Return rate based on units."""
        gu = KPIEngine.gross_units(df)
        if gu == 0:
            return 0.0
        return float(KPIEngine.return_units(df) / gu)

    @staticmethod
    def return_rate_value(df: pd.DataFrame) -> float:
        """Return rate based on financial value."""
        gs = KPIEngine.gross_sales(df)
        if gs == 0:
            return 0.0
        return float(KPIEngine.return_value(df) / gs)

    @staticmethod
    def sales_growth(current_sales: float, prior_sales: float) -> float:
        if prior_sales == 0:
            return 0.0 if current_sales == 0 else float('inf')
        return float((current_sales - prior_sales) / prior_sales)

    @staticmethod
    def share_percentage(entity_value: float, total_value: float) -> float:
        """Generic share calculation (for market_share, category_share, channel_share)."""
        if total_value == 0:
            return 0.0
        return float(entity_value / total_value)

    @staticmethod
    def marketing_spend(df: pd.DataFrame) -> float:
        if df.empty or 'spend' not in df.columns:
            return 0.0
        return float(df['spend'].sum())

    @staticmethod
    def ctr(df: pd.DataFrame) -> float:
        if df.empty or 'impressions' not in df.columns or 'clicks' not in df.columns:
            return 0.0
        imp = df['impressions'].sum()
        if imp == 0:
            return 0.0
        return float(df['clicks'].sum() / imp)

    @staticmethod
    def conversion_rate(df: pd.DataFrame) -> float:
        if df.empty or 'clicks' not in df.columns or 'conversions' not in df.columns:
            return 0.0
        clicks = df['clicks'].sum()
        if clicks == 0:
            return 0.0
        return float(df['conversions'].sum() / clicks)

    @staticmethod
    def price_gap(df: pd.DataFrame) -> float:
        if df.empty or 'price_gap_percent' not in df.columns:
            return 0.0
        # Average price gap across the rows provided
        gap = df['price_gap_percent'].mean()
        return float(gap) if not pd.isna(gap) else 0.0
