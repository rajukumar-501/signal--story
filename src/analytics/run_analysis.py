import argparse
import json
from .data_model import AnalyticalDataModel
from .event_detector import EventDetector
from .driver_generator import DriverGenerator
from .evidence_scorer import EvidenceScorer
from .contradiction_engine import ContradictionEngine
from .driver_ranker import DriverRanker
from .diagnosis import DiagnosisFormatter, DiagnosisGate

def run_analysis(request: dict) -> dict:
    dm = AnalyticalDataModel()
    
    # 1. Event Detection
    detector = EventDetector(dm)
    event = detector.detect_event(request)
    
    if event["baseline_status"] != "VALID":
        unestablished_diagnosis = DiagnosisGate.evaluate(event, [])
        return DiagnosisFormatter.format_diagnosis(event, [], unestablished_diagnosis)

    # 2. Generate Candidate Drivers
    generator = DriverGenerator(dm)
    candidates = generator.generate_candidates(event)
    
    # 3. Score Evidence
    candidates = EvidenceScorer.score_candidates(candidates)
    
    # 4. Evaluate Contradictions
    contradictor = ContradictionEngine(dm)
    candidates = contradictor.evaluate_contradictions(candidates, event)
    
    # 5. Rank Hypotheses
    ranked_hypotheses = DriverRanker.rank_candidates(candidates)
    
    # 6. Evaluate Diagnosis Gate
    diagnosis = DiagnosisGate.evaluate(event, ranked_hypotheses)
    
    # 7. Format Output
    return DiagnosisFormatter.format_diagnosis(event, ranked_hypotheses, diagnosis)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Deterministic Cross-Source Analytical Engine")
    parser.add_argument("--market", type=str, help="Market name")
    parser.add_argument("--category", type=str, help="Category name")
    parser.add_argument("--product", type=str, help="Product code")
    parser.add_argument("--date", type=str, required=True, help="Date YYYY-MM-DD")
    parser.add_argument("--kpi", type=str, required=True, help="KPI to analyze")
    
    args = parser.parse_args()
    
    request = {
        "date": args.date,
        "kpi": args.kpi
    }
    if args.market: request["market"] = args.market
    if args.category: request["category"] = args.category
    if args.product: request["product_code"] = args.product
    
    result = run_analysis(request)
    print(json.dumps(result, indent=2))
