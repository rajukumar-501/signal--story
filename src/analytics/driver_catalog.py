from typing import Dict, Any

class DriverCatalog:
    """
    Registry of all candidate driver families and their definitions for Phase 3A.
    """
    DRIVERS = {
        "DRIVER_01_INVENTORY": {
            "name": "Inventory / Availability",
            "required_datasets": ["fact_sales_monthly", "fact_inventory_monthly"],
            "relevant_metrics": ["stockout_flag", "stockout_hours", "closing_stock_units", "received_units"],
            "expected_direction": "deterioration (stockout increase or closing stock drop)",
            "evidence_conditions": ["Sales decline AND inventory availability deterioration"],
            "contradiction_conditions": ["Sales declined but stock was fully available (stockout_flag = 0)"]
        },
        "DRIVER_02_PRICING": {
            "name": "Competitive Pricing Pressure",
            "required_datasets": ["fact_sales_monthly", "fact_competitor_pricing_monthly"],
            "relevant_metrics": ["our_price", "average_competitor_price", "price_gap_percent"],
            "expected_direction": "price_gap_percent increases (our price relatively higher)",
            "evidence_conditions": ["Sales deteriorate AND competitive price position deteriorates"],
            "contradiction_conditions": ["Sales decline in markets without the price signal", "Our price was actually lower"]
        },
        "DRIVER_03_MARKETING": {
            "name": "Marketing Effectiveness",
            "required_datasets": ["fact_sales_monthly", "fact_marketing_monthly"],
            "relevant_metrics": ["spend", "impressions", "clicks", "conversions", "conversion_rate", "ctr"],
            "expected_direction": "spend increases BUT conversion_rate/ctr deteriorates OR sales fail to respond",
            "evidence_conditions": ["Marketing investment changes materially AND conversion performance deteriorates AND/OR sales fail to respond proportionally"],
            "contradiction_conditions": ["Sales decline was market-wide", "Inventory stockouts occurred during marketing push"]
        },
        "DRIVER_04_RETURNS": {
            "name": "Returns Spike",
            "required_datasets": ["fact_sales_monthly"],
            "relevant_metrics": ["gross_sales_amount", "return_sales_amount", "signed_sales_amount", "return_rate"],
            "expected_direction": "return_rate increases materially",
            "evidence_conditions": ["Return rate increases materially AND returns materially affect net revenue"],
            "contradiction_conditions": ["Returns increased only after sales fell", "Gross sales fell equally"]
        },
        "DRIVER_05_SUPPORT": {
            "name": "Customer Service / Support Deterioration",
            "required_datasets": ["fact_sales_monthly", "fact_support_tickets", "fact_crm_notes", "fact_sales_calls"],
            "relevant_metrics": ["ticket volume", "ticket growth", "negative sentiment rate"],
            "expected_direction": "ticket volume/negative sentiment increases",
            "evidence_conditions": ["Support issues spike ahead of or alongside sales drop"],
            "contradiction_conditions": ["Support volume remained normal", "No relevant unstructured evidence exists"]
        },
        "DRIVER_06_CUSTOMER": {
            "name": "Customer / Segment Change",
            "required_datasets": ["fact_sales_monthly", "dim_customer"],
            "relevant_metrics": ["revenue by segment", "revenue share", "segment growth"],
            "expected_direction": "shift in segment concentration or relative channel deterioration",
            "evidence_conditions": ["Specific segments/channels deteriorate relative to others"],
            "contradiction_conditions": ["All segments declined equally (absolute drop, not a shift)"]
        },
        "DRIVER_07_MARKET": {
            "name": "Market / Regional Change",
            "required_datasets": ["fact_sales_monthly", "dim_market"],
            "relevant_metrics": ["market share", "market growth"],
            "expected_direction": "market specific decline vs total",
            "evidence_conditions": ["Decline isolated to specific region"],
            "contradiction_conditions": ["Decline is global"]
        },
        "DRIVER_08_PRODUCT_MIX": {
            "name": "Product / Category Mix Shift",
            "required_datasets": ["fact_sales_monthly", "dim_product"],
            "relevant_metrics": ["category share", "product share"],
            "expected_direction": "relative performance shift",
            "evidence_conditions": ["Category/product share drops while others grow or remain stable"],
            "contradiction_conditions": ["All products dropped equally"]
        },
        "DRIVER_09_UNEXPLAINED": {
            "name": "Unexplained / Insufficient Evidence",
            "required_datasets": [],
            "relevant_metrics": [],
            "expected_direction": "none",
            "evidence_conditions": ["No strong driver meets evidence threshold"],
            "contradiction_conditions": []
        }
    }
    
    @classmethod
    def get_driver(cls, driver_id: str) -> Dict[str, Any]:
        return cls.DRIVERS.get(driver_id, {})
    
    @classmethod
    def list_drivers(cls) -> list:
        return list(cls.DRIVERS.keys())
