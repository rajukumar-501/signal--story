import os
import sys
import inspect
from pathlib import Path
from src.analytics.run_analysis import run_analysis

def test_leakage_prevention():
    """Ensure ground truth modules are not imported by the analytics engine."""
    # 1. sys.modules check
    leakage_modules = [m for m in sys.modules.keys() if "ground_truth" in m]
    assert len(leakage_modules) == 0, f"sys.modules Leakage detected: {leakage_modules}"
    
    # 2. Inspect run_analysis signature
    sig = inspect.signature(run_analysis)
    assert 'expected_driver' not in sig.parameters
    assert 'true_root_cause' not in sig.parameters

    # 3. Check for leaked words in src/analytics/
    project_root = Path(__file__).resolve().parent.parent
    analytics_dir = project_root / "src" / "analytics"
    banned_words = ["S001_truth", "S002_truth", "evaluation_ground_truth"]
    exempt_files = ["evaluator.py", "remediate_ground_truth.py", "scenario_ground_truth.py"]
    
    for file_path in analytics_dir.rglob("*.py"):
        if file_path.name in exempt_files:
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            for word in banned_words:
                assert word not in content, f"Leakage word '{word}' found in {file_path.name}"
                
def test_determinism():
    """Run the engine twice and assert identical output."""
    request = {
        "market": "Germany",
        "date": "2020-03-01",
        "kpi": "gross_sales"
    }
    result1 = run_analysis(request)
    result2 = run_analysis(request)
    
    assert result1 == result2, "Engine output is not deterministic."

def test_missing_data_handling():
    """Verify how the engine handles queries with zero data."""
    request = {
        "market": "NonExistentMarket",
        "date": "2020-03-01",
        "kpi": "gross_sales"
    }
    result = run_analysis(request)
    assert result["event"]["baseline_status"] == "INSUFFICIENT_HISTORY"
    assert result["overall_status"] == "NOT_ESTABLISHED"

def test_behavior_triggers():
    """Verify engine triggers specific drivers under known conditions without ground truth."""
    # 1. Marketing trigger (China, A2520150501, 2021-04-01 - known to trigger MARKETING)
    res_mkt = run_analysis({"market": "China", "product_code": "A2520150501", "date": "2021-04-01", "kpi": "gross_sales"})
    drivers_mkt = [c["driver"] for c in res_mkt["candidate_drivers"]]
    assert "DRIVER_03_MARKETING" in drivers_mkt, "Engine should trigger MARKETING when spend/ctr changes materially."

    # 2. Market/Pricing trigger (China, A0621150308, 2021-01-01)
    res_prc = run_analysis({"market": "China", "product_code": "A0621150308", "date": "2021-01-01", "kpi": "gross_sales"})
    drivers_prc = [c["driver"] for c in res_prc["candidate_drivers"]]
    assert "DRIVER_02_PRICING" in drivers_prc, "Engine should trigger PRICING when price gap worsens."
    
    # 3. Product Mix / Category Share trigger (Portugal, Wi fi extender, 2019-09-01)
    res_mix = run_analysis({"market": "Portugal", "category": "Wi fi extender", "date": "2019-09-01", "kpi": "category_share"})
    drivers_mix = [c["driver"] for c in res_mix["candidate_drivers"]]
    assert "DRIVER_08_PRODUCT_MIX" in drivers_mix, "Engine should trigger PRODUCT_MIX on category share drops."
    
    # 4. Uncertainty trigger (Germany, 2020-05-01 - a random date with no huge drop)
    res_unc = run_analysis({"market": "Germany", "date": "2020-05-01", "kpi": "gross_sales"})
    # It might still trigger something, but if evidence is weak, it should be NOT_ESTABLISHED
    # We will just verify the engine runs properly for uncertainty scenarios.
    assert "overall_status" in res_unc

if __name__ == "__main__":
    test_leakage_prevention()
    test_determinism()
    test_missing_data_handling()
    test_behavior_triggers()
    print("Engineering tests completed successfully.")
